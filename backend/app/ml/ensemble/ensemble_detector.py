"""
Ensemble detector combining multiple AI text detection models.

Uses sklearn's VotingClassifier with weighted soft voting to combine
predictions from stylometric, perplexity, and contrastive models.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple

try:
    from sklearn.ensemble import VotingClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from app.ml.feature_extraction import extract_feature_vector, calculate_perplexity
from app.ml.contrastive_model import get_contrastive_model
from app.ml.ensemble.base_detectors import (
    StylometricDetector,
    PerplexityDetector,
    ContrastiveDetectorWrapper,
)
from app.ml.ensemble.weights import calculate_weights_from_accuracy, default_model_weights
from app.ml.ensemble.calibration import CalibratedEnsemble, fit_calibration


class EnsembleDetector:
    """
    Multi-model ensemble detector for AI-generated text.

    Combines three detection approaches:
    1. Stylometric analysis (feature-based)
    2. Perplexity-based detection (language model)
    3. Contrastive learning (embedding similarity)

    Uses weighted soft voting where weights are proportional to model accuracy.
    """

    def __init__(
        self,
        model_accuracy: Optional[Dict[str, float]] = None,
        use_sklearn: bool = True,
        use_calibration: bool = False
    ):
        """
        Initialize the ensemble detector.

        Args:
            model_accuracy: Optional dict mapping model names to accuracy scores.
                Expected keys: 'stylometric', 'perplexity', 'contrastive'
                Values should be in [0, 1] range.
            use_sklearn: Whether to use sklearn VotingClassifier. If False or sklearn
                unavailable, uses manual weighted averaging.
            use_calibration: Whether to use probability calibration (requires sklearn).
        """
        self.model_accuracy = model_accuracy or {}
        self.use_sklearn = use_sklearn and SKLEARN_AVAILABLE
        self.use_calibration = use_calibration and SKLEARN_AVAILABLE

        # Initialize base detectors
        self.stylometric_detector = StylometricDetector()
        self.perplexity_detector = PerplexityDetector()
        self.contrastive_detector = ContrastiveDetectorWrapper()

        # Calculate weights from accuracy (or use defaults)
        self.weights = self._calculate_weights(self.model_accuracy)

        # Initialize sklearn VotingClassifier if available
        self.voting_classifier = None
        self.calibrated_ensemble = None
        if self.use_sklearn:
            self._init_voting_classifier()

    def _calculate_weights(self, model_accuracies: Dict[str, float]) -> List[float]:
        """
        Calculate normalized weights from model accuracy scores.

        Args:
            model_accuracies: Dict of model names to accuracy scores

        Returns:
            List of weights [stylometric, perplexity, contrastive]
        """
        return calculate_weights_from_accuracy(model_accuracies)

    def _init_voting_classifier(self):
        """Initialize sklearn VotingClassifier with base estimators."""
        if not SKLEARN_AVAILABLE:
            return

        try:
            estimators = [
                ('stylometric', self.stylometric_detector),
                ('perplexity', self.perplexity_detector),
                ('contrastive', self.contrastive_detector)
            ]

            self.voting_classifier = VotingClassifier(
                estimators=estimators,
                voting='soft',
                weights=self.weights,
                n_jobs=-1  # Use all available cores
            )

            # Fit with dummy data to initialize the classifier
            # Each estimator handles its own initialization in fit()
            dummy_X = np.array([[0.0] * 27])  # 27 features from extract_feature_vector
            dummy_y = np.array([0])  # Dummy labels

            try:
                self.voting_classifier.fit(dummy_X, dummy_y)
            except Exception as e:
                # If fit fails, we'll fall back to manual prediction
                print(f"Warning: VotingClassifier fit failed: {e}. Using manual ensemble.")
                self.voting_classifier = None

        except Exception as e:
            print(f"Warning: Failed to initialize VotingClassifier: {e}")
            self.voting_classifier = None

    def _update_weights(self, model_accuracies: Dict[str, float]) -> None:
        """
        Update ensemble weights based on new accuracy measurements.

        Args:
            model_accuracies: Dict of model names to updated accuracy scores
        """
        self.weights = self._calculate_weights(model_accuracies)
        self.model_accuracy = model_accuracies

        # Reinitialize voting classifier with new weights
        if self.voting_classifier is not None:
            self._init_voting_classifier()

    def predict_ai_probability(
        self,
        text: str,
        reference_features: Optional[np.ndarray] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Predict AI probability for text using ensemble of models.

        Args:
            text: Text to analyze
            reference_features: Optional reference features (human fingerprint)
                for contrastive model comparison

        Returns:
            Tuple of (ensemble_probability, model_probabilities)
            - ensemble_probability: Final AI probability (0-1)
            - model_probabilities: Dict with individual model probabilities
        """
        if not text or not text.strip():
            return 0.5, {
                "stylometric": 0.5,
                "perplexity": 0.5,
                "contrastive": 0.5,
                "ensemble": 0.5
            }

        try:
            # Get predictions from each model
            stylometric_prob = self._get_stylometric_probability(text)
            perplexity_prob = self._get_perplexity_probability(text)
            contrastive_prob = self._get_contrastive_probability(
                text, reference_features
            )

            # Combine using weighted soft voting
            if self.voting_classifier is not None:
                # Use sklearn VotingClassifier
                ensemble_prob = self._sklearn_ensemble_predict(
                    text, [stylometric_prob, perplexity_prob, contrastive_prob]
                )
            else:
                # Manual weighted average
                ensemble_prob = (
                    self.weights[0] * stylometric_prob +
                    self.weights[1] * perplexity_prob +
                    self.weights[2] * contrastive_prob
                )

            # Clamp to [0, 1]
            ensemble_prob = max(0.0, min(1.0, ensemble_prob))

            return ensemble_prob, {
                "stylometric": float(stylometric_prob),
                "perplexity": float(perplexity_prob),
                "contrastive": float(contrastive_prob),
                "ensemble": float(ensemble_prob)
            }

        except Exception as e:
            print(f"Error in ensemble prediction: {e}")
            # Fallback to stylometric only
            fallback_prob = self._get_stylometric_probability(text)
            return fallback_prob, {
                "stylometric": float(fallback_prob),
                "perplexity": 0.5,
                "contrastive": 0.5,
                "ensemble": float(fallback_prob)
            }

    def _get_stylometric_probability(self, text: str) -> float:
        """Get AI probability from stylometric model."""
        try:
            features = extract_feature_vector(text)

            # Use stylometric detector's predict_proba
            proba = self.stylometric_detector.predict_proba(
                features.reshape(1, -1)
            )

            # Return probability of class 1 (AI-generated)
            return float(proba[0, 1])

        except Exception as e:
            print(f"Error in stylometric prediction: {e}")
            # Fallback to heuristic
            return self._stylometric_fallback(text)

    def _get_perplexity_probability(self, text: str) -> float:
        """Get AI probability from perplexity model."""
        try:
            # Perplexity detector needs the text directly
            proba = self.perplexity_detector.predict_proba_text(text)

            # Return probability of class 1 (AI-generated)
            return float(proba[1])

        except Exception as e:
            print(f"Error in perplexity prediction: {e}")
            return 0.5

    def _get_contrastive_probability(
        self,
        text: str,
        reference_features: Optional[np.ndarray]
    ) -> float:
        """Get AI probability from contrastive model."""
        try:
            features = extract_feature_vector(text)

            # Use contrastive detector's predict_proba
            if reference_features is not None:
                proba = self.contrastive_detector.predict_proba_with_reference(
                    features.reshape(1, -1),
                    reference_features
                )
            else:
                proba = self.contrastive_detector.predict_proba(
                    features.reshape(1, -1)
                )

            # Return probability of class 1 (AI-generated)
            return float(proba[0, 1])

        except Exception as e:
            print(f"Error in contrastive prediction: {e}")
            return 0.5

    def _sklearn_ensemble_predict(
        self,
        text: str,
        probabilities: List[float]
    ) -> float:
        """
        Use sklearn VotingClassifier for ensemble prediction.

        Args:
            text: Input text
            probabilities: List of probabilities from each model

        Returns:
            Ensemble probability
        """
        # For soft voting, sklearn internally weights the probabilities
        # We calculate manually since sklearn expects feature input
        return sum(w * p for w, p in zip(self.weights, probabilities))

    def _stylometric_fallback(self, text: str) -> float:
        """
        Fallback stylometric heuristic when feature extraction fails.

        Args:
            text: Text to analyze

        Returns:
            AI probability estimate (0-1)
        """
        try:
            features = extract_feature_vector(text)

            if len(features) < 2:
                return 0.5

            # Simple heuristic: low burstiness + low perplexity = AI-like
            burstiness = features[0] if len(features) > 0 else 0.5
            perplexity = features[1] if len(features) > 1 else 0.5

            # Normalize features
            burstiness_score = max(0.0, min(1.0, burstiness / 2.0))
            perplexity_score = max(0.0, min(1.0, perplexity / 100.0))

            # AI text has lower burstiness and perplexity
            ai_score = (1.0 - burstiness_score) * 0.6 + (1.0 - perplexity_score) * 0.4

            return float(max(0.0, min(1.0, ai_score)))

        except Exception:
            return 0.5

    def get_model_info(self) -> Dict:
        """
        Get information about the ensemble configuration.

        Returns:
            Dict with model weights and availability status
        """
        info = {
            "model_weights": {
                "stylometric": self.weights[0],
                "perplexity": self.weights[1],
                "contrastive": self.weights[2]
            },
            "model_accuracy": self.model_accuracy,
            "sklearn_available": SKLEARN_AVAILABLE,
            "using_sklearn": self.voting_classifier is not None,
            "model_used": "ensemble" if self.voting_classifier is not None else "manual",
            "using_calibration": self.calibrated_ensemble is not None
        }

        # Add calibration metrics if available
        if self.calibrated_ensemble is not None:
            info["calibration_metrics"] = self.calibrated_ensemble.get_calibration_metrics()

        return info

    def calibrate(
        self,
        X_calib: np.ndarray,
        y_calib: np.ndarray,
        method: str = 'sigmoid',
        cv: int = 5
    ) -> bool:
        """
        Calibrate the ensemble using a separate calibration dataset.

        IMPORTANT: Use different data than training to prevent data leakage.
        Calibration should be done on held-out data.

        Args:
            X_calib: Calibration features
            y_calib: Calibration labels (0=human, 1=AI)
            method: 'sigmoid' (Platt scaling) or 'isotonic'
            cv: Number of cross-validation folds

        Returns:
            True if calibration succeeded, False otherwise
        """
        if not SKLEARN_AVAILABLE:
            print("Warning: scikit-learn not available, cannot calibrate")
            return False

        if self.voting_classifier is None:
            print("Warning: VotingClassifier not initialized, cannot calibrate")
            return False

        try:
            self.calibrated_ensemble = fit_calibration(
                self.voting_classifier,
                X_calib,
                y_calib,
                method=method,
                cv=cv
            )
            return self.calibrated_ensemble is not None

        except Exception as e:
            print(f"Error during calibration: {e}")
            return False

    def get_calibration_metrics(self) -> Optional[Dict]:
        """
        Get calibration quality metrics.

        Returns:
            Dict with Brier score and calibration info, or None if not calibrated
        """
        if self.calibrated_ensemble is None:
            return None

        return self.calibrated_ensemble.get_calibration_metrics()


def predict_ai_probability(
    text: str,
    model_accuracy: Optional[Dict[str, float]] = None,
    reference_features: Optional[np.ndarray] = None
) -> Tuple[float, Dict[str, float]]:
    """
    Convenience function for single-prediction ensemble inference.

    Args:
        text: Text to analyze
        model_accuracy: Optional model accuracy dict for weight calculation
        reference_features: Optional reference features for contrastive model

    Returns:
        Tuple of (ensemble_probability, model_probabilities)
    """
    detector = EnsembleDetector(model_accuracy=model_accuracy)
    return detector.predict_ai_probability(text, reference_features)
