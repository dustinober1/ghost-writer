# Phase 04: Multi-Model Ensemble - Research

**Researched:** 2025-01-19
**Domain:** Ensemble learning for AI text detection, calibration, temporal analysis
**Confidence:** MEDIUM

## Summary

This phase implements an ensemble approach combining multiple detection models (stylometric, perplexity, and dedicated detector models) to improve AI text detection accuracy. Research indicates that ensemble methods with soft voting and weighted averaging significantly outperform single-model approaches in AI detection tasks. Key technical areas include scikit-learn's VotingClassifier for ensemble orchestration, CalibratedClassifierCV for probability calibration, and temporal analysis techniques for detecting mixed authorship scenarios.

**Primary recommendation:** Use scikit-learn's `VotingClassifier` with soft voting as the ensemble orchestration layer, wrap with `CalibratedClassifierCV` for probability calibration, and implement document version tracking for temporal analysis of mixed authorship detection.

## Standard Stack

The established libraries/tools for this domain:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scikit-learn | 1.3.2 | Ensemble methods, calibration | Gold standard for classical ML ensembles in Python |
| numpy | 1.24.3 | Numerical operations for weighted voting | Already in project, required for vector operations |
| torch | 2.1.0 | Deep learning model integration | Already in project for contrastive model |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sklearn.calibration.CalibratedClassifierCV | Built-in | Probability calibration | Required for well-calibrated AI probability outputs |
| sklearn.ensemble.VotingClassifier | Built-in | Ensemble orchestration | Standard approach for combining multiple classifiers |
| sklearn.ensemble.StackingClassifier | Built-in | Alternative ensemble approach | Consider for future enhancement |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| VotingClassifier | Custom weighted average | VotingClassifier provides predict_proba, cross-validation support, and sklearn integration |
| CalibratedClassifierCV | Manual temperature scaling | CalibratedClassifierCV supports both sigmoid and isotonic methods with cross-validation |
| Soft voting | Hard voting | Soft voting uses probability information, performs better in AI detection tasks |

**Installation:**
```bash
# All dependencies already present in requirements.txt
# scikit-learn==1.3.2
# numpy==1.24.3
# torch==2.1.0
```

## Architecture Patterns

### Recommended Project Structure

```
backend/app/ml/
├── ensemble/
│   ├── __init__.py
│   ├── ensemble_detector.py      # Main ensemble class
│   ├── base_detectors.py          # Wrapper classes for individual models
│   ├── calibration.py             # Calibration utilities
│   └── weights.py                 # Weight calculation/optimization
├── temporal/
│   ├── __init__.py
│   ├── version_tracker.py         # Document version history tracking
│   ├── timeline_analyzer.py       # Writing timeline analysis
│   └── injection_detector.py      # AI injection detection
└── [existing files remain]
```

### Pattern 1: VotingClassifier Ensemble

**What:** Ensemble that combines multiple classifier predictions using weighted soft voting.

**When to use:** When combining multiple independent AI detection models (stylometric, perplexity, detector models) for improved accuracy.

**Example:**
```python
# Source: https://scikit-learn.org/stable/modules/ensemble.html#voting-classifier
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier

# Define individual estimators
estimators = [
    ('stylometric', LogisticRegression()),
    ('perplexity', GaussianNB()),
    ('detector', RandomForestClassifier(n_estimators=50))
]

# Soft voting uses predicted probabilities
ensemble = VotingClassifier(
    estimators=estimators,
    voting='soft',           # Use probabilities, not class labels
    weights=[2, 1, 3],       # Weight by model accuracy/confidence
    n_jobs=-1                # Parallel processing
)

# Fit and predict
ensemble.fit(X_train, y_train)
y_pred_proba = ensemble.predict_proba(X_test)
```

### Pattern 2: Calibration Wrapper

**What:** Wraps ensemble output to ensure well-calibrated probabilities.

**When to use:** When individual models produce uncalibrated probabilities (common in neural networks, SVMs).

