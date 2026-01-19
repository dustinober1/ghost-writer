# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2025-01-18)

**Core value:** Reliable AI text detection with transparent explainability
**Current focus:** Phase 2: Batch Analysis

## Current Position

Phase: 2 of 7 (Batch Analysis)
Plan: 1 of 5 in current phase
Status: In progress
Last activity: 2026-01-19 — Completed plan 02-01 (Batch Analysis Data Model)

Progress: [██████████░] 18% (5/28 total plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 5
- Average duration: 14 minutes
- Total execution time: 1.2 hours

**By Phase:**

| Phase | Plans | Complete | Avg/Plan |
|-------|-------|----------|----------|
| 1. Explainability | 4 | 4 | 15 minutes |
| 2. Batch Analysis | 5 | 1 | 8 minutes |
| 3. Enterprise API | 4 | 0 | TBD |
| 4. Multi-Model Ensemble | 3 | 0 | TBD |
| 5. Enhanced Fingerprinting | 4 | 0 | TBD |
| 6. Style Transfer | 4 | 0 | TBD |
| 7. Distribution | 4 | 0 | TBD |

**Recent Trend:**
- Last 5 plans: 01-01 (10 min), 01-02 (30 min), 01-03 (4 min), 01-04 (20 min), 02-01 (8 min)
- Trend: Steady progress, infrastructure stable
- Phase 1 complete, Phase 2 batch analysis data model complete

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

**From Plan 01-04 (Overused Phrases & Patterns Detection):**
1. **Statistical-only pattern detection** - N-gram extraction and frequency counting instead of ML models, providing fast deterministic results without external dependencies
2. **Three detection dimensions** - Repeated phrases (2-4 word n-grams appearing 3+ times), sentence starts (>30% threshold), word repetition (>5% threshold)
3. **Severity tiers based on frequency** - HIGH (>=5 phrases, >=50% starts, >=10% words), MEDIUM (>=3 phrases, >=35% starts, >=7% words), LOW (minimum thresholds)
4. **Pattern UI placement** - Below Document Explanation, visible but not competing with main AI Probability score
5. **Dismissible pattern card** - Users can hide pattern information to reduce clutter, following progressive disclosure UX principle
6. **Development mode authentication bypass** - DEVELOPMENT_MODE environment variable allows local testing without auth, improving developer experience

**From Plan 02-01 (Batch Analysis Data Model):**
1. **String-based status storage** - Using String columns with Python enum validation instead of database-native ENUM for better cross-database compatibility and easier migration
2. **JSON storage for complex batch fields** - Similarity matrices, clusters, and embeddings stored as JSON for flexibility without requiring additional database extensions
3. **Cascade delete on job deletion** - When a BatchAnalysisJob is deleted, all associated BatchDocuments are automatically removed
4. **Snake_case throughout batch schemas** - All field names use snake_case to align with Python/SQLAlchemy conventions (frontend will transform as needed)
5. **Batch job lifecycle pattern** - PENDING -> PROCESSING -> COMPLETED/FAILED with progress tracking via processed_documents / total_documents

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

**Infrastructure:**
- Download Ollama models (llama3:8b, nomic-embed-text:v1.5) - ~4GB, required for full AI detection pipeline

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

**From Plan 01-04:**
1. **Pattern detection accuracy:** Statistical thresholds may need calibration based on real AI-generated text - monitor false positives/negatives
2. **Performance with large documents:** Pattern detection adds computational overhead - test with documents >10k words
3. **Pattern UI clutter:** Too many patterns may overwhelm users - consider showing only HIGH/MEDIUM severity by default
4. **N-gram language dependence:** Current approach assumes English word tokenization - may need adjustments for other languages

## Session Continuity

Last session: 2026-01-19 17:30 UTC
Stopped at: Completed plan 02-01 (Batch Analysis Data Model)
Resume file: None (Plan 02-01 complete, ready for 02-02)

**Infrastructure Note:**
- Ollama service added to docker-compose.yml (llama3:8b, nomic-embed-text:v1.5 models)
- Health check supports degraded mode (200 OK without Ollama)
- Backend/celery depend on service_started (not service_healthy) for faster startup
- DEVELOPMENT_MODE environment variable added for auth bypass in local development
- Slowapi parameter naming conflict resolved (avoid `request` parameter name in endpoints)
- Batch analysis tables added via Alembic migration 002_add_batch_analysis_tables
