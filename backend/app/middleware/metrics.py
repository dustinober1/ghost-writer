"""
Prometheus metrics middleware for monitoring API performance.
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time

# HTTP request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Analysis metrics
analysis_requests_total = Counter(
    'analysis_requests_total',
    'Total analysis requests',
    ['granularity']
)

analysis_duration_seconds = Histogram(
    'analysis_duration_seconds',
    'Analysis duration in seconds',
    ['granularity'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

analysis_ai_probability = Histogram(
    'analysis_ai_probability',
    'Distribution of AI probability scores',
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Model metrics
model_predictions_total = Counter(
    'model_predictions_total',
    'Total model predictions',
    ['model_type']
)

# Queue depth (for Celery when implemented)
analysis_queue_depth = Gauge(
    'analysis_queue_depth',
    'Number of analysis jobs in queue'
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP request metrics"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Get endpoint path (remove query params)
        endpoint = request.url.path
        
        # Record metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        return response


def get_metrics_response():
    """Get Prometheus metrics as response"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
