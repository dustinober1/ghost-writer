# Technology Stack: Advanced Features

**Project:** Ghost-Writer
**Research Date:** 2025-01-18
**Mode:** Stack enhancements for Phase 1-5 features

## Executive Summary

Based on 2025 ecosystem research, the recommended stack for advanced Ghost-Writer features builds strategically on the existing foundation:

**Core additions:**
- **SHAP 0.50.0** - Model explainability (per-sentence attribution)
- **Celery 5.3.4** (existing) - Batch processing job queue
- **scikit-learn 1.3.2** (existing) - Multi-model ensemble
- **WXT** - Browser extension framework
- **Qdrant** - Vector database for document clustering

**Key decision:** Leverage existing stack (Celery, scikit-learn, PyTorch) where possible. Only add new technologies where clear 2025 standard exists and no existing option suffices.

---

## 1. Explainability: Per-Sentence Confidence & Feature Attribution

### Recommended: SHAP 0.50.0

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **SHAP** | **0.50.0** | Feature attribution for sentence-level AI detection | Game-theoretic approach, model-agnostic, industry standard in 2025. TreeExplainer for fast exact tree SHAP values, KernelExplainer for model-agnostic support. |
| numpy | existing | Numerical computing for SHAP calculations | Already in stack, required by SHAP |
| matplotlib | existing | Visualization of feature attributions | Already in stack, SHAP integrates for plots |

### Installation

```bash
# Core explainability
pip install shap==0.50.0

# For visualizations (likely already present)
pip install matplotlib
```

### Why SHAP Over Alternatives

| Alternative | Why Not |
|-------------|---------|
| **LIME** | Less theoretically sound (local linear approximation), SHAP unifies multiple methods including LIME, SHAP provides global feature importance |
| **ELI5** | Less maintained, fewer features, SHAP has better visualization |
| **Custom implementation** | Reinventing wheel, SHAP provides battle-tested implementations |

### Implementation Pattern

```python
# Example: Sentence-level attribution
import shap

# For tree-based models (fast exact)
explainer = shap.TreeExplainer(model)
shap_values = explainer(sentence_features)

# For model-agnostic (slower)
explainer = shap.KernelExplainer(model.predict, background_data)
shap_values = explainer.shap_values(sentence_features)

# Visualize
shap.waterfall(shap_values[i])  # Single sentence explanation
shap.summary_plot(shap_values, feature_names)
```

### Confidence: HIGH

