from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/ghostwriter"
)

# Create engine with connection pool settings
# pool_pre_ping=True will verify connections before using
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=300,  # Recycle connections after 5 minutes
    echo=False,  # Set to True for SQL query logging
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    tier = Column(String, default="free", nullable=False)  # 'free', 'pro', 'enterprise'

    # Relationships
    writing_samples = relationship(
        "WritingSample", back_populates="user", cascade="all, delete-orphan"
    )
    fingerprints = relationship(
        "Fingerprint", back_populates="user", cascade="all, delete-orphan"
    )
    analysis_results = relationship(
        "AnalysisResult", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    batch_jobs = relationship(
        "BatchAnalysisJob", back_populates="user", cascade="all, delete-orphan"
    )
    api_keys = relationship(
        "ApiKey", back_populates="user", cascade="all, delete-orphan"
    )


class WritingSample(Base):
    __tablename__ = "writing_samples"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text_content = Column(Text, nullable=False)
    source_type = Column(String, nullable=False)  # 'upload', 'manual', 'api'
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="writing_samples")


class Fingerprint(Base):
    __tablename__ = "fingerprints"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    feature_vector = Column(JSON, nullable=False)  # Stored as JSONB in PostgreSQL
    model_version = Column(String, default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="fingerprints")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text_content = Column(Text, nullable=False)
    heat_map_data = Column(JSON, nullable=False)  # Array of segments with scores
    overall_ai_probability = Column(
        String, nullable=False
    )  # Float as string for precision
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="analysis_results")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String, unique=True, index=True, nullable=False)  # SHA-256 hash
    key_prefix = Column(String, index=True, nullable=False)  # First 8 chars for identification
    name = Column(String, nullable=False)  # User-defined key name
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class BatchAnalysisJob(Base):
    __tablename__ = "batch_analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="PENDING", nullable=False, index=True)
    total_documents = Column(Integer, default=0, nullable=False)
    processed_documents = Column(Integer, default=0, nullable=False)
    granularity = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    similarity_matrix = Column(JSON, nullable=True)
    clusters = Column(JSON, nullable=True)

    user = relationship("User", back_populates="batch_jobs")
    documents = relationship(
        "BatchDocument", back_populates="job", cascade="all, delete-orphan"
    )


class BatchDocument(Base):
    __tablename__ = "batch_documents"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("batch_analysis_jobs.id"), nullable=False)
    filename = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    text_content = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False)
    status = Column(String, default="PENDING", nullable=False, index=True)
    ai_probability = Column(Float, nullable=True)
    confidence_distribution = Column(JSON, nullable=True)
    heat_map_data = Column(JSON, nullable=True)
    embedding = Column(JSON, nullable=True)
    cluster_id = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("BatchAnalysisJob", back_populates="documents")


class ModelPerformance(Base):
    """Track per-model performance for ensemble weight optimization."""
    __tablename__ = "model_performance"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False, index=True)  # stylometric, perplexity, contrastive, ensemble
    correct_count = Column(Integer, default=0, nullable=False)
    total_count = Column(Integer, default=0, nullable=False)
    accuracy = Column(Float, default=0.0, nullable=False)  # Computed field
    avg_confidence = Column(Float, nullable=True)  # Average confidence when prediction > 0.7
    brier_score = Column(Float, nullable=True)  # Probability calibration quality
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    metadata = Column(JSON, nullable=True)  # Additional metrics per-model


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize database: {e}")
        print("   The application will continue, but database features will not work.")
        print(
            "   Please check your DATABASE_URL in .env file and ensure PostgreSQL is running."
        )
