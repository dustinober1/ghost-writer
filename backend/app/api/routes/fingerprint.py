from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db, User, FingerprintSample, EnhancedFingerprint
from app.models.schemas import (
    WritingSampleCreate,
    WritingSampleResponse,
    FingerprintStatus,
    FingerprintResponse,
    FingerprintSampleCreate,
    FingerprintSampleResponse,
    CorpusStatus,
    EnhancedFingerprintResponse
)
from app.services.fingerprint_service import get_fingerprint_service
from app.utils.auth import get_current_user
from app.middleware.rate_limit import general_rate_limit
from app.utils.file_validation import validate_upload_file, validate_text_length
from app.middleware.input_sanitization import sanitize_text, sanitize_filename
from app.ml.fingerprint.corpus_builder import FingerprintCorpusBuilder
from app.ml.feature_extraction import extract_feature_vector
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
