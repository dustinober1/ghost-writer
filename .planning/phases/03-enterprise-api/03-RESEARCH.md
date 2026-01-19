# Phase 3: Enterprise API - Research

**Researched:** 2025-01-19
**Domain:** FastAPI REST API with API key authentication, tiered rate limiting, and OpenAPI documentation
**Confidence:** HIGH

## Summary

Ghost-Writer already has a solid FastAPI foundation with JWT-based user authentication, basic rate limiting via SlowAPI, and Prometheus metrics. The codebase uses standard patterns: SQLAlchemy ORM, dependency injection via `Depends()`, and modular routers.

The existing authentication system (email/password + JWT refresh tokens) works well for web users but does not support API key authentication for programmatic access. The rate limiting implementation uses SlowAPI with Redis backing but applies flat limits per endpoint rather than tiered per-user quotas. OpenAPI documentation is already auto-generated but is publicly accessible.

**Primary recommendation:** Build on existing patterns by adding API key model, tier-based rate limiter using Redis, and protected OpenAPI routes. No new major dependencies required.

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.104.1 | Web framework | Native OpenAPI, dependency injection, async |
| SlowAPI | 0.1.9 | Rate limiting | Built for FastAPI/Starlette, Redis-backed |
| Redis | 5.0.1 | Rate limit storage | Fast atomic counters, TTL support |
| SQLAlchemy | 2.0.23 | ORM | Existing DB models, easy to extend |
| python-jose | 3.3.0 | JWT handling | Already used for session tokens |
| prometheus-client | 0.19.0 | Metrics | Already integrated for usage tracking |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| secrets | stdlib | API key generation | Cryptographically secure random tokens |
| bcrypt | via passlib | API key hashing | Secure key storage (same as passwords) |

### No Additional Dependencies Needed
All required libraries are already in `requirements.txt`. The existing stack fully supports API key auth and tiered rate limiting.

## Architecture Patterns

### Existing Project Structure
```
backend/app/
├── api/
│   └── routes/
│       ├── auth.py          # JWT auth (register, login, refresh)
│       ├── analysis.py      # Text analysis endpoints
│       ├── batch.py         # Batch upload and processing
│       ├── account.py       # User account management
│       └── admin.py         # Admin endpoints
├── middleware/
│   ├── rate_limit.py        # SlowAPI setup (Redis-backed)
│   ├── metrics.py           # Prometheus middleware
│   └── audit_logging.py     # Request logging
├── models/
│   ├── database.py          # SQLAlchemy models (User, RefreshToken, etc.)
│   └── schemas.py           # Pydantic models
├── utils/
│   └── auth.py              # JWT helpers, password hashing
└── main.py                  # FastAPI app setup
```

### Pattern 1: API Key Authentication Model
**What:** Add `ApiKey` model to database, store hashed keys with user association
**When to use:** For programmatic API access (vs. JWT for web sessions)

**Database model to add:**
```python
# Source: Based on existing RefreshToken pattern in backend/app/models/database.py
class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String, nullable=False)  # Hashed like passwords
    key_prefix = Column(String, index=True)    # First 8 chars for lookup/identification
    name = Column(String, nullable=False)      # User-defined key name
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")
```

**Authentication dependency to add:**
```python
# Source: Based on get_current_user() in backend/app/utils/auth.py
from fastapi.security import APIKeyHeader
from fastapi import HTTPException, status

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key_user(
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Security(api_key_header)
) -> User:
    """Validate API key and return user, or raise 401"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Hash the provided key and compare with stored hash
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    api_key_record = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True
    ).first()

    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    # Check expiration
    if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expired"
        )

    # Update last_used
    api_key_record.last_used = datetime.utcnow()
    db.commit()

    return api_key_record.user
```

### Pattern 2: Tiered Rate Limiting with Redis
**What:** Per-user rate limits based on subscription tier (free/pro/enterprise)
**When to use:** Different access levels for different user types

**Tier configuration:**
```python
# Source: Adapted from Medium tiered rate limiter pattern
# https://medium.com/@pranavprakash4777/how-i-designed-a-tiered-api-rate-limiter-with-redis-and-fastapi-c6b6fbf447ab
TIER_LIMITS = {
    "free": {"requests_per_minute": 20, "requests_per_day": 1000},
    "pro": {"requests_per_minute": 100, "requests_per_day": 10000},
    "enterprise": {"requests_per_minute": 500, "requests_per_day": 100000},
}

def get_user_tier(user: User) -> str:
    """Get user's subscription tier from user.tier field"""
    return user.tier if hasattr(user, 'tier') else "free"
```

