from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.models.database import get_db, User
from app.models.schemas import RewriteRequest, RewriteResponse
from app.services.fingerprint_service import get_fingerprint_service
from app.ml.dspy_rewriter import get_dspy_rewriter
from app.utils.auth import get_current_user
from app.middleware.rate_limit import rewrite_rate_limit
from app.middleware.input_sanitization import sanitize_text
from app.utils.file_validation import validate_text_length
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rewrite", tags=["rewrite"])


@router.post("/rewrite", response_model=RewriteResponse)
@rewrite_rate_limit
def rewrite_text(
    request: RewriteRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rewrite text to match user's style using Ollama.
    """
    try:
        # Validate and sanitize input
        validate_text_length(request.text)
        sanitized_text = sanitize_text(request.text)
        
        rewriter = get_dspy_rewriter()
        fingerprint_service = get_fingerprint_service()
        
        # Generate style guidance
        if request.target_style:
            # Use provided style guidance
            style_guidance = sanitize_text(request.target_style)
            rewritten_text = rewriter.rewrite_text(
                text=sanitized_text,
                style_guidance=style_guidance
            )
        else:
            # Get user's fingerprint for style matching
            user_fingerprint = fingerprint_service.get_user_fingerprint(db, current_user.id)
            
            if not user_fingerprint:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fingerprint found. Please upload writing samples and generate a fingerprint first, or provide a target_style."
                )
            
            fingerprint_dict = {
                "feature_vector": user_fingerprint.feature_vector,
                "model_version": user_fingerprint.model_version
            }
            
            # Use fingerprint to generate style guidance
            rewritten_text = rewriter.rewrite_with_fingerprint(
                text=sanitized_text,
                fingerprint=fingerprint_dict
            )
        
        # Sanitize output
        rewritten_text = sanitize_text(rewritten_text)
        
        # For now, we'll just return the result
        # In a full implementation, you might want to save rewrite history
        return RewriteResponse(
            original_text=sanitized_text,
            rewritten_text=rewritten_text,
            rewrite_id=0,  # Would be from database in full implementation
            created_at=datetime.utcnow()
        )
    
    except ValueError as e:
        logger.error(f"ValueError in rewrite endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Exception in rewrite endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rewriting text: {str(e)}"
        )


@router.get("/history")
def get_rewrite_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get rewriting history for current user.
    (Placeholder - would need a RewriteHistory table in full implementation)
    """
    # This would query a RewriteHistory table in a full implementation
    return {"history": []}
