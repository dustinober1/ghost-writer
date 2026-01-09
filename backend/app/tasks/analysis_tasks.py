"""
Background tasks for long-running analysis operations.
"""
from app.celery_app import celery_app
from app.services.analysis_service import get_analysis_service
from app.services.fingerprint_service import get_fingerprint_service
from sqlalchemy.orm import Session
from app.models.database import SessionLocal, AnalysisResult, User


@celery_app.task(name="app.tasks.analyze_text_async")
def analyze_text_async(user_id: int, text: str, granularity: str = "sentence"):
    """
    Analyze text in the background for long texts (>5000 words).
    
    Args:
        user_id: User ID
        text: Text to analyze
        granularity: Analysis granularity
    
    Returns:
        Analysis result ID
    """
    db = SessionLocal()
    try:
        analysis_service = get_analysis_service()
        fingerprint_service = get_fingerprint_service()
        
        # Get user's fingerprint if available
        user_fingerprint = fingerprint_service.get_user_fingerprint(db, user_id)
        fingerprint_dict = None
        if user_fingerprint:
            fingerprint_dict = {
                "feature_vector": user_fingerprint.feature_vector,
                "model_version": user_fingerprint.model_version
            }
        
        # Analyze text
        result = analysis_service.analyze_text(
            text=text,
            granularity=granularity,
            user_fingerprint=fingerprint_dict,
        )
        
        # Save analysis result
        from app.models.schemas import TextSegment
        segments = [
            TextSegment(
                text=seg["text"],
                ai_probability=seg["ai_probability"],
                start_index=seg["start_index"],
                end_index=seg["end_index"]
            )
            for seg in result["segments"]
        ]
        
        analysis_result = AnalysisResult(
            user_id=user_id,
            text_content=text,
            heat_map_data={
                "segments": [seg.dict() for seg in segments],
                "overall_ai_probability": result["overall_ai_probability"]
            },
            overall_ai_probability=str(result["overall_ai_probability"])
        )
        db.add(analysis_result)
        db.commit()
        db.refresh(analysis_result)
        
        return analysis_result.id
    finally:
        db.close()
