"""
Tests for DSPy rewriter.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from app.ml.dspy_rewriter import DSPyRewriter, get_dspy_rewriter


def test_dspy_rewriter_init_ollama():
    """Test DSPyRewriter initialization with Ollama."""
    with patch.dict(os.environ, {"DEFAULT_LLM_MODEL": "ollama"}):
        rewriter = DSPyRewriter(model="ollama")
        assert rewriter.model_name == "ollama"


def test_dspy_rewriter_init_openai():
    """Test DSPyRewriter initialization with OpenAI."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "DEFAULT_LLM_MODEL": "openai"}):
        rewriter = DSPyRewriter(model="openai")
        assert rewriter.model_name == "openai"


def test_dspy_rewriter_init_anthropic():
    """Test DSPyRewriter initialization with Anthropic."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key", "DEFAULT_LLM_MODEL": "anthropic"}):
        rewriter = DSPyRewriter(model="anthropic")
        assert rewriter.model_name == "anthropic"


def test_dspy_rewriter_fallback_to_ollama():
    """Test fallback to Ollama when API key missing."""
    with patch.dict(os.environ, {}, clear=True):
        rewriter = DSPyRewriter(model="openai")
        # Should fallback to ollama
        assert rewriter.model_name == "ollama"


def test_rewrite_text_empty():
    """Test rewriting empty text."""
    rewriter = DSPyRewriter()
    with pytest.raises(ValueError, match="cannot be empty"):
        rewriter.rewrite_text("", "Some style")


def test_rewrite_text_with_style_guidance():
    """Test rewriting text with style guidance."""
    rewriter = DSPyRewriter()
    
    with patch.object(rewriter, '_rewrite_with_direct_api', return_value="Rewritten text"):
        result = rewriter.rewrite_text("Original text", "Formal style")
        assert result == "Rewritten text"


def test_rewrite_text_no_style_guidance():
    """Test rewriting text without style guidance."""
    rewriter = DSPyRewriter()
    
    with patch.object(rewriter, '_rewrite_with_direct_api', return_value="Rewritten text"):
        result = rewriter.rewrite_text("Original text", None)
        assert result == "Rewritten text"


def test_rewrite_with_openai():
    """Test rewriting with OpenAI."""
    rewriter = DSPyRewriter(model="openai")
    
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        with patch('app.ml.dspy_rewriter.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Rewritten text"
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            result = rewriter._rewrite_with_openai("Original", "Style")
            assert result == "Rewritten text"


def test_rewrite_with_anthropic():
    """Test rewriting with Anthropic."""
    rewriter = DSPyRewriter(model="anthropic")
    
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch('app.ml.dspy_rewriter.anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_message.content[0].text = "Rewritten text"
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client
            
            result = rewriter._rewrite_with_anthropic("Original", "Style")
            assert result == "Rewritten text"


def test_rewrite_with_ollama():
    """Test rewriting with Ollama."""
    rewriter = DSPyRewriter(model="ollama")
    
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


def test_check_ollama_model():
    """Test checking if Ollama model exists."""
    rewriter = DSPyRewriter()
    
    with patch('app.ml.dspy_rewriter.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "llama3.1:8b"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = rewriter._check_ollama_model("http://localhost:11434", "llama3.1:8b")
        assert result == True


def test_rewrite_with_fingerprint():
    """Test rewriting with fingerprint."""
    rewriter = DSPyRewriter()
    fingerprint = {
        "feature_vector": [0.5] * 13,
        "model_version": "1.0"
    }
    
    with patch.object(rewriter, 'rewrite_text', return_value="Rewritten"):
        result = rewriter.rewrite_with_fingerprint("Original", fingerprint)
        assert result == "Rewritten"


def test_generate_style_guidance():
    """Test generating style guidance from fingerprint."""
    rewriter = DSPyRewriter()
    fingerprint = {
        "feature_vector": [0.5] * 13,
        "model_version": "1.0"
    }
    
    guidance = rewriter._generate_style_guidance(fingerprint)
    assert isinstance(guidance, str)
    assert len(guidance) > 0


def test_get_dspy_rewriter():
    """Test getting DSPy rewriter instance."""
    # Reset global instance
    import app.ml.dspy_rewriter
    app.ml.dspy_rewriter._rewriter_instance = None
    
    rewriter1 = get_dspy_rewriter()
    rewriter2 = get_dspy_rewriter()
    
    # Should return the same instance
    assert rewriter1 is rewriter2


def test_unsupported_model():
    """Test initialization with unsupported model."""
    with pytest.raises(ValueError, match="Unsupported model"):
        DSPyRewriter(model="unsupported")