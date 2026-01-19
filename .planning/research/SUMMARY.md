# Project Research Summary

**Project:** Ghost-Writer
**Domain:** AI Text Detection & Stylometric Analysis Platform
**Researched:** 2025-01-18
**Confidence:** HIGH

## Executive Summary

Ghost-Writer is an AI text detection platform with unique competitive advantages in stylometric analysis and personal fingerprinting. The platform currently exceeds MVP with core detection, heat map visualization, and style rewriting implemented. Research shows the market has matured into three tiers: basic detectors (document-level scoring), intermediate platforms (sentence-level analysis), and advanced systems (ensemble models, batch processing, enterprise APIs). Ghost-Writer currently sits in the intermediate tier but has differentiators (27+ stylometric features, personal fingerprinting) that competitors lack.

The recommended approach focuses on five architectural layers built incrementally: (1) multi-model ensemble for improved accuracy, (2) explainability layer using SHAP for feature attribution, (3) batch processing with Celery for enterprise workflows, (4) document clustering with pgvector for similarity search, and (5) browser extension with WXT framework for distribution. Key risks include adversarial text evasion (NEURIPS 2025 research shows universal attacks work), misleading attribution in explainability systems, and GPU memory exhaustion in Ollama deployments. Mitigation strategies include ensemble methods, uncertainty quantification with confidence intervals, and health checks with automatic restart.

Critical finding: Explainability has shifted from "nice-to-have" to table stakes. Users now demand per-sentence attribution, confidence intervals, and feature-level explanations. This aligns perfectly with Ghost-Writer's existing stylometric feature extraction (27+ features already computed but not fully exposed). The gap is not in detection capability but in enterprise features (batch processing, API access) and making explainability visible to users.

## Key Findings

### Recommended Stack

The stack builds strategically on existing foundation (FastAPI, PostgreSQL, Redis, Celery, Ollama, PyTorch). Only add new technologies where clear 2025 standard exists and no existing option suffices.

**Core additions:**
- **SHAP 0.50.0** — Model explainability (per-sentence attribution) — Industry standard in 2025, game-theoretic approach, model-agnostic
- **Celery 5.3.4** (existing) — Batch processing job queue — Already in stack, production-ready for document processing
- **scikit-learn 1.3.2** (existing) — Multi-model ensemble — Already in stack, comprehensive ensemble implementations
- **WXT** — Browser extension framework — Cross-browser (Chrome V3 + Firefox V2/V3), teams migrating from Plasmo to WXT in 2025
- **pgvector** (PostgreSQL extension) — Vector similarity search — Self-hosted, simpler than Qdrant for current scale, integrates with existing database

**Key decision:** Leverage existing stack where possible. Only SHAP, WXT, and pgvector are new additions. All other capabilities (ensemble, batch processing) use existing technologies.

### Expected Features

**Must have (table stakes):**
- Per-sentence feature attribution — Users expect transparency, not just "AI detected"
- Batch analysis with multi-file upload — Enterprise workflows process documents in bulk
- Enterprise API with auth, rate limiting, documentation — Developers integrate detection into workflows
- Export formats (CSV, JSON, PDF) — Integration with existing workflows
- Scan history and audit trail — Compliance and reference needs

**Should have (competitive differentiators):**
- Personal writing style fingerprint — Compare text against YOUR voice, not generic "human" (UNIQUE to Ghost-Writer)
- 27+ stylometric features with attribution — Deep linguistic insight beyond "AI detected" (competitive advantage)
- AI→Human style rewriting — Fix AI-generated text to sound natural (already implemented)
- Document clustering and similarity — Group related documents, detect content farms
- Model attribution (which AI generated text) — Actionable intelligence for investigation

**Defer (v2+):**
- Multi-model ensemble — High complexity, diminishing returns if current model is accurate
- Domain-specific models (academic, legal, journalism) — Requires training data per domain
- Temporal analysis (writing timeline) — Interesting but not urgent for enterprise readiness
- Voice cloning (fingerprint enhancement) — High complexity, Phase 4 feature

### Architecture Approach

