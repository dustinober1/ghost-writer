"""Tests for admin routes."""
import pytest
from app.models.database import User
from app.utils.auth import get_password_hash


class TestAdminRoutes:
    """Test admin management endpoints."""
    
    @pytest.fixture
    def admin_user(self, test_db):
        """Create an admin user."""
        admin = User(
            email="admin@test.com",
            password_hash=get_password_hash("adminpassword123"),
            email_verified=True,
            is_active=True,
            is_admin=True
        )
        test_db.add(admin)
        test_db.commit()
        test_db.refresh(admin)
        return admin
    
    @pytest.fixture
    def admin_headers(self, client, admin_user):
        """Get auth headers for admin user."""
        response = client.post(
            "/api/auth/login-json",
            json={"email": "admin@test.com", "password": "adminpassword123"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_stats_as_admin(self, client, admin_headers):
        """Test getting system stats as admin."""
        response = client.get("/api/admin/stats", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "total_analyses" in data
        assert "analyses_last_24h" in data
    
    def test_get_stats_as_non_admin(self, client, auth_headers):
        """Test non-admin cannot access stats."""
        response = client.get("/api/admin/stats", headers=auth_headers)
        assert response.status_code == 403
    
    def test_get_stats_unauthenticated(self, client):
        """Test unauthenticated access to stats."""
        response = client.get("/api/admin/stats")
        assert response.status_code == 401
    
    def test_list_users(self, client, admin_headers, sample_user):
        """Test listing users as admin."""
        response = client.get("/api/admin/users", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert len(data["users"]) > 0
    
    def test_list_users_with_search(self, client, admin_headers, sample_user):
        """Test searching users."""
        response = client.get(
            f"/api/admin/users?search={sample_user.email[:5]}",
            headers=admin_headers
        )
        assert response.status_code == 200
    
    def test_get_user_details(self, client, admin_headers, sample_user):
        """Test getting user details."""
        response = client.get(
            f"/api/admin/users/{sample_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["user"]["email"] == sample_user.email
        assert "stats" in data
        assert "recent_analyses" in data
    
    def test_get_user_details_not_found(self, client, admin_headers):
        """Test getting non-existent user."""
        response = client.get("/api/admin/users/99999", headers=admin_headers)
        assert response.status_code == 404
    
    def test_deactivate_user(self, client, admin_headers, sample_user, test_db):
        """Test deactivating a user."""
        response = client.post(
            f"/api/admin/users/{sample_user.id}/deactivate",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        test_db.refresh(sample_user)
        assert sample_user.is_active == False
    
    def test_activate_user(self, client, admin_headers, sample_user, test_db):
        """Test activating a user."""
        # First deactivate
        sample_user.is_active = False
        test_db.commit()
        
        response = client.post(
            f"/api/admin/users/{sample_user.id}/activate",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        test_db.refresh(sample_user)
        assert sample_user.is_active == True
    
    def test_unlock_user(self, client, admin_headers, sample_user, test_db):
        """Test unlocking a locked user."""
        from datetime import datetime, timedelta
        
        # Lock the user
        sample_user.failed_login_attempts = 5
        sample_user.locked_until = datetime.utcnow() + timedelta(hours=1)
        test_db.commit()
        
        response = client.post(
            f"/api/admin/users/{sample_user.id}/unlock",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        test_db.refresh(sample_user)
        assert sample_user.failed_login_attempts == 0
        assert sample_user.locked_until is None
    
    def test_verify_user_email(self, client, admin_headers, sample_user, test_db):
        """Test manually verifying user email."""
        sample_user.email_verified = False
        test_db.commit()
        
        response = client.post(
            f"/api/admin/users/{sample_user.id}/verify-email",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        test_db.refresh(sample_user)
        assert sample_user.email_verified == True
    
    def test_delete_user(self, client, admin_headers, sample_user, test_db):
        """Test deleting a user."""
        user_id = sample_user.id
        
        response = client.delete(
            f"/api/admin/users/{user_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        user = test_db.query(User).filter(User.id == user_id).first()
        assert user is None
    
    def test_admin_cannot_delete_self(self, client, admin_headers, admin_user):
        """Test admin cannot delete their own account."""
        response = client.delete(
            f"/api/admin/users/{admin_user.id}",
            headers=admin_headers
        )
        assert response.status_code == 400
    
    def test_list_recent_analyses(self, client, admin_headers):
        """Test listing recent analyses."""
        response = client.get("/api/admin/analyses", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "analyses" in data
        assert "total" in data
