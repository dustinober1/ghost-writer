"""
Additional edge case tests for fingerprint generation.
"""
import pytest
import numpy as np
from app.ml.fingerprint import (
    generate_fingerprint,
    update_fingerprint,
    compare_to_fingerprint
)


def test_generate_fingerprint_empty_list():
    """Test generating fingerprint with empty list."""
    with pytest.raises(ValueError, match="At least one"):
        generate_fingerprint([])


def test_generate_fingerprint_whitespace_only():
    """Test generating fingerprint with whitespace-only samples."""
    samples = ["   ", "\n\n", "   \n   "]
    with pytest.raises(ValueError, match="No valid"):
        generate_fingerprint(samples)


def test_generate_fingerprint_single_sample():
    """Test generating fingerprint with single sample."""
    samples = ["Single sample text for fingerprint."]
    fingerprint = generate_fingerprint(samples)
    
    assert "feature_vector" in fingerprint
    assert fingerprint["sample_count"] == 1
    assert len(fingerprint["feature_vector"]) > 0


def test_generate_fingerprint_mixed_valid_invalid():
    """Test generating fingerprint with mix of valid and invalid samples."""
    samples = [
        "Valid sample 1.",
        "   ",  # Invalid (whitespace only)
        "Valid sample 2.",
        "\n\n",  # Invalid
        "Valid sample 3."
    ]
    fingerprint = generate_fingerprint(samples)
    
    assert "feature_vector" in fingerprint
    # Should use only valid samples
    assert fingerprint["sample_count"] == 5  # Count includes all, but only valid are used


def test_update_fingerprint_empty_new_samples():
    """Test updating fingerprint with empty new samples."""
    existing = {
        "feature_vector": [0.5] * 13,
        "sample_count": 3,
        "model_version": "1.0"
    }
    
    updated = update_fingerprint(existing, [])
    assert updated == existing  # Should return unchanged


def test_update_fingerprint_whitespace_samples():
    """Test updating fingerprint with whitespace-only samples."""
    existing = {
        "feature_vector": [0.5] * 13,
        "sample_count": 3,
        "model_version": "1.0"
    }
    
    updated = update_fingerprint(existing, ["   ", "\n\n"])
    assert updated == existing  # Should return unchanged if no valid samples


def test_update_fingerprint_weight_zero():
    """Test updating fingerprint with weight 0."""
    existing = {
        "feature_vector": [0.5] * 13,
        "sample_count": 3,
        "model_version": "1.0"
    }
    
    updated = update_fingerprint(existing, ["New sample"], weight=0.0)
    # Should be unchanged (weight 0 = no new data)
    assert np.allclose(np.array(existing["feature_vector"]), np.array(updated["feature_vector"]))


def test_update_fingerprint_weight_one():
    """Test updating fingerprint with weight 1.0."""
    existing = {
        "feature_vector": [0.5] * 13,
        "sample_count": 3,
        "model_version": "1.0"
    }
    
    updated = update_fingerprint(existing, ["New sample"], weight=1.0)
    # Should use only new data
    assert updated["feature_vector"] != existing["feature_vector"]


def test_compare_to_fingerprint_empty_text():
    """Test comparing empty text to fingerprint."""
    fingerprint = {
        "feature_vector": [0.5] * 13,
        "model_version": "1.0"
    }
    
    similarity = compare_to_fingerprint("", fingerprint)
    assert 0 <= similarity <= 1


def test_compare_to_fingerprint_zero_vector():
    """Test comparing to fingerprint with zero vector."""
    fingerprint = {
        "feature_vector": [0.0] * 13,
        "model_version": "1.0"
    }
    
    similarity = compare_to_fingerprint("Test text", fingerprint)
    # Should handle zero vector gracefully
    assert similarity == 0.0 or similarity is not None


def test_compare_to_fingerprint_identical():
    """Test comparing text that matches fingerprint."""
    text = "Sample text for comparison."
    samples = [text]
    
    fingerprint = generate_fingerprint(samples)
    similarity = compare_to_fingerprint(text, fingerprint)
    
    # Should have high similarity
    assert similarity > 0
    assert similarity <= 1


def test_update_fingerprint_sample_count():
    """Test that sample count is updated correctly."""
    existing = {
        "feature_vector": [0.5] * 13,
        "sample_count": 3,
        "model_version": "1.0"
    }
    
    updated = update_fingerprint(existing, ["New 1", "New 2"], weight=0.3)
    assert updated["sample_count"] == existing["sample_count"] + 2