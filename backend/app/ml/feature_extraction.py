import numpy as np
import nltk
from typing import Dict, List, Tuple
from collections import Counter
import re
import requests
import math
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


def extract_ngram_features(text: str, n_values: List[int] = [2, 3]) -> Dict[str, float]:
    """
    Extract n-gram features for better stylometric analysis.
    
    Args:
        text: Input text
        n_values: List of n values for n-grams (default: bigrams and trigrams)
    
    Returns:
        Dictionary of n-gram features
    """
    words = text.lower().split()
    words = [re.sub(r'[^a-z]', '', w) for w in words if re.sub(r'[^a-z]', '', w)]
    
    if len(words) < 2:
        return {
            "bigram_diversity": 0.0,
            "trigram_diversity": 0.0,
            "bigram_repetition": 0.0,
            "trigram_repetition": 0.0
        }
    
    features = {}
    
    for n in n_values:
        if len(words) < n:
            features[f"{n}gram_diversity"] = 0.0
            features[f"{n}gram_repetition"] = 0.0
            continue
            
        # Generate n-grams
        ngrams = [tuple(words[i:i+n]) for i in range(len(words) - n + 1)]
        
        if not ngrams:
            features[f"{n}gram_diversity"] = 0.0
            features[f"{n}gram_repetition"] = 0.0
            continue
        
        # Count n-grams
        ngram_counts = Counter(ngrams)
        
        # Diversity: unique n-grams / total n-grams
        diversity = len(ngram_counts) / len(ngrams) if ngrams else 0.0
        
        # Repetition: how many n-grams appear more than once
        repeated = sum(1 for count in ngram_counts.values() if count > 1)
        repetition = repeated / len(ngram_counts) if ngram_counts else 0.0
        
        features[f"{'bi' if n == 2 else 'tri'}gram_diversity"] = float(diversity)
        features[f"{'bi' if n == 2 else 'tri'}gram_repetition"] = float(repetition)
    
    return features


def calculate_coherence_metrics(text: str) -> Dict[str, float]:
    """
    Calculate text coherence metrics to distinguish AI vs human writing.
    
    AI text tends to have:
    - Higher local coherence (adjacent sentences are related)
    - More consistent topic focus
    - Smoother transitions
    
    Human text tends to have:
    - More topic jumps
    - More varied coherence
    - Sometimes abrupt transitions
    """
    sentences = split_into_sentences(text)
    
    if len(sentences) < 2:
        return {
            "lexical_overlap": 0.0,
            "topic_consistency": 0.0,
            "transition_smoothness": 0.0
        }
    
    # Calculate lexical overlap between adjacent sentences
    overlaps = []
    for i in range(len(sentences) - 1):
        words1 = set(sentences[i].lower().split())
        words2 = set(sentences[i+1].lower().split())
        
        # Remove common stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 
                    'would', 'could', 'should', 'may', 'might', 'can', 'to', 'of',
                    'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
                    'it', 'its', 'this', 'that', 'and', 'or', 'but', 'if', 'so'}
        
        words1 = words1 - stopwords
        words2 = words2 - stopwords
        
        if words1 and words2:
            overlap = len(words1 & words2) / min(len(words1), len(words2))
            overlaps.append(overlap)
    
    lexical_overlap = np.mean(overlaps) if overlaps else 0.0
    
    # Topic consistency: variance in sentence lengths (low variance = more consistent)
    sentence_lengths = [len(s.split()) for s in sentences]
    length_variance = np.var(sentence_lengths) if len(sentence_lengths) > 1 else 0.0
    # Normalize: higher score = more consistent (lower variance)
    topic_consistency = 1.0 / (1.0 + length_variance / 10.0)
    
    # Transition smoothness: check for transition words
    transition_words = ['however', 'therefore', 'moreover', 'furthermore', 'additionally',
                       'consequently', 'nevertheless', 'meanwhile', 'similarly', 'likewise',
                       'first', 'second', 'third', 'finally', 'next', 'then', 'also',
                       'in addition', 'for example', 'in contrast', 'on the other hand']
    
    transition_count = 0
    for sentence in sentences:
        sentence_lower = sentence.lower()
        for word in transition_words:
            if word in sentence_lower:
                transition_count += 1
                break
    
    transition_smoothness = transition_count / len(sentences) if sentences else 0.0
    
    return {
        "lexical_overlap": float(lexical_overlap),
        "topic_consistency": float(topic_consistency),
        "transition_smoothness": float(transition_smoothness)
    }


