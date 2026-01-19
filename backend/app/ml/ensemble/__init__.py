"""
Multi-model ensemble for AI text detection.

Combines predictions from stylometric, perplexity, and contrastive models
using weighted soft voting for improved accuracy.
"""

from .ensemble_detector import EnsembleDetector
from .base_detectors import (
    StylometricDetector,
    PerplexityDetector,
    ContrastiveDetectorWrapper,
)
from .weights import calculate_weights_from_accuracy, default_model_weights

__all__ = [
    "EnsembleDetector",
    "StylometricDetector",
    "PerplexityDetector",
    "ContrastiveDetectorWrapper",
    "calculate_weights_from_accuracy",
    "default_model_weights",
]
