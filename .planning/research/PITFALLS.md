# Domain Pitfalls

**Domain:** AI Text Detection & Stylometric Analysis Platform
**Researched:** 2025-01-18
**Confidence:** HIGH

## Critical Pitfalls

Mistakes that cause rewrites, security incidents, or complete feature failure.

### Pitfall 1: Misleading Attribution in Explainability Systems

**What goes wrong:** Feature attribution methods (SHAP, LIME, attention visualization) claim to explain AI predictions but actually show spurious correlations. Users trust explanations that are mathematically correct but semantically meaningless.

**Why it happens:**
- Attribution methods highlight any feature that correlates with predictions, including proxy variables
- Neural networks are "overconfident in their mistakes, thus masking their errors"
- Sentence-level heat maps show probability without indicating model uncertainty

**Consequences:**
- Users make decisions based on false confidence (e.g., academic accusations, HR screening)
- Model appears explainable but explanations are misleading
- Legal liability when explanations are proven wrong

**Prevention:**
- Always show calibrated confidence intervals with explanations
- Include uncertainty quantification ( monte carlo dropout, ensemble variance)
- Use multiple attribution methods and show when they disagree
- Add explicit disclaimers: "This feature contributed to prediction but may not be causally meaningful"
- Implement adversarial explanation testing to find spurious attributions

**Detection:**
- Manual review of high-confidence cases reveals non-sensical feature attributions
- Different attribution methods (gradient-based, perturbation-based) disagree significantly
- Explanations change dramatically with minor text rewording

**Phase:** Phase 1 (Explainability) - Must address before shipping per-sentence confidence

---

### Pitfall 2: Adversarial Text Evades All Detection Models

**What goes wrong:** Minor token-level perturbations (paraphrasing, synonym substitution) completely bypass AI detection. Universal attacks work across multiple detector types simultaneously.

**Why it happens:**
- AI detectors rely on surface patterns that adversarial attacks can mask
- Gradient-based optimization (GradEscape, NEURIPS 2025) crafts text to evade detection
- Tokenization attacks specifically target detection mechanism weaknesses
- Commercial watermark removal tools already available

**Consequences:**
- False negative rate approaches 100% against adversarial examples
- System provides false sense of security
- Reputation damage when bypass is publicized

**Prevention:**
- NEVER claim detection is "bypass-proof" - it's an arms race
- Implement ensemble of detection methods (stylometric + perplexity + watermarking)
- Add adversarial training: include attack-generated examples in training data
- Monitor detection evasion attempts and retrain regularly
- Rate limit analysis to prevent automated adversarial probing

**Detection:**
- Sudden increase in low-score texts that are obviously AI-generated
- Users report easy bypass methods
- Comparison with adversarial paper benchmarks shows poor performance

**Phase:** Phase 2 (Multi-model ensemble) - Critical for detection robustness

---

### Pitfall 3: GPU Memory Exhaustion in Ollama Production Deployments

**What goes wrong:** Ollama models consume unreleased GPU memory (up to 6GB reported) after connection errors or timeouts. KV cache memory leaks accumulate until OOM killer terminates the container.

**Why it happens:**
- No automatic cleanup between requests
- VRAM to cache transfers are slow and cause performance bottlenecks
- Multi-GPU setups actually slow inference due to PCIe transfer overhead
- Connection closures leave resources in undefined state

**Consequences:**
- Service hangs after processing some requests
- Container crashes under load
- No recovery except full container restart

**Prevention:**
- Implement Ollama health checks with automatic restart on memory threshold
- Use single GPU per model (avoid multi-GPU)
- Enable Flash Attention and quantized K/V cache
- Monitor GPU memory usage and set strict limits
- Implement request queuing to prevent concurrent model loading
- Consider vLLM for high-throughput scenarios if Ollama instability persists

**Detection:**
- `nvidia-smi` shows monotonically increasing GPU memory usage
- Ollama processes become unresponsive under load
- Latency increases over time as cache fills