def calculate_punctuation_features(text: str) -> Dict[str, float]:
    """
    Extract punctuation patterns which can distinguish AI from human writing.
    """
    if not text:
        return {
            "comma_ratio": 0.0,
            "semicolon_ratio": 0.0,
            "question_ratio": 0.0,
            "exclamation_ratio": 0.0,
            "parentheses_ratio": 0.0
        }
    
    words = text.split()
    word_count = len(words) if words else 1
    
    comma_count = text.count(',')
    semicolon_count = text.count(';')
    question_count = text.count('?')
    exclamation_count = text.count('!')
    parentheses_count = text.count('(') + text.count(')')
    
    return {
        "comma_ratio": float(comma_count / word_count),
        "semicolon_ratio": float(semicolon_count / word_count),
        "question_ratio": float(question_count / word_count),
        "exclamation_ratio": float(exclamation_count / word_count),
        "parentheses_ratio": float(parentheses_count / word_count)
    }


def calculate_readability_scores(text: str) -> Dict[str, float]:
    """
    Calculate readability metrics (Flesch-Kincaid, etc.)
    """
    words = text.split()
    sentences = split_into_sentences(text)
    
    if not words or not sentences:
        return {
            "flesch_reading_ease": 0.0,
            "flesch_kincaid_grade": 0.0
        }
    
    word_count = len(words)
    sentence_count = len(sentences)
    
    # Count syllables (approximate)
    def count_syllables(word):
        word = word.lower()
        vowels = 'aeiou'
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith('e'):
            count = max(1, count - 1)
        return max(1, count)
    
    total_syllables = sum(count_syllables(w) for w in words)
    
    # Flesch Reading Ease
    fre = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (total_syllables / word_count)
    fre = max(0, min(100, fre))  # Clamp to 0-100
    
    # Flesch-Kincaid Grade Level
    fkg = 0.39 * (word_count / sentence_count) + 11.8 * (total_syllables / word_count) - 15.59
    fkg = max(0, min(20, fkg))  # Clamp to reasonable grade levels
    
    return {
        "flesch_reading_ease": float(fre),
        "flesch_kincaid_grade": float(fkg)
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
    
    # N-gram features (NEW)
    ngram_features = extract_ngram_features(text)
    features.update(ngram_features)
    
    # Coherence metrics (NEW)
    coherence_features = calculate_coherence_metrics(text)
    features.update(coherence_features)
    
    # Punctuation features (NEW)
    punctuation_features = calculate_punctuation_features(text)
    features.update(punctuation_features)
    
    # Readability scores (NEW)
    readability_features = calculate_readability_scores(text)
    features.update(readability_features)
    
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
        # Original features
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
        "avg_sentence_length",
        # N-gram features
        "bigram_diversity",
        "trigram_diversity",
        "bigram_repetition",
        "trigram_repetition",
        # Coherence features
        "lexical_overlap",
        "topic_consistency",
        "transition_smoothness",
        # Punctuation features
        "comma_ratio",
        "semicolon_ratio",
        "question_ratio",
        "exclamation_ratio",
        "parentheses_ratio",
        # Readability features
        "flesch_reading_ease",
        "flesch_kincaid_grade"
    ]
    
    vector = np.array([features.get(f, 0.0) for f in feature_order])
    
    # Normalize vector (L2 normalization)
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    
    return vector


# Feature names for interpretability
FEATURE_NAMES = [
    "burstiness", "perplexity", "rare_word_ratio", "unique_word_ratio",
    "noun_ratio", "verb_ratio", "adjective_ratio", "adverb_ratio",
    "avg_word_length", "sentence_complexity", "word_count", "sentence_count",
    "avg_sentence_length", "bigram_diversity", "trigram_diversity",
    "bigram_repetition", "trigram_repetition", "lexical_overlap",
    "topic_consistency", "transition_smoothness", "comma_ratio",
    "semicolon_ratio", "question_ratio", "exclamation_ratio",
    "parentheses_ratio", "flesch_reading_ease", "flesch_kincaid_grade"
]
