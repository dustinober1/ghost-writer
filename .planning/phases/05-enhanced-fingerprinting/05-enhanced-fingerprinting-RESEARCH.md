# Phase 05: Enhanced Fingerprinting - Research

**Researched:** 2026-01-19
**Domain:** Stylometric fingerprinting, time-weighted learning, style drift detection
**Confidence:** MEDIUM

## Summary

This phase implements enhanced personal writing fingerprints that can detect style drift and evolution over time. The core approach builds on the existing 27-feature stylometric extraction system, adding corpus-based training with time-weighted samples (exponential moving average), confidence intervals for similarity scores, and drift detection alerts. Research indicates that stylometric fingerprinting with cosine similarity thresholds around 0.5-0.85 is effective for authorship verification, and exponential moving average (EMA) with alpha values between 0.1-0.3 provides smooth adaptation to style evolution while maintaining core pattern recognition.

**Primary recommendation:** Build on the existing `fingerprint.py` module using scikit-learn's preprocessing scalers for feature normalization, implement time-weighted training via exponential moving average (alpha=0.3 for recency), use cosine similarity with dynamic thresholds (0.7-0.85) for fingerprint comparison, and implement drift detection using statistical process control techniques (confidence intervals via standard deviation bands).

## Standard Stack

The established libraries/tools for this domain:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 1.24.3 | Vector operations for feature averaging | Already in project; required for EMA calculations |
| scikit-learn | 1.3.2 | Feature scaling, similarity metrics | Gold standard for preprocessing and distance metrics |
| scipy | 1.11.4 | Statistical functions for confidence intervals | Provides stats for drift detection |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sklearn.preprocessing.StandardScaler | Built-in | Z-score normalization for features | Use when features have Gaussian-like distributions |
| sklearn.preprocessing.MinMaxScaler | Built-in | Scale to [0,1] range | Use when features have natural boundaries |
| sklearn.metrics.pairwise.cosine_similarity | Built-in | Compute fingerprint similarity | Primary similarity metric for authorship verification |
| scipy.stats | Built-in | Confidence interval calculations | For drift detection uncertainty quantification |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Cosine similarity | Euclidean distance | Cosine similarity (0.5-0.85 threshold) is standard for authorship verification; Euclidean more sensitive to vector magnitude |
| EMA time-weighting | Simple moving average | EMA gives exponential decay, recent samples weighted higher; SMA gives equal weight to all samples |
| StandardScaler | RobustScaler | RobustScaler better for outliers but stylometric features typically bounded; StandardScaler is simpler and adequate |

**Installation:**
```bash
# All dependencies already present in requirements.txt
# numpy==1.24.3
# scikit-learn==1.3.2
# scipy==1.11.4
```

## Architecture Patterns

### Recommended Project Structure

```
backend/app/ml/
├── fingerprint/
│   ├── __init__.py
│   ├── corpus_builder.py          # Multi-sample corpus management
│   ├── time_weighted_trainer.py   # EMA-based training with recency weights
│   ├── drift_detector.py          # Style drift detection with confidence intervals
│   └── similarity_calculator.py   # Cosine similarity with dynamic thresholds
├── feature_extraction.py          # Existing 27-feature extractor (enhance)
└── fingerprint.py                 # Existing base fingerprint module (extend)

backend/app/models/
├── database.py                    # Add FingerprintCorpus, FingerprintSample tables
└── schemas.py                     # Add corpus, drift alert schemas

backend/app/api/
└── routes/
    └── fingerprint.py             # Corpus management, drift alerts endpoints

frontend/src/components/
├── fingerprint/
│   ├── CorpusBuilder.tsx          # Multi-sample upload interface
│   ├── FingerprintProfile.tsx     # Visual fingerprint representation
│   └── DriftAlerts.tsx            # Style drift notifications with explanations
```

### Pattern 1: Time-Weighted Fingerprint Training

**What:** Exponential moving average (EMA) applied to feature vectors, giving higher weight to recent writing samples while maintaining historical patterns.

**When to use:** When building fingerprints from corpora with samples collected over time; accounts for natural style evolution.

