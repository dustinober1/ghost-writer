from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from app.utils.auth import get_current_user_or_api_key
from app.models.database import User

router = APIRouter(tags=["documentation"])


@router.get("/docs", include_in_schema=False)
async def get_swagger_documentation(
    current_user: User = Depends(get_current_user_or_api_key)
):
    """
    Swagger UI documentation - requires authentication.

    Use your JWT token from login or API key to access.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Use JWT token or API key."
        )

    from app.main import app
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - Swagger UI",
        swagger_favicon_url=""
    )


@router.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(
    current_user: User = Depends(get_current_user_or_api_key)
):
    """
    ReDoc documentation - requires authentication.

    Use your JWT token from login or API key to access.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Use JWT token or API key."
        )

    from app.main import app
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - ReDoc"
    )


@router.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema(
    current_user: User = Depends(get_current_user_or_api_key)
):
    """
    OpenAPI schema - requires authentication.

    Returns the full OpenAPI 3.0 specification for this API.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Use JWT token or API key."
        )

    from app.main import app

    if app.openapi_schema:
        return app.openapi_schema

    # Tier-based rate limit information
    TIER_LIMITS = {
        "free": 30,      # requests per minute
        "pro": 100,
        "enterprise": 1000
    }

    # Generate OpenAPI schema with additional info
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description=app.description
    )

    # Add rate limit information to the schema
    openapi_schema["info"]["x-rate-limits"] = {
        "free": TIER_LIMITS["free"],
        "pro": TIER_LIMITS["pro"],
        "enterprise": TIER_LIMITS["enterprise"]
    }

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token from /api/auth/login-json"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key from /api/keys"
        }
    }

    # Set default security - endpoints can use either auth method
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "security" not in method:
                # Allow either auth method
                method["security"] = [{"BearerAuth": []}, {"ApiKeyAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema
