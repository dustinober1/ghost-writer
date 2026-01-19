from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.database import get_db, User, FingerprintSample, EnhancedFingerprint, Fingerprint, DriftAlert
from app.models.schemas import (
    WritingSampleCreate,
    WritingSampleResponse,
    FingerprintStatus,
    FingerprintResponse,
    FingerprintSampleCreate,
    FingerprintSampleResponse,
    CorpusStatus,
    EnhancedFingerprintResponse,
    FingerprintComparisonRequest,
    FingerprintComparisonResponse,
    FingerprintProfile,
    FeatureDeviation,
    ConfidenceInterval,
    DriftDetectionResult,
    DriftAlertResponse,
    DriftAlertsList,
    FeatureChange,
    DriftSeverity
)
from app.services.fingerprint_service import get_fingerprint_service
from app.utils.auth import get_current_user
from app.middleware.rate_limit import general_rate_limit
from app.utils.file_validation import validate_upload_file, validate_text_length
from app.middleware.input_sanitization import sanitize_text, sanitize_filename
from app.ml.fingerprint.corpus_builder import FingerprintCorpusBuilder
from app.ml.fingerprint.similarity_calculator import FingerprintComparator
from app.ml.fingerprint.drift_detector import StyleDriftDetector
from app.ml.feature_extraction import extract_feature_vector
import pickle
import base64
import docx
import PyPDF2
import io

router = APIRouter(prefix="/api/fingerprint", tags=["fingerprint"])


@router.post("/upload", response_model=WritingSampleResponse, status_code=status.HTTP_201_CREATED)
@general_rate_limit
def upload_writing_sample(
    text: str = None,
    file: UploadFile = File(None),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a writing sample. Can provide text directly or upload a file (txt, docx, pdf).
    """
    fingerprint_service = get_fingerprint_service()
    
    text_content = None
    
    if file:
        # Validate file
        validate_upload_file(file)
        sanitized_filename = sanitize_filename(file.filename)
        
        # Read file content
        file_content = file.file.read()
        
        if sanitized_filename.endswith('.txt'):
            text_content = file_content.decode('utf-8')
        elif sanitized_filename.endswith('.docx'):
            doc = docx.Document(io.BytesIO(file_content))
            text_content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        elif sanitized_filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text_content = '\n'.join([page.extract_text() for page in pdf_reader.pages])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Supported: txt, docx, pdf"
            )
        
        # Sanitize extracted text
        text_content = sanitize_text(text_content)
    elif text:
        validate_text_length(text)
        text_content = sanitize_text(text)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either text or file must be provided"
        )
    
    if not text_content or not text_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content cannot be empty"
        )
    
    try:
        sample = fingerprint_service.upload_writing_sample(
            db=db,
            user_id=current_user.id,
            text_content=text_content,
            source_type="upload" if file else "manual"
        )
        return sample
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading sample: {str(e)}"
        )


@router.get("/status", response_model=FingerprintStatus)
def get_fingerprint_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's fingerprint status"""
    fingerprint_service = get_fingerprint_service()
    return fingerprint_service.get_fingerprint_status(db, current_user.id)


@router.post("/generate", response_model=FingerprintResponse)
def generate_fingerprint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate or update user's fingerprint from their writing samples"""
    fingerprint_service = get_fingerprint_service()
    
    try:
        fingerprint = fingerprint_service.generate_user_fingerprint(db, current_user.id)
        return fingerprint
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating fingerprint: {str(e)}"
        )