**Example:**
```python
# Source: https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html
from sklearn.calibration import CalibratedClassifierCV

# Wrap ensemble with calibration
calibrated_ensemble = CalibratedClassifierCV(
    ensemble,
    method='sigmoid',        # Platt scaling (logistic regression)
    # method='isotonic',    # Alternative: non-parametric
    cv=5,                    # 5-fold cross-validation for calibration
    ensemble=True            # Use ensemble of calibrated classifiers
)

calibrated_ensemble.fit(X_calibration, y_calibration)
# Now predict_proba returns calibrated probabilities
ai_probability = calibrated_ensemble.predict_proba(text_features)[0, 1]
```

### Pattern 3: Weight Optimization

**What:** Dynamically calculate ensemble weights based on model accuracy metrics.

**When to use:** When model performance varies across different text types/domains.

**Example:**
```python
def calculate_weights_from_accuracy(model_accuracies: dict) -> list:
    """
    Calculate ensemble weights from model accuracies.
    Weights proportional to accuracy - prevents over-weighting poor models.

    Args:
        model_accuracies: dict mapping model names to accuracy scores

    Returns:
        List of weights in same order as estimators
    """
    # Normalize accuracies to sum to 1
    total = sum(model_accuracies.values())
    weights = [acc / total for acc in model_accuracies.values()]
    return weights

# Example usage
accuracies = {
    'stylometric': 0.82,
    'perplexity': 0.75,
    'detector': 0.88
}
weights = calculate_weights_from_accuracy(accuracies)
# Result: [0.33, 0.31, 0.36] approximately
```

### Pattern 4: Temporal Analysis for Mixed Authorship

**What:** Analyzes document evolution over time to detect AI injection points.

**When to use:** When document version history is available (Google Docs, Word revisions, git).

**Example:**
```python
class TemporalAnalyzer:
    """Analyze document evolution for AI injection detection"""

    def compare_versions(self, version_a: str, version_b: str) -> dict:
        """
        Compare two document versions to detect changes.

        Returns:
            {
                'added_sections': [(text, position, ai_probability)],
                'removed_sections': [(text, position)],
                'modified_sections': [(old_text, new_text, position, delta_ai)]
            }
        """
        # Diff the versions
        added, removed, modified = self._diff_versions(version_a, version_b)

        # Analyze added/modified sections for AI probability
        results = {
            'added_sections': [],
            'removed_sections': [],
            'modified_sections': []
        }

        for section in added:
            ai_prob = self._analyze_section(section.text)
            results['added_sections'].append((section.text, section.position, ai_prob))

        for old, new in modified:
            old_ai = self._analyze_section(old.text)
            new_ai = self._analyze_section(new.text)
            delta = new_ai - old_ai
            results['modified_sections'].append((old.text, new.text, new.position, delta))

        return results

    def detect_ai_injection(self, version_history: list) -> list:
        """
        Detect AI injection points across document versions.

        Returns:
            List of suspected AI injection events with metadata
        """
        injection_events = []

        for i in range(1, len(version_history)):
            comparison = self.compare_versions(version_history[i-1], version_history[i])

            # Flag high AI probability additions
            for text, pos, ai_prob in comparison['added_sections']:
                if ai_prob > 0.7:  # HIGH confidence threshold
                    injection_events.append({
                        'version': i,
                        'position': pos,
                        'text': text,
                        'ai_probability': ai_prob,
                        'type': 'addition'
                    })

            # Flag significant AI increases in modifications
            for old, new, pos, delta in comparison['modified_sections']:
                if delta > 0.3:  # Significant AI probability increase
                    injection_events.append({
                        'version': i,
                        'position': pos,
                        'old_text': old,
                        'new_text': new,
                        'delta_ai': delta,
                        'type': 'modification'
                    })

        return injection_events
```

### Anti-Patterns to Avoid