**Sources:**
- [SHAP GitHub Repository](https://github.com/shap/shap) - Official repo, active development
- [SHAP PyPI](https://pypi.org/project/shap/) - Latest version 0.50.0 released 2025-11-11
- [SHAP Documentation](https://shap.readthedocs.io/) - Comprehensive guides
- 2025 research confirms SHAP and LIME remain dominant methods for feature attribution

---

## 2. Batch Processing: Job Queues & Multi-File Analysis

### Recommended: Celery 5.3.4 (Existing)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Celery** | **5.3.4** (existing) | Distributed task queue for batch document processing | Already in stack, production-ready, battle-tested for document processing workflows |
| **Redis** | **5.0.1** (existing) | Message broker and result backend | Already in stack, required by Celery |
| **Flower** | **2.0.0** | Celery monitoring UI (optional add-on) | Real-time task monitoring, helpful for debugging batch jobs |

### Installation

```bash
# Already in requirements.txt, but ensure versions:
celery==5.3.4
redis==5.0.1

# Optional monitoring
pip install flower==2.0.0
```

### Why Celery Over Alternatives

| Alternative | Why Not |
|-------------|---------|
| **RQ (Redis Queue)** | Simpler but less feature-rich, Celery already in stack, Celery provides better scheduling and retries |
| **Arq** | Async-focused but less mature, Celery more battle-tested for document processing |
| **Dramatiq** | Good alternative but Celery already integrated |

### 2025 Best Practices (Verified)

**From research:**
1. **Use task priorities** for urgent vs. batch jobs
2. **Implement dead letter queues** for failed tasks
3. **Set task timeouts** to prevent hanging jobs
4. **Use Celery Canvas** (chains, chords) for multi-step workflows
5. **Monitor with Flower** or Prometheus metrics

**Implementation Pattern:**

```python
# tasks.py
from celery import Celery
from celery import chain, chord

app = Celery('ghostwriter', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3)
def analyze_document(self, doc_id):
    try:
        # Analysis logic
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

# Workflow: Chain multiple tasks
workflow = chain(
    extract_features.s(doc_id),
    analyze_sentences.s(),
    generate_report.s()
)
```

### Confidence: HIGH

**Sources:**
- [Celery 5.6.2 Documentation](https://docs.celeryq.dev/en/stable/) - Current stable version
- [Celery Best Practices 2025](https://oneuptime.com/blog/post/2025-01-06-python-celery-redis-job-queue/view) - Recent implementation guide
- [7 Scheduler Strategies for Python Jobs](https://medium.com/@ThinkingLoop/7-scheduler-strategies-for-python-jobs-celery-rq-arq-48b1eb5f8f79) - Celery vs RQ vs Arq comparison (2 months old)

---

## 3. Multi-Model Ensemble: AI Detection Combining

### Recommended: scikit-learn 1.3.2 (Existing)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **scikit-learn** | **1.3.2** (existing) | Ensemble methods (VotingClassifier, StackingClassifier) | Already in stack, production-ready, comprehensive ensemble implementations |
| **PyTorch** | **2.1.0** (existing) | Deep learning model integration | Already in stack for custom model implementations |

### Installation

```bash
# Already in stack
scikit-learn==1.3.2
torch==2.1.0
```

### Why scikit-learn Over Alternatives

| Alternative | Why Not |
|-------------|---------|
| **XGBoost/LightGBM only** | Good for boosting but limited to tree models, scikit-learn provides voting/stacking for any model type |
| **Custom ensemble** | Reinventing wheel, scikit-learn provides battle-tested implementations with cross-validation support |

### 2025 Ensemble Patterns

**Voting Classifier (Simple):**

```python
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# Combine existing stylometric model + new detector model
ensemble = VotingClassifier(
    estimators=[
        ('stylometric', stylometric_model),
        ('perplexity', perplexity_model),
        ('detector', detector_model)
    ],
    voting='soft'  # Use probabilities
)
```

**Stacking Classifier (Advanced):**

```python
from sklearn.ensemble import StackingClassifier
from sklearn.ensemble import GradientBoostingClassifier

# Meta-learner combines base models
ensemble = StackingClassifier(
    estimators=[
        ('stylometric', stylometric_model),
        ('perplexity', perplexity_model),
        ('detector', detector_model)
    ],
    final_estimator=GradientBoostingClassifier(n_estimators=25),
    cv=5  # Cross-validation for meta-features
)
```

### Confidence: HIGH

**Sources:**
- [scikit-learn Ensemble Documentation](https://scikit-learn.org/stable/modules/ensemble.html) - Official documentation (v1.8.0)
- [Ensemble Methods 2025](https://www.analyticsvidhya.com/blog/2023/01/ensemble-learning-methods-bagging-boosting-and-stacking/) - Updated April 2025
- [Voting Ensembles in ML](https://pub.towardsai.net/voting-ensembles-in-machine-learning-making-predictions-stronger-together-b5db981fd225) - October 2024

---

## 4. Browser Extensions: Chrome & Firefox

### Recommended: WXT Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **WXT** | **latest** | Modern browser extension framework | Cross-browser (Chrome V3 + Firefox V2/V3), framework-agnostic (works with React), Type-safe, excellent DX |
| **React** | **18.2.0** (existing) | Extension UI | Already in stack, WXT has excellent React integration |
| **Vite** | **5.0.0** (existing) | Extension build tool | Already in stack, WXT built on Vite |

### Installation

```bash
# Create new extension
npm create wxt@latest ghostwriter-extension

# Or add to existing project
npm install -D wxt
```

### Why WXT Over Alternatives

| Alternative | Why Not |
|-------------|---------|
| **Plasmo** | React-centric (less flexible), some teams migrating away to WXT, less mature cross-browser support |
| **CRXJS** | Less mature, smaller community, WXT has better documentation |
| **Vanilla Manifest V3** | Too low-level, reinventing build/dev tools, WXT provides modern DX |

### 2025 Browser Extension Landscape

**Key Findings:**
- **Chrome:** Manifest V3 mandatory since June 2024
- **Firefox:** Supports both V2 and V3 (no deprecation planned)
- **Cross-browser:** WXT makes this trivial with automatic manifest handling

**Real-world Migration:**
> "Why We Decided to Migrate from Plasmo to WXT" - Teams report WXT better for:
- Framework flexibility (not React-only)
- Cross-browser compatibility
- TypeScript support
- Active development

**Implementation Pattern:**

```typescript
// entrypoints/content.ts
import { createContentScript } from 'wxt/sandbox'

export default defineContentScript({
  matches: ['<all_urls>'],
  main() {
    // Analyze text on page
    const selection = window.getSelection().toString()
    if (selection.length > 50) {
      // Send to Ghost-Writer API
      chrome.runtime.sendMessage({
        type: 'analyze',
        text: selection
      })
    }
  }
})

// entrypoints/background.ts
export default defineBackground(() => {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'analyze') {
      // Call Ghost-Writer API
      analyzeText(message.text)
        .then(result => sendResponse(result))
      return true  // Async response
    }
  })
})
```

### Confidence: HIGH

**Sources:**
- [WXT Comparison Page](https://wxt.dev/guide/resources/compare) - Official comparison (updated Feb 2025)
- [Chrome Extension Framework Comparison 2025](https://www.devkit.best/blog/mdx/chrome-extension-framework-comparison-2025) - December 19, 2025
- [Why We Migrated from Plasmo to WXT](https://jetwriter.ai/blog/migrate-plasmo-to-wxt) - Real-world migration (Sept 2024)
- [The 2025 State of Browser Extension Frameworks](https://redreamality.com/blog/the-2025-state-of-browser-extension-frameworks-a-comparative-analysis-of-plasmo-wxt-and-crxjs/) - September 3, 2025

---

## 5. Document Clustering & Similarity Search

### Recommended: Qdrant Vector Database

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Qdrant** | **latest** | Vector similarity search and document clustering | Written in Rust (fast), self-hosted, excellent hybrid search, production-ready, active development |
| **sentence-transformers** | **latest** | Generate document embeddings | State-of-the-art embeddings, easy integration with Qdrant |
| **FastEmbed** | **latest** (optional) | Lightweight embedding generation | Qdrant's official library, faster for production use |

### Installation

```bash
# Vector database
pip install qdrant-client

# Embeddings (choose one)
pip install sentence-transformers  # Full-featured
pip install fastembed  # Lightweight, Qdrant-optimized

# Or run Qdrant in Docker
docker run -p 6333:6333 qdrant/qdrant
```

### Why Qdrant Over Alternatives

| Alternative | Why Not |
|-------------|---------|
| **Weaviate** | Excellent hybrid search but Qdrant has simpler setup, faster performance, lower resource requirements |
| **Milvus** | More complex setup, higher resource requirements, overkill for Ghost-Writer's use case |
| **pgvector** | Good for Postgres users but Qdrant provides better vector-specific features and performance |
| **Chroma** | Too simple, lacks production features like filtering and payload indexing |

### 2025 Vector Database Research

**Key Findings:**
- **Self-hosted cost:** $100-200/month on AWS for Qdrant vs $300-600/month for Milvus
- **Performance:** Qdrant excels at high recall rates with customizable ANN methods
- **Hybrid search:** Qdrant provides superior hybrid search (vector + keyword) vs pure vector databases
- **Production readiness:** Both Qdrant and Weaviate are production-ready; Qdrant chosen for performance/simplicity

**Implementation Pattern:**

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Initialize
client = QdrantClient(url="http://localhost:6333")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Create collection
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Index documents
docs = ["Sample text 1", "Sample text 2"]
vectors = embedder.encode(docs).tolist()

client.upsert(
    collection_name="documents",
    points=[
        PointStruct(id=1, vector=vectors[0], payload={"text": docs[0]}),
        PointStruct(id=2, vector=vectors[1], payload={"text": docs[1]})
    ]
)

# Similarity search
query = "Find similar documents"
query_vector = embedder.encode(query).tolist()

results = client.search(
    collection_name="documents",
    query_vector=query_vector,
    limit=5
)
```

### Confidence: HIGH

**Sources:**
- [Qdrant Documentation](https://qdrant.tech/documentation/) - Official docs
- [Best Vector Databases 2025](https://www.firecrawl.dev/blog/best-vector-databases-2025) - October 20, 2025 comparison
- [Vector Database Comparison 2025](https://tensorblue.com/blog/vector-database-comparison-pinecone-weaviate-qdrant-milvus-2025) - Detailed cost/performance analysis
- [Best Vector DB for RAG 2025](https://digitaloneagency.com.au/best-vector-database-for-rag-in-2025-pinecone-vs-weaviate-vs-qdrant-vs-milvus-vs-chroma/) - Recommends Weaviate or Qdrant for open-source

---

## 6. Additional Supporting Technologies

### API Layer (Enhanced)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **FastAPI** | **0.104.1** (existing) | REST API endpoints | Already in stack, async support, auto OpenAPI docs |
| **python-jose** | **3.3.0** (existing) | JWT API authentication | Already in stack |
| **slowapi** | **0.1.9** (existing) | Rate limiting per API key | Already in stack |

### Testing & Quality

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **pytest** | existing | Async API testing | Already in stack |
| **locust** | **2.20.1** (existing) | Load testing batch endpoints | Already in stack |

### Monitoring & Observability

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **structlog** | **23.2.0** (existing) | Structured logging | Already in stack |
| **prometheus-client** | **0.19.0** (existing) | Metrics collection | Already in stack |
| **sentry-sdk** | **1.40.0** (existing) | Error tracking | Already in stack |

---

## Installation Summary

### Full Additions to requirements.txt

```txt
# ===== NEW ADDITIONS FOR ADVANCED FEATURES =====

# Explainability (Section 1)
shap==0.50.0

# Batch Processing (Section 2) - Already present
# celery==5.3.4
# redis==5.0.1

# Multi-model Ensemble (Section 3) - Already present
# scikit-learn==1.3.2
# torch==2.1.0

# Browser Extension (Section 4) - Frontend addition
# Installed via npm in extension/
# npm install -D wxt

# Document Clustering (Section 5)
qdrant-client==1.12.0
sentence-transformers==3.0.1
# fastembed  # Optional, for production use

# Optional Monitoring
# flower==2.0.0  # For Celery monitoring UI
```

### Frontend package.json additions

```json
{
  "devDependencies": {
    "wxt": "^0.19.0"
  }
}
```

---

## Migration Path

### Phase 1: Core Enhancements
1. Add SHAP for explainability (per-sentence attribution)
2. Enhance Celery tasks for batch processing
3. Build ensemble models with scikit-learn

### Phase 2: Advanced Detection
1. Multi-model ensemble integration
2. Performance optimization with Celery chords

### Phase 5: Distribution
1. Build browser extension with WXT
2. Add vector similarity search with Qdrant

---

## What NOT to Use (Anti-Patterns for 2025)

### ❌ Avoid These

| Technology | Why Avoid |
|------------|-----------|
| **LIME** (instead of SHAP) | Less theoretically sound, SHAP supersedes it |
| **RQ** (instead of Celery) | Already have Celery, RQ offers no advantage |
| **Plasmo** (instead of WXT) | Teams migrating away, less flexible |
| **Weaviate** (instead of Qdrant) | Good but Qdrant simpler/faster for this use case |
| **Milvus** (instead of Qdrant) | Overkill, higher cost, more complex |
| **Cloud vector DBs** (Pinecone) | Violates self-hosted constraint |
| **Custom ensemble code** | scikit-learn provides battle-tested implementations |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Explainability (SHAP) | HIGH | Industry standard, actively maintained, verified with PyPI |
| Batch Processing (Celery) | HIGH | Already in stack, 2025 best practices verified |
| Multi-model Ensemble (sklearn) | HIGH | Already in stack, official docs comprehensive |
| Browser Extensions (WXT) | HIGH | 2025 comparisons favor WXT, real-world migration evidence |
| Vector Database (Qdrant) | HIGH | 2025 comparisons favor Qdrant/Weaviate, Qdrant chosen for performance |

---

## Sources

### Explainability
- [SHAP GitHub](https://github.com/shap/shap) - Official repository
- [SHAP PyPI](https://pypi.org/project/shap/) - Latest version 0.50.0 (2025-11-11)
- [Intro to SHAP, LIME](https://medium.com/data-science-collective/intro-to-shap-lime-and-model-interpretability-88bf4f88ea15) - Method comparison
- [Comparing Explainable AI Models](https://www.mdpi.com/2079-9292/14/23/4766) - 2025 research

### Batch Processing
- [Celery Documentation](https://docs.celeryq.dev/en/stable/) - Version 5.6.2
- [Celery + Redis Job Queue 2025](https://oneuptime.com/blog/post/2025-01-06-python-celery-redis-job-queue/view) - January 6, 2025
- [7 Scheduler Strategies](https://medium.com/@ThinkingLoop/7-scheduler-strategies-for-python-jobs-celery-rq-arq-48b1eb5f8f79) - 2 months old

### Multi-model Ensemble
- [scikit-learn Ensemble Guide](https://scikit-learn.org/stable/modules/ensemble.html) - Official documentation v1.8.0
- [Ensemble Learning Methods 2025](https://www.analyticsvidhya.com/blog/2023/01/ensemble-learning-methods-bagging-boosting-and-stacking/) - Updated April 4, 2025
- [Voting Ensembles in ML](https://pub.towardsai.net/voting-ensembles-in-machine-learning-making-predictions-stronger-together-b5db981fd225) - October 4, 2024

### Browser Extensions
- [WXT Comparison](https://wxt.dev/guide/resources/compare) - Official (updated Feb 8, 2025)
- [Chrome Extension Frameworks 2025](https://www.devkit.best/blog/mdx/chrome-extension-framework-comparison-2025) - December 19, 2025
- [State of Browser Extension Frameworks 2025](https://redreamality.com/blog/the-2025-state-of-browser-extension-frameworks-a-comparative-analysis-of-plasmo-wxt-and-crxjs/) - September 3, 2025
- [Migration from Plasmo to WXT](https://jetwriter.ai/blog/migrate-plasmo-to-wxt) - September 26, 2024

### Vector Databases
- [Qdrant Documentation](https://qdrant.tech/documentation/) - Official docs
- [Best Vector Databases 2025](https://www.firecrawl.dev/blog/best-vector-databases-2025) - October 20, 2025
- [Vector DB Comparison 2025](https://tensorblue.com/blog/vector-database-comparison-pinecone-weaviate-qdrant-milvus-2025) - Cost/performance analysis
- [Best Vector DB for RAG 2025](https://digitaloneagency.com.au/best-vector-database-for-rag-in-2025-pinecone-vs-weaviate-vs-qdrant-vs-milvus-vs-chroma/) - Recommends Qdrant/Weaviate

---

*Last updated: 2025-01-18*
