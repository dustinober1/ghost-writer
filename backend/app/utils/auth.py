from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models.database import get_db, User, RefreshToken
from app.models.schemas import TokenData
import os
import hashlib
import bcrypt
import secrets
from zxcvbn import zxcvbn
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
MAX_FAILED_LOGIN_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
ACCOUNT_LOCKOUT_MINUTES = int(os.getenv("ACCOUNT_LOCKOUT_MINUTES", "15"))
MIN_PASSWORD_STRENGTH = int(os.getenv("MIN_PASSWORD_STRENGTH", "2"))  # 0-4 scale

# Configure CryptContext with bcrypt
# We'll use bcrypt directly to avoid passlib's initialization issues
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Bcrypt has a 72-byte limit for passwords
BCRYPT_MAX_PASSWORD_LENGTH = 72


def _prepare_password_for_bcrypt(password: str) -> bytes:
    """
    Prepare password for bcrypt hashing.
    If password is longer than 72 bytes, hash it with SHA-256 first.
    This preserves security while working within bcrypt's limitations.
    Returns bytes that bcrypt can handle (max 72 bytes).
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
        # Hash with SHA-256 first (produces 32 bytes)
        # This is well under 72 bytes, so bcrypt can handle it
        return hashlib.sha256(password_bytes).digest()
    # Return as-is if within limit (bcrypt handles up to 72 bytes)
    return password_bytes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        # Prepare password the same way we did during hashing
        prepared = _prepare_password_for_bcrypt(plain_password)
        # Use bcrypt directly to avoid passlib initialization issues
        return bcrypt.checkpw(prepared, hashed_password.encode('utf-8'))
    except Exception:
        # If direct bcrypt fails, return False
        # This could happen with malformed hashes or other errors
        return False


def get_password_hash(password: str) -> str:
    """Hash a password, handling passwords longer than bcrypt's 72-byte limit"""
    prepared = _prepare_password_for_bcrypt(password)
    # Use bcrypt directly to avoid passlib initialization issues
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prepared, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength using zxcvbn.
    Returns (is_valid, error_message)
    """
    result = zxcvbn(password)
    score = result['score']
    
    if score < MIN_PASSWORD_STRENGTH:
        feedback = result.get('feedback', {})
        suggestions = feedback.get('suggestions', [])
        warning = feedback.get('warning', '')
        
        messages = []
        if warning:
            messages.append(warning)
        if suggestions:
            messages.extend(suggestions[:2])  # Limit to 2 suggestions
        
        error_msg = "Password is too weak. "
        if messages:
            error_msg += " ".join(messages)
        else:
            error_msg += f"Score: {score}/4 (minimum: {MIN_PASSWORD_STRENGTH}/4)"
        
        return False, error_msg
    
    return True, ""


def check_account_locked(user: User) -> bool:
    """Check if account is locked"""
    if user.locked_until is None:
        return False
    
    if user.locked_until > datetime.utcnow():
        return True
    
    # Lock expired, reset
    user.locked_until = None
    user.failed_login_attempts = 0
    return False


def handle_failed_login(db: Session, user: User):
    """Handle a failed login attempt"""
    user.failed_login_attempts += 1
    
    if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
        user.locked_until = datetime.utcnow() + timedelta(minutes=ACCOUNT_LOCKOUT_MINUTES)
        user.failed_login_attempts = 0  # Reset counter after locking
    
    db.commit()


def handle_successful_login(db: Session, user: User):
    """Handle a successful login - reset failed attempts"""
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()


def create_refresh_token(db: Session, user_id: int) -> str:
    """Create a refresh token and store it in the database"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(refresh_token)
    db.commit()
    
    return token


def verify_refresh_token(db: Session, token: str) -> Optional[User]:
    """Verify a refresh token and return the user"""
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.expires_at > datetime.utcnow(),
        RefreshToken.revoked == False
    ).first()
    
    if not refresh_token:
        return None
    
    return db.query(User).filter(User.id == refresh_token.user_id).first()


def revoke_refresh_token(db: Session, token: str):
    """Revoke a refresh token"""
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token
    ).first()
    
    if refresh_token:
        refresh_token.revoked = True
        db.commit()


def revoke_all_user_refresh_tokens(db: Session, user_id: int):
    """Revoke all refresh tokens for a user (e.g., on password change)"""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False
    ).update({"revoked": True})
    db.commit()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    return user


def extract_token_from_header(request: Request) -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    Returns None if no token or invalid format.
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None

    # Expected format: "Bearer <token>"
    parts = authorization.split()
    if parts[0].lower() != "bearer" or len(parts) != 2:
        return None

    return parts[1]


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """
    Get the current authenticated user from JWT token, but return None if not authenticated.
    Used for development mode to allow API testing without full auth flow.
    """
    # Extract token from Authorization header
    token = extract_token_from_header(request)

    # In development mode, if no token provided, return None
    if os.getenv("ENVIRONMENT") == "development" and not token:
        return None

    # No token provided
    if not token:
        return None

    # Try to decode and validate token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None

        user = db.query(User).filter(User.email == email).first()
        if not user or not user.is_active:
            return None

        return user
    except (JWTError, Exception):
        return None
