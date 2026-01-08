import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional
import os
from pathlib import Path


class SiameseNetwork(nn.Module):
    """
    Siamese Network for contrastive learning.
    Takes two feature vectors and outputs a similarity score.
    """
    
    def __init__(self, input_dim: int = 13, hidden_dims: list = [64, 32, 16]):
        super(SiameseNetwork, self).__init__()
        
        # Shared encoder network
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim
        
        self.encoder = nn.Sequential(*layers)
        
        # Final embedding dimension
        self.embedding_dim = hidden_dims[-1]
        
        # Similarity layer
        self.similarity = nn.Sequential(
            nn.Linear(self.embedding_dim * 2, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through Siamese network.
        
        Args:
            x1: First feature vector batch
            x2: Second feature vector batch
        
        Returns:
            Similarity score between 0 and 1
        """
        # Encode both inputs
        emb1 = self.encoder(x1)
        emb2 = self.encoder(x2)
        
        # Concatenate embeddings
        combined = torch.cat([emb1, emb2], dim=1)
        
        # Calculate similarity
        similarity = self.similarity(combined)
        
        return similarity.squeeze()


class ContrastiveModel:
    """
    Wrapper class for the contrastive learning model with inference capabilities.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SiameseNetwork()
        self.model.to(self.device)
        self.model.eval()
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            # Initialize with random weights (for development)
            # In production, this should load a pre-trained model
            print("Warning: No pre-trained model found. Using randomly initialized weights.")
    
    def load_model(self, model_path: str):
        """Load a trained model from file"""
        try:
            checkpoint = torch.load(model_path, map_location=self.device)
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            self.model.eval()
            print(f"Model loaded from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
    
    def save_model(self, model_path: str):
        """Save the model to file"""
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
        }, model_path)
        print(f"Model saved to {model_path}")
    
    def predict_similarity(self, feature_vector1: np.ndarray, feature_vector2: np.ndarray) -> float:
        """
        Predict similarity between two feature vectors.
        
        Args:
            feature_vector1: First feature vector
            feature_vector2: Second feature vector
        
        Returns:
            Similarity score between 0 and 1 (1 = same author, 0 = different author)
        """
        # Convert to tensors
        vec1 = torch.FloatTensor(feature_vector1).unsqueeze(0).to(self.device)
        vec2 = torch.FloatTensor(feature_vector2).unsqueeze(0).to(self.device)
        
        # Predict
        with torch.no_grad():
            similarity = self.model(vec1, vec2)
        
        return float(similarity.cpu().item())
    
    def predict_ai_probability(self, text_features: np.ndarray, reference_features: np.ndarray) -> float:
        """
        Predict probability that text was written by AI vs human.
        Uses similarity to reference (human) features.
        
        Args:
            text_features: Features of text to analyze
            reference_features: Features of reference human writing
        
        Returns:
            AI probability (0 = human-like, 1 = AI-like)
        """
        similarity = self.predict_similarity(text_features, reference_features)
        # Convert similarity to AI probability
        # High similarity = human-like (low AI probability)
        # Low similarity = AI-like (high AI probability)
        ai_probability = 1.0 - similarity
        return float(ai_probability)


# Global model instance (lazy loading)
_model_instance = None


def get_contrastive_model(model_path: Optional[str] = None) -> ContrastiveModel:
    """Get or create the global contrastive model instance"""
    global _model_instance
    
    if _model_instance is None:
        if model_path is None:
            # Default model path
            default_path = Path(__file__).parent.parent.parent / "ml_models" / "saved_models" / "contrastive_model.pth"
            model_path = str(default_path) if default_path.exists() else None
        
        _model_instance = ContrastiveModel(model_path=model_path)
    
    return _model_instance
