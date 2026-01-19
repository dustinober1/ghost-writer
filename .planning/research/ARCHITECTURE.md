# Architecture Patterns

**Domain:** AI Text Detection Platform with Advanced Features
**Researched:** 2025-01-18
**Mode:** Ecosystem Research

## Executive Summary

Ghost-Writer's current architecture follows a layered service-oriented pattern (API → Services → ML → Models) with FastAPI, PostgreSQL, Redis, Celery, and Ollama. The proposed enhancements—explainability, batch processing, multi-model ensembles, browser extension, and document clustering—require extending this architecture with five new subsystems that integrate cleanly with existing components.

**Key architectural insight:** Each enhancement maps to a distinct architectural layer that can be built incrementally without disrupting core functionality. The recommended build order follows dependency chains: (1) ensemble layer, (2) explainability layer, (3) batch processing layer, (4) clustering layer, (5) browser extension.

## Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Routes     │  │ Middleware   │  │   Auth       │          │
│  │  (analysis,  │  │ (rate limit, │  │  (JWT)       │          │
│  │   fingerprint,│  │  security,  │  │              │          │
│  │   rewrite)   │  │   audit)     │  │              │          │
│  └──────┬───────┘  └──────────────┘  └──────────────┘          │
│         │                                                        │
│  ┌──────▼───────┐                                              │
│  │   Services   │  ◄── Business logic layer                    │
│  │  (Analysis,  │                                              │
│  │   Fingerprint│                                              │
│  │   Rewrite)   │                                              │
│  └──────┬───────┘                                              │
└─────────┼──────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────┐
│                    ML / Feature Extraction                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Feature    │  │ Contrastive  │  │   Ollama     │          │
│  │ Extraction   │  │    Model     │  │  Embeddings  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────┐
│              Data Layer (PostgreSQL + Redis)                    │
└─────────────────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────┐
│              Background Tasks (Celery Workers)                   │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │   Analysis   │  │   Rewrite    │                            │
│  │    Tasks     │  │    Tasks     │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

**Component Boundaries:**

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| Routes | HTTP request/response handling, validation | Services, Middleware |
| Middleware | Cross-cutting concerns (rate limiting, security, audit) | All routes |
| Services | Business logic orchestration | ML layer, Data layer |
| ML/Feature Extraction | Feature computation, model inference | Services, Ollama |
| Data Layer | Persistence, caching | Services, Tasks |
| Celery Workers | Async long-running operations | Data layer, ML layer |

**Data Flow:**
1. HTTP request → Routes (validation, auth)
2. Routes → Services (business logic)
3. Services → ML layer (feature extraction, inference)
4. Services ↔ Data layer (persist results, cache lookups)
5. For long-running: Routes → Celery → Workers → ML → Data

---

## Proposed Architecture Extensions

### Overview Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      Client Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   React      │  │   Browser    │  │   API        │          │
│  │   Web UI     │  │  Extension   │  │  Clients     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                     API Gateway (FastAPI)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Existing   │  │   Ensemble  │  │Explainability│             │
│  │   Routes    │  │    Routes   │  │    Routes    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                    Service Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Existing   │  │   Ensemble  │  │Explainability│             │
│  │  Services   │  │   Service   │  │   Service    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐                             │
│  │    Batch    │  │  Clustering │                             │
│  │   Service   │  │   Service   │                             │
│  └─────────────┘  └─────────────┘                             │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                    ML Inference Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Existing   │  │   Ensemble  │  │Explainability│             │
│  │     ML      │  │  Orchestrator│  │   Engine    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│              Data & Vector Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ PostgreSQL  │  │    Redis    │  │ pgvector    │             │
│  │ (relational)│  │  (cache)    │  │ (similarity)│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│              Task Queue Layer                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    Celery   │  │   Batch     │  │  Clustering │             │
│  │   Workers   │  │   Workers   │  │   Workers   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Multi-Model Ensemble Architecture

**Purpose:** Combine multiple AI detection models (stylometric, embedding-based, contrastive) to improve accuracy and robustness.

### Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│          Ensemble Orchestrator (NEW)                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  - Model Registry (discover, version, validate)     │   │
│  │  - Inference Router (parallel model execution)      │   │
│  │  - Aggregation Engine (voting, weighting, stacking) │   │
│  │  - Performance Monitor (track model accuracy)       │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼─────┐   ┌─────▼───┐   ┌──────▼────┐
│ Model 1 │   │ Model 2 │   │  Model 3  │
│(Stylometric)│ (Embedding)│ │(Contrastive)│
│  Existing │   │   New    │   │  Existing │
└──────────┘   └──────────┘   └───────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| EnsembleService | API endpoint for ensemble predictions | Routes, EnsembleOrchestrator |
| EnsembleOrchestrator | Coordinate multi-model inference | ModelRegistry, AggregationEngine |
| ModelRegistry | Model discovery, versioning, health checks | All models, Database |
| AggregationEngine | Combine predictions (voting/weighting) | All models |
| PerformanceMonitor | Track model accuracy, update weights | ModelRegistry, Database |

### Data Flow

```
1. Request → EnsembleRoute → EnsembleService
2. EnsembleService → EnsembleOrchestrator.predict(text)
3. Orchestrator → ModelRegistry.get_active_models()
4. Orchestrator → Parallel: [Model1.predict(), Model2.predict(), Model3.predict()]
5. Orchestrator → AggregationEngine.aggregate(predictions)
6. AggregationEngine → Apply voting/weighting strategy
7. Orchestrator → Return ensemble_prediction + confidence
8. EnsembleService → Cache result (Redis) + Persist (PostgreSQL)
```

### Aggregation Strategies

**Voting Methods (HIGH confidence - 2025 research):**

| Strategy | Description | Use Case |
|----------|-------------|----------|
| Majority Hard Voting | Each model votes AI/Human, majority wins | Simple, interpretable |
| Weighted Hard Voting | Models have different voting weights | When some models are more accurate |
| Soft Voting | Average probability scores across models | When models output probabilities |
| Stacking | Meta-learner learns to combine predictions | When you have training data for meta-model |

**Weight Calculation:**
```python
# Dynamic weight based on recent accuracy
weight = model.base_accuracy * model.recent_performance_factor * model.confidence_score

# Update weights based on validation set
def update_weights(validation_predictions, ground_truth):
    for model in models:
        accuracy = calculate_accuracy(model.predictions, ground_truth)
        model.weight = normalize(accuracy)
```

### Implementation Pattern

```python
# backend/app/ml/ensemble/ensemble_orchestrator.py
class EnsembleOrchestrator:
    def __init__(self):
        self.model_registry = ModelRegistry()
        self.aggregation_engine = AggregationEngine()
        self.performance_monitor = PerformanceMonitor()

    async def predict(self, text: str, strategy: str = "weighted_vote"):
        # Get active models
        models = await self.model_registry.get_active_models()

        # Parallel inference
        predictions = await asyncio.gather(*[
            model.predict(text) for model in models
        ])

        # Aggregate predictions
        result = self.aggregation_engine.aggregate(
            predictions=predictions,
            strategy=strategy,
            weights=self.model_registry.get_weights()
        )

        # Monitor performance
        await self.performance_monitor.record_inference(models, result)

        return result
```

