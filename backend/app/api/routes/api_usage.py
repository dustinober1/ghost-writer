from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import get_db, User
from app.utils.auth import get_current_user, get_api_key_user
from app.middleware.rate_limit import get_tiered_rate_limiter

router = APIRouter(prefix="/api", tags=["usage"])


def get_current_user_for_api(
    token: Optional[User] = Depends(get_current_user),
    api_key_user: Optional[User] = Depends(get_api_key_user),
) -> Optional[User]:
    """Get authenticated user from either JWT token or API key"""
    if token:
        return token
    if api_key_user:
        return api_key_user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )


@router.get("/usage")
async def get_usage_metrics(
    current_user: User = Depends(get_current_user_for_api),
    db: Session = Depends(get_db)
):
    """
    Get current API usage metrics for the authenticated user.

    Returns:
    - Current tier
    - Rate limits for the tier
    - Usage statistics (requests today, this minute)
    - Remaining quota
    """
    # Get user's tier
    tier = current_user.tier if hasattr(current_user, 'tier') else "free"

    # Get usage stats from rate limiter
    limiter = get_tiered_rate_limiter()
    stats = limiter.get_usage_stats(current_user.id, tier)

    return stats


@router.get("/limits")
async def get_rate_limits(
    current_user: User = Depends(get_current_user_for_api),
):
    """
    Get rate limit information for the current user.

    Returns the rate limits that apply to the user's tier.
    """
    tier = current_user.tier if hasattr(current_user, 'tier') else "free"

    from app.middleware.rate_limit import TIER_LIMITS

    return {
        "tier": tier,
        "limits": TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    }
