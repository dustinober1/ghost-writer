from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db, User, AnalysisResult
from app.models.schemas import AnalysisRequest, AnalysisResponse, HeatMapData, TextSegment
from app.services.analysis_service import get_analysis_service
from app.services.fingerprint_service import get_fingerprint_service
from app.utils.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
def analyze_text(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze text and return heat map data with AI probability scores.
    """
    try:
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
        
        # Analyze text
        result = analysis_service.analyze_text(
            text=request.text,
            granularity=request.granularity,
            user_fingerprint=fingerprint_dict
        )
        
        # Convert to response format
        segments = [
            TextSegment(
                text=seg["text"],
                ai_probability=seg["ai_probability"],
                start_index=seg["start_index"],
                end_index=seg["end_index"]
            )
            for seg in result["segments"]
        ]
        
        heat_map_data = HeatMapData(
            segments=segments,
            overall_ai_probability=result["overall_ai_probability"]
        )
        
        # Save analysis result
        analysis_result = AnalysisResult(
            user_id=current_user.id,
            text_content=request.text,
            heat_map_data={
                "segments": [seg.dict() for seg in segments],
                "overall_ai_probability": result["overall_ai_probability"]
            },
            overall_ai_probability=str(result["overall_ai_probability"])
        )
        db.add(analysis_result)
        db.commit()
        db.refresh(analysis_result)
        
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
