"""
Style drift detection using statistical process control.

This module provides z-score based drift detection to identify significant
changes in writing style that may indicate AI assistance or other influences.

Drift thresholds based on statistical process control:
- WARNING: >=2.0 standard deviations from baseline (95% confidence)
- ALERT: >=3.0 standard deviations from baseline (99.7% confidence)
"""
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from collections import deque


class StyleDriftDetector:
    """
    Detects writing style drift using z-score based statistical process control.

    Tracks similarity scores over time and identifies significant deviations
    from established baselines. Uses sliding window analysis to accommodate
    gradual style evolution while flagging sudden changes.

    Attributes:
        window_size: Number of recent samples to maintain for analysis
        drift_threshold: Standard deviations for "warning" level (default 2.0)
        alert_threshold: Standard deviations for "alert" level (default 3.0)
        similarity_window: Sliding window of recent similarity scores
        baseline_mean: Mean of baseline similarities
        baseline_std: Standard deviation of baseline similarities
        baseline_established: Whether baseline has been established
    """

    # Default thresholds
    DEFAULT_WINDOW_SIZE = 10  # Number of samples in sliding window
    DEFAULT_DRIFT_THRESHOLD = 2.0  # Warning level (2 sigma)
    DEFAULT_ALERT_THRESHOLD = 3.0  # Alert level (3 sigma)

    def __init__(
        self,
        window_size: int = DEFAULT_WINDOW_SIZE,
        drift_threshold: float = DEFAULT_DRIFT_THRESHOLD,
        alert_threshold: float = DEFAULT_ALERT_THRESHOLD
    ):
        """
        Initialize the drift detector.

        Args:
            window_size: Number of recent samples to analyze
            drift_threshold: Standard deviations for "warning" level (default 2.0)
            alert_threshold: Standard deviations for "alert" level (default 3.0)
        """
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        self.alert_threshold = alert_threshold
        self.similarity_window = deque(maxlen=window_size)
        self.baseline_mean = None
        self.baseline_std = None
        self.baseline_established = False

    def establish_baseline(self, similarities: List[float]) -> None:
        """
        Establish baseline statistics from initial similarity scores.

        Should be called with a representative sample of the user's
        typical similarity scores (e.g., 10+ samples).

        Args:
            similarities: List of similarity scores to establish baseline

        Raises:
            ValueError: If similarities list is empty
        """
        if not similarities or len(similarities) == 0:
            raise ValueError("Cannot establish baseline from empty similarities list")

        similarities_array = np.array(similarities)
        self.baseline_mean = float(np.mean(similarities_array))
        self.baseline_std = float(np.std(similarities_array))

        # Initialize window with baseline data
        self.similarity_window.clear()
        for s in similarities[-self.window_size:]:
            self.similarity_window.append(s)

        self.baseline_established = True

    def check_drift(
        self,
        similarity: float,
        feature_deviations: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ) -> Dict:
        """
        Check if current similarity indicates drift from baseline.

        Calculates z-score (standard deviations from mean) to determine
        if the current similarity represents a statistically significant
        deviation from established baseline.

        Args:
            similarity: Current similarity score to check
            feature_deviations: Optional dict of feature deviations from comparison
            timestamp: Optional timestamp of the check (for logging)

        Returns:
            Dictionary with drift detection results:
                - drift_detected: bool - Whether drift was detected
                - severity: str - "warning", "alert", or "none"
                - similarity: float - The similarity score checked
                - baseline_mean: float - Current baseline mean
                - z_score: float - Statistical distance from baseline
                - confidence_interval: [lower, upper] - Acceptable range
                - changed_features: List[Dict] - Features that changed most
                - timestamp: datetime - When check was performed
        """
        # If baseline not established, cannot detect drift
        if not self.baseline_established:
            return {
                "drift_detected": False,
                "severity": "none",
                "similarity": similarity,
                "baseline_mean": 0.0,
                "z_score": 0.0,
                "confidence_interval": [0.0, 1.0],
                "changed_features": [],
                "timestamp": timestamp or datetime.utcnow(),
                "reason": "baseline_not_established"
            }

        # Add current similarity to sliding window
        self.similarity_window.append(similarity)

        # Calculate z-score: (baseline_mean - similarity) / baseline_std
        # Negative z_score means text is MORE similar than baseline (unusual)
        # Positive z_score means text is LESS similar than baseline (potential drift)
        if self.baseline_std > 0:
            z_score = (self.baseline_mean - similarity) / self.baseline_std
        else:
            # No variance in baseline, cannot calculate meaningful z-score
            z_score = 0.0

        # Determine severity based on absolute z-score
        abs_z_score = abs(z_score)

        if abs_z_score >= self.alert_threshold:
            severity = "alert"
            drift_detected = True
        elif abs_z_score >= self.drift_threshold:
            severity = "warning"
            drift_detected = True
        else:
            severity = "none"
            drift_detected = False

        # Calculate confidence interval for baseline
        # [mean - threshold*std, mean + threshold*std]
        ci_lower = max(0.0, self.baseline_mean - self.drift_threshold * self.baseline_std)
        ci_upper = min(1.0, self.baseline_mean + self.drift_threshold * self.baseline_std)

        # Analyze feature changes if provided
        changed_features = self._analyze_feature_changes(feature_deviations)

        return {
            "drift_detected": drift_detected,
            "severity": severity,
            "similarity": similarity,
            "baseline_mean": self.baseline_mean,
            "z_score": z_score,
            "confidence_interval": [ci_lower, ci_upper],
            "changed_features": changed_features,
            "timestamp": timestamp or datetime.utcnow()
        }

    def _analyze_feature_changes(
        self,
        feature_deviations: Optional[Dict]
    ) -> List[Dict]:
        """
        Analyze feature deviations to identify most changed features.

        Args:
            feature_deviations: Dict from FingerprintComparator.compare_with_confidence()
                with format {"feature_name": {"text_value", "fingerprint_value", "deviation", ...}}

        Returns:
            List of feature changes sorted by normalized_deviation DESC:
                [
                    {
                        "feature": str,
                        "current_value": float,
                        "baseline_value": float,
                        "normalized_deviation": float
                    }
                ]
        """
        if not feature_deviations:
            return []

        changes = []
        for feature_name, deviation_info in feature_deviations.items():
            changes.append({
                "feature": feature_name,
                "current_value": deviation_info.get("text_value", 0.0),
                "baseline_value": deviation_info.get("fingerprint_value", 0.0),
                "normalized_deviation": deviation_info.get("normalized_deviation", 0.0)
            })

        # Sort by normalized deviation (highest first)
        changes.sort(key=lambda x: x["normalized_deviation"], reverse=True)
        return changes

    def update_baseline(self, new_similarities: List[float]) -> None:
        """
        Update baseline with new similarity scores.

        Used when user acknowledges drift as legitimate style change,
        effectively establishing a new baseline for future comparisons.

        Args:
            new_similarities: New similarity scores to incorporate into baseline
        """
        if not new_similarities:
            return

        # Combine current window with new similarities
        combined = list(self.similarity_window) + new_similarities

        # Recalculate baseline statistics
        combined_array = np.array(combined)
        self.baseline_mean = float(np.mean(combined_array))
        self.baseline_std = float(np.std(combined_array))

        # Update window with most recent samples
        self.similarity_window.clear()
        for s in combined[-self.window_size:]:
            self.similarity_window.append(s)

    def get_status(self) -> Dict:
        """
        Get current detector status.

        Returns:
            Dictionary with current state:
                - baseline_established: bool
                - baseline_mean: float or None
                - baseline_std: float or None
                - window_size: int
                - current_window_size: int
                - thresholds: dict with drift and alert values
        """
        return {
            "baseline_established": self.baseline_established,
            "baseline_mean": self.baseline_mean,
            "baseline_std": self.baseline_std,
            "window_size": self.window_size,
            "current_window_size": len(self.similarity_window),
            "thresholds": {
                "drift": self.drift_threshold,
                "alert": self.alert_threshold
            }
        }

    def reset(self) -> None:
        """Reset detector to initial state (baseline cleared)."""
        self.similarity_window.clear()
        self.baseline_mean = None
        self.baseline_std = None
        self.baseline_established = False


