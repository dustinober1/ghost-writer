"""
Temporal analysis API endpoints.

Provides endpoints for:
- Storing and retrieving document versions
- Analyzing document timeline and trends
- Detecting AI injection events
- Comparing document versions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.database import get_db, User
from app.models.schemas import (
    DocumentVersionCreate,
    DocumentVersionResponse,
    TimelineResponse,
    TimelineDataPoint,
    InjectionResponse,
    InjectionEvent,
    MixedAuthorshipIndicator,
    VersionComparisonRequest,
    VersionComparison,
    VersionsListResponse
)
from app.utils.auth import get_current_user_or_api_key, get_current_user
from app.ml.temporal.version_tracker import VersionTracker, DocumentNotFound
from app.ml.temporal.timeline_analyzer import TimelineAnalyzer
from app.ml.temporal.injection_detector import InjectionDetector
from app.services.analysis_service import get_analysis_service

router = APIRouter(prefix="/api/temporal", tags=["temporal"])


@router.post("/version", response_model=DocumentVersionResponse)
def store_document_version(
    request: DocumentVersionCreate,
    current_user: User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """
    Store a new document version with AI analysis.

    Analyzes the document content using the ensemble detector
    and stores the results with segment-level AI probabilities.

    Requires authentication (JWT or API key).
    """
    try:
        # Get analysis service and analyze the text
        analysis_service = get_analysis_service()

        # Run ensemble analysis
        analysis_result = analysis_service.analyze_with_ensemble(
            text=request.content,
            granularity=request.granularity,
            user_fingerprint=None,
            user_id=current_user.id,
            use_cache=True
        )

        # Store the version
        tracker = VersionTracker()
        version_id = tracker.store_version(
            user_id=current_user.id,
            document_id=request.document_id,
            content=request.content,
            analysis_result=analysis_result,
            db=db
        )

        # Get the stored version
        version = tracker.get_version_by_number(
            document_id=request.document_id,
            version_number=analysis_result.get('version_number', 1),
            db=db
        )

        if not version:
            # Fallback: query directly
            from app.models.database import DocumentVersion as DV
            dv = db.query(DV).filter(DV.id == version_id).first()
            return DocumentVersionResponse(
                version_id=dv.id,
                version_number=dv.version_number,
                document_id=request.document_id,
                created_at=dv.created_at,
                word_count=dv.word_count,
                overall_ai_probability=dv.overall_ai_probability,
                segment_ai_scores=dv.segment_ai_scores
            )

        return DocumentVersionResponse(
            version_id=version['version_id'],
            version_number=version['version_number'],
            document_id=request.document_id,
            created_at=datetime.fromisoformat(version['created_at']) if isinstance(version['created_at'], str) else version['created_at'],
            word_count=version['word_count'],
            overall_ai_probability=version['overall_ai_probability'],
            segment_ai_scores=version.get('segment_ai_scores')
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error storing version: {str(e)}"
        )


@router.get("/timeline/{document_id}", response_model=TimelineResponse)
def get_document_timeline(
    document_id: str,
    current_user: User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """
    Get timeline analysis for a document.

    Returns the evolution of AI probability across document versions,
    including trend detection and AI velocity.

    Requires authentication (JWT or API key).
    """
    try:
        analyzer = TimelineAnalyzer()
        result = analyzer.analyze_timeline(document_id, db)

        # Convert timeline data to response models
        timeline_data = []
        for point in result.get('timeline', []):
            timeline_data.append(TimelineDataPoint(
                version_id=point['version_id'],
                version_number=point['version_number'],
                timestamp=point['timestamp'],
                word_count=point['word_count'],
                avg_ai_prob=point['avg_ai_prob'],
                max_ai_prob=point['max_ai_prob'],
                min_ai_prob=point['min_ai_prob'],
                std_ai_prob=point['std_ai_prob'],
                high_confidence_count=point['high_confidence_count'],
                medium_confidence_count=point['medium_confidence_count'],
                low_confidence_count=point['low_confidence_count'],
                overall_ai_probability=point['overall_ai_probability']
            ))

        return TimelineResponse(
            timeline=timeline_data,
            overall_trend=result.get('overall_trend', 'no_data'),
            ai_velocity=result.get('ai_velocity', 0.0),
            total_versions=result.get('total_versions', 0),
            error=result.get('error')
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing timeline: {str(e)}"
        )


@router.get("/versions/{document_id}", response_model=VersionsListResponse)
def get_document_versions(
    document_id: str,
    current_user: User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """
    Get all versions for a document.

    Returns a list of all document versions ordered by creation time.

    Requires authentication (JWT or API key).
    """
    try:
        tracker = VersionTracker()
        versions = tracker.get_version_history(document_id, db)

        version_responses = []
        for v in versions:
            created_at = datetime.fromisoformat(v['created_at']) if isinstance(v['created_at'], str) else v['created_at']
            version_responses.append(DocumentVersionResponse(
                version_id=v['version_id'],
                version_number=v['version_number'],
                document_id=document_id,
                created_at=created_at,
                word_count=v['word_count'],
                overall_ai_probability=v['overall_ai_probability'],
                segment_ai_scores=v.get('segment_ai_scores')
            ))

        return VersionsListResponse(
            versions=version_responses,
            total_versions=len(versions),
            document_id=document_id
        )

    except DocumentNotFound:
        return VersionsListResponse(
            versions=[],
            total_versions=0,
            document_id=document_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving versions: {str(e)}"
        )


@router.post("/compare", response_model=VersionComparison)
def compare_document_versions(
    request: VersionComparisonRequest,
    current_user: User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """
    Compare two document versions to identify differences.

    Returns added, removed, and modified sections between versions,
    along with AI probability information for each change.

    Requires authentication (JWT or API key).
    """
    try:
        tracker = VersionTracker()

        # Get version IDs from version numbers
        version_a = tracker.get_version_by_number(request.document_id, request.version_a, db)
        version_b = tracker.get_version_by_number(request.document_id, request.version_b, db)

        if not version_a or not version_b:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"One or both versions not found for document: {request.document_id}"
            )

        # Compare the versions
        comparison = tracker.compare_versions(version_a['version_id'], version_b['version_id'], db)

        # Convert to response format
        from app.models.schemas import DiffSection

        added_sections = [
            DiffSection(
                text=s['text'],
                position=s['position'],
                ai_probability=s.get('ai_probability')
            )
            for s in comparison.get('added_sections', [])
        ]

        removed_sections = [
            DiffSection(
                text=s['text'],
                position=s['position']
            )
            for s in comparison.get('removed_sections', [])
        ]

        modified_sections = [
            DiffSection(
                text=s['new_text'],
                position=s['position'],
                old_text=s.get('old_text'),
                new_text=s.get('new_text'),
                old_position=s.get('old_position'),
                delta_ai=s.get('delta_ai')
            )
            for s in comparison.get('modified_sections', [])
        ]

        return VersionComparison(
            added_sections=added_sections,
            removed_sections=removed_sections,
            modified_sections=modified_sections,
            similarity_score=comparison.get('similarity_score', 0.0),
            version_a_number=comparison.get('version_a_number', request.version_a),
            version_b_number=comparison.get('version_b_number', request.version_b)
        )

    except DocumentNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {request.document_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing versions: {str(e)}"
        )


@router.get("/injections/{document_id}", response_model=InjectionResponse)
def get_injection_analysis(
    document_id: str,
    current_user: User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """
    Get AI injection analysis for a document.

    Detects and analyzes AI-generated content that was added
    between document versions, along with mixed authorship indicators.

    Requires authentication (JWT or API key).
    """
    try:
        detector = InjectionDetector()
        summary = detector.get_injection_summary(document_id, db)

        # Convert injection events
        injection_events = []
        for event in summary.get('injection_events', []):
            injection_events.append(InjectionEvent(
                version=event['version'],
                version_id=event['version_id'],
                timestamp=event['timestamp'],
                position=event['position'],
                text=event['text'],
                ai_probability=event['ai_probability'],
                type=event['type'],
                severity=event['severity'],
                delta_ai=event.get('delta_ai'),
                old_text=event.get('old_text'),
                new_text=event.get('new_text')
            ))

        # Convert mixed authorship indicators
        mixed_indicators = []
        for indicator in summary.get('mixed_authorship_indicators', []):
            mixed_indicators.append(MixedAuthorshipIndicator(
                type=indicator['type'],
                description=indicator['description'],
                value=indicator['value'],
                severity=indicator['severity'],
                version=indicator.get('version'),
                from_version=indicator.get('from_version'),
                to_version=indicator.get('to_version'),
                segment_index=indicator.get('segment_index')
            ))

        return InjectionResponse(
            injection_events=injection_events,
            injection_score=summary.get('injection_score', 0.0),
            total_injections=summary.get('total_injections', 0),
            additions_count=summary.get('additions_count', 0),
            modifications_count=summary.get('modifications_count', 0),
            severity_breakdown=summary.get('severity_breakdown', {}),
            mixed_authorship_indicators=mixed_indicators,
            overall_risk=summary.get('overall_risk', 'none')
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing injections: {str(e)}"
        )


@router.get("/summary/{document_id}")
def get_temporal_summary(
    document_id: str,
    current_user: User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """
    Get a comprehensive temporal analysis summary for a document.

    Combines timeline, injection, and comparison data into a single response.

    Requires authentication (JWT or API key).
    """
    try:
        # Get timeline
        timeline_analyzer = TimelineAnalyzer()
        timeline_result = timeline_analyzer.analyze_timeline(document_id, db)

        # Get injection summary
        injection_detector = InjectionDetector()
        injection_summary = injection_detector.get_injection_summary(document_id, db)

        # Get version count
        tracker = VersionTracker()
        try:
            versions = tracker.get_version_history(document_id, db)
            latest_version = versions[-1] if versions else None
        except DocumentNotFound:
            versions = []
            latest_version = None

        return {
            'document_id': document_id,
            'has_versions': len(versions) > 0,
            'total_versions': len(versions),
            'latest_version': {
                'version_number': latest_version['version_number'],
                'created_at': latest_version['created_at'],
                'overall_ai_probability': latest_version['overall_ai_probability'],
                'word_count': latest_version['word_count']
            } if latest_version else None,
            'timeline': {
                'overall_trend': timeline_result.get('overall_trend'),
                'ai_velocity': timeline_result.get('ai_velocity'),
                'total_versions': timeline_result.get('total_versions')
            },
            'injections': {
                'total_injections': injection_summary.get('total_injections', 0),
                'injection_score': injection_summary.get('injection_score', 0.0),
                'overall_risk': injection_summary.get('overall_risk', 'none'),
                'severity_breakdown': injection_summary.get('severity_breakdown', {})
            },
            'mixed_authorship': {
                'indicators_count': len(injection_summary.get('mixed_authorship_indicators', [])),
                'has_indicators': len(injection_summary.get('mixed_authorship_indicators', [])) > 0
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )
