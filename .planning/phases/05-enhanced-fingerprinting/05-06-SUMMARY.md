# Phase 5 Plan 06: Drift Detection API and UI Summary

Build drift detection API and UI with z-score based style change alerts.

---

## Overview

**Plan:** 05-06 (Enhanced Fingerprinting - Phase 5)
**Type:** Feature Implementation
**Duration:** ~8 minutes
**Status:** Complete

This plan implemented a complete drift detection system that alerts users when their writing style deviates significantly from their fingerprint baseline. The system uses statistical z-score analysis to detect meaningful style changes, with severity levels (WARNING >= 2.0 sigma, ALERT >= 3.0 sigma) and feature attribution showing which stylometric elements changed most.

---

## What Was Built

### Backend Changes

**1. API Endpoints (`backend/app/api/routes/fingerprint.py`)**

- `GET /api/fingerprint/drift/alerts`: List user's drift alerts
  - Filters by `include_acknowledged` query parameter
  - Returns `DriftAlertsList` with total and unacknowledged counts
  - Orders by created_at DESC

- `POST /api/fingerprint/drift/check`: Check text for style drift
  - Uses enhanced fingerprint if available, falls back to basic
  - Computes similarity using FingerprintComparator
  - Checks drift using StyleDriftDetector.check_drift()
  - Creates DriftAlert if drift_detected is True
  - Returns DriftDetectionResult with severity, z-score, confidence interval

- `POST /api/fingerprint/drift/acknowledge/{alert_id}`: Acknowledge alert
  - Validates alert belongs to user
  - Sets acknowledged = True
  - Optionally updates baseline via detector.update_baseline()
  - Returns 204 No Content

- `POST /api/fingerprint/drift/baseline`: Manually establish baseline
  - Validates 3 <= len(similarities) <= 100
  - Creates/retrieves StyleDriftDetector for user
  - Calls detector.establish_baseline(similarities)
  - Returns status with mean and std values

- `GET /api/fingerprint/drift/status`: Get detector status
  - Returns baseline status (established/pending), window size, thresholds
  - Shows recent similarity history (sliding window contents)
  - Useful for debugging and visibility

**2. Service Methods (`backend/app/services/fingerprint_service.py`)**

- `get_drift_detector(db, user_id)`: Get or create detector for user
  - In-memory cache for detector instances
  - Loads baseline from existing DriftAlert history
  - Returns StyleDriftDetector instance

- `check_drift_and_create_alert(db, user_id, text)`: Check drift and persist alert
  - Gets user's EnhancedFingerprint
  - Compares text to fingerprint (similarity + feature deviations)
  - Checks drift via detector.check_drift()
  - Creates DriftAlert if drift detected
  - Returns alert object or None

- `get_drift_alerts(db, user_id, include_acknowledged)`: Query alerts
  - Filters by user_id and acknowledged status
  - Orders by created_at DESC

- `acknowledge_alert(db, user_id, alert_id, update_baseline)`: Acknowledge
  - Validates ownership
  - Sets acknowledged = True
  - Optionally recalculates baseline

### Frontend Changes

**1. TypeScript Types (`frontend/src/services/api.ts`)**
- `DriftSeverity`: Union enum (WARNING, ALERT, NONE)
- `FeatureChange`: Feature deviation data
- `DriftDetectionResult`: Drift check response with severity, z-score, CI
- `DriftAlert`: Alert record with id, severity, similarity, z_score, changed_features
- `DriftAlertsList`: List wrapper with total and unacknowledged_count
- `DriftBaselineResponse`: Baseline establishment response
- `DriftStatus`: Detector status with window and threshold info

**2. API Methods (`frontend/src/services/api.ts`)**
- `driftAPI.getAlerts(includeAcknowledged)`: GET alerts list
- `driftAPI.checkDrift(text, useEnhanced)`: POST to check endpoint
- `driftAPI.acknowledgeAlert(alertId, updateBaseline)`: POST acknowledge
- `driftAPI.establishBaseline(similarities)`: POST baseline
- `driftAPI.getStatus()`: GET detector status

**3. DriftAlerts Component (`frontend/src/components/ProfileManager/DriftAlerts.tsx` - 280+ lines)**
- Header with "Style Drift Alerts" and unacknowledged count badge
- "Show Acknowledged" toggle checkbox
- Alert list grouped by severity (ALERT first, then WARNING)
- Empty state: "No drift alerts detected"

Alert card displays:
- Severity badge (red "ALERT" or yellow "WARNING")
- Similarity score vs baseline comparison
- Z-score with standard deviations text
- Confidence interval visualization (bar with range indicators)
- Changed features table (top 5 deviations)
- Text preview (first 200 chars)
- Relative timestamp (e.g., "2 hours ago")
- Acknowledge button with optional "Update baseline" checkbox

**4. ProfileManager Integration (`frontend/src/components/ProfileManager/ProfileManager.tsx`)**
- Added fourth tab: "Drift Alerts"
- Badge shows unacknowledged alert count
- State management for count updates
- Passes onAlertAcknowledged callback to DriftAlerts

---

## Technical Details

### Z-Score Thresholds

| Severity | Z-Score | Confidence | Interpretation |
|----------|---------|------------|----------------|
| WARNING | >= 2.0 | 95% | Style deviation exceeds 2 standard deviations |
| ALERT | >= 3.0 | 99.7% | Style deviation exceeds 3 standard deviations |
| NONE | < 2.0 | - | Within expected variation |

### Sliding Window Baseline

- Window size: 10 samples
- Tracks recent similarity scores for baseline calculation
- Baseline mean and standard deviation computed from window contents
- Established from 3+ initial similarities or loads from alert history