**Example:**
```python
# Source: Based on EMA weight decay research
# https://arxiv.org/abs/2411.18704
import numpy as np
from typing import List, Dict
from datetime import datetime, timedelta

class TimeWeightedFingerprintBuilder:
    """Build fingerprints with time-weighted averaging."""

    def __init__(self, alpha: float = 0.3):
        """
        Args:
            alpha: EMA smoothing factor (0-1).
                   Higher = more weight to recent samples.
                   0.3 is standard for balanced recency.
        """
        self.alpha = alpha
        self.fingerprint_vector = None
        self.sample_count = 0
        self.feature_stats = {}  # Track per-feature statistics

    def add_sample(self, features: np.ndarray, timestamp: datetime = None) -> None:
        """
        Add a new writing sample to the fingerprint.

        Args:
            features: Normalized feature vector
            timestamp: When sample was written (for time decay)
        """
        if self.fingerprint_vector is None:
            # Initialize with first sample
            self.fingerprint_vector = features.copy()
            self.sample_count = 1
        else:
            # Apply EMA update
            # new_fingerprint = (1 - alpha) * old + alpha * new
            self.fingerprint_vector = (
                (1 - self.alpha) * self.fingerprint_vector +
                self.alpha * features
            )
            self.sample_count += 1

        # Update feature statistics for confidence intervals
        self._update_stats(features)

    def compute_recency_weights(self, timestamps: List[datetime],
                                current_time: datetime) -> np.ndarray:
        """
        Compute exponential decay weights based on sample age.

        Args:
            timestamps: List of sample timestamps
            current_time: Reference time for decay calculation

        Returns:
            Array of weights summing to 1.0
        """
        # Calculate age in days
        ages = np.array([
            (current_time - ts).total_seconds() / 86400  # days
            for ts in timestamps
        ])

        # Exponential decay: weight = e^(-lambda * age)
        # lambda controls decay rate; lambda = -ln(alpha) for consistency with EMA
        decay_rate = -np.log(self.alpha)
        raw_weights = np.exp(-decay_rate * ages)

        # Normalize to sum to 1
        return raw_weights / raw_weights.sum()

    def get_fingerprint(self) -> Dict:
        """Return the current fingerprint with metadata."""
        if self.fingerprint_vector is None:
            raise ValueError("No samples added to fingerprint")

        return {
            "feature_vector": self.fingerprint_vector.tolist(),
            "sample_count": self.sample_count,
            "model_version": "2.0",
            "method": "time_weighted_ema",
            "alpha": self.alpha,
            "feature_statistics": self._get_feature_stats_summary()
        }

    def _update_stats(self, features: np.ndarray) -> None:
        """Update running statistics for confidence intervals."""
        for i, val in enumerate(features):
            if i not in self.feature_stats:
                self.feature_stats[i] = {
                    "mean": val,
                    "variance": 0.0,
                    "count": 1
                }
            else:
                # Welford's online algorithm for variance
                stats = self.feature_stats[i]
                stats["count"] += 1
                delta = val - stats["mean"]
                stats["mean"] += delta / stats["count"]
                stats["variance"] += delta * (val - stats["mean"])
```

### Pattern 2: Fingerprint Similarity with Confidence Intervals

**What:** Compute cosine similarity between text and fingerprint, with confidence intervals based on feature variance.

**When to use:** When comparing new text against a user's fingerprint; provides uncertainty quantification.