Ghost-Writer follows a layered service-oriented pattern (API → Services → ML → Models) with FastAPI, PostgreSQL, Redis, Celery, and Ollama. Proposed enhancements require extending this architecture with five new subsystems that integrate cleanly with existing components. Each enhancement maps to a distinct architectural layer that can be built incrementally without disrupting core functionality.

**Major components:**
1. **Ensemble Orchestrator** — Coordinate multi-model inference (stylometric, embedding-based, contrastive) with model registry, aggregation engine (voting/stacking), and performance monitoring
2. **Explainability Engine** — SHAP/LIME integration for feature attribution with attribution calculator, explanation formatter, and cache manager for expensive computations
3. **Batch Processing Service** — Job orchestrator for multi-file analysis with progress tracking (WebSocket), result aggregation, and Celery worker coordination
4. **Clustering & Similarity Service** — Vector embedding manager with pgvector storage, similarity search engine (cosine similarity), and clustering algorithms (K-means, DBSCAN)
5. **Browser Extension** — Chrome/Firefox extension with content script (page interaction), background service worker (API calls), and popup UI (quick analysis)

### Critical Pitfalls

**Top 5 from research:**

1. **Misleading Attribution in Explainability Systems** — Feature attribution methods (SHAP, LIME) claim to explain predictions but show spurious correlations. Prevention: Always show calibrated confidence intervals, use multiple attribution methods, add explicit disclaimers about causal meaning.

2. **Adversarial Text Evades All Detection Models** — Minor token-level perturbations completely bypass AI detection. Universal attacks work across multiple detector types (NEURIPS 2025). Prevention: NEVER claim "bypass-proof," implement ensemble of detection methods, add adversarial training.

3. **GPU Memory Exhaustion in Ollama Deployments** — Ollama models consume unreleased GPU memory (up to 6GB) after connection errors. KV cache memory leaks accumulate until OOM killer terminates container. Prevention: Implement health checks with automatic restart, use single GPU per model, enable Flash Attention.

4. **Stylometric False Positives from Closed-World Assumption** — Authorship verification fails when true author isn't in candidate set. High precision methods still produce false positives when imposter authors have similar writing styles. Prevention: Implement open-set recognition, require minimum text length (500+ words), show calibration ("90% confident this matches User X vs other candidates").

5. **Ensemble Model Calibration Drift** — Multi-model ensembles become overconfident over time, showing 95%+ confidence on wrong predictions. Calibration drifts as individual models degrade at different rates. Prevention: Implement temperature scaling, regular recalibration on held-out data, monitor calibration metrics (ECE, Brier score).

## Implications for Roadmap

Based on research, suggested phase structure follows dependency chains and build order from architecture:

### Phase 1: Enterprise Foundation
**Rationale:** Table stakes gaps (per-sentence attribution, batch processing, API access) block enterprise adoption. These features have clear patterns and high confidence research.

**Delivers:**
- Per-sentence feature attribution using SHAP (exposes existing 27+ stylometric features)
- Batch processing with Celery for multi-file upload with progress tracking
- Enterprise API layer with authentication, rate limiting, OpenAPI documentation
- Export formats (CSV, JSON, PDF) and scan history

**Addresses:** Table stakes from FEATURES.md (explainability, batch analysis, API access)

**Avoids:** Misleading attribution (Pitfall 1) by including uncertainty quantification; API key leakage (Pitfall 6) with scoped keys and rotation; batch memory exhaustion (Pitfall 5) with Redis-backed queues

**Stack used:** SHAP 0.50.0, Celery 5.3.4 (existing), FastAPI (existing), Redis (existing)

### Phase 2: Advanced Detection
**Rationale:** Multi-model ensemble improves core detection accuracy, which all other features depend on. Research shows ensemble methods reduce both false positives and false negatives.

**Delivers:**
- Multi-model ensemble (stylometric + embedding-based + contrastive)
- Weighted voting and stacking classifiers
- Model registry with versioning and health checks
- Adversarial training to improve robustness

**Uses:** scikit-learn 1.3.2 (existing), PyTorch (existing)

