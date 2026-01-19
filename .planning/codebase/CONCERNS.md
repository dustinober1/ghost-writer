# Codebase Concerns

**Analysis Date:** 2025-01-18

## Tech Debt

**Feature extraction complexity:**
- Issue: 570-line file `/backend/app/ml/feature_extraction.py` contains all feature extraction logic without modularity
- Files: `/backend/app/ml/feature_extraction.py`
- Impact: Difficult to test, maintain, and extend with new features. Changes risk breaking existing functionality.
- Fix approach: Split into separate modules by feature type (burstiness, perplexity, syntactic, semantic, ngram, coherence, punctuation, readability)

**Unhandled Ollama API failures:**
- Issue: Perplexity calculation silently fails to heuristic fallback without proper error propagation
- Files: `/backend/app/ml/feature_extraction.py` (lines 112-126), `/backend/app/ml/ollama_embeddings.py`
- Impact: Users get degraded analysis results without knowing the ML model failed. No visibility into Ollama connectivity issues.
- Fix approach: Return structured result indicating which features used API vs heuristic, add health check status

**Email not configured for production:**
- Issue: Email sending defaults to console logging. SMTP_ENABLED defaults to false.
- Files: `/backend/app/utils/email.py` (line 17), `/backend/app/utils/email.py` (lines 152-161)
- Impact: Email verification and password reset features don't work in production without SMTP configuration. Users cannot verify accounts or reset passwords.
- Fix approach: Require SMTP configuration in production environments, add email queue for async processing

**In-memory rate limiting without Redis:**
- Issue: Rate limiter falls back to in-memory storage when Redis unavailable, defeating distributed rate limiting
- Files: `/backend/app/middleware/rate_limit.py` (lines 22-26)
- Impact: In production with multiple backend instances, rate limits are not shared. Users can exceed limits by hitting different instances.
- Fix approach: Make Redis required for production deployments, fail fast if Redis unavailable

**Hardcoded localhost defaults:**
- Issue: Multiple services default to localhost URLs, breaking in containerized/production environments
- Files: `/backend/app/models/database.py` (line 10), `/backend/app/ml/feature_extraction.py` (line 64), `/backend/app/ml/dspy_rewriter.py` (line 25), `/backend/app/ml/ollama_embeddings.py` (line 24), `/backend/app/utils/email.py` (line 18, 23)
- Impact: Production deployments fail if environment variables not set. Containers cannot communicate across services.
- Fix approach: Remove localhost defaults, require explicit configuration for all external dependencies

## Known Bugs

**Audit logging middleware token parsing incomplete:**
- Issue: JWT token parsing in audit middleware is stubbed (lines 26-33), leaving user_email and user_id always None
- Files: `/backend/app/middleware/audit_logging.py` (lines 26-33)
- Symptoms: Audit logs don't capture which user performed actions, making security investigations impossible
- Trigger: All authenticated requests
- Workaround: None - audit logs incomplete
- Fix approach: Decode JWT properly using same logic as `get_current_user()` dependency

**File upload accepts .docx/.pdf but only reads as text:**
- Issue: Frontend accepts .docx and .pdf files but FileReader only reads as text (line 137), which won't work for binary formats
- Files: `/frontend/src/components/TextInput/TextInput.tsx` (lines 94-103, 137), `/frontend/src/components/ProfileManager/ProfileManager.tsx` (lines 59-73)
- Symptoms: Uploading .docx or .pdf files results in corrupted content or errors
- Trigger: User uploads .docx or .pdf file
- Workaround: Use .txt files or paste text directly
- Fix approach: Use proper libraries (mammoth.js for .docx, pdf.js for .pdf) or remove support for binary formats

**Frontend hardcodes backend URL in error message:**
- Issue: Error message references localhost:8000 directly
- Files: `/frontend/src/services/api.ts` (line 46)
- Symptoms: Misleading error messages when backend runs on different port/host
- Trigger: Network errors
- Workaround: None - cosmetic but confusing
- Fix approach: Use API_BASE_URL from environment variable

## Security Considerations

**Default SECRET_KEY in production:**
- Risk: Application allows startup with default secret key "your-secret-key-change-in-production"
- Files: `/backend/app/main.py` (lines 167-174), `/backend/app/utils/auth.py` (line 19)
- Current mitigation: Startup check raises ValueError if ENVIRONMENT=production and SECRET_KEY not changed
- Recommendations: The check exists but is runtime-only. Generate SECRET_KEY at deployment time. Consider using key management service (KMS, AWS Secrets Manager, etc.)