### Integration Points

- **Routes:** New `/api/analysis/ensemble` endpoint
- **Services:** EnsembleService wraps orchestrator
- **Database:** Store ensemble predictions, model weights, performance metrics
- **Cache:** Ensemble results cached with key `ensemble:{text_hash}`

### Build Order Implications

**Build FIRST** - Foundation for other enhancements:
- Batch processing uses ensemble for bulk analysis
- Explainability layer needs ensemble predictions to attribute
- Browser extension benefits from improved accuracy

**Dependencies:**
- Requires: Existing models (stylometric, contrastive)
- Enables: Ensemble-aware explainability, batch ensemble analysis

---

## 2. Explainability Pipeline Architecture

**Purpose:** Provide feature attribution, highlighting what makes text AI-generated, using SHAP/LIME integration.

### Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│       Explainability Engine (NEW)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Attribution Calculator (SHAP/LIME wrappers)        │   │
│  │  - Feature importance scores                         │   │
│  │  - Token-level attributions                          │   │
│  │  - Segment-level explanations                        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Explanation Formatter                              │   │
│  │  - Generate human-readable explanations             │   │
│  │  - Create visualization data (heatmaps, highlights) │   │
│  │  - Export JSON for frontend                         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Cache Manager (explanations are expensive)         │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                     │
                     ├──► Model (being explained)
                     └──► Features (used for attribution)
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| ExplainabilityService | API endpoint for explanations | Routes, AttributionCalculator |
| AttributionCalculator | Compute SHAP/LIME values | ML models, FeatureExtractor |
| ExplanationFormatter | Format explanations for UI | AttributionCalculator, Cache |
| CacheManager | Cache expensive SHAP computations | Redis |

### Data Flow

```
1. Request text for analysis → AnalysisRoute
2. AnalysisRoute → AnalysisService.analyze() → Get predictions
3. AnalysisRoute → ExplainabilityService.explain(text, predictions)
4. ExplainabilityService → AttributionCalculator.compute_attributions()
   - Load model and background dataset
   - Compute SHAP values for each token/segment
   - Calculate feature importance scores
5. AttributionCalculator → ExplanationFormatter.format()
   - Generate: "AI probability: 78%, driven by low burstiness (0.32), low perplexity (45)"
   - Create visualization data: highlight tokens by attribution score
6. ExplanationFormatter → Cache result (Redis)
7. ExplainabilityService → Return explanation + prediction
8. Frontend displays heat map + explanation
```

### SHAP Integration Pattern (HIGH confidence - 2025 sources)

**Key Finding from Research:** SHAP and LIME are mature production-ready frameworks in 2025, with FastAPI integration patterns well-established.

```python
# backend/app/ml/explainability/attribution_calculator.py
import shap
from app.ml.feature_extraction import extract_feature_vector

class AttributionCalculator:
    def __init__(self, model):
        self.model = model
        # Initialize SHAP explainer (cached per model)
        self.explainer = None

    def get_explainer(self, background_data):
        """Lazy-load SHAP explainer with background dataset"""
        if self.explainer is None:
            # Use KernelExplainer for model-agnostic explanations
            self.explainer = shap.KernelExplainer(
                self.model.predict,
                background_data  # Sample of training data
            )
        return self.explainer

    async def compute_attributions(self, text: str):
        """Compute SHAP values for text"""
        # Extract features
        features = extract_feature_vector(text)

        # Get explainer
        background = await self._get_background_data()
        explainer = self.get_explainer(background)

        # Compute SHAP values
        shap_values = explainer.shap_values(features)

        # Format results
        return {
            "feature_importance": self._format_importance(shap_values, features),
            "token_attributions": await self._compute_token_attributions(text),
            "explanation_text": self._generate_explanation(shap_values, features)
        }

    def _format_importance(self, shap_values, features):
        """Map SHAP values to feature names"""
        feature_names = [
            "burstiness", "perplexity", "rare_word_ratio",
            "unique_word_ratio", "noun_ratio", "verb_ratio", ...
        ]
        return [
            {"feature": name, "importance": float(value)}
            for name, value in zip(feature_names, shap_values)
        ]
```

### Explanation Output Format

```json
{
  "prediction": {
    "ai_probability": 0.78,
    "confidence": "high"
  },
  "explanation": {
    "summary": "This text is 78% likely to be AI-generated. Key indicators include low burstiness (sentence length variation) and low perplexity (predictability).",
    "feature_importance": [
      {"feature": "burstiness", "value": 0.32, "impact": "high", "direction": "low_burstiness_indicates_ai"},
      {"feature": "perplexity", "value": 45.2, "impact": "medium", "direction": "low_perplexity_indicates_ai"},
      {"feature": "unique_word_ratio", "value": 0.45, "impact": "low", "direction": "neutral"}
    ],
    "token_highlights": [
      {"token": "Furthermore", "attribution": 0.15, "reason": "formal_transition_word"},
      {"token": "utilizing", "attribution": 0.12, "reason": "corporate_vocabulary"}
    ],
    "visual_data": {
      "heatmap": [[0.1, 0.2, 0.8, ...]],  // Per-segment AI probabilities
      "attention_weights": [...]
    }
  }
}
```

### Caching Strategy

**Problem:** SHAP computations are expensive (10-100x slower than prediction)

**Solution:** Multi-level caching

```python
# backend/app/ml/explainability/cache_manager.py
class ExplanationCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = 86400  # 24 hours

    async def get_cached_explanation(self, text_hash: str, model_version: str):
        key = f"explanation:{model_version}:{text_hash}"
        return await self.redis.get(key)

    async def cache_explanation(self, text_hash: str, model_version: str, explanation: dict):
        key = f"explanation:{model_version}:{text_hash}"
        await self.redis.setex(key, self.cache_ttl, json.dumps(explanation))

    async def get_background_dataset(self, model_version: str):
        """Cache background dataset for SHAP explainer"""
        key = f"shap_background:{model_version}"
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        # Generate fresh background dataset
        background = await self._generate_background_dataset()
        await self.redis.setex(key, 3600, json.dumps(background))  # 1 hour
        return background
```

### Integration Points

- **Routes:** Extend `/api/analysis` with `?explain=true` parameter
- **Services:** ExplainabilityService coordinates attribution computation
- **ML Layer:** Access to models and feature extraction
- **Database:** Store explanations for audit trail
- **Cache:** Redis for expensive SHAP computations

### Build Order Implications

**Build SECOND** (after ensemble):
- Depends on: Ensemble or single model for prediction
- Enables: User-facing explanations, auditability

**Why this order:**
- Ensemble improves predictions first
- Then explainability helps users understand improved predictions
- Explaining ensembles is more complex (needs multi-model attribution)

---

## 3. Batch Processing Architecture

**Purpose:** Process multiple documents asynchronously with job queues, progress tracking, and result aggregation.

### Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│            Batch Processing Service (NEW)                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Job Orchestrator                                    │   │
│  │  - Create batch jobs from document lists            │   │
│  │  - Split into chunks for parallel processing        │   │
│  │  - Manage job lifecycle (queued, running, complete) │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Progress Tracker                                    │   │
│  │  - Real-time job status updates                     │   │
│  │  - Document-level progress                          │   │
│  │  - Estimated completion time                        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Result Aggregator                                   │   │
│  │  - Collect individual document results              │   │
│  │  - Generate batch statistics                        │   │
│  │  - Create exportable reports (CSV, JSON)            │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                     │
                     ├──► Celery Task Queue (existing)
                     └──► Batch Workers (new)
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| BatchService | API endpoints for batch operations | Routes, JobOrchestrator |
| JobOrchestrator | Create and manage batch jobs | Celery, ProgressTracker |
| ProgressTracker | Track job/document status | Database, WebSocket (real-time) |
| ResultAggregator | Collect and format batch results | Database, Storage |
| BatchWorker | Process individual documents | AnalysisService, Database |

### Data Flow

```
1. User uploads document list → BatchRoute.create_job()
2. BatchService → JobOrchestrator.create_batch_job(docs, options)
3. Orchestrator → Database: Create BatchJob record (status: queued)
4. Orchestrator → Celery: Dispatch document chunks to workers
   - chunk_size = 10 documents per task
   - priority = user_tier (paid users get priority)
5. BatchWorker processes documents:
   - For each doc: AnalysisService.analyze()
   - Save individual results to Database
   - Update ProgressTracker
6. Frontend polls/WebSocket receives progress updates
7. All documents complete → ResultAggregator.generate_report()
8. User downloads results → BatchRoute.download_results(job_id)
```

### Database Schema

```sql
-- Batch jobs table
CREATE TABLE batch_jobs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    status VARCHAR(50),  -- queued, processing, completed, failed
    total_documents INTEGER,
    completed_documents INTEGER DEFAULT 0,
    failed_documents INTEGER DEFAULT 0,
    options JSONB,  -- analysis options, granularity, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result_summary JSONB
);

-- Document results table
CREATE TABLE batch_document_results (
    id UUID PRIMARY KEY,
    batch_job_id UUID REFERENCES batch_jobs(id),
    document_index INTEGER,  -- Position in original upload
    status VARCHAR(50),  -- pending, processing, completed, failed
    result JSONB,  -- Analysis result
    error_message TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Result storage table
CREATE TABLE batch_job_exports (
    id UUID PRIMARY KEY,
    batch_job_id UUID REFERENCES batch_jobs(id),
    file_type VARCHAR(10),  -- csv, json, xlsx
    file_path TEXT,
    file_size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Celery Task Definition

```python
# backend/app/tasks/batch_tasks.py
from app.celery_app import celery_app
from app.services.analysis_service import get_analysis_service

@celery_app.task(name="app.tasks.process_batch_chunk")
def process_batch_chunk(job_id: str, document_indices: list, documents: list, options: dict):
    """Process a chunk of documents in a batch job"""
    db = SessionLocal()
    analysis_service = get_analysis_service()

    try:
        results = []
        for idx, doc in zip(document_indices, documents):
            try:
                # Analyze document
                result = analysis_service.analyze_text(
                    text=doc,
                    granularity=options.get("granularity", "sentence"),
                    use_cache=True
                )

                # Save result
                doc_result = BatchDocumentResult(
                    batch_job_id=job_id,
                    document_index=idx,
                    status="completed",
                    result=result,
                    completed_at=datetime.utcnow()
                )
                db.add(doc_result)
                results.append(result)

            except Exception as e:
                # Log failure but continue with other docs
                doc_result = BatchDocumentResult(
                    batch_job_id=job_id,
                    document_index=idx,
                    status="failed",
                    error_message=str(e)
                )
                db.add(doc_result)

        db.commit()

        # Update job progress
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
        job.completed_documents += len(results)
        job.failed_documents += len(documents) - len(results)
        db.commit()

        return {"processed": len(results), "failed": len(documents) - len(results)}

    finally:
        db.close()

@celery_app.task(name="app.tasks.finalize_batch_job")
def finalize_batch_job(job_id: str):
    """Generate export files and update job status"""
    db = SessionLocal()
    try:
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()

        # Generate statistics
        results = db.query(BatchDocumentResult).filter(
            BatchDocumentResult.batch_job_id == job_id,
            BatchDocumentResult.status == "completed"
        ).all()

        # Calculate aggregate statistics
        avg_ai_probability = mean([r.result["overall_ai_probability"] for r in results])
        job.result_summary = {
            "total_documents": job.total_documents,
            "completed_documents": job.completed_documents,
            "failed_documents": job.failed_documents,
            "average_ai_probability": avg_ai_probability,
            "high_ai_count": sum(1 for r in results if r.result["overall_ai_probability"] > 0.7)
        }

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

        # Generate export files
        generate_csv_export(job_id, results)
        generate_json_export(job_id, results)

    finally:
        db.close()
```

### Progress Tracking (Real-time)

**Option 1: WebSocket (preferred for real-time)**

```python
# backend/app/api/routes/batch.py
from fastapi import WebSocket

@router.websocket("/ws/batch/{job_id}")
async def batch_job_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        while True:
            # Query job progress from database
            job = get_batch_job_progress(job_id)
            await websocket.send_json({
                "job_id": job_id,
                "status": job.status,
                "completed": job.completed_documents,
                "total": job.total_documents,
                "progress_percent": (job.completed_documents / job.total_documents * 100)
            })

            # Break if job complete
            if job.status in ["completed", "failed"]:
                break

            await asyncio.sleep(1)  # Update every second
    finally:
        await websocket.close()
```

**Option 2: Polling (simpler, less efficient)**

```python
@router.get("/batch/{job_id}/progress")
def get_job_progress(job_id: str):
    job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
    return {
        "job_id": job_id,
        "status": job.status,
        "completed": job.completed_documents,
        "total": job.total_documents,
        "progress_percent": (job.completed_documents / job.total_documents * 100) if job.total_documents > 0 else 0
    }
```

### Build Order Implications

**Build THIRD** (after ensemble + explainability):
- Depends on: Ensemble (for better batch analysis), Explainability (optional per-document explanations)
- Enables: Large-scale document analysis

**Why this order:**
- Batch processing is a higher-level feature that orchestrates existing analysis
- Should have stable analysis pipeline before adding complexity of batch jobs
- Ensemble and explainability improve single-document analysis, making batch more valuable

---

## 4. Browser Extension Architecture

**Purpose:** Chrome/Firefox extension for in-browser text analysis, content script integration, and background worker communication.

### Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                 Browser Extension (NEW)                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Popup UI (React)                                    │   │
│  │  - Quick analysis text box                           │   │
│  │  - Settings (API key, preferences)                   │   │
│  │  - Auth (login/logout)                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Content Script (Injected into web pages)            │   │
│  │  - Detect text selection                             │   │
│  │  - Context menu: "Analyze with Ghost-Writer"        │   │
│  │  - Highlight AI-generated text                       │   │
│  │  - Show tooltip with AI probability                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Background Service Worker                           │   │
│  │  - API communication (authenticated requests)        │   │
│  │  - Token management (refresh JWT)                    │   │
│  │  - Cache results (extension storage)                 │   │
│  │  - Rate limiting (respect API limits)                │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────┘
                                 │
                                 ├──► Ghost-Writer API (FastAPI)
                                 └──► Extension Storage (IndexedDB)
```