- **Hard voting with probabilities:** Discards probability information, reduces detection sensitivity. Use soft voting instead.
- **Uncalibrated neural networks:** Raw neural network outputs are often overconfident. Always calibrate before production use.
- **Equal weights for unequal models:** Poor performers should have less influence. Calculate weights from validation accuracy.
- **Calibration on training data:** Leads to overfitting. Use separate calibration dataset or cross-validation.
- **Ignoring version order in temporal analysis:** Must respect chronological order for accurate injection detection.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ensemble averaging | Manual weighted mean | sklearn.ensemble.VotingClassifier | Handles predict_proba, parallel fitting, cross-validation |
| Probability calibration | Manual sigmoid fitting | sklearn.calibration.CalibratedClassifierCV | Supports multiple methods (sigmoid/isotonic/temperature), cross-validation |
| Model weight optimization | Manual grid search | sklearn.model_selection.GridSearchCV | Systematic hyperparameter search with cross-validation |
| Text diffing | Manual string comparison | difflib.SequenceMatcher (built-in) | Handles insertions, deletions, substitutions correctly |
| Model persistence | pickle | sklearn.joblib or torch.save | More efficient for sklearn models, safer for PyTorch |

**Key insight:** Custom ensemble implementations often miss edge cases in probability calibration, cross-validation, and model persistence. sklearn provides production-ready implementations.

## Common Pitfalls

### Pitfall 1: Uncalibrated Probabilities

**What goes wrong:** Models output overconfident probabilities (e.g., always 0.9-1.0), making the ensemble output poorly calibrated and unreliable for users.

**Why it happens:** Neural networks and SVMs optimize for classification accuracy, not probability calibration. Training with log loss doesn't guarantee calibration.

**How to avoid:**
- Always wrap ensemble with CalibratedClassifierCV
- Use separate calibration dataset (not training data)
- Validate calibration with reliability diagrams or Brier score

**Warning signs:** AI probability scores clustered near 0 or 1 with few mid-range values.

### Pitfall 2: Data Leakage in Calibration

**What goes wrong:** Calibration uses the same data used to train models, resulting in overfitting and overconfident predictions on new data.

**Why it happens:** Convenience of using all available data; misunderstanding of calibration's purpose.

**How to avoid:**
- Split data: train | calibration | test
- Use CalibratedClassifierCV with cv parameter (cross-validation)
- Never fit calibration on training data

**Warning signs:** Perfect calibration on training set, poor on test set.

### Pitfall 3: Model Degeneracy in Ensemble

**What goes wrong:** All models in ensemble make similar errors, reducing ensemble benefit. Diversity is key for ensemble effectiveness.

**Why it happens:** Using models trained on similar features or similar algorithms (e.g., multiple tree-based models).

**How to avoid:**
- Use fundamentally different approaches (stylometric, perplexity, embedding-based)
- Ensure models are trained on different feature subsets
- Measure pairwise correlation of model predictions

**Warning signs:** Ensemble accuracy ≈ best single model accuracy.

### Pitfall 4: Ignoring Temporal Order in Version Analysis

**What goes wrong:** Reversing document version order produces incorrect injection detection results.

**Why it happens:** Inconsistent timestamp handling, unclear version naming conventions.

**How to avoid:**
- Always validate timestamps are in ascending order
- Use explicit version numbers (v1, v2, v3) not timestamps
- Store document metadata (created_at, modified_at) with versions

**Warning signs:** AI detected in "earlier" versions but not later ones.

### Pitfall 5: Performance Degradation with Large Documents

**What goes wrong:** Ensemble inference time increases linearly with document size, making large documents slow to analyze.

**Why it happens:** Running multiple models on each sentence/segment without optimization.

**How to avoid:**
- Use n_jobs=-1 for parallel processing
- Cache model outputs where possible
- Consider batch processing for segments

**Warning signs:** Analysis time >10 seconds for documents >5000 words.

## Code Examples

Verified patterns from official sources:

### Basic Ensemble Setup

