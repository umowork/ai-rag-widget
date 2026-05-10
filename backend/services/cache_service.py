"""
Simple in-memory response cache with TTL.
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ResponseCache:
    """
    In-memory cache for LLM responses.
    Keys are hashed (query + context) pairs; values are cached with TTL.
    """

    def __init__(self, ttl_seconds: int = 300, max_size: int = 128):
        """
        Args:
            ttl_seconds: Time-to-live for cache entries (default 5 min).
            max_size: Maximum number of entries.
        """
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _make_key(self, query: str, context: str) -> str:
        """Generate a deterministic cache key."""
        raw = f"{query}:::{context}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, query: str, context: str) -> Optional[str]:
        """
        Retrieve cached response if available and not expired.

        Returns:
            Cached response string or None.
        """
        key = self._make_key(query, context)
        entry = self._cache.get(key)
        if entry is None:
            return None

        if time.time() - entry["ts"] > self._ttl:
            del self._cache[key]
            logger.debug("Cache expired for key=%s...", key[:8])
            return None

        logger.debug("Cache hit for key=%s...", key[:8])
        return entry["response"]

    def set(self, query: str, context: str, response: str) -> None:
        """
        Store a response in cache.

        Args:
            query: The user query.
            context: The context used.
            response: The generated response.
        """
        key = self._make_key(query, context)
        self._cache[key] = {"response": response, "ts": time.time()}

        # Evict oldest if over max_size
        if len(self._cache) > self._max_size:
            oldest_key = min(self._cache, key=lambda k: self._cache[k]["ts"])
            del self._cache[oldest_key]
            logger.debug("Evicted oldest cache entry: key=%s...", oldest_key[:8])

    def invalidate(self, query: str, context: str) -> None:
        """Remove a specific cache entry."""
        key = self._make_key(query, context)
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
        logger.debug("Cache cleared")

    @property
    def size(self) -> int:
        """Current number of cache entries."""
        return len(self._cache)