@router.post("/finetune", response_model=FingerprintResponse)
def fine_tune_fingerprint(
    new_samples: List[str],
    weight: float = 0.3,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fine-tune user's fingerprint with new samples.
    
    Args:
        new_samples: List of new text samples
        weight: Weight for new samples (0.0 to 1.0, default 0.3)
    """
    fingerprint_service = get_fingerprint_service()
    
    if not new_samples:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one new sample is required"
        )
    
    if not 0.0 <= weight <= 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Weight must be between 0.0 and 1.0"
        )
    
    try:
        fingerprint = fingerprint_service.fine_tune_fingerprint(
            db=db,
            user_id=current_user.id,
            new_samples=new_samples,
            weight=weight
        )
        return fingerprint
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fine-tuning fingerprint: {str(e)}"
        )


# ============= Corpus Management Endpoints =============

@router.post("/corpus/add", response_model=FingerprintSampleResponse, status_code=status.HTTP_201_CREATED)
@general_rate_limit
def add_corpus_sample(
    sample: FingerprintSampleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a writing sample to the corpus for enhanced fingerprint generation.
    Requires at least 10 samples to generate an enhanced fingerprint.
    """
    # Sanitize text content
    text_content = sanitize_text(sample.text_content)

    if not text_content or not text_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content cannot be empty"
        )

    if len(text_content) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content must be at least 10 characters"
        )

    try:
        # Extract features from text
        features = extract_feature_vector(text_content)
        features_list = features.tolist() if hasattr(features, 'tolist') else list(features)

        # Create fingerprint sample
        fingerprint_sample = FingerprintSample(
            user_id=current_user.id,
            text_content=text_content,
            source_type=sample.source_type,
            features=features_list,
            word_count=len(text_content.split()),
            written_at=sample.written_at
        )
        db.add(fingerprint_sample)
        db.commit()
        db.refresh(fingerprint_sample)

        # Create response with text preview
        response_data = {
            "id": fingerprint_sample.id,
            "user_id": fingerprint_sample.user_id,
            "source_type": fingerprint_sample.source_type,
            "word_count": fingerprint_sample.word_count,
            "created_at": fingerprint_sample.created_at,
            "written_at": fingerprint_sample.written_at,
            "text_preview": text_content[:100] + "..." if len(text_content) > 100 else text_content
        }
        return FingerprintSampleResponse(**response_data)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding sample to corpus: {str(e)}"
        )


@router.get("/corpus/status", response_model=CorpusStatus)
def get_corpus_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get corpus status including sample count, source distribution,
    and whether the corpus is ready for enhanced fingerprint generation.
    """
    try:
        # Query all fingerprint samples for user
        samples = db.query(FingerprintSample).filter(
            FingerprintSample.user_id == current_user.id
        ).all()

        sample_count = len(samples)
        total_words = sum(s.word_count for s in samples)

        # Calculate source distribution
        source_distribution: dict[str, int] = {}
        for sample in samples:
            source = sample.source_type
            source_distribution[source] = source_distribution.get(source, 0) + 1

        # Get oldest and newest sample timestamps
        oldest_sample = None
        newest_sample = None
        if samples:
            oldest_sample = min(s.created_at for s in samples)
            newest_sample = max(s.created_at for s in samples)

        ready_for_fingerprint = sample_count >= FingerprintCorpusBuilder.MIN_SAMPLES_FOR_FINGERPRINT
        samples_needed = max(0, FingerprintCorpusBuilder.MIN_SAMPLES_FOR_FINGERPRINT - sample_count)

        return CorpusStatus(
            sample_count=sample_count,
            total_words=total_words,
            source_distribution=source_distribution,
            ready_for_fingerprint=ready_for_fingerprint,
            samples_needed=samples_needed,
            oldest_sample=oldest_sample,
            newest_sample=newest_sample
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting corpus status: {str(e)}"
        )


@router.get("/corpus/samples", response_model=List[FingerprintSampleResponse])
def list_corpus_samples(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all corpus samples with pagination.
    Samples are ordered by creation date (newest first).
    """
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    try:
        # Query samples with pagination
        query = db.query(FingerprintSample).filter(
            FingerprintSample.user_id == current_user.id
        ).order_by(FingerprintSample.created_at.desc())

        total = query.count()
        offset = (page - 1) * page_size
        samples = query.offset(offset).limit(page_size).all()

        # Create responses with text previews
        result = []
        for sample in samples:
            text_preview = sample.text_content[:100] + "..." if len(sample.text_content) > 100 else sample.text_content
            result.append(FingerprintSampleResponse(
                id=sample.id,
                user_id=sample.user_id,
                source_type=sample.source_type,
                word_count=sample.word_count,
                created_at=sample.created_at,
                written_at=sample.written_at,
                text_preview=text_preview
            ))
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing corpus samples: {str(e)}"
        )


