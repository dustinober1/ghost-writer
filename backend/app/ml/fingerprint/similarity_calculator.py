"""
Fingerprint similarity calculator with confidence intervals.

This module provides similarity comparison between text samples and fingerprints,
including confidence interval calculations to quantify uncertainty in similarity scores.
Confidence intervals help distinguish between statistically significant matches
and random similarities.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
import math

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from app.ml.feature_extraction import FEATURE_NAMES


class FingerprintComparator:
    """
    Compares text features to fingerprints with confidence intervals.

    Provides similarity scores with statistical confidence bounds, enabling
    more reliable authorship verification decisions.

    Similarity thresholds based on authorship verification research:
    - HIGH (>=0.85): Strong match, likely same author
    - MEDIUM (>=0.70): Likely match, requires context
    - LOW (<0.70): Ambiguous, below reliable threshold

    Attributes:
        THRESHOLD_HIGH_SIMILARITY: Threshold for strong match (0.85)
        THRESHOLD_MEDIUM_SIMILARITY: Threshold for likely match (0.70)
        THRESHOLD_LOW_SIMILARITY: Below this indicates ambiguous (0.50)
        confidence_level: Confidence level for interval calculation (default 0.95)
        z_score: Pre-computed z-score for confidence interval
    """

    # Cosine similarity thresholds from authorship verification research
    THRESHOLD_HIGH_SIMILARITY = 0.85  # Strong match
    THRESHOLD_MEDIUM_SIMILARITY = 0.70  # Likely match
    THRESHOLD_LOW_SIMILARITY = 0.50  # Ambiguous/below threshold

    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize the comparator with confidence level.

        Args:
            confidence_level: Confidence level for intervals (0-1, default 0.95)
                             0.95 means 95% confidence that true similarity lies within interval

        Raises:
            ValueError: If confidence_level not in valid range
        """
        if not 0 < confidence_level < 1:
            raise ValueError(
                f"confidence_level must be in (0, 1) range, got {confidence_level}"
            )

        self.confidence_level = confidence_level
        self.z_score = self._calculate_z_score(confidence_level)

    def _calculate_z_score(self, confidence_level: float) -> float:
        """
        Calculate z-score for given confidence level.

        Uses scipy if available, otherwise approximates with pre-computed values.

        Args:
            confidence_level: Confidence level (e.g., 0.95)

        Returns:
            Z-score for the confidence level
        """
        if SCIPY_AVAILABLE:
            # Use scipy.stats.norm.ppf for exact calculation
            # ppf(percentile) gives the value at which CDF equals percentile
            return float(stats.norm.ppf((1 + confidence_level) / 2))
        else:
            # Fallback to pre-computed values for common confidence levels
            z_scores = {
                0.90: 1.645,
                0.95: 1.960,
                0.99: 2.576
            }
            # Find closest match or default to 1.96 (95%)
            closest = min(z_scores.keys(), key=lambda x: abs(x - confidence_level))
            return z_scores.get(closest, 1.960)

    def compare_with_confidence(
        self,
        text_features: np.ndarray,
        fingerprint: Dict,
        fingerprint_stats: Optional[Dict] = None
    ) -> Dict:
        """
        Compare text features to fingerprint with confidence interval.

        Args:
            text_features: Feature vector from extract_feature_vector()
            fingerprint: Fingerprint dictionary with 'feature_vector' key
            fingerprint_stats: Optional dict with 'mean', 'std', 'variance' arrays

        Returns:
            Dictionary with:
                - similarity: Cosine similarity score (0-1)
                - confidence_interval: [lower_bound, upper_bound]
                - match_level: "HIGH" | "MEDIUM" | "LOW"
                - feature_deviations: Top 5 features with largest deviations
                - z_score: Z-score used for CI calculation
        """
        # Extract fingerprint vector
        if isinstance(fingerprint["feature_vector"], list):
            fp_vector = np.array(fingerprint["feature_vector"])
        else:
            fp_vector = fingerprint["feature_vector"]

        # Ensure text_features is numpy array
        if not isinstance(text_features, np.ndarray):
            text_features = np.array(text_features)

        # Calculate cosine similarity
        similarity = self._cosine_similarity(text_features, fp_vector)

        # Calculate confidence interval width
        ci_width = self._calculate_ci_width(
            text_features, fp_vector, fingerprint_stats
        )

        # Compute confidence interval bounds
        lower_bound = max(0.0, similarity - ci_width)
        upper_bound = min(1.0, similarity + ci_width)

        # Classify match level
        match_level = self._classify_match(similarity)

        # Compute feature deviations
        feature_deviations = self._compute_feature_deviations(
            text_features, fp_vector, fingerprint_stats
        )

        return {
            "similarity": float(similarity),
            "confidence_interval": [float(lower_bound), float(upper_bound)],
            "match_level": match_level,
            "feature_deviations": feature_deviations,
            "z_score": self.z_score,
            "confidence_level": self.confidence_level
        }

    def _cosine_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two vectors.

        Uses sklearn if available, otherwise manual calculation.

        Args:
            vec1: First feature vector
            vec2: Second feature vector

        Returns:
            Cosine similarity in range [-1, 1], clamped to [0, 1]
        """
        if SKLEARN_AVAILABLE:
            # sklearn returns shape (1, 1), extract scalar
            result = cosine_similarity(
                vec1.reshape(1, -1),
                vec2.reshape(1, -1)
            )
            return float(result[0, 0])
        else:
            # Manual calculation
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            # Clamp to [0, 1] for similarity (cosine can be negative)
            return float(max(0.0, min(1.0, similarity)))

    def _calculate_ci_width(
        self,
        text_features: np.ndarray,
        fp_vector: np.ndarray,
        stats: Optional[Dict]
    ) -> float:
        """
        Calculate confidence interval width based on feature variance.

        Uses Standard Error of Mean (SEM) for uncertainty estimation:
            SEM = sqrt(mean(variance) / n_features)
            CI_width = z_score * SEM

        Args:
            text_features: Text feature vector
            fp_vector: Fingerprint vector
            stats: Optional dict with variance array

        Returns:
            Confidence interval width (similarity units)
        """
        if stats is None or "variance" not in stats:
            # Default CI width when no statistics available
            return 0.1

        variances = stats["variance"]

        if not variances or len(variances) == 0:
            return 0.1

        # Calculate mean variance across all features
        mean_variance = np.mean(variances)

        # Calculate Standard Error of Mean
        n_features = len(text_features)
        sem = math.sqrt(mean_variance / n_features) if n_features > 0 else 0.1

        # CI width = z_score * SEM
        ci_width = self.z_score * sem

        # Clamp to reasonable range
        return float(max(0.01, min(0.3, ci_width)))

    def _classify_match(self, similarity: float) -> str:
        """
        Classify similarity score into match level categories.

        Args:
            similarity: Cosine similarity score (0-1)

        Returns:
            Match level: "HIGH" | "MEDIUM" | "LOW"
        """
        if similarity >= self.THRESHOLD_HIGH_SIMILARITY:
            return "HIGH"
        elif similarity >= self.THRESHOLD_MEDIUM_SIMILARITY:
            return "MEDIUM"
        else:
            return "LOW"

    def _compute_feature_deviations(
        self,
        text_features: np.ndarray,
        fp_vector: np.ndarray,
        stats: Optional[Dict]
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute feature-wise deviations between text and fingerprint.

        Identifies which stylometric features differ most significantly,
        providing interpretability for similarity scores.

        Args:
            text_features: Text feature vector
            fp_vector: Fingerprint vector
            stats: Optional dict with std for normalization

        Returns:
            Dictionary of top 5 features by normalized deviation:
                {
                    "feature_name": {
                        "text_value": float,
                        "fingerprint_value": float,
                        "deviation": float
                    }
                }
        """
        deviations = {}

        for i, feature_name in enumerate(FEATURE_NAMES):
            if i >= len(text_features) or i >= len(fp_vector):
                break

            text_val = float(text_features[i])
            fp_val = float(fp_vector[i])
            abs_deviation = abs(text_val - fp_val)

            # Normalize by standard deviation if available
            if stats and "std" in stats and i < len(stats["std"]):
                std_val = float(stats["std"][i])
                # Avoid division by zero
                if std_val > 1e-10:
                    normalized_deviation = abs_deviation / std_val
                else:
                    normalized_deviation = abs_deviation
            else:
                normalized_deviation = abs_deviation

            # Only include significantly different features (>2 sigma if std available)
            if normalized_deviation > 2.0 or (stats is None and abs_deviation > 0.1):
                deviations[feature_name] = {
                    "text_value": text_val,
                    "fingerprint_value": fp_val,
                    "deviation": abs_deviation,
                    "normalized_deviation": normalized_deviation
                }

        # Return top 5 by normalized deviation
        sorted_features = sorted(
            deviations.items(),
            key=lambda x: x[1]["normalized_deviation"],
            reverse=True
        )[:5]

        return dict(sorted_features)

    def compare_texts(
        self,
        text1_features: np.ndarray,
        text2_features: np.ndarray
    ) -> float:
        """
        Simple cosine similarity between two text feature vectors.

        Convenience method for direct text-to-text comparison.

        Args:
            text1_features: First text's feature vector
            text2_features: Second text's feature vector

        Returns:
            Cosine similarity score (0-1)
        """
        return self._cosine_similarity(text1_features, text2_features)