**Phase:** Phase 1 (Enterprise API) - Must address before batch processing launches

---

### Pitfall 4: Stylometric False Positives from Closed-World Assumption

**What goes wrong:** Authorship verification fails when true author isn't in candidate set. High precision methods still produce false positives when imposter authors have similar writing styles.

**Why it happens:**
- Most algorithms assume true author is in training data (closed-world)
- Text length constraints: shorter texts increase false positive risk
- Similar writing styles between candidates cause misattribution
- Language dependencies: methods don't generalize across languages

**Consequences:**
- Wrongful accusations of AI-generated content
- Academic integrity cases based on flawed analysis
- Legal liability from defamation

**Prevention:**
- NEVER claim 100% certainty in authorship verification
- Implement open-set recognition: reject when confidence below threshold
- Show calibration: "90% confident this matches User X vs other candidates"
- Require minimum text length (500+ words) for fingerprinting
- Use distance-based methods with calibrated thresholds
- Explicitly warn when imposter authors are too similar

**Detection:**
- Verification claims contradict known authorship
- High confidence scores on obviously incorrect matches
- Cross-validation shows poor performance on held-out authors

**Phase:** Phase 3 (Enhanced fingerprinting) - Critical for authorship verification

---

## Moderate Pitfalls

Mistakes that cause delays, technical debt, or degraded performance.

### Pitfall 5: Batch Processing Memory Exhaustion

**What goes wrong:** In-memory job queues consume unlimited memory until OOM killer terminates process at 47GB+ (real production incident).

**Why it happens:**
- In-memory queues have no backpressure mechanism
- Workers can't completely protect against CPU overloading or heap exhaustion
- No limit on queued job size
- Memory leaks in batch processing workers under high ingestion

**Consequences:**
- System crashes during bulk uploads
- Lost batch jobs when process is killed
- Poor user experience for enterprise customers

**Prevention:**
- Use Redis-backed job queues (Celery/RQ) with max size limits
- Implement backpressure: reject new jobs when queue exceeds threshold
- Set Redis maxmemory policy (e.g., allkeys-lru)
- Monitor queue depth and worker memory usage
- Implement job priorities to prevent starvation
- Use streaming for large file processing instead of loading all into memory

**Detection:**
- Memory usage grows linearly with queue size
- Process killed by OOM killer under load
- Redis memory usage increases monotonically

**Phase:** Phase 1 (Batch processing) - Must address before enterprise launch

---

### Pitfall 6: Rate Limiting Bypassed Through API Key Leakage

**What goes wrong:** API keys exposed in client-side code, logs, or version control allow unlimited quota consumption and credential stuffing attacks.

**Why it happens:**
- Keys embedded in browser extensions or mobile apps
- Keys committed to GitHub repositories
- Keys logged in error messages or debug output
- No key rotation mechanism
- Insufficient rate limit granularity (only per-IP, not per-key)

**Consequences:**
- Quota exhaustion affecting legitimate users
- Credential stuffing attacks using stolen keys
- Financial loss from overage charges
- Account takeover when keys are associated with user accounts

**Prevention:**
- NEVER embed API keys in client-side code
- Implement API key rotation (automatic every 90 days)
- Use scoped keys with granular permissions (read-only, write-only, admin)
- Implement per-key rate limiting separate from per-IP limits
- Add key usage monitoring and anomaly detection
- Log all API key usage for audit trails
- Implement key revocation webhooks
- Use API gateways with built-in key management

**Detection:**
- Sudden spike in usage from single API key
- Keys used from multiple geographic locations simultaneously
- Keys used after user account deletion
- API keys found in GitHub repositories or browser inspect tools

**Phase:** Phase 1 (Enterprise API) - Critical security requirement

---

### Pitfall 7: Browser Extension Content Script Performance Degradation

**What goes wrong:** Content scripts injected into every page slow down page load by 2-5 seconds, causing users to uninstall extension.

