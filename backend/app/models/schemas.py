from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


# Confidence Level Enum
class ConfidenceLevel(str, Enum):
    """Confidence level for AI probability categorization"""
    HIGH = "HIGH"      # > 0.7
    MEDIUM = "MEDIUM"  # 0.4 - 0.7
    LOW = "LOW"        # < 0.4


# User Schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=1000, description="Password (8-1000 characters)")


class UserResponse(UserBase):
    id: int
    email_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Writing Sample Schemas
class WritingSampleBase(BaseModel):
    text_content: str
    source_type: str


class WritingSampleCreate(WritingSampleBase):
    pass


class WritingSampleResponse(WritingSampleBase):
    id: int
    user_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


# Fingerprint Schemas
class FingerprintBase(BaseModel):
    feature_vector: List[float]
    model_version: str
    
    class Config:
        protected_namespaces = ()


class FingerprintResponse(FingerprintBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FingerprintStatus(BaseModel):
    has_fingerprint: bool
    fingerprint: Optional[FingerprintResponse] = None
    sample_count: int


# Analysis Schemas
class FeatureAttribution(BaseModel):
    """Individual feature attribution for explaining AI detection"""
    feature_name: str
    importance: float  # 0-1 normalized importance score
    interpretation: str  # Human-readable explanation


class TextSegment(BaseModel):
    text: str
    ai_probability: float
    start_index: int
    end_index: int
    confidence_level: ConfidenceLevel
    feature_attribution: Optional[List[FeatureAttribution]] = None  # Top 5 contributing features


class HeatMapData(BaseModel):
    segments: List[TextSegment]
    overall_ai_probability: float
    confidence_distribution: Optional[Dict[str, int]] = None  # {"HIGH": count, "MEDIUM": count, "LOW": count}


class AnalysisRequest(BaseModel):
    text: str
    granularity: str = "sentence"  # "sentence" or "paragraph"


class AnalysisResponse(BaseModel):
    heat_map_data: HeatMapData
    analysis_id: int
    created_at: datetime


# Rewrite Schemas
class RewriteRequest(BaseModel):
    text: str
    target_style: Optional[str] = None  # If None, use user's fingerprint


class RewriteResponse(BaseModel):
    original_text: str
    rewritten_text: str
    rewrite_id: int
    created_at: datetime


# Auth Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    email: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=1000)


class EmailVerificationRequest(BaseModel):
    token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=1000)


# Analytics Schemas
class AnalyticsOverview(BaseModel):
    total_analyses: int
    total_rewrites: int
    total_samples: int
    has_fingerprint: bool
    fingerprint_accuracy: Optional[float] = None
    average_ai_probability: Optional[float] = None


class ActivityEntry(BaseModel):
    id: int
    type: str  # 'analysis', 'rewrite', 'sample_upload', 'fingerprint_generated'
    description: str
    created_at: datetime
    metadata: Optional[Dict] = None


class TrendDataPoint(BaseModel):
    date: str
    count: int
    value: Optional[float] = None


class TrendData(BaseModel):
    label: str
    data: List[TrendDataPoint]


class PerformanceMetrics(BaseModel):
    average_ai_probability: float
    high_confidence_count: int  # > 0.7
    medium_confidence_count: int  # 0.4 - 0.7
    low_confidence_count: int  # < 0.4
    total_analyses: int


class AnalysisHistoryItem(BaseModel):
    id: int
    text_preview: str
    overall_ai_probability: float
    word_count: int
    created_at: datetime


class AnalysisHistoryResponse(BaseModel):
    items: List[AnalysisHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int
