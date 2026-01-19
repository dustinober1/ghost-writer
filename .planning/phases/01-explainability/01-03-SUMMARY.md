---
phase: 01-explainability
plan: 03
subsystem: Explainability / Natural Language Explanations
tags: natural-language-explanations, template-based-explanation, document-summary, sentence-explanation, explainability-ui

# Dependency graph
requires:
  - phase: 01-explainability/01-01
    provides: confidence-level-categorization, three-tier-system
  - phase: 01-explainability/01-02
    provides: feature-attribution, heuristic-importance-scoring, feature-interpretations
provides:
  - Document-level natural language explanations (2-3 sentences)
  - Sentence-level natural language explanations (1-2 sentences)
  - Template-based explanation generation (no LLM required)
  - Frontend UI for displaying explanations
affects: future-explainability-plans

# Tech tracking
tech-stack:
  added: None
  patterns:
    - Template-based explanation generation
    - Feature pattern aggregation across segments
    - Confidence-level-specific explanation styles
    - Two-tier explanation system (document + sentence)

key-files:
  created: []
  modified:
    - backend/app/services/analysis_service.py (added explanation generation methods)
    - backend/app/models/schemas.py (added explanation fields to schemas)
    - backend/app/api/routes/analysis.py (pass through explanations in API)
    - frontend/src/components/HeatMap/HeatMap.tsx (added explanation UI)

key-decisions:
  - Template-based explanations vs LLM generation (templates are faster, deterministic, no external dependencies)
  - Three-tier explanation styles (HIGH/MEDIUM/LOW) matching confidence levels
  - Feature pattern descriptions for 20+ stylometric features
  - Document explanation placement (prominent but below main score)
  - Sentence explanation placement (in sidebar, near top)

patterns-established:
  - Template-based natural language generation from structured data
  - Feature importance aggregation across high-confidence segments
  - Graceful degradation for missing explanation data

# Metrics
duration: 4min
completed: 2025-01-19
---

# Phase 1 Plan 03: Natural Language Explanations Summary

**Template-based natural language explanation system with document-level summaries and sentence-level specific explanations using feature attribution data**

## Performance

- **Duration:** 4 minutes (254 seconds)
- **Started:** 2026-01-19T13:45:04Z
- **Completed:** 2026-01-19T13:49:18Z
- **Tasks:** 4 completed
- **Files modified:** 4

## Accomplishments

- Implemented document-level explanation generation that summarizes overall AI assessment with 2-3 sentences
- Implemented sentence-level explanation generation that provides specific reasons for each segment's classification
- Added schema extensions and API pass-through for both explanation types
- Created frontend UI with "What This Means" document card and "In Plain English" sentence card

## Task Commits

Each task was committed atomically:

1. **Task 1 & 2: Backend explanation generation** - `a0a40eb` (feat)
2. **Task 3: Schema and API updates** - `5b70d23` (feat)
3. **Task 4: Frontend explanation UI** - `3dbb969` (feat)

**Plan metadata:** (to be created after SUMMARY)

## Files Created/Modified

- `backend/app/services/analysis_service.py` - Added `generate_document_explanation()`, `generate_sentence_explanation()`, helper methods, and FEATURE_PATTERNS dict
- `backend/app/models/schemas.py` - Added `sentence_explanation` to TextSegment, `document_explanation` to HeatMapData
- `backend/app/api/routes/analysis.py` - Updated API to pass through explanation fields
- `frontend/src/components/HeatMap/HeatMap.tsx` - Added interfaces and UI components for explanations

## Implementation Details

### Backend Changes

#### 1. Feature Pattern Descriptions (`FEATURE_PATTERNS` dict)

Added 20+ pattern descriptions mapping feature names to human-readable explanations:

- `low_burstiness`: "consistent sentence lengths throughout"
- `low_perplexity`: "predictable word choices and common phrases"
- `low_unique_words`: "repetitive vocabulary"
- `high_bigram_repetition`: "formulaic expression patterns"
- etc.

#### 2. Document-Level Explanation (`generate_document_explanation()`)