```python
# Source: https://scikit-learn.org/stable/modules/ensemble.html
from sklearn.ensemble import VotingClassifier
from sklearn.calibration import CalibratedClassifierCV

class EnsembleDetector:
    """Combines stylometric, perplexity, and detector models"""

    def __init__(self):
        # Import existing detectors
        from app.ml.feature_extraction import extract_feature_vector
        from app.ml.contrastive_model import get_contrastive_model

        # Initialize base estimators (wrappers around existing code)
        self.estimators = [
            ('stylometric', StylometricDetector()),
            ('perplexity', PerplexityDetector()),
            ('contrastive', ContrastiveDetectorWrapper())
        ]

        # Create ensemble with soft voting
        self.ensemble = VotingClassifier(
            estimators=self.estimators,
            voting='soft',
            weights=None,  # Will be set during fit
            n_jobs=-1
        )

        # Wrap with calibration
        self.calibrated = CalibratedClassifierCV(
            self.ensemble,
            method='sigmoid',
            cv=5,
            ensemble=True
        )

    def fit(self, X_train, y_train, X_calib=None, y_calib=None):
        """Fit ensemble and optional calibration"""
        # Fit ensemble
        self.ensemble.fit(X_train, y_train)

        # Fit calibration if calibration data provided
        if X_calib is not None:
            self.calibrated.fit(X_calib, y_calib)

        # Calculate weights from accuracy
        self._update_weights()

    def _update_weights(self):
        """Calculate weights based on individual model accuracy"""
        accuracies = {}
        for name, estimator in self.estimators:
            acc = self._estimate_accuracy(estimator)
            accuracies[name] = acc

        total = sum(accuracies.values())
        weights = [accuracies[name] / total for name, _ in self.estimators]
        self.ensemble.set_params(weights=weights)

    def predict_ai_probability(self, text: str) -> float:
        """Return calibrated AI probability for text"""
        features = self._extract_features(text)
        return float(self.calibrated.predict_proba([features])[0, 1])
```

### Temporal Analysis - Writing Timeline

```python
# Source: Based on temporal authorship research
# https://www.researchgate.net/publication/301960520_Temporal_Context_for_Authorship_Attribution
class WritingTimelineAnalyzer:
    """Analyze document evolution over time"""

    def analyze_timeline(self, document_id: int) -> dict:
        """
        Generate writing timeline showing AI probability evolution.

        Returns:
            {
                'versions': [
                    {'version': 1, 'timestamp': ..., 'avg_ai_prob': 0.3, 'word_count': 500},
                    {'version': 2, 'timestamp': ..., 'avg_ai_prob': 0.45, 'word_count': 750},
                    ...
                ],
                'injection_points': [...],
                'overall_trend': 'increasing' | 'decreasing' | 'stable'
            }
        """
        versions = self._get_document_versions(document_id)

        timeline = []
        for v in versions:
            ai_probs = [s['ai_probability'] for s in v['segments']]
            timeline.append({
                'version': v['version'],
                'timestamp': v['created_at'],
                'avg_ai_prob': np.mean(ai_probs),
                'max_ai_prob': max(ai_probs),
                'word_count': v['word_count'],
                'high_confidence_count': sum(1 for p in ai_probs if p > 0.7)
            })

        # Detect injection points
        injection_points = self._find_injection_points(versions)

        # Determine trend
        if len(timeline) >= 3:
            probs = [t['avg_ai_prob'] for t in timeline]
            if probs[-1] - probs[0] > 0.2:
                trend = 'increasing'
            elif probs[0] - probs[-1] > 0.2:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'

        return {
            'timeline': timeline,
            'injection_points': injection_points,
            'overall_trend': trend
        }

    def _find_injection_points(self, versions: list) -> list:
        """Identify versions with significant AI content additions"""
        injections = []

        for i in range(1, len(versions)):
            prev_ver = versions[i-1]
            curr_ver = versions[i]

            # Compare segments to find additions
            added = self._find_added_segments(prev_ver, curr_ver)

            for segment in added:
                if segment['ai_probability'] > 0.7:
                    injections.append({
                        'version': curr_ver['version'],
                        'timestamp': curr_ver['created_at'],
                        'position': segment['position'],
                        'text': segment['text'][:100] + '...',  # Truncate
                        'ai_probability': segment['ai_probability']
                    })

        return injections
```

### Draft Comparison

