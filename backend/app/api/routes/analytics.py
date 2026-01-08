from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, Float
from app.models.database import get_db, User, AnalysisResult, WritingSample, Fingerprint
from app.models.schemas import (
    AnalyticsOverview,
    ActivityEntry,
    TrendData,
    TrendDataPoint,
    PerformanceMetrics,
    AnalysisHistoryItem,
    AnalysisHistoryResponse,
)
from app.utils.auth import get_current_user
from datetime import datetime, timedelta
from typing import List, Optional

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard overview statistics for the current user.
    """
    try:
        # Total analyses
        total_analyses = db.query(AnalysisResult).filter(
            AnalysisResult.user_id == current_user.id
        ).count()

        # Total writing samples
        total_samples = db.query(WritingSample).filter(
            WritingSample.user_id == current_user.id
        ).count()

        # Check if user has fingerprint
        fingerprint = db.query(Fingerprint).filter(
            Fingerprint.user_id == current_user.id
        ).first()
        has_fingerprint = fingerprint is not None

        # Calculate average AI probability
        analyses = db.query(AnalysisResult).filter(
            AnalysisResult.user_id == current_user.id
        ).all()
        
        average_ai_probability = None
        if analyses:
            probabilities = [float(ar.overall_ai_probability) for ar in analyses]
            average_ai_probability = sum(probabilities) / len(probabilities)

        # Rewrites count (placeholder - would need RewriteHistory table)
        total_rewrites = 0

        # Fingerprint accuracy (placeholder - would need accuracy tracking)
        fingerprint_accuracy = None

        return AnalyticsOverview(
            total_analyses=total_analyses,
            total_rewrites=total_rewrites,
            total_samples=total_samples,
            has_fingerprint=has_fingerprint,
            fingerprint_accuracy=fingerprint_accuracy,
            average_ai_probability=average_ai_probability,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching analytics overview: {str(e)}"
        )


@router.get("/activity", response_model=List[ActivityEntry])
def get_recent_activity(
    days: int = Query(30, ge=1, le=90, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent user activity for the last N days.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        activities: List[ActivityEntry] = []

        # Analysis activities
        analyses = db.query(AnalysisResult).filter(
            and_(
                AnalysisResult.user_id == current_user.id,
                AnalysisResult.created_at >= cutoff_date
            )
        ).order_by(desc(AnalysisResult.created_at)).limit(50).all()

        for analysis in analyses:
            text_preview = analysis.text_content[:100] + "..." if len(analysis.text_content) > 100 else analysis.text_content
            activities.append(ActivityEntry(
                id=analysis.id,
                type="analysis",
                description=f"Analyzed text: {text_preview}",
                created_at=analysis.created_at,
                metadata={"ai_probability": float(analysis.overall_ai_probability)}
            ))

        # Writing sample uploads
        samples = db.query(WritingSample).filter(
            and_(
                WritingSample.user_id == current_user.id,
                WritingSample.uploaded_at >= cutoff_date
            )
        ).order_by(desc(WritingSample.uploaded_at)).limit(20).all()

        for sample in samples:
            activities.append(ActivityEntry(
                id=sample.id,
                type="sample_upload",
                description=f"Uploaded writing sample ({sample.source_type})",
                created_at=sample.uploaded_at,
                metadata={"source_type": sample.source_type}
            ))

        # Fingerprint generation/updates
        fingerprints = db.query(Fingerprint).filter(
            and_(
                Fingerprint.user_id == current_user.id,
                Fingerprint.updated_at >= cutoff_date
            )
        ).order_by(desc(Fingerprint.updated_at)).limit(10).all()

        for fp in fingerprints:
            activities.append(ActivityEntry(
                id=fp.id,
                type="fingerprint_generated",
                description=f"Fingerprint {'updated' if fp.created_at != fp.updated_at else 'generated'}",
                created_at=fp.updated_at,
                metadata={"model_version": fp.model_version}
            ))

        # Sort by created_at descending
        activities.sort(key=lambda x: x.created_at, reverse=True)
        
        return activities[:50]  # Return top 50 most recent
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching activity: {str(e)}"
        )


@router.get("/trends", response_model=List[TrendData])
def get_usage_trends(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get usage trends over time.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily analysis counts
        daily_analyses = db.query(
            func.date(AnalysisResult.created_at).label('date'),
            func.count(AnalysisResult.id).label('count')
        ).filter(
            and_(
                AnalysisResult.user_id == current_user.id,
                AnalysisResult.created_at >= cutoff_date
            )
        ).group_by(func.date(AnalysisResult.created_at)).all()

        analysis_data = [
            TrendDataPoint(date=row.date.isoformat(), count=row.count)
            for row in daily_analyses
        ]

        # Daily average AI probability
        daily_avg_prob = db.query(
            func.date(AnalysisResult.created_at).label('date'),
            func.avg(func.cast(AnalysisResult.overall_ai_probability, Float)).label('avg_prob')
        ).filter(
            and_(
                AnalysisResult.user_id == current_user.id,
                AnalysisResult.created_at >= cutoff_date
            )
        ).group_by(func.date(AnalysisResult.created_at)).all()

        probability_data = [
            TrendDataPoint(date=row.date.isoformat(), count=0, value=float(row.avg_prob) if row.avg_prob else None)
            for row in daily_avg_prob
        ]

        return [
            TrendData(label="Daily Analyses", data=analysis_data),
            TrendData(label="Average AI Probability", data=probability_data),
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching trends: {str(e)}"
        )


@router.get("/performance", response_model=PerformanceMetrics)
def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI detection performance metrics.
    """
    try:
        analyses = db.query(AnalysisResult).filter(
            AnalysisResult.user_id == current_user.id
        ).all()

        if not analyses:
            return PerformanceMetrics(
                average_ai_probability=0.0,
                high_confidence_count=0,
                medium_confidence_count=0,
                low_confidence_count=0,
                total_analyses=0,
            )

        probabilities = [float(ar.overall_ai_probability) for ar in analyses]
        average_ai_probability = sum(probabilities) / len(probabilities)

        high_confidence = sum(1 for p in probabilities if p > 0.7)
        medium_confidence = sum(1 for p in probabilities if 0.4 <= p <= 0.7)
        low_confidence = sum(1 for p in probabilities if p < 0.4)

        return PerformanceMetrics(
            average_ai_probability=average_ai_probability,
            high_confidence_count=high_confidence,
            medium_confidence_count=medium_confidence,
            low_confidence_count=low_confidence,
            total_analyses=len(analyses),
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching performance metrics: {str(e)}"
        )