**Example:**
```python
# Source: Based on cosine similarity threshold research
# https://aclanthology.org/2025.findings-emnlp.856.pdf
import numpy as np
from scipy import stats
from sklearn.metrics.pairwise import cosine_similarity

class FingerprintComparator:
    """Compare text to fingerprint with confidence intervals."""

    # Cosine similarity thresholds from authorship verification research
    # Source: EMNLP 2025 findings on residualized similarity
    THRESHOLD_HIGH_SIMILARITY = 0.85  # Strong match
    THRESHOLD_MEDIUM_SIMILARITY = 0.70  # Likely match
    THRESHOLD_LOW_SIMILARITY = 0.50  # Ambiguous/below threshold

    def __init__(self, confidence_level: float = 0.95):
        """
        Args:
            confidence_level: For confidence intervals (0.95 = 95%)
        """
        self.confidence_level = confidence_level
        self.z_score = stats.norm.ppf((1 + confidence_level) / 2)

    def compare_with_confidence(
        self,
        text_features: np.ndarray,
        fingerprint: Dict,
        fingerprint_stats: Dict = None
    ) -> Dict:
        """
        Compare text to fingerprint with confidence intervals.

        Args:
            text_features: Feature vector of text to compare
            fingerprint: Fingerprint dictionary with feature_vector
            fingerprint_stats: Per-feature statistics for CI calculation

        Returns:
            {
                "similarity": float,  # Cosine similarity [0, 1]
                "confidence_interval": [lower, upper],
                "match_level": "HIGH" | "MEDIUM" | "LOW",
                "feature_deviations": {...}  # Which features differ most
            }
        """
        fp_vector = np.array(fingerprint["feature_vector"])

        # Compute cosine similarity
        similarity = float(cosine_similarity(
            text_features.reshape(1, -1),
            fp_vector.reshape(1, -1)
        )[0, 0])

        # Calculate confidence interval based on feature variance
        ci_width = self._calculate_ci_width(
            text_features, fp_vector, fingerprint_stats
        )

        result = {
            "similarity": similarity,
            "confidence_interval": [
                max(0, similarity - ci_width),
                min(1, similarity + ci_width)
            ],
            "match_level": self._classify_match(similarity),
            "feature_deviations": self._compute_feature_deviations(
                text_features, fp_vector, fingerprint_stats
            )
        }

        return result

    def _calculate_ci_width(
        self,
        text_features: np.ndarray,
        fp_vector: np.ndarray,
        stats: Dict = None
    ) -> float:
        """Calculate confidence interval width."""
        if stats is None:
            # Default CI width without statistics
            return 0.1

        # Calculate standard error based on feature variance
        variances = np.array([
            stats.get(i, {}).get("variance", 0.01)
            for i in range(len(text_features))
        ])

        # Standard error of the mean
        sem = np.sqrt(np.mean(variances) / len(text_features))

        # CI width = z_score * SEM
        return self.z_score * sem

    def _classify_match(self, similarity: float) -> str:
        """Classify similarity level based on thresholds."""
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
        stats: Dict = None
    ) -> Dict:
        """Identify which features deviate most from fingerprint."""
        from app.ml.feature_extraction import FEATURE_NAMES

        deviations = {}
        for i, (text_val, fp_val) in enumerate(zip(text_features, fp_vector)):
            feature_name = FEATURE_NAMES[i] if i < len(FEATURE_NAMES) else f"feature_{i}"
            deviation = abs(text_val - fp_val)

            # Normalize deviation by feature variance if available
            if stats and i in stats:
                variance = stats[i].get("variance", 0.01)
                normalized_dev = deviation / (np.sqrt(variance) + 1e-6)
            else:
                normalized_dev = deviation

            if normalized_dev > 2.0:  # Significant deviation
                deviations[feature_name] = {
                    "text_value": float(text_val),
                    "fingerprint_value": float(fp_val),
                    "deviation": float(normalized_dev)
                }

        # Sort by deviation and return top 5
        return dict(sorted(deviations.items(),
                          key=lambda x: x[1]["deviation"],
                          reverse=True)[:5])
```

### Pattern 3: Style Drift Detection

**What:** Monitor fingerprint similarity over time and alert when style drifts significantly from established patterns.

**When to use:** Continuous monitoring of user writing to detect when style changes (potentially indicating AI assistance or other influences).

