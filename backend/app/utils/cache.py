"""Cache utilities.

Priority:
  1. Redis  — used when a Redis server is reachable.
  2. In-memory dict  — automatic fallback when Redis is absent/unreachable.
     ⚠  In-memory cache is per-process and has no TTL enforcement in the
     stdlib (entries are only pruned on the next *get* after expiry), so
     it is suitable for development / single-worker deployments only.

To enable Redis:
  pip install redis
  Set REDIS_URL in backend/.env  (default: redis://localhost:6379/0)
  Start the Redis server (docker run -p 6379:6379 redis, or via docker-compose)
"""

import json
import time
import logging
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


# ── In-memory fallback ────────────────────────────────────────────────────────

class _MemoryCache:
    """Thread-unsafe in-process dict cache — only for dev / single-worker use."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}   # key → (value, expires_at)

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at and time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        expires_at = time.monotonic() + expire if expire else 0.0
        self._store[key] = (value, expires_at)
        return True

    def delete(self, key: str) -> bool:
        self._store.pop(key, None)
        return True


# ── Main cache service ────────────────────────────────────────────────────────

class CacheService:
    """Redis cache with automatic in-memory fallback."""

    def __init__(self) -> None:
        self._redis = None
        self._mem   = _MemoryCache()
        self.enabled = False          # True = Redis is live
        self.backend = "memory"       # "redis" | "memory"

        try:
            import redis
            client = redis.from_url(
                settings.redis_url,
                socket_connect_timeout=2,
                socket_timeout=2,         # also cap individual operation time
            )
            client.ping()             # raises if server not available
            self._redis  = client
            self.enabled = True
            self.backend = "redis"
            logger.info("Cache backend: Redis (%s)", settings.redis_url)
        except ImportError:
            logger.info("Cache backend: memory (redis package not installed — pip install redis)")
        except Exception:
            # Deliberately suppressed: Redis is optional. No traceback in logs.
            logger.info(
                "Cache backend: memory (Redis unreachable at %s — "
                "install & start Redis to enable it)",
                settings.redis_url,
            )

    # ── public interface ───────────────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        if self._redis:
            try:
                raw = self._redis.get(key)
                return json.loads(raw) if raw else None
            except Exception:
                pass                  # fall through to memory
        return self._mem.get(key)

    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        if self._redis:
            try:
                self._redis.setex(key, expire, json.dumps(value, default=str))
                return True
            except Exception:
                pass
        return self._mem.set(key, value, expire)

    def delete(self, key: str) -> bool:
        if self._redis:
            try:
                self._redis.delete(key)
                return True
            except Exception:
                pass
        return self._mem.delete(key)


# Singleton used across the application
cache = CacheService()
