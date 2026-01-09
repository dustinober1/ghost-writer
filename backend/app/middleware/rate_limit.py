"""
Rate limiting middleware using slowapi.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import os

# Initialize limiter with Redis if available, otherwise use in-memory storage
REDIS_URL = os.getenv("REDIS_URL", None)

if REDIS_URL:
    try:
        from slowapi.middleware import SlowAPIMiddleware
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=REDIS_URL,
            default_limits=["1000 per hour"]
        )
    except Exception:
        # Fallback to in-memory if Redis unavailable
        limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per hour"])
else:
    limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per hour"])


def get_rate_limiter():
    """Get the rate limiter instance"""
    return limiter


# Rate limit decorators for different endpoints
auth_rate_limit = limiter.limit("5 per minute")
analysis_rate_limit = limiter.limit("30 per minute")
rewrite_rate_limit = limiter.limit("10 per minute")
general_rate_limit = limiter.limit("100 per minute")


def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handler for rate limit exceeded exceptions"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}"
        }
    )
