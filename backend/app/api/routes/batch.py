"""
Batch analysis API routes for uploading and processing multiple documents.
"""
import io
import zipfile
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.database import get_db, User, BatchAnalysisJob, BatchDocument
from app.models.schemas import (
    BatchUploadResponse,
    BatchJobStatusResponse,
    BatchResultsResponse,
    BatchDocumentSummary,
    BatchClusterSummary,
    BatchDocumentDetail,
    BatchJobStatus,
    BatchDocumentStatus,
)
from app.services.analysis_service import get_analysis_service
from app.services.batch_analysis_service import get_batch_analysis_service
from app.middleware.input_sanitization import sanitize_text
from app.utils.file_validation import validate_file_size, validate_text_length
from app.utils.auth import get_current_user
import csv
import json


router = APIRouter(prefix="/api/batch", tags=["batch"])


def _extract_text_from_upload(file: UploadFile) -> tuple[str, str]:
    """
    Extract text content and filename from an uploaded file.

    Args:
        file: UploadFile object

    Returns:
        Tuple of (filename, text_content)

    Raises:
        HTTPException: If file cannot be processed
    """
    filename = file.filename or f"document_{datetime.utcnow().timestamp()}"

    # Validate file size
    validate_file_size(file)

    # Read file content
    content = file.file.read()

    # Try to decode as text
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text_content = content.decode("latin-1")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not decode file '{filename}' as text. Please ensure it's a valid text file."
            )

    # Validate text length
    validate_text_length(text_content)

    # Sanitize text
    text_content = sanitize_text(text_content, max_length=100000)

    return filename, text_content


def _process_zip_file(zip_file: UploadFile) -> List[tuple[str, str]]:
    """
    Extract text files from a ZIP archive.

    Args:
        zip_file: UploadFile containing ZIP data

    Returns:
        List of (filename, text_content) tuples

    Raises:
        HTTPException: If ZIP cannot be processed
    """
    validate_file_size(zip_file)

    try:
        zip_content = zip_file.file.read()
        zip_buffer = io.BytesIO(zip_content)

        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            files_data = []

            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    continue

                # Only process text files
                filename = file_info.filename
                if not filename.lower().endswith('.txt'):
                    continue

                # Extract content
                with zip_ref.open(file_info) as extracted_file:
                    try:
                        text_content = extracted_file.read().decode('utf-8')
                    except UnicodeDecodeError:
                        # Skip files that can't be decoded
                        continue

                # Validate and sanitize
                validate_text_length(text_content)
                text_content = sanitize_text(text_content, max_length=100000)

                files_data.append((filename, text_content))

            return files_data

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ZIP file. Please upload a valid ZIP archive."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing ZIP file: {str(e)}"
        )


