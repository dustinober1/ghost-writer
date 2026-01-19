# Coding Conventions

**Analysis Date:** 2025-01-18

## Naming Patterns

**Files:**
- **Python (backend):** `snake_case.py` - modules use lowercase with underscores (e.g., `text_processing.py`, `auth_routes.py`)
- **TypeScript (frontend):** `PascalCase.tsx` for components, `camelCase.ts` for utilities/hooks (e.g., `Button.tsx`, `useRetry.ts`)
- **Test files:** `test_*.py` for Python, `*.test.ts`/`*.test.tsx`/`*.spec.ts` for TypeScript

**Functions:**
- **Python:** `snake_case` - all functions use lowercase with underscores (e.g., `get_password_hash`, `validate_password_strength`)
- **TypeScript:** `camelCase` - all functions use camelCase (e.g., `getErrorMessage`, `handleAnalyze`)
- **Async functions:** Use `async def` in Python, `async/await` in TypeScript - no special naming

**Variables:**
- **Python:** `snake_case` for local variables (e.g., `hashed_password`, `access_token`)
- **TypeScript:** `camelCase` for local variables (e.g., `isLoading`, `errorMsg`)

**Types/Classes:**
- **Python:** `PascalCase` for classes (e.g., `UserCreate`, `AnalysisService`, `Token`)
- **TypeScript:** `PascalCase` for interfaces/types/components (e.g., `ButtonProps`, `RetryState`, `TextInput`)
- **Enums:** `PascalCase` with `SCREAMING_CASE` values in Python; TypeScript uses string unions or enum objects

## Code Style

**Formatting:**
- **Python:** No explicit formatter configured (consider adding `black` or `autopep8`)
- **TypeScript:** Vite with `@vitejs/plugin-react` - uses standard React patterns
- **CSS:** Tailwind CSS utility classes with `cn()` helper for conditional merging (uses `clsx` + `tailwind-merge`)

**Linting:**
- **TypeScript:** ESLint with `@typescript-eslint/eslint-plugin` and `@typescript-eslint/parser`
  - Config: `--max-warnings 0` flag in package.json scripts
  - Extends recommended TypeScript and React rules
- **Python:** No explicit linter configured (consider adding `flake8` or `ruff`)

## Import Organization

**Python - Order:**
1. Standard library imports
2. Third-party imports
3. Local application imports (`from app.*`)
4. Blank line separating each group

```python
# Standard library
from datetime import datetime, timedelta
from typing import Optional

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Local
from app.models.database import get_db
from app.utils.auth import verify_password
```

**TypeScript - Order:**
1. React/library imports
2. Third-party component imports
3. Local imports (relative paths)
4. Type imports grouped together

```typescript
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../ui/Card';
import { cn } from '../../utils/cn';
```

**Path Aliases:**
- Frontend uses relative imports: `../../services/api`, `../ui/Button`
- Backend uses absolute imports from `app` package: `from app.models.database import User`

## Error Handling

**Patterns:**

**Python (FastAPI):**
- Use `HTTPException` for API errors with status codes
- Return structured error responses with `detail` field
- Validate passwords with custom validation returning `(is_valid, error_message)` tuple

```python
# From /Users/dustinober/Projects/ghost-writer/backend/app/api/routes/auth.py
if not user or not verify_password(user_data.password, user.password_hash):
    if user:
        handle_failed_login(db, user)
        log_auth_event("login", user_id=user.id, user_email=user.email, success=False)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
```

**TypeScript:**
- Use try-catch for async operations
- Extract error messages with `getErrorMessage()` utility
- Show errors via Toast context or Alert components

```typescript
// From /Users/dustinober/Projects/ghost-writer/frontend/src/services/api.ts
export const getErrorMessage = (error: any): string => {
  if (error.response) {
    const errorData = error.response.data;
    if (Array.isArray(errorData?.detail)) {
      return errorData.detail.map((err: any) => `${err.loc?.slice(1).join('.')}: ${err.msg}`).join(', ');
    } else if (errorData?.detail) {
      return errorData.detail;
    }
  }
  return error.message || 'An unexpected error occurred';
};
```

