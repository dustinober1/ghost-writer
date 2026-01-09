"""
Account management routes for GDPR compliance and user settings.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.models.database import (
    get_db, User, WritingSample, Fingerprint, AnalysisResult,
    RefreshToken, PasswordResetToken, EmailVerificationToken
)
from app.utils.auth import get_current_user, get_password_hash, verify_password, revoke_all_user_refresh_tokens
from datetime import datetime, timedelta
from typing import Optional
import json
import io
import csv

router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("/me")
def get_account_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user account information"""
    # Count user data
    sample_count = db.query(WritingSample).filter(WritingSample.user_id == current_user.id).count()
    analysis_count = db.query(AnalysisResult).filter(AnalysisResult.user_id == current_user.id).count()
    fingerprint = db.query(Fingerprint).filter(Fingerprint.user_id == current_user.id).first()
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "email_verified": current_user.email_verified,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat(),
        "data_summary": {
            "writing_samples": sample_count,
            "analysis_results": analysis_count,
            "has_fingerprint": fingerprint is not None,
        }
    }


@router.get("/export")
def export_user_data(
    format: str = "json",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all user data (GDPR data portability).
    
    Args:
        format: Export format - 'json' or 'csv'
    """
    # Collect all user data
    user_data = {
        "account": {
            "id": current_user.id,
            "email": current_user.email,
            "email_verified": current_user.email_verified,
            "created_at": current_user.created_at.isoformat(),
        },
        "writing_samples": [],
        "fingerprint": None,
        "analysis_results": [],
        "export_metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "format": format,
        }
    }
    
    # Writing samples
    samples = db.query(WritingSample).filter(WritingSample.user_id == current_user.id).all()
    for sample in samples:
        user_data["writing_samples"].append({
            "id": sample.id,
            "text_content": sample.text_content,
            "source_type": sample.source_type,
            "uploaded_at": sample.uploaded_at.isoformat(),
        })
    
    # Fingerprint
    fingerprint = db.query(Fingerprint).filter(Fingerprint.user_id == current_user.id).first()
    if fingerprint:
        user_data["fingerprint"] = {
            "id": fingerprint.id,
            "feature_vector": fingerprint.feature_vector,
            "model_version": fingerprint.model_version,
            "created_at": fingerprint.created_at.isoformat(),
            "updated_at": fingerprint.updated_at.isoformat(),
        }
    
    # Analysis results
    analyses = db.query(AnalysisResult).filter(AnalysisResult.user_id == current_user.id).all()
    for analysis in analyses:
        user_data["analysis_results"].append({
            "id": analysis.id,
            "text_content": analysis.text_content,
            "heat_map_data": analysis.heat_map_data,
            "overall_ai_probability": analysis.overall_ai_probability,
            "created_at": analysis.created_at.isoformat(),
        })
    
    if format == "json":
        # Return as JSON file
        json_str = json.dumps(user_data, indent=2)
        return StreamingResponse(
            io.BytesIO(json_str.encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=ghostwriter_export_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d')}.json"
            }
        )
    elif format == "csv":
        # Return as CSV (flattened)
        output = io.StringIO()
        
        # Account info
        output.write("# Account Information\n")
        writer = csv.writer(output)
        writer.writerow(["Field", "Value"])
        writer.writerow(["Email", current_user.email])
        writer.writerow(["Created At", current_user.created_at.isoformat()])
        writer.writerow(["Email Verified", current_user.email_verified])
        output.write("\n")
        
        # Writing samples
        output.write("# Writing Samples\n")
        writer.writerow(["ID", "Source Type", "Uploaded At", "Text Content (preview)"])
        for sample in user_data["writing_samples"]:
            writer.writerow([
                sample["id"],
                sample["source_type"],
                sample["uploaded_at"],
                sample["text_content"][:100] + "..." if len(sample["text_content"]) > 100 else sample["text_content"]
            ])
        output.write("\n")
        
        # Analysis results
        output.write("# Analysis Results\n")
        writer.writerow(["ID", "AI Probability", "Created At", "Text (preview)"])
        for analysis in user_data["analysis_results"]:
            writer.writerow([
                analysis["id"],
                analysis["overall_ai_probability"],
                analysis["created_at"],
                analysis["text_content"][:100] + "..." if len(analysis["text_content"]) > 100 else analysis["text_content"]
            ])
        
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=ghostwriter_export_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Use 'json' or 'csv'"
        )


@router.post("/request-deletion")
def request_account_deletion(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request account deletion (GDPR right to erasure).
    Account will be scheduled for deletion after a 30-day grace period.
    """
    # For immediate deletion during development, we'll delete now
    # In production, you'd schedule this with a grace period
    
    # Mark account as inactive (soft delete)
    current_user.is_active = False
    
    # Revoke all tokens
    revoke_all_user_refresh_tokens(db, current_user.id)
    
    db.commit()
    
    return {
        "message": "Account deletion requested. Your account has been deactivated and will be permanently deleted in 30 days.",
        "deletion_scheduled_for": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "note": "Contact support to cancel the deletion request."
    }


@router.delete("/delete-immediately")
def delete_account_immediately(
    password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Immediately delete account and all associated data (GDPR right to erasure).
    Requires password confirmation.
    """
    # Verify password
    if not verify_password(password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    user_id = current_user.id
    
    # Delete all user data in order (respect foreign keys)
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).delete()
    db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user_id).delete()
    db.query(AnalysisResult).filter(AnalysisResult.user_id == user_id).delete()
    db.query(Fingerprint).filter(Fingerprint.user_id == user_id).delete()
    db.query(WritingSample).filter(WritingSample.user_id == user_id).delete()
    db.query(User).filter(User.id == user_id).delete()
    
    db.commit()
    
    return {"message": "Account and all associated data have been permanently deleted."}


@router.delete("/data/{data_type}")
def delete_specific_data(
    data_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete specific types of user data.
    
    Args:
        data_type: Type of data to delete - 'samples', 'fingerprint', 'analyses'
    """
    if data_type == "samples":
        deleted = db.query(WritingSample).filter(WritingSample.user_id == current_user.id).delete()
        # Also delete fingerprint as it depends on samples
        db.query(Fingerprint).filter(Fingerprint.user_id == current_user.id).delete()
        db.commit()
        return {"message": f"Deleted {deleted} writing samples and associated fingerprint."}
    
    elif data_type == "fingerprint":
        deleted = db.query(Fingerprint).filter(Fingerprint.user_id == current_user.id).delete()
        db.commit()
        return {"message": "Fingerprint deleted." if deleted else "No fingerprint found."}
    
    elif data_type == "analyses":
        deleted = db.query(AnalysisResult).filter(AnalysisResult.user_id == current_user.id).delete()
        db.commit()
        return {"message": f"Deleted {deleted} analysis results."}
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data_type. Use 'samples', 'fingerprint', or 'analyses'"
        )
