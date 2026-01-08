"""
Tests for fingerprint service.
"""
import pytest
from app.services.fingerprint_service import FingerprintService, get_fingerprint_service
from app.models.database import WritingSample, Fingerprint


def test_upload_writing_sample(db, test_user):
    """Test uploading a writing sample."""
    service = FingerprintService()
    sample = service.upload_writing_sample(
        db=db,
        user_id=test_user.id,
        text_content="Sample text",
        source_type="manual"
    )
    
    assert sample.id is not None
    assert sample.user_id == test_user.id
    assert sample.text_content == "Sample text"
    assert sample.source_type == "manual"


def test_get_user_samples(db, test_user):
    """Test getting user writing samples."""
    service = FingerprintService()
    
    # Upload multiple samples
    service.upload_writing_sample(db, test_user.id, "Sample 1", "manual")
    service.upload_writing_sample(db, test_user.id, "Sample 2", "manual")
    
    samples = service.get_user_samples(db, test_user.id)
    assert len(samples) == 2


def test_generate_user_fingerprint_new(db, test_user):
    """Test generating a new fingerprint."""
    service = FingerprintService()
    
    # Upload samples
    service.upload_writing_sample(db, test_user.id, "First sample", "manual")
    service.upload_writing_sample(db, test_user.id, "Second sample", "manual")
    
    # Generate fingerprint
    fingerprint = service.generate_user_fingerprint(db, test_user.id)
    
    assert fingerprint is not None
    assert fingerprint.user_id == test_user.id
    assert "feature_vector" in fingerprint.feature_vector or isinstance(fingerprint.feature_vector, list)
    assert fingerprint.model_version is not None


def test_generate_user_fingerprint_update(db, test_user):
    """Test updating an existing fingerprint."""
    service = FingerprintService()
    
    # Create initial fingerprint
    service.upload_writing_sample(db, test_user.id, "Initial sample", "manual")
    fingerprint1 = service.generate_user_fingerprint(db, test_user.id)
    
    # Add more samples and update
    service.upload_writing_sample(db, test_user.id, "Additional sample", "manual")
    fingerprint2 = service.generate_user_fingerprint(db, test_user.id)
    
    # Should be the same fingerprint (updated)
    assert fingerprint1.id == fingerprint2.id
    assert fingerprint2.updated_at >= fingerprint1.created_at


def test_generate_user_fingerprint_no_samples(db, test_user):
    """Test generating fingerprint without samples."""
    service = FingerprintService()
    with pytest.raises(ValueError, match="No writing samples"):
        service.generate_user_fingerprint(db, test_user.id)


def test_get_user_fingerprint_exists(db, test_user):
    """Test getting existing fingerprint."""
    service = FingerprintService()
    
    # Create fingerprint
    service.upload_writing_sample(db, test_user.id, "Sample", "manual")
    created = service.generate_user_fingerprint(db, test_user.id)
    
    # Retrieve it
    retrieved = service.get_user_fingerprint(db, test_user.id)
    assert retrieved is not None
    assert retrieved.id == created.id


def test_get_user_fingerprint_not_exists(db, test_user):
    """Test getting non-existent fingerprint."""
    service = FingerprintService()
    fingerprint = service.get_user_fingerprint(db, test_user.id)
    assert fingerprint is None


def test_fine_tune_fingerprint_existing(db, test_user):
    """Test fine-tuning existing fingerprint."""
    service = FingerprintService()
    
    # Create initial fingerprint
    service.upload_writing_sample(db, test_user.id, "Initial", "manual")
    service.generate_user_fingerprint(db, test_user.id)
    
    # Fine-tune
    new_samples = ["New sample 1", "New sample 2"]
    updated = service.fine_tune_fingerprint(
        db=db,
        user_id=test_user.id,
        new_samples=new_samples,
        weight=0.3
    )
    
    assert updated is not None
    assert updated.user_id == test_user.id


def test_fine_tune_fingerprint_no_existing(db, test_user):
    """Test fine-tuning when no fingerprint exists."""
    service = FingerprintService()
    
    new_samples = ["Sample 1", "Sample 2"]
    fingerprint = service.fine_tune_fingerprint(
        db=db,
        user_id=test_user.id,
        new_samples=new_samples,
        weight=0.3
    )
    
    # Should create new fingerprint
    assert fingerprint is not None
    assert fingerprint.user_id == test_user.id


def test_get_fingerprint_status_no_fingerprint(db, test_user):
    """Test getting status when no fingerprint exists."""
    service = FingerprintService()
    status = service.get_fingerprint_status(db, test_user.id)
    
    assert status["has_fingerprint"] == False
    assert status["sample_count"] == 0
    assert status["fingerprint"] is None


def test_get_fingerprint_status_with_fingerprint(db, test_user):
    """Test getting status when fingerprint exists."""
    service = FingerprintService()
    
    # Create fingerprint
    service.upload_writing_sample(db, test_user.id, "Sample 1", "manual")
    service.upload_writing_sample(db, test_user.id, "Sample 2", "manual")
    service.generate_user_fingerprint(db, test_user.id)
    
    status = service.get_fingerprint_status(db, test_user.id)
    
    assert status["has_fingerprint"] == True
    assert status["sample_count"] == 2
    assert status["fingerprint"] is not None


def test_get_fingerprint_service():
    """Test getting fingerprint service instance."""
    service1 = get_fingerprint_service()
    service2 = get_fingerprint_service()
    # Should return the same instance
    assert service1 is service2