**Example:**
```python
# Source: Based on concept drift detection research
# https://www.mdpi.com/2078-2489/15/12/786
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from collections import deque

class StyleDriftDetector:
    """Detect significant style drift from fingerprint baseline."""

    def __init__(
        self,
        window_size: int = 10,
        drift_threshold: float = 2.0,
        alert_threshold: float = 3.0
    ):
        """
        Args:
            window_size: Number of recent samples to analyze
            drift_threshold: Standard deviations for "warning" level
            alert_threshold: Standard deviations for "alert" level
        """
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        self.alert_threshold = alert_threshold

        # Sliding window of recent similarities
        self.similarity_window = deque(maxlen=window_size)

        # Baseline statistics
        self.baseline_mean = None
        self.baseline_std = None
        self.baseline_established = False

        # Track feature-level drift
        self.feature_history = {}

    def establish_baseline(self, similarities: List[float]) -> None:
        """
        Establish baseline from initial samples.

        Args:
            similarities: List of similarity scores from known-good samples
        """
        self.baseline_mean = np.mean(similarities)
        self.baseline_std = np.std(similarities)
        self.baseline_established = True

    def check_drift(
        self,
        similarity: float,
        feature_deviations: Dict = None,
        timestamp: datetime = None
    ) -> Dict:
        """
        Check if current sample indicates style drift.

        Args:
            similarity: Current similarity score
            feature_deviations: Deviations per feature
            timestamp: When sample was analyzed

        Returns:
            {
                "drift_detected": bool,
                "severity": "none" | "warning" | "alert",
                "z_score": float,
                "similarity": float,
                "baseline_mean": float,
                "changed_features": List[str]
            }
        """
        if not self.baseline_established:
            return {
                "drift_detected": False,
                "severity": "none",
                "reason": "baseline_not_established"
            }

        # Add to sliding window
        self.similarity_window.append(similarity)

        # Calculate z-score
        if self.baseline_std > 0:
            z_score = (self.baseline_mean - similarity) / self.baseline_std
        else:
            z_score = 0

        # Determine severity
        if abs(z_score) >= self.alert_threshold:
            severity = "alert"
            drift_detected = True
        elif abs(z_score) >= self.drift_threshold:
            severity = "warning"
            drift_detected = True
        else:
            severity = "none"
            drift_detected = False

        # Identify most changed features
        changed_features = self._analyze_feature_changes(feature_deviations)

        return {
            "drift_detected": drift_detected,
            "severity": severity,
            "z_score": float(z_score),
            "similarity": similarity,
            "baseline_mean": float(self.baseline_mean),
            "confidence_interval": [
                float(self.baseline_mean - self.drift_threshold * self.baseline_std),
                float(self.baseline_mean + self.drift_threshold * self.baseline_std)
            ],
            "changed_features": changed_features,
            "timestamp": timestamp or datetime.utcnow()
        }

    def _analyze_feature_changes(self, feature_deviations: Dict) -> List[Dict]:
        """Analyze which features changed most significantly."""
        if not feature_deviations:
            return []

        changes = []
        for feature_name, deviation_info in feature_deviations.items():
            changes.append({
                "feature": feature_name,
                "current_value": deviation_info["text_value"],
                "baseline_value": deviation_info["fingerprint_value"],
                "normalized_deviation": deviation_info["deviation"]
            })

        # Sort by normalized deviation
        return sorted(changes, key=lambda x: x["normalized_deviation"], reverse=True)

    def update_baseline(self, new_similarities: List[float]) -> None:
        """
        Update baseline with new data (e.g., after confirmed style evolution).

        Args:
            new_similarities: New similarity scores to incorporate
        """
        all_similarities = list(self.similarity_window) + new_similarities
        self.baseline_mean = np.mean(all_similarities)
        self.baseline_std = np.std(all_similarities)
```

### Pattern 4: Multi-Document Corpus Builder

**What:** Aggregate writing samples from multiple documents to build robust fingerprint, handling different document types.

**When to use:** User has multiple writing samples (10+) from different sources/contexts.