@router.post("/upload", response_model=BatchUploadResponse)
async def upload_batch(
    files: List[UploadFile] = File(None),
    zip_file: UploadFile = File(None),
    granularity: str = Query("sentence", description="Analysis granularity: sentence or paragraph"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple documents for batch analysis.

    Accepts either multiple individual files or a single ZIP archive.
    Each file is processed asynchronously to analyze AI-generated content.

    Args:
        files: List of individual text files
        zip_file: Single ZIP archive containing text files
        granularity: Analysis granularity (sentence or paragraph)
        current_user: Authenticated user
        db: Database session

    Returns:
        BatchUploadResponse with job_id and initial status
    """
    if not files and not zip_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either files or zip_file must be provided"
        )

    if files and zip_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either files or zip_file, not both"
        )

    # Collect all documents
    documents_data = []

    if zip_file:
        # Process ZIP file
        if not zip_file.filename or not zip_file.filename.lower().endswith('.zip'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="zip_file must be a .zip file"
            )
        documents_data = _process_zip_file(zip_file)
    else:
        # Process individual files
        for file in files:
            filename, text_content = _extract_text_from_upload(file)
            documents_data.append((filename, text_content))

    if not documents_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid text files found. Please upload .txt files."
        )

    # Create batch job
    batch_job = BatchAnalysisJob(
        user_id=current_user.id,
        status=BatchJobStatus.PENDING,
        total_documents=len(documents_data),
        processed_documents=0,
        granularity=granularity,
        created_at=datetime.utcnow()
    )
    db.add(batch_job)
    db.commit()
    db.refresh(batch_job)

    # Create document records
    for filename, text_content in documents_data:
        word_count = len(text_content.split())
        batch_document = BatchDocument(
            job_id=batch_job.id,
            filename=filename,
            source_type="batch_upload",
            text_content=text_content,
            word_count=word_count,
            status=BatchDocumentStatus.PENDING,
            created_at=datetime.utcnow()
        )
        db.add(batch_document)

    db.commit()

    # Enqueue Celery task for processing
    from app.tasks.batch_tasks import process_batch_job
    process_batch_job.delay(batch_job.id)

    return BatchUploadResponse(
        job_id=batch_job.id,
        status=BatchJobStatus.PENDING
    )


@router.get("/{job_id}/status", response_model=BatchJobStatusResponse)
def get_batch_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of a batch analysis job.

    Args:
        job_id: Batch job ID
        current_user: Authenticated user
        db: Database session

    Returns:
        BatchJobStatusResponse with current status and progress
    """
    batch_job = db.query(BatchAnalysisJob).filter(
        BatchAnalysisJob.id == job_id,
        BatchAnalysisJob.user_id == current_user.id
    ).first()

    if not batch_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found"
        )

    progress = 0.0
    if batch_job.total_documents > 0:
        progress = (batch_job.processed_documents / batch_job.total_documents) * 100

    return BatchJobStatusResponse(
        job_id=batch_job.id,
        status=batch_job.status,
        total_documents=batch_job.total_documents,
        processed_documents=batch_job.processed_documents,
        granularity=batch_job.granularity,
        created_at=batch_job.created_at,
        started_at=batch_job.started_at,
        completed_at=batch_job.completed_at,
        error_message=batch_job.error_message,
        progress=round(progress, 2)
    )


@router.get("/{job_id}/results", response_model=BatchResultsResponse)
def get_batch_results(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the results of a completed batch analysis job.

    Includes document summaries, clusters, and similarity matrix.

    Args:
        job_id: Batch job ID
        current_user: Authenticated user
        db: Database session

    Returns:
        BatchResultsResponse with documents, clusters, and similarity matrix
    """
    batch_job = db.query(BatchAnalysisJob).filter(
        BatchAnalysisJob.id == job_id,
        BatchAnalysisJob.user_id == current_user.id
    ).first()

    if not batch_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found"
        )

    # Get all documents for this job
    documents = db.query(BatchDocument).filter(
        BatchDocument.job_id == job_id
    ).all()

    # Build document summaries
    document_summaries = []
    for doc in documents:
        confidence_level = None
        if doc.ai_probability is not None:
            if doc.ai_probability > 0.7:
                confidence_level = "HIGH"
            elif doc.ai_probability >= 0.4:
                confidence_level = "MEDIUM"
            else:
                confidence_level = "LOW"

        document_summaries.append(BatchDocumentSummary(
            id=doc.id,
            filename=doc.filename,
            word_count=doc.word_count,
            ai_probability=doc.ai_probability,
            confidence_level=confidence_level,
            cluster_id=doc.cluster_id,
            status=doc.status
        ))

    # Build cluster summaries
    cluster_summaries = []
    if batch_job.clusters:
        for cluster in batch_job.clusters:
            cluster_docs = [d for d in documents if d.cluster_id == cluster.get("cluster_id")]
            avg_prob = None
            if cluster_docs:
                probs = [d.ai_probability for d in cluster_docs if d.ai_probability is not None]
                if probs:
                    avg_prob = sum(probs) / len(probs)

            cluster_summaries.append(BatchClusterSummary(
                cluster_id=cluster.get("cluster_id", 0),
                document_count=len(cluster_docs),
                avg_ai_probability=avg_prob
            ))

    # Get similarity matrix
    similarity_matrix = batch_job.similarity_matrix

    return BatchResultsResponse(
        job=BatchJobStatusResponse(
            job_id=batch_job.id,
            status=batch_job.status,
            total_documents=batch_job.total_documents,
            processed_documents=batch_job.processed_documents,
            granularity=batch_job.granularity,
            created_at=batch_job.created_at,
            started_at=batch_job.started_at,
            completed_at=batch_job.completed_at,
            error_message=batch_job.error_message,
            progress=100.0 if batch_job.status == BatchJobStatus.COMPLETED else 0.0
        ),
        documents=document_summaries,
        clusters=cluster_summaries,
        similarity_matrix=similarity_matrix
    )


@router.get("/{job_id}/export")
async def export_batch(
    job_id: int,
    format: str = Query("csv", description="Export format: csv or json"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export batch analysis results.

    Args:
        job_id: Batch job ID
        format: Export format (csv or json)
        current_user: Authenticated user
        db: Database session

    Returns:
        StreamingResponse with exported data
    """
    if format not in ["csv", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'csv' or 'json'"
        )

    batch_job = db.query(BatchAnalysisJob).filter(
        BatchAnalysisJob.id == job_id,
        BatchAnalysisJob.user_id == current_user.id
    ).first()

    if not batch_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found"
        )

    documents = db.query(BatchDocument).filter(
        BatchDocument.job_id == job_id
    ).all()

    if format == "json":
        # Build JSON export
        export_data = {
            "job_id": job_id,
            "status": batch_job.status,
            "total_documents": batch_job.total_documents,
            "created_at": batch_job.created_at.isoformat(),
            "completed_at": batch_job.completed_at.isoformat() if batch_job.completed_at else None,
            "clusters": batch_job.clusters or [],
            "similarity_matrix": batch_job.similarity_matrix,
            "documents": []
        }

        for doc in documents:
            doc_data = {
                "id": doc.id,
                "filename": doc.filename,
                "word_count": doc.word_count,
                "ai_probability": doc.ai_probability,
                "confidence_distribution": doc.confidence_distribution,
                "cluster_id": doc.cluster_id,
                "status": doc.status,
                "error_message": doc.error_message
            }
            export_data["documents"].append(doc_data)

        # Create JSON response
        json_str = json.dumps(export_data, indent=2)
        return StreamingResponse(
            io.StringIO(json_str),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=batch_analysis_{job_id}.json"
            }
        )

    else:  # CSV format
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Document ID", "Filename", "Word Count", "AI Probability",
            "Confidence Level", "Cluster ID", "Status"
        ])

        # Write data rows
        for doc in documents:
            confidence_level = ""
            if doc.ai_probability is not None:
                if doc.ai_probability > 0.7:
                    confidence_level = "HIGH"
                elif doc.ai_probability >= 0.4:
                    confidence_level = "MEDIUM"
                else:
                    confidence_level = "LOW"

            writer.writerow([
                doc.id,
                doc.filename,
                doc.word_count,
                f"{doc.ai_probability:.4f}" if doc.ai_probability is not None else "",
                confidence_level,
                doc.cluster_id if doc.cluster_id else "",
                doc.status
            ])

        # Add job summary at the end
        writer.writerow([])
        writer.writerow(["Job Summary"])
        writer.writerow(["Job ID", job_id])
        writer.writerow(["Status", batch_job.status])
        writer.writerow(["Total Documents", batch_job.total_documents])
        writer.writerow(["Created At", batch_job.created_at.isoformat()])
        if batch_job.completed_at:
            writer.writerow(["Completed At", batch_job.completed_at.isoformat()])

        # Create response
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=batch_analysis_{job_id}.csv"
            }
        )