Generates 2-3 sentence document summary based on:

- Overall AI probability (>0.7, 0.4-0.7, <0.4)
- Confidence distribution (HIGH/MEDIUM/LOW counts)
- Dominant feature patterns across high-confidence segments

**Template structure:**
- **HIGH (>0.7):** "This document shows strong indicators of AI-generated content. Key patterns include [patterns]. Approximately X of Y sentences are flagged as high-confidence AI-generated."
- **MEDIUM (0.4-0.7):** "This document contains mixed signals - some sections appear AI-generated while others seem human-written. [patterns]. Overall, X of Y sentences show strong AI patterns, while Z appear primarily human-written."
- **LOW (<0.4):** "This document primarily shows human-like writing patterns. [patterns]. Only X of Y sentences are flagged as potentially AI-generated."

#### 3. Sentence-Level Explanation (`generate_sentence_explanation()`)

Generates 1-2 sentence segment-specific explanation based on:

- Confidence level (HIGH/MEDIUM/LOW)
- Top 2 features from attribution
- Pattern combinations (e.g., low burstiness + low perplexity)

**Template structure:**
- **HIGH:** "This sentence is flagged as highly likely to be AI-generated. Primary indicators: [feature1, feature2]. The sentence shows [pattern description]."
- **MEDIUM:** "This sentence shows some AI-like patterns but is less certain. Contributing factors: [feature1, feature2]. [suggestion for humanizing]."
- **LOW:** "This sentence appears primarily human-written. Human-like indicators: [feature1, feature2]. No strong AI patterns detected."

#### 4. Helper Methods

- `_analyze_document_feature_patterns()`: Aggregates feature importance across high-confidence segments
- `_feature_to_pattern_key()`: Maps feature names and values to pattern keys
- `_get_pattern_description()`: Generates pattern descriptions for HIGH confidence
- `_get_humanizing_suggestion()`: Provides suggestions for MEDIUM confidence

### Frontend Changes

#### 5. Document Explanation Card ("What This Means")

- **Location:** Main content area, below Overall AI Probability card
- **Icon:** Info icon with primary color
- **Styling:** Callout/info box style, readable paragraph with good spacing
- **Placement:** Prominent but below main score (sets context without overwhelming)
- **Graceful degradation:** Only shows if `document_explanation` exists

#### 6. Sentence Explanation Card ("In Plain English")

- **Location:** Sidebar, below Segment Details
- **Title:** "In Plain English" with subtitle "Why this sentence was flagged"
- **Content:** `selectedSegment.sentence_explanation`
- **Styling:** Readable paragraph, distinct from feature list
- **Placement:** Near top of sidebar, visible immediately when segment selected
- **Graceful degradation:** Shows "not available" message if missing

## Deviations from Plan

### Auto-fixed Issues

**None.** Plan executed exactly as written with no deviations, bugs, or blocking issues.

### Authentication Gates

**None.** No authentication requirements encountered during execution.

## Key Decisions

### Decision 1: Template-Based vs LLM Generation

**Context:** How to generate natural language explanations.

**Options considered:**
1. **Template-based generation** (conditionals + string formatting) - *SELECTED*
2. Ollama/LLM generation
3. Hybrid (template for simple, LLM for complex)

**Rationale:**
- Templates are faster (no network calls to Ollama)
- Deterministic and predictable (same input = same output)
- No external dependencies (works even if Ollama is down)
- Easier to test and maintain
- Feature attribution already provides rich data for templates

**Outcome:** Correct - Explanations are clear, specific, and generated instantly.

### Decision 2: Three-Tier Explanation Styles

**Context:** How to style explanations based on confidence level.

**Options considered:**
1. **Three-tier styles** (HIGH/MEDIUM/LOW) - *SELECTED*
2. Single uniform style
3. Continuous gradient of styles

**Rationale:**
- Matches confidence level categorization from 01-01
- HIGH needs strong warnings, LOW needs reassurance, MEDIUM needs nuance
- Different information needs per confidence level
- Aligns with user mental model from confidence badges

