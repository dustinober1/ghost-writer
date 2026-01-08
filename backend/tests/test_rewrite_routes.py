"""
Tests for rewrite routes.
"""
import pytest
from fastapi import status
from unittest.mock import patch, MagicMock


def test_rewrite_with_target_style(client, auth_headers):
    """Test rewriting text with target style."""
    with patch('app.api.routes.rewrite.get_dspy_rewriter') as mock_get_rewriter:
        mock_rewriter = MagicMock()
        mock_rewriter.rewrite_text.return_value = "Rewritten text with style"
        mock_get_rewriter.return_value = mock_rewriter
        
        response = client.post(
            "/api/rewrite/rewrite",
            headers=auth_headers,
            json={
                "text": "Original text to rewrite",
                "target_style": "Write in a formal academic style"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["original_text"] == "Original text to rewrite"
        assert data["rewritten_text"] == "Rewritten text with style"
        assert "rewrite_id" in data
        assert "created_at" in data


def test_rewrite_with_fingerprint(client, auth_headers, db, test_user):
    """Test rewriting text using user's fingerprint."""
    from app.services.fingerprint_service import get_fingerprint_service
    
    # Create fingerprint
    fingerprint_service = get_fingerprint_service()
    fingerprint_service.upload_writing_sample(
        db=db,
        user_id=test_user.id,
        text_content="Sample writing",
        source_type="manual"
    )
    fingerprint_service.generate_user_fingerprint(db, test_user.id)
    
    with patch('app.api.routes.rewrite.get_dspy_rewriter') as mock_get_rewriter:
        mock_rewriter = MagicMock()
        mock_rewriter.rewrite_with_fingerprint.return_value = "Rewritten with fingerprint"
        mock_get_rewriter.return_value = mock_rewriter
        
        response = client.post(
            "/api/rewrite/rewrite",
            headers=auth_headers,
            json={
                "text": "Original text",
                "target_style": None
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "rewritten_text" in data


def test_rewrite_no_fingerprint(client, auth_headers):
    """Test rewriting without fingerprint and no target style."""
    with patch('app.api.routes.rewrite.get_dspy_rewriter') as mock_get_rewriter:
        mock_rewriter = MagicMock()
        mock_get_rewriter.return_value = mock_rewriter
        
        response = client.post(
            "/api/rewrite/rewrite",
            headers=auth_headers,
            json={
                "text": "Original text",
                "target_style": None
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fingerprint" in response.json()["detail"].lower()


def test_rewrite_empty_text(client, auth_headers):
    """Test rewriting with empty text."""
    with patch('app.api.routes.rewrite.get_dspy_rewriter') as mock_get_rewriter:
        mock_rewriter = MagicMock()
        mock_rewriter.rewrite_text.side_effect = ValueError("Text cannot be empty")
        mock_get_rewriter.return_value = mock_rewriter
        
        response = client.post(
            "/api/rewrite/rewrite",
            headers=auth_headers,
            json={
                "text": "",
                "target_style": "Some style"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_rewrite_unauthorized(client):
    """Test rewriting without authentication."""
    response = client.post(
        "/api/rewrite/rewrite",
        json={
            "text": "Original text",
            "target_style": "Some style"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_rewrite_history(client, auth_headers):
    """Test getting rewrite history."""
    response = client.get(
        "/api/rewrite/history",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "history" in data
    assert isinstance(data["history"], list)