**Implements:** Ensemble Orchestrator from ARCHITECTURE.md

**Avoids:** Adversarial evasion (Pitfall 2) with ensemble methods; ensemble calibration drift (Pitfall 8) with temperature scaling and recalibration

### Phase 3: Enhanced Analytics
**Rationale:** Document clustering and similarity search build on batch processing (for efficient embedding generation) and provide enterprise value for content farms detection.

**Delivers:**
- Document clustering with K-means/DBSCAN
- Vector similarity search with pgvector
- Near-duplicate detection
- Similarity matrices for document groups

**Uses:** pgvector (new), scikit-learn (existing), Ollama embeddings (existing)

**Implements:** Clustering & Similarity Service from ARCHITECTURE.md

**Avoids:** Naive vector search without indexing (anti-pattern) by using IVFFlat indexes

### Phase 4: Style Transfer Enhancement
**Rationale:** Enhance existing style rewriting (AI→Human) with fingerprint-based personalization. Differentiator that competitors lack.

**Delivers:**
- Fingerprint-based style rewriting (match user's voice)
- Corpus builder for improving fingerprint over time
- Time-weighted training to account for style evolution
- Style drift alerts

**Uses:** Existing DSPy/Ollama implementation, existing contrastive model

**Avoids:** Contrastive learning false performance signals (Pitfall 9) with proper evaluation on balanced datasets

### Phase 5: Distribution
**Rationale:** Browser extension depends on stable API contract from all backend features. Build last to avoid breaking changes.

**Delivers:**
- Chrome/Firefox browser extension with WXT framework
- Inline detection on web pages
- Context menu integration ("Analyze with Ghost-Writer")
- API communication with auth and caching

**Uses:** WXT framework (new), existing API endpoints

**Implements:** Browser Extension from ARCHITECTURE.md

**Avoids:** Content script performance degradation (Pitfall 7) with deferred analysis and code splitting; permission bloat (Pitfall 14) with specific host permissions

### Phase Ordering Rationale

**Why this order:**
- **Phase 1 first:** Table stakes features (explainability, batch, API) block enterprise adoption but have well-documented patterns. Leverages existing stylometric features that are currently hidden.
- **Phase 2 second:** Ensemble improves core detection accuracy, making all downstream features more reliable. Research shows adversarial attacks are critical threat.
- **Phase 3 third:** Clustering depends on batch processing for efficient embedding generation. Advanced analytics feature that builds on stable analysis pipeline.
- **Phase 4 fourth:** Style transfer enhancement differentiates Ghost-Writer but is not required for enterprise readiness.
- **Phase 5 last:** Browser extension depends on stable API contract from all backend features. Can be developed in parallel but deployment should wait.

**Why this grouping:**
- Phase 1 groups table stakes features together for enterprise readiness
- Phase 2-3 group advanced ML capabilities (ensemble, clustering)
- Phase 4-5 group user-facing distribution features (style enhancement, browser extension)

**How this avoids pitfalls:**
- Phase 1 addresses misleading attribution (Pitfall 1) with uncertainty quantification
- Phase 2 addresses adversarial evasion (Pitfall 2) with ensemble methods
- Phase 3 addresses naive vector search (anti-pattern) with proper indexing
- Phase 5 addresses extension performance (Pitfall 7) with deferred loading
- All phases address GPU memory leaks (Pitfall 3) with health checks

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 2 (Multi-model Ensemble):** Complex integration, calibration methods need validation with official documentation. Research shows ensemble calibration drift is critical issue.
- **Phase 3 (Document Clustering):** Limited specific research on clustering AI-generated vs human documents. Need to validate K-means vs DBSCAN for this use case.
- **Phase 5 (Browser Extension):** Performance best practices not well-documented for 2025. Need to research current Chrome extension performance benchmarks.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Enterprise Foundation):** Well-documented patterns. SHAP integration (official docs), Celery batch processing (2025 production guides), FastAPI (best practices established).
- **Phase 4 (Style Transfer):** Existing implementation with DSPy/Ollama. Enhancement pattern is straightforward.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies verified with 2025 sources. SHAP (PyPI 0.50.0), WXT (2025 comparisons favor it), Celery/scikit-learn (existing) |
| Features | HIGH | Table stakes verified across competitor comparison articles (GPTZero, Originality.AI, Copyleaks). Differentiators confirmed as unique to Ghost-Writer |
| Architecture | HIGH | Component boundaries and data flow patterns verified with official docs (FastAPI, Celery, Chrome extensions, pgvector). Build order follows clear dependencies |
| Pitfalls | HIGH | Adversarial attacks (NEURIPS 2025, USENIX Security 2025), explainability pitfalls (multiple 2024-2025 papers), infrastructure issues (directly observed in codebase) |