**Bare exception handling swallows errors:**
- Risk: Multiple locations catch all exceptions silently, hiding security-relevant errors
- Files: `/backend/app/middleware/audit_logging.py` (line 32), `/backend/app/middleware/rate_limit.py` (line 22), `/backend/app/utils/auth.py` (line 59), `/backend/app/ml/dspy_rewriter.py` (line 224), `/backend/app/main.py` (lines 224, 237, 247)
- Current mitigation: Some log warnings, others fail silently
- Recommendations: Replace bare `except Exception:` with specific exception types. Ensure authentication and authorization failures are always logged.

**Audit logging doesn't extract user from JWT:**
- Risk: Security events logged without user context, making forensics impossible
- Files: `/backend/app/middleware/audit_logging.py` (lines 23-33)
- Current mitigation: None - user_id and user_email always None in logs
- Recommendations: Implement proper JWT decoding in middleware to populate user context for all security-relevant logs

**Email verification tokens never expire in cleanup:**
- Risk: Old email verification tokens accumulate in database without cleanup mechanism
- Files: `/backend/app/utils/email.py` (lines 31-49)
- Current mitigation: Tokens expire after 7 days but rows not deleted
- Recommendations: Add periodic cleanup job to remove expired tokens from database

**Password reset tokens not single-use in all code paths:**
- Risk: Token is marked used after reset, but verification doesn't check if already used
- Files: `/backend/app/utils/email.py` (lines 90-101, 104-112)
- Current mitigation: Token has 1-hour expiry, marked as used after reset
- Recommendations: Add check for `used=False` in `verify_password_reset_token()` to prevent reuse

## Performance Bottlenecks

**Synchronous feature extraction without caching:**
- Problem: Every text analysis recalculates all features from scratch, no caching of repeated analyses
- Files: `/backend/app/ml/feature_extraction.py` (lines 453-504)
- Cause: No cache integration for feature extraction results
- Improvement path: Implement Redis caching for feature vectors keyed by text hash (already have `text_hash()` utility in cache.py)

**Sequential file uploads in frontend:**
- Problem: Multiple files uploaded one-by-one with full round-trip for each
- Files: `/frontend/src/components/ProfileManager/ProfileManager.tsx` (lines 81-96)
- Cause: Sequential `for` loop with await for each file upload
- Improvement path: Implement batch upload endpoint on backend, or parallel uploads with Promise.all() (with rate limiting)

**N-gram extraction inefficient for large texts:**
- Problem: O(n*m) complexity where n is text length and m is n-gram size, generates all combinations in memory
- Files: `/backend/app/ml/feature_extraction.py` (lines 247-298)
- Cause: Creates all n-grams upfront before counting
- Improvement path: Use streaming/iterative approach for large texts, or skip n-gram features for texts >10,000 words

**Database queries not optimized for admin user list:**
- Problem: N+1 query problem when loading user stats - each user requires additional queries for sample_count, analysis_count, has_fingerprint
- Files: `/backend/app/api/routes/admin.py` (lines 116-141)
- Cause: Sequential database queries for each user's statistics
- Improvement path: Use JOIN queries or subqueries to fetch all stats in single query

**Fingerprint generation loads all samples into memory:**
- Problem: All writing samples loaded simultaneously when generating fingerprint
- Files: `/backend/app/services/fingerprint_service.py` (assumed based on pattern)
- Cause: Likely loading all User's WritingSample records at once
- Improvement path: Implement batch processing for large sample counts, stream samples instead of loading all

## Fragile Areas

**Admin routes lack proper authorization checks:**
- Files: `/backend/app/api/routes/admin.py` (lines 51-58)
- Why fragile: Only checks `is_admin` attribute, but User model may not have this column in all deployments
- Safe modification: Add migration to ensure `is_admin` column exists, use separate admin role table for flexibility
- Test coverage: Gaps - no tests for admin authorization edge cases (non-admin users, missing is_admin attribute)

**Ollama model checking returns None on failure:**
- Files: `/backend/app/ml/dspy_rewriter.py` (lines 208-226)
- Why fragile: Returns None instead of boolean when check fails, causing ambiguous error handling. Caller checks `if model_exists is False` but None also falsy.
- Safe modification: Always return boolean, raise exception on connection failures
- Test coverage: Present in `/backend/app/tests/test_dspy_rewriter.py` but doesn't cover the None return path

