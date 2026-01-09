"""
Email service for sending authentication and notification emails.
In production, configure with actual SMTP settings.
For development, emails can be logged or sent via a service like SendGrid.
"""
import os
import secrets
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database import EmailVerificationToken, PasswordResetToken, User
from dotenv import load_dotenv

load_dotenv()

# Email configuration
SMTP_ENABLED = os.getenv("SMTP_ENABLED", "false").lower() == "true"
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@ghostwriter.local")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)


def create_email_verification_token(db: Session, user_id: int) -> str:
    """Create and store an email verification token"""
    # Delete existing token if any
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user_id
    ).delete()
    
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    verification_token = EmailVerificationToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(verification_token)
    db.commit()
    
    return token


def create_password_reset_token(db: Session, user_id: int) -> str:
    """Create and store a password reset token"""
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    reset_token = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()
    
    return token


def verify_email_token(db: Session, token: str) -> Optional[User]:
    """Verify and use an email verification token"""
    verification = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token == token,
        EmailVerificationToken.expires_at > datetime.utcnow()
    ).first()
    
    if not verification:
        return None
    
    user = db.query(User).filter(User.id == verification.user_id).first()
    if not user:
        return None
    
    # Mark email as verified
    user.email_verified = True
    db.delete(verification)
    db.commit()
    
    return user


def verify_password_reset_token(db: Session, token: str) -> Optional[User]:
    """Verify a password reset token (don't mark as used yet)"""
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.expires_at > datetime.utcnow(),
        PasswordResetToken.used == False
    ).first()
    
    if not reset:
        return None
    
    return db.query(User).filter(User.id == reset.user_id).first()


def mark_password_reset_token_used(db: Session, token: str):
    """Mark a password reset token as used"""
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()
    
    if reset:
        reset.used = True
        db.commit()


async def send_email(to: str, subject: str, body: str, html_body: Optional[str] = None):
    """
    Send an email. In development, logs to console.
    In production, configure with actual SMTP or email service.
    """
    if SMTP_ENABLED:
        # Use fastapi-mail or similar
        try:
            from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
            
            conf = ConnectionConfig(
                MAIL_USERNAME=SMTP_USER,
                MAIL_PASSWORD=SMTP_PASSWORD,
                MAIL_FROM=SMTP_FROM,
                MAIL_PORT=SMTP_PORT,
                MAIL_SERVER=SMTP_HOST,
                MAIL_STARTTLS=True,
                MAIL_SSL_TLS=False,
                USE_CREDENTIALS=True,
            )
            
            message = MessageSchema(
                subject=subject,
                recipients=[to],
                body=body,
                subtype="html" if html_body else "plain",
            )
            
            if html_body:
                message.body = html_body
            
            fm = FastMail(conf)
            await fm.send_message(message)
        except Exception as e:
            print(f"Error sending email: {e}")
            # Fall back to logging
            print(f"[EMAIL] To: {to}\nSubject: {subject}\nBody:\n{body}")
    else:
        # Development mode - log to console
        print(f"\n{'='*60}")
        print(f"[EMAIL] To: {to}")
        print(f"Subject: {subject}")
        print(f"{'='*60}")
        print(body)
        if html_body:
            print(f"\nHTML Body:\n{html_body}")
        print(f"{'='*60}\n")


async def send_verification_email(db: Session, user: User):
    """Send email verification email"""
    token = create_email_verification_token(db, user.id)
    verification_url = f"{FRONTEND_URL}/verify-email?token={token}"
    
    subject = "Verify your email address"
    html_body = f"""
    <html>
    <body>
        <h2>Welcome to Ghostwriter!</h2>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{verification_url}">Verify Email</a></p>
        <p>Or copy and paste this URL into your browser:</p>
        <p>{verification_url}</p>
        <p>This link will expire in 7 days.</p>
        <p>If you didn't create an account, you can safely ignore this email.</p>
    </body>
    </html>
    """
    
    await send_email(user.email, subject, "", html_body)


async def send_password_reset_email(db: Session, user: User):
    """Send password reset email"""
    token = create_password_reset_token(db, user.id)
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    
    subject = "Reset your password"
    html_body = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>You requested to reset your password. Click the link below to reset it:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>Or copy and paste this URL into your browser:</p>
        <p>{reset_url}</p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request a password reset, you can safely ignore this email.</p>
    </body>
    </html>
    """
    
    await send_email(user.email, subject, "", html_body)