**Example:**
```python
# Source: Based on corpus-based authorship verification research
# https://www.researchgate.net/publication/348171080_Authorship_Identification_Using_Stylometry_and_Document_Fingerprinting
from typing import List, Dict, Optional
from datetime import datetime
import numpy as np
from app.ml.feature_extraction import extract_feature_vector, FEATURE_NAMES

class FingerprintCorpusBuilder:
    """Build robust fingerprints from multi-document corpora."""

    # Minimum samples for robust fingerprint
    MIN_SAMPLES_FOR_FINGERPRINT = 10

    def __init__(self):
        self.samples = []  # List of (features, timestamp, source_type)
        self.feature_scaler = None  # sklearn scaler for normalization

    def add_sample(
        self,
        text: str,
        source_type: str = "manual",
        timestamp: Optional[datetime] = None
    ) -> Dict:
        """
        Add a writing sample to the corpus.

        Args:
            text: Writing sample text
            source_type: 'email', 'essay', 'blog', 'document', etc.
            timestamp: When written (for time-weighting)

        Returns:
            Sample metadata with extracted features
        """
        if not text or not text.strip():
            raise ValueError("Text sample cannot be empty")

        # Extract features
        features = extract_feature_vector(text)

        sample = {
            "features": features,
            "timestamp": timestamp or datetime.utcnow(),
            "source_type": source_type,
            "word_count": len(text.split()),
            "raw_features": extract_all_features(text)
        }

        self.samples.append(sample)
        return sample

    def build_fingerprint(
        self,
        method: str = "time_weighted",
        alpha: float = 0.3
    ) -> Dict:
        """
        Build fingerprint from corpus samples.

        Args:
            method: 'average', 'time_weighted', or 'source_weighted'
            alpha: EMA parameter for time_weighted method

        Returns:
            Fingerprint dictionary with metadata
        """
        if len(self.samples) < self.MIN_SAMPLES_FOR_FINGERPRINT:
            raise ValueError(
                f"Need at least {self.MIN_SAMPLES_FOR_FINGERPRINT} samples; "
                f"have {len(self.samples)}"
            )

        # Sort by timestamp for time-weighted methods
        sorted_samples = sorted(self.samples, key=lambda s: s["timestamp"])

        if method == "time_weighted":
            return self._build_time_weighted(sorted_samples, alpha)
        elif method == "average":
            return self._build_average()
        elif method == "source_weighted":
            return self._build_source_weighted()
        else:
            raise ValueError(f"Unknown method: {method}")

    def _build_time_weighted(
        self,
        sorted_samples: List[Dict],
        alpha: float
    ) -> Dict:
        """Build fingerprint using exponential moving average."""
        trainer = TimeWeightedFingerprintBuilder(alpha=alpha)

        for sample in sorted_samples:
            trainer.add_sample(sample["features"], sample["timestamp"])

        fingerprint = trainer.get_fingerprint()

        # Add corpus metadata
        fingerprint.update({
            "corpus_size": len(self.samples),
            "date_range": {
                "earliest": sorted_samples[0]["timestamp"].isoformat(),
                "latest": sorted_samples[-1]["timestamp"].isoformat()
            },
            "source_distribution": self._get_source_distribution(),
            "average_word_count": np.mean([s["word_count"] for s in self.samples])
        })

        return fingerprint

    def _build_average(self) -> Dict:
        """Build fingerprint using simple average."""
        all_features = np.array([s["features"] for s in self.samples])
        mean_vector = np.mean(all_features, axis=0)

        # Calculate per-feature statistics for confidence intervals
        std_vector = np.std(all_features, axis=0)

        feature_stats = {}
        for i, (mean, std) in enumerate(zip(mean_vector, std_vector)):
            feature_stats[i] = {
                "mean": float(mean),
                "std": float(std),
                "variance": float(std ** 2),
                "count": len(self.samples)
            }

        return {
            "feature_vector": mean_vector.tolist(),
            "feature_statistics": feature_stats,
            "sample_count": len(self.samples),
            "method": "average"
        }

    def _build_source_weighted(self) -> Dict:
        """Build fingerprint weighting by source type reliability."""
        # Define source weights (formal writing more reliable for fingerprint)
        source_weights = {
            "essay": 1.2,
            "academic": 1.3,
            "blog": 1.0,
            "email": 0.9,
            "document": 1.1,
            "manual": 1.0
        }

        weighted_sum = np.zeros(len(FEATURE_NAMES))
        total_weight = 0

        for sample in self.samples:
            weight = source_weights.get(sample["source_type"], 1.0)
            weighted_sum += weight * sample["features"]
            total_weight += weight

        fingerprint_vector = weighted_sum / total_weight if total_weight > 0 else weighted_sum

        return {
            "feature_vector": fingerprint_vector.tolist(),
            "sample_count": len(self.samples),
            "method": "source_weighted"
        }

    def _get_source_distribution(self) -> Dict[str, int]:
        """Get count of samples by source type."""
        distribution = {}
        for sample in self.samples:
            source = sample["source_type"]
            distribution[source] = distribution.get(source, 0) + 1
        return distribution

    def get_corpus_summary(self) -> Dict:
        """Get summary of corpus without building fingerprint."""
        if not self.samples:
            return {"sample_count": 0}

        return {
            "sample_count": len(self.samples),
            "total_words": sum(s["word_count"] for s in self.samples),
            "source_distribution": self._get_source_distribution(),
            "ready_for_fingerprint": len(self.samples) >= self.MIN_SAMPLES_FOR_FINGERPRINT
        }
```

