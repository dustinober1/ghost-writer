"""
Training script for the contrastive learning model.
Trains a Siamese network to distinguish between human and AI text.
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.ml.contrastive_model import SiameseNetwork, ContrastiveModel
from app.ml.feature_extraction import extract_feature_vector


class TextPairDataset(Dataset):
    """Dataset for training contrastive model with text pairs"""
    
    def __init__(self, pairs, labels):
        """
        Args:
            pairs: List of (feature_vector1, feature_vector2) tuples
            labels: List of labels (1 = same author, 0 = different author)
        """
        self.pairs = pairs
        self.labels = labels
    
    def __len__(self):
        return len(self.pairs)
    
    def __getitem__(self, idx):
        vec1, vec2 = self.pairs[idx]
        label = self.labels[idx]
        return (
            torch.FloatTensor(vec1),
            torch.FloatTensor(vec2),
            torch.FloatTensor([label])
        )


def generate_training_data(human_texts, ai_texts, num_pairs=1000):
    """
    Generate training pairs from human and AI texts.
    
    Args:
        human_texts: List of human-written text samples
        ai_texts: List of AI-generated text samples
        num_pairs: Number of pairs to generate
    
    Returns:
        pairs: List of (feature_vector1, feature_vector2) tuples
        labels: List of labels (1 = same, 0 = different)
    """
    pairs = []
    labels = []
    
    # Extract features
    human_features = [extract_feature_vector(text) for text in human_texts]
    ai_features = [extract_feature_vector(text) for text in ai_texts]
    
    # Generate positive pairs (same type)
    for _ in range(num_pairs // 2):
        # Human-human pairs
        idx1, idx2 = np.random.choice(len(human_features), 2, replace=False)
        pairs.append((human_features[idx1], human_features[idx2]))
        labels.append(1.0)
        
        # AI-AI pairs
        idx1, idx2 = np.random.choice(len(ai_features), 2, replace=False)
        pairs.append((ai_features[idx1], ai_features[idx2]))
        labels.append(1.0)
    
    # Generate negative pairs (different types)
    for _ in range(num_pairs // 2):
        idx1 = np.random.randint(len(human_features))
        idx2 = np.random.randint(len(ai_features))
        pairs.append((human_features[idx1], ai_features[idx2]))
        labels.append(0.0)
    
    return pairs, labels


def train_model(
    human_texts,
    ai_texts,
    epochs=50,
    batch_size=32,
    learning_rate=0.001,
    model_save_path=None
):
    """
    Train the contrastive learning model.
    
    Args:
        human_texts: List of human-written text samples
        ai_texts: List of AI-generated text samples
        epochs: Number of training epochs
        batch_size: Batch size for training
        learning_rate: Learning rate
        model_save_path: Path to save trained model
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Generate training data
    print("Generating training data...")
    pairs, labels = generate_training_data(human_texts, ai_texts, num_pairs=2000)
    
    # Create dataset and dataloader
    dataset = TextPairDataset(pairs, labels)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Initialize model
    model = SiameseNetwork()
    model.to(device)
    
    # Loss and optimizer
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training loop
    print("Starting training...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        
        for batch_idx, (vec1, vec2, label) in enumerate(dataloader):
            vec1 = vec1.to(device)
            vec2 = vec2.to(device)
            label = label.to(device)
            
            # Forward pass
            optimizer.zero_grad()
            output = model(vec1, vec2)
            loss = criterion(output, label.squeeze())
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
    
    # Save model
    if model_save_path is None:
        model_save_path = Path(__file__).parent / "saved_models" / "contrastive_model.pth"
    
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    contrastive_model = ContrastiveModel()
    contrastive_model.model = model
    contrastive_model.save_model(str(model_save_path))
    
    print(f"Training complete! Model saved to {model_save_path}")
    return model


if __name__ == "__main__":
    # Example usage with sample data
    # In production, load from actual datasets
    human_texts = [
        "This is a sample human-written text. It has natural variation in sentence length and structure.",
        "Another example of human writing. Notice how the style can vary significantly between sentences.",
        "Human authors tend to write with more personality and less uniformity than AI models."
    ]
    
    ai_texts = [
        "This is a sample AI-generated text. It typically has more uniform sentence structure and length.",
        "AI models often produce text with consistent patterns and less variation in style.",
        "The writing style of AI models is generally more predictable and uniform compared to human authors."
    ]
    
    # Expand datasets (in production, use real data)
    human_texts = human_texts * 100
    ai_texts = ai_texts * 100
    
    train_model(human_texts, ai_texts, epochs=20)
