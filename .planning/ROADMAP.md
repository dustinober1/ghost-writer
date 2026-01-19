# Roadmap: Ghost-Writer

## Overview

Ghost-Writer evolves from a solid MVP (core detection, fingerprinting, rewriting) through 7 phases that deliver enterprise readiness, advanced accuracy, personalization, and broad distribution. Each phase builds on previous capabilities, starting with table-stakes features (explainability, batch processing, API access) that block enterprise adoption, then advancing detection accuracy through ensemble methods, enhancing analytics with clustering, personalizing style transfer with fingerprint-based rewriting, and finally distributing through browser extensions and platform integrations.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Explainability** - Transparent AI detection with per-sentence attribution
- [x] **Phase 2: Batch Analysis** - Multi-file processing with clustering and comparison
- [x] **Phase 3: Enterprise API** - REST API with authentication, rate limiting, and documentation
- [x] **Phase 4: Multi-Model Ensemble** - Improved accuracy through combined detection methods
- [ ] **Phase 5: Enhanced Fingerprinting** - Corpus-based fingerprints with style drift alerts
- [ ] **Phase 6: Style Transfer** - Granular rewriting controls with intent preservation
- [ ] **Phase 7: Distribution** - Browser extension and platform integrations

## Phase Details

### Phase 1: Explainability

**Goal**: Users can understand WHY text was flagged as AI-generated, not just receive a probability score.

**Depends on**: Nothing (first phase)

**Requirements**: EXP-01, EXP-02, EXP-03, EXP-04

**Success Criteria** (what must be TRUE):
1. User can view per-sentence confidence scores for analyzed text, with color-coded highlighting (high/medium/low risk)
2. User can view feature attribution showing which stylometric features (burstiness, perplexity, rare words, etc.) contributed to AI detection for each sentence
3. User can view clear, natural language explanations of why content was flagged (e.g., "This sentence has low burstiness and high perplexity, indicating AI-generated patterns")
4. User can view overused phrases and patterns that triggered detection, with specific examples highlighted in the text

**Plans**: 4 plans in 3 waves (complete)

Plans:
- [x] 01-01-PLAN.md — Per-sentence confidence scoring with color-coded risk categorization (high/medium/low)
- [x] 01-02-PLAN.md — Feature attribution showing which stylometric features contributed to AI detection
- [x] 01-03-PLAN.md — Natural language explanations at document and sentence level
- [x] 01-04-PLAN.md — Overused phrases and patterns detection with text highlighting

**Completed**: 2026-01-19

---

### Phase 2: Batch Analysis

**Goal**: Users can analyze multiple documents at once and identify patterns across large document sets.

**Depends on**: Phase 1 (explainability provides foundation for batch results)

**Requirements**: BATCH-01, BATCH-02, BATCH-03, BATCH-04

**Success Criteria** (what must be TRUE):
1. User can upload multiple files at once via ZIP archive or folder drag-drop, with progress indicator for processing
2. System can cluster documents by similarity using vector embeddings, grouping related documents together automatically
3. User can view comparison matrix showing pairwise similarity scores across all uploaded documents, with heatmap visualization
4. User can export bulk results to CSV/JSON formats, including per-document scores, confidence intervals, and cluster assignments

**Plans**: 3 plans in 3 waves (complete)

Plans:
- [x] 02-01: Batch upload and processing pipeline with Celery
- [x] 02-02: Document clustering and similarity analysis
- [x] 02-03: Comparison matrix visualization and export functionality

**Completed**: 2026-01-19

---

### Phase 3: Enterprise API

**Goal**: Developers can integrate Ghost-Writer detection into their applications and workflows.

**Depends on**: Phase 2 (batch analysis provides mature backend for API endpoints)

**Requirements**: API-01, API-02, API-03, API-04

**Success Criteria** (what must be TRUE):
1. Developer can access comprehensive REST API with OpenAPI/Swagger documentation, including all endpoints for single and batch analysis
2. Developer can authenticate using API keys with scoped permissions (read-only, analysis, admin) and secure key rotation
3. System enforces tiered rate limiting (free tier: 100 requests/day, paid tier: 10,000 requests/day) with proper HTTP headers (X-RateLimit-Remaining)
4. Developer can view usage metrics and dashboard showing API call volume, quota consumption, and error rates over time

**Plans**: 4 plans in 3 waves (complete)

Plans:
- [x] 03-01-PLAN.md — API key authentication model with database migration and CRUD endpoints
- [x] 03-02-PLAN.md — Tiered rate limiting middleware with Redis-backed user-based quotas
- [x] 03-03-PLAN.md — Protected OpenAPI documentation requiring authentication
- [x] 03-04-PLAN.md — API usage dashboard for key management and usage visualization

