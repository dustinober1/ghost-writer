"""
Celery tasks for background processing.
"""
from app.celery_app import celery_app
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


@celery_app.task(bind=True)
def analyze_text_async(self, text: str, user_id: int, granularity: str = "sentence"):
    """
    Background task for analyzing large texts.
    
    Args:
        text: Text to analyze
        user_id: User ID
        granularity: Analysis granularity
    """
    from app.services.analysis_service import get_analysis_service
    
    try:
        logger.info("Starting async analysis", task_id=self.request.id, user_id=user_id)
        
        analysis_service = get_analysis_service()
        result = analysis_service.analyze_text(
            text=text,
            granularity=granularity,
            user_fingerprint=None
        )
        
        logger.info("Async analysis completed", task_id=self.request.id, user_id=user_id)
        return result
        
    except Exception as e:
        logger.error("Async analysis failed", task_id=self.request.id, error=str(e))
        raise


@celery_app.task
def cleanup_expired_tokens():
    """Clean up expired refresh tokens and password reset tokens."""
    from app.models.database import SessionLocal, RefreshToken, PasswordResetToken, EmailVerificationToken
    
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Delete expired refresh tokens
        expired_refresh = db.query(RefreshToken).filter(
            RefreshToken.expires_at < now
        ).delete()
        
        # Delete expired password reset tokens
        expired_reset = db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at < now
        ).delete()
        
        # Delete expired email verification tokens
        expired_email = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.expires_at < now
        ).delete()
        
        db.commit()
        
        logger.info(
            "Token cleanup completed",
            expired_refresh=expired_refresh,
            expired_reset=expired_reset,
            expired_email=expired_email
        )
        
    except Exception as e:
        logger.error("Token cleanup failed", error=str(e))
        db.rollback()
    finally:
        db.close()


@celery_app.task
def cleanup_old_analysis_results():
    """Clean up old analysis results based on retention policy."""
    from app.models.database import SessionLocal, AnalysisResult
    import os
    
    retention_days = int(os.getenv("ANALYSIS_RETENTION_DAYS", "90"))
    
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        deleted = db.query(AnalysisResult).filter(
            AnalysisResult.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(
            "Analysis cleanup completed",
            deleted_count=deleted,
            retention_days=retention_days
        )
        
    except Exception as e:
        logger.error("Analysis cleanup failed", error=str(e))
        db.rollback()
    finally:
        db.close()


@celery_app.task
def send_email_async(to: str, subject: str, body: str, html_body: str = None):
    """Send email asynchronously."""
    import asyncio
    from app.utils.email import send_email
    
    try:
        asyncio.run(send_email(to, subject, body, html_body))
        logger.info("Email sent", to=to, subject=subject)
    except Exception as e:
        logger.error("Email sending failed", to=to, error=str(e))
        raise
