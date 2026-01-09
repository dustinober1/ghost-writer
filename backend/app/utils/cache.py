"""
Redis caching utilities for Ghostwriter.
"""
import os
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import structlog

logger = structlog.get_logger()

# Redis client (lazy initialization)
_redis_client = None

REDIS_URL = os.getenv("REDIS_URL")
CACHE_TTL_FINGERPRINT = 3600  # 1 hour for fingerprints
CACHE_TTL_ANALYSIS = 1800  # 30 minutes for analysis results
CACHE_TTL_FEATURES = 600  # 10 minutes for feature extraction


def get_redis_client():
    """Get or create Redis client."""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    if not REDIS_URL:
        logger.debug("Redis URL not configured, caching disabled")
        return None
    
    try:
        import redis
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        _redis_client.ping()  # Test connection
        logger.info("Redis cache connected", url=REDIS_URL.split("@")[-1])
        return _redis_client
    except Exception as e:
        logger.warning("Failed to connect to Redis", error=str(e))
        return None


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a cache key from prefix and arguments."""
    key_data = f"{prefix}:{':'.join(str(a) for a in args)}"
    if kwargs:
        key_data += f":{json.dumps(kwargs, sort_keys=True)}"
    
    # Hash long keys
    if len(key_data) > 200:
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"
    
    return key_data


def get_cached(key: str) -> Optional[Any]:
    """Get value from cache."""
    redis = get_redis_client()
    if not redis:
        return None
    
    try:
        value = redis.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning("Cache get failed", key=key, error=str(e))
    
    return None


def set_cached(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set value in cache with TTL."""
    redis = get_redis_client()
    if not redis:
        return False
    
    try:
        redis.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.warning("Cache set failed", key=key, error=str(e))
        return False


def delete_cached(key: str) -> bool:
    """Delete value from cache."""
    redis = get_redis_client()
    if not redis:
        return False
    
    try:
        redis.delete(key)
        return True
    except Exception as e:
        logger.warning("Cache delete failed", key=key, error=str(e))
        return False


def delete_pattern(pattern: str) -> int:
    """Delete all keys matching pattern."""
    redis = get_redis_client()
    if not redis:
        return 0
    
    try:
        keys = redis.keys(pattern)
        if keys:
            return redis.delete(*keys)
    except Exception as e:
        logger.warning("Cache pattern delete failed", pattern=pattern, error=str(e))
    
    return 0


def cached(prefix: str, ttl: int = 3600):
    """
    Decorator for caching function results.
    
    Usage:
        @cached("fingerprint", ttl=3600)
        def get_fingerprint(user_id: int):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = get_cached(key)
            if cached_value is not None:
                logger.debug("Cache hit", key=key)
                return cached_value
            
            # Call function and cache result
            logger.debug("Cache miss", key=key)
            result = func(*args, **kwargs)
            
            if result is not None:
                set_cached(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Specialized cache functions for common operations

def cache_fingerprint(user_id: int, fingerprint_data: dict) -> bool:
    """Cache user fingerprint."""
    key = f"fingerprint:user:{user_id}"
    return set_cached(key, fingerprint_data, CACHE_TTL_FINGERPRINT)


def get_cached_fingerprint(user_id: int) -> Optional[dict]:
    """Get cached fingerprint for user."""
    key = f"fingerprint:user:{user_id}"
    return get_cached(key)


def invalidate_fingerprint(user_id: int) -> bool:
    """Invalidate cached fingerprint for user."""
    key = f"fingerprint:user:{user_id}"
    return delete_cached(key)


def cache_analysis_result(text_hash: str, result: dict, user_id: int = None) -> bool:
    """Cache analysis result."""
    key = f"analysis:{text_hash}"
    if user_id:
        key = f"analysis:user:{user_id}:{text_hash}"
    return set_cached(key, result, CACHE_TTL_ANALYSIS)


def get_cached_analysis(text_hash: str, user_id: int = None) -> Optional[dict]:
    """Get cached analysis result."""
    key = f"analysis:{text_hash}"
    if user_id:
        key = f"analysis:user:{user_id}:{text_hash}"
    return get_cached(key)


def cache_features(text_hash: str, features: dict) -> bool:
    """Cache extracted features."""
    key = f"features:{text_hash}"
    return set_cached(key, features, CACHE_TTL_FEATURES)


def get_cached_features(text_hash: str) -> Optional[dict]:
    """Get cached features."""
    key = f"features:{text_hash}"
    return get_cached(key)


def text_hash(text: str) -> str:
    """Generate hash for text content."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]