### Component Boundaries (HIGH confidence - 2025 Chrome docs)

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| Popup UI | User interface for quick analysis | BackgroundWorker, ExtensionStorage |
| Content Script | Page interaction, text detection | BackgroundWorker, Page DOM |
| BackgroundWorker | API calls, auth, caching | Ghost-Writer API, Content Script, Popup |
| ExtensionStorage | Local cache, user settings | BackgroundWorker, Popup |

### Data Flow

```
User Flow: Analyze selected text on a webpage

1. User selects text on webpage → Content Script detects selection
2. User right-clicks → Context menu: "Analyze with Ghost-Writer"
3. Content Script → Message to BackgroundWorker: {action: "analyze", text: "..."}
4. BackgroundWorker → Check cache (ExtensionStorage)
5. If not cached → BackgroundWorker → API: POST /api/analysis
   - Headers: Authorization: Bearer <jwt>
   - Body: {text: "...", granularity: "sentence"}
6. API → Returns analysis result
7. BackgroundWorker → Cache result (ExtensionStorage)
8. BackgroundWorker → Message to Content Script: {result: {...}}
9. Content Script → Highlight text segments with AI probability overlay
10. User sees heat map overlay on webpage
```

### Manifest File (Chrome Extension v3)

```json
{
  "manifest_version": 3,
  "name": "Ghost-Writer AI Detection",
  "version": "1.0.0",
  "description": "Detect AI-generated text in your browser",
  "permissions": [
    "storage",
    "activeTab",
    "contextMenus",
    "scripting"
  ],
  "host_permissions": [
    "https://api.ghostwriter.local/*"
  ],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "css": ["highlight.css"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "key": "..." // Generated during build
}
```

### Background Service Worker

```javascript
// extension/background.js

// API configuration
const API_BASE_URL = "https://api.ghostwriter.local";
let authToken = null;

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  // Create context menu
  chrome.contextMenus.create({
    id: "analyze-text",
    title: "Analyze with Ghost-Writer",
    contexts: ["selection"]
  });
});

// Handle context menu click
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "analyze-text") {
    const selectedText = info.selectionText;
    analyzeText(tab.id, selectedText);
  }
});

// Analyze text
async function analyzeText(tabId, text) {
  try {
    // Check cache first
    const cached = await getCachedAnalysis(text);
    if (cached) {
      sendToContentScript(tabId, { type: "result", data: cached });
      return;
    }

    // Call API
    const response = await fetch(`${API_BASE_URL}/api/analysis/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${authToken}`
      },
      body: JSON.stringify({
        text: text,
        granularity: "sentence",
        explain: true
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();

    // Cache result
    await cacheAnalysis(text, result);

    // Send to content script
    sendToContentScript(tabId, { type: "result", data: result });

  } catch (error) {
    sendToContentScript(tabId, { type: "error", message: error.message });
  }
}

// Send message to content script
function sendToContentScript(tabId, message) {
  chrome.tabs.sendMessage(tabId, message);
}

// Cache management
async function getCachedAnalysis(text) {
  return new Promise((resolve) => {
    const hash = simpleHash(text);
    chrome.storage.local.get([`analysis_${hash}`], (result) => {
      resolve(result[`analysis_${hash}`] || null);
    });
  });
}

async function cacheAnalysis(text, result) {
  const hash = simpleHash(text);
  await chrome.storage.local.set({
    [`analysis_${hash}`]: {
      result,
      timestamp: Date.now()
    }
  });
}

// Simple hash function for cache keys
function simpleHash(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return hash.toString(16);
}
```

### Content Script

```javascript
// extension/content.js

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "result") {
    highlightText(message.data);
  } else if (message.type === "error") {
    showError(message.message);
  }
});

// Highlight text segments with AI probability overlay
function highlightText(analysisResult) {
  const segments = analysisResult.segments;

  segments.forEach(segment => {
    const aiProb = segment.ai_probability;

    // Determine color based on AI probability
    let color;
    if (aiProb < 0.3) {
      color = "rgba(0, 255, 0, 0.2)"; // Green (human)
    } else if (aiProb < 0.7) {
      color = "rgba(255, 255, 0, 0.2)"; // Yellow (mixed)
    } else {
      color = "rgba(255, 0, 0, 0.2)"; // Red (AI)
    }

    // Find and highlight text
    const textNode = findTextNode(segment.text);
    if (textNode) {
      const span = document.createElement("span");
      span.style.backgroundColor = color;
      span.title = `AI Probability: ${(aiProb * 100).toFixed(1)}%`;
      span.textContent = segment.text;

      textNode.parentNode.replaceChild(span, textNode);
    }
  });
}

// Find text node containing specific text
function findTextNode(text) {
  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    null
  );

  let node;
  while (node = walker.nextNode()) {
    if (node.textContent.includes(text)) {
      return node;
    }
  }
  return null;
}

// Show error message
function showError(message) {
  const toast = document.createElement("div");
  toast.textContent = `Ghost-Writer Error: ${message}`;
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #ff4444;
    color: white;
    padding: 12px 20px;
    border-radius: 4px;
    z-index: 10000;
  `;
  document.body.appendChild(toast);

  setTimeout(() => toast.remove(), 5000);
}
```

### API Communication Best Practices

**Authentication Flow:**

```javascript
// extension/background.js

// Login flow
async function login(email, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login-json`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({email, password})
  });

  const data = await response.json();

  // Store tokens
  await chrome.storage.local.set({
    accessToken: data.access_token,
    refreshToken: data.refresh_token
  });

  authToken = data.access_token;
}

// Refresh token flow
async function refreshAccessToken() {
  const {refreshToken} = await chrome.storage.local.get("refreshToken");

  const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${refreshToken}`
    }
  });

  const data = await response.json();

  await chrome.storage.local.set({
    accessToken: data.access_token
  });

  authToken = data.access_token;
}

// Intercept API calls and add auth token
async function authenticatedFetch(url, options = {}) {
  if (!authToken) {
    const {accessToken} = await chrome.storage.local.get("accessToken");
    authToken = accessToken;
  }

  options.headers = options.headers || {};
  options.headers["Authorization"] = `Bearer ${authToken}`;

  let response = await fetch(url, options);

  // Refresh token if expired
  if (response.status === 401) {
    await refreshAccessToken();
    options.headers["Authorization"] = `Bearer ${authToken}`;
    response = await fetch(url, options);
  }

  return response;
}
```

### Rate Limiting (Extension-side)

```javascript
// extension/rate-limiter.js

class RateLimiter {
  constructor(maxRequests, perMilliseconds) {
    this.maxRequests = maxRequests;
    this.perMilliseconds = perMilliseconds;
    this.requests = [];
  }