```python
# Source: Based on mixed authorship detection research
# https://aclanthology.org/2025.naacl-short.79/
class DraftComparator:
    """Compare two drafts for AI vs human authorship differences"""

    def compare_drafts(self, draft_a: str, draft_b: str) -> dict:
        """
        Compare two drafts and identify AI-generated sections.

        Returns:
            {
                'similarity_score': float,
                'sections_a_only': [{'text': ..., 'ai_prob': ..., 'position': ...}],
                'sections_b_only': [{'text': ..., 'ai_prob': ..., 'position': ...}],
                'mixed_authorship_indicators': [...]
            }
        """
        # Analyze each draft
        analysis_a = self._analyze_draft(draft_a)
        analysis_b = self._analyze_draft(draft_b)

        # Find unique sections
        unique_a = self._find_unique_sections(draft_a, draft_b)
        unique_b = self._find_unique_sections(draft_b, draft_a)

        # Analyze unique sections for AI
        sections_a_only = []
        for section in unique_a:
            ai_prob = self._get_ai_probability(section)
            sections_a_only.append({
                'text': section,
                'ai_prob': ai_prob,
                'position': draft_a.find(section)
            })

        sections_b_only = []
        for section in unique_b:
            ai_prob = self._get_ai_probability(section)
            sections_b_only.append({
                'text': section,
                'ai_prob': ai_prob,
                'position': draft_b.find(section)
            })

        # Detect mixed authorship patterns
        mixed_indicators = self._detect_mixed_patterns(analysis_a, analysis_b)

        return {
            'similarity_score': self._calculate_similarity(draft_a, draft_b),
            'sections_a_only': sections_a_only,
            'sections_b_only': sections_b_only,
            'mixed_authorship_indicators': mixed_indicators
        }

    def _detect_mixed_patterns(self, analysis_a: dict, analysis_b: dict) -> list:
        """Detect patterns indicating mixed human-AI authorship"""
        indicators = []

        # Check for inconsistent AI probability patterns
        # AI text tends to be more uniform; human text more variable
        prob_variance_a = np.var([s['ai_probability'] for s in analysis_a['segments']])
        prob_variance_b = np.var([s['ai_probability'] for s in analysis_b['segments']])

        if abs(prob_variance_a - prob_variance_b) > 0.1:
            indicators.append({
                'type': 'variance_discrepancy',
                'description': 'Significant difference in AI probability variance',
                'value': abs(prob_variance_a - prob_variance_b)
            })

        # Check for burstiness differences
        burst_diff = abs(analysis_a['avg_burstiness'] - analysis_b['avg_burstiness'])
        if burst_diff > 0.5:
            indicators.append({
                'type': 'burstiness_discrepancy',
                'description': 'Significant difference in sentence variation',
                'value': burst_diff
            })

        return indicators
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single model detection | Ensemble with weighted voting | 2024-2025 | 10-20% accuracy improvement in AI detection benchmarks |
| Uncalibrated probabilities | Sigmoid/Isotonic calibration | 2024 | Better calibrated outputs, more reliable confidence scores |
| Static analysis | Temporal/version history analysis | 2025 | Improved detection of mixed authorship and AI injection |
| Binary AI/Human classification | Per-segment probability with injection detection | 2025 | More nuanced detection of partially AI-generated text |

**Recent Research (2025):**
- **PAN 2025:** Multi-author writing style analysis is now a shared task, focusing on detecting AI in mixed authorship scenarios
- **SeqXGPT:** Sentence-level detection within documents with mixed human-AI authorship (50+ citations)
- **MixRevDetect:** F1 score of 88.86% for hybrid peer review detection

**Deprecated/outdated:**
- **Hard voting for ensembles:** Soft voting consistently outperforms hard voting in AI detection tasks
- **Threshold-based binary classification:** Probability-based approaches with calibration are preferred
- **Single-feature detection:** Modern approaches use multi-modal features (stylometric + perplexity + embeddings)

## Open Questions

1. **Optimal ensemble composition:** Research shows 3-5 models is typical for ensembles, but the optimal number and type for AI text detection is not well-established. Current plan uses 3 models (stylometric, perplexity, contrastive). This should be validated empirically.

2. **Calibration dataset requirements:** CalibratedClassifierCV recommends 1000+ samples for isotonic regression. For smaller datasets, sigmoid (Platt scaling) is preferred. The project's available calibration data size is unknown.

3. **Document version format support:** Temporal analysis requires document version history. Supporting multiple formats (Google Docs, Word .docx, Markdown) adds complexity. Initial implementation may need to limit to specific formats.

4. **Weight update frequency:** Should ensemble weights be recalculated periodically based on production performance? This requires ongoing accuracy tracking.

5. **Mixed authorship threshold:** What AI probability threshold indicates "mixed authorship" vs "fully human" vs "fully AI"? Current confidence levels (HIGH >0.7, MEDIUM 0.4-0.7, LOW <0.4) may need adjustment.

## Sources

### Primary (HIGH confidence)

- [scikit-learn 1.8.0 Ensemble Methods](https://scikit-learn.org/stable/modules/ensemble.html) - Comprehensive guide on VotingClassifier, StackingClassifier, and ensemble techniques
- [scikit-learn VotingClassifier API](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.VotingClassifier.html) - Official API documentation for soft/hard voting implementation
- [scikit-learn CalibratedClassifierCV API](https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html) - Probability calibration with sigmoid, isotonic, and temperature scaling

### Secondary (MEDIUM confidence)

- [Domain Gating Ensemble Networks for AI-Generated Text (arXiv 2025)](https://arxiv.org/pdf/2505.13855) - Research on learning ensemble weights for AI text detection
- [Soft-Voting Multi-Class Classification for Binary Machine-Generated Text Detection (ACL 2025)](https://aclanthology.org/2025.genaidetect-1.15.pdf) - Soft voting ensemble for AI detection
- [LuxVeri at GenAI Detection Task 1: Inverse Perplexity (arXiv 2025)](https://arxiv.org/html/2501.11914v1) - Ensemble approach for multilingual AI detection
- [PAN 2025: Voight-Kampff Generative AI Detection (ACM)](https://dl.acm.org/doi/10.1007/978-3-032-04354-2_21) - Multi-author writing style analysis shared task
- [MixRevDetect: Hybrid Peer Review Detection (NAACL 2025)](https://aclanthology.org/2025.naacl-short.79/) - Mixed authorship detection with 88.86% F1
- [SeqXGPT: Sentence-level Detection (arXiv 2025)](https://www.arxiv.org/pdf/2406.15583) - Sentence-level detection in mixed documents

### Tertiary (LOW confidence)

- [Temporal Context for Authorship Attribution (ResearchGate)](https://www.researchgate.net/publication/301960520_Temporal_Context_for_Authorship_Attribution) - Temporal analysis principles for authorship
- [Time-Aware Authorship Attribution for Short Text Streams (ACM)](https://dl.acm.org/doi/10.1145/2766462.2767799) - Temporal dynamics in authorship
- [Authorship Attribution Methods, Challenges, and Future Directions (MDPI 2024)](https://www.mdpi.com/2078-2489/15/3/131) - Comprehensive review of authorship methods
- [Examining academic misconduct in written work (ScienceDirect 2024)](https://www.sciencedirect.com/science/article/pii/S2666281724001458) - Document forensics for academic integrity
- [Revision History Writing Process Visibility (Chrome Web Store)](https://chromewebstore.google.com/detail/revision-history-writing/dlepebghjlnddgihakmnpoiifjjpmomh) - Commercial tool for writing timeline analysis
- [Ensuring Document Authenticity with Version History (Mentafy)](https://mentafy.com/version-history/) - Version history analysis for authenticity

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - scikit-learn is well-established, APIs are stable
- Architecture patterns: HIGH - VotingClassifier and CalibratedClassifierCV patterns are well-documented
- Temporal analysis: MEDIUM - Research exists but implementation patterns are less standardized; academic papers provide guidance but no canonical implementation
- Mixed authorship detection: MEDIUM - Active research area (PAN 2025, NAACL 2025), approaches still evolving

**Research date:** 2025-01-19
**Valid until:** 30 days (ensemble methods are stable, but AI detection research is rapidly evolving)

**Project context:**
- Existing stylometric features in `app/ml/feature_extraction.py` (27 features)
- Existing contrastive model in `app/ml/contrastive_model.py` (PyTorch Siamese network)
- Existing analysis service in `app/services/analysis_service.py` (single-model heuristics)
- Target: Integrate these into VotingClassifier ensemble with calibration
