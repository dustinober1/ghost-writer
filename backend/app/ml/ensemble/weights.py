"""
Weight calculation for ensemble model voting.

Calculates normalized weights based on individual model accuracy/performance.
Models with higher accuracy receive higher weight in the ensemble voting.
"""

from typing import Dict, List, Optional


def calculate_weights_from_accuracy(
    model_accuracies: Dict[str, float]
) -> List[float]:
    """
    Calculate normalized ensemble weights from model accuracy scores.

    Weights are proportional to accuracy values and normalized to sum to 1.0.

    Args:
        model_accuracies: Dict mapping model names to accuracy scores.
            Expected keys: 'stylometric', 'perplexity', 'contrastive'
            Values should be in [0, 1] range (accuracy scores).

    Returns:
        List of weights [stylometric, perplexity, contrastive] normalized to sum to 1.0

    Example:
        >>> accs = {'stylometric': 0.85, 'perplexity': 0.75, 'contrastive': 0.80}
        >>> calculate_weights_from_accuracy(accs)
        [0.361, 0.319, 0.340]
    """
    # Define model order for consistent output
    model_order = ['stylometric', 'perplexity', 'contrastive']

    # Start with default weights
    weights = default_model_weights()

    # Update weights based on provided accuracies
    if model_accuracies:
        accuracy_values = []
        for model_name in model_order:
            acc = model_accuracies.get(model_name)
            if acc is not None and 0 < acc <= 1:
                accuracy_values.append(acc)
            else:
                # Use default weight component if accuracy not provided
                accuracy_values.append(default_model_weights()[model_order.index(model_name)])

        # Normalize to sum to 1.0
        total = sum(accuracy_values)
        if total > 0:
            weights = [v / total for v in accuracy_values]
        else:
            weights = default_model_weights_list()
    else:
        weights = default_model_weights_list()

    return weights


def default_model_weights() -> Dict[str, float]:
    """
    Get default model weights when accuracy data is unavailable.

    Weights based on expected model performance:
    - Stylometric: 0.40 (most reliable, feature-based)
    - Perplexity: 0.30 (language model signal)
    - Contrastive: 0.30 (embedding similarity)

    Returns:
        Dict mapping model names to default weights
    """
    return {
        'stylometric': 0.40,
        'perplexity': 0.30,
        'contrastive': 0.30
    }


def default_model_weights_list() -> List[float]:
    """
    Get default model weights as list in standard order.

    Returns:
        List of weights [stylometric, perplexity, contrastive]
    """
    defaults = default_model_weights()
    return [defaults['stylometric'], defaults['perplexity'], defaults['contrastive']]


def update_weights_with_performance(
    current_weights: Dict[str, float],
    new_metrics: Dict[str, float],
    learning_rate: float = 0.1
) -> Dict[str, float]:
    """
    Update ensemble weights based on recent performance metrics.

    Gradually adjusts weights toward better-performing models.

    Args:
        current_weights: Current weight dict
        new_metrics: Recent performance metrics (accuracy or f1 score)
        learning_rate: How much to adjust weights (0-1)

    Returns:
        Updated weight dict
    """
    model_names = ['stylometric', 'perplexity', 'contrastive']

    # Calculate target weights from new metrics
    target_weights = calculate_weights_from_accuracy(new_metrics)

    # Blend current weights with target weights
    updated = {}
    for i, name in enumerate(model_names):
        current_val = current_weights.get(name, default_model_weights()[name])
        target_val = target_weights[i]

        # Smooth update: move toward target
        updated[name] = current_val + learning_rate * (target_val - current_val)

    # Renormalize
    total = sum(updated.values())
    if total > 0:
        updated = {k: v / total for k, v in updated.items()}

    return updated


def get_weight_info(weights: List[float]) -> Dict[str, any]:
    """
    Get detailed information about ensemble weights.

    Args:
        weights: List of weights [stylometric, perplexity, contrastive]

    Returns:
        Dict with weight information and statistics
    """
    model_names = ['stylometric', 'perplexity', 'contrastive']

    return {
        'weights_by_model': {name: weight for name, weight in zip(model_names, weights)},
        'total_weight': sum(weights),
        'max_weight': max(weights),
        'min_weight': min(weights),
        'weight_range': max(weights) - min(weights),
        'dominant_model': model_names[int(np.argmax(weights))] if weights else None,
        'is_normalized': abs(sum(weights) - 1.0) < 1e-6
    }


# Import numpy for argmax if available
try:
    import numpy as np
except ImportError:
    import math
    # Fallback for argmax
    def np(arg):
        class ArrayLike:
            def __init__(self, arr):
                self.arr = arr
            def argmax(self):
                return max(range(len(self.arr)), key=lambda i: self.arr[i])
        return ArrayLike(arg)
