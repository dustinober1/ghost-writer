# Testing Patterns

**Analysis Date:** 2025-01-18

## Test Framework

**Backend (Python):**
- **Runner:** pytest 7.4.3
- **Config:** `/Users/dustinober/Projects/ghost-writer/backend/pytest.ini`
- **Coverage:** pytest-cov with 100% minimum requirement (`--cov-fail-under=100`)

**Frontend (TypeScript):**
- **Runner:** Vitest 1.0.0
- **Config:** `/Users/dustinober/Projects/ghost-writer/frontend/vitest.config.ts`
- **Coverage:** v8 provider with text, json, and html reporters
- **Test Environment:** jsdom

**E2E:**
- **Runner:** Playwright
- **Config:** `/Users/dustinober/Projects/ghost-writer/e2e/playwright.config.ts`
- **Browsers:** Chromium, Firefox, WebKit
- **Reporter:** HTML with screenshots on failure

**Run Commands:**

```bash
# Backend tests
cd backend && pytest -v --tb=short --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=100 --strict-markers

# Frontend tests
cd frontend && npm test              # Run all tests (vitest)
cd frontend && npm run test:coverage # Run with coverage

# E2E tests
cd e2e && npx playwright test        # Run all E2E tests
```

## Test File Organization

**Location:**
- **Backend:** Co-located in `/backend/tests/` directory
- **Frontend:** Co-located with source files using `*.test.ts`/`*.test.tsx` suffix
- **E2E:** Separate `/e2e/tests/` directory

**Naming:**
- **Backend Python:** `test_*.py` prefix (e.g., `test_auth_routes.py`, `test_text_processing.py`)
- **Frontend:** `*.test.ts`, `*.test.tsx` suffix (e.g., `Button.test.tsx`, `useRetry.test.ts`)
- **E2E:** `*.spec.ts` suffix (e.g., `analysis.spec.ts`, `auth.spec.ts`)

**Structure:**
```
backend/
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── test_auth_routes.py      # Route tests
│   ├── test_text_processing.py  # Utility tests
│   └── test_*.py                # Other tests
frontend/src/
├── components/
│   └── ui/
│       ├── Button.tsx
│       └── Button.test.tsx      # Component tests
├── hooks/
│   ├── useRetry.ts
│   └── useRetry.test.ts         # Hook tests
e2e/
└── tests/
    ├── analysis.spec.ts         # E2E scenarios
    └── auth.spec.ts
```

## Test Structure

**Backend (pytest):**

```python
# From /Users/dustinober/Projects/ghost-writer/backend/tests/test_auth_routes.py
def test_register_success(client, db):
    """Test successful user registration."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password" not in data
```

**Frontend (Vitest):**

```typescript
// From /Users/dustinober/Projects/ghost-writer/frontend/src/components/ui/Button.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Button from './Button';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

**Patterns:**
- **Setup:** Use `beforeEach` for common setup (Vitest), `@pytest.fixture` (pytest)
- **Teardown:** Automatic cleanup in pytest (fixture scope), `cleanup` functions in Vitest
- **Assertion:** `assert` in pytest, `expect()` from Vitest
- **Test grouping:** `describe` blocks in Vitest, test class organization in pytest

## Mocking

**Backend (pytest):**

```python
# From /Users/dustinober/Projects/ghost-writer/backend/tests/test_cache.py
from unittest.mock import patch, MagicMock

@patch("app.utils.cache.get_redis_client")
def test_get_cached_no_redis(self, mock_redis):
    """Test get_cached when Redis is unavailable."""
    from app.utils.cache import get_cached

    mock_redis.return_value = None

    result = get_cached("test:key")
    assert result is None
```

**Frontend (Vitest):**

```typescript
// From /Users/dustinober/Projects/ghost-writer/frontend/src/hooks/useRetry.test.ts
import { vi } from 'vitest';

