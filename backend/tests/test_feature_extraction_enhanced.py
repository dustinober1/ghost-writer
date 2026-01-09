"""Tests for enhanced feature extraction (n-grams, coherence)."""
import pytest
import numpy as np


class TestEnhancedFeatureExtraction:
    """Test new feature extraction functions."""
    
    def test_extract_ngram_features(self):
        """Test n-gram feature extraction."""
        from app.ml.feature_extraction import extract_ngram_features
        
        text = "The quick brown fox jumps over the lazy dog again and again."
        features = extract_ngram_features(text)
        
        assert "bigram_diversity" in features
        assert "trigram_diversity" in features
        assert "bigram_repetition" in features
        assert "trigram_repetition" in features
        
        # Diversity should be between 0 and 1
        assert 0 <= features["bigram_diversity"] <= 1
        assert 0 <= features["trigram_diversity"] <= 1
    
    def test_extract_ngram_features_short_text(self):
        """Test n-gram extraction with very short text."""
        from app.ml.feature_extraction import extract_ngram_features
        
        text = "Hi"
        features = extract_ngram_features(text)
        
        assert features["bigram_diversity"] == 0.0
        assert features["trigram_diversity"] == 0.0
    
    def test_calculate_coherence_metrics(self):
        """Test coherence metrics calculation."""
        from app.ml.feature_extraction import calculate_coherence_metrics
        
        text = """
        The sun was shining brightly. It was a beautiful day.
        However, dark clouds appeared on the horizon. Soon it began to rain.
        Therefore, everyone went inside.
        """
        features = calculate_coherence_metrics(text)
        
        assert "lexical_overlap" in features
        assert "topic_consistency" in features
        assert "transition_smoothness" in features
        
        # Check ranges
        assert 0 <= features["lexical_overlap"] <= 1
        assert 0 <= features["topic_consistency"] <= 1
        assert 0 <= features["transition_smoothness"] <= 1
    
    def test_coherence_with_transitions(self):
        """Test coherence detects transition words."""
        from app.ml.feature_extraction import calculate_coherence_metrics
        
        text_with_transitions = """
        First, we analyze the data.
        Moreover, we verify the results.
        Therefore, the conclusion is valid.
        """
        
        text_without_transitions = """
        We analyze the data.
        We verify the results.
        The conclusion is valid.
        """
        
        features_with = calculate_coherence_metrics(text_with_transitions)
        features_without = calculate_coherence_metrics(text_without_transitions)
        
        # Text with transitions should have higher smoothness
        assert features_with["transition_smoothness"] >= features_without["transition_smoothness"]
    
    def test_calculate_punctuation_features(self):
        """Test punctuation feature extraction."""
        from app.ml.feature_extraction import calculate_punctuation_features
        
        text = "Hello, world! How are you? I'm (quite) well; thanks."
        features = calculate_punctuation_features(text)
        
        assert "comma_ratio" in features
        assert "semicolon_ratio" in features
        assert "question_ratio" in features
        assert "exclamation_ratio" in features
        assert "parentheses_ratio" in features
        
        # Should have detected punctuation
        assert features["comma_ratio"] > 0
        assert features["question_ratio"] > 0
        assert features["exclamation_ratio"] > 0
    
    def test_calculate_punctuation_empty_text(self):
        """Test punctuation features with empty text."""
        from app.ml.feature_extraction import calculate_punctuation_features
        
        features = calculate_punctuation_features("")
        
        assert features["comma_ratio"] == 0.0
        assert features["question_ratio"] == 0.0
    
    def test_calculate_readability_scores(self):
        """Test readability score calculation."""
        from app.ml.feature_extraction import calculate_readability_scores
        
        simple_text = "The cat sat. The dog ran. The bird flew."
        complex_text = """
        The phenomenological manifestation of consciousness represents
        an epistemological challenge that transcends traditional
        philosophical methodologies and necessitates interdisciplinary
        approaches incorporating neuroscientific perspectives.
        """
        
        simple_features = calculate_readability_scores(simple_text)
        complex_features = calculate_readability_scores(complex_text)
        
        # Simple text should have higher reading ease
        assert simple_features["flesch_reading_ease"] > complex_features["flesch_reading_ease"]
        
        # Complex text should have higher grade level
        assert complex_features["flesch_kincaid_grade"] > simple_features["flesch_kincaid_grade"]
    
    def test_extract_feature_vector_dimensions(self):
        """Test that feature vector has expected dimensions."""
        from app.ml.feature_extraction import extract_feature_vector, FEATURE_NAMES
        
        text = "This is a test sentence for feature extraction analysis."
        vector = extract_feature_vector(text)
        
        # Vector length should match feature names
        assert len(vector) == len(FEATURE_NAMES)
    
    def test_extract_feature_vector_normalized(self):
        """Test that feature vector is normalized."""
        from app.ml.feature_extraction import extract_feature_vector
        
        text = "This is a longer piece of text with multiple sentences. It should produce normalized features."
        vector = extract_feature_vector(text)
        
        # L2 norm should be approximately 1
        norm = np.linalg.norm(vector)
        assert 0.99 <= norm <= 1.01 or norm == 0  # Allow for zero vector case
    
    def test_extract_all_features_comprehensive(self):
        """Test that all features are extracted."""
        from app.ml.feature_extraction import extract_all_features
        
        text = """
        Artificial intelligence is transforming our world. However, many challenges remain.
        First, we must address ethical concerns. Moreover, we need better interpretability.
        The future looks promising, but uncertain.
        """
        
        features = extract_all_features(text)
        
        # Original features
        assert "burstiness" in features
        assert "perplexity" in features
        assert "noun_ratio" in features
        assert "verb_ratio" in features
        
        # New n-gram features
        assert "bigram_diversity" in features
        assert "trigram_diversity" in features
        
        # New coherence features
        assert "lexical_overlap" in features
        assert "topic_consistency" in features
        assert "transition_smoothness" in features
        
        # New punctuation features
        assert "comma_ratio" in features
        
        # New readability features
        assert "flesch_reading_ease" in features
        assert "flesch_kincaid_grade" in features
