# Architecture

**Analysis Date:** 2025-01-18

## Pattern Overview

**Overall:** Service-Oriented Architecture with Clear Separation of Concerns

**Key Characteristics:**
- Frontend-backend separation with REST API communication
- Layered backend architecture with dedicated services, models, and API routes
- ML pipeline with feature extraction, embeddings, and contrastive learning
- Background task processing with Celery for async operations
- Middleware-based cross-cutting concerns (rate limiting, security, metrics)

## Layers

**API Layer (Backend):**
- Purpose: HTTP interface, request validation, authentication, routing
- Location: `backend/app/api/routes/`
- Contains: FastAPI route handlers for auth, analysis, fingerprint, rewrite, analytics, account, admin
- Depends on: Services layer, models, middleware, utils
- Used by: Frontend via REST API

**Services Layer:**
- Purpose: Business logic orchestration, state management, external service coordination
- Location: `backend/app/services/`
- Contains: `AnalysisService`, `FingerprintService` - coordinate ML models, caching, database operations
- Depends on: ML layer, models, utils
- Used by: API routes

**ML Layer:**
- Purpose: Feature extraction, embeddings, fingerprinting, style rewriting
- Location: `backend/app/ml/`
- Contains: `feature_extraction.py`, `ollama_embeddings.py`, `contrastive_model.py`, `fingerprint.py`, `dspy_rewriter.py`
- Depends on: Ollama (external LLM), PyTorch, NLTK, numpy
- Used by: Services layer

**Models Layer:**
- Purpose: Database ORM models and Pydantic schemas
- Location: `backend/app/models/`
- Contains: `database.py` (SQLAlchemy ORM: User, WritingSample, Fingerprint, AnalysisResult, tokens), `schemas.py` (Pydantic request/response models)
- Depends on: SQLAlchemy, PostgreSQL
- Used by: All layers

**Middleware Layer:**
- Purpose: Cross-cutting concerns applied globally to requests
- Location: `backend/app/middleware/`
- Contains: `rate_limit.py`, `security_headers.py`, `audit_logging.py`, `metrics.py`, `input_sanitization.py`
- Depends on: slowapi, structlog, prometheus-client
- Used by: FastAPI application (applied in `backend/app/main.py`)

**Background Tasks Layer:**
- Purpose: Async job processing for maintenance and long-running operations
- Location: `backend/app/tasks/`
- Contains: `analysis_tasks.py`, scheduled cleanup tasks
- Depends on: Celery, Redis
- Used by: Celery worker process

**Frontend Layer:**
- Purpose: User interface, state management, API communication
- Location: `frontend/src/`
- Contains: React components, hooks, contexts, API client
- Depends on: Backend API via axios
- Used by: Browser clients

## Data Flow

**Text Analysis Flow:**

1. User submits text via frontend (`TextInput` component)
2. Frontend calls `analysisAPI.analyze()` in `frontend/src/services/api.ts`
3. FastAPI route handler at `backend/app/api/routes/analysis.py` receives request
4. Middleware chain executes: rate limit check, input sanitization, audit logging
5. `AnalysisService.analyze_text()` in `backend/app/services/analysis_service.py` orchestrates:
   - Text splitting by granularity (sentence/paragraph)
   - For each segment: `extract_feature_vector()` + `get_ollama_embedding()`
   - AI probability calculation using heuristics or fingerprint comparison
6. Results saved to `AnalysisResult` model in PostgreSQL
7. Response returned with segment-level AI probabilities for heat map visualization
8. Frontend renders `HeatMap` component with color-coded segments

**Authentication Flow:**

1. User submits credentials via `Login` component
2. Frontend calls `authAPI.login()` in `frontend/src/services/api.ts`
3. FastAPI route handler at `backend/app/api/routes/auth.py` validates credentials
4. Password verified against hash in `User` model
5. JWT access token generated and returned
6. Frontend stores token in localStorage
7. Subsequent API calls include token in Authorization header via axios interceptor

**Fingerprint Generation Flow:**

1. User uploads writing samples via `ProfileManager` component
2. Samples stored in `WritingSample` model
3. User triggers fingerprint generation
4. `FingerprintService` calls `generate_fingerprint()` in `backend/app/ml/fingerprint.py`
5. For each sample: `extract_feature_vector()` extracts 27 stylometric features
6. Feature vectors averaged to create user signature
7. Fingerprint stored in `Fingerprint` model as JSONB
8. Future analyses compare against this fingerprint for personalization

