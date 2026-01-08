"""
Tests for analysis routes.
"""
import pytest
from fastapi import status


def test_analyze_text_success(client, auth_headers):
    """Test successful text analysis."""
    response = client.post(
        "/api/analysis/analyze",
        headers=auth_headers,
        json={
            "text": "This is a sample text for analysis. It contains multiple sentences.",
            "granularity": "sentence"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "heat_map_data" in data
    assert "segments" in data["heat_map_data"]
    assert "overall_ai_probability" in data["heat_map_data"]
    assert "analysis_id" in data
    assert "created_at" in data
    assert len(data["heat_map_data"]["segments"]) > 0


def test_analyze_text_paragraph_granularity(client, auth_headers):
    """Test text analysis with paragraph granularity."""
    response = client.post(
        "/api/analysis/analyze",
        headers=auth_headers,
        json={
            "text": "First paragraph.\n\nSecond paragraph.\n\nThird paragraph.",
            "granularity": "paragraph"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["heat_map_data"]["segments"]) >= 1


def test_analyze_text_invalid_granularity(client, auth_headers):
    """Test text analysis with invalid granularity."""
    response = client.post(
        "/api/analysis/analyze",
        headers=auth_headers,
        json={
            "text": "Sample text",
            "granularity": "invalid"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_analyze_text_empty(client, auth_headers):
    """Test text analysis with empty text."""
    response = client.post(
        "/api/analysis/analyze",
        headers=auth_headers,
        json={
            "text": "",
            "granularity": "sentence"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_analyze_text_unauthorized(client):
    """Test text analysis without authentication."""
    response = client.post(
        "/api/analysis/analyze",
        json={
            "text": "Sample text",
            "granularity": "sentence"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_analyze_text_with_fingerprint(client, auth_headers, db, test_user):
    """Test text analysis with user fingerprint."""
    from app.services.fingerprint_service import get_fingerprint_service
    from app.models.database import WritingSample
    
    # Create writing samples and fingerprint
    fingerprint_service = get_fingerprint_service()
    sample = fingerprint_service.upload_writing_sample(
        db=db,
        user_id=test_user.id,
        text_content="This is my writing sample. It demonstrates my style.",
        source_type="manual"
    )
    fingerprint_service.generate_user_fingerprint(db, test_user.id)
    
    # Analyze text (should use fingerprint)
    response = client.post(
        "/api/analysis/analyze",
        headers=auth_headers,
        json={
            "text": "This is a sample text for analysis.",
            "granularity": "sentence"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "heat_map_data" in data