**Why it happens:**
- Heavy DOM manipulation on page load
- Large JavaScript bundles injected synchronously
- No defer mechanism for non-critical operations
- Running on every page instead of just content-relevant pages
- Memory leaks from event listeners not cleaned up

**Consequences:**
- High uninstall rate due to performance issues
- Poor reviews complaining about browser slowdown
- Chrome Web Store warnings for performance violations
- Race conditions during navigation crash content scripts

**Prevention:**
- Use `document_idle` instead of `document_start` for non-critical scripts
- Defer analysis until user explicitly triggers (right-click, button click)
- Use content scripts only on relevant pages (match patterns in manifest)
- Implement code splitting: load minimal bundle, lazy-load heavy ML models
- Use background service worker for heavy computation, not content scripts
- Monitor content script execution time with DevTools
- Test on performance-critical sites (Facebook, Twitter, Gmail)

**Detection:**
- Chrome DevTools shows 2+ second content script evaluation time
- Users report extension slows down browsing
- Chrome Web Store performance warnings
- Extension crashes on complex sites

**Phase:** Phase 5 (Browser extension) - Performance critical for adoption

---

### Pitfall 8: Ensemble Model Calibration Drift

**What goes wrong:** Multi-model ensembles become overconfident over time, showing 95%+ confidence on wrong predictions. Calibration drifts as individual models degrade at different rates.

**Why it happens:**
- Naive ensemble methods (averaging, voting) don't account for varying model reliability
- Class overfitting in ensemble weights
- Data drift affects ensemble components differently
- No recalibration mechanism after deployment
- Weight averaging methods inherit overfitting from training

**Consequences:**
- False confidence in incorrect predictions
- Poor performance on new data distributions
- Ensemble performs worse than individual models
- Users lose trust in high-confidence predictions

**Prevention:**
- Implement temperature scaling for each ensemble component
- Use last-layer dropout for uncertainty estimation
- Regular recalibration on held-out data (weekly/monthly)
- Monitor calibration metrics (ECE, Brier score) in production
- Use weighted ensembles where weights = validation performance
- Implement ensemble diversity metrics to detect overfitting
- Consider Monte Carlo dropout for uncertainty estimation

**Detection:**
- Reliability diagram shows overconfidence curve
- High confidence predictions have low accuracy
- Calibration error increases over time
- Individual models disagree but ensemble is still overconfident

**Phase:** Phase 2 (Multi-model ensemble) - Critical for trustworthy predictions

---

### Pitfall 9: Contrastive Learning False Performance Signals

**What goes wrong:** Contrastive models appear to perform well due to inherited strengths from pre-trained embeddings, not actual learning. Zero-shot accuracy reflects embedding quality, not training effectiveness.

**Why it happens:**
- Data imbalance induces biases in classification models
- False performance signals from pre-trained base models
- Sample mining challenges: ineffective positive/negative pair selection
- Label space alignment issues for zero-shot classification

**Consequences:**
- Model performs well on validation but fails in production
- Wasted training time on models that aren't actually learning
- False sense of model capability
- Poor generalization to new writing styles

**Prevention:**
- Evaluate on balanced datasets to detect bias
- Ablation studies: compare with and without contrastive training
- Use hard negative mining for better pair selection
- Monitor training loss vs validation performance gap
- Implement proper cross-validation across different authors
- Test on out-of-distribution data before deployment

**Detection:**
- Training accuracy is high but validation accuracy plateaus
- Model performance similar to using embeddings without training
- Poor performance on new writing styles
- Ablation shows minimal impact from contrastive loss

**Phase:** Phase 2 (Advanced detection) - Model evaluation rigor required

---

### Pitfall 10: Cache Utility Returns None for Failures

**What goes wrong:** Cache failures return `None`, which is ambiguous with "cache miss." Calling code can't distinguish between "cache doesn't have this key" and "cache is down."

**Why it happens:**
- Current implementation: `get_cached()` returns `None` on both cache miss and error
- Bare exception handling catches all errors silently
- No distinction between cache unavailability and key absence
- No metrics on cache health

