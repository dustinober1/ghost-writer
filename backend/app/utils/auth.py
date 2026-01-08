from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models.database import get_db, User
from app.models.schemas import TokenData
import os
import hashlib
import bcrypt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

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
    return user
