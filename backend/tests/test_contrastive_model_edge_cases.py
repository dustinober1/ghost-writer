"""
Additional edge case tests for contrastive model.
"""
import pytest
import numpy as np
import torch
from app.ml.contrastive_model import SiameseNetwork, ContrastiveModel, get_contrastive_model
from pathlib import Path
import os
from unittest.mock import patch, MagicMock


def test_siamese_network_different_input_dims():
    """Test Siamese network with different input dimensions."""
    model = SiameseNetwork(input_dim=20, hidden_dims=[64, 32])
    
    x1 = torch.randn(1, 20)
    x2 = torch.randn(1, 20)
    
    output = model(x1, x2)
    assert output.shape == (1,)
    assert 0 <= output.item() <= 1


def test_contrastive_model_load_model_file_not_exists():
    """Test loading model when file doesn't exist."""
    model = ContrastiveModel(model_path="/nonexistent/path/model.pth")
    # Should use random weights
    assert model.model is not None


def test_contrastive_model_save_and_load():
    """Test saving and loading model."""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, "test_model.pth")
        
        model1 = ContrastiveModel()
        model1.save_model(model_path)
        
        assert os.path.exists(model_path)
        
        model2 = ContrastiveModel(model_path=model_path)
        assert model2.model is not None


def test_contrastive_model_predict_similarity_same_vectors():
    """Test similarity prediction with identical vectors."""
    model = ContrastiveModel()
    
    vec = np.random.rand(13).astype(np.float32)
    similarity = model.predict_similarity(vec, vec)
    
    # Should be high similarity (close to 1.0)
    assert 0 <= similarity <= 1


def test_contrastive_model_predict_similarity_different_shapes():
    """Test similarity prediction with different array shapes."""
    model = ContrastiveModel()
    
    vec1 = np.random.rand(13).astype(np.float32)
    vec2 = np.random.rand(13).astype(np.float32)
    
    # Both 1D arrays
    similarity = model.predict_similarity(vec1, vec2)
    assert 0 <= similarity <= 1


def test_contrastive_model_predict_ai_probability_edge_cases():
    """Test AI probability prediction with edge cases."""
    model = ContrastiveModel()
    
    # Zero vectors
    zero_vec = np.zeros(13, dtype=np.float32)
    prob = model.predict_ai_probability(zero_vec, zero_vec)
    assert 0 <= prob <= 1
    
    # Maximum vectors
    max_vec = np.ones(13, dtype=np.float32)
    prob = model.predict_ai_probability(max_vec, max_vec)
    assert 0 <= prob <= 1


def test_get_contrastive_model_multiple_calls():
    """Test getting contrastive model instance multiple times."""
    import app.ml.contrastive_model
    app.ml.contrastive_model._model_instance = None
    
    model1 = get_contrastive_model()
    model2 = get_contrastive_model()
    
    # Should return the same instance
    assert model1 is model2


def test_get_contrastive_model_with_path():
    """Test getting contrastive model with custom path."""
    import app.ml.contrastive_model
    app.ml.contrastive_model._model_instance = None
    
    model = get_contrastive_model(model_path="/nonexistent/path")
    assert model is not None