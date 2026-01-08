"""
Fingerprint generation and management.
Creates unique vector signatures for users based on their writing samples.
"""
import numpy as np
from typing import List, Dict
from app.ml.feature_extraction import extract_feature_vector, extract_all_features


def generate_fingerprint(text_samples: List[str]) -> Dict:
    """
    Generate a fingerprint from multiple text samples.
    Averages feature vectors from all samples to create a unique signature.
    
    Args:
        text_samples: List of text strings from the same author
    
    Returns:
        Dictionary containing the fingerprint (feature vector and metadata)
    """
    if not text_samples:
        raise ValueError("At least one text sample is required")
    
    # Extract features from each sample
    feature_vectors = []
    for text in text_samples:
        if text and text.strip():
            vector = extract_feature_vector(text)
            feature_vectors.append(vector)
    
    if not feature_vectors:
        raise ValueError("No valid text samples found")
    
    # Average the feature vectors to create the fingerprint
    fingerprint_vector = np.mean(feature_vectors, axis=0)
    
    # Also store individual feature statistics for reference
    all_features = [extract_all_features(text) for text in text_samples if text and text.strip()]
    
    fingerprint = {
        "feature_vector": fingerprint_vector.tolist(),
        "sample_count": len(text_samples),
        "model_version": "1.0"
    }
    
    return fingerprint


def update_fingerprint(existing_fingerprint: Dict, new_samples: List[str], weight: float = 0.3) -> Dict:
    """
    Update an existing fingerprint with new samples.
    Uses weighted average to incorporate new data.
    
    Args:
        existing_fingerprint: Existing fingerprint dictionary
        new_samples: List of new text samples
        weight: Weight for new samples (0.0 to 1.0)
    
    Returns:
        Updated fingerprint dictionary
    """
    if not new_samples:
        return existing_fingerprint
    
    # Extract features from new samples
    new_vectors = []
    for text in new_samples:
        if text and text.strip():
            vector = extract_feature_vector(text)
            new_vectors.append(vector)
    
    if not new_vectors:
        return existing_fingerprint
    
    # Average new vectors
    new_fingerprint_vector = np.mean(new_vectors, axis=0)
    
    # Get existing vector
    existing_vector = np.array(existing_fingerprint["feature_vector"])
    
    # Weighted average
    updated_vector = (1 - weight) * existing_vector + weight * new_fingerprint_vector
    
    # Update fingerprint
    updated_fingerprint = existing_fingerprint.copy()
    updated_fingerprint["feature_vector"] = updated_vector.tolist()
    updated_fingerprint["sample_count"] += len(new_samples)
    
    return updated_fingerprint


def compare_to_fingerprint(text: str, fingerprint: Dict) -> float:
    """
    Compare a text sample to a fingerprint.
    Returns a similarity score.
    
    Args:
        text: Text to compare
        fingerprint: Fingerprint dictionary
    
    Returns:
        Similarity score (0 to 1, higher = more similar)
    """
    text_vector = extract_feature_vector(text)
    fingerprint_vector = np.array(fingerprint["feature_vector"])
    
    # Calculate cosine similarity
    dot_product = np.dot(text_vector, fingerprint_vector)
    norm_text = np.linalg.norm(text_vector)
    norm_fingerprint = np.linalg.norm(fingerprint_vector)
    
    if norm_text == 0 or norm_fingerprint == 0:
        return 0.0
    
    similarity = dot_product / (norm_text * norm_fingerprint)
    return float(similarity)
