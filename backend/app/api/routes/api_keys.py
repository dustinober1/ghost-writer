from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import secrets
import hashlib

from app.models.database import get_db, User, ApiKey
from app.utils.auth import get_current_user
from pydantic import BaseModel


router = APIRouter(prefix="/api/keys", tags=["api-keys"])


# Pydantic schemas for API keys
class ApiKeyCreate(BaseModel):
    name: str
    expires_in_days: Optional[int] = None


class ApiKeyResponse(BaseModel):
    id: int
    key_prefix: str
    name: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None


class ApiKeyCreatedResponse(BaseModel):
    key: str  # Only shown on creation
    key_prefix: str
    name: str
    expires_at: Optional[datetime] = None


@router.post("", response_model=ApiKeyCreatedResponse)
async def create_api_key(
    name: str = Body(..., embed=True, min_length=1, max_length=100),
    expires_in_days: Optional[int] = Body(None, gt=0, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new API key for the current user. Returns the full key (only shown once)."""
    # Check user's API key limit (free: 3 keys, pro: 10, enterprise: unlimited)
    existing_keys = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id,
        ApiKey.is_active == True
    ).count()

    tier = current_user.tier if hasattr(current_user, "tier") else "free"
    max_keys = {"free": 3, "pro": 10, "enterprise": 9999}.get(tier, 3)

    if existing_keys >= max_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum API key limit reached ({max_keys} keys for {tier} tier)"
        )

    # Generate secure random key (32 bytes = 43 chars in urlsafe encoding)
    raw_key = f"gw_{secrets.token_urlsafe(32)}"

    # Hash for storage (SHA-256)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    # Store prefix for identification (first 8 chars after prefix)
    key_prefix = raw_key[:8]

    # Calculate expiration
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    # Save to database
    api_key = ApiKey(
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
        expires_at=expires_at
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    # Return full key only on creation
    return ApiKeyCreatedResponse(
        key=raw_key,
        key_prefix=key_prefix,
        name=name,
        expires_at=expires_at
    )


@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all API keys for the current user (prefixes only, never full keys)."""
    api_keys = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id
    ).order_by(ApiKey.created_at.desc()).all()

    return [
        ApiKeyResponse(
            id=key.id,
            key_prefix=key.key_prefix,
            name=key.name,
            is_active=key.is_active,
            created_at=key.created_at,
            expires_at=key.expires_at,
            last_used=key.last_used
        )
        for key in api_keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete (revoke) an API key."""
    api_key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.user_id == current_user.id
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    db.delete(api_key)
    db.commit()

    return None
