# Ghost-Writer

## What This Is

Ghost-Writer is an AI-generated text detection and stylometric analysis platform. Users can analyze text to determine whether it was written by AI or humans, create personal writing fingerprints for comparison, and rewrite text to match specific styles. The system uses machine learning (stylometric features, embeddings, contrastive learning) to provide detailed analysis with visual heat maps.

## Core Value

Reliable AI text detection with transparent explainability — users must understand WHY text was flagged, not just receive a probability score.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ User authentication (email/password, JWT sessions, email verification) — existing
- ✓ Single document text analysis with AI probability scoring — existing
- ✓ Stylometric feature extraction (27 features: burstiness, perplexity, rare words) — existing
- ✓ Heat map visualization showing sentence-level AI probabilities — existing
- ✓ Personal fingerprint generation from uploaded writing samples — existing
- ✓ Fingerprint-based analysis (compare text against user's writing style) — existing
- ✓ DSPy/Ollama-powered style rewriting (make text more human/AI-like) — existing
- ✓ PostgreSQL + Redis data persistence — existing
- ✓ Docker deployment (dev and production configurations) — existing
- ✓ Rate limiting, metrics, audit logging — existing

### Active

<!-- Current scope. Building toward these. -->

- [ ] Per-sentence confidence scores with feature attribution (explainability)
- [ ] Batch document analysis (multi-file upload, clustering, comparison matrix)
- [ ] Enterprise API layer (batch endpoints, job queue, API keys, rate limit tiers)
- [ ] Multi-model detection ensemble (stylometric + perplexity + detector model)
- [ ] Temporal analysis (writing timeline, draft comparison, injection detection)
- [ ] Domain-specific models (academic, legal, journalism, technical)
- [ ] Enhanced personal fingerprint (corpus builder, time-weighted training, style drift alerts)
- [ ] Authorship verification (disputed authorship, plagiarism-style reports)
- [ ] Advanced rewriting engine (granular controls, intent preservation, iterative refinement)
- [ ] Voice cloning from corpus (match tone, industry jargon injection)
- [ ] Browser extension (inline detection, right-click analyze, inbox scanning)
- [ ] Platform integrations (Google Docs, Microsoft Word, Slack/Teams, LMS)
- [ ] Reporting & compliance (PDF reports, audit trail, GDPR compliance)
- [ ] User dashboard (analysis history, usage stats, saved fingerprints, team management)
- [ ] Admin dashboard (system metrics, model performance, user analytics)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Real-time collaboration editing — Focus is analysis, not co-creation
- Social features (sharing, comments) — Enterprise/research tool, not social platform
- Mobile applications — Web-first, mobile responsive UI sufficient for current audience
- Alternative LLM providers — Committed to Ollama for privacy/cost control
- Cloud hosting (AWS/GCP) — Self-hosted Docker deployment maintains data control

## Context

Ghost-Writer began as a personal project to explore AI text detection using stylometric analysis. The current system (v1) is production-ready with core detection, fingerprinting, and rewriting capabilities. The platform has broad appeal across academic researchers (AI in student submissions), enterprise teams (HR screening, publishing), individuals (authorship verification), and developers (API integration).

The 6-phase roadmap represents natural evolution of the platform:
- Phase 1: Core enhancements (explainability, batch, API) — enterprise readiness
- Phase 2: Advanced detection (multi-model, temporal, domain-specific) — accuracy improvements
- Phase 3: Enhanced fingerprinting (corpus builder, authorship verification) — personalization
- Phase 4: Style transfer (advanced rewriting, voice cloning) — generative capabilities
- Phase 5: Distribution (browser extension, integrations) — accessibility
- Phase 6: Analytics (dashboards, reporting) — operational maturity

Technical architecture uses FastAPI (backend), React (frontend), PostgreSQL (data), Redis (cache/queue), and Ollama (LLM). ML pipeline relies on PyTorch, spaCy, NLTK for feature extraction and embeddings.

## Constraints

- **Tech Stack**: Python 3.10/TypeScript — Existing codebase, maintain consistency
- **LLM Dependency**: Ollama self-hosted — Privacy-first, no external API costs
- **Deployment**: Docker Compose — Self-hosted only, no cloud hosting plans
- **Timeline**: Ongoing — No deadline, personal project with sustainable pace
- **Data Privacy**: User text never sent externally — All processing local/self-hosted

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Ollama over OpenAI/Anthropic | Cost control, privacy, no rate limits | ✓ Good |
| FastAPI over Flask/Django | Async performance, modern Python ecosystem | ✓ Good |
| React over Vue/Svelte | Familiarity, existing component patterns | ✓ Good |
| Self-hosted only | Data privacy appeals to enterprise/academic users | — Pending |
| Per-sentence analysis | Granular explainability vs document-level score | ✓ Good |
| Contrastive learning over supervised | No need for labeled AI/human datasets | ✓ Good |

---

*Last updated: 2025-01-18 after initialization*