it('retries on failure', async () => {
  const mockFn = vi.fn()
    .mockRejectedValueOnce(new Error('First fail'))
    .mockRejectedValueOnce(new Error('Second fail'))
    .mockResolvedValue({ data: 'success' });

  const { result } = renderHook(() =>
    useRetry(mockFn, { maxRetries: 3, initialDelay: 100 })
  );

  await act(async () => {
    await result.current.execute();
  });

  expect(mockFn).toHaveBeenCalledTimes(3);
});
```

**What to Mock:**
- External API calls (axios, fetch)
- Database connections
- Third-party services (Redis, Ollama)
- Browser APIs (localStorage, IntersectionObserver)
- Time-related functions (setTimeout, setInterval) - use `vi.useFakeTimers()`

**What NOT to Mock:**
- Business logic functions
- Data transformations
- Pure functions (utilities, text processing)

## Fixtures and Factories

**Backend Fixtures:**

```python
# From /Users/dustinober/Projects/ghost-writer/backend/tests/conftest.py
@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for a test user."""
    response = client.post(
        "/api/auth/login-json",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

**Location:**
- Backend: `/Users/dustinober/Projects/ghost-writer/backend/tests/conftest.py`
- Frontend: `/Users/dustinober/Projects/ghost-writer/frontend/src/test/setup.ts`

## Coverage

**Requirements:**
- **Backend:** 100% coverage enforced (`--cov-fail-under=100`)
- **Frontend:** Coverage configured but no minimum enforced

**View Coverage:**

```bash
# Backend
cd backend && pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend
cd frontend && npm run test:coverage
# Coverage output in console, detailed in coverage/ directory
```

## Test Types

**Unit Tests:**
- **Backend:** Test individual functions, utilities, models in isolation
  - Example: `/Users/dustinober/Projects/ghost-writer/backend/tests/test_text_processing.py`
  - Scope: `split_into_sentences`, `get_word_count`, etc.
- **Frontend:** Test components and hooks in isolation with `@testing-library/react`
  - Example: `/Users/dustinober/Projects/ghost-writer/frontend/src/components/ui/Button.test.tsx`
  - Scope: Component rendering, event handlers, prop behavior

**Integration Tests:**
- **Backend:** Test API endpoints with TestClient and database
  - Example: `/Users/dustinober/Projects/ghost-writer/backend/tests/test_auth_routes.py`
  - Scope: Full request/response cycle with database
- **Frontend:** Test integration of components with hooks
  - Scope: Component + hook interactions, API service mocking

**E2E Tests:**
- **Framework:** Playwright
- **Scope:** Full user flows across multiple pages
- **Example patterns from `/Users/dustinober/Projects/ghost-writer/e2e/tests/analysis.spec.ts`:**

```typescript
// Helper function for test setup
async function loginAsTestUser(page: any) {
  await page.goto('/login');
  await page.getByLabel(/email/i).fill('test@example.com');
  await page.getByLabel(/password/i).fill('testpassword123');
  await page.getByRole('button', { name: /sign in|login/i }).click();
  await page.waitForURL(/\/(dashboard)?$/);
}

test.describe('Text Analysis', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test('should analyze text and show results', async ({ page }) => {
    await page.goto('/analyze');
    const textarea = page.getByRole('textbox');
    await textarea.fill(testText);
    await page.getByRole('button', { name: /analyze/i }).click();
    await expect(page.getByText(/probability/i)).toBeVisible({ timeout: 30000 });
  });
});
```

## Common Patterns

**Async Testing:**

```python
# Python - pytest-asyncio for async tests
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

```typescript
// TypeScript - use act() for state updates
import { act, waitFor } from '@testing-library/react';

it('retries on failure', async () => {
  const { result } = renderHook(() => useRetry(mockFn));

  await act(async () => {
    await result.current.execute();
  });

  await waitFor(() => {
    expect(result.current.data).toEqual({ data: 'success' });
  });
});
```

**Error Testing:**

```python
# Python - Test error responses
def test_login_wrong_password(client, test_user):
    response = client.post(
        "/api/auth/login-json",
        json={"email": test_user.email, "password": "wrongpassword"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrect" in response.json()["detail"].lower()
```

```typescript
// TypeScript - Test error states
it('returns error after max retries', async () => {
  const mockFn = vi.fn().mockRejectedValue(new Error('Always fails'));
  const { result } = renderHook(() => useRetry(mockFn));

  await act(async () => {
    try {
      await result.current.execute();
    } catch (e) {
      // Expected
    }
  });

  expect(result.current.error).toBeInstanceOf(Error);
});
```

**Database Testing (Backend):**
- Use in-memory SQLite for tests (`TEST_DATABASE_URL = "sqlite:///./test.db"`)
- Fresh database for each test via fixture scope
- Automatic cleanup after each test

**Time-Based Testing (Frontend):**
```typescript
beforeEach(() => {
  vi.useFakeTimers();
});

it('handles delays', async () => {
  // Trigger timer-based operation
  await vi.advanceTimersByTimeAsync(100);
  // Assert result
});
```

---

*Testing analysis: 2025-01-18*
