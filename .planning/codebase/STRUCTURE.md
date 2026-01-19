# Codebase Structure

**Analysis Date:** 2025-01-18

## Directory Layout

```
[project-root]/
├── backend/          # FastAPI backend application
├── frontend/         # React + Vite frontend application
├── ml_models/        # ML training scripts and model checkpoints
├── e2e/              # End-to-end tests
├── docs/             # Documentation
├── .github/          # GitHub workflows (CI/CD)
├── .planning/        # Planning documents (GSD framework)
└── [config files]    # Docker compose, nginx, Makefile, scripts
```

## Directory Purposes

**backend/:**
- Purpose: Python FastAPI application serving REST API
- Contains: API routes, services, ML models, database models, middleware, background tasks, tests
- Key files: `backend/app/main.py` (FastAPI app entry point), `backend/app/api/routes/` (API endpoints)

**frontend/:**
- Purpose: React TypeScript SPA for user interface
- Contains: React components, hooks, contexts, API client, utilities, tests
- Key files: `frontend/src/App.tsx` (React root), `frontend/src/services/api.ts` (API client)

**ml_models/:**
- Purpose: Training scripts and model checkpoints for ML components
- Contains: Training data, model artifacts, training notebooks
- Key files: `ml_models/data/training_samples/` (sample data for training)

**e2e/:**
- Purpose: End-to-end integration tests
- Contains: Playwright/spec-style tests covering full user flows
- Key files: `e2e/tests/analysis.spec.ts`, `e2e/tests/auth.spec.ts`

**docs/:**
- Purpose: Project documentation
- Contains: Setup guides, architecture docs, deployment instructions

**.github/workflows/:**
- Purpose: GitHub Actions CI/CD pipelines
- Contains: Automated testing and deployment workflows

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI application initialization, middleware registration, router inclusion
- `backend/app/celery_app.py`: Celery worker configuration for background tasks
- `frontend/src/main.tsx`: React application bootstrap
- `frontend/vite.config.ts`: Vite dev server configuration with API proxy

**Configuration:**
- `docker-compose.yml`: Development environment orchestration (postgres, redis, backend, frontend, nginx)
- `docker-compose.prod.yml`: Production environment configuration
- `backend/alembic.ini`: Database migration configuration
- `backend/Dockerfile`: Backend container build definition
- `frontend/Dockerfile`: Frontend container build definition
- `nginx.conf`: Reverse proxy configuration
- `backend/requirements.txt`: Python dependencies
- `frontend/package.json`: Node dependencies and scripts

**Core Logic:**
- `backend/app/api/routes/`: REST API endpoint handlers
- `backend/app/services/`: Business logic services (AnalysisService, FingerprintService)
- `backend/app/ml/`: ML pipeline (feature extraction, embeddings, fingerprinting, rewriting)
- `backend/app/models/`: Database ORM and Pydantic schemas
- `backend/app/middleware/`: Request/response middleware
- `frontend/src/components/`: React UI components organized by feature

**Testing:**
- `backend/tests/`: Pytest-based unit and integration tests
- `frontend/src/test/`: Vitest configuration and setup
- `frontend/src/**/*.test.tsx`: Co-located component tests
- `backend/tests/load/locustfile.py`: Load testing configuration
- `e2e/tests/`: End-to-end Playwright tests

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `feature_extraction.py`, `rate_limit.py`)
- React components: `PascalCase.tsx` (e.g., `TextInput.tsx`, `ProfileManager.tsx`)
- Test files: `*.test.tsx` (frontend), `test_*.py` (backend)
- Utility files: `*.utils.ts` (frontend), `*.py` (backend utils)

**Directories:**
- Feature components: `PascalCase/` (e.g., `frontend/src/components/TextInput/`)
- Shared UI: `ui/` (e.g., `frontend/src/components/ui/`)
- Backend modules: `snake_case/` (e.g., `backend/app/api/routes/`)

**Functions:**
- Python: `snake_case` (e.g., `extract_feature_vector`, `get_analysis_service`)
- TypeScript: `camelCase` (e.g., `analyze`, `getErrorMessage`)

## Where to Add New Code

**New Feature (Backend):**
- Primary code: `backend/app/api/routes/[feature].py` (API endpoints)
- Business logic: `backend/app/services/[feature]_service.py`
- Tests: `backend/tests/test_[feature]_routes.py`, `backend/tests/test_[feature]_service.py`

**New Feature (Frontend):**
- Component: `frontend/src/components/[FeatureName]/[FeatureName].tsx`
- Tests: `frontend/src/components/[FeatureName]/[FeatureName].test.tsx`
- API calls: Add to `frontend/src/services/api.ts` (authAPI, analysisAPI, etc.)

**New Component/Module:**
- Implementation: `frontend/src/components/[ComponentName]/[ComponentName].tsx`
- Styles: Co-located CSS modules or Tailwind classes
- Tests: `frontend/src/components/[ComponentName]/[ComponentName].test.tsx`

**Utilities:**
- Shared helpers: `frontend/src/utils/[utility].ts` (e.g., `cn.ts` for className merging)
- Backend utils: `backend/app/utils/[utility].py` (e.g., `auth.py`, `cache.py`)

**New ML Feature:**
- Implementation: `backend/app/ml/[feature].py`
- Service integration: Call from `backend/app/services/analysis_service.py`
- Tests: `backend/tests/test_[feature].py`

**New Database Model:**
- Definition: `backend/app/models/database.py` (SQLAlchemy ORM)
- Schema: `backend/app/models/schemas.py` (Pydantic)
- Migration: `backend/alembic/versions/[version]_[description].py`

## Special Directories

**backend/alembic/versions/:**
- Purpose: Database migration scripts
- Generated: Yes (via `alembic revision --autogenerate`)
- Committed: Yes

**frontend/src/components/ui/:**
- Purpose: Shared/reusable UI components (Button, Card, Modal, etc.)
- Generated: No
- Committed: Yes

**backend/app/middleware/:**
- Purpose: Cross-cutting request/response processing
- Generated: No
- Committed: Yes

**ml_models/data/training_samples/:**
- Purpose: Sample data for ML model training
- Generated: Partially (can include user-generated samples)
- Committed: Depends (check .gitignore)

**node_modules/, venv/, __pycache__/:**
- Purpose: Dependency installation and Python bytecode
- Generated: Yes
- Committed: No (excluded by .gitignore)

**.planning/codebase/:**
- Purpose: GSD framework analysis documents (this file, ARCHITECTURE.md, etc.)
- Generated: Yes (by GSD agents)
- Committed: Yes

---

*Structure analysis: 2025-01-18*
