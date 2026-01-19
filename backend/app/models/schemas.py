from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


# Confidence Level Enum
class ConfidenceLevel(str, Enum):
    """Confidence level for AI probability categorization"""

    HIGH = "HIGH"  # > 0.7
    MEDIUM = "MEDIUM"  # 0.4 - 0.7
    LOW = "LOW"  # < 0.4


# Pattern Type Enum
class PatternType(str, Enum):
    """Type of overused pattern detected"""

    REPEATED_PHRASE = "repeated_phrase"
    SENTENCE_START = "sentence_start"
    WORD_REPETITION = "word_repetition"


# Pattern Severity Enum
class PatternSeverity(str, Enum):
    """Severity level of overused pattern"""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Batch status enums
class BatchJobStatus(str, Enum):
    """Status of a batch analysis job"""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BatchDocumentStatus(str, Enum):
    """Status of a document within a batch job"""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# User Schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=8, max_length=1000, description="Password (8-1000 characters)"
    )


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
        from_attributes = True


class FingerprintResponse(FingerprintBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class FingerprintStatus(BaseModel):
    has_fingerprint: bool
    fingerprint: Optional[FingerprintResponse] = None
    sample_count: int


# Corpus-Based Fingerprint Schemas
class FingerprintSampleCreate(BaseModel):
    """Request schema for adding writing samples to corpus."""
    text_content: str = Field(..., min_length=10)
    source_type: str = Field(
        default="manual",
        pattern="^(email|essay|blog|academic|document|manual)$"
    )
    written_at: Optional[datetime] = None


class FingerprintSampleResponse(BaseModel):
    """Response schema for individual fingerprint samples."""
    id: int
    user_id: int
    source_type: str
    word_count: int
    created_at: datetime
    written_at: Optional[datetime] = None
    text_preview: str  # First 100 chars of text_content

    class Config:
        from_attributes = True


class CorpusStatus(BaseModel):
    """Corpus summary response for tracking sample collection progress."""
    sample_count: int
    total_words: int
    source_distribution: Dict[str, int]
    ready_for_fingerprint: bool
    samples_needed: int  # How many more samples needed (min 10)
    oldest_sample: Optional[datetime] = None
    newest_sample: Optional[datetime] = None


class EnhancedFingerprintResponse(BaseModel):
    """Response schema for enhanced/corpus-based fingerprints."""
    id: int
    user_id: int
    corpus_size: int
    method: str
    alpha: float
    source_distribution: Optional[Dict[str, int]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Fingerprint Comparison Schemas
class FeatureDeviation(BaseModel):
    """Individual feature deviation between text and fingerprint."""
    feature: str
    text_value: float
    fingerprint_value: float
    deviation: float


class ConfidenceInterval(BaseModel):
    """Confidence interval for similarity score."""
    lower: float
    upper: float


class FingerprintComparisonRequest(BaseModel):
    """Request schema for comparing text to fingerprint."""
    text: str = Field(..., min_length=10)
    use_enhanced: bool = Field(default=True, description="Use enhanced fingerprint if available")


class FingerprintComparisonResponse(BaseModel):
    """Response schema for fingerprint comparison with confidence intervals."""
    similarity: float = Field(..., ge=0.0, le=1.0)
    confidence_interval: ConfidenceInterval
    match_level: str = Field(..., pattern="^(HIGH|MEDIUM|LOW)$")
    feature_deviations: List[FeatureDeviation]
    method_used: str  # "time_weighted_ema", "average", or "basic"
    corpus_size: Optional[int] = None


class FingerprintProfile(BaseModel):
    """Profile response with fingerprint metadata."""
    has_fingerprint: bool
    corpus_size: Optional[int] = None
    method: Optional[str] = None
    alpha: Optional[float] = None
    source_distribution: Optional[Dict[str, int]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    feature_count: int = 27  # Number of stylometric features


# Drift Detection Schemas
class DriftSeverity(str, Enum):
    """Severity level for style drift detection."""
    WARNING = "warning"
    ALERT = "alert"
    NONE = "none"


class FeatureChange(BaseModel):
    """Single feature change detected during drift analysis."""
    feature: str
    current_value: float
    baseline_value: float
    normalized_deviation: float


class DriftDetectionResult(BaseModel):
    """Result from drift detection analysis."""
    drift_detected: bool
    severity: DriftSeverity
    similarity: float
    baseline_mean: float
    z_score: float
    confidence_interval: List[float]  # [lower, upper]
    changed_features: List[FeatureChange]
    timestamp: Optional[datetime] = None
    reason: Optional[str] = None  # E.g., "baseline_not_established"


class DriftAlertResponse(BaseModel):
    """Response schema for drift alerts."""
    id: int
    severity: DriftSeverity
    similarity_score: float
    baseline_similarity: float
    z_score: float
    changed_features: List[FeatureChange]
    text_preview: Optional[str] = None
    acknowledged: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DriftAlertsList(BaseModel):
    """List of drift alerts with summary."""
    alerts: List[DriftAlertResponse]
    total: int
    unacknowledged_count: int


class DriftStatus(BaseModel):
    """Current drift detector status for a user."""
    baseline_established: bool
    baseline_mean: Optional[float] = None
    baseline_std: Optional[float] = None
    current_window_size: int
    unacknowledged_alerts: int
    last_check: Optional[datetime] = None


# Analysis Schemas
class FeatureAttribution(BaseModel):
    """Individual feature attribution for explaining AI detection"""

    feature_name: str
    importance: float  # 0-1 normalized importance score
    interpretation: str  # Human-readable explanation


class OverusedPattern(BaseModel):
    """Overused pattern detected in text"""

    pattern_type: PatternType
    pattern: str  # The actual repeated text
    count: int = Field(
        ..., ge=2, description="Number of occurrences (must be at least 2)"
    )
    locations: List[int] = Field(
        ..., min_items=1, description="Start indices in text where pattern occurs"
    )
    severity: PatternSeverity
    percentage: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Percentage of total (for sentence starts/word freq)",
    )
    examples: Optional[List[str]] = Field(
        None, description="Sample occurrences of the pattern"
    )


class TextSegment(BaseModel):
    text: str
    ai_probability: float
    start_index: int
    end_index: int
    confidence_level: ConfidenceLevel
    feature_attribution: Optional[List[FeatureAttribution]] = (
        None  # Top 5 contributing features
    )
    sentence_explanation: Optional[str] = (
        None  # Natural language explanation for this segment
    )


class HeatMapData(BaseModel):
    segments: List[TextSegment]
    overall_ai_probability: float
    confidence_distribution: Optional[Dict[str, int]] = (
        None  # {"HIGH": count, "MEDIUM": count, "LOW": count}
    )
    overused_patterns: Optional[List[OverusedPattern]] = (
        None  # Detected overused patterns
    )
    document_explanation: Optional[str] = (
        None  # Natural language explanation for overall document
    )


class AnalysisRequest(BaseModel):
    text: str
    granularity: str = "sentence"  # "sentence" or "paragraph"


class AnalysisResponse(BaseModel):
    heat_map_data: HeatMapData
    analysis_id: int
    created_at: datetime


# Batch Schemas
class BatchUploadResponse(BaseModel):
    job_id: int
    status: BatchJobStatus


class BatchDocumentSummary(BaseModel):
    id: int
    filename: str
    word_count: int
    ai_probability: Optional[float] = None
    confidence_level: Optional[str] = None
    cluster_id: Optional[int] = None
    status: BatchDocumentStatus


class BatchClusterSummary(BaseModel):
    cluster_id: int
    document_count: int
    avg_ai_probability: Optional[float] = None


class BatchJobStatusResponse(BaseModel):
    job_id: int
    status: BatchJobStatus
    total_documents: int
    processed_documents: int
    granularity: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float


class BatchResultsResponse(BaseModel):
    job: BatchJobStatusResponse
    documents: List[BatchDocumentSummary]
    clusters: List[BatchClusterSummary]
    similarity_matrix: Optional[List[List[float]]] = None


class BatchDocumentDetail(BaseModel):
    id: int
    filename: str
    source_type: str
    text_content: str
    word_count: int
    status: BatchDocumentStatus
    ai_probability: Optional[float] = None
    confidence_distribution: Optional[Dict[str, int]] = None
    heat_map_data: Optional[HeatMapData] = None
    embedding: Optional[List[float]] = None
    cluster_id: Optional[int] = None
    error_message: Optional[str] = None
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


# Ensemble Schemas
class EnsembleResult(BaseModel):
    """Result from multi-model ensemble AI detection"""

    stylometric_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI probability from stylometric feature model"
    )
    perplexity_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI probability from perplexity model"
    )
    contrastive_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI probability from contrastive embedding model"
    )
    ensemble_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted ensemble AI probability"
    )
    model_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "stylometric": 0.4,
            "perplexity": 0.3,
            "contrastive": 0.3
        },
        description="Weight applied to each model in ensemble"
    )
    model_used: str = Field(
        default="ensemble",
        description="Which model generated the primary prediction"
    )