**Consequences:**
- Silent fallback to expensive operations (re-running ML models)
- No monitoring of cache degradation
- Can't detect when Redis is down
- Performance degradation goes unnoticed

**Prevention:**
- Use typed result objects: `Result<T, CacheError>` instead of `T | None`
- Implement circuit breaker: fail fast when cache is consistently down
- Add separate methods: `get_cached()` (returns None on miss) vs `check_cache_health()` (raises on error)
- Log cache failures with error details
- Add metrics: cache hit rate, cache error rate, cache latency
- Implement graceful degradation but with explicit alerts

**Detection:**
- Increased latency despite high "cache hit" rate
- Logs show cache errors but operation continues
- Metrics show 100% cache hit rate (misses counted as hits)
- No alerts when Redis goes down

**Phase:** Phase 1 (Enterprise API) - Infrastructure reliability required

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable without rewrites.

### Pitfall 11: Hardcoded Localhost Defaults

**What goes wrong:** Configuration defaults to `localhost:11434` (Ollama), `localhost:6379` (Redis), etc. Works in dev but fails in containerized production.

**Why it happens:**
- `os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")` defaults to localhost
- Environment variables not set in Docker Compose
- No validation that configured services are reachable
- Error messages show "localhost" instead of actual configured URL

**Consequences:**
- Containers fail to start in production
- Confusing error messages
- Works on developer machine but not in deployment

**Prevention:**
- Use `None` as default and validate at startup
- Fail fast with clear error: "OLLAMA_BASE_URL not set"
- Validate service reachability on initialization (health checks)
- Show actual configured URL in error messages
- Use environment variable validation library (pydantic-settings, environs)
- Document required environment variables in README

**Detection:**
- Error messages reference "localhost" in production logs
- Services fail to connect with "connection refused"
- Works in dev but fails in Docker

**Phase:** Phase 1 (Enterprise readiness) - Infrastructure hardening

---

### Pitfall 12: Bare Exception Handling Masks Root Causes

**What goes wrong:** `except Exception as e:` without specific exception types or logging. Errors are caught but not properly reported, making debugging impossible.

**Why it happens:**
- Lazy error handling during development
- Fear of crashes leads to over-catching
- No logging in except blocks
- Generic error messages like "operation failed"

**Consequences:**
- Silent failures: operations appear to succeed but don't
- Impossible to debug production issues
- No alerting on actual errors
- Users see generic "something went wrong"

**Prevention:**
- Catch specific exceptions: `except redis.ConnectionError as e:`
- Always log with context: `logger.error("Redis connection failed", url=url, error=str(e))`
- Use structlog for structured logging
- Implement exception chaining: `raise NewError from e`
- Use `raise` without arguments to re-raise after logging
- Add monitoring: alert on specific exception types

**Detection:**
- Many bare `except:` or `except Exception:` blocks in codebase
- Logs show "operation failed" without details
- Production issues have no stack traces
- Silent failures discovered during manual testing

**Phase:** Phase 1 (Production readiness) - Error handling hygiene

---

### Pitfall 13: No API Input Validation Middleware

**What goes wrong:** API endpoints accept malformed input, causing cryptic errors deep in ML pipeline or database. No validation until data reaches business logic.

**Why it happens:**
- Relying on Pydantic models only (validates after endpoint hit)
- No request size limits
- No content-type validation
- No schema validation for JSON payloads

**Consequences:**
- Database errors from oversized strings
- ML model crashes from malformed input
- Poor error messages to API consumers
- Wasted resources processing invalid requests

**Prevention:**
- Implement FastAPI middleware for request validation
- Add request size limits (max 10MB for analysis text)
- Validate content-type before processing
- Use Pydantic for schema validation with custom validators
- Return 400 Bad Request with specific validation errors
- Sanitize input to prevent injection attacks