**State Management:**
- Backend: SQLAlchemy ORM with session-per-request pattern via `get_db()` dependency
- Frontend: React local component state + localStorage for auth token
- Cache: Redis (optional, via `backend/app/utils/cache.py`) for analysis results and features

## Key Abstractions

**AnalysisService:**
- Purpose: Orchestrates text analysis pipeline (feature extraction, embedding, scoring)
- Examples: `backend/app/services/analysis_service.py`
- Pattern: Singleton service with `get_analysis_service()` factory, separates orchestration from implementation

**Fingerprint:**
- Purpose: User writing signature as averaged feature vector
- Examples: `backend/app/ml/fingerprint.py`, `backend/app/models/database.py:Fingerprint`
- Pattern: Stored as JSONB in PostgreSQL, generated from multiple `WritingSample` records

**Feature Vector:**
- Purpose: 27-dimensional representation of text stylometric properties
- Examples: `backend/app/ml/feature_extraction.py:extract_feature_vector()`
- Pattern: L2-normalized numpy array with consistent feature ordering for model compatibility

**Middleware Pipeline:**
- Purpose: Apply cross-cutting concerns to all requests
- Examples: `backend/app/middleware/*.py`
- Pattern: FastAPI middleware executed in registration order (rate limit, metrics, audit logging, security headers, CORS)

## Entry Points

**Backend Application:**
- Location: `backend/app/main.py`
- Triggers: Uvicorn server startup (`uvicorn app.main:app --reload`)
- Responsibilities: FastAPI app initialization, middleware registration, router inclusion, startup event handlers, health/readiness/liveness/metrics endpoints

**Celery Worker:**
- Location: `backend/app/celery_app.py`
- Triggers: Celery worker process startup
- Responsibilities: Background task processing, periodic task scheduling (token cleanup, analysis result cleanup)

**Frontend Application:**
- Location: `frontend/src/main.tsx`, `frontend/src/App.tsx`
- Triggers: Browser loads the application
- Responsibilities: React root rendering, route definition, lazy-loaded component setup, context provider composition

**Vite Dev Server:**
- Location: `frontend/vite.config.ts`
- Triggers: `npm run dev` command
- Responsibilities: Hot module reloading, API proxy to backend, TypeScript compilation

## Error Handling

**Strategy:** Layered error handling with appropriate HTTP status codes and logging

**Patterns:**
- API routes: Try/except blocks returning `HTTPException` with 400/500 status codes
- Frontend: Axios interceptor extracts error messages from FastAPI validation responses
- Services: Raise `ValueError` for validation errors, let other exceptions propagate
- Middleware: Structured JSON logging via structlog with request context
- Sentry integration for production error tracking (configurable via SENTRY_DSN)

**Validation:**
- Pydantic schemas for request/response validation
- Custom validators in `backend/app/utils/file_validation.py`
- Input sanitization in `backend/app/middleware/input_sanitization.py` using bleach

## Cross-Cutting Concerns

**Logging:** Structured JSON logging via structlog, configured in `backend/app/main.py`. Includes request ID tracking, user context, and component status.

**Validation:** Pydantic schema validation on API routes, custom text length validation, file type validation for uploads.

**Authentication:** JWT-based authentication with access tokens (30min expiry) and refresh tokens (30 days). Token management via `RefreshToken` model. Login attempt tracking and account lockout after failed attempts.

**Rate Limiting:** Per-IP rate limits using slowapi with Redis backing (or in-memory fallback). Auth: 5/min, Analysis: 30/min, Rewrite: 10/min, General: 100/min.

**Metrics:** Prometheus metrics endpoint at `/metrics` via `MetricsMiddleware`. Tracks request counts, latencies, error rates.

**Security:** Security headers middleware, CORS configuration, input sanitization (bleach for HTML), SECRET_KEY validation in production.

**Caching:** Redis-backed caching for analysis results and feature vectors. Hash-based cache keys with optional per-user isolation.

**Audit Logging:** All analysis events logged with user_id, text_length, analysis_id, ai_probability.

---

*Architecture analysis: 2025-01-18*