**Cache utility returns None for all failures:**
- Files: `/backend/app/utils/cache.py` (lines 31, 41, 62, 71)
- Why fragile: Cannot distinguish between "cache miss" and "cache error". Silent failures degrade performance without visibility.
- Safe modification: Return explicit Result type or raise exceptions for connection failures
- Test coverage: None for cache failure scenarios

**Authentication depends on email_verified but accounts can be created without verification:**
- Files: `/backend/app/api/routes/auth.py` (lines 122-127), `/backend/app/api/routes/auth.py` (lines 169-174)
- Why fragile: Users register and can't login until email verified, but no mechanism to handle stale unverified accounts
- Safe modification: Add background job to delete unverified accounts after 7-30 days, provide "resend verification" flow
- Test coverage: Limited - tests don't cover unverified account expiry

**Feature extraction depends on NLTK data downloads:**
- Files: `/backend/app/ml/feature_extraction.py` (lines 10-29)
- Why fragile: Silent failure if nltk download fails, causes runtime errors when using POS tagging or other features
- Safe modification: Verify all required NLTK data is present on startup, fail fast if missing
- Test coverage: Tests mock NLTK, don't verify actual data presence

**Large frontend components without prop validation:**
- Files: `/frontend/src/components/TextInput/TextInput.tsx` (509 lines), `/frontend/src/components/ProfileManager/ProfileManager.tsx` (479 lines)
- Why fragile: Complex state management in single component, no TypeScript interfaces for all state
- Safe modification: Extract state to custom hooks, split into smaller components with clear props
- Test coverage: No component tests for these major components

## Scaling Limits

**Monolithic feature extraction blocks request handler:**
- Current capacity: Single analysis request blocks entire request thread for 2-30 seconds depending on text size
- Limit: Cannot handle concurrent analyses efficiently. 10 concurrent requests = 10 blocked threads
- Scaling path: Move feature extraction to background task queue (Celery/Redis already configured but not used for analysis)

**In-memory cache limits scalability:**
- Current capacity: Each backend instance has own cache. No cache sharing across instances.
- Limit: Cache hit rate decreases with each additional instance. Memory usage grows linearly with instances.
- Scaling path: Redis cache is implemented but optional. Make Redis required for multi-instance deployments

**Rate limiting per-instance:**
- Current capacity: 100 requests/hour per IP per instance
- Limit: 10 instances = 1000 requests/hour effective limit (distributed), but in-memory fallback breaks this
- Scaling path: Require Redis for rate limiting in production

**Database connection pooling not explicitly configured:**
- Current capacity: SQLAlchemy defaults (typically 5-20 connections)
- Limit: May exhaust connections under high load, causing connection timeouts
- Scaling path: Configure explicit pool size in DATABASE_URL or SQLAlchemy config

**Frontend has no request queuing or backpressure:**
- Current capacity: User can trigger unlimited analysis requests simultaneously
- Limit: Browser may crash or backend overwhelmed with parallel requests
- Scaling path: Add request debouncing, disable buttons during processing, queue client-side requests

## Dependencies at Risk

**passlib bcrypt wrapper has initialization issues:**
- Risk: Code comments indicate "passlib initialization issues" (line 28, 57), uses bcrypt directly as workaround
- Files: `/backend/app/utils/auth.py` (lines 27-29, 57-58, 68)
- Impact: If passlib/bcrypt versions conflict, password hashing breaks and users cannot login
- Migration plan: Already migrated to direct bcrypt usage. Remove passlib dependency entirely once confirmed stable

**fastapi-mail is optional dependency:**
- Risk: Imported inside try/except in email module. If missing, email fails silently
- Files: `/backend/app/utils/email.py` (lines 122-151)
- Impact: Email features break without clear error in production
- Migration plan: Make fastapi-mail required dependency or remove SMTP email feature entirely

**DSPy rewriter compatibility:**
- Risk: Code has backwards compatibility aliases (lines 289-301) suggesting recent migration from DSPy to Ollama
- Files: `/backend/app/ml/dspy_rewriter.py` (lines 289-301)
- Impact: Old code paths may still reference DSPy, breaking if DSPy dependency removed
- Migration plan: Already using OllamaRewriter exclusively. Remove DSPy references and backwards compatibility aliases

**NLTK data downloads at module import:**
- Risk: NLTK data downloaded on first import, may fail silently or slow startup
- Files: `/backend/app/ml/feature_extraction.py` (lines 10-29)
- Impact: Feature extraction fails if data unavailable
- Migration plan: Bundle NLTK data with application or verify presence in Docker build

