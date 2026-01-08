from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.models.database import get_db, User
from app.models.schemas import (
    WritingSampleCreate,
    WritingSampleResponse,
    FingerprintStatus,
    FingerprintResponse
)
from app.services.fingerprint_service import get_fingerprint_service
from app.utils.auth import get_current_user
import docx
import PyPDF2
import io

router = APIRouter(prefix="/api/fingerprint", tags=["fingerprint"])


@router.post("/upload", response_model=WritingSampleResponse, status_code=status.HTTP_201_CREATED)
def upload_writing_sample(
    text: str = None,
    file: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a writing sample. Can provide text directly or upload a file (txt, docx, pdf).
    """
    fingerprint_service = get_fingerprint_service()
    
    text_content = None
    
    if file:
        # Read file content
        file_content = file.file.read()
        
        if file.filename.endswith('.txt'):
            text_content = file_content.decode('utf-8')
        elif file.filename.endswith('.docx'):
            doc = docx.Document(io.BytesIO(file_content))
            text_content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        elif file.filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text_content = '\n'.join([page.extract_text() for page in pdf_reader.pages])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Supported: txt, docx, pdf"
            )
    elif text:
        text_content = text
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
