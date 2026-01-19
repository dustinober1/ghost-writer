"""
Enhanced fingerprinting modules for corpus-based, time-weighted fingerprint generation.

This package provides multiple approaches to building and comparing writing fingerprints:

1. **FingerprintCorpusBuilder** - Multi-sample aggregation with time-weighted,
   source-weighted, and simple averaging methods. Requires MIN_SAMPLES_FOR_FINGERPRINT=10
   samples to build a statistically robust fingerprint.

2. **TimeWeightedFingerprintBuilder** - Real-time EMA-based fingerprint building
   that incrementally updates as new samples arrive. Suitable for streaming scenarios.

3. **FingerprintComparator** - Similarity comparison with confidence intervals
   for statistically reliable authorship verification decisions.

Usage:
    ```python
    from app.ml.fingerprint import (
        FingerprintCorpusBuilder,
        TimeWeightedFingerprintBuilder,
        FingerprintComparator
    )

    # Corpus-based approach (batch)
    corpus = FingerprintCorpusBuilder()
    corpus.add_sample(text1, source_type="essay")
    corpus.add_sample(text2, source_type="academic")
    # ... add 10+ samples
    fingerprint = corpus.build_fingerprint(method="time_weighted")

    # Time-weighted approach (streaming)
    builder = TimeWeightedFingerprintBuilder(alpha=0.3)
    builder.add_sample(features1)
    builder.add_sample(features2)
    # ... add 10+ samples
    fingerprint = builder.get_fingerprint()

    # Comparison with confidence
    comparator = FingerprintComparator(confidence_level=0.95)
    result = comparator.compare_with_confidence(
        text_features,
        fingerprint,
        fingerprint_stats
    )
    print(f"Similarity: {result['similarity']} ± {result['confidence_interval']}")
    ```
"""

# Enhanced fingerprinting modules
from .corpus_builder import (
    FingerprintCorpusBuilder,
    add_sample as corpus_add_sample,
    build_fingerprint as corpus_build_fingerprint
)
from .time_weighted_trainer import (
    TimeWeightedFingerprintBuilder,
    add_sample as weighted_add_sample,
    get_fingerprint as weighted_get_fingerprint,
    compute_recency_weights
)
from .similarity_calculator import (
    FingerprintComparator,
    compare_with_confidence,
    classify_match,
    THRESHOLD_HIGH_SIMILARITY,
    THRESHOLD_MEDIUM_SIMILARITY,
    THRESHOLD_LOW_SIMILARITY
)

# Legacy functions (for backward compatibility with app.ml.fingerprint)
from ..fingerprint import (
    generate_fingerprint,
    update_fingerprint,
    compare_to_fingerprint
)

__all__ = [
    # Enhanced API
    "FingerprintCorpusBuilder",
    "TimeWeightedFingerprintBuilder",
    "FingerprintComparator",
    "compare_with_confidence",
    "classify_match",
    "compute_recency_weights",
    # Threshold constants
    "THRESHOLD_HIGH_SIMILARITY",
    "THRESHOLD_MEDIUM_SIMILARITY",
    "THRESHOLD_LOW_SIMILARITY",
    # Legacy API
    "generate_fingerprint",
    "update_fingerprint",
    "compare_to_fingerprint",
]

# Module-level constants for easy access
MIN_SAMPLES_FOR_FINGERPRINT = 10  # Minimum samples for valid fingerprint
DEFAULT_ALPHA = 0.3  # Default EMA smoothing parameter
DEFAULT_CONFIDENCE_LEVEL = 0.95  # Default confidence for intervals