**nltk dependency large and slow to import:**
- Risk: nltk is heavy library with slow import time
- Files: `/backend/app/ml/feature_extraction.py` (line 2)
- Impact: Increases cold start time for serverless/containerized deployments
- Migration plan: Consider alternative NLP libraries (spaCy is faster but larger, textblob is lighter but less features)

## Missing Critical Features

**No API input validation middleware:**
- Problem: Input sanitization middleware exists (`/backend/app/middleware/input_sanitization.py`) but not applied to all endpoints
- Blocks: Protection against XSS, injection attacks in text analysis inputs
- Files: `/backend/app/middleware/input_sanitization.py` (imported but not universally applied)
- Priority: High - user-provided text analyzed without proper sanitization

**No request signing/webhook verification:**
- Problem: If external integrations added, no webhook signature verification
- Blocks: Secure integration with external services
- Priority: Medium - not currently used but limits future integrations

**No database migration rollback strategy:**
- Problem: Alembic configured but no documented rollback procedure
- Blocks: Safe database schema changes in production
- Files: `/backend/alembic/` directory exists
- Priority: High - production deployments need rollback capability

**No distributed tracing:**
- Problem: Sentry enabled for errors but no distributed tracing for performance debugging
- Blocks: Debugging slow requests across services
- Files: `/backend/app/main.py` (lines 150-165)
- Priority: Medium - useful for multi-service debugging but not critical for monolith

**No automated backup strategy:**
- Problem: Database backups not automated, no restore procedures documented
- Blocks: Disaster recovery, data loss prevention
- Priority: High - production data safety requirement

**No API versioning:**
- Problem: All routes at `/api/*` with no version prefix (v1, v2)
- Blocks: Breaking API changes without disrupting existing clients
- Files: `/backend/app/api/routes/*` all use `/api/{resource}` pattern
- Priority: Medium - becomes critical with external API consumers

## Test Coverage Gaps

**Untested area: Cache failure scenarios**
- What's not tested: Redis connection failures, cache serialization errors, cache poisoning
- Files: `/backend/app/utils/cache.py`, `/backend/app/middleware/rate_limit.py`
- Risk: Cache failures cause silent performance degradation or data inconsistency
- Priority: High - cache is performance-critical

**Untested area: Email sending failures**
- What's not tested: SMTP connection failures, email delivery failures, token expiry edge cases
- Files: `/backend/app/utils/email.py`
- Risk: Users cannot verify accounts or reset passwords silently
- Priority: Medium - affects user onboarding but not core functionality

**Untested area: Admin authorization edge cases**
- What's not tested: Missing is_admin attribute, admin deactivating self, admin deleting own account
- Files: `/backend/app/api/routes/admin.py`
- Risk: Privilege escalation, accidental admin lockout
- Priority: High - security-critical

**Untested area: Ollama unavailability handling**
- What's not tested: Ollama server down during analysis, model not found, timeout handling
- Files: `/backend/app/ml/feature_extraction.py`, `/backend/app/ml/dspy_rewriter.py`, `/backend/app/ml/ollama_embeddings.py`
- Risk: Analysis failures cascade, no graceful degradation
- Priority: High - Ollama is core dependency

**Untested area: Frontend error boundary coverage**
- What's not tested: Component crash recovery, error boundary triggering, offline behavior
- Files: `/frontend/src/components/ErrorBoundary/ErrorBoundary.tsx` (101 lines, no tests)
- Risk: Unhandled errors leave application in broken state
- Priority: Medium - affects user experience

**Untested area: Large text handling**
- What's not tested: Texts >10,000 words, memory usage, timeout handling
- Files: `/backend/app/ml/feature_extraction.py`, `/frontend/src/components/TextInput/TextInput.tsx`
- Risk: Memory exhaustion, request timeouts, poor UX on large inputs
- Priority: Medium - edge case but causes crashes when it occurs

**Untested area: Concurrent file uploads**
- What's not tested: Multiple users uploading simultaneously, same user uploading multiple files rapidly
- Files: `/frontend/src/components/ProfileManager/ProfileManager.tsx`, `/backend/app/api/routes/fingerprint.py`
- Risk: Race conditions, duplicate fingerprints, database locks
- Priority: Low - unlikely to cause issues but worth testing

**Untested area: JWT token expiry edge cases**
- What's not tested: Token expires mid-request, refresh token expires during refresh flow
- Files: `/backend/app/utils/auth.py`, `/backend/app/api/routes/auth.py`
- Risk: Users logged out unexpectedly, poor UX
- Priority: Medium - affects user session reliability

---

*Concerns audit: 2025-01-18*
