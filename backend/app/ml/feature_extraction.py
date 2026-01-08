import numpy as np
import nltk
from typing import Dict, List
from collections import Counter
import re
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
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

# Load GPT-2 model for perplexity calculation (lazy loading)
_perplexity_model = None
_perplexity_tokenizer = None


def _get_perplexity_model():
    """Lazy load GPT-2 model for perplexity calculation"""
    global _perplexity_model, _perplexity_tokenizer
    if _perplexity_model is None:
        try:
            _perplexity_tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
            _perplexity_model = GPT2LMHeadModel.from_pretrained('gpt2')
            _perplexity_model.eval()
            if torch.cuda.is_available():
                _perplexity_model = _perplexity_model.cuda()
        except Exception as e:
            print(f"Warning: Could not load GPT-2 model: {e}")
            # Return None to use fallback
            return None, None
    return _perplexity_model, _perplexity_tokenizer


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
    Calculate perplexity using GPT-2 model.
    Lower perplexity = more predictable = potentially more AI-like.
    Higher perplexity = less predictable = potentially more human-like.
    """
    try:
        model, tokenizer = _get_perplexity_model()
        
        if model is None or tokenizer is None:
            # Fallback: use simple heuristic
            return 50.0
        
        # Tokenize text
        encodings = tokenizer(text, return_tensors='pt', max_length=1024, truncation=True)
        
        if torch.cuda.is_available():
            encodings = {k: v.cuda() for k, v in encodings.items()}
        
        # Calculate loss
        with torch.no_grad():
            outputs = model(**encodings, labels=encodings['input_ids'])
            loss = outputs.loss
        
        perplexity = torch.exp(loss).item()
        return float(perplexity)
    except Exception as e:
        # Fallback: return a default value if model fails
        print(f"Error calculating perplexity: {e}")
        return 50.0  # Default perplexity value


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
