"""
Search engine combining FTS5 and semantic search
"""

from typing import List, Dict, Optional
from forge.knowledgeforge.pattern_store import PatternStore
from forge.knowledgeforge.cache import PatternCache
from forge.utils.logger import logger


class SearchEngine:
    """Unified search interface for KnowledgeForge patterns"""

    def __init__(
        self,
        pattern_store: PatternStore,
        cache_size: int = 128,
        default_method: str = 'hybrid'
    ):
        """
        Initialize search engine

        Args:
            pattern_store: Pattern store instance
            cache_size: Size of search result cache
            default_method: Default search method ('keyword', 'semantic', 'hybrid')
        """
        self.pattern_store = pattern_store
        self.cache = PatternCache(maxsize=cache_size)
        self.default_method = default_method

    def search(
        self,
        query: str,
        max_results: int = 10,
        method: Optional[str] = None
    ) -> List[Dict]:
        """
        Search patterns with caching

        Args:
            query: Search query
            max_results: Maximum results to return
            method: Search method (keyword, semantic, hybrid)

        Returns:
            List of matching patterns
        """
        method = method or self.default_method
        cache_key = f"{query}:{max_results}:{method}"

        # Check cache first
        cached_results = self.cache.get(cache_key)
        if cached_results is not None:
            logger.debug(f"Cache hit for query: {query}")
            return cached_results

        # Perform search
        logger.debug(f"Cache miss for query: {query}, searching...")
        results = self.pattern_store.search(query, max_results, method)

        # Cache results
        self.cache.set(cache_key, results)

        return results

    def search_by_topic(self, topic: str, max_results: int = 10) -> List[Dict]:
        """
        Search patterns by topic

        Args:
            topic: Topic to search for
            max_results: Maximum results to return

        Returns:
            List of matching patterns
        """
        return self.search(f"topic:{topic}", max_results, method='keyword')

    def search_by_module(self, module: str, max_results: int = 10) -> List[Dict]:
        """
        Search patterns by module

        Args:
            module: Module to search for
            max_results: Maximum results to return

        Returns:
            List of matching patterns
        """
        return self.search(f"module:{module}", max_results, method='keyword')

    def get_related_patterns(self, pattern_filename: str, max_results: int = 5) -> List[Dict]:
        """
        Get patterns related to a given pattern

        Args:
            pattern_filename: Filename of the reference pattern
            max_results: Maximum results to return

        Returns:
            List of related patterns
        """
        pattern = self.pattern_store.get_pattern_by_filename(pattern_filename)
        if not pattern:
            return []

        # Use pattern content for semantic search
        return self.search(pattern['content'][:500], max_results, method='semantic')

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        return self.cache.get_stats()

    def clear_cache(self):
        """Clear search result cache"""
        self.cache.clear()
        logger.info("Search cache cleared")
