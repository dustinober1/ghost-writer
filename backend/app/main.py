from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, analysis, fingerprint, rewrite, analytics
from app.models.database import init_db
from app.utils.db_check import check_db_connection

app = FastAPI(
    title="Ghostwriter Forensic Analytics API",
    description="API for stylometric fingerprinting and AI detection",
    version="1.0.0"
)

# CORS middleware
# Allow all localhost origins for development (including 127.0.0.1 variations)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://0.0.0.0:3000",
        "http://0.0.0.0:5173",
    ],
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


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    # Try to initialize database, but don't fail if it's not available
    # This allows the API to start even if database isn't configured yet
    try:
        init_db()
    except Exception as e:
        print(f"⚠️  Database initialization skipped: {e}")
        print("   API will start, but database-dependent endpoints may not work.")


@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Ghostwriter Forensic Analytics API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    is_connected, message = check_db_connection()
    return {
        "status": "healthy",
        "database": "connected" if is_connected else "disconnected",
        "message": message
    }
