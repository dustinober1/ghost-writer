"""
Tiered rate limiting middleware using Redis for user-based quota tracking.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import redis
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Tier configuration: requests per day
TIER_LIMITS = {
    "free": {"requests_per_day": 100, "requests_per_minute": 10},
    "pro": {"requests_per_day": 10000, "requests_per_minute": 100},
    "enterprise": {"requests_per_day": 100000, "requests_per_minute": 500},
}

# Initialize Redis client
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    # Test connection
    redis_client.ping()
except Exception:
    redis_client = None
    print("Warning: Redis not available, rate limiting will be degraded")


def get_user_tier(user) -> str:
    """Get user's subscription tier from user.tier field"""
    if hasattr(user, 'tier') and user.tier:
        return user.tier
    return "free"


def get_rate_limit_key(user_id: int, limit_type: str) -> str:
    """Generate Redis key for rate limit tracking"""
    now = datetime.utcnow()
    if limit_type == "day":
        # Use current date for daily key (resets at midnight UTC)
        date_key = now.strftime("%Y-%m-%d")
        return f"ratelimit:user:{user_id}:day:{date_key}"
    else:  # minute
        # Use current hour:minute for minute key
        minute_key = now.strftime("%Y-%m-%d:%H:%M")
        return f"ratelimit:user:{user_id}:min:{minute_key}"


def check_rate_limit(user_id: int, tier: str) -> Dict[str, Any]:
    """
    Check and increment rate limits for a user.

    Returns dict with:
    - allowed: bool (whether request is allowed)
    - remaining_day: int (requests remaining today)
    - remaining_min: int (requests remaining this minute)
    - reset_time: str (ISO datetime when daily limit resets)
    - limit_day: int (daily limit)
    - limit_min: int (minute limit)
    """
    if not redis_client:
        # Redis unavailable - allow all (degraded mode)
        return {
            "allowed": True,
            "remaining_day": 9999,
            "remaining_min": 9999,
            "reset_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "limit_day": 9999,
            "limit_min": 9999
        }

    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    day_key = get_rate_limit_key(user_id, "day")
    min_key = get_rate_limit_key(user_id, "minute")

    # Use Redis pipeline for atomic operations
    pipe = redis_client.pipeline()

    # Increment counters
    pipe.incr(day_key)
    pipe.incr(min_key)

    # Set expiration (daily key expires at end of day, minute key expires in 60s)
    # Calculate seconds until midnight UTC
    now = datetime.utcnow()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_until_midnight = int((midnight - now).total_seconds())

    pipe.expire(day_key, seconds_until_midnight)
    pipe.expire(min_key, 60)

    # Get current counts
    results = pipe.execute()
    day_count = min(results[0], limits["requests_per_day"])
    min_count = min(results[1], limits["requests_per_minute"])

    remaining_day = max(0, limits["requests_per_day"] - day_count)
    remaining_min = max(0, limits["requests_per_minute"] - min_count)

    # Check if limits exceeded
    day_exceeded = day_count > limits["requests_per_day"]
    min_exceeded = min_count > limits["requests_per_minute"]

    if min_exceeded:
        return {
            "allowed": False,
            "remaining_day": remaining_day,
            "remaining_min": 0,
            "reset_time": (now + timedelta(seconds=60)).isoformat(),
            "limit_day": limits["requests_per_day"],
            "limit_min": limits["requests_per_minute"],
            "error": "minute_limit_exceeded"
        }

    if day_exceeded:
        return {
            "allowed": False,
            "remaining_day": 0,
            "remaining_min": remaining_min,
            "reset_time": midnight.isoformat(),
            "limit_day": limits["requests_per_day"],
            "limit_min": limits["requests_per_minute"],
            "error": "day_limit_exceeded"
        }

    return {
        "allowed": True,
        "remaining_day": remaining_day,
        "remaining_min": remaining_min,
        "reset_time": midnight.isoformat(),
        "limit_day": limits["requests_per_day"],
        "limit_min": limits["requests_per_minute"]
    }


def add_rate_limit_headers(response: JSONResponse, rate_info: Dict[str, Any]):
    """Add rate limit headers to response"""
    response.headers["X-RateLimit-Limit-Day"] = str(rate_info["limit_day"])
    response.headers["X-RateLimit-Remaining-Day"] = str(rate_info["remaining_day"])
    response.headers["X-RateLimit-Limit-Minute"] = str(rate_info["limit_min"])
    response.headers["X-RateLimit-Remaining-Minute"] = str(rate_info["remaining_min"])
    response.headers["X-RateLimit-Reset"] = rate_info["reset_time"]
    return response


class TieredRateLimiter:
    """Rate limiter that works with user-based authentication"""

    def __init__(self):
        self.redis_client = redis_client

    def check_request(self, request: Request, user_id: int, tier: str) -> Dict[str, Any]:
        """Check if request should be rate limited"""
        return check_rate_limit(user_id, tier)

    def get_usage_stats(self, user_id: int, tier: str) -> Dict[str, Any]:
        """Get current usage statistics for a user"""
        if not redis_client:
            return {
                "tier": tier,
                "limits": TIER_LIMITS.get(tier, TIER_LIMITS["free"]),
                "usage": {"requests_today": 0, "requests_this_minute": 0},
                "remaining": {"today": 0, "this_minute": 0}
            }

        limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        day_key = get_rate_limit_key(user_id, "day")
        min_key = get_rate_limit_key(user_id, "minute")

        day_count = int(redis_client.get(day_key) or 0)
        min_count = int(redis_client.get(min_key) or 0)

        return {
            "tier": tier,
            "limits": limits,
            "usage": {
                "requests_today": day_count,
                "requests_this_minute": min_count
            },
            "remaining": {
                "today": max(0, limits["requests_per_day"] - day_count),
                "this_minute": max(0, limits["requests_per_minute"] - min_count)
            }
        }


# Global limiter instance
tiered_limiter = TieredRateLimiter()


# Maintain backward compatibility with existing SlowAPI limiter
# for IP-based rate limiting on public endpoints
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=REDIS_URL if redis_client else None,
    default_limits=["1000 per hour"]
)


def get_rate_limiter():
    """Get the rate limiter instance"""
    return limiter


def get_tiered_rate_limiter():
    """Get the tiered rate limiter instance"""
    return tiered_limiter


# Legacy rate limit decorators (for endpoints not using tiered limiting)
auth_rate_limit = limiter.limit("5 per minute")
analysis_rate_limit = limiter.limit("30 per minute")
rewrite_rate_limit = limiter.limit("10 per minute")
general_rate_limit = limiter.limit("100 per minute")


def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handler for SlowAPI rate limit exceeded exceptions"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}"
        },
        headers={
            "Retry-After": "60"
        }
    )
