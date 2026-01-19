# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2025-01-18)

**Core value:** Reliable AI text detection with transparent explainability
**Current focus:** Phase 1: Explainability

## Current Position

Phase: 1 of 7 (Explainability)
Plan: 3 of 4 in current phase
Status: In progress
Last activity: 2025-01-19 — Completed plan 01-03 (Natural Language Explanations)

Progress: [███░░░░░░░░] 75% (3/4 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: 15 minutes
- Total execution time: 0.75 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Explainability | 3 | 4 | 15 minutes |
| 2. Batch Analysis | 0 | TBD | - |
| 3. Enterprise API | 0 | TBD | - |
| 4. Multi-Model Ensemble | 0 | TBD | - |
| 5. Enhanced Fingerprinting | 0 | TBD | - |
| 6. Style Transfer | 0 | TBD | - |
| 7. Distribution | 0 | TBD | - |

**Recent Trend:**
- Last 5 plans: 01-01 (10 min), 01-02 (30 min), 01-03 (4 min)
- Trend: Steady progress, infrastructure stable

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

**From Plan 01-01 (Per-Sentence Confidence Scoring):**
1. **Three-tier confidence thresholds** (HIGH >0.7, MEDIUM 0.4-0.7, LOW <0.4) - Balances sensitivity and specificity while providing intuitive semantic categories
2. **Additive visual indicators** (badge overlays) - Preserves existing gradient background while adding discrete categorization
3. **No modification to AI probability calculation** - Confidence categorization added as separate layer, maintaining existing detection logic integrity

**From Plan 01-02 (Feature Attribution):**
1. **Heuristic-based feature importance** (deviation from human baseline) - Simpler than SHAP/LIME, requires no additional ML models, provides interpretable scores
2. **Top 5 features per segment** - Reduces cognitive load while capturing >80% of importance signal, aligns with human working memory limits
3. **Three-tier importance color coding** (red/yellow/green) - Matches confidence visualization from 01-01, uses universal stoplight metaphor
4. **Degraded health check strategy** - Application returns 200 with degraded status when Ollama unavailable, allowing basic features without full AI pipeline
5. **Human-like baselines for 27 features** - Domain knowledge ranges for burstiness, perplexity, POS ratios, coherence, punctuation, readability

**From Plan 01-03 (Natural Language Explanations):**
1. **Template-based explanation generation** - Faster and more deterministic than LLM-based generation, no external dependencies, works even if Ollama is down
2. **Three-tier explanation styles** - Different tone and detail per confidence level (HIGH: strong warnings, MEDIUM: nuanced with suggestions, LOW: reassurance)
3. **Document explanation placement** - Below Overall AI Probability card (prominent but not overwhelming, sets context without competing with main score)
4. **Sentence explanation placement** - In sidebar below Segment Details (context-specific, complements "Why This Flag?" feature attribution)
5. **Feature pattern descriptions** - 20+ stylometric feature patterns mapped to human-readable descriptions for explanations

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

**From Plan 01-02:**
1. **Baseline calibration needed:** Human-like baselines may need adjustment based on production data - monitor user feedback
2. **Feature correlation:** Some features are correlated (burstiness/sentence complexity) - may double-count importance
3. **Interpretation edge cases:** Template-based interpretations may not cover all scenarios - consider NLG improvements
4. **Performance monitoring:** Feature importance adds ~50ms per segment - monitor with large documents (1000+ segments)
5. **MutableHeaders API differences:** Starlette's MutableHeaders differs from dict - no pop() method, use del with try/except

**From Plan 01-03:**
1. **Explanation accuracy:** Template patterns may need refinement based on user feedback - collect and iterate
2. **Feature coverage:** 20+ patterns cover most cases but edge cases may exist - monitor user queries
3. **Tone calibration:** HIGH confidence explanations may feel too harsh, LOW too reassuring - A/B test alternatives
4. **Pattern localization:** Current patterns assume English grammar/style - consider i18n for future

## Session Continuity

Last session: 2025-01-19 13:49 UTC
Stopped at: Completed plan 01-03 (Natural Language Explanations)
Resume file: None (plan complete, ready for 01-04)

**Infrastructure Note:**
- Ollama service added to docker-compose.yml (llama3:8b, nomic-embed-text:v1.5 models)
- Health check supports degraded mode (200 OK without Ollama)
- Backend/celery depend on service_started (not service_healthy) for faster startup