@router.delete("/corpus/sample/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_corpus_sample(
    sample_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific corpus sample.
    Only samples belonging to the current user can be deleted.
    """
    try:
        sample = db.query(FingerprintSample).filter(
            FingerprintSample.id == sample_id
        ).first()

        if not sample:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sample not found"
            )

        if sample.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own samples"
            )

        db.delete(sample)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting sample: {str(e)}"
        )


@router.post("/corpus/generate", response_model=EnhancedFingerprintResponse)
def generate_enhanced_fingerprint(
    method: str = "time_weighted",
    alpha: float = 0.3,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an enhanced fingerprint from the corpus.
    Requires at least 10 samples in the corpus.

    Args:
        method: Aggregation method ('time_weighted', 'average', 'source_weighted')
        alpha: EMA smoothing parameter for time_weighted method (0.0 to 1.0)
    """
    # Validate method
    valid_methods = ["time_weighted", "average", "source_weighted"]
    if method not in valid_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid method. Must be one of: {', '.join(valid_methods)}"
        )

    # Validate alpha
    if not 0.0 < alpha <= 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alpha must be between 0.0 and 1.0"
        )

    try:
        # Get all user's fingerprint samples
        samples = db.query(FingerprintSample).filter(
            FingerprintSample.user_id == current_user.id
        ).all()

        if len(samples) < FingerprintCorpusBuilder.MIN_SAMPLES_FOR_FINGERPRINT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Need at least {FingerprintCorpusBuilder.MIN_SAMPLES_FOR_FINGERPRINT} samples to generate enhanced fingerprint. "
                       f"You have {len(samples)} samples."
            )

        # Build corpus and generate fingerprint
        builder = FingerprintCorpusBuilder(min_samples=FingerprintCorpusBuilder.MIN_SAMPLES_FOR_FINGERPRINT)

        for sample in samples:
            # Load features from stored JSON
            features = sample.features
            timestamp = sample.written_at or sample.created_at

            # Add sample to builder
            builder.samples.append({
                "features": features,
                "timestamp": timestamp,
                "source_type": sample.source_type,
                "word_count": sample.word_count
            })

        # Generate fingerprint
        fingerprint_data = builder.build_fingerprint(method=method, alpha=alpha)

        # Check if enhanced fingerprint already exists
        existing_fingerprint = db.query(EnhancedFingerprint).filter(
            EnhancedFingerprint.user_id == current_user.id
        ).first()

        if existing_fingerprint:
            # Update existing fingerprint
            existing_fingerprint.feature_vector = fingerprint_data["feature_vector"]
            existing_fingerprint.feature_statistics = fingerprint_data.get("feature_statistics")
            existing_fingerprint.corpus_size = fingerprint_data["sample_count"]
            existing_fingerprint.method = fingerprint_data["method"]
            existing_fingerprint.alpha = fingerprint_data.get("alpha", alpha)
            existing_fingerprint.source_distribution = fingerprint_data.get("source_distribution")
            existing_fingerprint.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_fingerprint)
            enhanced_fp = existing_fingerprint
        else:
            # Create new enhanced fingerprint
            enhanced_fp = EnhancedFingerprint(
                user_id=current_user.id,
                feature_vector=fingerprint_data["feature_vector"],
                feature_statistics=fingerprint_data.get("feature_statistics"),
                corpus_size=fingerprint_data["sample_count"],
                method=fingerprint_data["method"],
                alpha=fingerprint_data.get("alpha", alpha),
                source_distribution=fingerprint_data.get("source_distribution")
            )
            db.add(enhanced_fp)
            db.commit()
            db.refresh(enhanced_fp)

        return EnhancedFingerprintResponse(
            id=enhanced_fp.id,
            user_id=enhanced_fp.user_id,
            corpus_size=enhanced_fp.corpus_size,
            method=enhanced_fp.method,
            alpha=enhanced_fp.alpha,
            source_distribution=enhanced_fp.source_distribution,
            created_at=enhanced_fp.created_at,
            updated_at=enhanced_fp.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating enhanced fingerprint: {str(e)}"
        )


# ============= Fingerprint Comparison Endpoints =============