### Anti-Patterns to Avoid

- **Equal weighting for all samples:** Ignores style evolution over time. Use time-weighted (EMA) approach.
- **Static similarity thresholds:** Different users have different natural variation. Use baseline-relative detection with confidence intervals.
- **Hard drift boundaries:** Style evolves gradually. Use statistical thresholds (z-scores) rather than fixed cutoffs.
- **Ignoring feature correlation:** Some stylometric features correlate (burstiness/sentence complexity). Consider multivariate approaches.
- **Single-sample fingerprints:** One sample is insufficient for robust fingerprinting. Require 10+ samples.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Feature normalization | Manual min-max scaling | sklearn.preprocessing.StandardScaler/MinMaxScaler | Handles edge cases, fits/transforms consistently |
| Cosine similarity | Manual dot product | sklearn.metrics.pairwise.cosine_similarity | Handles edge cases, batch processing |
| Confidence intervals | Manual z-score calc | scipy.stats.norm.interval | Proper statistical functions |
| EMA calculation | Manual loop | pandas.Series.ewm() for dataframes | Optimized, handles missing data |
| Feature importance ranking | Manual variance calc | sklearn.inspection.permutation_importance | Model-agnostic, handles correlation |

**Key insight:** Scikit-learn and scipy provide production-ready implementations of statistical operations. Custom implementations often miss edge cases and statistical nuances.

## Common Pitfalls

### Pitfall 1: Insufficient Corpus Size

**What goes wrong:** Fingerprints built from few samples (<10) are unstable and produce high false-positive drift alerts.

**Why it happens:** Natural writing variation within a single author can exceed variation between authors with small sample sizes.

**How to avoid:**
- Require minimum 10 samples before generating fingerprint
- Show progress toward minimum in UI
- Provide clear messaging when corpus is insufficient

**Warning signs:** High similarity variance (>0.15) within same-author samples.

### Pitfall 2: Overfitting to Specific Document Types

**What goes wrong:** Fingerprint trained only on emails flags essays as "drift" due to different stylistic norms.

**Why it happens:** Different document types have different conventions (formality, sentence length, etc.).

**How to avoid:**
- Track document type per sample
- Build separate fingerprints per document type if significant variance
- Use source-weighted averaging to favor formal writing

**Warning signs:** Systematic drift alerts correlated with document type.

### Pitfall 3: Confusing Style Evolution with Drift

**What goes wrong:** Natural style improvement over time flagged as problematic drift.

**Why it happens:** Writing style naturally evolves; gradual improvement should not trigger alerts.

**How to avoid:**
- Use EMA with moderate alpha (0.2-0.3) to adapt to gradual change
- Only alert on sudden, significant deviations (z-score > 2-3)
- Allow users to acknowledge drift and update baseline

**Warning signs:** Persistent low-level drift alerts over long periods.

### Pitfall 4: Ignoring Seasonal/Contextual Variation

**What goes wrong:** Academic writing during semester differs from summer casual writing; flagged as drift.

**Why it happens:** Writing context affects style (academic vs casual, stressed vs relaxed).

**How to avoid:**
- Track temporal patterns in alerts
- Consider time-of-year context in drift detection
- Allow users to set "expected variation" periods

**Warning signs:** Periodic drift alerts at regular intervals.

### Pitfall 5: Uncalibrated Confidence Intervals

**What goes wrong:** Reported 95% confidence interval only contains true value 70% of time.

**Why it happens:** Assumption of normality may not hold; feature variance may be underestimated.

**How to avoid:**
- Use empirical confidence intervals from sample history when possible
- Validate calibration on held-out data
- Report uncertainty honestly

**Warning signs:** Alerts consistently outside confidence bounds.

## Code Examples

Verified patterns from official sources:

### Feature Normalization for Fingerprints

```python
# Source: https://scikit-learn.org/stable/modules/preprocessing.html
from sklearn.preprocessing import StandardScaler
import numpy as np

class FingerprintNormalizer:
    """Normalize features for fingerprint comparison."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.fitted = False

    def fit(self, feature_vectors: np.ndarray) -> None:
        """
        Fit scaler to feature vectors.

        Args:
            feature_vectors: Array of shape (n_samples, n_features)
        """
        self.scaler.fit(feature_vectors)
        self.fitted = True

    def transform(self, features: np.ndarray) -> np.ndarray:
        """Normalize features using fitted scaler."""
        if not self.fitted:
            raise ValueError("Scaler not fitted. Call fit() first.")
        return self.scaler.transform(features.reshape(1, -1))[0]

    def fit_transform(self, feature_vectors: np.ndarray) -> np.ndarray:
        """Fit and transform in one step."""
        return self.scaler.fit_transform(feature_vectors)
```

