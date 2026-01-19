"""
Time-weighted fingerprint training using Exponential Moving Average (EMA).

Writing style evolves over time. This module implements EMA-based fingerprint
building that gives higher weight to recent writing samples while maintaining
historical patterns. This approach allows fingerprints to adapt to style evolution
while maintaining stability through the smoothing factor.
"""
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math

from app.ml.feature_extraction import extract_feature_vector, FEATURE_NAMES


class TimeWeightedFingerprintBuilder:
    """
    Builds time-weighted fingerprints using Exponential Moving Average.

    EMA gives higher weight to recent samples while maintaining historical patterns.
    The alpha parameter controls recency sensitivity:
    - Higher alpha (e.g., 0.5) = more responsive to recent changes
    - Lower alpha (e.g., 0.1) = more stable, slower to adapt

    Default alpha=0.3 provides balanced recency tracking based on stylometric
    analysis research.

    Attributes:
        MIN_SAMPLES_FOR_FINGERPRINT: Minimum samples required for valid fingerprint
        alpha: EMA smoothing factor (0-1)
    """

    MIN_SAMPLES_FOR_FINGERPRINT = 10

    def __init__(self, alpha: float = 0.3):
        """
        Initialize the time-weighted fingerprint builder.

        Args:
            alpha: EMA smoothing factor (0-1). Higher = more weight to recent samples.
                   0.3 is standard for balanced recency in time-series analysis.
                   - alpha=1.0: Only latest sample matters (no smoothing)
                   - alpha=0.1: Very slow adaptation (high stability)
                   - alpha=0.3: Balanced (recommended for writing style)

        Raises:
            ValueError: If alpha not in valid range (0, 1]
        """
        if not 0 < alpha <= 1:
            raise ValueError(f"alpha must be in (0, 1] range, got {alpha}")

        self.alpha = alpha
        self.fingerprint_vector: Optional[np.ndarray] = None
        self.sample_count = 0
        self.feature_stats: Dict[int, Dict[str, float]] = {}
        # Track timestamps for recency calculations
        self.timestamps: List[datetime] = []

    def add_sample(
        self,
        features: np.ndarray,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Add a writing sample to the fingerprint.

        Applies EMA update rule:
            new_ema = (1 - alpha) * old_ema + alpha * new_sample

        Also tracks per-feature statistics using Welford's online algorithm
        for numerically stable variance calculation (needed for confidence intervals).

        Args:
            features: Feature vector from extract_feature_vector()
            timestamp: When the text was written (defaults to now)

        Raises:
            ValueError: If features is empty or wrong shape
        """
        if features is None or len(features) == 0:
            raise ValueError("Features cannot be empty")

        # Convert to numpy array if needed
        if not isinstance(features, np.ndarray):
            features = np.array(features)

        # Track timestamp
        if timestamp is None:
            timestamp = datetime.utcnow()
        self.timestamps.append(timestamp)

        # First sample: initialize directly
        if self.fingerprint_vector is None:
            self.fingerprint_vector = features.copy()
            self.sample_count = 1
            # Initialize stats with first sample
            for i, val in enumerate(features):
                self.feature_stats[i] = {
                    "mean": float(val),
                    "variance": 0.0,
                    "count": 1
                }
            return

        # Apply EMA update: new_ema = (1 - alpha) * old_ema + alpha * new
        self.fingerprint_vector = (
            (1 - self.alpha) * self.fingerprint_vector +
            self.alpha * features
        )
        self.sample_count += 1

        # Update feature statistics using Welford's algorithm
        self._update_stats(features)

    def _update_stats(self, features: np.ndarray) -> None:
        """
        Update running statistics using Welford's online algorithm.

        Welford's algorithm provides numerically stable variance calculation
        by updating mean and variance incrementally. This avoids catastrophic
        cancellation that can occur with naive two-pass algorithms.

        For each feature i:
            count_n = count_{n-1} + 1
            delta = new_value - mean_{n-1}
            mean_n = mean_{n-1} + delta / count_n
            delta2 = new_value - mean_n
            M2_n = M2_{n-1} + delta * delta2
            variance_n = M2_n / count_n

        Args:
            features: New feature vector to incorporate into statistics
        """
        n = self.sample_count

        for i, val in enumerate(features):
            if i not in self.feature_stats:
                # Initialize with this value
                self.feature_stats[i] = {
                    "mean": float(val),
                    "variance": 0.0,
                    "count": 1
                }
            else:
                stats = self.feature_stats[i]
                stats["count"] += 1

                # Welford's algorithm for variance
                delta = val - stats["mean"]
                stats["mean"] += delta / stats["count"]
                delta2 = val - stats["mean"]

                # M2 (sum of squared differences from mean)
                if "m2" not in stats:
                    stats["m2"] = 0.0
                stats["m2"] += delta * delta2

                # Variance = M2 / count
                stats["variance"] = stats["m2"] / stats["count"]

    def compute_recency_weights(
        self,
        timestamps: List[datetime],
        current_time: Optional[datetime] = None
    ) -> np.ndarray:
        """
        Compute exponential recency weights for a list of timestamps.

        More recent timestamps receive higher weight based on exponential decay:
            weight = e^(-lambda * age)

        Lambda is derived from alpha for consistency with EMA:
            lambda = -ln(alpha)

        This formula ensures that:
        - At age=0, weight=1 (current time)
        - At age such that lambda*age=1, weight=e^-1 ~ 0.37
        - Weights sum to 1 after normalization

        Args:
            timestamps: List of sample timestamps (ascending or descending)
            current_time: Reference time for age calculation (defaults to now)

        Returns:
            NumPy array of normalized weights summing to 1.0
        """
        if not timestamps:
            return np.array([])

        if current_time is None:
            current_time = datetime.utcnow()

        # Calculate lambda from alpha
        # alpha = e^(-lambda) for unit time step, so lambda = -ln(alpha)
        lambda_param = -math.log(self.alpha)

        # Calculate age in days for each timestamp
        ages = np.array([
            (current_time - ts).total_seconds() / 86400.0  # Convert to days
            for ts in timestamps
        ])

        # Calculate exponential decay weights
        weights = np.exp(-lambda_param * ages)

        # Normalize to sum to 1.0
        total = np.sum(weights)
        if total > 0:
            weights = weights / total

        return weights

    def get_fingerprint(self) -> Dict:
        """
        Get the current fingerprint as a serializable dictionary.

        Returns:
            Dictionary containing:
                - feature_vector: List of float values (27 features)
                - sample_count: Number of samples incorporated
                - model_version: Fingerprint format version
                - method: Fingerprinting method identifier
                - alpha: EMA smoothing parameter used
                - feature_statistics: Per-feature mean/std/variance for confidence intervals
                - date_range: Oldest and newest sample timestamps

        Raises:
            ValueError: If insufficient samples for valid fingerprint
        """
        if self.fingerprint_vector is None or self.sample_count < self.MIN_SAMPLES_FOR_FINGERPRINT:
            raise ValueError(
                f"Need at least {self.MIN_SAMPLES_FOR_FINGERPRINT} samples "
                f"to build fingerprint (have {self.sample_count})"
            )

        date_range = None
        if self.timestamps:
            date_range = {
                "earliest": min(self.timestamps).isoformat(),
                "latest": max(self.timestamps).isoformat()
            }

        return {
            "feature_vector": self.fingerprint_vector.tolist(),
            "sample_count": self.sample_count,
            "model_version": "2.0",
            "method": "time_weighted_ema",
            "alpha": self.alpha,
            "feature_statistics": self._get_feature_stats_summary(),
            "date_range": date_range
        }

    def _get_feature_stats_summary(self) -> Dict[str, List[float]]:
        """
        Convert feature_stats to serializable format with FEATURE_NAMES mapping.

        Returns:
            Dictionary with keys: mean, std, variance
            Each key maps to a list of 27 values (one per feature)
        """
        n_features = len(FEATURE_NAMES)

        # Initialize arrays
        means = np.zeros(n_features)
        variances = np.zeros(n_features)

        # Fill in tracked statistics
        for idx, stats in self.feature_stats.items():
            if idx < n_features:
                means[idx] = stats["mean"]
                variances[idx] = stats["variance"]

        # Calculate std from variance (add small epsilon to avoid sqrt(0))
        epsilon = 1e-10
        stds = np.sqrt(np.maximum(variances, epsilon))

        return {
            "mean": means.tolist(),
            "std": stds.tolist(),
            "variance": variances.tolist()
        }

    def reset(self) -> None:
        """
        Reset the fingerprint builder to initial state.

        Clears all accumulated data and allows starting fresh.
        """
        self.fingerprint_vector = None
        self.sample_count = 0
        self.feature_stats = {}
        self.timestamps = []

    def is_ready(self) -> bool:
        """
        Check if enough samples have been added for a valid fingerprint.

        Returns:
            True if sample_count >= MIN_SAMPLES_FOR_FINGERPRINT
        """
        return self.sample_count >= self.MIN_SAMPLES_FOR_FINGERPRINT

    def samples_needed(self) -> int:
        """
        Get number of additional samples needed for valid fingerprint.

        Returns:
            Number of samples still required (0 if ready)
        """
        return max(0, self.MIN_SAMPLES_FOR_FINGERPRINT - self.sample_count)


def add_sample(
    builder: TimeWeightedFingerprintBuilder,
    text: str,
    timestamp: Optional[datetime] = None
) -> Dict:
    """
    Convenience function to extract features and add to builder.

    Args:
        builder: TimeWeightedFingerprintBuilder instance
        text: Text content to analyze
        timestamp: When text was written (defaults to now)

    Returns:
        Dictionary with extracted features
    """
    features = extract_feature_vector(text)
    builder.add_sample(features, timestamp)
    return {
        "feature_count": len(features),
        "timestamp": timestamp or datetime.utcnow()
    }


def get_fingerprint(
    builder: TimeWeightedFingerprintBuilder
) -> Dict:
    """
    Convenience function to get fingerprint from builder.

    Args:
        builder: TimeWeightedFingerprintBuilder instance

    Returns:
        Fingerprint dictionary
    """
    return builder.get_fingerprint()


def compute_recency_weights(
    timestamps: List[datetime],
    alpha: float = 0.3,
    current_time: Optional[datetime] = None
) -> np.ndarray:
    """
    Convenience function to compute recency weights without a builder instance.

    Args:
        timestamps: List of sample timestamps
        alpha: EMA smoothing parameter
        current_time: Reference time for age calculation

    Returns:
        NumPy array of normalized weights
    """
    builder = TimeWeightedFingerprintBuilder(alpha=alpha)
    return builder.compute_recency_weights(timestamps, current_time)