class EnsembleAnalysisRequest(BaseModel):
    """Request for ensemble-based text analysis"""

    text: str
    granularity: str = Field(default="sentence", description="sentence or paragraph")
    use_ensemble: bool = Field(
        default=True,
        description="Use multi-model ensemble (vs stylometric only)"
    )
    model_weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional custom weights for ensemble models"
    )


# Ensemble Management Schemas
class ModelStats(BaseModel):
    """Performance statistics for a single model"""

    model_name: str
    accuracy: float
    total_predictions: int
    correct_predictions: int
    avg_confidence: float
    last_updated: datetime
    ema_accuracy: float = 0.5


class CalibrationMetrics(BaseModel):
    """Calibration quality metrics"""

    brier_score: Optional[float] = None
    last_calibrated: Optional[datetime] = None
    method: str = 'sigmoid'  # 'sigmoid' or 'isotonic'
    cv_folds: int = 5
    is_fitted: bool = False


class EnsembleStatsResponse(BaseModel):
    """Response with ensemble performance statistics"""

    model_stats: List[ModelStats]
    calibration_metrics: CalibrationMetrics
    current_weights: Dict[str, float]
    ensemble_accuracy: float
    total_predictions: int
    last_updated: Optional[datetime] = None


class CalibrateRequest(BaseModel):
    """Request to recalibrate the ensemble"""

    method: str = Field(default='sigmoid', pattern='^(sigmoid|isotonic)$')
    cv: int = Field(default=5, ge=2, le=10)


