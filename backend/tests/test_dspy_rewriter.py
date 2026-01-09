"""
Tests for Ollama rewriter.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from app.ml.dspy_rewriter import OllamaRewriter, get_ollama_rewriter, get_dspy_rewriter


def test_ollama_rewriter_init():
    """Test OllamaRewriter initialization."""
    with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434", "OLLAMA_MODEL": "llama3.1:8b"}):
        rewriter = OllamaRewriter()
        assert rewriter.ollama_base_url == "http://localhost:11434"
        assert rewriter.ollama_model == "llama3.1:8b"


def test_ollama_rewriter_init_defaults():
    """Test OllamaRewriter initialization with defaults."""
    with patch.dict(os.environ, {}, clear=True):
        rewriter = OllamaRewriter()
        assert rewriter.ollama_base_url == "http://localhost:11434"
        assert rewriter.ollama_model == "llama3.1:8b"


def test_rewrite_text_empty():
    """Test rewriting empty text."""
    rewriter = OllamaRewriter()
    with pytest.raises(ValueError, match="cannot be empty"):
        rewriter.rewrite_text("", "Some style")


def test_rewrite_text_with_style_guidance():
    """Test rewriting text with style guidance."""
    rewriter = OllamaRewriter()
    
    with patch.object(rewriter, '_rewrite_with_ollama', return_value="Rewritten text"):
        result = rewriter.rewrite_text("Original text", "Formal style")
        assert result == "Rewritten text"


def test_rewrite_text_no_style_guidance():
    """Test rewriting text without style guidance."""
    rewriter = OllamaRewriter()
    
    with patch.object(rewriter, '_rewrite_with_ollama', return_value="Rewritten text"):
        result = rewriter.rewrite_text("Original text", None)
        assert result == "Rewritten text"


def test_rewrite_with_ollama():
    """Test rewriting with Ollama."""
    rewriter = OllamaRewriter()
    
    with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434", "OLLAMA_MODEL": "llama3.1:8b"}):
        with patch('app.ml.dspy_rewriter.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Rewritten text"}}]
            }
            mock_post.return_value = mock_response
            
            with patch.object(rewriter, '_check_ollama_model', return_value=True):
                result = rewriter._rewrite_with_ollama("Original", "Style")
                assert result == "Rewritten text"


def test_rewrite_with_ollama_legacy_endpoint():
    """Test rewriting with Ollama legacy endpoint when chat endpoint fails."""
    rewriter = OllamaRewriter()
    
    with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434", "OLLAMA_MODEL": "llama3.1:8b"}):
        with patch('app.ml.dspy_rewriter.requests.post') as mock_post:
            # First call fails (chat endpoint)
            # Second call succeeds (legacy endpoint)
            mock_post.side_effect = [
                MagicMock(status_code=200, json=lambda: {
                    "message": {"content": "Unexpected format"}  # Triggers fallback
                }),
                MagicMock(status_code=200, json=lambda: {
                    "response": "Rewritten text via legacy"
                })
            ]
            
            with patch.object(rewriter, '_check_ollama_model', return_value=True):
                result = rewriter._rewrite_with_ollama("Original", "Style")
                assert result == "Rewritten text via legacy"


def test_check_ollama_model():
    """Test checking if Ollama model exists."""
    rewriter = OllamaRewriter()
    
    with patch('app.ml.dspy_rewriter.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "llama3.1:8b"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = rewriter._check_ollama_model("http://localhost:11434", "llama3.1:8b")
        assert result == True


def test_check_ollama_model_not_found():
    """Test checking when model doesn't exist."""
    rewriter = OllamaRewriter()
    
    with patch('app.ml.dspy_rewriter.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "different-model"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = rewriter._check_ollama_model("http://localhost:11434", "llama3.1:8b")
        assert result == False


def test_rewrite_with_fingerprint():
    """Test rewriting with fingerprint."""
    rewriter = OllamaRewriter()
    fingerprint = {
        "feature_vector": [0.5] * 13,
        "model_version": "1.0"
    }
    
    with patch.object(rewriter, 'rewrite_text', return_value="Rewritten"):
        result = rewriter.rewrite_with_fingerprint("Original", fingerprint)
        assert result == "Rewritten"


def test_generate_style_guidance():
    """Test generating style guidance from fingerprint."""
    rewriter = OllamaRewriter()
    fingerprint = {
        "feature_vector": [0.5] * 13,
        "model_version": "1.0"
    }
    
    guidance = rewriter._generate_style_guidance(fingerprint)
    assert isinstance(guidance, str)
    assert len(guidance) > 0
    assert "style characteristics" in guidance.lower()


def test_get_ollama_rewriter():
    """Test getting Ollama rewriter instance."""
    # Reset global instance
    import app.ml.dspy_rewriter
    app.ml.dspy_rewriter._rewriter_instance = None
    
    rewriter1 = get_ollama_rewriter()
    rewriter2 = get_ollama_rewriter()
    
    # Should return the same instance
    assert rewriter1 is rewriter2


def test_get_dspy_rewriter_backwards_compatibility():
    """Test backwards compatibility alias for get_dspy_rewriter."""
    # Reset global instance
    import app.ml.dspy_rewriter
    app.ml.dspy_rewriter._rewriter_instance = None
    
    rewriter = get_dspy_rewriter()
    # Should return OllamaRewriter instance
    assert isinstance(rewriter, OllamaRewriter)


def test_rewrite_ollama_model_not_found_error():
    """Test error when Ollama model not found."""
    rewriter = OllamaRewriter()
    
    with patch('app.ml.dspy_rewriter.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response
        
        with patch.object(rewriter, '_check_ollama_model', return_value=False):
            with pytest.raises(ValueError, match="not found"):
                rewriter._rewrite_with_ollama("Original", "Style")


def test_rewrite_ollama_connection_error():
    """Test error when cannot connect to Ollama."""
    rewriter = OllamaRewriter()
    
    with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434", "OLLAMA_MODEL": "llama3.1:8b"}):
        with patch('app.ml.dspy_rewriter.requests.post') as mock_post:
            import requests
            mock_post.side_effect = requests.exceptions.ConnectionError()
            
            with pytest.raises(ValueError, match="Cannot connect to Ollama"):
                rewriter._rewrite_with_ollama("Original", "Style")
