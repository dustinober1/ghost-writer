"""
Probability calibration for ensemble model predictions.

Uses sklearn's CalibratedClassifierCV to map raw model probabilities
to well-calibrated probabilities that better reflect true likelihoods.

Raw ML model outputs are often overconfident (probabilities clustered
near 0 or 1). Calibration maps these to true probabilities using
cross-validation on held-out data.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import json
import os

try:
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.model_selection import cross_val_predict
    from sklearn.metrics import brier_score_loss
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from app.ml.ensemble.weights import default_model_weights, default_model_weights_list


class CalibratedEnsemble:
    """
    Wrapper for a calibrated ensemble classifier.

    Wraps a fitted VotingClassifier with sklearn's CalibratedClassifierCV
    to produce well-calibrated probabilities.

    Uses Platt scaling (sigmoid) by default for small datasets,
    isotonic regression for larger datasets.
    """

    def __init__(
        self,
        base_estimator,
        method: str = 'sigmoid',
        cv: int = 5,
        is_fitted: bool = False
    ):
        """
        Initialize the calibrated ensemble.

        Args:
            base_estimator: Fitted VotingClassifier or other sklearn classifier
            method: 'sigmoid' (Platt scaling) for small datasets,
                   'isotonic' for larger datasets
            cv: Number of cross-validation folds
            is_fitted: Whether the base estimator is already fitted
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for calibration")

        self.base_estimator = base_estimator
        self.method = method
        self.cv = cv
        self.is_fitted = is_fitted
        self.calibrated_classifier = None
        self.brier_score = None
        self.calibration_timestamp = None

        # Try to create the calibrated classifier
        self._init_calibrated_classifier()

    def _init_calibrated_classifier(self) -> None:
        """Initialize the CalibratedClassifierCV wrapper."""
        if not SKLEARN_AVAILABLE:
            return

        try:
            # Wrap the base estimator in CalibratedClassifierCV
            # ensemble=True creates an ensemble of calibrated classifiers
            # from each CV fold, which improves stability
            self.calibrated_classifier = CalibratedClassifierCV(
                self.base_estimator,
                method=self.method,
                cv=self.cv,
                ensemble=True
            )
        except Exception as e:
            print(f"Warning: Failed to initialize CalibratedClassifierCV: {e}")

    def fit(self, X_calib: np.ndarray, y_calib: np.ndarray) -> 'CalibratedEnsemble':
        """
        Fit the calibration on a separate calibration dataset.

        IMPORTANT: Use different data than training to prevent data leakage.
        Calibration should be done on held-out data that was not used
        for training the base estimator.

        Args:
            X_calib: Calibration features
            y_calib: Calibration labels (0=human, 1=AI)

        Returns:
            Self for method chaining
        """
        if self.calibrated_classifier is None:
            print("Warning: CalibratedClassifierCV not initialized, skipping calibration")
            return self

        try:
            # Fit the calibrated classifier
            self.calibrated_classifier.fit(X_calib, y_calib)
            self.is_fitted = True
            self.calibration_timestamp = datetime.utcnow()

            # Calculate Brier score to assess calibration quality
            y_prob = self.calibrated_classifier.predict_proba(X_calib)[:, 1]
            self.brier_score = brier_score_loss(y_calib, y_prob)

            print(f"Calibration complete. Brier score: {self.brier_score:.4f}")

        except Exception as e:
            print(f"Error fitting calibration: {e}")
            self.is_fitted = False

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict calibrated probabilities.

        Args:
            X: Features to predict on

        Returns:
            Array of shape (n_samples, 2) with [human_prob, ai_prob]
        """
        if not self.is_fitted or self.calibrated_classifier is None:
            # Fall back to base estimator
            if hasattr(self.base_estimator, 'predict_proba'):
                return self.base_estimator.predict_proba(X)
            else:
                # Neutral predictions if no predictor available
                if X.ndim == 1:
                    X = X.reshape(1, -1)
                return np.ones((X.shape[0], 2)) * 0.5

        try:
            return self.calibrated_classifier.predict_proba(X)
        except Exception as e:
            print(f"Error in calibrated prediction: {e}")
            # Fall back to base estimator
            if hasattr(self.base_estimator, 'predict_proba'):
                return self.base_estimator.predict_proba(X)
            return np.ones((X.shape[0], 2)) * 0.5

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Args:
            X: Features to predict on

        Returns:
            Array of class predictions (0=human, 1=AI)
        """
        probas = self.predict_proba(X)
        return (probas[:, 1] > 0.5).astype(int)

    def get_calibration_metrics(self) -> Dict[str, any]:
        """
        Get calibration quality metrics.

        Returns:
            Dict with Brier score, timestamp, and method info
        """
        return {
            'brier_score': self.brier_score,
            'calibration_timestamp': self.calibration_timestamp.isoformat() if self.calibration_timestamp else None,
            'method': self.method,
            'cv_folds': self.cv,
            'is_fitted': self.is_fitted
        }

    def get_reliability_data(
        self,
        X: np.ndarray,
        y: np.ndarray,
        n_bins: int = 10
    ) -> Dict[str, List]:
        """
        Generate data for reliability diagram visualization.

        A reliability diagram plots predicted probability vs actual frequency
        in bins. Well-calibrated models should follow the diagonal.

        Args:
            X: Features to evaluate on
            y: True labels
            n_bins: Number of bins for the reliability diagram

        Returns:
            Dict with bin data for plotting
        """
        if not self.is_fitted:
            return {}

        try:
            # Get predicted probabilities
            y_prob = self.predict_proba(X)[:, 1]

            # Create bins
            bin_edges = np.linspace(0, 1, n_bins + 1)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

            # Assign samples to bins
            bin_indices = np.digitize(y_prob, bin_edges) - 1
            bin_indices = np.clip(bin_indices, 0, n_bins - 1)

            # Calculate actual frequency and mean predicted for each bin
            mean_predicted = []
            mean_actual = []
            count = []

            for i in range(n_bins):
                mask = bin_indices == i
                if np.sum(mask) > 0:
                    mean_predicted.append(float(np.mean(y_prob[mask])))
                    mean_actual.append(float(np.mean(y[mask])))
                    count.append(int(np.sum(mask)))
                else:
                    mean_predicted.append(float(bin_centers[i]))
                    mean_actual.append(0.0)
                    count.append(0)

            return {
                'bin_centers': [float(x) for x in bin_centers],
                'mean_predicted': mean_predicted,
                'mean_actual': mean_actual,
                'count': count,
                'n_bins': n_bins
            }

        except Exception as e:
            print(f"Error generating reliability data: {e}")
            return {}