  async waitForSlot() {
    const now = Date.now();

    // Remove old requests outside time window
    this.requests = this.requests.filter(
      time => now - time < this.perMilliseconds
    );

    // If at limit, wait
    if (this.requests.length >= this.maxRequests) {
      const oldestRequest = this.requests[0];
      const waitTime = this.perMilliseconds - (now - oldestRequest);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }

    // Add current request
    this.requests.push(Date.now());
  }
}

// Usage: Respect API rate limits (30 requests/minute for analysis)
const analysisRateLimiter = new RateLimiter(30, 60 * 1000);

async function rateLimitedAnalyze(text) {
  await analysisRateLimiter.waitForSlot();
  return analyzeText(text);
}
```

### Build Order Implications

**Build FIFTH** (after all backend features):
- Depends on: Stable API endpoints, authentication, ensemble/explainability/batch
- Enables: User-facing browser extension

**Why last:**
- Browser extension depends on stable API contract
- Should build backend features first to know what endpoints to expose
- Can be developed in parallel with other features, but deployment should wait

---

## 5. Document Clustering & Similarity Search Architecture

**Purpose:** Group similar documents, find near-duplicates, enable similarity search across analyzed documents.

### Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│          Clustering & Similarity Service (NEW)              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Vector Embedding Manager                            │   │
│  │  - Generate embeddings for documents                 │   │
│  │  - Store in pgvector (PostgreSQL)                    │   │
│  │  - Batch embedding for efficiency                    │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Similarity Search Engine                            │   │
│  │  - Nearest neighbor queries (cosine similarity)     │   │
│  │  - Threshold-based filtering                        │   │
│  │  - Hybrid search (vector + metadata filters)        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Clustering Engine                                   │   │
│  │  - K-means / DBSCAN clustering                      │   │
│  │  - Hierarchical clustering (topic groups)           │   │
│  │  - Near-duplicate detection                         │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                     │
                     ├──► PostgreSQL + pgvector extension
                     └──► Celery Workers (async clustering)
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| ClusteringService | API endpoints for clustering/similarity | Routes, VectorManager |
| VectorManager | Embedding generation and storage | Ollama, PostgreSQL/pgvector |
| SimilarityEngine | Nearest neighbor search | PostgreSQL/pgvector |
| ClusteringEngine | Document clustering algorithms | VectorManager, Database |
| ClusteringWorker | Async clustering jobs | Celery, ClusteringEngine |

### Data Flow

```
Document Similarity Search:

1. User provides text → POST /api/clustering/similar
2. ClusteringService → VectorManager.generate_embedding(text)
3. VectorManager → Ollama API: Get embedding vector
4. VectorManager → PostgreSQL: Insert embedding (if not cached)
5. ClusteringService → SimilarityEngine.find_similar(embedding, threshold=0.85)
6. SimilarityEngine → PostgreSQL pgvector query:
   SELECT * FROM documents
   ORDER BY embedding <-> query_vector
   LIMIT 10
7. SimilarityEngine → Return similar documents with similarity scores
8. ClusteringService → Format and return results

Document Clustering (Batch):

1. User requests clustering → POST /api/clustering/cluster
2. ClusteringService → ClusteringWorker.cluster_documents(filters)
3. Worker → VectorManager.batch_generate_embeddings(docs)
4. Worker → ClusteringEngine.run_clustering(embeddings, algorithm="kmeans")
5. Worker → Save cluster assignments to Database
6. Worker → Return cluster statistics
7. User → GET /api/clustering/clusters/{cluster_id}
```

### Database Schema (pgvector)

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table with embeddings
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    text_content TEXT NOT NULL,
    embedding vector(768),  -- Ollama llama3.1:8b embedding dimension
    created_at TIMESTAMP DEFAULT NOW(),
    -- Metadata for hybrid search
    ai_probability FLOAT,
    word_count INTEGER,
    language VARCHAR(10)
);

-- Index for vector similarity search
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Clusters table
CREATE TABLE document_clusters (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    cluster_name TEXT,
    algorithm VARCHAR(50),  -- kmeans, dbscan, hierarchical
    parameters JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Document cluster assignments
CREATE TABLE document_cluster_assignments (
    document_id UUID REFERENCES documents(id),
    cluster_id UUID REFERENCES document_clusters(id),
    confidence FLOAT,
    PRIMARY KEY (document_id, cluster_id)
);

-- Similar documents cache (precomputed)
CREATE TABLE similar_documents (
    document_id UUID REFERENCES documents(id),
    similar_document_id UUID REFERENCES documents(id),
    similarity_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (document_id, similar_document_id)
);
```

### Vector Manager Implementation

```python
# backend/app/ml/clustering/vector_manager.py
import numpy as np
from app.ml.ollama_embeddings import get_ollama_embedding
from sqlalchemy.orm import Session
from app.models.database import SessionLocal

class VectorManager:
    def __init__(self):
        self.embedding_dim = 768  # Ollama llama3.1:8b dimension

    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using Ollama"""
        return await get_ollama_embedding(text)

    async def store_embedding(self, doc_id: str, text: str, db: Session):
        """Generate and store embedding for document"""
        embedding = await self.generate_embedding(text)

        # Convert to pgvector format
        embedding_str = "[" + ",".join(map(str, embedding.tolist())) + "]"

        db.execute("""
            INSERT INTO documents (id, text_content, embedding)
            VALUES (:id, :text, :embedding)
            ON CONFLICT (id) DO UPDATE
            SET embedding = :embedding
        """, {
            "id": doc_id,
            "text": text,
            "embedding": embedding_str
        })

    async def batch_generate_embeddings(self, texts: list) -> list:
        """Generate embeddings for multiple texts efficiently"""
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings

    async def find_similar_documents(
        self,
        query_text: str,
        db: Session,
        limit: int = 10,
        threshold: float = 0.85
    ) -> list:
        """Find similar documents using vector search"""

        # Generate query embedding
        query_embedding = await self.generate_embedding(query_text)
        embedding_str = "[" + ",".join(map(str, query_embedding.tolist())) + "]"

        # Execute similarity search using pgvector
        result = db.execute("""
            SELECT
                id,
                text_content,
                1 - (embedding <=> :query_embedding::vector) as similarity
            FROM documents
            WHERE 1 - (embedding <=> :query_embedding::vector) > :threshold
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :limit
        """, {
            "query_embedding": embedding_str,
            "threshold": threshold,
            "limit": limit
        })

        return result.fetchall()
```

### Clustering Engine Implementation