class CalibrateResponse(BaseModel):
    """Response after calibration"""

    status: str
    brier_score: Optional[float] = None
    timestamp: datetime
    method: str
    cv_folds: int


class UpdateWeightsRequest(BaseModel):
    """Request to manually update ensemble weights"""

    stylometric: float = Field(..., ge=0.05, le=0.9)
    perplexity: float = Field(..., ge=0.05, le=0.9)
    contrastive: float = Field(..., ge=0.05, le=0.9)

    def validate_weights(self) -> bool:
        """Ensure weights sum to approximately 1.0"""
        total = self.stylometric + self.perplexity + self.contrastive
        return abs(total - 1.0) < 0.01


class WeightsResponse(BaseModel):
    """Response with current ensemble weights"""

    stylometric: float
    perplexity: float
    contrastive: float
    last_updated: Optional[datetime] = None


# Temporal Analysis Schemas
class DocumentVersionCreate(BaseModel):
    """Request to create a new document version"""

    document_id: str = Field(..., min_length=1, description="External document identifier")
    content: str = Field(..., min_length=1, description="Document text content")
    granularity: str = Field(default="sentence", description="Analysis granularity")


class DocumentVersionResponse(BaseModel):
    """Response with document version details"""

    version_id: int
    version_number: int
    document_id: str
    created_at: datetime
    word_count: int
    overall_ai_probability: float
    segment_ai_scores: Optional[List[Dict]] = None


class TimelineDataPoint(BaseModel):
    """Single data point in the document timeline"""

    version_id: int
    version_number: int
    timestamp: str
    word_count: int
    avg_ai_prob: float
    max_ai_prob: float
    min_ai_prob: float
    std_ai_prob: float
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    overall_ai_probability: float


class TimelineResponse(BaseModel):
    """Response with document timeline analysis"""

    timeline: List[TimelineDataPoint]
    overall_trend: str  # 'increasing', 'decreasing', 'stable', 'insufficient_data'
    ai_velocity: float
    total_versions: int
    error: Optional[str] = None


class InjectionEvent(BaseModel):
    """AI injection event detected between versions"""

    version: int
    version_id: int
    timestamp: str
    position: int
    text: str
    ai_probability: float
    type: str  # 'addition' or 'modification'
    severity: str  # 'high', 'medium', 'low'
    delta_ai: Optional[float] = None
    old_text: Optional[str] = None
    new_text: Optional[str] = None


class MixedAuthorshipIndicator(BaseModel):
    """Indicator suggesting mixed human-AI authorship"""

    type: str  # 'variance_discrepancy', 'probability_spike', 'version_shift'
    description: str
    value: float
    severity: str  # 'high', 'medium', 'low'
    version: Optional[int] = None
    from_version: Optional[int] = None
    to_version: Optional[int] = None
    segment_index: Optional[int] = None


class InjectionResponse(BaseModel):
    """Response with AI injection analysis"""

    injection_events: List[InjectionEvent]
    injection_score: float
    total_injections: int
    additions_count: int
    modifications_count: int
    severity_breakdown: Dict[str, int]
    mixed_authorship_indicators: List[MixedAuthorshipIndicator]
    overall_risk: str  # 'high', 'medium', 'low', 'none'


class VersionComparisonRequest(BaseModel):
    """Request to compare two document versions"""

    document_id: str = Field(..., min_length=1)
    version_a: int = Field(..., ge=1, description="First version number")
    version_b: int = Field(..., ge=1, description="Second version number")


class DiffSection(BaseModel):
    """A section of text that was added, removed, or modified"""

    text: str
    position: int
    ai_probability: Optional[float] = None
    old_text: Optional[str] = None
    new_text: Optional[str] = None
    old_position: Optional[int] = None
    delta_ai: Optional[float] = None


class VersionComparison(BaseModel):
    """Comparison result between two document versions"""

    added_sections: List[DiffSection]
    removed_sections: List[DiffSection]
    modified_sections: List[DiffSection]
    similarity_score: float
    version_a_number: int
    version_b_number: int


class VersionsListResponse(BaseModel):
    """Response listing all versions of a document"""

    versions: List[DocumentVersionResponse]
    total_versions: int
    document_id: str
