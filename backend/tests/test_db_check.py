"""
Tests for database check utilities.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.utils.db_check import check_db_connection, is_db_available


def test_check_db_connection_success():
    """Test successful database connection check."""
    with patch('app.utils.db_check.engine') as mock_engine:
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = None
        
        is_connected, message = check_db_connection()
        
        assert is_connected == True
        assert "successful" in message.lower() or "success" in message.lower()


def test_check_db_connection_failure():
    """Test failed database connection check."""
    with patch('app.utils.db_check.engine') as mock_engine:
        mock_engine.connect.side_effect = Exception("Connection failed")
        
        is_connected, message = check_db_connection()
        
        assert is_connected == False
        assert "failed" in message.lower() or "error" in message.lower()


def test_is_db_available_true():
    """Test is_db_available when database is available."""
    with patch('app.utils.db_check.check_db_connection', return_value=(True, "Success")):
        assert is_db_available() == True


def test_is_db_available_false():
    """Test is_db_available when database is not available."""
    with patch('app.utils.db_check.check_db_connection', return_value=(False, "Failed")):
        assert is_db_available() == False