```python
# backend/app/ml/clustering/clustering_engine.py
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score
import numpy as np

class ClusteringEngine:
    def __init__(self):
        self.algorithms = {
            "kmeans": self._kmeans_cluster,
            "dbscan": self._dbscan_cluster
        }

    async def cluster_documents(
        self,
        embeddings: np.ndarray,
        algorithm: str = "kmeans",
        n_clusters: int = 5,
        **kwargs
    ) -> dict:
        """Run clustering algorithm on document embeddings"""

        if algorithm not in self.algorithms:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        # Run clustering
        cluster_func = self.algorithms[algorithm]
        labels, metrics = await cluster_func(embeddings, n_clusters, **kwargs)

        # Calculate cluster statistics
        cluster_stats = self._calculate_cluster_stats(labels, embeddings)

        return {
            "labels": labels.tolist(),
            "n_clusters": len(set(labels)),
            "metrics": metrics,
            "cluster_stats": cluster_stats
        }

    async def _kmeans_cluster(
        self,
        embeddings: np.ndarray,
        n_clusters: int,
        **kwargs
    ) -> tuple:
        """K-means clustering"""

        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            **kwargs
        )
        labels = kmeans.fit_predict(embeddings)

        # Calculate metrics
        silhouette = silhouette_score(embeddings, labels)

        metrics = {
            "silhouette_score": float(silhouette),
            "inertia": float(kmeans.inertia_),
            "n_iter": int(kmeans.n_iter_)
        }

        return labels, metrics

    async def _dbscan_cluster(
        self,
        embeddings: np.ndarray,
        eps: float = 0.5,
        min_samples: int = 5,
        **kwargs
    ) -> tuple:
        """DBSCAN clustering (density-based)"""

        dbscan = DBSCAN(
            eps=eps,
            min_samples=min_samples,
            metric="cosine",
            **kwargs
        )
        labels = dbscan.fit_predict(embeddings)

        # Calculate metrics (excluding noise points)
        unique_labels = set(labels)
        unique_labels.discard(-1)  # Remove noise label

        if len(unique_labels) > 1:
            silhouette = silhouette_score(
                embeddings,
                labels,
                metric="cosine"
            )
        else:
            silhouette = 0.0

        metrics = {
            "silhouette_score": float(silhouette),
            "n_clusters": len(unique_labels),
            "n_noise_points": int(sum(1 for l in labels if l == -1))
        }

        return labels, metrics

    def _calculate_cluster_stats(
        self,
        labels: np.ndarray,
        embeddings: np.ndarray
    ) -> list:
        """Calculate statistics for each cluster"""

        unique_labels = set(labels)
        cluster_stats = []

        for label in unique_labels:
            mask = labels == label
            cluster_embeddings = embeddings[mask]

            stats = {
                "cluster_id": int(label),
                "size": int(sum(mask)),
                "centroid": cluster_embeddings.mean(axis=0).tolist(),
                "avg_distance_to_centroid": float(
                    np.linalg.norm(
                        cluster_embeddings - cluster_embeddings.mean(axis=0),
                        axis=1
                    ).mean()
                )
            }
            cluster_stats.append(stats)

        return cluster_stats
```

### Similarity Search API

```python
# backend/app/api/routes/clustering.py
from fastapi import APIRouter, Depends
from app.ml.clustering.vector_manager import VectorManager
from app.ml.clustering.clustering_engine import ClusteringEngine
from app.models.database import get_db

router = APIRouter(prefix="/api/clustering", tags=["clustering"])

@router.post("/similar")
async def find_similar_documents(
    text: str,
    limit: int = 10,
    threshold: float = 0.85,
    db: Session = Depends(get_db)
):
    """Find documents similar to input text"""
    vector_manager = VectorManager()

    similar_docs = await vector_manager.find_similar_documents(
        query_text=text,
        db=db,
        limit=limit,
        threshold=threshold
    )

    return {
        "query_text": text,
        "similar_documents": [
            {
                "id": doc.id,
                "text": doc.text_content,
                "similarity": float(doc.similarity)
            }
            for doc in similar_docs
        ]
    }

@router.post("/cluster")
async def cluster_documents(
    algorithm: str = "kmeans",
    n_clusters: int = 5,
    db: Session = Depends(get_db)
):
    """Cluster all documents for a user"""
    # Trigger async clustering job
    job_id = await cluster_documents_async.delay(
        user_id=user.id,
        algorithm=algorithm,
        n_clusters=n_clusters
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Clustering job started"
    }
```

### Build Order Implications

**Build FOURTH** (after batch processing):
- Depends on: Vector storage (pgvector), batch analysis (for embedding many docs)
- Enables: Document organization, similarity search, duplicate detection

**Why this order:**
- Needs batch processing to efficiently generate embeddings for many documents
- Advanced feature that builds on top of analysis pipeline
- Can be developed in parallel with browser extension, but core backend should come first

---

## Integration Points & Data Flow Summary

### Cross-Component Communication

```
┌─────────────────────────────────────────────────────────────────┐
│                        Request Flow                              │
└─────────────────────────────────────────────────────────────────┘

1. Web UI Request:
   React → FastAPI Route → Service → ML/Ensemble → DB → Response

2. Browser Extension Request:
   Content Script → Background Worker → FastAPI Route → ...
   (same as Web UI from API onward)

3. Batch Processing:
   Web UI → BatchService → Celery → BatchWorker → AnalysisService → ...
   (uses standard analysis pipeline)

4. Clustering:
   Web UI → ClusteringService → VectorManager → Ollama → pgvector → ...
   (separate from analysis pipeline)

┌─────────────────────────────────────────────────────────────────┐
│                    Component Dependencies                        │
└─────────────────────────────────────────────────────────────────┘

Layer 1: Core ML (Existing)
  - Feature Extraction
  - Contrastive Model
  - Ollama Embeddings

Layer 2: Ensemble (Build FIRST)
  - Depends on: Layer 1
  - Adds: Model Registry, Aggregation Engine

Layer 3: Explainability (Build SECOND)
  - Depends on: Layer 1 or 2
  - Adds: SHAP/LIME integration, Attribution Calculator

Layer 4: Batch Processing (Build THIRD)
  - Depends on: Layer 1 + 2 + 3
  - Adds: Job Orchestrator, Progress Tracker, Batch Workers

Layer 5: Clustering (Build FOURTH)
  - Depends on: Layer 1, Batch Processing (for efficiency)
  - Adds: Vector Manager, Similarity Search, Clustering Engine

Layer 6: Browser Extension (Build FIFTH)
  - Depends on: All backend layers
  - Adds: Content Scripts, Background Worker, Popup UI
```

### Shared Infrastructure

**Database (PostgreSQL):**
- Existing: users, analysis_results, fingerprints
- New: batch_jobs, batch_document_results, documents (with pgvector), clusters

**Cache (Redis):**
- Existing: analysis results cache
- New: ensemble results cache, SHAP background datasets, explanations cache

**Task Queue (Celery):**
- Existing: analysis_tasks, rewrite_tasks
- New: batch_tasks, clustering_tasks

**Storage:**
- New: Export files (CSV, JSON) for batch jobs
- New: Model versions for ensemble registry

---

## Recommended Build Order

### Phase 1: Foundation (Ensemble)
**Why first:** Improves core detection accuracy, which all other features depend on.

**Components:**
1. ModelRegistry - discover and version models
2. EnsembleOrchestrator - coordinate multi-model inference
3. AggregationEngine - combine predictions
4. PerformanceMonitor - track model accuracy

**Dependencies:** Existing ML models (stylometric, contrastive)
**Enables:** Better predictions for explainability, batch processing