**Overall confidence:** HIGH

**Research quality:**
- Stack: All technologies verified with official sources or 2025 ecosystem research
- Features: Table stakes confirmed by multiple competitor comparisons; differentiators validated as unique
- Architecture: Patterns verified with official documentation; implementation examples provided
- Pitfalls: Critical pitfalls backed by peer-reviewed research or production incident reports

### Gaps to Address

**Medium confidence areas requiring validation during implementation:**

1. **Document clustering for AI detection** — Research found general text clustering methods but no specific research on clustering AI-generated vs human documents. Handle by: Testing both K-means and DBSCAN on labeled dataset, using silhouette score to evaluate cluster quality.

2. **Browser extension performance benchmarks** — Limited 2025-specific performance data for content scripts. Handle by: Testing extension on performance-critical sites (Facebook, Twitter, Gmail), using Chrome DevTools to measure content script evaluation time.

3. **Multi-model ensemble calibration** — Research shows calibration drift is critical but specific methods for AI text detection ensembles not documented. Handle by: Implementing temperature scaling with regular recalibration on held-out data, monitoring calibration metrics (ECE, Brier score).

4. **Ollama GPU memory leaks** — Based on community reports, not official documentation. Handle by: Implementing health checks with automatic restart, monitoring GPU memory usage, having vLLM as fallback option.

**Low confidence areas (not critical for initial phases):**

1. **Enterprise API rate limiting tiers** — No specific data on AI detection API pricing/tiers. Handle by: Researching competitor API pricing during Phase 1 planning, starting with conservative limits.

2. **Temporal analysis for writing timeline** — Interesting but deferred to post-MVP. Not needed for current roadmap.

3. **Voice cloning for fingerprint enhancement** — High complexity, Phase 4 feature. Can research when closer to implementation.

## Sources

