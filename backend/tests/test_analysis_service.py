"""
Tests for analysis service.
"""
import pytest
import numpy as np
from app.services.analysis_service import AnalysisService, get_analysis_service


def test_analyze_text_sentence_granularity():
    """Test analyzing text with sentence granularity."""
    service = AnalysisService()
    text = "First sentence. Second sentence. Third sentence."
    result = service.analyze_text(text, granularity="sentence")
    
    assert "segments" in result
    assert "overall_ai_probability" in result
    assert "granularity" in result
    assert result["granularity"] == "sentence"
    assert len(result["segments"]) > 0
    assert all(0 <= seg["ai_probability"] <= 1 for seg in result["segments"])


def test_analyze_text_paragraph_granularity():
    """Test analyzing text with paragraph granularity."""
    service = AnalysisService()
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    result = service.analyze_text(text, granularity="paragraph")
    
    assert result["granularity"] == "paragraph"
    assert len(result["segments"]) > 0


def test_analyze_text_invalid_granularity():
    """Test analyzing text with invalid granularity."""
    service = AnalysisService()
    with pytest.raises(ValueError, match="Invalid granularity"):
        service.analyze_text("Text", granularity="invalid")


def test_analyze_text_empty():
    """Test analyzing empty text."""
    service = AnalysisService()
    with pytest.raises(ValueError, match="cannot be empty"):
        service.analyze_text("")


def test_analyze_text_with_fingerprint():
    """Test analyzing text with user fingerprint."""
    service = AnalysisService()
    text = "Sample text for analysis."
    fingerprint = {
        "feature_vector": [0.5] * 13,
        "model_version": "1.0"
    }
    result = service.analyze_text(text, granularity="sentence", user_fingerprint=fingerprint)
    
    assert "segments" in result
    assert "overall_ai_probability" in result


def test_analyze_with_fingerprint_method():
    """Test analyze_with_fingerprint method."""
    service = AnalysisService()
    text = "Sample text."
    fingerprint = {
        "feature_vector": [0.5] * 13,
        "model_version": "1.0"
    }
    result = service.analyze_with_fingerprint(text, fingerprint, granularity="sentence")
    
    assert "segments" in result


def test_estimate_ai_probability():
    """Test AI probability estimation."""
    service = AnalysisService()
    features = np.array([0.5, 50.0, 0.1, 0.2] + [0.0] * 9)  # Minimal feature vector
    prob = service._estimate_ai_probability(features)
    
    assert 0 <= prob <= 1


def test_estimate_ai_probability_short_vector():
    """Test AI probability estimation with short feature vector."""
    service = AnalysisService()
    features = np.array([0.5])
    prob = service._estimate_ai_probability(features)
    
    assert prob == 0.5  # Default value


def test_get_analysis_service():
    """Test getting analysis service instance."""
    service1 = get_analysis_service()
    service2 = get_analysis_service()
    # Should return the same instance
    assert service1 is service2


def test_analyze_text_whitespace_handling():
    """Test that whitespace-only segments are skipped."""
    service = AnalysisService()
    text = "First sentence.   \n\n   Second sentence."
    result = service.analyze_text(text, granularity="sentence")
    
    # Should not have empty segments
    assert all(seg["text"].strip() for seg in result["segments"])