@router.post("/compare", response_model=FingerprintComparisonResponse)
def compare_text_to_fingerprint(
    request: FingerprintComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compare text to user's fingerprint with confidence intervals.

    Returns similarity score, confidence interval, match level,
    and which features differ most.

    Args:
        request: Comparison request with text and use_enhanced flag
        current_user: Authenticated user
        db: Database session

    Returns:
        FingerprintComparisonResponse with similarity analysis
    """
    # Sanitize input text
    text_content = sanitize_text(request.text)

    if not text_content or len(text_content.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text must be at least 10 characters long"
        )

    # Try to get enhanced fingerprint first if use_enhanced is True
    fingerprint_dict = None
    fingerprint_stats = None
    method_used = "basic"

    if request.use_enhanced:
        enhanced_fp = db.query(EnhancedFingerprint).filter(
            EnhancedFingerprint.user_id == current_user.id
        ).first()

        if enhanced_fp:
            fingerprint_dict = {
                "feature_vector": enhanced_fp.feature_vector,
                "corpus_size": enhanced_fp.corpus_size,
                "method": enhanced_fp.method
            }
            fingerprint_stats = enhanced_fp.feature_statistics
            method_used = f"{enhanced_fp.method}_ema" if enhanced_fp.method == "time_weighted" else enhanced_fp.method

    # Fall back to basic fingerprint if no enhanced fingerprint
    if fingerprint_dict is None:
        basic_fp = db.query(Fingerprint).filter(
            Fingerprint.user_id == current_user.id
        ).first()

        if not basic_fp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No fingerprint found. Please generate a fingerprint first."
            )

        fingerprint_dict = {
            "feature_vector": basic_fp.feature_vector,
            "model_version": basic_fp.model_version
        }
        method_used = "basic"

    # Extract features from input text
    try:
        text_features = extract_feature_vector(text_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting features from text: {str(e)}"
        )

    # Compare using FingerprintComparator
    try:
        comparator = FingerprintComparator(confidence_level=0.95)
        comparison_result = comparator.compare_with_confidence(
            text_features, fingerprint_dict, fingerprint_stats
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing text to fingerprint: {str(e)}"
        )

    # Convert feature deviations to response format
    feature_deviations = []
    for feature_name, deviation_data in comparison_result.get("feature_deviations", {}).items():
        feature_deviations.append(FeatureDeviation(
            feature=feature_name,
            text_value=deviation_data.get("text_value", 0.0),
            fingerprint_value=deviation_data.get("fingerprint_value", 0.0),
            deviation=deviation_data.get("deviation", 0.0)
        ))

    # Build confidence interval
    ci_lower, ci_upper = comparison_result.get("confidence_interval", [0.0, 1.0])
    confidence_interval = ConfidenceInterval(lower=ci_lower, upper=ci_upper)

    return FingerprintComparisonResponse(
        similarity=comparison_result["similarity"],
        confidence_interval=confidence_interval,
        match_level=comparison_result["match_level"],
        feature_deviations=feature_deviations,
        method_used=method_used,
        corpus_size=fingerprint_dict.get("corpus_size")
    )


@router.get("/profile", response_model=FingerprintProfile)
def get_fingerprint_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's fingerprint profile with metadata.

    Returns information about the user's fingerprint including
    corpus size, method, alpha, source distribution, and timestamps.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        FingerprintProfile with metadata
    """
    # Try enhanced fingerprint first
    enhanced_fp = db.query(EnhancedFingerprint).filter(
        EnhancedFingerprint.user_id == current_user.id
    ).first()

    if enhanced_fp:
        return FingerprintProfile(
            has_fingerprint=True,
            corpus_size=enhanced_fp.corpus_size,
            method=enhanced_fp.method,
            alpha=enhanced_fp.alpha,
            source_distribution=enhanced_fp.source_distribution,
            created_at=enhanced_fp.created_at,
            updated_at=enhanced_fp.updated_at,
            feature_count=27
        )

    # Fall back to basic fingerprint
    basic_fp = db.query(Fingerprint).filter(
        Fingerprint.user_id == current_user.id
    ).first()

    if basic_fp:
        return FingerprintProfile(
            has_fingerprint=True,
            corpus_size=None,
            method=basic_fp.model_version,
            alpha=None,
            source_distribution=None,
            created_at=basic_fp.created_at,
            updated_at=basic_fp.updated_at,
            feature_count=27
        )

    # No fingerprint found
    return FingerprintProfile(
        has_fingerprint=False,
        feature_count=27
    )


# ============= Drift Detection Endpoints =============

# In-memory cache for drift detectors (user_id -> detector)
_drift_detector_cache: Dict[int, StyleDriftDetector] = {}


def get_drift_detector(user_id: int, db: Session) -> StyleDriftDetector:
    """
    Get or create a drift detector for the user.

    Attempts to load baseline from existing alerts or creates new detector.
    """
    if user_id in _drift_detector_cache:
        return _drift_detector_cache[user_id]

    detector = StyleDriftDetector()

    # Try to establish baseline from recent unacknowledged alerts
    recent_alerts = db.query(DriftAlert).filter(
        DriftAlert.user_id == user_id,
        DriftAlert.acknowledged == False
    ).order_by(DriftAlert.created_at.desc()).limit(10).all()

    if recent_alerts:
        # Use baseline from first alert's stored baseline similarity
        # and build similarity history from alerts
        similarities = [alert.baseline_similarity for alert in recent_alerts if alert.baseline_similarity > 0]
        if similarities and len(similarities) >= 3:
            detector.establish_baseline(similarities)

    _drift_detector_cache[user_id] = detector
    return detector


@router.get("/drift/alerts", response_model=DriftAlertsList)
def get_drift_alerts(
    include_acknowledged: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get drift alerts for current user.

    include_acknowledged: If False, only return unacknowledged alerts
    """
    try:
        query = db.query(DriftAlert).filter(
            DriftAlert.user_id == current_user.id
        )

        if not include_acknowledged:
            query = query.filter(DriftAlert.acknowledged == False)

        alerts = query.order_by(DriftAlert.created_at.desc()).all()

        # Count unacknowledged
        unacknowledged_count = db.query(DriftAlert).filter(
            DriftAlert.user_id == current_user.id,
            DriftAlert.acknowledged == False
        ).count()

        # Convert to response format
        alert_responses = []
        for alert in alerts:
            # Convert changed_features from JSON/dict to FeatureChange objects
            changed_features = []
            if alert.changed_features:
                for feature_data in alert.changed_features:
                    changed_features.append(FeatureChange(**feature_data))

            alert_responses.append(DriftAlertResponse(
                id=alert.id,
                severity=DriftSeverity(alert.severity),
                similarity_score=alert.similarity_score,
                baseline_similarity=alert.baseline_similarity,
                z_score=alert.z_score,
                changed_features=changed_features,
                text_preview=alert.text_preview,
                acknowledged=alert.acknowledged,
                created_at=alert.created_at
            ))

        return DriftAlertsList(
            alerts=alert_responses,
            total=len(alert_responses),
            unacknowledged_count=unacknowledged_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting drift alerts: {str(e)}"
        )


@router.post("/drift/check", response_model=DriftDetectionResult)
@general_rate_limit
def check_drift_on_text(
    request: FingerprintComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if text indicates style drift from user's fingerprint.
    Creates an alert if drift is detected.
    """
    # Sanitize input text
    text_content = sanitize_text(request.text)

    if not text_content or len(text_content.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text must be at least 10 characters long"
        )

    # Get user's enhanced fingerprint
    enhanced_fp = db.query(EnhancedFingerprint).filter(
        EnhancedFingerprint.user_id == current_user.id
    ).first()

    if not enhanced_fp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No enhanced fingerprint found. Please generate an enhanced fingerprint first."
        )

    # Get or create drift detector
    detector = get_drift_detector(current_user.id, db)

    # Extract features from text
    try:
        text_features = extract_feature_vector(text_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting features from text: {str(e)}"
        )

    # Compare text to fingerprint
    fingerprint_dict = {
        "feature_vector": enhanced_fp.feature_vector,
        "corpus_size": enhanced_fp.corpus_size,
        "method": enhanced_fp.method
    }
    fingerprint_stats = enhanced_fp.feature_statistics

    comparator = FingerprintComparator(confidence_level=0.95)
    comparison_result = comparator.compare_with_confidence(
        text_features, fingerprint_dict, fingerprint_stats
    )

    similarity = comparison_result["similarity"]

    # Check for drift
    drift_result = detector.check_drift(
        similarity=similarity,
        feature_deviations=comparison_result.get("feature_deviations", {}),
        timestamp=datetime.utcnow()
    )

    # Create alert if drift detected
    if drift_result["drift_detected"]:
        # Convert changed_features to list of dicts for JSON storage
        changed_features_json = []
        for feature_change in drift_result.get("changed_features", []):
            changed_features_json.append({
                "feature": feature_change.get("feature", ""),
                "current_value": feature_change.get("current_value", 0.0),
                "baseline_value": feature_change.get("baseline_value", 0.0),
                "normalized_deviation": feature_change.get("normalized_deviation", 0.0)
            })

        # Create text preview
        text_preview = text_content[:200] + "..." if len(text_content) > 200 else text_content

        new_alert = DriftAlert(
            user_id=current_user.id,
            fingerprint_id=enhanced_fp.id,
            severity=drift_result["severity"],
            similarity_score=similarity,
            baseline_similarity=drift_result["baseline_mean"],
            z_score=drift_result["z_score"],
            changed_features=changed_features_json,
            text_preview=text_preview,
            acknowledged=False
        )
        db.add(new_alert)
        db.commit()

    # Format response
    changed_features_response = []
    for feature_change in drift_result.get("changed_features", []):
        changed_features_response.append(FeatureChange(
            feature=feature_change.get("feature", ""),
            current_value=feature_change.get("current_value", 0.0),
            baseline_value=feature_change.get("baseline_value", 0.0),
            normalized_deviation=feature_change.get("normalized_deviation", 0.0)
        ))

    return DriftDetectionResult(
        drift_detected=drift_result["drift_detected"],
        severity=DriftSeverity(drift_result["severity"]),
        similarity=drift_result["similarity"],
        baseline_mean=drift_result["baseline_mean"],
        z_score=drift_result["z_score"],
        confidence_interval=drift_result["confidence_interval"],
        changed_features=changed_features_response,
        timestamp=drift_result.get("timestamp")
    )


@router.post("/drift/acknowledge/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def acknowledge_alert(
    alert_id: int,
    update_baseline: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Acknowledge a drift alert.

    update_baseline: If True, recalculate baseline from recent similarities
    """
    try:
        alert = db.query(DriftAlert).filter(
            DriftAlert.id == alert_id
        ).first()

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )

        if alert.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only acknowledge your own alerts"
            )

        alert.acknowledged = True

        # Update baseline if requested
        if update_baseline:
            detector = get_drift_detector(current_user.id, db)

            # Get recent similarities from alerts
            recent_alerts = db.query(DriftAlert).filter(
                DriftAlert.user_id == current_user.id
            ).order_by(DriftAlert.created_at.desc()).limit(10).all()

            similarities = [a.similarity_score for a in recent_alerts if a.similarity_score > 0]
            if similarities:
                detector.update_baseline(similarities)

        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error acknowledging alert: {str(e)}"
        )


@router.post("/drift/baseline")
def establish_drift_baseline(
    similarities: List[float],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually establish drift baseline from similarity scores.

    Useful for initializing baseline after corpus creation.
    """
    # Validate input
    if len(similarities) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 3 similarity scores required to establish baseline"
        )

    if len(similarities) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 similarity scores allowed"
        )

    # Validate all values are between 0 and 1
    for s in similarities:
        if not 0.0 <= s <= 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All similarity scores must be between 0.0 and 1.0"
            )

    try:
        # Get or create detector
        detector = get_drift_detector(current_user.id, db)
        detector.establish_baseline(similarities)

        status_response = detector.get_status()

        return {
            "status": "baseline_established",
            "mean": status_response["baseline_mean"],
            "std": status_response["baseline_std"],
            "window_size": status_response["current_window_size"],
            "thresholds": status_response["thresholds"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error establishing baseline: {str(e)}"
        )


@router.get("/drift/status")
def get_drift_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current drift detector status for the user.
    """
    try:
        detector = get_drift_detector(current_user.id, db)
        status_response = detector.get_status()

        # Count unacknowledged alerts
        unacknowledged_count = db.query(DriftAlert).filter(
            DriftAlert.user_id == current_user.id,
            DriftAlert.acknowledged == False
        ).count()

        # Get last alert timestamp
        last_alert = db.query(DriftAlert).filter(
            DriftAlert.user_id == current_user.id
        ).order_by(DriftAlert.created_at.desc()).first()

        return {
            "baseline_established": status_response["baseline_established"],
            "baseline_mean": status_response["baseline_mean"],
            "baseline_std": status_response["baseline_std"],
            "current_window_size": status_response["current_window_size"],
            "thresholds": status_response["thresholds"],
            "unacknowledged_alerts": unacknowledged_count,
            "last_check": last_alert.created_at if last_alert else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting drift status: {str(e)}"
        )