### Primary (HIGH confidence)
**STACK sources:**
- [SHAP PyPI](https://pypi.org/project/shap/) — Latest version 0.50.0 (2025-11-11)
- [WXT Comparison Page](https://wxt.dev/guide/resources/compare) — Official comparison (updated Feb 2025)
- [Celery Documentation](https://docs.celeryq.dev/en/stable/) — Version 5.6.2
- [scikit-learn Ensemble Guide](https://scikit-learn.org/stable/modules/ensemble.html) — Official documentation v1.8.0
- [Qdrant Documentation](https://qdrant.tech/documentation/) — Official docs
- [pgvector GitHub Repository](https://github.com/pgvector/pgvector) — Official pgvector documentation

**FEATURES sources:**
- [GPTZero - 7 Best AI Detectors 2025](https://gptzero.me/news/best-ai-detectors/) — Detailed feature comparison, accuracy benchmarks
- [Eden AI - Best AI Content Detection APIs 2025](https://www.edenai.co/post/best-ai-content-detection-apis) — API comparison, use cases
- [Detecting AI - Top Features 2025](https://detectingai.uz/blog/top-features-to-look-for-in-ai-detector-tools-in-2025) — Feature requirements, user expectations

**ARCHITECTURE sources:**
- [Explainable AI in Production: SHAP and LIME for Real-time Predictions](https://www.javacodegeeks.com/2025/03/explainable-ai-in-production-shap-and-lime-for-real-time-predictions.html) — Production deployment strategies
- [Building Scalable Background Jobs with FastAPI + Celery + Redis](https://medium.com/@shaikhasif03/building-scalable-background-jobs-with-fastapi-celery-redis-e43152829c61) — Practical implementation guide
- [Content scripts - Chrome for Developers](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts) — Official documentation
- [Vector Similarity Search Deep Dive](https://severalnines.com/blog/vector-similarity-search-with-postgresqls-pgvector-a-deep-dive/) — In-depth exploration

**PITFALLS sources:**
- [NEURIPS 2025: A Universal Attack for Humanizing AI-Generated Text](https://neurips.cc/virtual/2025/poster/116833) — Universal adversarial attacks
- [ScienceDirect: Explainability pitfalls in XAI (2024, 100+ citations)](https://www.sciencedirect.com/science/article/pii/S2666389924000795) — XAI pitfalls
- [Google Vertex AI: Overconfidence in neural networks](https://cloud.google.com/vertex-ai/docs/explainable-ai/overview) — Official documentation on overconfidence
- [USENIX Security 2025: GradEscape gradient-based evader](https://www.usenix.org/system/files/usenixsecurity25-meng.pdf) — Adversarial attacks
- [ArXiv: Human-AI Collaboration challenges (May 2025)](https://arxiv.org/pdf/2505.08828) — Stylometric false positives
- [Zuplo: 10 best practices for API rate limiting in 2025](https://zuplo.com/learning-center/10-best-practices-for-api-rate-limiting-in-2025) — API security best practices

### Secondary (MEDIUM confidence)
**STACK sources:**
- [Chrome Extension Framework Comparison 2025](https://www.devkit.best/blog/mdx/chrome-extension-framework-comparison-2025) — December 19, 2025
- [Why We Migrated from Plasmo to WXT](https://jetwriter.ai/blog/migrate-plasmo-to-wxt) — Real-world migration (Sept 2024)
- [Best Vector Databases 2025](https://www.firecrawl.dev/blog/best-vector-databases-2025) — October 20, 2025 comparison

**FEATURES sources:**
- [Zapier - Best AI Content Detectors 2025](https://zapier.com/blog/ai-content-detector/) — Tool comparisons, accuracy focus
- [MDPI Mathematics - Weighted-Voting Ensemble for Fake News Detection](https://www.mdpi.com/2227-7390/13/3/449) — Ensemble methods for detection

**ARCHITECTURE sources:**
- [FastAPI Best Practices: A Complete Guide](https://medium.com/@abipoongodi1211/fastapi-best-practices-a-complete-guide-for-building-production-ready-apis-bb27062d7617) — Comprehensive best practices
- [Celery + Redis + FastAPI: The Ultimate 2025 Production Guide](https://medium.com/@dewasheesh.rana/celery-redis-fastapi-the-ultimate-2025-production-guide-broker-vs-backend-explained-5b84ef508fa7) — Production best practices

**PITFALLS sources:**
- [DataAnnotation.tech: Queue implementations breaking in production](https://www.dataannotation.tech/developers/queue-implementations?) — Queue failure patterns
- [Cloudflare: Rate limiting best practices](https://developers.cloudflare.com/waf/rate-limiting-rules/best-practices/) — Security practices
- [BioRxiv: Calibrated ensembles reduce overfitting](https://www.biorxiv.org/content/10.1101/2021.07.26.453832.full) — Ensemble calibration

### Tertiary (LOW confidence)
**FEATURES sources:**
- [HasteWire - Can Stylometry Detect AI Authorship?](https://hastewire.com/blog/can-stylometry-detect-ai-authorship-methods-explained) — Stylometric features overview (single source)
- [ResearchGate - Text Clustering for Scientific Articles](https://www.researchgate.net/publication/396361654_Text_clustering_for_analyzing_scientific_article_using_pre-trained_language_model_and_k-means_algorithm) — Clustering applications (not AI-specific)

**PITFALLS sources:**
- Browser extension performance issues — Based on general web search, limited official documentation
- Ollama-specific GPU memory leaks — Based on community reports, not official docs

---
*Research completed: 2025-01-18*
*Ready for roadmap: yes*
