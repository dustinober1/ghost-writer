"""Tests for account management routes (GDPR compliance)."""
import pytest
from unittest.mock import patch, MagicMock


class TestAccountRoutes:
    """Test account management endpoints."""
    
    def test_get_account_info(self, client, auth_headers, sample_user):
        """Test getting account information."""
        response = client.get("/api/account/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == sample_user.email
        assert "data_summary" in data
        assert "writing_samples" in data["data_summary"]
        assert "analysis_results" in data["data_summary"]
    
    def test_get_account_info_unauthenticated(self, client):
        """Test account info requires authentication."""
        response = client.get("/api/account/me")
        assert response.status_code == 401
    
    def test_export_data_json(self, client, auth_headers, sample_user, test_db):
        """Test exporting user data as JSON."""
        response = client.get(
            "/api/account/export?format=json",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
    
    def test_export_data_csv(self, client, auth_headers):
        """Test exporting user data as CSV."""
        response = client.get(
            "/api/account/export?format=csv",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
    
    def test_export_data_invalid_format(self, client, auth_headers):
        """Test exporting with invalid format."""
        response = client.get(
            "/api/account/export?format=xml",
            headers=auth_headers
        )
        assert response.status_code == 400
    
    def test_delete_specific_data_samples(self, client, auth_headers, sample_user, test_db):
        """Test deleting specific data types."""
        from app.models.database import WritingSample
        
        # Add a sample first
        sample = WritingSample(
            user_id=sample_user.id,
            text_content="Test sample text",
            source_type="manual"
        )
        test_db.add(sample)
        test_db.commit()
        
        # Delete samples
        response = client.delete(
            "/api/account/data/samples",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify deletion
        count = test_db.query(WritingSample).filter(
            WritingSample.user_id == sample_user.id
        ).count()
        assert count == 0
    
    def test_delete_specific_data_analyses(self, client, auth_headers, sample_user, test_db):
        """Test deleting analysis results."""
        from app.models.database import AnalysisResult
        
        # Add an analysis
        analysis = AnalysisResult(
            user_id=sample_user.id,
            text_content="Test analysis text",
            heat_map_data={"segments": []},
            overall_ai_probability="0.5"
        )
        test_db.add(analysis)
        test_db.commit()
        
        # Delete analyses
        response = client.delete(
            "/api/account/data/analyses",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_delete_specific_data_invalid_type(self, client, auth_headers):
        """Test deleting with invalid data type."""
        response = client.delete(
            "/api/account/data/invalid",
            headers=auth_headers
        )
        assert response.status_code == 400
    
    def test_request_account_deletion(self, client, auth_headers, sample_user, test_db):
        """Test requesting account deletion."""
        response = client.post(
            "/api/account/request-deletion",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # User should be deactivated
        test_db.refresh(sample_user)
        assert sample_user.is_active == False
    
    def test_delete_account_immediately(self, client, auth_headers, sample_user, test_db):
        """Test immediate account deletion with password confirmation."""
        from app.models.database import User
        
        user_id = sample_user.id
        
        response = client.delete(
            f"/api/account/delete-immediately?password=testpassword123",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # User should be deleted
        user = test_db.query(User).filter(User.id == user_id).first()
        assert user is None
    
    def test_delete_account_wrong_password(self, client, auth_headers):
        """Test account deletion with wrong password."""
        response = client.delete(
            "/api/account/delete-immediately?password=wrongpassword",
            headers=auth_headers
        )
        assert response.status_code == 401
