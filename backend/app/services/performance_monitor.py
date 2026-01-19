"""
Performance monitoring and dynamic weight updates for ensemble models.

Tracks per-model prediction accuracy over time and updates ensemble weights
based on observed performance.

Uses exponential moving average for smooth weight transitions and
prevents rapid weight changes from noisy data.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.models.database import get_db
from app.ml.ensemble.weights import default_model_weights, update_weights_with_performance


# Default minimum predictions before updating weights
MIN_PREDICTIONS_FOR_UPDATE = 100

# Default minimum weight per model (no model gets zeroed out)
MIN_MODEL_WEIGHT = 0.1

# Exponential moving average smoothing factor
EMA_ALPHA = 0.3  # Higher = more responsive to new data


@dataclass
class ModelPerformanceRecord:
    """Single prediction record for performance tracking."""
    model_name: str
    predicted_prob: float
    actual_label: int  # 0 = human, 1 = AI
    timestamp: datetime
    document_id: Optional[int] = None
    user_id: Optional[int] = None
    was_correct: Optional[bool] = None


class PerformanceMonitor:
    """
    Tracks and analyzes model performance for ensemble weight updates.

    Stores prediction records and calculates per-model accuracy metrics.
    Updates ensemble weights based on observed performance.
    """

    def __init__(
        self,
        db_session: Optional[Session] = None,
        min_predictions: int = MIN_PREDICTIONS_FOR_UPDATE,
        min_weight: float = MIN_MODEL_WEIGHT,
        ema_alpha: float = EMA_ALPHA
    ):
        """
        Initialize the performance monitor.

        Args:
            db_session: Optional database session for persistence
            min_predictions: Minimum predictions before updating weights
            min_weight: Minimum weight per model (prevents zeroing)
            ema_alpha: Exponential moving average smoothing factor
        """
        self.db_session = db_session
        self.min_predictions = min_predictions
        self.min_weight = min_weight
        self.ema_alpha = ema_alpha

        # In-memory prediction storage
        self._predictions: List[ModelPerformanceRecord] = []

        # EMA tracking for smooth accuracy estimates
        self._ema_accuracy: Dict[str, float] = {}

        # Load persisted data if available
        self._load_from_storage()

    def track_prediction(
        self,
        model_name: str,
        predicted_prob: float,
        actual_label: int,
        document_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Record a prediction result for performance tracking.

        Args:
            model_name: Name of the model (stylometric, perplexity, contrastive, ensemble)
            predicted_prob: Predicted AI probability (0-1)
            actual_label: Ground truth label (0=human, 1=AI)
            document_id: Optional document ID for reference
            user_id: Optional user ID for user-specific tracking

        Returns:
            True if recorded successfully
        """
        if model_name not in ['stylometric', 'perplexity', 'contrastive', 'ensemble']:
            print(f"Warning: Unknown model name: {model_name}")
            return False

        # Determine if prediction was correct
        predicted_label = 1 if predicted_prob > 0.5 else 0
        was_correct = (predicted_label == actual_label)

        record = ModelPerformanceRecord(
            model_name=model_name,
            predicted_prob=float(predicted_prob),
            actual_label=int(actual_label),
            timestamp=datetime.utcnow(),
            document_id=document_id,
            user_id=user_id,
            was_correct=was_correct
        )

        self._predictions.append(record)

        # Update EMA for this model
        if model_name not in self._ema_accuracy:
            self._ema_accuracy[model_name] = 0.5  # Start with neutral
        else:
            # Update EMA: new = alpha * current + (1 - alpha) * old
            self._ema_accuracy[model_name] = (
                self.ema_alpha * (1.0 if was_correct else 0.0) +
                (1 - self.ema_alpha) * self._ema_accuracy[model_name]
            )

        # Persist if we have enough records
        if len(self._predictions) % 50 == 0:
            self._save_to_storage()

        return True

    def get_model_stats(self, model_name: Optional[str] = None) -> Dict:
        """
        Get performance statistics for one or all models.

        Args:
            model_name: Specific model name, or None for all models

        Returns:
            Dict with model statistics
        """
        model_names = [model_name] if model_name else ['stylometric', 'perplexity', 'contrastive', 'ensemble']

        stats = {}
        for name in model_names:
            model_predictions = [p for p in self._predictions if p.model_name == name]

            if not model_predictions:
                stats[name] = {
                    'model_name': name,
                    'total_predictions': 0,
                    'correct_predictions': 0,
                    'accuracy': 0.0,
                    'last_updated': None,
                    'avg_confidence': 0.0,
                    'ema_accuracy': self._ema_accuracy.get(name, 0.5)
                }
                continue

            correct_count = sum(1 for p in model_predictions if p.was_correct)
            total_count = len(model_predictions)
            accuracy = correct_count / total_count if total_count > 0 else 0.0

            # Average confidence when prediction > 0.7 (high confidence)
            high_conf_preds = [p.predicted_prob for p in model_predictions if p.predicted_prob > 0.7]
            avg_confidence = sum(high_conf_preds) / len(high_conf_preds) if high_conf_preds else 0.0

            last_updated = max(p.timestamp for p in model_predictions) if model_predictions else None

            stats[name] = {
                'model_name': name,
                'total_predictions': total_count,
                'correct_predictions': correct_count,
                'accuracy': round(accuracy, 4),
                'last_updated': last_updated.isoformat() if last_updated else None,
                'avg_confidence': round(avg_confidence, 4),
                'ema_accuracy': round(self._ema_accuracy.get(name, 0.5), 4)
            }

        return stats if model_name else stats

    def update_weights(self) -> Dict[str, float]:
        """
        Calculate updated ensemble weights based on performance.

        Uses EMA accuracy for smooth transitions. Enforces minimum weight
        per model to prevent any model from being zeroed out.

        Returns:
            Dict of updated weights {stylometric: w1, perplexity: w2, ...}
        """
        stats = self.get_model_stats()

        # Get EMA accuracies for base models only
        model_names = ['stylometric', 'perplexity', 'contrastive']
        accuracies = {}

        for name in model_names:
            model_stats = stats.get(name, {})
            total_preds = model_stats.get('total_predictions', 0)

            # Use EMA accuracy if we have enough data
            if total_preds >= self.min_predictions:
                accuracies[name] = model_stats.get('ema_accuracy', 0.5)
            else:
                # Use default weight component if insufficient data
                defaults = default_model_weights()
                # Map default weights to pseudo-accuracy
                # Higher default weight = higher assumed accuracy
                accuracies[name] = 0.5 + (defaults.get(name, 0.33) - 0.33) * 0.5

        # Calculate initial weights from accuracies
        total = sum(accuracies.values())
        if total > 0:
            weights = {k: v / total for k, v in accuracies.items()}
        else:
            weights = default_model_weights()

        # Enforce minimum weight constraint
        for name in weights:
            if weights[name] < self.min_weight:
                weights[name] = self.min_weight

        # Renormalize after minimum weight enforcement
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    def calculate_brier_score(self, model_name: str) -> float:
        """
        Calculate Brier score for a specific model.

        Brier score measures probability calibration quality.
        Lower is better (0 = perfect calibration).

        Formula: mean((predicted_prob - actual_label)^2)

        Args:
            model_name: Name of the model to evaluate

        Returns:
            Brier score (lower is better)
        """
        model_predictions = [p for p in self._predictions if p.model_name == model_name]

        if not model_predictions:
            return 1.0  # Worst possible score if no data

        if NUMPY_AVAILABLE:
            probs = np.array([p.predicted_prob for p in model_predictions])
            labels = np.array([p.actual_label for p in model_predictions])
            return float(np.mean((probs - labels) ** 2))
        else:
            # Pure Python fallback
            squared_errors = [(p.predicted_prob - p.actual_label) ** 2 for p in model_predictions]
            return sum(squared_errors) / len(squared_errors)

    def get_reliability_data(
        self,
        model_name: str,
        n_bins: int = 10
    ) -> Dict[str, List]:
        """
        Generate data for reliability diagram visualization.

        Bins predicted probabilities and compares to actual frequencies.
        Well-calibrated models show predicted ≈ actual in each bin.

        Args:
            model_name: Name of the model to evaluate
            n_bins: Number of probability bins

        Returns:
            Dict with bin data for plotting
        """
        model_predictions = [p for p in self._predictions if p.model_name == model_name]

        if not model_predictions:
            return {}

        # Sort by predicted probability
        sorted_preds = sorted(model_predictions, key=lambda p: p.predicted_prob)

        # Create bins
        bin_edges = [i / n_bins for i in range(n_bins + 1)]
        bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(n_bins)]

        # Initialize bin data
        bin_data = {
            'bin_edges': bin_edges,
            'bin_centers': bin_centers,
            'mean_predicted': [],
            'mean_actual': [],
            'count': []
        }

        # Calculate statistics for each bin
        for i in range(n_bins):
            lower = bin_edges[i]
            upper = bin_edges[i + 1]

            # Find predictions in this bin
            # Edge case: upper bound inclusive for last bin
            if i == n_bins - 1:
                in_bin = [p for p in sorted_preds if lower <= p.predicted_prob <= upper]
            else:
                in_bin = [p for p in sorted_preds if lower <= p.predicted_prob < upper]

            if in_bin:
                mean_pred = sum(p.predicted_prob for p in in_bin) / len(in_bin)
                mean_actual = sum(p.actual_label for p in in_bin) / len(in_bin)
                bin_data['mean_predicted'].append(float(mean_pred))
                bin_data['mean_actual'].append(float(mean_actual))
                bin_data['count'].append(len(in_bin))
            else:
                bin_data['mean_predicted'].append(float(bin_centers[i]))
                bin_data['mean_actual'].append(0.0)
                bin_data['count'].append(0)

        return bin_data

    def get_prediction_history(
        self,
        model_name: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get recent prediction history for a model.

        Args:
            model_name: Name of the model
            limit: Maximum number of records to return
            since: Optional start time filter

        Returns:
            List of prediction records as dicts
        """
        predictions = [p for p in self._predictions if p.model_name == model_name]

        if since:
            predictions = [p for p in predictions if p.timestamp >= since]

        # Sort by timestamp descending and limit
        predictions = sorted(predictions, key=lambda p: p.timestamp, reverse=True)[:limit]

        return [
            {
                'model_name': p.model_name,
                'predicted_prob': p.predicted_prob,
                'actual_label': p.actual_label,
                'timestamp': p.timestamp.isoformat(),
                'was_correct': p.was_correct
            }
            for p in predictions
        ]

    def clear_old_predictions(self, days_to_keep: int = 30) -> int:
        """
        Remove prediction records older than specified days.

        Args:
            days_to_keep: Number of days of history to retain

        Returns:
            Number of records removed
        """
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        initial_count = len(self._predictions)

        self._predictions = [p for p in self._predictions if p.timestamp > cutoff]

        removed_count = initial_count - len(self._predictions)
        if removed_count > 0:
            self._save_to_storage()

        return removed_count

    def get_summary(self) -> Dict:
        """
        Get overall performance summary.

        Returns:
            Dict with summary statistics across all models
        """
        total_predictions = len(self._predictions)

        stats_by_model = self.get_model_stats()
        current_weights = self.update_weights()

        return {
            'total_predictions': total_predictions,
            'models_tracked': list(stats_by_model.keys()),
            'model_stats': stats_by_model,
            'current_weights': current_weights,
            'min_predictions_for_update': self.min_predictions,
            'last_updated': max(
                (s['last_updated'] for s in stats_by_model.values() if s['last_updated']),
                default=None
            )
        }

    def _load_from_storage(self) -> None:
        """Load prediction records from persistent storage."""
        storage_path = self._get_storage_path()

        if not os.path.exists(storage_path):
            return

        try:
            with open(storage_path, 'r') as f:
                data = json.load(f)

            # Load EMA values
            self._ema_accuracy = data.get('ema_accuracy', {})

            # Load predictions (limit to most recent to avoid memory issues)
            predictions_data = data.get('predictions', [])
            max_predictions = 10000  # Limit in-memory storage

            for pred in predictions_data[-max_predictions:]:
                self._predictions.append(ModelPerformanceRecord(
                    model_name=pred['model_name'],
                    predicted_prob=pred['predicted_prob'],
                    actual_label=pred['actual_label'],
                    timestamp=datetime.fromisoformat(pred['timestamp']),
                    document_id=pred.get('document_id'),
                    user_id=pred.get('user_id'),
                    was_correct=pred.get('was_correct')
                ))

            print(f"Loaded {len(self._predictions)} prediction records from storage")

        except Exception as e:
            print(f"Error loading performance data: {e}")

    def _save_to_storage(self) -> None:
        """Save prediction records to persistent storage."""
        storage_path = self._get_storage_path()

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)

            # Prepare data for serialization
            predictions_data = [
                {
                    'model_name': p.model_name,
                    'predicted_prob': p.predicted_prob,
                    'actual_label': p.actual_label,
                    'timestamp': p.timestamp.isoformat(),
                    'document_id': p.document_id,
                    'user_id': p.user_id,
                    'was_correct': p.was_correct
                }
                for p in self._predictions[-1000:]  # Only save most recent 1000
            ]

            data = {
                'ema_accuracy': self._ema_accuracy,
                'predictions': predictions_data,
                'last_saved': datetime.utcnow().isoformat()
            }

            with open(storage_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Error saving performance data: {e}")

    def _get_storage_path(self) -> str:
        """Get the file path for persistent storage."""
        # Store in backend/data directory
        base_dir = os.path.dirname(os.path.dirname(__file__))
        data_dir = os.path.join(base_dir, 'data')
        return os.path.join(data_dir, 'performance_monitor.json')


# Global monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def track_ensemble_prediction(
    model_probs: Dict[str, float],
    actual_label: int,
    document_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> None:
    """
    Track predictions from all ensemble models.

    Convenience function to record predictions from all models at once.

    Args:
        model_probs: Dict of model names to predicted AI probabilities
        actual_label: Ground truth label (0=human, 1=AI)
        document_id: Optional document ID
        user_id: Optional user ID
    """
    monitor = get_performance_monitor()

    for model_name, prob in model_probs.items():
        if model_name in ['stylometric', 'perplexity', 'contrastive', 'ensemble']:
            monitor.track_prediction(
                model_name=model_name,
                predicted_prob=prob,
                actual_label=actual_label,
                document_id=document_id,
                user_id=user_id
            )


def get_current_weights() -> Dict[str, float]:
    """
    Get current ensemble weights based on performance.

    Returns:
        Dict of model weights
    """
    monitor = get_performance_monitor()
    return monitor.update_weights()
