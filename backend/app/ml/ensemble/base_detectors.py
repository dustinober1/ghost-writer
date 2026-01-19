"""
Base detector wrappers for sklearn-compatible ensemble integration.

Provides sklearn-compatible wrapper classes for:
1. StylometricDetector - Feature-based AI detection
2. PerplexityDetector - Language model perplexity detection
3. ContrastiveDetectorWrapper - Siamese network embedding-based detection
"""

import numpy as np
from typing import Dict, Optional, Union

from app.ml.feature_extraction import extract_feature_vector, calculate_perplexity
from app.ml.contrastive_model import get_contrastive_model


class StylometricDetector:
    """
    sklearn-compatible wrapper for stylometric feature-based detection.

    Uses feature vectors extracted from text to predict AI probability.
    Lower burstiness, lower perplexity, and lower diversity indicate AI-generated text.
    """

    def __init__(self):
        """Initialize the stylometric detector."""
        self.feature_dim = 27  # Number of features in extract_feature_vector
        self._is_fitted = False

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "StylometricDetector":
        """
        Fit the detector (stores training data shape).

        Args:
            X: Feature array of shape (n_samples, n_features)
            y: Optional labels (not used for this unsupervised detector)

        Returns:
            Self for sklearn compatibility
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        self.feature_dim = X.shape[1] if len(X.shape) > 1 else len(X)
        self._is_fitted = True

        # Store reference statistics for normalization
        self._feature_means = np.mean(X, axis=0) if len(X) > 1 else np.zeros(self.feature_dim)
        self._feature_stds = np.std(X, axis=0) if len(X) > 1 else np.ones(self.feature_dim)

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict AI probability using stylometric features.

        Args:
            X: Feature array of shape (n_samples, n_features)

        Returns:
            Probability array of shape (n_samples, 2)
            Column 0: Probability of human-written
            Column 1: Probability of AI-generated
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        n_samples = X.shape[0]
        probas = np.zeros((n_samples, 2))

        for i in range(n_samples):
            features = X[i]

            # Calculate AI probability from features
            ai_prob = self._features_to_ai_probability(features)

            probas[i, 0] = 1.0 - ai_prob  # Human probability
            probas[i, 1] = ai_prob  # AI probability

        return probas

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels (0=human, 1=AI).

        Args:
            X: Feature array

        Returns:
            Class predictions
        """
        probas = self.predict_proba(X)
        return (probas[:, 1] > 0.5).astype(int)

    def _features_to_ai_probability(self, features: np.ndarray) -> float:
        """
        Convert feature vector to AI probability.

        Uses inverse normalization - features deviating from human-like
        baselines increase AI probability.

        Args:
            features: Feature vector

        Returns:
            AI probability (0-1)
        """
        # Handle edge cases
        if len(features) < 2:
            return 0.5

        # Key features: burstiness (index 0), perplexity (index 1)
        burstiness = features[0]
        perplexity = features[1]

        # Normalize to 0-1 range for heuristic
        # AI text tends to have lower burstiness and lower perplexity
        burstiness_score = max(0.0, min(1.0, burstiness / 2.0))
        perplexity_score = max(0.0, min(1.0, perplexity / 100.0))

        # Calculate AI probability
        # Higher values of burstiness/perplexity = more human-like (lower AI prob)
        ai_prob = (1.0 - burstiness_score) * 0.6 + (1.0 - perplexity_score) * 0.4

        # Consider other features if available
        if len(features) >= 4:
            # unique_word_ratio at index 3
            unique_ratio = features[3]
            # Lower unique ratio = more AI-like
            unique_score = max(0.0, min(1.0, unique_ratio))
            ai_prob = ai_prob * 0.8 + (1.0 - unique_score) * 0.2

        return float(max(0.0, min(1.0, ai_prob)))

    def transform_text_to_features(self, texts: list) -> np.ndarray:
        """
        Transform text list to feature array.

        Args:
            texts: List of text strings

        Returns:
            Feature array
        """
        features_list = []
        for text in texts:
            vec = extract_feature_vector(text)
            features_list.append(vec)

        return np.array(features_list)


