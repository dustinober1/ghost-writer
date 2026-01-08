"""
Unit tests for contrastive learning model.
"""
import pytest
import numpy as np
from app.ml.contrastive_model import SiameseNetwork, ContrastiveModel


def test_siamese_network_forward():
    """Test Siamese network forward pass"""
    model = SiameseNetwork(input_dim=13)
    
    # Create dummy feature vectors
    x1 = np.random.rand(1, 13).astype(np.float32)
    x2 = np.random.rand(1, 13).astype(np.float32)
    
    import torch
    x1_tensor = torch.FloatTensor(x1)
    x2_tensor = torch.FloatTensor(x2)
    
    output = model(x1_tensor, x2_tensor)
    
    assert output.shape == (1,)
    assert 0 <= output.item() <= 1  # Similarity score should be between 0 and 1


def test_contrastive_model_predict_similarity():
    """Test similarity prediction"""
    model = ContrastiveModel()
    
    vec1 = np.random.rand(13).astype(np.float32)
    vec2 = np.random.rand(13).astype(np.float32)
    
    similarity = model.predict_similarity(vec1, vec2)
    
    assert 0 <= similarity <= 1


def test_contrastive_model_predict_ai_probability():
    """Test AI probability prediction"""
    model = ContrastiveModel()
    
    text_features = np.random.rand(13).astype(np.float32)
    reference_features = np.random.rand(13).astype(np.float32)
    
    ai_prob = model.predict_ai_probability(text_features, reference_features)
    
    assert 0 <= ai_prob <= 1
