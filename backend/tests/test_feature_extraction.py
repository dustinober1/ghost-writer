"""
Unit tests for feature extraction engine.
"""
import pytest
import numpy as np
from app.ml.feature_extraction import (
    calculate_burstiness,
    calculate_rare_word_frequency,
    extract_syntactic_features,
    extract_semantic_features,
    extract_all_features,
    extract_feature_vector
)


def test_calculate_burstiness():
    """Test burstiness calculation"""
    # High variance text (human-like)
    text1 = "Short. This is a much longer sentence with more words and complexity. Short again. Another very long and complex sentence that demonstrates natural variation."
    burstiness1 = calculate_burstiness(text1)
    assert burstiness1 > 0
    
    # Low variance text (AI-like)
    text2 = "This is a sentence. This is another sentence. This is yet another sentence. All sentences are similar."
    burstiness2 = calculate_burstiness(text2)
    assert burstiness2 >= 0
    
    # Empty text
    burstiness3 = calculate_burstiness("")
    assert burstiness3 == 0.0


def test_calculate_rare_word_frequency():
    """Test rare word frequency calculation"""
    text = "This is a test with some uncommon words like serendipity and perspicacious."
    result = calculate_rare_word_frequency(text)
    
    assert "rare_word_ratio" in result
    assert "unique_word_ratio" in result
    assert 0 <= result["rare_word_ratio"] <= 1
    assert 0 <= result["unique_word_ratio"] <= 1


def test_extract_syntactic_features():
    """Test syntactic feature extraction"""
    text = "The quick brown fox jumps over the lazy dog. It is a beautiful day."
    features = extract_syntactic_features(text)
    
    assert "noun_ratio" in features
    assert "verb_ratio" in features
    assert "adjective_ratio" in features
    assert "adverb_ratio" in features
    assert all(0 <= v <= 1 for v in features.values())


def test_extract_semantic_features():
    """Test semantic feature extraction"""
    text = "This is a test sentence with various words."
    features = extract_semantic_features(text)
    
    assert "avg_word_length" in features
    assert "sentence_complexity" in features
    assert features["avg_word_length"] > 0


def test_extract_all_features():
    """Test complete feature extraction"""
    text = "This is a sample text for testing feature extraction. It contains multiple sentences."
    features = extract_all_features(text)
    
    assert "burstiness" in features
    assert "perplexity" in features
    assert "rare_word_ratio" in features
    assert len(features) > 0


def test_extract_feature_vector():
    """Test feature vector extraction"""
    text = "This is a test text."
    vector = extract_feature_vector(text)
    
    assert isinstance(vector, np.ndarray)
    assert len(vector) > 0
    # Check normalization
    norm = np.linalg.norm(vector)
    assert norm <= 1.0 or norm == 0.0  # Either normalized or zero vector