**Outcome:** Correct - Users get appropriate tone and detail for each confidence level.

### Decision 3: Document Explanation Placement

**Context:** Where to display document-level explanation in UI.

**Options considered:**
1. **Below Overall AI Probability card** (prominent but not top) - *SELECTED*
2. Above Overall AI Probability card
3. In sidebar
4. Modal/popup

**Rationale:**
- Overall score is most important, should be first
- Document explanation sets context for detailed analysis
- Below main score = visible but not overwhelming
- Doesn't clutter sidebar (already has segment details)

**Outcome:** Correct - Document explanation provides context without competing with main score.

### Decision 4: Sentence Explanation Placement

**Context:** Where to display sentence-level explanation in UI.

**Options considered:**
1. **Sidebar, below Segment Details** - *SELECTED*
2. Above "Why This Flag?" feature attribution
3. In tooltip on segment hover
4. Inline with text

**Rationale:**
- Appears when user clicks segment (context-specific)
- Below Segment Details = visible immediately
- Above feature attribution = narrative before technical details
- Complements "Why This Flag?" (narrative + data)

**Outcome:** Correct - Narrative explanation helps users understand feature attribution.

## Next Phase Readiness

### Blocking Issues

**None.** All success criteria met, no blockers identified.

### Concerns to Monitor

1. **Explanation accuracy:** Template patterns may need refinement based on user feedback
2. **Feature coverage:** 20+ patterns cover most cases but edge cases may exist
3. **Tone calibration:** HIGH confidence explanations may feel too harsh, LOW too reassuring
4. **Pattern localization:** Current patterns assume English grammar/style

### Technical Debt

**None.** Implementation is clean, follows existing patterns, no shortcuts taken.

### Recommendations for Future Plans

1. **Plan 01-04 (Overused Phrases):** Can reference explanations for additional context
2. **Production validation:** Collect user feedback on explanation helpfulness
3. **A/B testing:** Test different explanation templates for optimal clarity
4. **Internationalization:** Consider localization for non-English text

## Success Criteria

All success criteria from plan met:

- [x] `generate_document_explanation()` implemented and called
- [x] `generate_sentence_explanation()` implemented and called
- [x] HeatMapData schema includes `document_explanation`
- [x] TextSegment schema includes `sentence_explanation`
- [x] Document explanation card displays in UI
- [x] Sentence explanation displays in sidebar
- [x] Explanations reference specific features and patterns
- [x] Explanations are readable and helpful

## Artifacts Generated

### Backend

- **FEATURE_PATTERNS dict:** 20+ feature pattern descriptions
- **generate_document_explanation():** backend/app/services/analysis_service.py (lines 522-586)
- **generate_sentence_explanation():** backend/app/services/analysis_service.py (lines 588-647)
- **_analyze_document_feature_patterns():** backend/app/services/analysis_service.py (lines 713-762)
- **_feature_to_pattern_key():** backend/app/services/analysis_service.py (lines 764-827)
- **_get_pattern_description():** backend/app/services/analysis_service.py (lines 649-685)
- **_get_humanizing_suggestion():** backend/app/services/analysis_service.py (lines 687-711)

### Schemas

- **TextSegment.extension:** Added `sentence_explanation` field (line 120)
- **HeatMapData.extension:** Added `document_explanation` field (line 128)

### Frontend

- **TextSegment interface:** Added `sentence_explanation?` field
- **HeatMapData interface:** Added `document_explanation?` field
- **Document explanation card:** "What This Means" card (lines 299-314)
- **Sentence explanation card:** "In Plain English" card (lines 553-575)

## Commits

```bash
a0a40eb feat(01-03): implement document and sentence explanation generation
5b70d23 feat(01-03): add explanation fields to schemas and API
3dbb969 feat(01-03): add explanation UI to HeatMap component
```

All commits follow conventional commit format with `{type}({phase}-{plan}): {description}` pattern.

---

*Summary created: 2025-01-19*
*Plan completed successfully - All tasks executed, verified, and committed*
*No deviations or authentication gates - clean execution*