@router.get("/history", response_model=AnalysisHistoryResponse)
def get_analysis_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in text content"),
    min_probability: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum AI probability"),
    max_probability: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum AI probability"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated analysis history with filtering and search.
    """
    try:
        query = db.query(AnalysisResult).filter(
            AnalysisResult.user_id == current_user.id
        )

        # Search filter
        if search:
            query = query.filter(
                AnalysisResult.text_content.ilike(f"%{search}%")
            )

        # Probability filters
        if min_probability is not None:
            query = query.filter(
                func.cast(AnalysisResult.overall_ai_probability, Float) >= min_probability
            )
        if max_probability is not None:
            query = query.filter(
                func.cast(AnalysisResult.overall_ai_probability, Float) <= max_probability
            )

        # Get total count
        total = query.count()

        # Pagination
        offset = (page - 1) * page_size
        analyses = query.order_by(desc(AnalysisResult.created_at)).offset(offset).limit(page_size).all()

        items = [
            AnalysisHistoryItem(
                id=ar.id,
                text_preview=ar.text_content[:100] + "..." if len(ar.text_content) > 100 else ar.text_content,
                overall_ai_probability=float(ar.overall_ai_probability),
                word_count=len(ar.text_content.split()),
                created_at=ar.created_at,
            )
            for ar in analyses
        ]

        total_pages = (total + page_size - 1) // page_size

        return AnalysisHistoryResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching analysis history: {str(e)}"
        )
