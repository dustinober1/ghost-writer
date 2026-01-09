"""
Admin routes for system management.
Requires admin privileges.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.database import (
    get_db, User, WritingSample, Fingerprint, AnalysisResult,
    RefreshToken
)
from app.utils.auth import get_current_user
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["admin"])


# Pydantic models for admin responses
class UserAdminResponse(BaseModel):
    id: int
    email: str
    email_verified: bool
    is_active: bool
    is_admin: bool
    created_at: datetime
    failed_login_attempts: int
    locked_until: Optional[datetime]
    sample_count: int
    analysis_count: int
    has_fingerprint: bool

    class Config:
        from_attributes = True


class SystemStatsResponse(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    total_analyses: int
    total_samples: int
    total_fingerprints: int
    analyses_last_24h: int
    analyses_last_7d: int
    new_users_last_24h: int
    new_users_last_7d: int


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin privileges."""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/stats", response_model=SystemStatsResponse)
def get_system_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system-wide statistics."""
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    
    return SystemStatsResponse(
        total_users=db.query(User).count(),
        active_users=db.query(User).filter(User.is_active == True).count(),
        verified_users=db.query(User).filter(User.email_verified == True).count(),
        total_analyses=db.query(AnalysisResult).count(),
        total_samples=db.query(WritingSample).count(),
        total_fingerprints=db.query(Fingerprint).count(),
        analyses_last_24h=db.query(AnalysisResult).filter(
            AnalysisResult.created_at >= day_ago
        ).count(),
        analyses_last_7d=db.query(AnalysisResult).filter(
            AnalysisResult.created_at >= week_ago
        ).count(),
        new_users_last_24h=db.query(User).filter(
            User.created_at >= day_ago
        ).count(),
        new_users_last_7d=db.query(User).filter(
            User.created_at >= week_ago
        ).count(),
    )


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    active_only: bool = False,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users with pagination."""
    query = db.query(User)
    
    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    total = query.count()
    users = query.order_by(desc(User.created_at)).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    # Enrich with stats
    user_list = []
    for user in users:
        sample_count = db.query(WritingSample).filter(
            WritingSample.user_id == user.id
        ).count()
        analysis_count = db.query(AnalysisResult).filter(
            AnalysisResult.user_id == user.id
        ).count()
        has_fingerprint = db.query(Fingerprint).filter(
            Fingerprint.user_id == user.id
        ).first() is not None
        
        user_list.append({
            "id": user.id,
            "email": user.email,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "is_admin": getattr(user, 'is_admin', False),
            "created_at": user.created_at.isoformat(),
            "failed_login_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until.isoformat() if user.locked_until else None,
            "sample_count": sample_count,
            "analysis_count": analysis_count,
            "has_fingerprint": has_fingerprint,
        })
    
    return {
        "users": user_list,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }


@router.get("/users/{user_id}")
def get_user_details(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed information about a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user statistics
    samples = db.query(WritingSample).filter(WritingSample.user_id == user_id).all()
    analyses = db.query(AnalysisResult).filter(AnalysisResult.user_id == user_id).order_by(
        desc(AnalysisResult.created_at)
    ).limit(10).all()
    fingerprint = db.query(Fingerprint).filter(Fingerprint.user_id == user_id).first()
    active_sessions = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).count()
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "is_admin": getattr(user, 'is_admin', False),
            "created_at": user.created_at.isoformat(),
            "failed_login_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until.isoformat() if user.locked_until else None,
        },
        "stats": {
            "sample_count": len(samples),
            "analysis_count": db.query(AnalysisResult).filter(
                AnalysisResult.user_id == user_id
            ).count(),
            "has_fingerprint": fingerprint is not None,
            "fingerprint_updated": fingerprint.updated_at.isoformat() if fingerprint else None,
            "active_sessions": active_sessions,
        },
        "recent_analyses": [
            {
                "id": a.id,
                "created_at": a.created_at.isoformat(),
                "overall_ai_probability": a.overall_ai_probability,
                "text_preview": a.text_content[:100] + "..." if len(a.text_content) > 100 else a.text_content
            }
            for a in analyses
        ]
    }


@router.post("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Activate a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    
    return {"message": f"User {user.email} activated"}


@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = False
    
    # Revoke all sessions
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id
    ).update({"revoked": True})
    
    db.commit()
    
    return {"message": f"User {user.email} deactivated"}


@router.post("/users/{user_id}/unlock")
def unlock_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Unlock a locked user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    
    return {"message": f"User {user.email} unlocked"}


@router.post("/users/{user_id}/verify-email")
def verify_user_email(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Manually verify a user's email."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.email_verified = True
    db.commit()
    
    return {"message": f"Email verified for {user.email}"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a user and all their data."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )
    
    # Delete all user data
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
    db.query(AnalysisResult).filter(AnalysisResult.user_id == user_id).delete()
    db.query(Fingerprint).filter(Fingerprint.user_id == user_id).delete()
    db.query(WritingSample).filter(WritingSample.user_id == user_id).delete()
    db.query(User).filter(User.id == user_id).delete()
    
    db.commit()
    
    return {"message": f"User deleted"}


@router.get("/analyses")
def list_recent_analyses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List recent analyses across all users."""
    query = db.query(AnalysisResult).join(User)
    
    if user_id:
        query = query.filter(AnalysisResult.user_id == user_id)
    
    total = query.count()
    analyses = query.order_by(desc(AnalysisResult.created_at)).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    return {
        "analyses": [
            {
                "id": a.id,
                "user_id": a.user_id,
                "user_email": a.user.email,
                "created_at": a.created_at.isoformat(),
                "overall_ai_probability": a.overall_ai_probability,
                "text_preview": a.text_content[:100] + "..." if len(a.text_content) > 100 else a.text_content
            }
            for a in analyses
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }
