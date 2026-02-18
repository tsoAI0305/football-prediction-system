"""Redis cache utilities."""
import json
from typing import Optional, Any
from app.config import settings


class CacheService:
    """Redis cache service for caching API responses."""
    
    def __init__(self):
        """Initialize cache service."""
        self.enabled = False
        self.client = None
        
        # Try to initialize Redis connection
        try:
            import redis
            self.client = redis.from_url(settings.REDIS_URL)
            self.client.ping()
            self.enabled = True
        except Exception as e:
            print(f"Redis not available: {e}")
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds (default: 5 minutes)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            self.client.setex(
                key,
                expire,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False


# Global cache instance
cache = CacheService()