def fit_calibration(
    ensemble_estimator,
    X_calib: np.ndarray,
    y_calib: np.ndarray,
    method: str = 'sigmoid',
    cv: int = 5
) -> Optional[CalibratedEnsemble]:
    """
    Fit a CalibratedClassifierCV on an ensemble estimator.

    Args:
        ensemble_estimator: Fitted VotingClassifier or similar
        X_calib: Calibration features (MUST be separate from training data)
        y_calib: Calibration labels
        method: 'sigmoid' or 'isotonic'
        cv: Number of CV folds

    Returns:
        CalibratedEnsemble instance or None if sklearn unavailable
    """
    if not SKLEARN_AVAILABLE:
        print("Warning: scikit-learn not available, cannot calibrate")
        return None

    try:
        calibrated = CalibratedEnsemble(
            base_estimator=ensemble_estimator,
            method=method,
            cv=cv
        )
        calibrated.fit(X_calib, y_calib)
        return calibrated

    except Exception as e:
        print(f"Error fitting calibration: {e}")
        return None


def calibrate_predict(
    calibrated_ensemble: Optional[CalibratedEnsemble],
    text: str,
    feature_extractor
) -> Tuple[float, Dict[str, float]]:
    """
    Extract features from text and return calibrated AI probability.

    Args:
        calibrated_ensemble: Fitted CalibratedEnsemble (or None)
        text: Text to analyze
        feature_extractor: Function to extract features from text

    Returns:
        Tuple of (ai_probability, metadata_dict)
    """
    if not text or not text.strip():
        return 0.5, {'error': 'empty_text'}

    try:
        # Extract features
        features = feature_extractor(text)
        X = features.reshape(1, -1)

        if calibrated_ensemble is not None and calibrated_ensemble.is_fitted:
            # Use calibrated prediction
            probas = calibrated_ensemble.predict_proba(X)
            ai_prob = float(probas[0, 1])
            calibration_used = True
        else:
            # No calibration - return neutral estimate
            ai_prob = 0.5
            calibration_used = False

        metadata = {
            'calibration_used': calibration_used,
            'method': calibrated_ensemble.method if calibration_used else None,
            'brier_score': calibrated_ensemble.brier_score if calibration_used else None
        }

        return ai_prob, metadata

    except Exception as e:
        return 0.5, {'error': str(e)}


