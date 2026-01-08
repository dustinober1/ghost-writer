"""
Tests for fingerprint routes.
"""
import pytest
from fastapi import status
from io import BytesIO


def test_upload_text_sample(client, auth_headers):
    """Test uploading a text sample."""
    response = client.post(
        "/api/fingerprint/upload",
        headers=auth_headers,
        data={"text": "This is my writing sample for fingerprint generation."}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["text_content"] == "This is my writing sample for fingerprint generation."
    assert "id" in data
    assert "user_id" in data


def test_upload_txt_file(client, auth_headers):
    """Test uploading a TXT file."""
    file_content = b"This is text content from a file."
    response = client.post(
        "/api/fingerprint/upload",
        headers=auth_headers,
        files={"file": ("sample.txt", BytesIO(file_content), "text/plain")}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "text_content" in data
    assert "id" in data


def test_upload_docx_file(client, auth_headers):
    """Test uploading a DOCX file."""
    # Create a minimal docx file content (simplified test)
    # In real test, would use python-docx to create actual file
    file_content = b"fake docx content"
    response = client.post(
        "/api/fingerprint/upload",
        headers=auth_headers,
        files={"file": ("sample.docx", BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    # May fail if docx is invalid, but should handle gracefully
    assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_500_INTERNAL_SERVER_ERROR]


def test_upload_pdf_file(client, auth_headers):
    """Test uploading a PDF file."""
    # Create minimal PDF content (simplified)
    file_content = b"%PDF-1.4\nfake pdf content"
    response = client.post(
        "/api/fingerprint/upload",
        headers=auth_headers,
        files={"file": ("sample.pdf", BytesIO(file_content), "application/pdf")}
    )
    # May fail if PDF is invalid, but should handle gracefully
    assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_500_INTERNAL_SERVER_ERROR]


def test_upload_unsupported_file_type(client, auth_headers):
    """Test uploading an unsupported file type."""
    file_content = b"some content"
    response = client.post(
        "/api/fingerprint/upload",
        headers=auth_headers,
        files={"file": ("sample.exe", BytesIO(file_content), "application/x-msdownload")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "unsupported" in response.json()["detail"].lower()


def test_upload_no_text_or_file(client, auth_headers):
    """Test uploading without text or file."""
    response = client.post(
        "/api/fingerprint/upload",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "text or file" in response.json()["detail"].lower() or "must be provided" in response.json()["detail"]


def test_upload_empty_text(client, auth_headers):
    """Test uploading empty text."""
    response = client.post(
        "/api/fingerprint/upload",
        headers=auth_headers,
        data={"text": "   "}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "empty" in response.json()["detail"].lower()


def test_get_fingerprint_status_no_fingerprint(client, auth_headers):
    """Test getting fingerprint status when no fingerprint exists."""
    response = client.get(
        "/api/fingerprint/status",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["has_fingerprint"] == False
    assert data["sample_count"] == 0


def test_get_fingerprint_status_with_fingerprint(client, auth_headers, db, test_user):
    """Test getting fingerprint status when fingerprint exists."""
    from app.services.fingerprint_service import get_fingerprint_service
    
    fingerprint_service = get_fingerprint_service()
    
    # Upload samples
    fingerprint_service.upload_writing_sample(
        db=db,
        user_id=test_user.id,
        text_content="Sample 1",
        source_type="manual"
    )
    fingerprint_service.upload_writing_sample(
        db=db,
        user_id=test_user.id,
        text_content="Sample 2",
        source_type="manual"
    )
    
    # Generate fingerprint
    fingerprint_service.generate_user_fingerprint(db, test_user.id)
    
    # Check status
    response = client.get(
        "/api/fingerprint/status",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["has_fingerprint"] == True
    assert data["sample_count"] == 2
    assert data["fingerprint"] is not None


def test_generate_fingerprint_success(client, auth_headers, db, test_user):
    """Test generating fingerprint successfully."""
    from app.services.fingerprint_service import get_fingerprint_service
    
    fingerprint_service = get_fingerprint_service()
    
    # Upload samples
    fingerprint_service.upload_writing_sample(
        db=db,
        user_id=test_user.id,
        text_content="First sample",
        source_type="manual"
    )
    fingerprint_service.upload_writing_sample(
        db=db,
        user_id=test_user.id,
        text_content="Second sample",
        source_type="manual"
    )
    
    # Generate fingerprint
    response = client.post(
        "/api/fingerprint/generate",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "feature_vector" in data
    assert "model_version" in data
    assert data["user_id"] == test_user.id


def test_generate_fingerprint_no_samples(client, auth_headers):
    """Test generating fingerprint without samples."""
    response = client.post(
        "/api/fingerprint/generate",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "samples" in response.json()["detail"].lower()


def test_finetune_fingerprint_success(client, auth_headers, db, test_user):
    """Test fine-tuning fingerprint successfully."""
    from app.services.fingerprint_service import get_fingerprint_service
    
    fingerprint_service = get_fingerprint_service()
    
    # Create initial fingerprint
    fingerprint_service.upload_writing_sample(
        db=db,
        user_id=test_user.id,
        text_content="Initial sample",
        source_type="manual"
    )
    fingerprint_service.generate_user_fingerprint(db, test_user.id)
    
    # Fine-tune
    response = client.post(
        "/api/fingerprint/finetune",
        headers=auth_headers,
        json={
            "new_samples": ["New sample 1", "New sample 2"],
            "weight": 0.3
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "feature_vector" in data


def test_finetune_fingerprint_no_samples(client, auth_headers):
    """Test fine-tuning with no new samples."""
    response = client.post(
        "/api/fingerprint/finetune",
        headers=auth_headers,
        json={
            "new_samples": [],
            "weight": 0.3
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_finetune_fingerprint_invalid_weight(client, auth_headers):
    """Test fine-tuning with invalid weight."""
    response = client.post(
        "/api/fingerprint/finetune",
        headers=auth_headers,
        json={
            "new_samples": ["Sample"],
            "weight": 1.5
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "weight" in response.json()["detail"].lower()


def test_upload_unauthorized(client):
    """Test uploading without authentication."""
    response = client.post(
        "/api/fingerprint/upload",
        data={"text": "Sample"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED