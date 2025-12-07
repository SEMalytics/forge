"""
LRU caching for pattern access
"""

from functools import lru_cache
from typing import Dict, Any, Optional, Callable
import time


class PatternCache:
    """LRU cache for frequently accessed patterns"""

    def __init__(self, maxsize: int = 128):
        """
        Initialize pattern cache

        Args:
            maxsize: Maximum number of items to cache
        """
        self.maxsize = maxsize
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if key in self.cache:
            self.hit_count += 1
            self.access_times[key] = time.time()
            return self.cache[key]

        self.miss_count += 1
        return None

    def set(self, key: str, value: Any):
        """
        Set item in cache

        Args:
            key: Cache key
            value: Value to cache
        """
        # Evict oldest if cache is full
        if len(self.cache) >= self.maxsize and key not in self.cache:
            oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            del self.cache[oldest_key]
            del self.access_times[oldest_key]

        self.cache[key] = value
        self.access_times[key] = time.time()

    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.access_times.clear()
        self.hit_count = 0
        self.miss_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0

        return {
            'size': len(self.cache),
            'maxsize': self.maxsize,
            'hits': self.hit_count,
            'misses': self.miss_count,
            'hit_rate': hit_rate
        }


def cached_pattern_search(maxsize: int = 128) -> Callable:
    """
    Decorator for caching pattern search results

    Args:
        maxsize: Maximum cache size

    Returns:
        Decorator function
    """
    return lru_cache(maxsize=maxsize)
