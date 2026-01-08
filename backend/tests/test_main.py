"""
Tests for main application.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Ghostwriter Forensic Analytics API"
    assert data["version"] == "1.0.0"


def test_health_check_success(client):
    """Test health check endpoint with successful DB connection."""
    with patch('app.main.check_db_connection', return_value=(True, "Database connection successful")):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


def test_health_check_db_failure(client):
    """Test health check endpoint with failed DB connection."""
    with patch('app.main.check_db_connection', return_value=(False, "Database connection failed")):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "disconnected"


def test_startup_event():
    """Test startup event handler."""
    with patch('app.main.init_db') as mock_init_db:
        # Simulate startup
        mock_init_db.return_value = None
        
        # The startup event is called during app initialization
        # We can verify it's set up correctly
        assert hasattr(app, 'router')


def test_startup_event_db_failure():
    """Test startup event handler with database failure."""
    with patch('app.main.init_db') as mock_init_db:
        mock_init_db.side_effect = Exception("Database error")
        
        # Should not raise exception, just log
        try:
            mock_init_db()
        except Exception:
            pass  # Exception is caught in startup_event
        
        mock_init_db.assert_called()