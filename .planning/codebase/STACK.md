# Technology Stack

**Analysis Date:** 2025-01-18

## Languages

**Primary:**
- Python 3.10 - Backend API, ML models, data processing
- TypeScript - Frontend React application

**Secondary:**
- SQL - PostgreSQL database queries and migrations
- Shell - Bash scripts for container management and deployment

## Runtime

**Environment:**
- Python 3.10 (backend via Docker)
- Node.js 18 (frontend via Docker)

**Package Manager:**
- pip (Python) - Lockfile: present in `backend/requirements.txt`
- npm (Node.js) - Lockfile: present in `frontend/package-lock.json`

## Frameworks

**Core:**
- FastAPI 0.104.1 - Async REST API backend (`backend/app/main.py`)
- React 18.2.0 - Frontend UI framework
- Vite 5.0.0 - Frontend build tool and dev server (`frontend/vite.config.ts`)

**Testing:**
- Vitest 1.0.0 - Frontend unit testing (`frontend/vitest.config.ts`)
- pytest (Python) - Backend testing (used in CI)
- Testing Library - React component testing

**Build/Dev:**
- Docker Compose - Multi-container orchestration (`docker-compose.yml`)
- Uvicorn 0.24.0 - ASGI server for FastAPI
- Tailwind CSS 3.4.1 - Utility-first CSS framework
- TypeScript 5.2.2 - Frontend type safety
- Alembic 1.12.1 - Database migrations (`backend/alembic/`)

**ML/AI:**
- PyTorch 2.1.0 - Deep learning framework
- DSPy 2.3.5 - LLM orchestration and prompting
- spaCy 3.7.2 - NLP feature extraction
- NLTK 3.8.1 - Text processing and tokenization
- scikit-learn 1.3.2 - ML utilities
- NumPy 1.24.3 - Numerical computing
- Pandas 2.1.3 - Data manipulation

## Key Dependencies

**Critical:**
- SQLAlchemy 2.0.23 - Database ORM (`backend/app/models/database.py`)
- psycopg2-binary 2.9.9 - PostgreSQL adapter
- Pydantic 2.5.0 - Data validation and settings
- python-jose 3.3.0 - JWT token handling
- passlib 1.7.4 - Password hashing with bcrypt
- axios 1.6.2 - Frontend HTTP client (`frontend/src/services/api.ts`)

**Infrastructure:**
- Redis 5.0.1 - Caching and Celery broker
- Celery 5.3.4 - Background task processing (`backend/app/celery_app.py`)
- slowapi 0.1.9 - Rate limiting
- structlog 23.2.0 - Structured logging
- prometheus-client 0.19.0 - Metrics collection
- sentry-sdk 1.40.0 - Error tracking and monitoring

**ML/Feature Extraction:**
- requests 2.31.0 - HTTP client for Ollama API
- python-docx 1.1.0 - Word document parsing
- PyPDF2 3.0.1 - PDF document parsing
- reportlab 4.0.0 - PDF generation (demo data)

**Frontend Libraries:**
- React Router DOM 6.20.0 - Client-side routing
- Framer Motion 12.24.12 - Animation library
- Recharts 3.6.0 - Data visualization
- React Syntax Highlighter 15.5.0 - Code syntax highlighting
- Lucide React 0.562.0 - Icon library
- clsx 2.1.1 - Conditional className utility

## Configuration

**Environment:**
- Python dotenv for environment variable loading
- Environment-specific configs via `ENVIRONMENT` variable (development/production/test)
- CORS origins configurable via `CORS_ORIGINS` env var

**Key configs required:**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT signing key (must be strong in production)
- `OLLAMA_BASE_URL` - Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Model name (default: llama3.1:8b)
- `CORS_ORIGINS` - Comma-separated allowed frontend origins
- `SENTRY_DSN` - Optional Sentry error tracking

**Build:**
- `docker-compose.yml` - Development orchestration
- `docker-compose.prod.yml` - Production orchestration
- `backend/Dockerfile` - Multi-stage Python build
- `frontend/Dockerfile` - Node.js Alpine build
- `frontend/Dockerfile.prod` - Production Nginx build
- `Makefile` - Development commands wrapper
- `nginx.conf` - Reverse proxy configuration

## Platform Requirements

**Development:**
- Docker and Docker Compose (recommended)
- Python 3.10+ (if running locally)
- Node.js 18+ (if running locally)
- PostgreSQL 14+ (if running locally)
- Redis 7+ (if running locally)
- Ollama server with llama3.1:8b model pulled

**Production:**
- Docker-compatible runtime
- PostgreSQL 14+ database
- Redis 7+ for caching/Celery
- Ollama server accessible via `OLLAMA_BASE_URL`
- Nginx reverse proxy (included in docker-compose)

**Optional:**
- Sentry account for error tracking
- Prometheus-compatible metrics server

---

*Stack analysis: 2025-01-18*