**Logging:**
- **Python:** Structured logging with `structlog` in JSON format
  - Log levels: `info`, `warning`, `error`
  - Include context: `request_id`, `user_id`, `timestamp`
  - Security events logged with `log_auth_event()` and `log_analysis_event()`
- **TypeScript:** Console logging with `console.error()` for debugging

## Comments

**When to Comment:**
- Module-level docstrings (triple quotes) at top of Python files
- Function docstrings for public APIs describing args/returns
- Inline comments for complex logic (e.g., bcrypt password length workaround)

**JSDoc/TSDoc:**
- Not consistently used in TypeScript codebase
- Props interfaces defined separately with TypeScript types
- Consider adding JSDoc for complex utility functions

```python
# From /Users/dustinober/Projects/ghost-writer/backend/app/utils/auth.py
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        prepared = _prepare_password_for_bcrypt(plain_password)
        return bcrypt.checkpw(prepared, hashed_password.encode('utf-8'))
    except Exception:
        return False
```

## Function Design

**Size:**
- Aim for single-purpose functions
- Large components split into smaller sub-components
- Service classes contain related methods (e.g., `AnalysisService.analyze_text`)

**Parameters:**
- **Python:** Use type hints for all parameters (e.g., `text: str, granularity: str = "sentence"`)
- **TypeScript:** Use interfaces for complex parameter objects, primitives for simple values

**Return Values:**
- **Python:** Explicit return types in type hints
- **TypeScript:** Implicit or explicit return types
- API responses use Pydantic schemas (Python) or typed interfaces (TypeScript)

```python
# From /Users/dustinober/Projects/ghost-writer/backend/app/services/analysis_service.py
def analyze_text(
    self,
    text: str,
    granularity: str = "sentence",
    user_fingerprint: Optional[Dict] = None,
    user_id: int = None,
    use_cache: bool = True,
) -> Dict:
```

## Module Design

**Exports:**
- **Python:** Explicit `__init__.py` files expose module contents
- **TypeScript:** Named exports for utilities, default exports for components

**Barrel Files:**
- Frontend uses barrel files like `ui/index.ts` patterns implicitly through named exports
- Backend uses `from app.models.schemas import *` pattern in some files

**Service Pattern:**
- Backend uses singleton service instances with `get_*_service()` functions
- Global instance pattern: `_service_instance = None` with getter function

```python
# From /Users/dustinober/Projects/ghost-writer/backend/app/services/analysis_service.py
_analysis_service = None

def get_analysis_service() -> AnalysisService:
    """Get or create the global analysis service instance"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service
```

## Component Patterns (TypeScript)

**Props Interface:**
- Export props interfaces separately from component
- Extend HTML attributes where appropriate (`ButtonHTMLAttributes<HTMLButtonElement>`)

**forwardRef Pattern:**
- Use `forwardRef` for components that need ref forwarding
- Set `displayName` for debugging

```typescript
// From /Users/dustinober/Projects/ghost-writer/frontend/src/components/ui/Button.tsx
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, disabled, children, ...props }, ref) => {
    // ...
  }
);

Button.displayName = 'Button';
```

## Custom Hooks Pattern

**Return Type:**
- Hooks return tuple or object with state/actions
- Use `useCallback` for event handlers to prevent re-renders
- Use `useEffect` with cleanup for subscriptions

```typescript
// From /Users/dustinober/Projects/ghost-writer/frontend/src/hooks/useRetry.ts
export function useRetry<T>(
  asyncFn: () => Promise<T>,
  options: RetryOptions = {}
) {
  const [state, setState] = useState<RetryState<T>>({
    data: null,
    error: null,
    isLoading: false,
    attempt: 0,
  });

  const execute = useCallback(async () => {
    // ...
  }, [asyncFn, maxRetries, initialDelay, maxDelay, backoffFactor, onRetry]);

  return { ...state, execute, reset };
}
```

---

*Convention analysis: 2025-01-18*