**Completed**: 2026-01-19

---

### Phase 4: Multi-Model Ensemble

**Goal**: Detection accuracy improves through combining multiple AI detection approaches.

**Depends on**: Phase 3 (API infrastructure supports model versioning and A/B testing)

**Requirements**: ENSEMBLE-01, ENSEMBLE-02, ENSEMBLE-03

**Success Criteria** (what must be TRUE):
1. System combines stylometric + perplexity + detector models for improved accuracy, with weighted voting based on individual model performance
2. System uses weighted voting based on model accuracy, with calibration to prevent overconfidence and reduce false positives
3. User can view temporal analysis showing writing timeline, draft comparison, and AI injection detection (identifying portions of text that may have been AI-generated and inserted)

**Plans**: 3 plans in 3 waves (complete)

Plans:
- [x] 04-01-PLAN.md — Multi-model ensemble orchestrator with weighted voting (stylometric + perplexity + contrastive models via sklearn VotingClassifier)
- [x] 04-02-PLAN.md — Model calibration and performance monitoring (CalibratedClassifierCV, Brier score tracking, dynamic weight updates)
- [x] 04-03-PLAN.md — Temporal analysis and injection detection (document version tracking, timeline visualization, AI injection detection)

**Completed**: 2026-01-19

---

### Phase 5: Enhanced Fingerprinting

**Goal**: Users can create robust personal writing fingerprints that detect style drift and evolution over time.

**Depends on**: Phase 4 (ensemble improves fingerprint accuracy and reduces false positives)

**Requirements**: PRINT-01, PRINT-02, PRINT-03

**Success Criteria** (what must be TRUE):
1. User can build fingerprint from corpus of 10+ writing samples, with automatic feature extraction across different document types
2. System applies time-weighted training (recent writing weighted higher) to account for natural style evolution while maintaining consistent core patterns
3. User receives alerts when writing style drifts significantly from their fingerprint, with confidence intervals and specific feature changes highlighted

**Plans**: 3 plans in 3 waves

Plans:
- [ ] 05-01-PLAN.md — Corpus builder for fingerprint generation (FingerprintSample/EnhancedFingerprint tables, FingerprintCorpusBuilder, corpus API, CorpusBuilder UI)
- [ ] 05-02-PLAN.md — Time-weighted training algorithm (TimeWeightedFingerprintBuilder with EMA, FingerprintComparator with confidence intervals, comparison API, FingerprintProfile UI)
- [ ] 05-03-PLAN.md — Style drift detection and alerting (DriftAlert table, StyleDriftDetector, drift API, DriftAlerts UI)

---

### Phase 6: Style Transfer

**Goal**: Users can rewrite text to match specific styles while preserving original intent.

**Depends on**: Phase 5 (enhanced fingerprinting provides target style for rewriting)

**Requirements**: STYLE-01, STYLE-02, STYLE-03

**Success Criteria** (what must be TRUE):
1. User can adjust rewriting with granular controls (formality level, sentence length distribution, vocabulary complexity) before generation
2. System preserves intent while changing voice during rewrite, with semantic validation to ensure meaning is maintained
3. User can view A/B comparison (original vs rewritten side-by-side) with highlighted changes and diff visualization

**Plans**: TBD

Plans:
- [ ] 06-01: Granular rewriting controls and parameter tuning
- [ ] 06-02: Intent preservation validation
- [ ] 06-03: A/B comparison visualization with diff highlighting

---

### Phase 7: Distribution

**Goal**: Users can access Ghost-Writer detection directly in their workflow environments.

**Depends on**: Phase 6 (all backend features stable, avoiding breaking API changes)

**Requirements**: DIST-01, DIST-02

**Success Criteria** (what must be TRUE):
1. User can install browser extension (Chrome/Firefox) for inline detection on any web page, with right-click context menu integration
2. User can integrate with Google Docs, Microsoft Word, or LMS platforms (Canvas, Blackboard) through add-ons or API integrations

**Plans**: TBD

Plans:
- [ ] 07-01: Browser extension with WXT framework
- [ ] 07-02: Platform integrations (Google Docs, Microsoft Word, LMS)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Explainability | 4/4 | Complete | 2026-01-19 |
| 2. Batch Analysis | 3/3 | Complete | 2026-01-19 |
| 3. Enterprise API | 4/4 | Complete | 2026-01-19 |
| 4. Multi-Model Ensemble | 3/3 | Complete | 2026-01-19 |
| 5. Enhanced Fingerprinting | 0/3 | Not started | - |
| 6. Style Transfer | 0/TBD | Not started | - |
| 7. Distribution | 0/TBD | Not started | - |

---

*Roadmap created: 2025-01-18*
*Last updated: 2026-01-19*
