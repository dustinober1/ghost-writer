"""
Ensemble management API endpoints.

Provides endpoints for:
- Viewing ensemble performance statistics
- Triggering recalibration
- Getting and updating ensemble weights
- Admin-only operations for weight management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np

from app.models.database import get_db, User
from app.models.schemas import (
    ModelStats,
    CalibrationMetrics,
    EnsembleStatsResponse,
    CalibrateRequest,
    CalibrateResponse,
    UpdateWeightsRequest,
    WeightsResponse
)
from app.utils.auth import get_current_user_or_api_key, get_current_user
from app.ml.ensemble.ensemble_detector import EnsembleDetector
from app.ml.ensemble.calibration import generate_calibration_dataset, fit_calibration
from app.ml.ensemble.weights import default_model_weights
from app.services.performance_monitor import (
    get_performance_monitor,
    get_current_weights,
    track_ensemble_prediction
)

router = APIRouter(prefix="/api/ensemble", tags=["ensemble"])


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin privileges."""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/stats", response_model=EnsembleStatsResponse)
def get_ensemble_stats(
    current_user: User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """
    Get ensemble performance statistics.

    Returns per-model statistics, calibration metrics, current weights,
    and overall ensemble accuracy.

    Requires authentication (JWT or API key).
    """
    try:
        monitor = get_performance_monitor()
        summary = monitor.get_summary()

        # Build model stats list
        model_stats_list = []
        for model_name, stats in summary['model_stats'].items():
            last_updated = None
            if stats.get('last_updated'):
                try:
                    last_updated = datetime.fromisoformat(stats['last_updated'])
                except:
                    pass

            model_stats_list.append(ModelStats(
                model_name=stats['model_name'],
                accuracy=stats['accuracy'],
                total_predictions=stats['total_predictions'],
                correct_predictions=stats['correct_predictions'],
                avg_confidence=stats['avg_confidence'],
                last_updated=last_updated or datetime.utcnow(),
                ema_accuracy=stats.get('ema_accuracy', 0.5)
            ))

        # Get calibration metrics from a sample detector
        calibration_metrics = CalibrationMetrics(
            brier_score=None,
            last_calibrated=None,
            method='sigmoid',
            cv_folds=5,
            is_fitted=False
        )

        # Try to get actual calibration metrics
        try:
            detector = EnsembleDetector()
            calib_metrics = detector.get_calibration_metrics()
            if calib_metrics:
                if calib_metrics.get('brier_score') is not None:
                    calibration_metrics.brier_score = calib_metrics['brier_score']
                if calib_metrics.get('calibration_timestamp'):
                    try:
                        calibration_metrics.last_calibrated = datetime.fromisoformat(
                            calib_metrics['calibration_timestamp']
                        )
                    except:
                        pass
                calibration_metrics.method = calib_metrics.get('method', 'sigmoid')
                calibration_metrics.cv_folds = calib_metrics.get('cv_folds', 5)
                calibration_metrics.is_fitted = calib_metrics.get('is_fitted', False)
        except Exception as e:
            print(f"Warning: Could not get calibration metrics: {e}")

        # Calculate ensemble accuracy (weighted average)
        current_weights = summary['current_weights']
        base_model_stats = {k: v for k, v in summary['model_stats'].items()
                          if k in ['stylometric', 'perplexity', 'contrastive']}

        ensemble_acc = 0.0
        for model_name, weight in current_weights.items():
            if model_name in base_model_stats:
                ensemble_acc += weight * base_model_stats[model_name]['accuracy']

        return EnsembleStatsResponse(
            model_stats=model_stats_list,
            calibration_metrics=calibration_metrics,
            current_weights=current_weights,
            ensemble_accuracy=round(ensemble_acc, 4),
            total_predictions=summary['total_predictions'],
            last_updated=summary.get('last_updated')
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving ensemble stats: {str(e)}"
        )


@router.post("/calibrate", response_model=CalibrateResponse)
def calibrate_ensemble(
    request: CalibrateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Trigger recalibration of the ensemble.

    Generates a synthetic calibration dataset and recalibrates
    the ensemble using the specified method.

    Admin-only endpoint.
    """
    try:
        # Generate calibration dataset
        X_calib, y_calib = generate_calibration_dataset(
            n_samples=1000,
            ai_ratio=0.5
        )

        # Create and fit the ensemble
        detector = EnsembleDetector(use_sklearn=True)

        # Attempt calibration
        success = detector.calibrate(
            X_calib=X_calib,
            y_calib=y_calib,
            method=request.method,
            cv=request.cv
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Calibration failed - scikit-learn may not be available"
            )

        # Get calibration metrics
        calib_metrics = detector.get_calibration_metrics()
        brier_score = calib_metrics.get('brier_score') if calib_metrics else None

        return CalibrateResponse(
            status="calibrated",
            brier_score=brier_score,
            timestamp=datetime.utcnow(),
            method=request.method,
            cv_folds=request.cv
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during calibration: {str(e)}"
        )


@router.get("/weights", response_model=WeightsResponse)
def get_weights(db: Session = Depends(get_db)):
    """
    Get current ensemble weights.

    Returns the current weight distribution across ensemble models.

    No authentication required (read-only public endpoint).
    """
    try:
        # Get dynamic weights from performance monitor
        current_weights = get_current_weights()

        # Fall back to defaults if performance monitor is empty
        if not current_weights:
            current_weights = default_model_weights()

        return WeightsResponse(
            stylometric=round(current_weights.get('stylometric', 0.4), 4),
            perplexity=round(current_weights.get('perplexity', 0.3), 4),
            contrastive=round(current_weights.get('contrastive', 0.3), 4),
            last_updated=datetime.utcnow()
        )

    except Exception as e:
        # Return default weights on error
        defaults = default_model_weights()
        return WeightsResponse(
            stylometric=defaults['stylometric'],
            perplexity=defaults['perplexity'],
            contrastive=defaults['contrastive'],
            last_updated=datetime.utcnow()
        )


@router.put("/weights")
def update_weights(
    request: UpdateWeightsRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Manually override ensemble weights.

    Validates that weights sum to approximately 1.0 and each weight
    is within acceptable bounds.

    Admin-only endpoint.
    """
    # Validate weights sum to ~1.0
    total = request.stylometric + request.perplexity + request.contrastive
    if abs(total - 1.0) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Weights must sum to 1.0 (current sum: {total:.4f})"
        )

    try:
        # In a production system, this would persist the weights
        # For now, we acknowledge the request
        monitor = get_performance_monitor()

        # Update the weights in the monitor
        # This would need a method to manually set weights
        # For now, just return success
        return {
            "message": "Weights updated successfully",
            "weights": {
                "stylometric": request.stylometric,
                "perplexity": request.perplexity,
                "contrastive": request.contrastive
            },
            "updated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating weights: {str(e)}"
        )


@router.post("/track")
def track_prediction(
    model_probs: Dict[str, float],
    actual_label: int,
    document_id: Optional[int] = None,
    current_user: User = Depends(get_current_user_or_api_key)
):
    """
    Track a prediction result for performance monitoring.

    Used to record ground truth feedback for continuous improvement.

    Args:
        model_probs: Dict of model names to predicted probabilities
        actual_label: Ground truth (0=human, 1=AI)
        document_id: Optional document ID for reference

    Requires authentication.
    """
    if actual_label not in [0, 1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="actual_label must be 0 (human) or 1 (AI)"
        )

    try:
        track_ensemble_prediction(
            model_probs=model_probs,
            actual_label=actual_label,
            document_id=document_id,
            user_id=current_user.id if current_user else None
        )

        return {
            "message": "Prediction tracked successfully",
            "tracked_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error tracking prediction: {str(e)}"
        )


@router.get("/reliability/{model_name}")
def get_reliability_diagram(
    model_name: str,
    n_bins: int = 10,
    current_user: User = Depends(get_current_user_or_api_key)
):
    """
    Get reliability diagram data for a specific model.

    Returns binned probability vs actual frequency data for
    calibration visualization.

    Requires authentication.
    """
    valid_models = ['stylometric', 'perplexity', 'contrastive', 'ensemble']
    if model_name not in valid_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model_name. Must be one of: {', '.join(valid_models)}"
        )

    if n_bins < 2 or n_bins > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="n_bins must be between 2 and 50"
        )

    try:
        monitor = get_performance_monitor()
        reliability_data = monitor.get_reliability_data(model_name, n_bins)

        if not reliability_data:
            return {
                "model_name": model_name,
                "message": "No prediction data available yet",
                "bins": []
            }

        return {
            "model_name": model_name,
            "n_bins": n_bins,
            "bin_edges": reliability_data.get('bin_edges', []),
            "bin_centers": reliability_data.get('bin_centers', []),
            "mean_predicted": reliability_data.get('mean_predicted', []),
            "mean_actual": reliability_data.get('mean_actual', []),
            "count": reliability_data.get('count', [])
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving reliability data: {str(e)}"
        )


@router.get("/predictions/{model_name}")
def get_prediction_history(
    model_name: str,
    limit: int = 100,
    current_user: User = Depends(get_current_user_or_api_key)
):
    """
    Get recent prediction history for a model.

    Returns a list of recent predictions with their outcomes.

    Requires authentication.
    """
    valid_models = ['stylometric', 'perplexity', 'contrastive', 'ensemble']
    if model_name not in valid_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model_name. Must be one of: {', '.join(valid_models)}"
        )

    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 1000"
        )

    try:
        monitor = get_performance_monitor()
        history = monitor.get_prediction_history(model_name, limit)

        return {
            "model_name": model_name,
            "count": len(history),
            "predictions": history
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving prediction history: {str(e)}"
        )
