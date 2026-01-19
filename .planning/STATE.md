# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2025-01-18)

**Core value:** Reliable AI text detection with transparent explainability
**Current focus:** Phase 5: Enhanced Fingerprinting

## Current Position

Phase: 5 of 7 (in progress)
Plan: 3 of 4 in Phase 5
Status: Phase 5 Plan 3 Complete - Time-Weighted Training and Similarity Calculation
Last activity: 2026-01-19 — Completed 05-03-PLAN.md (Time-Weighted Training and Similarity Calculation)

Progress: [████████████████░░░░░░░░░░░] 61% (17/28 total plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 17
- Average duration: 9 minutes
- Total execution time: 2.5 hours

**By Phase:**

| Phase | Plans | Complete | Avg/Plan |
|-------|-------|----------|----------|
| 1. Explainability | 4 | 4 | 15 minutes |
| 2. Batch Analysis | 3 | 3 | 11 minutes |
| 3. Enterprise API | 4 | 4 | 3 minutes |
| 4. Multi-Model Ensemble | 3 | 3 | 10 minutes |
| 5. Enhanced Fingerprinting | 4 | 3 | 5 minutes |
| 6. Style Transfer | 4 | 0 | TBD |
| 7. Distribution | 4 | 0 | TBD |

**Recent Trend:**
- Last 5 plans: 04-02 (8 min), 04-03 (14 min), 05-01 (5 min), 05-03 (3 min)
- Trend: Phase 5 progressing through enhanced fingerprinting
- Phase 5 delivered: FingerprintSample, EnhancedFingerprint tables, corpus schemas, FingerprintCorpusBuilder, TimeWeightedFingerprintBuilder, FingerprintComparator

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

**From Plan 03-04 (API Usage Dashboard):**
1. **One-time key display modal** - Full API key shown only after creation, then inaccessible from UI - security best practice
2. **Usage progress bars with color coding** - Blue for daily, green for per-minute - visual distinction between quota types
3. **Tier-based display colors** - enterprise=purple, pro=blue, free=gray - instant tier recognition
4. **Confirmation before key deletion** - Prevents accidental loss of working API keys
5. **External link to /docs** - Opens API documentation in new tab for reference while managing keys

**From Plan 04-01 (Multi-Model Ensemble Detector):**
1. **Weighted soft voting via sklearn VotingClassifier** - Standard ensemble approach using probability-based voting instead of majority voting
2. **Default model weights: stylometric 0.4, perplexity 0.3, contrastive 0.3** - Reflects expected model reliability based on feature quality
3. **Graceful degradation to stylometric-only when sklearn unavailable** - SKLEARN_AVAILABLE flag enables service to continue without full ensemble
4. **Manual weighted average fallback** - When VotingClassifier initialization fails, manual calculation maintains ensemble functionality
5. **Ensemble results include per-model probabilities** - Transparency for debugging and analysis; shows individual model contributions
6. **analyze_with_ensemble() separate from analyze_text()** - New method preserves backward compatibility while adding ensemble capabilities
7. **sklearn-compatible detector wrappers** - Each detector implements fit/predict_proba/predict interface for VotingClassifier integration

**From Plan 04-02 (Ensemble Calibration and Performance Monitoring):**
1. **CalibratedClassifierCV with ensemble=True for stable cross-validation** - Wraps VotingClassifier with sklearn's calibration to prevent overconfidence
2. **Sigmoid (Platt scaling) as default calibration method** - Works better for small datasets (<1000 samples) compared to isotonic regression
3. **Exponential moving average (alpha=0.3) for smooth weight transitions** - Provides responsive yet stable weight updates based on performance
4. **Minimum 100 predictions before weight updates** - Prevents rapid weight changes from insufficient data that could degrade performance
5. **Minimum weight of 0.1 per model** - Ensures no model gets zeroed out, maintaining ensemble diversity even during temporary underperformance
6. **Separate calibration dataset requirement** - Calibration must use held-out data different from training to prevent data leakage
7. **Public read-only weights endpoint** - GET /api/ensemble/weights requires no auth for transparency, admin endpoints for modifications

**From Plan 04-03 (Temporal Analysis and AI Injection Detection):**
1. **Use difflib.SequenceMatcher for version diffing** - Python's built-in library provides robust diff algorithm without external dependencies. Returns opcodes for added/removed/modified sections.
2. **SHA-256 content hashing for deduplication** - Prevents storing identical versions, saving storage and enabling efficient change detection. Hash stored in indexed column for fast lookup.
3. **Trend threshold of 0.2 AI probability** - Minimum difference between first and last version averages to indicate increasing/decreasing trend. Balances noise sensitivity with meaningful change detection.
4. **Injection severity tiers** - High (>=0.8), medium (>=0.6), low (<0.6) AI probability thresholds. Enables UI prioritization and risk assessment.
5. **Per-segment AI probability storage** - Stores segment-level scores in JSON for each version. Enables granular injection detection at specific text positions.
6. **SVG-based line chart without external dependencies** - Uses native SVG with polyline for timeline visualization. Avoids heavy charting libraries while providing clear visual feedback.

**From Plan 05-01 (Corpus-Based Fingerprint Data Models):**
1. **MIN_SAMPLES_FOR_FINGERPRINT = 10** - Balances statistical robustness with practical data collection requirements
2. **Three aggregation methods: time_weighted (default), average, source_weighted** - Flexibility for different use cases and corpus compositions
3. **Welford's online algorithm for feature statistics** - Numerically stable variance calculation for confidence interval computation
4. **Source weights: academic=1.3, essay=1.2, document=1.1, blog=1.0, manual=1.0, email=0.9** - Formal writing prioritized in aggregation
5. **JSON storage for features and feature_statistics** - Flexibility without schema migrations, supports 27-element feature arrays
6. **written_at timestamp separate from created_at** - Enables time-weighted aggregation based on original writing date vs. database insertion

**From Plan 05-03 (Time-Weighted Training and Similarity Calculation):**
1. **EMA alpha=0.3** - Balances recency sensitivity with stability for writing style evolution tracking
2. **Lambda = -ln(alpha) for recency weight calculation** - Ensures mathematical consistency between EMA smoothing and exponential time decay
3. **95% confidence level with z-score=1.96** - Standard statistical confidence interval for similarity uncertainty quantification
4. **Similarity thresholds: HIGH=0.85, MEDIUM=0.70, LOW=0.50** - Based on authorship verification research for reliable classification
5. **Graceful degradation when scipy/sklearn unavailable** - Uses fallback calculations and pre-computed z-scores for robustness
6. **Top 5 feature deviations for interpretability** - Highlights most different stylometric features for user understanding
7. **TimeWeightedFingerprintBuilder for incremental updates** - Supports streaming scenarios where samples arrive over time

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

Last session: 2026-01-19 22:01 UTC
Stopped at: Completed 05-03-PLAN.md (Time-Weighted Training and Similarity Calculation)
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
- **NEW:** API Dashboard at /api-dash route with ApiDashboard component (387 lines)
- **NEW:** apiKeysAPI and usageAPI functions in frontend/src/services/api.ts
- **NEW:** Self-service API key creation with one-time key display modal
- **NEW:** Usage statistics with progress bars for daily and per-minute limits
- **NEW:** Ensemble module at backend/app/ml/ensemble/ with multi-model detection
- **NEW:** EnsembleDetector class with sklearn VotingClassifier and soft voting
- **NEW:** StylometricDetector, PerplexityDetector, ContrastiveDetectorWrapper sklearn-compatible classes
- **NEW:** calculate_weights_from_accuracy() utility for ensemble weight normalization
- **NEW:** analyze_with_ensemble() method returning per-model and ensemble probabilities
- **NEW:** EnsembleResult and EnsembleAnalysisRequest schemas for API responses
- **NEW:** CalibratedEnsemble class with sklearn CalibratedClassifierCV wrapper
- **NEW:** PerformanceMonitor service with EMA-based tracking and weight updates
- **NEW:** Ensemble management API: /api/ensemble/stats, /calibrate, /weights, /track, /reliability, /predictions
- **NEW:** ModelPerformance database table for persistent tracking
- **NEW:** Calibration metrics: Brier score, reliability diagram data
- **NEW:** Temporal module at backend/app/ml/temporal/ for version tracking
- **NEW:** DocumentVersion database table with SHA-256 content hashing
- **NEW:** VersionTracker, TimelineAnalyzer, InjectionDetector classes
- **NEW:** Temporal analysis API: POST /version, GET /timeline, /versions, /injections, POST /compare, GET /summary
- **NEW:** React TemporalAnalysis component with timeline visualization, injection display, version comparison (858 lines)
- **NEW:** FingerprintSample and EnhancedFingerprint database tables
- **NEW:** FingerprintCorpusBuilder at backend/app/ml/fingerprint/corpus_builder.py
- **NEW:** MIN_SAMPLES_FOR_FINGERPRINT = 10 constant
- **NEW:** Pydantic schemas: FingerprintSampleCreate, CorpusStatus, EnhancedFingerprintResponse
- **NEW:** Three aggregation methods: time_weighted (EMA), average, source_weighted
- **NEW:** Welford's online algorithm for feature statistics (mean, std, variance)
- **NEW:** TimeWeightedFingerprintBuilder at backend/app/ml/fingerprint/time_weighted_trainer.py (370 lines)
- **NEW:** EMA update formula: new_ema = (1-alpha)*old_ema + alpha*new_sample
- **NEW:** Recency weight calculation: weight = exp(-lambda*age), lambda = -ln(alpha)
- **NEW:** FingerprintComparator at backend/app/ml/fingerprint/similarity_calculator.py (396 lines)
- **NEW:** Similarity thresholds: HIGH=0.85, MEDIUM=0.70, LOW=0.50
- **NEW:** Confidence interval calculation: CI = z_score * SEM, SEM = sqrt(mean_variance / n_features)
- **NEW:** Top 5 feature deviations with normalization by std
- **NEW:** Module exports from app.ml.fingerprint: TimeWeightedFingerprintBuilder, FingerprintComparator, compare_with_confidence