def compare_with_confidence(
    text_features: np.ndarray,
    fingerprint: Dict,
    fingerprint_stats: Optional[Dict] = None,
    confidence_level: float = 0.95
) -> Dict:
    """
    Convenience function to compare with confidence intervals.

    Args:
        text_features: Feature vector from extract_feature_vector()
        fingerprint: Fingerprint dictionary with 'feature_vector' key
        fingerprint_stats: Optional dict with variance arrays
        confidence_level: Confidence level for interval (default 0.95)

    Returns:
        Comparison result dictionary with similarity, CI, match_level
    """
    comparator = FingerprintComparator(confidence_level=confidence_level)
    return comparator.compare_with_confidence(text_features, fingerprint, fingerprint_stats)


def classify_match(similarity: float) -> str:
    """
    Classify similarity score into match level without full comparator.

    Args:
        similarity: Cosine similarity score (0-1)

    Returns:
        Match level: "HIGH" | "MEDIUM" | "LOW"
    """
    if similarity >= FingerprintComparator.THRESHOLD_HIGH_SIMILARITY:
        return "HIGH"
    elif similarity >= FingerprintComparator.THRESHOLD_MEDIUM_SIMILARITY:
        return "MEDIUM"
    else:
        return "LOW"


# Export constants for direct access
__all__ = [
    "FingerprintComparator",
    "compare_with_confidence",
    "classify_match",
    "THRESHOLD_HIGH_SIMILARITY",
    "THRESHOLD_MEDIUM_SIMILARITY",
    "THRESHOLD_LOW_SIMILARITY"
]

# Module-level constants for convenience
THRESHOLD_HIGH_SIMILARITY = FingerprintComparator.THRESHOLD_HIGH_SIMILARITY
THRESHOLD_MEDIUM_SIMILARITY = FingerprintComparator.THRESHOLD_MEDIUM_SIMILARITY
THRESHOLD_LOW_SIMILARITY = FingerprintComparator.THRESHOLD_LOW_SIMILARITY
