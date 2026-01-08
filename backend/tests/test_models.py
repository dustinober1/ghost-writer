"""
Tests for database models and schemas.
"""
import pytest
from datetime import datetime
from app.models.database import User, WritingSample, Fingerprint, AnalysisResult
from app.models.schemas import (
    UserCreate, UserResponse, Token,
    WritingSampleCreate, WritingSampleResponse,
    FingerprintResponse, FingerprintStatus,
    AnalysisRequest, AnalysisResponse, HeatMapData, TextSegment,
    RewriteRequest, RewriteResponse
)


def test_user_model(db):
    """Test User model creation."""
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.created_at is not None


def test_writing_sample_model(db, test_user):
    """Test WritingSample model creation."""
    sample = WritingSample(
        user_id=test_user.id,
        text_content="Sample text",
        source_type="manual"
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)
    
    assert sample.id is not None
    assert sample.user_id == test_user.id
    assert sample.text_content == "Sample text"
    assert sample.uploaded_at is not None


def test_fingerprint_model(db, test_user):
    """Test Fingerprint model creation."""
    fingerprint = Fingerprint(
        user_id=test_user.id,
        feature_vector=[0.1, 0.2, 0.3] * 5,  # 15 values (close to 13)
        model_version="1.0"
    )
    db.add(fingerprint)
    db.commit()
    db.refresh(fingerprint)
    
    assert fingerprint.id is not None
    assert fingerprint.user_id == test_user.id
    assert isinstance(fingerprint.feature_vector, list)
    assert fingerprint.created_at is not None


def test_analysis_result_model(db, test_user):
    """Test AnalysisResult model creation."""
    result = AnalysisResult(
        user_id=test_user.id,
        text_content="Text to analyze",
        heat_map_data={"segments": [], "overall_ai_probability": 0.5},
        overall_ai_probability="0.5"
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    
    assert result.id is not None
    assert result.user_id == test_user.id
    assert isinstance(result.heat_map_data, dict)
    assert result.created_at is not None


def test_user_relationships(db, test_user):
    """Test User model relationships."""
    # Create related objects
    sample = WritingSample(
        user_id=test_user.id,
        text_content="Sample",
        source_type="manual"
    )
    fingerprint = Fingerprint(
        user_id=test_user.id,
        feature_vector=[0.1] * 13,
        model_version="1.0"
    )
    db.add(sample)
    db.add(fingerprint)
    db.commit()
    
    # Refresh user to load relationships
    db.refresh(test_user)
    
    assert len(test_user.writing_samples) >= 1
    assert len(test_user.fingerprints) >= 1


def test_user_create_schema():
    """Test UserCreate schema."""
    user_data = UserCreate(email="test@example.com", password="password123")
    assert user_data.email == "test@example.com"
    assert user_data.password == "password123"


def test_user_response_schema(test_user):
    """Test UserResponse schema."""
    user_response = UserResponse.model_validate(test_user)
    assert user_response.email == test_user.email
    assert user_response.id == test_user.id


def test_token_schema():
    """Test Token schema."""
    token = Token(access_token="token123", token_type="bearer")
    assert token.access_token == "token123"
    assert token.token_type == "bearer"


def test_analysis_request_schema():
    """Test AnalysisRequest schema."""
    request = AnalysisRequest(text="Sample text", granularity="sentence")
    assert request.text == "Sample text"
    assert request.granularity == "sentence"


def test_text_segment_schema():
    """Test TextSegment schema."""
    segment = TextSegment(
        text="Segment text",
        ai_probability=0.7,
        start_index=0,
        end_index=12
    )
    assert segment.text == "Segment text"
    assert segment.ai_probability == 0.7


def test_heat_map_data_schema():
    """Test HeatMapData schema."""
    segments = [
        TextSegment(text="First", ai_probability=0.5, start_index=0, end_index=5),
        TextSegment(text="Second", ai_probability=0.6, start_index=6, end_index=12)
    ]
    heat_map = HeatMapData(segments=segments, overall_ai_probability=0.55)
    assert len(heat_map.segments) == 2
    assert heat_map.overall_ai_probability == 0.55


def test_rewrite_request_schema():
    """Test RewriteRequest schema."""
    request = RewriteRequest(text="Original", target_style="Formal style")
    assert request.text == "Original"
    assert request.target_style == "Formal style"


def test_rewrite_response_schema():
    """Test RewriteResponse schema."""
    response = RewriteResponse(
        original_text="Original",
        rewritten_text="Rewritten",
        rewrite_id=1,
        created_at=datetime.utcnow()
    )
    assert response.original_text == "Original"
    assert response.rewritten_text == "Rewritten"