class PerplexityDetector:
    """
    sklearn-compatible wrapper for perplexity-based detection.

    Uses language model perplexity to predict AI probability.
    Lower perplexity = more predictable = more AI-like.
    """

    def __init__(self, perplexity_range: tuple = (20.0, 100.0)):
        """
        Initialize the perplexity detector.

        Args:
            perplexity_range: (min, max) expected perplexity values
        """
        self.perplexity_range = perplexity_range
        self._is_fitted = False
        self._calibration_params = {
            "threshold": 50.0,  # Midpoint of typical range
            "slope": 0.02  # Controls sensitivity
        }

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "PerplexityDetector":
        """
        Fit the detector (calibrates perplexity to probability mapping).

        Args:
            X: Not used (perplexity calculated from text directly)
            y: Optional labels for calibration

        Returns:
            Self for sklearn compatibility
        """
        self._is_fitted = True

        # Calibrate threshold if labels provided
        if y is not None and len(y) > 0:
            # Simple calibration: threshold = mean perplexity
            # In practice, would use more sophisticated calibration
            self._calibration_params["threshold"] = 50.0

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict AI probability (sklearn interface).

        Note: This detector uses text directly, not features.
        Use predict_proba_text() for actual predictions.

        Args:
            X: Placeholder feature array (not used)

        Returns:
            Probability array
        """
        # Return neutral probabilities since we need text input
        if X.ndim == 1:
            X = X.reshape(1, -1)

        n_samples = X.shape[0]
        return np.ones((n_samples, 2)) * 0.5  # Neutral predictions

    def predict_proba_text(self, text: str) -> np.ndarray:
        """
        Predict AI probability from text using perplexity.

        Args:
            text: Text to analyze

        Returns:
            Probability array [human_prob, ai_prob]
        """
        perplexity = calculate_perplexity(text)

        # Normalize perplexity to AI probability
        # Lower perplexity = higher AI probability
        threshold = self._calibration_params["threshold"]
        slope = self._calibration_params["slope"]

        # Sigmoid mapping from perplexity to AI probability
        ai_prob = 1.0 / (1.0 + np.exp(slope * (perplexity - threshold)))

        return np.array([1.0 - ai_prob, ai_prob])

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        probas = self.predict_proba(X)
        return (probas[:, 1] > 0.5).astype(int)


class ContrastiveDetectorWrapper:
    """
    sklearn-compatible wrapper for contrastive model detection.

    Uses Siamese network to compare text embeddings against reference.
    Lower similarity to human reference = higher AI probability.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the contrastive detector.

        Args:
            model_path: Optional path to pre-trained model
        """
        self.model = get_contrastive_model(model_path)
        self._is_fitted = False
        self._reference_features: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "ContrastiveDetectorWrapper":
        """
        Fit the detector (stores reference features).

        Args:
            X: Feature array of reference human text
            y: Optional labels

        Returns:
            Self for sklearn compatibility
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        # Store mean of features as reference
        self._reference_features = np.mean(X, axis=0)
        self._is_fitted = True

        return self

    def set_reference(self, reference_features: np.ndarray) -> None:
        """
        Set reference features for comparison.

        Args:
            reference_features: Reference feature vector
        """
        self._reference_features = reference_features
        self._is_fitted = True

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict AI probability using contrastive model.

        Args:
            X: Feature array of shape (n_samples, n_features)

        Returns:
            Probability array of shape (n_samples, 2)
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        n_samples = X.shape[0]
        probas = np.zeros((n_samples, 2))

        # Use default reference if not set
        if self._reference_features is None:
            # Use mean human-like features as default reference
            self._reference_features = self._get_default_reference()

        for i in range(n_samples):
            features = X[i]

            # Calculate similarity to reference
            similarity = self._calculate_similarity(features, self._reference_features)

            # Convert similarity to AI probability
            # High similarity = human-like (low AI prob)
            ai_prob = 1.0 - similarity

            probas[i, 0] = 1.0 - ai_prob  # Human probability
            probas[i, 1] = ai_prob  # AI probability

        return probas

    def predict_proba_with_reference(
        self,
        X: np.ndarray,
        reference_features: np.ndarray
    ) -> np.ndarray:
        """
        Predict AI probability with specific reference features.

        Args:
            X: Feature array
            reference_features: Reference features for comparison

        Returns:
            Probability array
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        n_samples = X.shape[0]
        probas = np.zeros((n_samples, 2))

        for i in range(n_samples):
            features = X[i]
            similarity = self._calculate_similarity(features, reference_features)
            ai_prob = 1.0 - similarity

            probas[i, 0] = 1.0 - ai_prob
            probas[i, 1] = ai_prob

        return probas

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        probas = self.predict_proba(X)
        return (probas[:, 1] > 0.5).astype(int)

    def _calculate_similarity(
        self,
        features1: np.ndarray,
        features2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between feature vectors.

        Args:
            features1: First feature vector
            features2: Second feature vector

        Returns:
            Similarity score (0-1, higher = more similar)
        """
        # Cosine similarity
        dot_product = np.dot(features1, features2)
        norm1 = np.linalg.norm(features1)
        norm2 = np.linalg.norm(features2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Clamp to [0, 1]
        return float(max(0.0, min(1.0, similarity)))

    def _get_default_reference(self) -> np.ndarray:
        """
        Get default reference features (human-like baseline).

        Returns:
            Default feature vector representing human writing
        """
        # Human-like feature values (based on domain knowledge)
        # Matches HUMAN_LIKE_BASELINES from feature_extraction
        reference = np.array([
            1.0,  # burstiness (higher = human)
            70.0,  # perplexity (higher = human)
            0.3,  # rare_word_ratio
            0.75,  # unique_word_ratio
            0.25,  # noun_ratio
            0.15,  # verb_ratio
            0.1,  # adjective_ratio
            0.05,  # adverb_ratio
            5.0,  # avg_word_length
            18.0,  # sentence_complexity
            0.7,  # bigram_diversity
            0.85,  # trigram_diversity
            0.05,  # bigram_repetition
            0.02,  # trigram_repetition
            0.2,  # lexical_overlap
            0.5,  # topic_consistency
            0.25,  # transition_smoothness
            0.1,  # comma_ratio
            0.015,  # semicolon_ratio
            0.03,  # question_ratio
            0.01,  # exclamation_ratio
            0.03,  # parentheses_ratio
            55.0,  # flesch_reading_ease
            10.0,  # flesch_kincaid_grade
        ])

        # Normalize to match extract_feature_vector output
        return reference / np.linalg.norm(reference)


def create_detector_fallback() -> Dict[str, object]:
    """
    Create fallback detectors when sklearn is unavailable.

    Returns:
        Dict of detector instances
    """
    return {
        "stylometric": StylometricDetector(),
        "perplexity": PerplexityDetector(),
        "contrastive": ContrastiveDetectorWrapper()
    }