### Database Schema for Enhanced Fingerprinting

```python
# Source: Extended from existing database.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from datetime import datetime

class FingerprintSample(Base):
    """Individual writing samples for corpus building."""
    __tablename__ = "fingerprint_samples"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    text_content = Column(Text, nullable=False)
    source_type = Column(String, nullable=False)  # email, essay, blog, etc.
    features = Column(JSON, nullable=False)  # 27 stylometric features
    word_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    written_at = Column(DateTime, nullable=True)  # When text was originally written

    # Relationships
    user = relationship("User", back_populates="fingerprint_samples")


class EnhancedFingerprint(Base):
    """Enhanced fingerprint with corpus support."""
    __tablename__ = "enhanced_fingerprints"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    feature_vector = Column(JSON, nullable=False)
    feature_statistics = Column(JSON, nullable=True)  # For confidence intervals
    corpus_size = Column(Integer, default=0, nullable=False)
    method = Column(String, default="time_weighted", nullable=False)  # EMA method
    alpha = Column(Float, default=0.3, nullable=False)  # EMA parameter
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_distribution = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="enhanced_fingerprints")


class DriftAlert(Base):
    """Style drift detection alerts."""
    __tablename__ = "drift_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fingerprint_id = Column(Integer, ForeignKey("enhanced_fingerprints.id"), nullable=False)
    severity = Column(String, nullable=False)  # warning, alert
    similarity_score = Column(Float, nullable=False)
    baseline_similarity = Column(Float, nullable=False)
    z_score = Column(Float, nullable=False)
    changed_features = Column(JSON, nullable=True)  # Features that changed most
    acknowledged = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="drift_alerts")
    fingerprint = relationship("EnhancedFingerprint", back_populates="drift_alerts")
```

### Drift Detection API Endpoint

