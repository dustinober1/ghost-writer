"""
Unit tests for fingerprint generation.
"""
import pytest
import numpy as np
from app.ml.fingerprint import (
    generate_fingerprint,
    update_fingerprint,
    compare_to_fingerprint
)


def test_generate_fingerprint():
    """Test fingerprint generation"""
    samples = [
        "This is a sample text. It has multiple sentences.",
        "Another sample with different content. Still human-written.",
        "Third sample to create a fingerprint."
    ]
    
    fingerprint = generate_fingerprint(samples)
    
    assert "feature_vector" in fingerprint
    assert "sample_count" in fingerprint
    assert "model_version" in fingerprint
    assert fingerprint["sample_count"] == len(samples)
    assert isinstance(fingerprint["feature_vector"], list)


def test_update_fingerprint():
    """Test fingerprint updating"""
    existing = {
        "feature_vector": [0.5] * 13,
        "sample_count": 3,
        "model_version": "1.0"
    }
    
    new_samples = ["New sample text.", "Another new sample."]
    
    updated = update_fingerprint(existing, new_samples, weight=0.3)
    
    assert updated["sample_count"] == existing["sample_count"] + len(new_samples)
    assert len(updated["feature_vector"]) == len(existing["feature_vector"])


def test_compare_to_fingerprint():
    """Test fingerprint comparison"""
    fingerprint = {
        "feature_vector": [0.5] * 13,
        "model_version": "1.0"
    }
    
    text = "This is a test text to compare against the fingerprint."
    
    similarity = compare_to_fingerprint(text, fingerprint)
    
    assert 0 <= similarity <= 1