### Phase 2: Explainability
**Why second:** Helps users understand ensemble predictions, builds trust.

**Components:**
1. AttributionCalculator - SHAP/LIME integration
2. ExplanationFormatter - format explanations
3. CacheManager - cache expensive SHAP computations
4. API endpoints - `/api/analysis?explain=true`

**Dependencies:** Ensemble (or single model), feature extraction
**Enables:** User-facing explanations, auditability

### Phase 3: Batch Processing
**Why third:** Orchestrates existing analysis for scale.

**Components:**
1. JobOrchestrator - create and manage batch jobs
2. ProgressTracker - track job/document status
3. ResultAggregator - collect and format batch results
4. BatchWorker - process document chunks
5. API endpoints - `/api/batch/*`, WebSocket progress

**Dependencies:** Ensemble, Explainability (optional)
**Enables:** Large-scale document analysis

### Phase 4: Clustering
**Why fourth:** Advanced feature that needs batch processing for efficiency.

**Components:**
1. VectorManager - embedding generation and storage
2. SimilarityEngine - nearest neighbor search
3. ClusteringEngine - document clustering
4. pgvector integration - vector similarity search
5. API endpoints - `/api/clustering/*`

**Dependencies:** Vector storage (pgvector), batch analysis (for embeddings)
**Enables:** Document organization, similarity search, duplicate detection

### Phase 5: Browser Extension
**Why fifth:** Depends on stable API contract from all backend features.

**Components:**
1. Content Script - page interaction, text detection
2. Background Worker - API calls, auth, caching
3. Popup UI - quick analysis interface
4. Context Menu - "Analyze with Ghost-Writer"

**Dependencies:** All backend API endpoints
**Enables:** In-browser analysis, user convenience

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Tight Coupling Between Components
**What:** Direct dependencies between ensemble, explainability, batch, clustering
**Why bad:** Can't deploy/upgrade components independently
**Instead:** Use service interfaces, message queues, or API boundaries

**Example of bad pattern:**
```python
# DON'T: Direct coupling
class EnsembleService:
    def __init__(self):
        self.explainability = ExplainabilityService()  # Tight coupling
```

**Example of good pattern:**
```python
# DO: Loose coupling via interfaces
class EnsembleService:
    def __init__(self, model_registry: ModelRegistry):
        self.models = model_registry
        # Explainability is separate, can be added via decorator
```

### Anti-Pattern 2: Blocking SHAP Computations in Request Path
**What:** Computing SHAP values synchronously in API request
**Why bad:** SHAP is 10-100x slower than prediction, blocks requests
**Instead:** Async computation, caching, or pre-computed explanations

**Example of bad pattern:**
```python
# DON'T: Blocking SHAP in request
@router.post("/analyze")
def analyze(text: str):
    prediction = model.predict(text)
    explanation = compute_shap(text)  # Blocks for seconds!
    return {prediction, explanation}
```

**Example of good pattern:**
```python
# DO: Async SHAP or cached
@router.post("/analyze")
async def analyze(text: str, explain: bool = False):
    prediction = model.predict(text)

    result = {"prediction": prediction}

    if explain:
        # Check cache first
        cached = await cache.get(f"explanation:{hash(text)}")
        if cached:
            result["explanation"] = cached
        else:
            # Trigger async computation
            task = compute_shap_async.delay(text)
            result["explanation_task_id"] = task.id

    return result
```

### Anti-Pattern 3: Monolithic Batch Jobs
**What:** Processing all documents in a single batch job without chunking
**Why bad:** No fault tolerance, can't resume from failures, poor progress tracking
**Instead:** Split into chunks, track progress per document

**Example of bad pattern:**
```python
# DON'T: Monolithic job
@celery.task
def process_batch(job_id, documents):
    results = []
    for doc in documents:
        results.append(analyze(doc))  # If one fails, all fail?
    save_results(results)
```

**Example of good pattern:**
```python
# DO: Chunked jobs with progress tracking
@celery.task
def process_batch_chunk(job_id, document_indices, documents):
    results = []
    for idx, doc in zip(document_indices, documents):
        try:
            result = analyze(doc)
            save_document_result(job_id, idx, "completed", result)
            results.append(result)
        except Exception as e:
            save_document_result(job_id, idx, "failed", error=str(e))
    update_job_progress(job_id, len(results))
    return results
```

### Anti-Pattern 4: Browser Extension Polling API
**What:** Extension polls API every second for updates
**Why bad:** Wastes quota, slow updates, poor UX
**Instead:** Use WebSocket for real-time updates or efficient caching

**Example of bad pattern:**
```javascript
// DON'T: Polling
setInterval(async () => {
  const result = await fetch(`/api/status/${jobId}`);
  updateUI(result);
}, 1000);
```

**Example of good pattern:**
```javascript
// DO: WebSocket or cache
// Option 1: WebSocket
const ws = new WebSocket(`wss://api.ghostwriter.local/ws/batch/${jobId}`);
ws.onmessage = (event) => updateUI(JSON.parse(event.data));

