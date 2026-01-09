from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.models.database import get_db, User
from app.middleware.rate_limit import auth_rate_limit
from app.middleware.input_sanitization import sanitize_text
from app.models.schemas import (
    UserCreate, UserResponse, Token, RefreshTokenRequest,
    ForgotPasswordRequest, ResetPasswordRequest, EmailVerificationRequest,
    ChangePasswordRequest
)
from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    validate_password_strength,
    check_account_locked,
    handle_failed_login,
    handle_successful_login,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    revoke_all_user_refresh_tokens,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.utils.email import (
    send_verification_email,
    verify_email_token,
    send_password_reset_email,
    verify_password_reset_token,
    mark_password_reset_token_used,
)
from app.middleware.audit_logging import log_auth_event

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@auth_rate_limit
async def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Create new user (email not verified by default)
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        email_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log registration
    log_auth_event("register", user_id=new_user.id, user_email=new_user.email, success=True)
    
    # Send verification email
    await send_verification_email(db, new_user)
    
    return new_user


def _create_token_response(user: User, db: Session) -> dict:
    """Helper to create token response with both access and refresh tokens"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(db, user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=Token)
@auth_rate_limit
def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db: Session = Depends(get_db)):
    """Login and get access token with refresh token"""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Check if account is locked
    if user and check_account_locked(user):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked due to too many failed login attempts. Try again later."
        )
    
    if not user or not verify_password(form_data.password, user.password_hash):
        if user:
            handle_failed_login(db, user)
            log_auth_event("login", user_id=user.id, user_email=user.email, success=False, 
                          details={"reason": "incorrect_password"})
        else:
            log_auth_event("login", user_email=form_data.username, success=False,
                          details={"reason": "user_not_found"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for verification link."
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Successful login
    handle_successful_login(db, user)
    
    return _create_token_response(user, db)


@router.post("/login-json", response_model=Token)
@auth_rate_limit
def login_json(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Login endpoint that accepts JSON (alternative to form data)"""
    user = db.query(User).filter(User.email == user_data.email).first()
    
    # Check if account is locked
    if user and check_account_locked(user):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked due to too many failed login attempts. Try again later."
        )
    
    if not user or not verify_password(user_data.password, user.password_hash):
        if user:
            handle_failed_login(db, user)
            log_auth_event("login", user_id=user.id, user_email=user.email, success=False, 
                          details={"reason": "incorrect_password", "endpoint": "login-json"})
        else:
            log_auth_event("login", user_email=user_data.email, success=False,
                          details={"reason": "user_not_found", "endpoint": "login-json"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for verification link."
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Successful login
    handle_successful_login(db, user)
    log_auth_event("login", user_id=user.id, user_email=user.email, success=True,
                  details={"endpoint": "login-json"})
    
    return _create_token_response(user, db)


@router.post("/refresh", response_model=Token)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    user = verify_refresh_token(db, request.refresh_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Check if user is still active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Revoke old refresh token (token rotation)
    revoke_refresh_token(db, request.refresh_token)
    
    # Create new tokens
    return _create_token_response(user, db)


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request password reset email"""
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success to prevent email enumeration
    if user:
        await send_password_reset_email(db, user)
    
    return {"message": "If the email exists, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token"""
    user = verify_password_reset_token(db, request.token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )
    
    # Validate new password strength
    is_valid, error_msg = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password
    user.password_hash = get_password_hash(request.new_password)
    
    # Revoke all refresh tokens for security
    revoke_all_user_refresh_tokens(db, user.id)
    
    # Mark token as used
    mark_password_reset_token_used(db, request.token)
    
    db.commit()
    
    return {"message": "Password reset successfully"}


@router.post("/verify-email")
def verify_email(request: EmailVerificationRequest, db: Session = Depends(get_db)):
    """Verify email address using token"""
    user = verify_email_token(db, request.token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resend email verification"""
    user = current_user
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    await send_verification_email(db, user)
    
    return {"message": "Verification email sent"}


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password"
        )
    
    # Validate new password strength
    is_valid, error_msg = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password
    current_user.password_hash = get_password_hash(request.new_password)
    
    # Revoke all refresh tokens for security
    revoke_all_user_refresh_tokens(db, current_user.id)
    
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
def logout(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Logout by revoking refresh token"""
    revoke_refresh_token(db, request.refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user