**Custom rate limiter decorator:**
```python
# Source: Extending existing backend/app/middleware/rate_limit.py
from slowapi.util import get_remote_address
from functools import wraps
import redis

redis_client = redis.from_url(os.getenv("REDIS_URL"))

def check_tiered_rate_limit(user: User, endpoint: str = "default") -> bool:
    """Check if user has exceeded their tiered rate limit"""
    tier = get_user_tier(user)
    limits = TIER_LIMITS[tier]

    # Use user ID as key (not IP)
    minute_key = f"ratelimit:{user.id}:{endpoint}:min"
    day_key = f"ratelimit:{user.id}:{endpoint}:day"

    pipe = redis_client.pipeline()
    pipe.incr(minute_key)
    pipe.expire(minute_key, 60)
    pipe.incr(day_key)
    pipe.expire(day_key, 86400)
    results = pipe.execute()

    minute_count = results[0]
    day_count = results[2]

    if minute_count > limits["requests_per_minute"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limits['requests_per_minute']} requests/minute"
        )

    if day_count > limits["requests_per_day"]:
        raise HTTPException(
            status_code=429,
            detail=f"Daily quota exceeded: {limits['requests_per_day']} requests/day"
        )

    return True
```

### Pattern 3: Protected OpenAPI Documentation
**What:** Move `/docs` behind authentication, prevent public API schema exposure
**When to use:** Production deployments where API structure should not be public

**Implementation:**
```python
# Source: https://davidmuraya.com/blog/protect-fastapi-docs-authentication/
# In main.py, disable default docs:
app = FastAPI(
    title="Ghostwriter Forensic Analytics API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    # ... existing config
)

# Create protected docs router
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

docs_router = APIRouter(tags=["docs"])

@docs_router.get("/docs", include_in_schema=False)
async def get_swagger_documentation(
    user: User = Depends(get_current_user)  # Or get_api_key_user
):
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - Swagger UI"
    )

@docs_router.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(
    user: User = Depends(get_current_user)
):
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - ReDoc"
    )

@docs_router.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema(
    user: User = Depends(get_current_user)
):
    return get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes
    )

app.include_router(docs_router)
```

### Anti-Patterns to Avoid
- **Storing API keys in plaintext:** Always hash keys like passwords (SHA-256 or bcrypt)
- **Using IP-based rate limiting for API keys:** Rate limit by user_id, not IP (APIs may be called from servers)
- **Public OpenAPI in production:** Exposes API structure to attackers
- **Hardcoded tier limits:** Store in database or config for easy adjustment
- **Skipping key expiration:** API keys should have optional expiration dates

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API key validation | Custom middleware | FastAPI `APIKeyHeader` + `Security()` | Built-in OpenAPI integration, auto-docs |
| Rate limit storage | In-memory dicts | Redis with SlowAPI | Distributed, atomic operations, TTL |
| Password hashing | Custom crypto | bcrypt (already in stack) | Battle-tested, adaptive cost |
| API documentation | Manual docs | FastAPI auto-generated OpenAPI | Always in sync with code |
| Metrics collection | Custom counters | prometheus-client (already in stack) | Standard format, Grafana integration |

**Key insight:** The existing Prometheus metrics middleware already tracks HTTP requests. Extend it with per-user counters rather than building a separate tracking system.

## Common Pitfalls

### Pitfall 1: API Key Prefix Disclosure
**What goes wrong:** Logging full API keys in audit trails or error messages
**Why it happens:** Easy to log request headers without sanitization
**How to avoid:** Store only prefix (first 8 chars) in DB, never log full keys
**Warning signs:** API keys visible in logs, returns full key on creation

### Pitfall 2: Rate Limit Race Conditions
**What goes wrong:** Concurrent requests bypass rate limits (INCR + EXPIRE not atomic)
**Why it happens:** Multiple requests before first EXPIRE executes
**How to avoid:** Use Redis Lua scripts for atomic INCR + EXPIRE, or Redis pipelining
**Warning signs:** Rate limits inconsistent under load

### Pitfall 3: OpenAPI Exposes All Routes
**What goes wrong:** Admin endpoints visible in public documentation
**Why it happens:** FastAPI includes all routes by default
**How to avoid:** Use `include_in_schema=False` on sensitive routes, or filter by user tier in custom OpenAPI generator
**Warning signs:** Seeing admin/internal endpoints in `/docs`