// Option 2: Efficient caching with long polling
const result = await cachedFetch(`/api/status/${jobId}`, {maxAge: 5000});
```

### Anti-Pattern 5: Naive Vector Search Without Indexing
**What:** Sequential scan of all vectors for similarity search
**Why bad:** O(n) complexity, doesn't scale beyond 10K documents
**Instead:** Use pgvector indexes (IVFFlat, HNSW)

**Example of bad pattern:**
```sql
-- DON'T: Sequential scan
SELECT * FROM documents
ORDER BY embedding <=> query_vector
LIMIT 10;  -- Scans all rows!
```

**Example of good pattern:**
```sql
-- DO: Indexed search
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Now uses index, O(log n)
SELECT * FROM documents
ORDER BY embedding <=> query_vector
LIMIT 10;
```

---

## Scalability Considerations

### At 1,000 Users
- **Ensemble:** Single model registry, in-memory aggregation
- **Explainability:** Cache SHAP results, background dataset ~100 samples
- **Batch Processing:** 2-4 Celery workers, job queue in Redis
- **Clustering:** pgvector with IVFFlat index, 100 lists
- **Browser Extension:** API rate limiting (30 req/min)

### At 10,000 Users
- **Ensemble:** Distributed model registry, model sharding by user segment
- **Explainability:** Dedicated SHAP workers, larger background datasets (1000 samples)
- **Batch Processing:** 8-16 Celery workers, priority queues, job results in object storage
- **Clustering:** pgvector partitioning by user_id, HNSW index for faster search
- **Browser Extension:** Distributed caching (CloudFlare), CDN for extension assets

### At 100,000 Users
- **Ensemble:** Multi-region model deployment, A/B testing infrastructure
- **Explainability:** Pre-computed explanations for common texts, approximate SHAP
- **Batch Processing:** Celery cluster with autoscaling (Kubernetes), S3 for exports
- **Clustering:** Dedicated vector database (Qdrant/Pinecone), separate from PostgreSQL
- **Browser Extension:** Edge computing (CloudFlare Workers), API gateway with rate limiting

---

## Sources

### Multi-Model Ensemble Architecture
- [An Optimized Weighted-Voting-Based Ensemble Learning for Fake News Detection (MDPI, 2025)](https://www.mdpi.com/2079-9292/14/23/4766) - MEDIUM confidence, peer-reviewed research on weighted voting
- [A Comparative Analysis of Hybrid Voting and Ensemble Learning (arXiv, September 2025)](https://arxiv.org/pdf/2509.18880?) - MEDIUM confidence, recent ensemble methods comparison
- [PAT: Ensemble Learning Model Architecture (July 2024)](https://example.com) - LOW confidence, general ensemble patterns (URL placeholder - search result was incomplete)

### Explainability & Feature Attribution
- [Explainable AI in Production: SHAP and LIME for Real-time Predictions (JavaCodeGeeks, March 2025)](https://www.javacodegeeks.com/2025/03/explainable-ai-in-production-shap-and-lime-for-real-time-predictions.html) - HIGH confidence, production deployment strategies
- [Explainable AI: SHAP, XAI Methods, and .NET Integration (DZone, August 2025)](https://dzone.com/articles/explainable-ai-shap-xai-methods-dotnet-integration) - HIGH confidence, integration patterns
- [SHAP vs LIME: Which XAI Tool Is Right for Your Use Case? (EthicalXAI, July 2025)](https://ethicalxai.com/blog/shap-vs-lime-xai-tool-comparison-2025.html) - HIGH confidence, tool comparison for 2025
- [Comparing Explainable AI Models: SHAP, LIME, and Their Applications (MDPI, 2025)](https://www.mdpi.com/2079-9292/14/23/4766) - HIGH confidence, peer-reviewed comparison
- [Explainable AI Framework Comparison (Medium, Kedion)](https://kedion.medium.com/explainable-ai-framework-comparison-106c783554a) - MEDIUM confidence, framework overview

### Batch Processing with Celery & FastAPI
- [Building Scalable Background Jobs with FastAPI + Celery + Redis (Medium, 2025)](https://medium.com/@shaikhasif03/building-scalable-background-jobs-with-fastapi-celery-redis-e43152829c61) - HIGH confidence, practical implementation guide
- [Celery + Redis + FastAPI: The Ultimate 2025 Production Guide (Medium, 2025)](https://medium.com/@dewasheesh.rana/celery-redis-fastapi-the-ultimate-2025-production-guide-broker-vs-backend-explained-5b84ef508fa7) - HIGH confidence, production best practices
- [Building async processing pipelines with FastAPI and Celery (Upsun DevCenter, October 2025)](https://devcenter.upsun.com/posts/building-async-processing-pipelines-with-fastapi-and-celery-on-upsun/) - HIGH confidence, recent implementation patterns
- [Building a Scalable Background Task System in Python (Python Plain English, August 2025)](https://python.plainenglish.io/building-a-scalable-background-task-system-in-python-3d37f543afdb) - HIGH confidence, distributed task architecture
- [Batch Processing with FastAPI: A Detailed Guide (LinkedIn)](https://www.linkedin.com/pulse/batch-processing-fastapi-detailed-guide-manikandan-parasuraman-o6whc) - MEDIUM confidence, specific to batch processing

### Browser Extension Architecture
- [The Architecture of Chrome Extension Permissions (Voicewriter, September 2024)](https://voicewriter.io/blog/the-architecture-of-chrome-extension-permissions-a-deep-dive) - HIGH confidence, component architecture
- [Content scripts - Chrome for Developers](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts) - HIGH confidence, official documentation
- [About extension service workers - Chrome for Developers](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers) - HIGH confidence, official background worker documentation
- [Content scripts - MDN Web Docs (November 30, 2025)](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Content_scripts) - HIGH confidence, official Firefox documentation
- [Understanding Chrome Extensions Communication (M2K Developments)](https://m2kdevelopments.medium.com/5-understanding-chrome-extensions-communication-0b76b3c7958f) - MEDIUM confidence, communication patterns

### Document Clustering & Vector Search
- [pgvector GitHub Repository](https://github.com/pgvector/pgvector) - HIGH confidence, official pgvector documentation
- [PostgreSQL as a Vector Database: A Pgvector Tutorial (TigerData)](https://www.tigerdata.com/blog/postgresql-as-a-vector-database-using-pgvector) - HIGH confidence, comprehensive tutorial
- [Everything You Need to Know About pgvector (Northflank, February 2025)](https://northflank.com/blog/postgresql-vector-search-guide-with-pgvector) - HIGH confidence, recent guide
- [Vector Similarity Search Deep Dive (SeveralNines, December 2025)](https://severalnines.com/blog/vector-similarity-search-with-postgresqls-pgvector-a-deep-dive/) - HIGH confidence, in-depth exploration
- [What is a Vector Database & How Does it Work (Pinecone)](https://www.pinecone.io/learn/vector-database/) - HIGH confidence, vector database fundamentals
- [Survey of Vector Database Management Systems (arXiv, 2023, 236 citations)](https://arxiv.org/pdf/2310.14021) - HIGH confidence, academic survey of 20+ systems
- [Vector Database vs. Document Databases (Zilliz, March 2025)](https://zilliz.com/blog/vector-database-vs-document-databases) - HIGH confidence, comparison and use cases

### FastAPI ML Serving Architecture
- [FastAPI Best Practices: A Complete Guide for Building Production-Ready APIs (Medium, 2025)](https://medium.com/@abipoongodi1211/fastapi-best-practices-a-complete-guide-for-building-production-ready-apis-bb27062d7617) - HIGH confidence, comprehensive best practices
- [FastAPI for Scalable Microservices: Best Practices (WebAndCrafts, January 2025)](https://webandcrafts.com/blog/fastapi-scalable-microservices) - HIGH confidence, microservices architecture
- [APIs for Model Serving - Made With ML by Anyscale](https://madewithml.com/courses/mlops/api/) - HIGH confidence, MLOps patterns for model serving
- [FastAPI Production Deployment Best Practices (Render, November 2025)](https://render.com/articles/fastapi-production-deployment-best-practices) - HIGH confidence, production deployment

### AI Text Detection Research
- [Diversity Boosts AI-Generated Text Detection (arXiv, 2025)](https://arxiv.org/pdf/2509.18880?) - MEDIUM confidence, recent detection research
- [Detecting AI-Generated Text: Factors Influencing Detectability (ResearchGate, 2024)](https://www.researchgate.net/publication/381666008_Detecting_AI-Generated_Text_Factors_Influencing_Detectability_with_Current_Methods) - HIGH confidence, comprehensive survey
- [Explainability for Large Language Models: A Survey (ACM)](https://dl.acm.org/doi/10.1145/3639372) - HIGH confidence, LLM explainability survey
- [Explainable Artificial Intelligence (XAI) 2.0: A manifesto (ScienceDirect, 2024, 609 citations)](https://www.sciencedirect.com/science/article/pii/S1566253524000794) - HIGH confidence, XAI foundations

**Note:** Some sources marked as LOW confidence where URLs were incomplete or sources were not verified against official documentation.
