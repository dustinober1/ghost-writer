# Requirements: Ghost-Writer

**Defined:** 2025-01-18
**Core Value:** Reliable AI text detection with transparent explainability

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Explainability (EXP)

- [ ] **EXP-01**: User can view per-sentence confidence scores for analyzed text
- [ ] **EXP-02**: User can view feature attribution showing which stylometric features contributed to AI detection
- [ ] **EXP-03**: User can view clear explanations of why content was flagged (not just that it was flagged)
- [ ] **EXP-04**: User can view overused phrases and patterns that triggered detection

### Batch Analysis (BATCH)

- [ ] **BATCH-01**: User can upload multiple files at once (ZIP, folder drag-drop)
- [ ] **BATCH-02**: System can cluster documents by similarity
- [ ] **BATCH-03**: User can view comparison matrix with pairwise similarity scores across all uploaded documents
- [ ] **BATCH-04**: User can export bulk results to CSV/JSON

### Enterprise API (API)

- [ ] **API-01**: Developer can access REST API with OpenAPI documentation
- [ ] **API-02**: Developer can authenticate using API keys
- [ ] **API-03**: System enforces tiered rate limiting (free/paid quotas)
- [ ] **API-04**: System provides usage metrics and dashboard

### Multi-Model Ensemble (ENSEMBLE)

- [ ] **ENSEMBLE-01**: System combines stylometric + perplexity + detector models for improved accuracy
- [ ] **ENSEMBLE-02**: System uses weighted voting based on model accuracy
- [ ] **ENSEMBLE-03**: User can view temporal analysis (writing timeline, injection detection)

### Enhanced Fingerprinting (PRINT)

- [ ] **PRINT-01**: User can build fingerprint from corpus of 10+ writing samples
- [ ] **PRINT-02**: System applies time-weighted training (recent writing weighted higher)
- [ ] **PRINT-03**: User receives alerts when writing style drifts significantly

### Style Transfer (STYLE)

- [ ] **STYLE-01**: User can adjust rewriting with granular controls (formality, sentence length, vocabulary)
- [ ] **STYLE-02**: System preserves intent while changing voice during rewrite
- [ ] **STYLE-03**: User can view A/B comparison (original vs rewritten side-by-side)

### Distribution (DIST)

- [ ] **DIST-01**: User can install browser extension (Chrome/Firefox) for inline detection
- [ ] **DIST-02**: User can integrate with Google Docs, Microsoft Word, or LMS platforms

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Reporting & Compliance

- **REPORT-01**: User can generate PDF reports with forensic analysis document
- **REPORT-02**: System maintains immutable audit log of all analyses
- **REPORT-03**: System provides evidence-grade timestamps and hashes
- **REPORT-04**: System implements GDPR compliance (data retention, right to delete)

### Advanced Analytics

- **ANALYTICS-01**: User can view analysis history with quick re-run capability
- **ANALYTICS-02**: User can view usage stats (documents analyzed, API calls, quota remaining)
- **ANALYTICS-03**: User can manage team (invite collaborators, share fingerprints)
- **ANALYTICS-04**: Admin can view system metrics (latency, throughput, error rates)
- **ANALYTICS-05**: Admin can view model performance trends over time

### Domain-Specific Models

- **DOMAIN-01**: System offers academic model for student submissions
- **DOMAIN-02**: System offers legal model for contracts/briefs
- **DOMAIN-03**: System offers journalism model for article verification
- **DOMAIN-04**: System offers technical model for code/documentation

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real-time collaboration editing | Focus is analysis, not co-creation. Crowded market (Google Docs). |
| Social features (sharing, comments) | Dilutes focus on analysis. Not social platform. |
| Mobile applications | High maintenance, limited utility. Mobile-responsive web sufficient. |
| Alternative LLM providers | Commit to Ollama for simplicity/cost control. Increases complexity. |
| Cloud hosting (AWS/GCP) | Self-hosted only. Data privacy appeal for enterprise/academics. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| EXP-01 | Phase 1 | Pending |
| EXP-02 | Phase 1 | Pending |
| EXP-03 | Phase 1 | Pending |
| EXP-04 | Phase 1 | Pending |
| BATCH-01 | Phase 2 | Pending |
| BATCH-02 | Phase 2 | Pending |
| BATCH-03 | Phase 2 | Pending |
| BATCH-04 | Phase 2 | Pending |
| API-01 | Phase 3 | Pending |
| API-02 | Phase 3 | Pending |
| API-03 | Phase 3 | Pending |
| API-04 | Phase 3 | Pending |
| ENSEMBLE-01 | Phase 4 | Pending |
| ENSEMBLE-02 | Phase 4 | Pending |
| ENSEMBLE-03 | Phase 4 | Pending |
| PRINT-01 | Phase 5 | Pending |
| PRINT-02 | Phase 5 | Pending |
| PRINT-03 | Phase 5 | Pending |
| STYLE-01 | Phase 6 | Pending |
| STYLE-02 | Phase 6 | Pending |
| STYLE-03 | Phase 6 | Pending |
| DIST-01 | Phase 7 | Pending |
| DIST-02 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 ✓

---

*Requirements defined: 2025-01-18*
*Last updated: 2025-01-18 after roadmap creation*