def generate_calibration_dataset(
    n_samples: int = 1000,
    ai_ratio: float = 0.5,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic calibration dataset if real data unavailable.

    Creates a mix of human-like and AI-like text patterns for calibration.

    Args:
        n_samples: Total number of samples to generate
        ai_ratio: Ratio of AI-generated samples (0-1)
        seed: Random seed for reproducibility

    Returns:
        Tuple of (X_features, y_labels)
    """
    np.random.seed(seed)

    n_ai = int(n_samples * ai_ratio)
    n_human = n_samples - n_ai

    # Human-like text features (higher burstiness, perplexity)
    human_features = np.array([
        np.random.uniform(0.8, 1.5, n_human),      # burstiness
        np.random.uniform(50, 150, n_human),        # perplexity
        np.random.uniform(0.3, 0.5, n_human),       # rare_word_ratio
        np.random.uniform(0.7, 0.9, n_human),       # unique_word_ratio
        np.random.uniform(0.2, 0.4, n_human),       # noun_ratio
        np.random.uniform(0.12, 0.2, n_human),      # verb_ratio
        np.random.uniform(0.08, 0.15, n_human),     # adjective_ratio
        np.random.uniform(0.02, 0.08, n_human),     # adverb_ratio
        np.random.uniform(4, 7, n_human),           # avg_word_length
        np.random.uniform(15, 25, n_human),         # sentence_complexity
        np.random.uniform(0.65, 0.85, n_human),     # bigram_diversity
        np.random.uniform(0.8, 0.95, n_human),      # trigram_diversity
        np.random.uniform(0.01, 0.1, n_human),      # bigram_repetition
        np.random.uniform(0.005, 0.05, n_human),    # trigram_repetition
        np.random.uniform(0.15, 0.35, n_human),     # lexical_overlap
        np.random.uniform(0.3, 0.6, n_human),       # topic_consistency
        np.random.uniform(0.2, 0.4, n_human),       # transition_smoothness
        np.random.uniform(0.08, 0.15, n_human),     # comma_ratio
        np.random.uniform(0.01, 0.03, n_human),     # semicolon_ratio
        np.random.uniform(0.02, 0.08, n_human),     # question_ratio
        np.random.uniform(0.005, 0.02, n_human),    # exclamation_ratio
        np.random.uniform(0.02, 0.05, n_human),     # parentheses_ratio
        np.random.uniform(40, 70, n_human),         # flesch_reading_ease
        np.random.uniform(8, 14, n_human),          # flesch_kincaid_grade
    ]).T

    # AI-like text features (lower burstiness, perplexity)
    ai_features = np.array([
        np.random.uniform(0.2, 0.6, n_ai),         # burstiness (lower)
        np.random.uniform(10, 40, n_ai),           # perplexity (lower)
        np.random.uniform(0.1, 0.25, n_ai),        # rare_word_ratio (lower)
        np.random.uniform(0.4, 0.7, n_ai),         # unique_word_ratio (lower)
        np.random.uniform(0.15, 0.25, n_ai),       # noun_ratio (lower)
        np.random.uniform(0.1, 0.15, n_ai),        # verb_ratio (lower)
        np.random.uniform(0.05, 0.1, n_ai),        # adjective_ratio (lower)
        np.random.uniform(0.01, 0.05, n_ai),       # adverb_ratio (lower)
        np.random.uniform(3, 5, n_ai),             # avg_word_length (lower)
        np.random.uniform(8, 15, n_ai),            # sentence_complexity (lower)
        np.random.uniform(0.4, 0.65, n_ai),        # bigram_diversity (lower)
        np.random.uniform(0.5, 0.75, n_ai),        # trigram_diversity (lower)
        np.random.uniform(0.05, 0.2, n_ai),        # bigram_repetition (higher)
        np.random.uniform(0.02, 0.1, n_ai),        # trigram_repetition (higher)
        np.random.uniform(0.1, 0.25, n_ai),        # lexical_overlap (different)
        np.random.uniform(0.6, 0.9, n_ai),         # topic_consistency (higher)
        np.random.uniform(0.1, 0.2, n_ai),         # transition_smoothness (lower)
        np.random.uniform(0.12, 0.2, n_ai),        # comma_ratio (higher)
        np.random.uniform(0.005, 0.015, n_ai),     # semicolon_ratio (lower)
        np.random.uniform(0.01, 0.04, n_ai),       # question_ratio (lower)
        np.random.uniform(0.002, 0.01, n_ai),      # exclamation_ratio (lower)
        np.random.uniform(0.01, 0.03, n_ai),       # parentheses_ratio (lower)
        np.random.uniform(70, 90, n_ai),           # flesch_reading_ease (higher)
        np.random.uniform(6, 10, n_ai),            # flesch_kincaid_grade (lower)
    ]).T

    # Combine and shuffle
    X = np.vstack([human_features, ai_features])
    y = np.hstack([np.zeros(n_human), np.ones(n_ai)])

    # Shuffle
    indices = np.random.permutation(n_samples)
    X = X[indices]
    y = y[indices]

    return X, y


def get_preloaded_calibration() -> Optional[CalibratedEnsemble]:
    """
    Load pre-trained calibration if available.

    Checks for a saved calibration file and loads it.

    Returns:
        CalibratedEnsemble or None
    """
    calibration_path = os.path.join(
        os.path.dirname(__file__),
        'calibration_data.json'
    )

    if not os.path.exists(calibration_path):
        return None

    try:
        with open(calibration_path, 'r') as f:
            data = json.load(f)

        print(f"Loaded calibration from {calibration_timestamp}")
        return CalibratedEnsemble(
            base_estimator=None,
            method=data.get('method', 'sigmoid'),
            cv=data.get('cv', 5),
            is_fitted=False  # Would need full model to be truly fitted
        )

    except Exception as e:
        print(f"Error loading calibration: {e}")
        return None


def save_calibration_data(calibration_metrics: Dict[str, any]) -> bool:
    """
    Save calibration metrics to file.

    Args:
        calibration_metrics: Dict with calibration data

    Returns:
        True if saved successfully
    """
    calibration_path = os.path.join(
        os.path.dirname(__file__),
        'calibration_data.json'
    )

    try:
        with open(calibration_path, 'w') as f:
            json.dump(calibration_metrics, f, indent=2, default=str)
        return True

    except Exception as e:
        print(f"Error saving calibration: {e}")
        return False
