"""
Additional edge case tests for feature extraction.
"""
import pytest
import numpy as np
from app.ml.feature_extraction import (
    calculate_burstiness,
    calculate_perplexity,
    calculate_rare_word_frequency,
    extract_syntactic_features,
    extract_semantic_features,
    extract_all_features,
    extract_feature_vector,
    _calculate_heuristic_perplexity
)
from unittest.mock import patch, MagicMock


def test_calculate_burstiness_single_sentence():
    """Test burstiness with single sentence."""
    text = "This is a single sentence."
    burstiness = calculate_burstiness(text)
    assert burstiness == 0.0  # No variance with single sentence


def test_calculate_burstiness_special_characters():
    """Test burstiness with special characters."""
    text = "First sentence! Second sentence? Third sentence."
    burstiness = calculate_burstiness(text)
    assert burstiness >= 0


def test_calculate_perplexity_with_ollama():
    """Test perplexity calculation using Ollama API."""
    with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434", "OLLAMA_MODEL": "llama3.1:8b"}):
        with patch('app.ml.feature_extraction.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "perplexity": 25.5,
                "eval_count": 10
            }
            mock_post.return_value = mock_response
            
            perplexity = calculate_perplexity("Test text")
            assert perplexity == 25.5


def test_calculate_perplexity_ollama_no_perplexity_field():
    """Test perplexity calculation when Ollama doesn't return perplexity field."""
    with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434", "OLLAMA_MODEL": "llama3.1:8b"}):
        with patch('app.ml.feature_extraction.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "eval_count": 10,
                "eval_duration": 1000
            }
            mock_post.return_value = mock_response
            
            perplexity = calculate_perplexity("Test text")
            # Should use fallback heuristic
            assert 20 <= perplexity <= 100


def test_calculate_perplexity_ollama_connection_error():
    """Test perplexity calculation when Ollama is unreachable."""
    with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434"}):
        with patch('app.ml.feature_extraction.requests.post') as mock_post:
            import requests
            mock_post.side_effect = requests.exceptions.ConnectionError()
            
            perplexity = calculate_perplexity("Test text")
            # Should return heuristic fallback
            assert 20 <= perplexity <= 100


def test_calculate_perplexity_ollama_timeout():
    """Test perplexity calculation when Ollama times out."""
    with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434"}):
        with patch('app.ml.feature_extraction.requests.post') as mock_post:
            import requests
            mock_post.side_effect = requests.exceptions.Timeout()
            
            perplexity = calculate_perplexity("Test text")
            # Should return heuristic fallback
            assert 20 <= perplexity <= 100


def test_calculate_heuristic_perplexity():
    """Test heuristic perplexity calculation."""
    text = "This is a simple test text with some variety in the words used."
    perplexity = _calculate_heuristic_perplexity(text)
    # Should be in reasonable range
    assert 20 <= perplexity <= 100


def test_calculate_heuristic_perplexity_empty():
    """Test heuristic perplexity with empty text."""
    perplexity = _calculate_heuristic_perplexity("")
    # Should return default value
    assert perplexity == 50.0


def test_calculate_rare_word_frequency_empty():
    """Test rare word frequency with empty text."""
    result = calculate_rare_word_frequency("")
    assert result["rare_word_ratio"] == 0.0
    assert result["unique_word_ratio"] == 0.0


def test_calculate_rare_word_frequency_single_word():
    """Test rare word frequency with single word."""
    result = calculate_rare_word_frequency("word")
    assert 0 <= result["rare_word_ratio"] <= 1
    assert 0 <= result["unique_word_ratio"] <= 1


def test_extract_syntactic_features_empty():
    """Test syntactic feature extraction with empty text."""
    features = extract_syntactic_features("")
    assert all(v == 0.0 for v in features.values())


def test_extract_syntactic_features_exception():
    """Test syntactic feature extraction with exception."""
    with patch('nltk.word_tokenize', side_effect=Exception("NLTK error")):
        features = extract_syntactic_features("Test text")
        # Should return default values
        assert all(v == 0.0 for v in features.values())


def test_extract_semantic_features_empty():
    """Test semantic feature extraction with empty text."""
    features = extract_semantic_features("")
    assert features["avg_word_length"] == 0.0
    assert features["sentence_complexity"] == 0.0


def test_extract_all_features_empty():
    """Test extracting all features from empty text."""
    features = extract_all_features("")
    assert features == {}


def test_extract_all_features_whitespace():
    """Test extracting features from whitespace-only text."""
    features = extract_all_features("   \n\n   ")
    # Should return empty or minimal features
    assert isinstance(features, dict)


def test_extract_feature_vector_empty():
    """Test feature vector extraction from empty text."""
    vector = extract_feature_vector("")
    assert isinstance(vector, np.ndarray)


def test_extract_feature_vector_normalization():
    """Test that feature vector is normalized."""
    text = "This is a test text with multiple words."
    vector = extract_feature_vector(text)
    
    norm = np.linalg.norm(vector)
    # Should be normalized (norm <= 1) or zero vector
    assert norm <= 1.0 or norm == 0.0


def test_extract_feature_vector_zero_vector():
    """Test feature vector extraction that results in zero vector."""
    # Text that results in all-zero features (edge case)
    text = ""  # Empty text
    vector = extract_feature_vector(text)
    assert isinstance(vector, np.ndarray)
