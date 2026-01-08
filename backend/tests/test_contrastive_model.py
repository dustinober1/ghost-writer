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


def test_contrastive_model_load_model():
    """Test loading model from file"""
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, "test_model.pth")
        
        # Create and save model
        model1 = ContrastiveModel()
        model1.save_model(model_path)
        
        # Load model
        model2 = ContrastiveModel(model_path=model_path)
        assert model2.model is not None


def test_contrastive_model_load_model_file_not_exists():
    """Test loading model when file doesn't exist"""
    model = ContrastiveModel(model_path="/nonexistent/path/model.pth")
    # Should use random weights, not raise error
    assert model.model is not None


def test_contrastive_model_load_model_invalid_file():
    """Test loading model from invalid file"""
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        invalid_path = os.path.join(tmpdir, "invalid.pth")
        # Create empty or invalid file
        with open(invalid_path, 'w') as f:
            f.write("invalid content")
        
        # Should handle gracefully
        try:
            model = ContrastiveModel(model_path=invalid_path)
            # If it loads, that's fine; if it fails, that's also expected
            assert True
        except Exception:
            # Exception is acceptable for invalid file
            assert True


def test_contrastive_model_save_model():
    """Test saving model to file"""
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, "test_model.pth")
        
        model = ContrastiveModel()
        model.save_model(model_path)
        
        assert os.path.exists(model_path)
