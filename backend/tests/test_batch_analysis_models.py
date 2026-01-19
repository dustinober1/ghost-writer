"""Tests for batch analysis ORM models."""

from app.models.database import User, BatchAnalysisJob, BatchDocument
from sqlalchemy import select

import pytest


@pytest.mark.usefixtures("db")
def test_batch_job_defaults_and_relationships(db):
    user = User(email="batch@example.com", password_hash="hash")
    db.add(user)
    db.flush()

    job = BatchAnalysisJob(
        user_id=user.id,
        granularity="sentence",
    )
    db.add(job)
    db.commit()

    refreshed_job = db.execute(select(BatchAnalysisJob)).scalars().first()
    assert refreshed_job is not None
    assert refreshed_job.status == "PENDING"
    assert refreshed_job.processed_documents == 0
    assert refreshed_job.similarity_matrix is None
    assert refreshed_job.user == user


@pytest.mark.usefixtures("db", "test_user")
def test_batch_document_defaults_and_links(db, test_user):
    job = BatchAnalysisJob(
        user_id=test_user.id,
        granularity="sentence",
    )
    db.add(job)
    db.flush()

    document = BatchDocument(
        job_id=job.id,
        filename="doc.txt",
        source_type="upload",
        text_content="sample",
        word_count=5,
    )
    db.add(document)
    db.commit()

    refreshed_document = db.execute(select(BatchDocument)).scalars().first()
    assert refreshed_document is not None
    assert refreshed_document.status == "PENDING"
    assert refreshed_document.ai_probability is None
    assert refreshed_document.cluster_id is None
    assert refreshed_document.job == job
    assert job.documents[0] == refreshed_document