**Detection:**
- Database errors: "value too long for type varchar(255)"
- ML model errors: "numpy array shape mismatch"
- 500 Internal Server Error for invalid input
- Logs show validation errors deep in call stack

**Phase:** Phase 1 (Enterprise API) - API contract enforcement

---

### Pitfall 14: Browser Extension Permission Bloat

**What goes wrong:** Extension requests unnecessary permissions (all sites access, background scripts, unlimited storage). Users reject installation due to privacy concerns.

**Why it happens:**
- Lazy use of `<all_urls>` instead of specific host patterns
- Requesting permissions for future features not yet implemented
- Using activeTab when content scripts would suffice
- No explanation for why permissions are needed

**Consequences:**
- Low installation rate due to permission warnings
- Users uninstall after seeing permission list
- Chrome Web Store review delays
- Privacy advocates flag extension as suspicious

**Prevention:**
- Use specific host permissions: `*://google.com/docs/*` not `<all_urls>`
- Request permissions incrementally as features are used
- Use activeTab permission only for user-triggered actions
- Add optional permissions for advanced features
- Document why each permission is needed in Chrome Web Store description
- Implement content script injection only on relevant pages

**Detection:**
- Manifest V3 uses `<all_urls>` permission
- Extension requires background permissions for simple operations
- Users complain about excessive permissions in reviews
- Chrome shows "Read and change all your data" warning

**Phase:** Phase 5 (Browser extension) - User trust critical for adoption

---

### Pitfall 15: Feature Attribution Shows Proxy Variables

**What goes wrong:** Explanation systems highlight features that correlate with predictions but aren't causally meaningful (e.g., "text length" or "comma usage" instead of "burstiness").

**Why it happens:**
- Attribution methods don't distinguish correlation from causation
- Models learn spurious correlations from training data
- No feature engineering to remove proxy variables
- Overlap between AI and human writing styles on some features

**Consequences:**
- Misleading explanations that don't reflect actual model reasoning
- Users game the system by changing irrelevant features
- Loss of trust when explanations are obviously wrong
- Regulatory risk for explainability requirements

**Prevention:**
- Remove features that are obvious proxies (text length, formatting)
- Use feature importance ranking with causal inference methods
- Test explanations by perturbing highlighted features
- Use counterfactual explanations: "what would need to change"
- Show multiple explanation methods and highlight disagreements
- Add uncertainty bounds to feature attributions

**Detection:**
- Feature importance changes dramatically with minor text changes
- Highlighted features don't align with domain knowledge
- Users can easily manipulate predictions by changing irrelevant features
- Different attribution methods show completely different features

**Phase:** Phase 1 (Explainability) - Critical for user trust

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| **Phase 1: Explainability** | Misleading attribution (Pitfall 1), Feature proxy variables (Pitfall 15) | Always show uncertainty, use multiple attribution methods, test with adversarial examples |
| **Phase 1: Batch Processing** | Memory exhaustion (Pitfall 5), GPU memory leaks (Pitfall 3) | Use Redis queues with max size, implement Ollama health checks, monitor GPU memory |
| **Phase 1: Enterprise API** | API key leakage (Pitfall 6), No input validation (Pitfall 13), Cache returns None (Pitfall 10) | Implement key rotation, add validation middleware, use typed cache results |
| **Phase 2: Multi-model Ensemble** | Calibration drift (Pitfall 8), Contrastive false signals (Pitfall 9) | Temperature scaling, regular recalibration, monitor calibration metrics |
| **Phase 2: Adversarial Robustness** | Universal attacks bypass detection (Pitfall 2) | Adversarial training, ensemble methods, never claim bypass-proof |
| **Phase 3: Enhanced Fingerprinting** | Closed-world false positives (Pitfall 4) | Open-set recognition, confidence thresholds, minimum text length requirements |
| **Phase 5: Browser Extension** | Performance degradation (Pitfall 7), Permission bloat (Pitfall 14) | Defer non-critical operations, use specific host permissions, monitor performance |
| **All Phases** | Hardcoded localhost (Pitfall 11), Bare exceptions (Pitfall 12) | Environment variable validation, specific exception handling, structured logging |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Explainability Pitfalls | HIGH | Multiple 2024-2025 research papers on XAI pitfalls, Google Vertex AI docs confirm |
| Adversarial Attacks | HIGH | NEURIPS 2025 paper, USENIX Security 2025, EMNLP 2025 all confirm universal attacks |
| GPU Memory Issues | MEDIUM | Based on production incident reports and GitHub issues, limited Ollama-specific documentation |
| Stylometric False Positives | HIGH | Multiple research papers on closed-world assumption, authorship verification challenges |
| Batch Processing Memory | HIGH | DataAnnotation.tech 2025 article on queue failures, GitHub issues confirm |
| API Security | HIGH | 2025 best practice guides from Zuplo, Cloudflare, OWASP - all agree on key management |
| Browser Extension Performance | MEDIUM | Based on Chrome DevTools documentation and community reports, limited academic sources |
| Ensemble Calibration | HIGH | Multiple 2024-2025 papers on calibration drift, weight-averaged models |
| Contrastive Learning | MEDIUM | ArXiv papers on class separability issues, limited production deployment data |
| Infrastructure Issues | HIGH | Directly observed in Ghost-Writer codebase (localhost defaults, bare exceptions, cache None returns) |

