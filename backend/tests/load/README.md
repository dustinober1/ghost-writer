# Load Testing with Locust

## Overview

This directory contains Locust load testing configurations for the Ghostwriter API.

## Prerequisites

Install Locust:
```bash
pip install locust
```

## Running Tests

### Interactive Mode (Web UI)

```bash
locust -f locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 to configure and run tests.

### Headless Mode

```bash
# 100 users, spawn rate 10/s, run for 60 seconds
locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s
```

## Test Scenarios

### GhostwriterUser

Simulates typical user behavior:
- Health checks (frequent)
- Text analysis (main task)
- Analytics retrieval
- Profile/fingerprint access

### HighLoadUser

Stress testing with rapid requests:
- Rapid health checks
- Rapid text analysis

## Performance Baseline

### Target Metrics

| Endpoint | Target P95 | Target RPS |
|----------|------------|------------|
| /health | < 50ms | 1000+ |
| /api/analysis/ | < 2000ms | 50+ |
| /api/auth/login | < 500ms | 100+ |

### Baseline Test Results

Run with: `locust -f locustfile.py --host=http://localhost:8000 --headless -u 50 -r 5 -t 60s`

Expected results (single server):
- Total RPS: ~100-200
- Median response time: ~100-300ms
- P95 response time: ~500-1000ms
- Error rate: < 1%

## Tips

1. Start with low user counts (10-20) and increase gradually
2. Monitor server CPU/memory during tests
3. Check database connection pool usage
4. Watch for rate limiting kicking in
5. Test with Redis enabled for caching benefits

## Integration with CI

Add to GitHub Actions:

```yaml
- name: Run Load Tests
  run: |
    pip install locust
    cd backend/tests/load
    locust -f locustfile.py --host=http://localhost:8000 --headless -u 20 -r 5 -t 30s --html=load_report.html
```