def establish_baseline(similarities: List[float], window_size: int = 10) -> StyleDriftDetector:
    """
    Convenience function to create detector and establish baseline.

    Args:
        similarities: List of similarity scores for baseline
        window_size: Size of sliding window for tracking

    Returns:
        Configured StyleDriftDetector with established baseline
    """
    detector = StyleDriftDetector(window_size=window_size)
    detector.establish_baseline(similarities)
    return detector


def check_drift(
    similarities: List[float],
    current_similarity: float,
    feature_deviations: Optional[Dict] = None,
    drift_threshold: float = 2.0,
    alert_threshold: float = 3.0
) -> Dict:
    """
    Convenience function for one-time drift check.

    Creates detector, establishes baseline, checks for drift.

    Args:
        similarities: Baseline similarity scores
        current_similarity: Current similarity to check
        feature_deviations: Optional feature deviation info
        drift_threshold: Warning threshold (default 2.0)
        alert_threshold: Alert threshold (default 3.0)

    Returns:
        Drift detection result dictionary
    """
    detector = StyleDriftDetector(
        drift_threshold=drift_threshold,
        alert_threshold=alert_threshold
    )
    detector.establish_baseline(similarities)
    return detector.check_drift(current_similarity, feature_deviations)


# Export constants and functions
__all__ = [
    "StyleDriftDetector",
    "establish_baseline",
    "check_drift",
    "update_baseline"
]
