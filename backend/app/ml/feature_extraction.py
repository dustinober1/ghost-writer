import numpy as np
import nltk
from typing import Dict, List
from collections import Counter
import re
import requests
from app.utils.text_processing import split_into_sentences, split_into_paragraphs

# Download NLTK data if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)


def calculate_burstiness(text: str) -> float:
    """
    Calculate burstiness: variance in sentence lengths.
    High burstiness (high variance) = more human-like.
    Low burstiness (low variance) = more AI-like.
    """
    sentences = split_into_sentences(text)
    if len(sentences) < 2:
        return 0.0
    
    sentence_lengths = [len(s.split()) for s in sentences]
    mean_length = np.mean(sentence_lengths)
    if mean_length == 0:
        return 0.0
    
    variance = np.var(sentence_lengths)
    # Normalize by mean to get coefficient of variation
    burstiness = np.sqrt(variance) / mean_length if mean_length > 0 else 0.0
    return float(burstiness)


def calculate_perplexity(text: str) -> float:
    """
    Calculate perplexity using Ollama API.
    Lower perplexity = more predictable = potentially more AI-like.
    Higher perplexity = less predictable = potentially more human-like.
    
    Uses Ollama's /api/generate endpoint with logprobs if available.
    Falls back to default value (50.0) if calculation fails.
    """
    import os
    
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    
    # Truncate text to reasonable length for API call
    # Ollama models have context limits
    max_length = 1000
    truncated_text = text[:max_length]
    
    try:
        # Try to get logprobs from Ollama API
        response = requests.post(
            f"{ollama_base_url}/api/generate",
            json={
                "model": ollama_model,
                "prompt": truncated_text,
                "stream": False,
                "options": {
                    "num_predict": 1,  # Get 1 token prediction
                    "temperature": 0.0  # Deterministic for perplexity
                },
                "raw": True  # Try to get raw output with logprobs
            },
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Check if logprobs are available
        if "eval_count" in result and result["eval_count"] > 0:
            # Calculate perplexity from Ollama's output
            # Ollama may provide perplexity directly or we can calculate from logits
            
            # Method 1: Check if Ollama provides perplexity directly
            if "perplexity" in result:
                return float(result["perplexity"])
            
            # Method 2: Calculate from eval_count and other metrics if available
            # This is a simplified approach - actual implementation depends on Ollama's response format
            if "eval_duration" in result and "eval_count" in result:
                # Use a heuristic based on evaluation metrics
                # This is not true perplexity but a reasonable proxy
                return float(min(100.0, result["eval_count"] / max(1, len(truncated_text.split())) * 50))
            
        # If we got here, logprobs/perplexity not available in expected format
        # Fall back to a text-based heuristic
        return _calculate_heuristic_perplexity(text)
        
    except requests.exceptions.ConnectionError:
        print(
            f"Warning: Cannot connect to Ollama at {ollama_base_url}. "
            "Using heuristic perplexity calculation."
        )
        return _calculate_heuristic_perplexity(text)
    except requests.exceptions.Timeout:
        print(
            f"Warning: Ollama perplexity request timed out. "
            "Using heuristic perplexity calculation."
        )
        return _calculate_heuristic_perplexity(text)
    except Exception as e:
        print(f"Warning: Error calculating perplexity with Ollama: {e}. Using heuristic.")
        return _calculate_heuristic_perplexity(text)


def _calculate_heuristic_perplexity(text: str) -> float:
    """
    Calculate a heuristic-based perplexity score using text statistics.
    This is a fallback when Ollama API is unavailable.
    
    Higher values = more unpredictable (more human-like)
    Lower values = more predictable (more AI-like)
    """
    words = text.split()
    sentences = split_into_sentences(text)
    
    if not words:
        return 50.0
    
    # Calculate various text features
    avg_word_length = np.mean([len(w) for w in words]) if words else 0
    unique_word_ratio = len(set(words)) / len(words) if words else 0
    avg_sentence_length = np.mean([len(s.split()) for s in sentences]) if sentences else 0
    
    # Heuristic: More unique words and variation = higher perplexity (more human-like)
    # Normalized to range roughly 20-100
    unique_score = unique_word_ratio * 50  # 0-50
    length_score = min(avg_word_length / 10, 20)  # 0-20
    sentence_score = min(avg_sentence_length / 2, 30)  # 0-30
    
    perplexity = 30.0 + unique_score + length_score + sentence_score
    
    # Clamp to reasonable range
    return float(max(20.0, min(100.0, perplexity)))


def calculate_rare_word_frequency(text: str, rare_word_threshold: int = 10000) -> Dict[str, float]:
    """
    Calculate frequency of rare words (uncommon vocabulary).
    Uses word frequency lists - words that appear less frequently are considered rare.
    """
    words = text.lower().split()
    if not words:
        return {"rare_word_ratio": 0.0, "unique_word_ratio": 0.0}
    
    # Simple heuristic: words with length > 8 or containing uncommon patterns
    rare_words = [w for w in words if len(w) > 8 or re.search(r'[^a-z\s]', w)]
    unique_words = set(words)
    
    rare_word_ratio = len(rare_words) / len(words) if words else 0.0
    unique_word_ratio = len(unique_words) / len(words) if words else 0.0
    
    return {
        "rare_word_ratio": float(rare_word_ratio),
        "unique_word_ratio": float(unique_word_ratio)
    }


def extract_syntactic_features(text: str) -> Dict[str, float]:
    """
    Extract syntactic features using POS tagging.
    Returns distributions of parts of speech.
    """
    try:
        tokens = nltk.word_tokenize(text.lower())
        pos_tags = nltk.pos_tag(tokens)
        
        # Count POS tags
        pos_counts = Counter([tag for word, tag in pos_tags])
        total = len(pos_tags) if pos_tags else 1
        
        # Extract key POS ratios
        noun_ratio = (pos_counts.get('NN', 0) + pos_counts.get('NNS', 0) + 
                     pos_counts.get('NNP', 0) + pos_counts.get('NNPS', 0)) / total
        verb_ratio = (pos_counts.get('VB', 0) + pos_counts.get('VBD', 0) + 
                     pos_counts.get('VBG', 0) + pos_counts.get('VBN', 0) + 
                     pos_counts.get('VBP', 0) + pos_counts.get('VBZ', 0)) / total
        adj_ratio = (pos_counts.get('JJ', 0) + pos_counts.get('JJR', 0) + 
                    pos_counts.get('JJS', 0)) / total
        adv_ratio = (pos_counts.get('RB', 0) + pos_counts.get('RBR', 0) + 
                    pos_counts.get('RBS', 0)) / total
        
        return {
            "noun_ratio": float(noun_ratio),
            "verb_ratio": float(verb_ratio),
            "adjective_ratio": float(adj_ratio),
            "adverb_ratio": float(adv_ratio)
        }
    except Exception as e:
        print(f"Error extracting syntactic features: {e}")
        return {
            "noun_ratio": 0.0,
            "verb_ratio": 0.0,
            "adjective_ratio": 0.0,
            "adverb_ratio": 0.0
        }


def extract_semantic_features(text: str) -> Dict[str, float]:
    """
    Extract semantic features.
    Simple implementation using word statistics.
    """
    words = text.lower().split()
    if not words:
        return {
            "avg_word_length": 0.0,
            "sentence_complexity": 0.0
        }
    
    # Average word length
    avg_word_length = np.mean([len(w) for w in words])
    
    # Sentence complexity (average words per sentence)
    sentences = split_into_sentences(text)
    sentence_complexity = np.mean([len(s.split()) for s in sentences]) if sentences else 0.0
    
    return {
        "avg_word_length": float(avg_word_length),
        "sentence_complexity": float(sentence_complexity)
    }


def extract_all_features(text: str) -> Dict[str, float]:
    """
    Extract all stylometric features and return as a feature vector.
    This creates the 'vector signature' for a text sample.
    """
    if not text or not text.strip():
        return {}
    
    features = {}
    
    # Burstiness
    features["burstiness"] = calculate_burstiness(text)
    
    # Perplexity
    features["perplexity"] = calculate_perplexity(text)
    
    # Rare word features
    rare_word_features = calculate_rare_word_frequency(text)
    features.update(rare_word_features)
    
    # Syntactic features
    syntactic_features = extract_syntactic_features(text)
    features.update(syntactic_features)
    
    # Semantic features
    semantic_features = extract_semantic_features(text)
    features.update(semantic_features)
    
    # Additional text statistics
    words = text.split()
    sentences = split_into_sentences(text)
    features["word_count"] = float(len(words))
    features["sentence_count"] = float(len(sentences))
    features["avg_sentence_length"] = float(np.mean([len(s.split()) for s in sentences])) if sentences else 0.0
    
    return features


def extract_feature_vector(text: str) -> np.ndarray:
    """
    Extract feature vector as numpy array for ML models.
    Returns a normalized feature vector.
    """
    features = extract_all_features(text)
    
    # Define feature order for consistent vectorization
    feature_order = [
        "burstiness",
        "perplexity",
        "rare_word_ratio",
        "unique_word_ratio",
        "noun_ratio",
        "verb_ratio",
        "adjective_ratio",
        "adverb_ratio",
        "avg_word_length",
        "sentence_complexity",
        "word_count",
        "sentence_count",
        "avg_sentence_length"
    ]
    
    vector = np.array([features.get(f, 0.0) for f in feature_order])
    
    # Normalize vector (L2 normalization)
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    
    return vector
