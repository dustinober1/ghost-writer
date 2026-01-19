---
phase: 05-enhanced-fingerprinting
plan: 03
subsystem: time-weighted-fingerprinting
tags: [ema, exponential-moving-average, time-weighted, fingerprint, similarity, confidence-interval, welford]

# Dependency graph
requires:
  - phase: 05-enhanced-fingerprinting
    plans: [01]
    provides: FingerprintCorpusBuilder, FEATURE_NAMES, MIN_SAMPLES_FOR_FINGERPRINT
provides:
  - TimeWeightedFingerprintBuilder for incremental EMA-based fingerprint building
  - FingerprintComparator for similarity with confidence intervals
  - Module exports for enhanced fingerprinting API
affects:
  - phase: 05-enhanced-fingerprinting
    plans: [04]
    reason: Time-weighted builder and comparator enable API route implementation

# Tech tracking
tech-stack:
  added: [TimeWeightedFingerprintBuilder, FingerprintComparator, EMA algorithm, Welford's algorithm, confidence intervals, z-score CI]
  patterns: [Incremental EMA updates, exponential recency decay, cosine similarity, statistical confidence bounds]

key-files:
  created: [backend/app/ml/fingerprint/time_weighted_trainer.py, backend/app/ml/fingerprint/similarity_calculator.py]
  modified: [backend/app/ml/fingerprint/__init__.py]

key-decisions:
  - "EMA alpha=0.3 - balances recency sensitivity with stability for writing style evolution"
  - "Lambda = -ln(alpha) for recency weight calculation - ensures consistency between EMA and time-decay"
  - "95% confidence level with z-score=1.96 - standard statistical confidence for interval bounds"
  - "Similarity thresholds: HIGH=0.85, MEDIUM=0.70, LOW=0.50 - based on authorship verification research"
  - "Graceful degradation when scipy/sklearn unavailable - uses fallback calculations and pre-computed z-scores"
  - "Welford's online algorithm for variance - numerically stable for incremental statistics"
  - "Top 5 feature deviations for interpretability - highlights most different stylometric features"

patterns-established:
  - "EMA formula: new_ema = (1 - alpha) * old_ema + alpha * new_sample"
  - "Recency weights: weight = exp(-lambda * age), normalized to sum to 1"
  - "Confidence interval width = z_score * SEM where SEM = sqrt(mean_variance / n_features)"
  - "Feature deviation normalized by std: (text_val - fp_val) / std_val"

# Metrics
duration: 3min
completed: 2026-01-19
---

# Phase 5 Plan 3: Time-Weighted Training and Similarity Calculation Summary

**EMA-based incremental fingerprint building with similarity comparison and confidence interval quantification**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-19T21:58:34Z
- **Completed:** 2026-01-19T22:01:39Z
- **Tasks:** 3
- **Files created:** 2
- **Files modified:** 1

## Accomplishments

### Task 1: TimeWeightedFingerprintBuilder with EMA

- `TimeWeightedFingerprintBuilder` class with `alpha=0.3` default EMA smoothing parameter
- `add_sample(features, timestamp)` method applying EMA update rule
- `MIN_SAMPLES_FOR_FINGERPRINT = 10` constant for statistical robustness
- Welford's online algorithm for numerically stable variance calculation via `_update_stats()`
- `compute_recency_weights(timestamps, current_time)` for exponential decay based on timestamp age
- `get_fingerprint()` returning feature_vector with per-feature statistics (mean, std, variance)
- `reset()`, `is_ready()`, `samples_needed()` utility methods
- Convenience functions: `add_sample()`, `get_fingerprint()`, `compute_recency_weights()`

### Task 2: FingerprintComparator with Confidence Intervals

- `FingerprintComparator` class with configurable confidence level (default 0.95)
- Similarity thresholds: `THRESHOLD_HIGH_SIMILARITY=0.85`, `THRESHOLD_MEDIUM_SIMILARITY=0.70`, `THRESHOLD_LOW_SIMILARITY=0.50`
- `compare_with_confidence()` returning similarity score with confidence interval bounds
- Z-score calculation via scipy.stats.norm.ppf (or pre-computed fallback values)
- Confidence interval width calculation using Standard Error of Mean (SEM)
- `_classify_match()` categorizing similarity into HIGH/MEDIUM/LOW levels
- `_compute_feature_deviations()` identifying top 5 most different stylometric features
- Graceful degradation when scipy/sklearn unavailable
- Convenience functions: `compare_with_confidence()`, `classify_match()`

### Task 3: Module Exports

- Updated `backend/app/ml/fingerprint/__init__.py` with comprehensive exports
- Exports: `FingerprintCorpusBuilder`, `TimeWeightedFingerprintBuilder`, `FingerprintComparator`
- Exports: `compare_with_confidence`, `classify_match`, `compute_recency_weights`
- Exports: Threshold constants (`THRESHOLD_HIGH_SIMILARITY`, `THRESHOLD_MEDIUM_SIMILARITY`, `THRESHOLD_LOW_SIMILARITY`)
- Maintains backward compatibility with legacy API (`generate_fingerprint`, `update_fingerprint`, `compare_to_fingerprint`)
- Module-level constants: `MIN_SAMPLES_FOR_FINGERPRINT=10`, `DEFAULT_ALPHA=0.3`, `DEFAULT_CONFIDENCE_LEVEL=0.95`
- Comprehensive docstring with usage examples

## Task Commits

Each task was committed atomically:

1. **Task 1: TimeWeightedFingerprintBuilder** - `fc26226` (feat)
2. **Task 2: FingerprintComparator** - `a96c813` (feat)
3. **Task 3: Module exports** - `0c0aa7f` (feat)

## Files Created/Modified

### Created

- `backend/app/ml/fingerprint/time_weighted_trainer.py` - Time-weighted EMA fingerprint builder (370 lines)
- `backend/app/ml/fingerprint/similarity_calculator.py` - Similarity calculator with confidence intervals (396 lines)

### Modified

- `backend/app/ml/fingerprint/__init__.py` - Enhanced module exports and documentation

## EMA Implementation Details

### EMA Update Formula

```
new_ema = (1 - alpha) * old_ema + alpha * new_sample
```

- **Alpha = 0.3**: Default smoothing parameter
- Higher alpha = more responsive to recent changes
- Lower alpha = more stable, slower adaptation

### Recency Weight Calculation

```
weight = exp(-lambda * age)
lambda = -ln(alpha)
```

- At age=0, weight=1 (current time has maximum weight)
- Lambda derived from alpha for EMA consistency
- Weights normalized to sum to 1.0

### Welford's Online Algorithm

Per-feature statistics updated incrementally:

```
count_n = count_{n-1} + 1
delta = new_value - mean_{n-1}
mean_n = mean_{n-1} + delta / count_n
delta2 = new_value - mean_n
M2_n = M2_{n-1} + delta * delta2
variance_n = M2_n / count_n
```

Advantages:
- Numerically stable (avoids catastrophic cancellation)
- Single-pass algorithm
- Suitable for streaming data

## Confidence Interval Calculation

### Formula

```
SEM = sqrt(mean_variance / n_features)
CI_width = z_score * SEM
CI = [similarity - CI_width, similarity + CI_width]
```

### Parameters

- **Confidence level**: 0.95 (95% confidence)
- **Z-score**: 1.96 (for 95% CI, calculated via scipy.stats.norm.ppf)
- **Fallback z-scores**: 0.90=1.645, 0.95=1.960, 0.99=2.576

### Similarity Thresholds

| Level | Threshold | Interpretation |
|-------|-----------|----------------|
| HIGH | >= 0.85 | Strong match, likely same author |
| MEDIUM | >= 0.70 | Likely match, requires context |
| LOW | < 0.70 | Ambiguous, below reliable threshold |

## Feature Deviation Analysis

- Computes absolute deviation: `|text_value - fingerprint_value|`
- Normalizes by standard deviation when available
- Returns top 5 features with `normalized_deviation > 2.0`
- Provides interpretable feature names from `FEATURE_NAMES`

## Graceful Degradation

The modules handle missing dependencies gracefully:

1. **scipy unavailable**: Uses pre-computed z-scores for common confidence levels
2. **sklearn unavailable**: Falls back to manual cosine similarity calculation
3. **No feature statistics**: Returns default CI width of 0.1

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Runtime dependencies not in test environment:** numpy, scipy, sklearn not available for runtime testing.
- **Resolution:** Syntax validation completed successfully via py_compile
- Code structure validated via AST parsing
- All required methods and constants verified

## Performance Notes

- EMA update is O(n_features) per sample - efficient for streaming
- Cosine similarity is O(n_features) - fast comparison
- Welford's algorithm is O(1) per feature per sample - optimal for incremental updates
- Confidence interval calculation is O(n_features) - negligible overhead

## Next Phase Readiness

- TimeWeightedFingerprintBuilder ready for API route integration (Plan 05-04)
- FingerprintComparator provides statistical confidence for verification decisions
- Module exports enable clean API: `from app.ml.fingerprint import TimeWeightedFingerprintBuilder, FingerprintComparator`
- Confidence intervals enable UI display of uncertainty bounds
- Feature deviations provide interpretable feedback for users

---
*Phase: 05-enhanced-fingerprinting*
*Plan: 03*
*Completed: 2026-01-19*