@router.get("/jobs", response_model=List[BatchJobStatusResponse])
def list_batch_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all batch jobs for the current user.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Authenticated user
        db: Database session

    Returns:
        List of BatchJobStatusResponse
    """
    jobs = db.query(BatchAnalysisJob).filter(
        BatchAnalysisJob.user_id == current_user.id
    ).order_by(BatchAnalysisJob.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for job in jobs:
        progress = 0.0
        if job.total_documents > 0:
            progress = (job.processed_documents / job.total_documents) * 100

        results.append(BatchJobStatusResponse(
            job_id=job.id,
            status=job.status,
            total_documents=job.total_documents,
            processed_documents=job.processed_documents,
            granularity=job.granularity,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            progress=round(progress, 2)
        ))

    return results


@router.get("/{job_id}/documents/{document_id}", response_model=BatchDocumentDetail)
def get_document_detail(
    job_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific document in a batch.

    Args:
        job_id: Batch job ID
        document_id: Document ID
        current_user: Authenticated user
        db: Database session

    Returns:
        BatchDocumentDetail with full document information
    """
    # Verify job ownership
    batch_job = db.query(BatchAnalysisJob).filter(
        BatchAnalysisJob.id == job_id,
        BatchAnalysisJob.user_id == current_user.id
    ).first()

    if not batch_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found"
        )

    # Get document
    document = db.query(BatchDocument).filter(
        BatchDocument.id == document_id,
        BatchDocument.job_id == job_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return BatchDocumentDetail(
        id=document.id,
        filename=document.filename,
        source_type=document.source_type,
        text_content=document.text_content,
        word_count=document.word_count,
        status=document.status,
        ai_probability=document.ai_probability,
        confidence_distribution=document.confidence_distribution,
        heat_map_data=document.heat_map_data,
        embedding=document.embedding,
        cluster_id=document.cluster_id,
        error_message=document.error_message,
        created_at=document.created_at
    )
