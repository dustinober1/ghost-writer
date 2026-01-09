"""
Audit logging middleware to log security-relevant events.
"""
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from datetime import datetime
import uuid

logger = structlog.get_logger()


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Log security-relevant events for audit trail"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get user info if authenticated
        user_email = None
        user_id = None
        try:
            # Try to get user from token if present
            if "authorization" in request.headers:
                # Extract user info from token (simplified)
                # In production, you'd decode the JWT properly
                pass
        except Exception:
            pass
        
        start_time = time.time()
        
        # Log request
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=request.client.host if request.client else None,
            user_email=user_email,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat(),
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            user_email=user_email,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat(),
        )
        
        # Log security-relevant events
        if response.status_code in [401, 403, 423]:
            logger.warning(
                "security_event",
                request_id=request_id,
                event_type="authentication_failure" if response.status_code == 401 else "authorization_failure",
                path=request.url.path,
                client_ip=request.client.host if request.client else None,
                status_code=response.status_code,
                timestamp=datetime.utcnow().isoformat(),
            )
        
        return response


def log_auth_event(event_type: str, user_id: int = None, user_email: str = None, 
                   success: bool = True, details: dict = None):
    """
    Log authentication-related events.
    
    Args:
        event_type: Type of event (login, logout, register, password_reset, etc.)
        user_id: User ID if available
        user_email: User email if available
        success: Whether the event was successful
        details: Additional details
    """
    logger.info(
        "auth_event",
        event_type=event_type,
        user_id=user_id,
        user_email=user_email,
        success=success,
        details=details or {},
        timestamp=datetime.utcnow().isoformat(),
    )


def log_analysis_event(user_id: int, text_length: int, analysis_id: int = None, 
                       ai_probability: float = None):
    """Log analysis request for audit trail"""
    logger.info(
        "analysis_event",
        user_id=user_id,
        text_length=text_length,
        analysis_id=analysis_id,
        ai_probability=ai_probability,
        timestamp=datetime.utcnow().isoformat(),
    )
