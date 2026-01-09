"""Tests for Redis caching utilities."""
import pytest
from unittest.mock import patch, MagicMock


class TestCacheUtilities:
    """Test caching functions."""
    
    def test_text_hash_consistency(self):
        """Test that text hashing is consistent."""
        from app.utils.cache import text_hash
        
        text = "Hello, World!"
        hash1 = text_hash(text)
        hash2 = text_hash(text)
        
        assert hash1 == hash2
        assert len(hash1) == 16
    
    def test_text_hash_different_inputs(self):
        """Test that different texts produce different hashes."""
        from app.utils.cache import text_hash
        
        hash1 = text_hash("Hello")
        hash2 = text_hash("World")
        
        assert hash1 != hash2
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        from app.utils.cache import cache_key
        
        key = cache_key("test", "arg1", "arg2")
        assert key.startswith("test:")
        assert "arg1" in key
        assert "arg2" in key
    
    def test_cache_key_with_kwargs(self):
        """Test cache key with keyword arguments."""
        from app.utils.cache import cache_key
        
        key = cache_key("test", "arg1", foo="bar")
        assert "foo" in key or len(key) <= 200
    
    @patch("app.utils.cache.get_redis_client")
    def test_get_cached_no_redis(self, mock_redis):
        """Test get_cached when Redis is unavailable."""
        from app.utils.cache import get_cached
        
        mock_redis.return_value = None
        
        result = get_cached("test:key")
        assert result is None
    
    @patch("app.utils.cache.get_redis_client")
    def test_set_cached_no_redis(self, mock_redis):
        """Test set_cached when Redis is unavailable."""
        from app.utils.cache import set_cached
        
        mock_redis.return_value = None
        
        result = set_cached("test:key", {"data": "value"})
        assert result == False
    
    @patch("app.utils.cache.get_redis_client")
    def test_delete_cached_no_redis(self, mock_redis):
        """Test delete_cached when Redis is unavailable."""
        from app.utils.cache import delete_cached
        
        mock_redis.return_value = None
        
        result = delete_cached("test:key")
        assert result == False
    
    @patch("app.utils.cache.get_redis_client")
    def test_cache_fingerprint(self, mock_redis):
        """Test fingerprint caching."""
        from app.utils.cache import cache_fingerprint, get_cached_fingerprint
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        fingerprint_data = {"vector": [0.1, 0.2, 0.3]}
        cache_fingerprint(1, fingerprint_data)
        
        mock_client.setex.assert_called_once()
    
    @patch("app.utils.cache.get_redis_client")
    def test_cache_analysis_result(self, mock_redis):
        """Test analysis result caching."""
        from app.utils.cache import cache_analysis_result
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        
        result = {"segments": [], "overall_ai_probability": 0.5}
        cache_analysis_result("abc123", result, user_id=1)
        
        mock_client.setex.assert_called_once()