```python
# Source: Based on FastAPI patterns
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.ml.fingerprint.drift_detector import StyleDriftDetector

router = APIRouter(prefix="/api/fingerprint", tags=["fingerprint"])

@router.post("/check-drift")
async def check_drift(
    text: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Check if text indicates style drift from user's fingerprint.

    Returns:
        {
            "drift_detected": bool,
            "severity": "warning" | "alert" | "none",
            "similarity": float,
            "confidence_interval": [float, float],
            "changed_features": [...]
        }
    """
    # Get user's fingerprint
    fingerprint = db.query(EnhancedFingerprint).filter(
        EnhancedFingerprint.user_id == current_user.id
    ).first()

    if not fingerprint:
        raise HTTPException(
            status_code=404,
            detail="Fingerprint not found. Build a corpus first."
        )

    # Extract features from text
    text_features = extract_feature_vector(text)

    # Get drift detector for user
    detector = get_drift_detector(current_user.id, db)

    # Check drift
    result = detector.check_drift(
        similarity=compare_to_fingerprint(text, fingerprint),
        feature_deviations=compute_feature_deviations(text_features, fingerprint)
    )

    # Create alert if drift detected
    if result["drift_detected"]:
        create_drift_alert(current_user.id, fingerprint.id, result, db)

    return result
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-sample fingerprint | Corpus-based (10+ samples) | 2025 | More robust fingerprints, reduced false positives |
| Equal sample weighting | Time-weighted (EMA) | 2024-2025 | Accounts for style evolution while maintaining patterns |
| Static similarity thresholds | Dynamic thresholds with confidence intervals | 2025 | Better adaptation to individual variation |
| Simple drift alerts | Statistical drift detection with feature attribution | 2025 | More actionable alerts with specific changes highlighted |

**Recent Research (2025):**
- **Stylometric Fingerprinting with Contextual Anomaly Detection:** Combines fingerprinting with anomaly detection for AI vs human text distinction
- **Residualized Similarity (EMNLP 2025):** Sets cosine similarity threshold at 0.5 for authorship verification
- **OLC-WA (2025):** Online classification with weighted average for drift-aware adaptation

**Deprecated/outdated:**
- **Single-document fingerprinting:** Insufficient for robust authorship verification
- **Fixed similarity thresholds:** Don't account for individual writing variation
- **Binary drift alerts:** Modern approaches use severity levels with feature attribution

## Open Questions

1. **Optimal corpus composition:** What mix of document types produces most robust fingerprint? Current plan accepts mixed sources but weights formal writing higher. This should be validated empirically.

2. **EMA alpha calibration:** Research suggests 0.2-0.3 for balanced recency, but optimal value may vary by user and writing frequency. Consider adaptive alpha based on sample rate.

3. **Minimum sample requirements:** Current plan requires 10 samples. Some research suggests 5-20 depending on feature dimensionality. Should adjust based on feature variance.

4. **Feature subset selection:** All 27 features may not be equally informative for fingerprinting. Consider feature selection based on within-author vs between-author variance ratio.

5. **Multi-language support:** Current stylometric features assume English grammar/style. Fingerprinting other languages requires language-specific feature extraction.

6. **Drift alert cadence:** How frequently should drift alerts be triggered? Too frequent = notification fatigue; too infrequent = missed issues.

## Sources

### Primary (HIGH confidence)

- [scikit-learn Preprocessing Documentation](https://scikit-learn.org/stable/modules/preprocessing.html) - StandardScaler, MinMaxScaler official API
- [scikit-learn Permutation Importance](https://scikit-learn.org/stable/modules/permutation_importance.html) - Feature importance calculation methods
- [scikit-learn Gaussian Processes](https://scikit-learn.org/stable/modules/gaussian_process.html) - Probabilistic predictions and confidence intervals

### Secondary (MEDIUM confidence)

- [Residualized Similarity for Explainable Authorship Verification (EMNLP 2025)](https://aclanthology.org/2025.findings-emnlp.856.pdf) - Sets 0.5 threshold for cosine similarity
- [Combining Style and Semantics for Robust Authorship Verification (2025)](https://www.sciencedirect.com/science/article/pii/S266682702500115X) - Cosine distance for stylistic consistency
- [CROSSNEWS: Cross-Genre Authorship Verification (AAAI 2025)](https://ojs.aaai.org/index.php/AAAI/article/view/34659/36814) - Dynamic similarity thresholds
- [A Systematic Review of Concept Drift Detection (2024)](https://www.mdpi.com/2078-2489/15/12/786) - Drift detection methodology
- [Calibrated and Sharp Uncertainties in Deep Learning (2022)](https://proceedings.mlr.press/v162/kuleshov22a/kuleshov22a.pdf) - Confidence interval theory

### Tertiary (LOW confidence)

- [Authorship Identification Using Stylometry and Document Fingerprinting (2025)](https://www.researchgate.net/publication/348171080_Authorship_Identification_Using_Stylometry_and_Document_Fingerprinting) - Continuous authentication approach
- [Stylometric Fingerprinting with Contextual Anomaly Detection (2025)](https://www.preprints.org/manuscript/202503.1770) - AI vs human text detection
- [Exponential Moving Average of Weights in Deep Learning (2024)](https://arxiv.org/abs/2411.18704) - EMA theory and application
- [OLC-WA: Drift Aware Tuning-Free Online Classification (2025)](https://www.sciencedirect.com/science/article/abs/pii/S095741742504463X) - Online drift detection

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - scikit-learn and scipy are well-established with stable APIs
- Architecture patterns: MEDIUM - EMA and cosine similarity are standard, but stylometric fingerprinting specifically is niche
- Drift detection: MEDIUM - General concept drift research is solid, but writing-style drift specifically is less standardized
- Threshold values: LOW - Similarity thresholds (0.5-0.85) from research but may require calibration per-user

**Research date:** 2026-01-19
**Valid until:** 30 days (ML preprocessing techniques stable, but authorship verification research evolving)

**Project context:**
- Existing 27-feature extraction in `app/ml/feature_extraction.py`
- Existing basic fingerprint module in `app/ml/fingerprint.py` (simple average only)
- Existing Fingerprint and WritingSample tables in database
- Target: Enhance with corpus building, time-weighted training, drift detection, and confidence intervals
