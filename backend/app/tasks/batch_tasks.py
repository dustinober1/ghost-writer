"""
Celery tasks for batch document analysis processing.
"""
from app.celery_app import celery_app
from app.services.analysis_service import get_analysis_service
from app.services.batch_analysis_service import get_batch_analysis_service
from app.models.database import SessionLocal, BatchAnalysisJob, BatchDocument
from app.models.schemas import BatchJobStatus, BatchDocumentStatus
from app.ml.ollama_embeddings import get_ollama_embedding
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.process_batch_job")
def process_batch_job(job_id: int) -> dict:
    """
    Process all documents in a batch analysis job.

    This task:
    1. Analyzes each document for AI probability
    2. Generates embeddings for each document
    3. Computes similarity matrix
    4. Clusters documents based on similarity
    5. Updates job status throughout

    Args:
        job_id: The batch job ID to process

    Returns:
        Dict with job_id, status, and summary
    """
    db = SessionLocal()
    analysis_service = get_analysis_service()
    batch_service = get_batch_analysis_service()

    try:
        # Get the job
        job = db.query(BatchAnalysisJob).filter(BatchAnalysisJob.id == job_id).first()
        if not job:
            logger.error(f"Batch job {job_id} not found")
            return {"job_id": job_id, "status": "error", "error": "Job not found"}

        # Update status to processing
        job.status = BatchJobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        db.commit()

        # Get all documents for this job
        documents = db.query(BatchDocument).filter(
            BatchDocument.job_id == job_id
        ).order_by(BatchDocument.id).all()

        if not documents:
            logger.warning(f"No documents found for job {job_id}")
            job.status = BatchJobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.processed_documents = 0
            db.commit()
            return {
                "job_id": job_id,
                "status": "completed",
                "total_documents": 0,
                "processed_documents": 0
            }

        # Store embeddings and results
        embeddings = []
        document_results = []

        for doc in documents:
            try:
                # Update document status
                doc.status = BatchDocumentStatus.PROCESSING
                db.commit()

                # Analyze the document
                result = analysis_service.analyze_text(
                    text=doc.text_content,
                    granularity=job.granularity,
                    use_cache=True
                )

                # Update document with analysis results
                doc.ai_probability = result.get("overall_ai_probability")
                doc.confidence_distribution = result.get("confidence_distribution")
                doc.heat_map_data = {
                    "segments": [s.dict() if hasattr(s, 'dict') else s for s in result.get("segments", [])],
                    "overall_ai_probability": result.get("overall_ai_probability")
                }

                # Generate embedding for this document
                embedding = get_ollama_embedding(doc.text_content)
                if embedding is not None:
                    doc.embedding = embedding
                    embeddings.append(embedding)
                else:
                    # Use zero vector if embedding fails
                    doc.embedding = None
                    embeddings.append([0.0] * 768)  # Default embedding size

                # Update document status to completed
                doc.status = BatchDocumentStatus.COMPLETED
                doc.cluster_id = None  # Will be set after clustering

                # Update job progress
                job.processed_documents += 1
                db.commit()

                document_results.append({
                    "document_id": doc.id,
                    "ai_probability": doc.ai_probability
                })

                logger.info(f"Processed document {doc.id} for job {job_id}: {doc.filename}")

            except Exception as e:
                logger.error(f"Error processing document {doc.id}: {str(e)}")
                doc.status = BatchDocumentStatus.FAILED
                doc.error_message = str(e)
                job.processed_documents += 1
                db.commit()

                # Add placeholder embedding to maintain matrix alignment
                embeddings.append([0.0] * 768)

        # Compute similarity matrix
        try:
            if embeddings:
                similarity_matrix = batch_service.build_similarity_matrix(embeddings)
                job.similarity_matrix = similarity_matrix

                # Cluster documents
                clusters = batch_service.cluster_documents(embeddings, threshold=0.85)
                job.clusters = clusters

                # Update cluster_id for each document
                for cluster in clusters:
                    cluster_id = cluster.get("cluster_id")
                    document_indices = cluster.get("document_ids", [])

                    # Map indices back to documents
                    for idx in document_indices:
                        if idx < len(documents):
                            documents[idx].cluster_id = cluster_id

                db.commit()
                logger.info(f"Computed similarity matrix and {len(clusters)} clusters for job {job_id}")

        except Exception as e:
            logger.error(f"Error computing similarity/clustering for job {job_id}: {str(e)}")

        # Mark job as completed
        job.status = BatchJobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Completed batch job {job_id}: {job.processed_documents}/{job.total_documents} documents")

        return {
            "job_id": job_id,
            "status": "completed",
            "total_documents": job.total_documents,
            "processed_documents": job.processed_documents,
            "clusters": len(job.clusters) if job.clusters else 0
        }

    except Exception as e:
        logger.error(f"Fatal error processing batch job {job_id}: {str(e)}")

        # Update job status to failed
        job.status = BatchJobStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()

        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e)
        }

    finally:
        db.close()


@celery_app.task(name="app.tasks.retry_batch_job")
def retry_batch_job(job_id: int) -> dict:
    """
    Retry failed documents in a batch job.

    Args:
        job_id: The batch job ID to retry

    Returns:
        Dict with retry results
    """
    db = SessionLocal()

    try:
        # Get the job
        job = db.query(BatchAnalysisJob).filter(BatchAnalysisJob.id == job_id).first()
        if not job:
            return {"job_id": job_id, "status": "error", "error": "Job not found"}

        # Get failed documents
        failed_docs = db.query(BatchDocument).filter(
            BatchDocument.job_id == job_id,
            BatchDocument.status == BatchDocumentStatus.FAILED
        ).all()

        if not failed_docs:
            return {
                "job_id": job_id,
                "status": "completed",
                "retried": 0,
                "message": "No failed documents to retry"
            }

        # Reset job status
        job.status = BatchJobStatus.PROCESSING
        db.commit()

        # Re-process using the main task
        result = process_batch_job(job_id)

        return {
            "job_id": job_id,
            "status": result.get("status"),
            "retried": len(failed_docs)
        }

    finally:
        db.close()
