# External Integrations

**Analysis Date:** 2025-01-18

## APIs & External Services

**LLM/Embeddings:**
- Ollama (local LLM server) - Text embeddings and style rewriting
  - SDK/Client: HTTP via requests library
  - Base URL: `OLLAMA_BASE_URL` env var (default: http://localhost:11434)
  - Model: `OLLAMA_MODEL` env var (default: llama3.1:8b)
  - Endpoints used:
    - `/api/embeddings` - Get text embeddings (`backend/app/ml/ollama_embeddings.py`)
    - `/v1/chat/completions` - OpenAI-compatible chat endpoint
    - `/api/generate` - Legacy generation endpoint
    - `/api/tags` - List available models
  - Implementation: `backend/app/ml/ollama_embeddings.py`, `backend/app/ml/dspy_rewriter.py`

**Monitoring & Observability:**
- Sentry (optional) - Error tracking and performance monitoring
  - SDK/Client: sentry-sdk[fastapi] 1.40.0
  - Config: `SENTRY_DSN` env var
  - Auto-initialized on startup if DSN provided
  - Integrations: FastAPI, SQLAlchemy
  - Traces sample rate: 10%
  - Implementation: `backend/app/main.py` startup event

## Data Storage

**Databases:**
- PostgreSQL 14
  - Connection: `DATABASE_URL` env var (format: postgresql://user:pass@host:port/db)
  - Client: SQLAlchemy 2.0.23 ORM with psycopg2-binary adapter
  - Connection pooling: Enabled with pool_pre_ping and pool_recycle=300
  - Migrations: Alembic 1.12.1 (`backend/alembic/`)
  - Models defined in: `backend/app/models/database.py`
  - Tables: users, writing_samples, fingerprints, analysis_results, refresh_tokens, password_reset_tokens, email_verification_tokens
  - Docker service: `postgres` (port 5432)

**Caching:**
- Redis 7 (Alpine)
  - Connection: `REDIS_URL` env var (format: redis://host:port/db)
  - Client: redis-py 5.0.1
  - Uses: Celery broker/backend, analysis result caching
  - Docker service: `redis` (port 6379)
  - Persistence: AOF enabled (appendonly yes)

**File Storage:**
- Local filesystem only
- Document uploads stored temporarily in memory/FormData
- ML models stored in: `ml_models/` volume (Docker) or local directory
- No S3 or cloud storage integration

## Authentication & Identity

**Auth Provider:**
- Custom JWT-based authentication
  - Implementation: FastAPI dependency injection
  - JWT handling: python-jose[cryptography] with HS256 algorithm
  - Password hashing: passlib[bcrypt] with bcrypt rounds
  - Token expiration: 30 minutes (access), 30 days (refresh)
  - Implementation files:
    - `backend/app/api/routes/auth.py` - Auth endpoints
    - `backend/app/middleware/` - Security middleware
  - Features:
    - Email verification tokens
    - Password reset tokens
    - Refresh token rotation
    - Account lockout after failed login attempts
    - Rate limiting on auth endpoints (5 req/min)

## Monitoring & Observability

**Error Tracking:**
- Sentry (optional/configurable)
  - Environment variable: `SENTRY_DSN`
  - SDK: sentry-sdk[fastapi]
  - Integrations: FastApiIntegration, SqlalchemyIntegration
  - Environment tagging via `ENVIRONMENT` var
  - Initialization: `backend/app/main.py` startup_event

**Metrics:**
- Prometheus metrics endpoint
  - Path: `/metrics`
  - Client: prometheus-client 0.19.0
  - Custom middleware: `backend/app/middleware/metrics.py`
  - Metrics collected: Request counts, latencies, error rates

**Logs:**
- Structured JSON logging via structlog
  - Framework: structlog 23.2.0
  - Format: JSON with timestamp, level, logger name
  - Configuration: `backend/app/main.py`
  - Audit logging: `backend/app/middleware/audit_logging.py`
  - Logs all API requests with user context

**Health Checks:**
- Multiple health endpoints:
  - `/health` - Comprehensive health with component status (DB, Ollama, Redis, ML model)
  - `/ready` - Readiness probe for Kubernetes
  - `/live` - Liveness probe for Kubernetes

## CI/CD & Deployment

**Hosting:**
- Self-hosted via Docker Compose
- Production configuration: `docker-compose.prod.yml`
- Development configuration: `docker-compose.yml`

**CI Pipeline:**
- GitHub Actions
  - Backend lint: flake8, black
  - Backend tests: pytest with coverage
  - Frontend lint: ESLint
  - Frontend build: npm run build
  - Security scan: Trivy vulnerability scanner
  - Workflows: `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`

**Build/Deployment:**
- Docker Compose for orchestration
- Multi-stage Docker builds:
  - Backend: Python 3.10-slim with build stage
  - Frontend: Node 18-alpine (dev) or Nginx (prod)
- Nginx reverse proxy for production
- Health checks on all services
- Resource limits configured

## Environment Configuration

**Required env vars:**
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Strong random string for JWT signing (production)
- `OLLAMA_BASE_URL` - Ollama server URL
- `OLLAMA_MODEL` - Model name to use

**Optional env vars:**
- `REDIS_URL` - Redis connection (default: redis://localhost:6379/0)
- `CORS_ORIGINS` - Allowed frontend origins (default: localhost:3000,5173)
- `FRONTEND_URL` - Frontend base URL
- `ENVIRONMENT` - Environment name (development/production/test)
- `SENTRY_DSN` - Sentry error tracking
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` - Database credentials
- `BACKEND_PORT`, `FRONTEND_PORT`, `POSTGRES_PORT` - Port overrides
- `OLLAMA_EMBEDDING_MODEL` - Specific model for embeddings

**Secrets location:**
- Environment variables (not committed to git)
- No secrets in codebase
- Production secrets must be provided at runtime

## Webhooks & Callbacks

**Incoming:**
- None - No webhook endpoints exposed

**Outgoing:**
- None - No outgoing webhooks configured

**Background Tasks:**
- Celery tasks for async operations
  - Task: `app.tasks.analyze_text_async` - Long-running text analysis
  - Scheduled tasks:
    - `cleanup-expired-tokens` - Every hour
    - `cleanup-old-analysis-results` - Every day
  - Implementation: `backend/app/celery_app.py`, `backend/app/tasks/`
  - Worker: `celery_worker` service in docker-compose

## External Dependencies

**Python ML Downloads (runtime):**
- spaCy model: `en_core_web_sm` (downloaded on build/startup)
- NLTK data: punkt, averaged_perceptron_tagger, stopwords, wordnet (downloaded on startup)
- Downloads handled in: `backend/Dockerfile`

**Node.js Dependencies:**
- All packages managed via npm
- No post-install hooks requiring external services

---

*Integration audit: 2025-01-18*