---

## Sources

### Explainability & Attribution
- [ScienceDirect: Explainability pitfalls in XAI (2024, 100+ citations)](https://www.sciencedirect.com/science/article/pii/S2666389924000795)
- [Google Vertex AI: Overconfidence in neural networks](https://cloud.google.com/vertex-ai/docs/explainable-ai/overview)
- [MDPI: Enhancing robustness of AI text detectors (2025)](https://www.mdpi.com/2227-7390/13/13/2145)

### Adversarial Attacks & Detection Bypass
- [NEURIPS 2025: A Universal Attack for Humanizing AI-Generated Text](https://neurips.cc/virtual/2025/poster/116833)
- [ArXiv: Universal attack paper (June 2025)](https://arxiv.org/pdf/2506.07001)
- [USENIX Security 2025: GradEscape gradient-based evader](https://www.usenix.org/system/files/usenixsecurity25-meng.pdf)
- [EMNLP 2025: TempParaphraser evasion framework](https://aclanthology.org/2025.emnlp-main.1607.pdf)
- [ArXiv: Watermarking robustness review (April 2025)](https://arxiv.org/html/2504.03765v1)

### Stylometric Analysis & False Positives
- [ArXiv: Human-AI Collaboration challenges (May 2025)](https://arxiv.org/pdf/2505.08828)
- [CEUR-WS: Bootstrap distance imposters method (2024)](https://ceur-ws.org/Vol-3834/paper61.pdf)
- [INRIA: Breaking closed-world assumption (2014, 45 citations)](https://inria.hal.science/hal-01393771/document)
- [SSRN: Computational forensic authorship analysis](https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3396724_code1938430.pdf?abstractid=3396724&mirid=1)
- [ACL: Distance-based authorship verification (2019)](https://aclanthology.org/W19-5611.pdf)

### Batch Processing & Memory
- [DataAnnotation.tech: Queue implementations breaking in production (Nov 2025)](https://www.dataannotation.tech/developers/queue-implementations?)
- [CloverDX: Job queue troubleshooting](https://doc.cloverdx.com/latest/operations/job-queue.html)
- [GitHub: Langfuse memory leak issue (Sep 2025)](https://github.com/langfuse/langfuse/issues/9368)
- [Kai Waehner: Top 20 batch processing problems (April 2025)](https://www.kai-waehner.de/blog/2025/04/01/the-top-20-problems-with-batch-processing-and-how-to-fix-them-with-data-streaming/)

### Multi-model Ensembles & Calibration
- [BioRxiv: Calibrated ensembles reduce overfitting (2021)](https://www.biorxiv.org/content/10.1101/2021.07.26.453832.full)
- [Springer: Data drift with confidence calibration (2025)](https://link.springer.com/article/10.1007/s10845-025-02569-6)
- [ACM: Multi-class imbalanced data with concept drift (2024, 20 citations)](https://dl.acm.org/doi/full/10.1145/3689627)
- [ArXiv: Mutual transport calibration (2024)](https://arxiv.org/html/2405.19656)

### Contrastive Learning Pitfalls
- [ArXiv: Class separability pitfalls in contrastive learning (Aug 2024)](https://arxiv.org/html/2408.13068v1)
- [ACL Anthology: Label-supervised contrastive learning for imbalanced text (2024)](https://aclanthology.org/2024.wnut-1.6.pdf)
- [ScienceDirect: Contrastive text embeddings with sample mining (2025)](https://www.sciencedirect.com/science/article/pii/S259000562500205X)

### API Security & Rate Limiting
- [Zuplo: 10 best practices for API rate limiting in 2025 (Jan 2025)](https://zuplo.com/learning-center/10-best-practices-for-api-rate-limiting-in-2025)
- [Cloudflare: Rate limiting best practices (Nov 2025)](https://developers.cloudflare.com/waf/rate-limiting-rules/best-practices/)
- [GCore: API rate limiting guide (Nov 2025)](https://gcore.com/learning/api-rate-limiting)
- [OWASP API Security Project](https://owasp.org/www-project-api-security/)
- [Permit.io: API security comprehensive guide (Jan 2024)](https://www.permit.io/blog/api-security-a-comprehensive-guide-for-developers)

### Browser Extension Performance
- [Microsoft Edge: Content script performance best practices](https://learn.microsoft.com/en-us/microsoft-edge/extensions-chromium/developer-guide/performance)
- [Chrome Developer: Manifest V3 migration guide](https://developer.chrome.com/docs/extensions/mv3/intro/)
- [Web search findings: Content script injection delays, timing issues, security vulnerabilities](LOW CONFIDENCE - general web search results)

### Ollama Production Issues
- [GitHub: Ollama production deployment discussions](LOW CONFIDENCE - based on web search summaries)
- [vLLM documentation: High-throughput serving alternatives](LOW CONFIDENCE - mentioned in search results)

### Infrastructure & Codebase Observations
- [Ghost-Writer codebase: Direct observation of cache.py, rate_limit.py, feature_extraction.py](HIGH CONFIDENCE - actual code review)
- [Hardcoded localhost defaults observed in feature_extraction.py line 64](HIGH CONFIDENCE)
- [Bare exception handling observed in cache.py lines 39, 68, 83](HIGH CONFIDENCE)
- [Cache returns None on failure observed in cache.py lines 58-71](HIGH CONFIDENCE)

---

## Notes

**LOW confidence items:**
- Browser extension performance issues (based on general web search, limited official documentation)
- Ollama-specific GPU memory leaks (based on community reports, not official docs)

**MEDIUM confidence items:**
- Batch processing memory exhaustion (documented but general to job queues, not specific to AI detection)
- Contrastive learning false performance signals (academic research but limited production data)

**HIGH confidence items:**
- All adversarial attack research (peer-reviewed 2025 papers from top conferences)
- Explainability pitfalls (multiple academic sources + Google official documentation)
- Stylometric false positives (well-documented in authorship verification research)
- API security best practices (consensus across multiple authoritative sources)
- Infrastructure issues (directly observed in Ghost-Writer codebase)

**Research gaps:**
- Limited official Ollama production deployment documentation
- Browser extension performance best practices not well-documented for 2025
- Contrastive learning production deployment experiences scarce

**Recommended deeper research for specific phases:**
- Phase 2: Verify multi-model ensemble calibration methods with official documentation
- Phase 5: Research current browser extension performance benchmarks (2025)
- Phase 2: Investigate vLLM vs Ollama stability for production use cases
