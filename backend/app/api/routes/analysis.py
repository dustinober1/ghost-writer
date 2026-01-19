from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.models.database import get_db, User, AnalysisResult
from app.models.schemas import AnalysisRequest, AnalysisResponse, HeatMapData, TextSegment
from app.services.analysis_service import get_analysis_service
from app.services.fingerprint_service import get_fingerprint_service
from app.utils.auth import get_current_user
from app.middleware.rate_limit import analysis_rate_limit
from app.middleware.input_sanitization import sanitize_text
from app.middleware.audit_logging import log_analysis_event
from app.utils.file_validation import validate_text_length
from datetime import datetime

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
@analysis_rate_limit
def analyze_text(
    request: AnalysisRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze text and return heat map data with AI probability scores.
    
    Uses Ollama embeddings combined with stylometric features for
    accurate AI probability estimation.
    """
    try:
        # Validate and sanitize input
        validate_text_length(request.text)
        sanitized_text = sanitize_text(request.text, max_length=100000)
        
        analysis_service = get_analysis_service()
        fingerprint_service = get_fingerprint_service()
        
        # Get user's fingerprint if available
        user_fingerprint = fingerprint_service.get_user_fingerprint(db, current_user.id)
        fingerprint_dict = None
        if user_fingerprint:
            fingerprint_dict = {
                "feature_vector": user_fingerprint.feature_vector,
                "model_version": user_fingerprint.model_version
            }
        
        # Analyze text (embedder removed - always uses Ollama)
        result = analysis_service.analyze_text(
            text=sanitized_text,
            granularity=request.granularity,
            user_fingerprint=fingerprint_dict,
        )
        
        # Convert to response format
        segments = [
            TextSegment(
                text=seg["text"],
                ai_probability=seg["ai_probability"],
                start_index=seg["start_index"],
                end_index=seg["end_index"],
                confidence_level=seg["confidence_level"]
            )
            for seg in result["segments"]
        ]

        heat_map_data = HeatMapData(
            segments=segments,
            overall_ai_probability=result["overall_ai_probability"],
            confidence_distribution=result.get("confidence_distribution")
        )
        
        # Save analysis result
        analysis_result = AnalysisResult(
            user_id=current_user.id,
            text_content=sanitized_text,
            heat_map_data={
                "segments": [seg.dict() for seg in segments],
                "overall_ai_probability": result["overall_ai_probability"],
                "confidence_distribution": result.get("confidence_distribution")
            },
            overall_ai_probability=str(result["overall_ai_probability"])
        )
        db.add(analysis_result)
        db.commit()
        db.refresh(analysis_result)
        
        # Log analysis event
        log_analysis_event(
            user_id=current_user.id,
            text_length=len(sanitized_text),
            analysis_id=analysis_result.id,
            ai_probability=result["overall_ai_probability"]
        )
        
        return AnalysisResponse(
            heat_map_data=heat_map_data,
            analysis_id=analysis_result.id,
            created_at=analysis_result.created_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing text: {str(e)}"
        )
