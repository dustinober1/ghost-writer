# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2025-01-18)

**Core value:** Reliable AI text detection with transparent explainability
**Current focus:** Phase 3: Enterprise API

## Current Position

Phase: 3 of 7 (in progress)
Plan: 3 of 4 in Phase 3
Status: Phase 3 Plans 1, 2, 3 complete
Last activity: 2026-01-19 — Completed 03-02 (Tiered Rate Limiting)

Progress: [████████████] 39% (11/28 total plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 11
- Average duration: 10 minutes
- Total execution time: 1.8 hours

**By Phase:**

| Phase | Plans | Complete | Avg/Plan |
|-------|-------|----------|----------|
| 1. Explainability | 4 | 4 | 15 minutes |
| 2. Batch Analysis | 3 | 3 | 11 minutes |
| 3. Enterprise API | 4 | 3 | 2 minutes |
| 4. Multi-Model Ensemble | 3 | 0 | TBD |
| 5. Enhanced Fingerprinting | 4 | 0 | TBD |
| 6. Style Transfer | 4 | 0 | TBD |
| 7. Distribution | 4 | 0 | TBD |

**Recent Trend:**
- Last 5 plans: 01-04 (20 min), 02-01 (8 min), 02-02 (5 min), 02-03 (11 min), 03-01 (2 min), 03-03 (1 min)
- Trend: Steady progress, Phase 3 nearly complete
- Phase 2 complete with clustering, similarity matrix, and batch upload UI

*Updated after each phase completion*

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

**From Plan 02-02 (Batch Similarity Clustering):**
1. **Union-Find clustering algorithm** - O(n) near-linear time complexity with path compression for efficient deterministic document grouping
2. **Cosine similarity via numpy dot product** - Vectorized operations for efficient similarity matrix generation with values in [-1, 1] range
3. **JSON-serializable outputs** - All numpy arrays converted to Python lists via .tolist() for API/database compatibility
4. **Default clustering threshold 0.85** - Balances sensitivity (catching similar docs) with specificity (avoiding over-clustering)
5. **Function + Class API pattern** - Top-level functions for direct use, BatchAnalysisService class for dependency injection

**From Plan 02-03 (Batch Upload and Results Dashboard):**
1. **ZIP file extraction for bulk uploads** - Single ZIP can contain multiple .txt files for improved UX with large batches
2. **Celery for non-blocking processing** - API returns immediately with job_id, actual analysis runs asynchronously with progress updates
3. **Overview-first dashboard layout** - Summary cards (documents, clusters, avg probability) shown before detailed tables
4. **Similarity heatmap via CSS grid** - No heavy visualization libraries; simple color-coded grid shows pairwise similarity
5. **Polling for status updates** - Frontend polls every 2-3 seconds during processing; navigates to results on completion
6. **Export streaming response** - CSV/JSON exports use FastAPI StreamingResponse for memory efficiency

**From Plan 03-01 (API Key Authentication Model):**
1. **SHA-256 hashing for API key storage** - Full key never stored, only hash; prevents key recovery even with database access
2. **Key prefix for identification** - First 8 characters stored separately so users can recognize keys without exposing full value
3. **Tier-based API key limits** - free=3, pro=10, enterprise=unlimited - prevents abuse while allowing scalability
4. **Full key only on creation** - Security best practice: key returned once, then only prefix shown
5. **gw_ prefix convention** - Human-readable prefix identifies Ghost-Writer API keys and allows future key type extensions
6. **Dual authentication support** - JWT for web sessions, API keys for programmatic access - both methods supported seamlessly

**From Plan 03-02 (Tiered Rate Limiting):**
1. **Redis for distributed rate limiting** - Enables horizontal scaling across multiple backend instances with shared state
2. **Tiered daily limits** - free=100, pro=10000, enterprise=100000 - aligns with business model for fair usage
3. **Per-minute limits** - free=10/min, pro=100/min, enterprise=500/min - prevents rapid-fire abuse
4. **Midnight UTC reset** - Daily keys use date-based Redis keys with calculated TTL until midnight
5. **Degraded mode on Redis failure** - System remains available when Redis unavailable; preferable to rejecting all requests
6. **X-RateLimit-* headers** - Standard HTTP headers (Limit-Day, Remaining-Day, Limit-Minute, Remaining-Minute, Reset) for quota visibility
7. **User-based not IP-based** - Rate limits follow authenticated users, supporting dynamic IPs and API key usage

**From Plan 03-03 (Protected OpenAPI Documentation):**
1. **Disable public docs by default** - Production best practice to hide API structure from unauthenticated users, reducing attack surface
2. **Protected docs endpoints** - /docs, /redoc, /openapi.json all require authentication via JWT or API key
3. **Explicit opt-in for public dev docs** - Requires both ENVIRONMENT=development AND ENABLE_PUBLIC_DOCS=true to prevent accidental public exposure
4. **Tier limits in OpenAPI schema** - Rate limit information (free: 30, pro: 100, enterprise: 1000) exposed in schema for API consumers

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

**From Plan 02-03:**
1. **Celery worker scaling:** Single worker may bottleneck with concurrent batch jobs - monitor and add workers if needed
2. **Large ZIP file handling:** No size limit on uploads currently - consider adding max file size constraints
3. **Heatmap readability:** CSS grid heatmap may become dense with >20 documents - consider pagination or clustering views
4. **Job retention:** No cleanup policy for old batch jobs - documents accumulate in database

## Session Continuity

Last session: 2026-01-19 20:25 UTC
Stopped at: Completed 03-02-PLAN.md (Tiered Rate Limiting)
Resume file: None

**Infrastructure Note:**
- Ollama service added to docker-compose.yml (llama3:8b, nomic-embed-text:v1.5 models)
- Health check supports degraded mode (200 OK without Ollama)
- Backend/celery depend on service_started (not service_healthy) for faster startup
- DEVELOPMENT_MODE environment variable added for auth bypass in local development
- Batch analysis tables added via Alembic migration 002_add_batch_analysis_tables
- BatchAnalysisService with build_similarity_matrix, cluster_documents methods
- Batch API routes: /api/batch/upload, /status, /results, /export, /jobs
- Celery task process_batch_job for async document processing
- React BatchAnalysis and BatchResults components with heatmap visualization
- API key authentication via SHA-256 hashed keys with X-API-Key header support
- ApiKey model with tier-based limits (free: 3, pro: 10, enterprise: unlimited)
- API key management endpoints: POST /api/keys, GET /api/keys, DELETE /api/keys/{id}
- Tiered rate limiting via Redis with TIER_LIMITS: free=100/day, pro=10000/day, enterprise=100000/day
- Rate limit endpoints: GET /api/usage, GET /api/limits with X-RateLimit-* headers
- Protected docs endpoints: /docs (Swagger UI), /redoc (ReDoc), /openapi.json all require auth
- Optional public dev docs available with ENVIRONMENT=development and ENABLE_PUBLIC_DOCS=true
