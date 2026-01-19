# AGENTS.md

This file is for agentic coding assistants working in this repository.
Follow the project conventions and prefer existing patterns over invention.

## Repository Overview
- Backend: FastAPI + SQLAlchemy + Alembic (Python)
- Frontend: React + TypeScript + Vite
- E2E: Playwright
- Orchestration: Docker Compose (via Makefile)

## Core Commands (Project Root)
- `make help`: list available Makefile targets
- `make build`: build Docker images
- `make up`: start all services (detached)
- `make up-logs`: start all services with logs
- `make down`: stop all services
- `make restart`: restart services (keep volumes/images)
- `make restart-clean`: restart and remove volumes (database reset)
- `make restart-all`: remove volumes and images
- `make logs`: stream logs for all services
- `make logs-backend`: stream backend logs
- `make logs-frontend`: stream frontend logs
- `make logs-db`: stream database logs
- `make status`: show container status
- `make migrate`: run Alembic migrations
- `make seed`: create default demo user
- `make test`: run backend tests in Docker

## Backend (Python / FastAPI)
Working directory: `backend`

### Setup
- `pip install -r requirements.txt`
- `pip install -r requirements-dev.txt`

### Run
- `uvicorn app.main:app --reload`

### Tests
- Run all tests: `pytest`
- Verbose: `pytest -v`
- Skip slow tests: `pytest -m "not slow"`
- Coverage report: `pytest --cov=app --cov-report=term-missing --cov-report=html`
- Single test file: `pytest tests/test_auth_routes.py`
- Single test function: `pytest tests/test_auth_routes.py::test_register_success`
- Single test class: `pytest tests/test_auth_routes.py::TestAuthRoutes`
- Keyword match: `pytest -k "register"`
- Stop on first failure: `pytest -x tests/test_auth_routes.py`
- Show prints: `pytest tests/test_auth_routes.py -s`

### Test Expectations
- Coverage threshold is **100%** (`backend/pytest.ini`)
- Tests use SQLite in-memory database
- New code must include tests to keep coverage at 100%

### Python Code Style
- Use type hints throughout (PEP 484 style)
- Prefer FastAPI dependency injection patterns
- Raise `HTTPException` with explicit status codes in routes
- Catch narrow exceptions when possible; avoid empty `except`
- Follow snake_case for functions/variables
- Use PascalCase for classes
- Pydantic models for API schemas live in `backend/app/models/schemas.py`
- Pydantic models often use `class Config: from_attributes = True`
- Docstrings are used for public functions and complex logic

## Frontend (React / TypeScript / Vite)
Working directory: `frontend`

### Setup
- `npm install`

### Run
- `npm run dev`
- `npm run build` (runs `tsc && vite build`)
- `npm run preview`

### Lint
- `npm run lint` (eslint, max warnings 0)

### Tests (Vitest)
- Run all tests: `npm run test`
- UI mode: `npm run test:ui`
- Coverage: `npm run test:coverage`
- Single test file: `npx vitest src/hooks/useRetry.test.ts`
- Single test name: `npx vitest src/hooks/useRetry.test.ts -t "test name"`
- Match pattern: `npx vitest -t "pattern"`
- Watch specific file: `npx vitest src/hooks/useRetry.test.ts --watch`

### TypeScript Conventions
- Strict mode enabled in `frontend/tsconfig.json`
- `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`
- Prefer named exports for components/utilities
- Use `export type` for type-only exports
- Strings generally use single quotes in TS/TSX
- Use React functional components and hooks

### Styling Conventions
- Tailwind is configured; dark mode is class-based
- Custom theme tokens live in `frontend/tailwind.config.js`
- Prefer existing component styles and utility classes
- Avoid introducing new color tokens unless necessary

## E2E (Playwright)
Working directory: `e2e`

### Run
- `npm test`
- UI mode: `npm run test:ui`
- Headed: `npm run test:headed`
- Show report: `npm run report`

### Single Test
- Specific file: `npx playwright test tests/example.spec.ts`
- Grep test name: `npx playwright test --grep "test name"`
- Specific browser: `npx playwright test --project=chromium`
- Debug: `npx playwright test --debug`

## Build / Lint / Test Summary
- Backend tests: `cd backend && pytest`
- Frontend lint: `cd frontend && npm run lint`
- Frontend tests: `cd frontend && npm run test`
- E2E tests: `cd e2e && npm test`

## Error Handling Guidelines
- Prefer explicit error types (`ValueError`, `HTTPException`, etc.)
- Provide user-safe error messages in API responses
- Log internal errors with context where possible
- Do not swallow exceptions silently

## Naming Conventions
- Python: snake_case functions/vars, PascalCase classes
- TypeScript: camelCase functions/vars, PascalCase components/types
- Files: lowercase with underscores in Python; component folders in PascalCase in frontend

## Imports
- Python: standard library first, third-party second, local last
- TypeScript: React/3rd-party first, local relative imports last
- Keep imports grouped and sorted logically

## Dependencies
- Prefer existing dependencies; do not add new ones without need
- Avoid breaking changes; keep changes minimal and scoped

## Notes on Missing Conventions
- No `.editorconfig`, `.prettierrc`, or `.eslintrc` files present
- ESLint is invoked from `frontend/package.json` with default config

## Cursor/Copilot Rules
- No `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` found
