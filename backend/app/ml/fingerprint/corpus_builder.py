"""
Fingerprint Corpus Builder for multi-sample aggregation.

This module provides time-weighted and source-weighted aggregation
of writing samples to create statistically robust fingerprints.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from app.ml.feature_extraction import extract_feature_vector, FEATURE_NAMES


class FingerprintCorpusBuilder:
    """
    Builds enhanced fingerprints from a corpus of writing samples.

    Supports multiple aggregation methods:
    - time_weighted: Exponential moving average based on timestamp
    - average: Simple mean of all samples
    - source_weighted: Weighted average by source type (essay, academic, etc.)
    """

    MIN_SAMPLES_FOR_FINGERPRINT = 10

    def __init__(self, min_samples: int = 10):
        """
        Initialize the corpus builder.

        Args:
            min_samples: Minimum samples required to build a fingerprint
        """
        self.min_samples = min_samples
        self.samples: List[Dict] = []

    def add_sample(
        self,
        text: str,
        source_type: str = "manual",
        timestamp: Optional[datetime] = None
    ) -> Dict:
        """
        Add a writing sample to the corpus.

        Args:
            text: Text content to add (must not be empty)
            source_type: Type of writing sample
            timestamp: When text was written (defaults to now)

        Returns:
            Dictionary with sample metadata (features, word_count, etc.)

        Raises:
            ValueError: If text is empty or whitespace only
        """
        if not text or not text.strip():
            raise ValueError("Text content cannot be empty")

        # Extract features
        features = extract_feature_vector(text)

        # Store sample with metadata
        sample = {
            "features": features,
            "timestamp": timestamp or datetime.utcnow(),
            "source_type": source_type,
            "word_count": len(text.split()),
            "raw_features": extract_all_features_raw(text)
        }

        self.samples.append(sample)
        return {
            "word_count": sample["word_count"],
            "source_type": source_type,
            "timestamp": sample["timestamp"]
        }

    def build_fingerprint(
        self,
        method: str = "time_weighted",
        alpha: float = 0.3
    ) -> Dict:
        """
        Build an enhanced fingerprint from the corpus.

        Args:
            method: Aggregation method ('time_weighted', 'average', 'source_weighted')
            alpha: EMA smoothing parameter for time_weighted method

        Returns:
            Dictionary with feature_vector, sample_count, method, feature_statistics

        Raises:
            ValueError: If insufficient samples (< MIN_SAMPLES_FOR_FINGERPRINT)
        """
        if len(self.samples) < self.MIN_SAMPLES_FOR_FINGERPRINT:
            raise ValueError(
                f"Need at least {self.MIN_SAMPLES_FOR_FINGERPRINT} samples "
                f"to build fingerprint (have {len(self.samples)})"
            )

        # Sort samples by timestamp for time-weighted methods
        sorted_samples = sorted(self.samples, key=lambda s: s["timestamp"])

        if method == "time_weighted":
            result = self._build_time_weighted(sorted_samples, alpha)
        elif method == "average":
            result = self._build_average(sorted_samples)
        elif method == "source_weighted":
            result = self._build_source_weighted(sorted_samples)
        else:
            raise ValueError(
                f"Unknown method: {method}. "
                f"Use 'time_weighted', 'average', or 'source_weighted'"
            )

        return result

    def get_corpus_summary(self) -> Dict:
        """
        Get summary statistics for the corpus.

        Returns:
            Dictionary with sample_count, total_words, source_distribution,
            ready_for_fingerprint, oldest_sample, newest_sample
        """
        if not self.samples:
            return {
                "sample_count": 0,
                "total_words": 0,
                "source_distribution": {},
                "ready_for_fingerprint": False,
                "samples_needed": self.MIN_SAMPLES_FOR_FINGERPRINT,
                "oldest_sample": None,
                "newest_sample": None
            }

        timestamps = [s["timestamp"] for s in self.samples]
        source_counts: Dict[str, int] = {}
        total_words = sum(s["word_count"] for s in self.samples)

        for sample in self.samples:
            source = sample["source_type"]
            source_counts[source] = source_counts.get(source, 0) + 1

        samples_needed = max(0, self.MIN_SAMPLES_FOR_FINGERPRINT - len(self.samples))

        return {
            "sample_count": len(self.samples),
            "total_words": total_words,
            "source_distribution": source_counts,
            "ready_for_fingerprint": len(self.samples) >= self.MIN_SAMPLES_FOR_FINGERPRINT,
            "samples_needed": samples_needed,
            "oldest_sample": min(timestamps),
            "newest_sample": max(timestamps)
        }

    def _build_time_weighted(
        self,
        sorted_samples: List[Dict],
        alpha: float
    ) -> Dict:
        """
        Build fingerprint using exponential moving average (time-weighted).

        More recent samples have higher weight. Uses Welford's online
        algorithm to track feature statistics for confidence intervals.

        Args:
            sorted_samples: Samples sorted by timestamp (ascending)
            alpha: EMA smoothing parameter (0 < alpha <= 1)

        Returns:
            Fingerprint dictionary with feature_vector and statistics
        """
        if not sorted_samples:
            raise ValueError("No samples available")

        # Initialize with first sample
        current_ema = sorted_samples[0]["features"].copy()

        # Initialize Welford's algorithm for statistics
        n = len(current_ema)
        mean = current_ema.copy()
        m2 = np.zeros(n)  # Sum of squares of differences

        # Process remaining samples with EMA
        for i, sample in enumerate(sorted_samples[1:], start=2):
            new_features = sample["features"]

            # Update EMA: new_ema = (1 - alpha) * old_ema + alpha * new
            current_ema = (1 - alpha) * current_ema + alpha * new_features

            # Update running statistics using Welford's algorithm
            delta = new_features - mean
            mean += delta / i
            delta2 = new_features - mean
            m2 += delta * delta2

        # Calculate variance and std
        variance = m2 / len(sorted_samples)
        std = np.sqrt(variance)

        # Build source distribution
        source_distribution = self._get_source_distribution(sorted_samples)

        # Get date range
        timestamps = [s["timestamp"] for s in sorted_samples]
        date_range = {
            "earliest": min(timestamps).isoformat(),
            "latest": max(timestamps).isoformat()
        }

        return {
            "feature_vector": current_ema.tolist(),
            "sample_count": len(sorted_samples),
            "method": "time_weighted",
            "alpha": alpha,
            "feature_statistics": {
                "mean": mean.tolist(),
                "std": std.tolist(),
                "variance": variance.tolist()
            },
            "source_distribution": source_distribution,
            "date_range": date_range,
            "average_word_count": sum(s["word_count"] for s in sorted_samples) / len(sorted_samples)
        }

    def _build_average(self, samples: List[Dict]) -> Dict:
        """
        Build fingerprint using simple average of all samples.

        Args:
            samples: List of sample dictionaries

        Returns:
            Fingerprint dictionary with feature_vector and statistics
        """
        # Stack all feature vectors
        features_matrix = np.array([s["features"] for s in samples])

        # Calculate mean
        mean_vector = np.mean(features_matrix, axis=0)

        # Calculate statistics
        std_vector = np.std(features_matrix, axis=0)
        variance_vector = np.var(features_matrix, axis=0)

        source_distribution = self._get_source_distribution(samples)

        timestamps = [s["timestamp"] for s in samples]

        return {
            "feature_vector": mean_vector.tolist(),
            "sample_count": len(samples),
            "method": "average",
            "alpha": 1.0,
            "feature_statistics": {
                "mean": mean_vector.tolist(),
                "std": std_vector.tolist(),
                "variance": variance_vector.tolist()
            },
            "source_distribution": source_distribution,
            "date_range": {
                "earliest": min(timestamps).isoformat(),
                "latest": max(timestamps).isoformat()
            },
            "average_word_count": sum(s["word_count"] for s in samples) / len(samples)
        }

    def _build_source_weighted(self, samples: List[Dict]) -> Dict:
        """
        Build fingerprint using source-type weighted average.

        Different source types receive different weights:
        - academic: 1.3 (most formal, represents true writing style)
        - essay: 1.2 (structured, representative)
        - document: 1.1 (professional)
        - blog: 1.0 (baseline)
        - manual: 1.0 (baseline, direct input)
        - email: 0.9 (informal, less representative)

        Args:
            samples: List of sample dictionaries

        Returns:
            Fingerprint dictionary with feature_vector and statistics
        """
        source_weights = {
            "essay": 1.2,
            "academic": 1.3,
            "blog": 1.0,
            "email": 0.9,
            "document": 1.1,
            "manual": 1.0
        }

        # Calculate weighted sum and total weight
        weighted_sum = None
        total_weight = 0.0

        for sample in samples:
            weight = source_weights.get(sample["source_type"], 1.0)
            features = sample["features"]

            if weighted_sum is None:
                weighted_sum = weight * features
            else:
                weighted_sum += weight * features

            total_weight += weight

        # Normalize by total weight
        if total_weight > 0:
            feature_vector = weighted_sum / total_weight
        else:
            feature_vector = np.mean([s["features"] for s in samples], axis=0)

        # Calculate statistics (unweighted for consistency)
        features_matrix = np.array([s["features"] for s in samples])
        mean_vector = np.mean(features_matrix, axis=0)
        std_vector = np.std(features_matrix, axis=0)
        variance_vector = np.var(features_matrix, axis=0)

        source_distribution = self._get_source_distribution(samples)

        timestamps = [s["timestamp"] for s in samples]

        return {
            "feature_vector": feature_vector.tolist(),
            "sample_count": len(samples),
            "method": "source_weighted",
            "alpha": 1.0,
            "feature_statistics": {
                "mean": mean_vector.tolist(),
                "std": std_vector.tolist(),
                "variance": variance_vector.tolist()
            },
            "source_distribution": source_distribution,
            "date_range": {
                "earliest": min(timestamps).isoformat(),
                "latest": max(timestamps).isoformat()
            },
            "average_word_count": sum(s["word_count"] for s in samples) / len(samples)
        }

    def _get_source_distribution(self, samples: List[Dict]) -> Dict[str, int]:
        """Get count of samples by source type."""
        distribution: Dict[str, int] = {}
        for sample in samples:
            source = sample["source_type"]
            distribution[source] = distribution.get(source, 0) + 1
        return distribution


def extract_all_features_raw(text: str) -> Dict[str, float]:
    """
    Extract raw (non-normalized) features for a text.

    This is a lightweight version that doesn't normalize the features,
    useful for storing raw feature values.

    Args:
        text: Input text

    Returns:
        Dictionary of feature names to values
    """
    from app.ml.feature_extraction import extract_all_features
    return extract_all_features(text)


def add_sample(
    builder: FingerprintCorpusBuilder,
    text: str,
    source_type: str = "manual",
    timestamp: Optional[datetime] = None
) -> Dict:
    """
    Convenience function to add a sample to a corpus builder.

    Args:
        builder: FingerprintCorpusBuilder instance
        text: Text content
        source_type: Type of writing sample
        timestamp: When text was written

    Returns:
        Sample metadata dictionary
    """
    return builder.add_sample(text, source_type, timestamp)


def build_fingerprint(
    builder: FingerprintCorpusBuilder,
    method: str = "time_weighted",
    alpha: float = 0.3
) -> Dict:
    """
    Convenience function to build a fingerprint from a corpus builder.

    Args:
        builder: FingerprintCorpusBuilder instance
        method: Aggregation method
        alpha: EMA smoothing parameter

    Returns:
        Fingerprint dictionary
    """
    return builder.build_fingerprint(method, alpha)