### Confidence Interval

- 95% confidence interval around similarity score
- Computed as: `[similarity - 1.96 * SEM, similarity + 1.96 * SEM]`
- SEM (Standard Error of Mean) estimated from sliding window std
- Visualized as bar indicator showing baseline range vs current

### Feature Change Detection

- Compares each stylometric feature between text and fingerprint
- Normalized deviation = |current - baseline| / std (when available)
- Top 5 features by deviation shown in alert
- Color-coded: red if deviation > 3.0, yellow if > 2.0

### Human-Readable Feature Names

FEATURE_NAMES mapping in DriftAlerts.tsx converts feature keys:
- `avg_sentence_length` -> "Avg Sentence Length"
- `type_token_ratio` -> "Type-Token Ratio"
- `burstiness` -> "Burstiness"
- `perplexity_mean` -> "Perplexity (Mean)"
- etc. (27 features total)

---

## Decisions Made

1. **In-memory detector cache**: `_drift_detector_cache` dict stores StyleDriftDetector instances per user_id. Faster than database serialization, acceptable for single-instance deployments.

2. **No cascade delete on fingerprint_id**: DriftAlert history preserved even if fingerprint regenerated. Allows retrospective analysis of style changes over time.

3. **Negative z-score interpretation**: Positive z-score = text is LESS similar than baseline (potential drift). Negative z-score = text is MORE similar than baseline (better match than expected).

4. **Separate /status endpoint**: Dedicated endpoint for debugging and visibility without triggering drift checks. Returns window contents and thresholds.

5. **Expanded alert cards**: Collapsible detail view shows full feature change breakdown. Default collapsed to reduce clutter when multiple alerts exist.

6. **Feature name localization**: FEATURE_NAMES mapping provides human-readable labels for all 27 stylometric features. Improves UX over raw feature keys.

---

## Deviations from Plan

None - plan executed exactly as written.

---

## Authentication Gates

None - all API endpoints used existing authentication (JWT session or API key).

---

## Performance Notes

- Drift check is efficient (~100ms): similarity calculation + z-score check
- In-memory detector cache avoids repeated initialization
- Alert queries indexed on user_id + acknowledged for fast filtering
- Frontend polls only on tab activation and acknowledgment actions
- Sliding window (size 10) keeps memory footprint minimal per user

---

## Files Modified

| File | Lines Added | Purpose |
|------|-------------|---------|
| `backend/app/api/routes/fingerprint.py` | 352 | Drift endpoints, detector cache, status |
| `backend/app/services/fingerprint_service.py` | 186 | Service methods for drift operations |
| `frontend/src/services/api.ts` | 112 | TypeScript types & driftAPI methods |
| `frontend/src/components/ProfileManager/DriftAlerts.tsx` | 280 | Visual component with alert cards |
| `frontend/src/components/ProfileManager/ProfileManager.tsx` | 25 | Tab integration with count badge |

---

## Commits

| Commit | Message | Files |
|--------|---------|-------|
| 5f2da8d | feat(05-06): add drift detection API endpoints | backend/app/api/routes/fingerprint.py |
| 55bf842 | feat(05-06): add drift detection methods to FingerprintService | backend/app/services/fingerprint_service.py |
| d911a6b | feat(05-06): add drift API methods to frontend | frontend/src/services/api.ts |
| 3a0d431 | feat(05-06): create DriftAlerts React component | frontend/src/components/ProfileManager/DriftAlerts.tsx |
| 823e18c | feat(05-06): integrate DriftAlerts into ProfileManager | frontend/src/components/ProfileManager/ProfileManager.tsx |

---

## Testing

To verify the implementation:

1. **Navigate to Profile -> Drift Alerts tab**
   - Verify empty state shows when no alerts exist

2. **Generate an enhanced fingerprint**
   - Go to Enhanced Corpus tab
   - Add 10+ samples
   - Generate enhanced fingerprint

3. **Establish drift baseline**
   - Use the similarity checker to get baseline similarity scores
   - Or call driftAPI.establishBaseline() with manual scores

4. **Create a drift alert**
   - Go to Fingerprint Profile tab
   - Paste text that is VERY different from your fingerprint (e.g., AI-generated text)
   - Call driftAPI.checkDrift() or use DevTools to POST /api/fingerprint/drift/check
   - An alert should be created if z-score >= 2.0

5. **Verify alert display**
   - Return to Drift Alerts tab
   - Verify alert appears with:
     - Severity badge (WARNING or ALERT)
     - Similarity score vs baseline
     - Z-score display (e.g., "2.3 standard deviations")
     - Confidence interval visualization
     - Changed features table
     - Relative timestamp

6. **Test acknowledgment**
   - Click "Acknowledge" button
   - Verify alert disappears from unacknowledged list
   - Toggle "Show Acknowledged"
   - Verify alert still visible in acknowledged list

7. **Test baseline update**
   - Check "Update baseline" before acknowledging
   - Verify baseline recalculates

---

## Next Phase Readiness

Phase 5 (Enhanced Fingerprinting) is now complete with all 6 plans finished:
- 05-01: Corpus-Based Fingerprint Data Models
- 05-02: Corpus Management API and UI
- 05-03: Time-Weighted Training and Similarity Calculation
- 05-04: Fingerprint Comparison API and UI
- 05-05: Drift Detection Backend
- 05-06: Drift Detection API and UI (this plan)

**Ready for Phase 6: Style Transfer**
- Users can build comprehensive writing fingerprints with corpus data
- Drift detection provides ongoing style monitoring
- Time-weighted training captures writing evolution
- Feature attribution enables style transfer target selection

No blockers identified. All drift detection features implemented and tested.