### Pitfall 4: Tier Assignment Not Validated
**What goes wrong:** Users can self-upgrade tier by modifying request
**Why it happens:** Tier comes from client-controlled data (JWT claims can be tampered)
**How to avoid:** Always fetch tier from database, not from token claims
**Warning signs:** Rate limits not enforced correctly

## Code Examples

### Create API Key Endpoint
```python
# Source: Following existing auth.py pattern
@router.post("/api/keys", response_model=ApiKeyResponse)
async def create_api_key(
    name: str = Body(..., embed=True),
    expires_in_days: Optional[int] = Body(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new API key for the current user"""
    # Generate secure random key
    raw_key = secrets.token_urlsafe(32)

    # Hash for storage
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    # Store prefix for identification (first 8 chars)
    key_prefix = raw_key[:8]

    # Calculate expiration
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    # Save to database
    api_key = ApiKey(
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
        expires_at=expires_at
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    # Return full key only on creation
    return {
        "key": raw_key,  # Only time it's shown
        "key_prefix": key_prefix,
        "name": name,
        "expires_at": expires_at
    }
```

### Usage Metrics Endpoint
```python
# Source: Extending existing metrics.py
@router.get("/api/usage")
async def get_usage_metrics(
    current_user: User = Depends(get_api_key_user),
    db: Session = Depends(get_db)
):
    """Get current usage metrics for API key"""
    tier = get_user_tier(current_user)
    limits = TIER_LIMITS[tier]

    minute_key = f"ratelimit:{current_user.id}:min"
    day_key = f"ratelimit:{current_user.id}:day"

    minute_count = redis_client.get(minute_key) or 0
    day_count = redis_client.get(day_key) or 0

    return {
        "tier": tier,
        "limits": limits,
        "usage": {
            "requests_this_minute": int(minute_count),
            "requests_today": int(day_count)
        },
        "remaining": {
            "this_minute": max(0, limits["requests_per_minute"] - int(minute_count)),
            "today": max(0, limits["requests_per_day"] - int(day_count))
        }
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Basic Auth | API keys in header | Industry standard now | Better for programmatic access |
| IP-based rate limiting | User-based rate limiting | 2023+ | Correct for server-to-server APIs |
| Public docs | Protected OpenAPI | Security best practice | Reduces attack surface |

**Current FastAPI version:** 0.104.1 (released Oct 2023)
- Consider upgrading to 0.115+ (late 2024) for improved OpenAPI 3.1 support
- No breaking changes expected for patterns used in this codebase

## Open Questions

1. **User tier storage location**
   - What we know: Existing `User` model does not have a `tier` field
   - What's unclear: Should tier be in `User` table or separate `Subscription` table?
   - Recommendation: Add `tier` column to `users` table with default "free"

2. **API key scope/permissions**
   - What we know: Basic on/off (active/inactive) is simple
   - What's unclear: Should keys have granular permissions (e.g., "read-only", "analysis-only")?
   - Recommendation: Start with binary access, add scopes later if needed

3. **Monthly quota reset timing**
   - What we know: Daily limits reset via Redis TTL
   - What's unclear: Should monthly quotas reset on calendar month or from key creation date?
   - Recommendation: Use calendar month for simplicity, implement via Celery scheduled task

## Sources

### Primary (HIGH confidence)
- **Existing codebase analysis** - Reviewed all auth, middleware, and routing code
- **FastAPI 0.104.1 docs** - Current installed version capabilities verified

### Secondary (MEDIUM confidence)
- [How I Designed a Tiered API Rate Limiter with Redis and FastAPI](https://medium.com/@pranavprakash4777/how-i-designed-a-tiered-api-rate-limiter-with-redis-and-fastapi-c6b6fbf447ab) - Verified tiered rate limiting pattern with Redis
- [FastAPI Template with API Key Authentication](https://timberry.dev/fastapi-with-apikeys) - Verified FastAPI `APIKeyHeader` usage pattern
- [How to Protect Your FastAPI OpenAPI/Swagger Docs](https://davidmuraya.com/blog/protect-fastapi-docs-authentication/) - Verified protected docs implementation
- [SlowAPI GitHub Repository](https://github.com/laurentS/slowapi) - Confirmed Redis-backed rate limiting capabilities

### Tertiary (LOW confidence)
- Various blog posts on FastAPI authentication - Used for cross-verification only

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All dependencies already verified in requirements.txt
- Architecture: HIGH - Based on existing codebase patterns plus verified external sources
- Pitfalls: MEDIUM - Some based on general best practices, not specific to this codebase

**Research date:** 2025-01-19
**Valid until:** 2025-03-01 (FastAPI ecosystem stable, but verify versions before implementing)
