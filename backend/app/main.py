from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import auth, analysis, fingerprint, rewrite, analytics, account, admin, batch, api_keys, docs
from app.models.database import init_db
from app.utils.db_check import check_db_connection
from app.middleware.rate_limit import get_rate_limiter, _rate_limit_exceeded_handler
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.audit_logging import AuditLoggingMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os
import structlog
import logging

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

app = FastAPI(
    title="Ghostwriter Forensic Analytics API",
    description="""
## Overview

Ghostwriter is a forensic analytics platform for stylometric fingerprinting and AI text detection.
Use local LLMs (Ollama) to analyze text patterns and distinguish between human and AI-generated content.

## Key Features

- **Stylometric Fingerprinting**: Create unique writing signatures from your samples
- **AI Detection**: Identify AI-generated text with heat map visualization
- **Style Rewriting**: Transform AI text to match your personal writing style
- **Privacy-First**: Uses local Ollama LLM - your data never leaves your infrastructure

## Authentication

This API requires authentication for all endpoints including documentation.

**Web UI Authentication:** Use JWT tokens from `/api/auth/login-json`
**API Access:** Use API keys from `/api/keys` with `X-API-Key` header

1. Register: `POST /api/auth/register`
2. Login: `POST /api/auth/login-json`
3. Use the returned `access_token` in the `Authorization: Bearer <token>` header
4. Or create an API key with `POST /api/keys` and use `X-API-Key` header

## Rate Limits

Rate limits are enforced per user based on subscription tier.

- **Free tier**: 30 requests/minute for analysis
- **Pro tier**: 100 requests/minute for analysis
- **Enterprise tier**: Custom limits

## GDPR Compliance

- Export your data: `GET /api/account/export`
- Delete your data: `DELETE /api/account/data/{type}`
- Delete account: `DELETE /api/account/delete-immediately`

## Features

* **Text Analysis**: Analyze text for AI vs human writing patterns
* **Fingerprinting**: Create personal writing fingerprints
* **Style Rewriting**: Rewrite AI-generated text to match your style
* **Analytics**: Track your analysis history and performance
* **Batch Analysis**: Upload multiple documents for AI detection
* **API Keys**: Generate API keys for programmatic access

## Support

For issues or questions, please contact support.
""",
    version="1.0.0",
    docs_url=None,  # Disable public docs
    redoc_url=None,  # Disable public redoc
    openapi_url=None,  # Disable public schema
    contact={
        "name": "Ghostwriter Support",
        "email": "support@ghostwriter.local",
    },
    license_info={
        "name": "MIT",
    },
)

# Add rate limiting
limiter = get_rate_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add metrics middleware
from app.middleware.metrics import MetricsMiddleware
app.add_middleware(MetricsMiddleware)

# Add audit logging (to log all requests)
app.add_middleware(AuditLoggingMiddleware)

# Add security headers
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware - configurable via environment
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(fingerprint.router)
app.include_router(rewrite.router)
app.include_router(analytics.router)
app.include_router(account.router)
app.include_router(admin.router)
app.include_router(batch.router)
app.include_router(api_keys.router)
app.include_router(docs.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    # Initialize Sentry for error tracking
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% of transactions
            environment=os.getenv("ENVIRONMENT", "development"),
        )
    
    # Check SECRET_KEY in production
    if os.getenv("ENVIRONMENT") == "production":
        secret_key = os.getenv("SECRET_KEY", "")
        if not secret_key or secret_key == "your-secret-key-change-in-production":
            raise ValueError(
                "SECRET_KEY must be set to a strong random value in production. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
    
    # Try to initialize database, but don't fail if it's not available
    # This allows the API to start even if database isn't configured yet
    try:
        init_db()
    except Exception as e:
        logger = structlog.get_logger()
        logger.warning(
            "database_init_failed",
            error=str(e),
            message="API will start, but database-dependent endpoints may not work"
        )


@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Ghostwriter Forensic Analytics API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """Enhanced health check endpoint with component status"""
    import time
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
    
    # Check database
    db_start = time.time()
    is_connected, db_message = check_db_connection()
    db_latency_ms = (time.time() - db_start) * 1000
    health_status["database"] = {
        "connected": is_connected,
        "latency_ms": round(db_latency_ms, 2),
        "message": db_message
    }
    
    # Check Ollama
    ollama_status = {"available": False, "model": os.getenv("OLLAMA_MODEL", "llama3.1:8b")}
    try:
        import requests
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=2)
        ollama_status["available"] = response.status_code == 200
    except Exception:
        pass
    health_status["ollama"] = ollama_status
    
    # Check Redis (if configured)
    redis_status = {"connected": False}
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url, socket_connect_timeout=1)
            r.ping()
            redis_status["connected"] = True
        except Exception:
            pass
    health_status["redis"] = redis_status
    
    # Check ML model
    model_status = {"loaded": False, "version": "1.0"}
    try:
        from app.ml.contrastive_model import get_contrastive_model
        model = get_contrastive_model()
        model_status["loaded"] = model is not None
    except Exception:
        pass
    health_status["model"] = model_status
    
    # Overall status - require database but allow degraded without Ollama
    if not is_connected:
        health_status["status"] = "unhealthy"
        status_code = 503
    elif not ollama_status["available"]:
        health_status["status"] = "degraded"
        status_code = 200  # Service is usable without Ollama
    else:
        health_status["status"] = "healthy"
        status_code = 200

    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/ready")
def readiness_check():
    """Readiness probe for Kubernetes - checks if service is ready to accept traffic"""
    is_connected, _ = check_db_connection()
    if not is_connected:
        return JSONResponse(
            content={"status": "not_ready", "reason": "database_not_connected"},
            status_code=503
        )
    return {"status": "ready"}


@app.get("/live")
def liveness_check():
    """Liveness probe for Kubernetes - checks if service is alive"""
    return {"status": "alive"}


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    from app.middleware.metrics import get_metrics_response
    return get_metrics_response()