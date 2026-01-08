"""
Pytest configuration and shared fixtures.
"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import Base, get_db, User
from app.utils.auth import get_password_hash

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    from app.models.database import get_db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for a test user."""
    response = client.post(
        "/api/auth/login-json",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def override_get_current_user(test_user):
    """Override get_current_user dependency for testing."""
    from app.utils.auth import get_current_user
    
    def _override_get_current_user():
        return test_user
    
    return _override_get_current_user


@pytest.fixture(autouse=True)
def reset_services():
    """Reset global service instances before each test."""
    # Reset global instances
    import app.services.analysis_service
    import app.services.fingerprint_service
    import app.ml.contrastive_model
    import app.ml.dspy_rewriter
    
    app.services.analysis_service._analysis_service = None
    app.services.fingerprint_service._fingerprint_service = None
    app.ml.contrastive_model._model_instance = None
    app.ml.dspy_rewriter._rewriter_instance = None
    
    yield
    
    # Clean up after test
    app.services.analysis_service._analysis_service = None
    app.services.fingerprint_service._fingerprint_service = None
    app.ml.contrastive_model._model_instance = None
    app.ml.dspy_rewriter._rewriter_instance = None