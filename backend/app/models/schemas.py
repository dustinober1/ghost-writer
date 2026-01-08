from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Optional
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=1000, description="Password (8-1000 characters)")


class UserResponse(UserBase):
    id: int
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
    feature_vector: Dict
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
class TextSegment(BaseModel):
    text: str
    ai_probability: float
    start_index: int
    end_index: int


class HeatMapData(BaseModel):
    segments: List[TextSegment]
    overall_ai_probability: float


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
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
