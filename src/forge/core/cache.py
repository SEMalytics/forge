"""
Caching & Incremental Builds for Forge

Provides intelligent caching to avoid regenerating unchanged code
and enable incremental builds for faster iteration.

Features:
- Content-based caching (hash specifications + dependencies)
- Cache invalidation based on dependency changes
- Incremental generation (only regenerate what changed)
- Persistent disk cache with TTL
- Cache statistics and management
"""

import hashlib
import json
import time
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from enum import Enum

from forge.utils.logger import logger


class CacheError(Exception):
    """Errors related to caching operations"""
    pass


class CacheStatus(Enum):
    """Status of a cache lookup"""
    HIT = "hit"
    MISS = "miss"
    STALE = "stale"
    INVALID = "invalid"


@dataclass
class CacheEntry:
    """
    A single cache entry storing generation results.

    Attributes:
        key: Unique cache key (content hash)
        task_id: Original task identifier
        content_hash: Hash of input content
        dependency_hash: Hash of dependencies
        files: Generated files (path -> content)
        created_at: When entry was created
        accessed_at: Last access time
        ttl_seconds: Time-to-live in seconds
        metadata: Additional metadata
    """
    key: str
    task_id: str
    content_hash: str
    dependency_hash: str
    files: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ttl_seconds: int = 86400 * 7  # 7 days default
    hit_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        created = datetime.fromisoformat(self.created_at)
        expires = created + timedelta(seconds=self.ttl_seconds)
        return datetime.now() >= expires

    @property
    def age_seconds(self) -> float:
        """Get age of entry in seconds"""
        created = datetime.fromisoformat(self.created_at)
        return (datetime.now() - created).total_seconds()

    def touch(self) -> None:
        """Update access time"""
        self.accessed_at = datetime.now().isoformat()
        self.hit_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "key": self.key,
            "task_id": self.task_id,
            "content_hash": self.content_hash,
            "dependency_hash": self.dependency_hash,
            "files": self.files,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "ttl_seconds": self.ttl_seconds,
            "hit_count": self.hit_count,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary"""
        return cls(
            key=data["key"],
            task_id=data["task_id"],
            content_hash=data["content_hash"],
            dependency_hash=data["dependency_hash"],
            files=data.get("files", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            accessed_at=data.get("accessed_at", datetime.now().isoformat()),
            ttl_seconds=data.get("ttl_seconds", 86400 * 7),
            hit_count=data.get("hit_count", 0),
            metadata=data.get("metadata", {})
        )


@dataclass
class CacheLookupResult:
    """Result of a cache lookup"""
    status: CacheStatus
    entry: Optional[CacheEntry] = None
    reason: Optional[str] = None

    @property
    def is_hit(self) -> bool:
        """Check if lookup was a hit"""
        return self.status == CacheStatus.HIT


class CacheKeyBuilder:
    """
    Builds cache keys from generation context.

    Uses content hashing to create deterministic keys based on:
    - Task specification
    - Project context
    - Dependencies
    - Tech stack
    - KnowledgeForge patterns
    """

    @staticmethod
    def hash_content(content: str) -> str:
        """Create SHA256 hash of content"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    def hash_list(items: List[str]) -> str:
        """Create hash of sorted list items"""
        sorted_items = sorted(items)
        combined = "|".join(sorted_items)
        return CacheKeyBuilder.hash_content(combined)

    @staticmethod
    def hash_dict(data: Dict[str, str]) -> str:
        """Create hash of dictionary"""
        sorted_items = sorted(data.items())
        combined = "|".join(f"{k}:{v}" for k, v in sorted_items)
        return CacheKeyBuilder.hash_content(combined)

    @classmethod
    def build_key(
        cls,
        task_id: str,
        specification: str,
        project_context: str,
        tech_stack: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        patterns: Optional[List[str]] = None,
        file_structure: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Build a cache key from generation inputs.

        Args:
            task_id: Task identifier
            specification: Task specification
            project_context: Project context
            tech_stack: Technology stack
            dependencies: Task dependencies
            patterns: KnowledgeForge patterns
            file_structure: Existing file structure

        Returns:
            Deterministic cache key
        """
        parts = [
            cls.hash_content(specification),
            cls.hash_content(project_context),
        ]

        if tech_stack:
            parts.append(cls.hash_list(tech_stack))

        if dependencies:
            parts.append(cls.hash_list(dependencies))

        if patterns:
            parts.append(cls.hash_list(patterns))

        if file_structure:
            parts.append(cls.hash_dict(file_structure))

        combined = "-".join(parts)
        return f"{task_id[:20]}-{cls.hash_content(combined)}"

    @classmethod
    def build_dependency_hash(
        cls,
        dependencies: List[str],
        dependency_results: Dict[str, Dict[str, str]]
    ) -> str:
        """
        Build hash of dependency outputs.

        Used to invalidate cache when dependencies change.

        Args:
            dependencies: List of dependency task IDs
            dependency_results: Results from dependency tasks

        Returns:
            Hash of dependency outputs
        """
        parts = []

        for dep_id in sorted(dependencies):
            if dep_id in dependency_results:
                files = dependency_results[dep_id]
                file_hash = cls.hash_dict(files)
                parts.append(f"{dep_id}:{file_hash}")

        return cls.hash_content("|".join(parts))


class GenerationCache:
    """
    Persistent cache for code generation results.

    Stores generated files on disk with metadata for fast retrieval
    and intelligent invalidation.
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_entries: int = 1000,
        default_ttl: int = 86400 * 7,  # 7 days
        max_size_mb: int = 500
    ):
        """
        Initialize generation cache.

        Args:
            cache_dir: Directory for cache storage
            max_entries: Maximum number of cache entries
            default_ttl: Default TTL in seconds
            max_size_mb: Maximum cache size in MB
        """
        self.cache_dir = cache_dir or Path(".forge/cache/generation")
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.max_size_mb = max_size_mb

        # In-memory index for fast lookups
        self._index: Dict[str, CacheEntry] = {}
        self._dirty = False

        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "stale": 0,
            "evictions": 0,
            "invalidations": 0
        }

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load index
        self._load_index()

    def _index_path(self) -> Path:
        """Get path to index file"""
        return self.cache_dir / "index.json"

    def _entry_path(self, key: str) -> Path:
        """Get path to entry directory"""
        return self.cache_dir / "entries" / key

    def _load_index(self) -> None:
        """Load cache index from disk"""
        index_path = self._index_path()

        if index_path.exists():
            try:
                data = json.loads(index_path.read_text())
                for key, entry_data in data.get("entries", {}).items():
                    self._index[key] = CacheEntry.from_dict(entry_data)

                self._stats = data.get("stats", self._stats)
                logger.debug(f"Loaded cache index with {len(self._index)} entries")

            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                self._index = {}

    def _save_index(self) -> None:
        """Save cache index to disk"""
        if not self._dirty:
            return

        try:
            data = {
                "entries": {k: v.to_dict() for k, v in self._index.items()},
                "stats": self._stats,
                "saved_at": datetime.now().isoformat()
            }

            self._index_path().write_text(json.dumps(data, indent=2))
            self._dirty = False

        except Exception as e:
            logger.warning(f"Failed to save cache index: {e}")

    def get(
        self,
        key: str,
        dependency_hash: Optional[str] = None
    ) -> CacheLookupResult:
        """
        Look up entry in cache.

        Args:
            key: Cache key
            dependency_hash: Expected dependency hash for validation

        Returns:
            CacheLookupResult with status and entry
        """
        if key not in self._index:
            self._stats["misses"] += 1
            return CacheLookupResult(
                status=CacheStatus.MISS,
                reason="Key not found"
            )

        entry = self._index[key]

        # Check expiration
        if entry.is_expired:
            self._stats["stale"] += 1
            return CacheLookupResult(
                status=CacheStatus.STALE,
                entry=entry,
                reason=f"Entry expired (age: {entry.age_seconds:.0f}s)"
            )

        # Check dependency hash if provided
        if dependency_hash and entry.dependency_hash != dependency_hash:
            self._stats["invalidations"] += 1
            return CacheLookupResult(
                status=CacheStatus.INVALID,
                entry=entry,
                reason="Dependencies changed"
            )

        # Verify files exist on disk
        entry_dir = self._entry_path(key)
        if not entry_dir.exists():
            self._stats["misses"] += 1
            del self._index[key]
            self._dirty = True
            return CacheLookupResult(
                status=CacheStatus.MISS,
                reason="Entry files missing"
            )

        # Cache hit!
        entry.touch()
        self._stats["hits"] += 1
        self._dirty = True

        return CacheLookupResult(
            status=CacheStatus.HIT,
            entry=entry
        )

    def put(
        self,
        key: str,
        task_id: str,
        content_hash: str,
        dependency_hash: str,
        files: Dict[str, str],
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CacheEntry:
        """
        Store entry in cache.

        Args:
            key: Cache key
            task_id: Task identifier
            content_hash: Hash of input content
            dependency_hash: Hash of dependencies
            files: Generated files to cache
            ttl_seconds: TTL override
            metadata: Additional metadata

        Returns:
            Created cache entry
        """
        # Check capacity
        if len(self._index) >= self.max_entries:
            self._evict_oldest()

        # Create entry
        entry = CacheEntry(
            key=key,
            task_id=task_id,
            content_hash=content_hash,
            dependency_hash=dependency_hash,
            files=files,
            ttl_seconds=ttl_seconds if ttl_seconds is not None else self.default_ttl,
            metadata=metadata or {}
        )

        # Store files on disk
        entry_dir = self._entry_path(key)
        entry_dir.mkdir(parents=True, exist_ok=True)

        for filepath, content in files.items():
            # Sanitize path
            safe_path = filepath.replace("..", "_").lstrip("/")
            file_path = entry_dir / safe_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        # Update index
        self._index[key] = entry
        self._dirty = True
        self._save_index()

        logger.debug(f"Cached {len(files)} files for {task_id} (key: {key[:12]}...)")
        return entry

    def load_files(self, key: str) -> Dict[str, str]:
        """
        Load cached files from disk.

        Args:
            key: Cache key

        Returns:
            Dictionary of file paths to content
        """
        entry_dir = self._entry_path(key)
        files = {}

        if not entry_dir.exists():
            return files

        for filepath in entry_dir.rglob("*"):
            if filepath.is_file():
                rel_path = filepath.relative_to(entry_dir)
                try:
                    files[str(rel_path)] = filepath.read_text()
                except Exception as e:
                    logger.warning(f"Failed to read cached file {filepath}: {e}")

        return files

    def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was invalidated
        """
        if key not in self._index:
            return False

        del self._index[key]

        # Remove files
        entry_dir = self._entry_path(key)
        if entry_dir.exists():
            shutil.rmtree(entry_dir)

        self._dirty = True
        self._stats["invalidations"] += 1
        return True

    def invalidate_by_task(self, task_id: str) -> int:
        """
        Invalidate all entries for a task.

        Args:
            task_id: Task identifier

        Returns:
            Number of entries invalidated
        """
        keys_to_remove = [
            k for k, v in self._index.items()
            if v.task_id == task_id
        ]

        for key in keys_to_remove:
            self.invalidate(key)

        return len(keys_to_remove)

    def invalidate_by_dependency(self, dependency_id: str) -> int:
        """
        Invalidate entries that depend on a specific task.

        Args:
            dependency_id: Dependency task ID

        Returns:
            Number of entries invalidated
        """
        keys_to_remove = []

        for key, entry in self._index.items():
            deps = entry.metadata.get("dependencies", [])
            if dependency_id in deps:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            self.invalidate(key)

        return len(keys_to_remove)

    def _evict_oldest(self, count: int = 1) -> int:
        """
        Evict oldest entries to make room.

        Args:
            count: Number of entries to evict

        Returns:
            Number of entries evicted
        """
        if not self._index:
            return 0

        # Sort by last access time
        sorted_entries = sorted(
            self._index.items(),
            key=lambda x: x[1].accessed_at
        )

        evicted = 0
        for key, _ in sorted_entries[:count]:
            if self.invalidate(key):
                evicted += 1
                self._stats["evictions"] += 1

        return evicted

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = len(self._index)

        # Clear index
        self._index.clear()
        self._dirty = True
        self._save_index()

        # Clear files
        entries_dir = self.cache_dir / "entries"
        if entries_dir.exists():
            shutil.rmtree(entries_dir)
            entries_dir.mkdir()

        logger.info(f"Cleared {count} cache entries")
        return count

    def cleanup_expired(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            k for k, v in self._index.items()
            if v.is_expired
        ]

        for key in expired_keys:
            self.invalidate(key)

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

        # Calculate disk usage
        disk_usage = 0
        entries_dir = self.cache_dir / "entries"
        if entries_dir.exists():
            for f in entries_dir.rglob("*"):
                if f.is_file():
                    disk_usage += f.stat().st_size

        return {
            "entries": len(self._index),
            "max_entries": self.max_entries,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "stale": self._stats["stale"],
            "evictions": self._stats["evictions"],
            "invalidations": self._stats["invalidations"],
            "hit_rate": hit_rate,
            "disk_usage_mb": disk_usage / (1024 * 1024),
            "max_size_mb": self.max_size_mb
        }

    def list_entries(
        self,
        task_id: Optional[str] = None,
        limit: int = 100
    ) -> List[CacheEntry]:
        """
        List cache entries.

        Args:
            task_id: Filter by task ID
            limit: Maximum entries to return

        Returns:
            List of cache entries
        """
        entries = list(self._index.values())

        if task_id:
            entries = [e for e in entries if e.task_id == task_id]

        # Sort by access time (most recent first)
        entries.sort(key=lambda x: x.accessed_at, reverse=True)

        return entries[:limit]


class IncrementalBuildDetector:
    """
    Detects what needs to be rebuilt based on changes.

    Analyzes task graph and cache state to determine
    the minimal set of tasks that need regeneration.
    """

    def __init__(self, cache: GenerationCache):
        """
        Initialize detector.

        Args:
            cache: Generation cache instance
        """
        self.cache = cache

    def detect_changes(
        self,
        tasks: List[Dict[str, Any]],
        dependency_graph: Dict[str, List[str]]
    ) -> Dict[str, str]:
        """
        Detect which tasks need regeneration.

        Args:
            tasks: List of task specifications
            dependency_graph: Task dependency graph

        Returns:
            Dictionary mapping task_id to change reason
        """
        changes = {}

        for task in tasks:
            task_id = task.get("id") or task.get("task_id")
            if not task_id:
                continue

            reason = self._check_task_changes(task, dependency_graph)
            if reason:
                changes[task_id] = reason

        # Propagate changes to dependents
        all_changes = dict(changes)
        for task_id in changes:
            dependents = self._get_all_dependents(task_id, dependency_graph)
            for dep_id in dependents:
                if dep_id not in all_changes:
                    all_changes[dep_id] = f"Dependency {task_id} changed"

        return all_changes

    def _check_task_changes(
        self,
        task: Dict[str, Any],
        dependency_graph: Dict[str, List[str]]
    ) -> Optional[str]:
        """
        Check if a specific task needs regeneration.

        Args:
            task: Task specification
            dependency_graph: Dependency graph

        Returns:
            Reason for regeneration, or None if cached
        """
        task_id = task.get("id") or task.get("task_id")

        # Build cache key
        key = CacheKeyBuilder.build_key(
            task_id=task_id,
            specification=task.get("specification", ""),
            project_context=task.get("project_context", ""),
            tech_stack=task.get("tech_stack", []),
            dependencies=dependency_graph.get(task_id, []),
            patterns=task.get("patterns", [])
        )

        # Check cache
        result = self.cache.get(key)

        if result.status == CacheStatus.MISS:
            return "Not cached"
        elif result.status == CacheStatus.STALE:
            return "Cache expired"
        elif result.status == CacheStatus.INVALID:
            return result.reason or "Dependencies changed"

        return None  # Cache hit, no changes needed

    def _get_all_dependents(
        self,
        task_id: str,
        dependency_graph: Dict[str, List[str]]
    ) -> Set[str]:
        """
        Get all tasks that depend on a given task (transitively).

        Args:
            task_id: Task to find dependents for
            dependency_graph: Dependency graph

        Returns:
            Set of dependent task IDs
        """
        dependents = set()
        to_check = [task_id]

        while to_check:
            current = to_check.pop()

            for tid, deps in dependency_graph.items():
                if current in deps and tid not in dependents:
                    dependents.add(tid)
                    to_check.append(tid)

        return dependents

    def get_build_order(
        self,
        changed_tasks: Dict[str, str],
        dependency_graph: Dict[str, List[str]]
    ) -> List[str]:
        """
        Get topological order for building changed tasks.

        Args:
            changed_tasks: Tasks that need regeneration
            dependency_graph: Dependency graph

        Returns:
            Ordered list of task IDs to build
        """
        # Filter graph to only changed tasks
        filtered_graph = {
            tid: [d for d in deps if d in changed_tasks]
            for tid, deps in dependency_graph.items()
            if tid in changed_tasks
        }

        # Topological sort
        result = []
        visited = set()
        temp_mark = set()

        def visit(node: str):
            if node in temp_mark:
                raise CacheError(f"Circular dependency detected involving {node}")

            if node not in visited:
                temp_mark.add(node)

                for dep in filtered_graph.get(node, []):
                    visit(dep)

                temp_mark.remove(node)
                visited.add(node)
                result.append(node)

        for task_id in changed_tasks:
            if task_id not in visited:
                visit(task_id)

        return result


class CachedGenerator:
    """
    Wrapper that adds caching to any code generator.

    Checks cache before generation and stores results after.
    """

    def __init__(
        self,
        generator: Any,  # CodeGenerator
        cache: GenerationCache
    ):
        """
        Initialize cached generator.

        Args:
            generator: Underlying code generator
            cache: Generation cache
        """
        self.generator = generator
        self.cache = cache

    async def generate(
        self,
        context: Any,  # GenerationContext
        dependency_results: Optional[Dict[str, Dict[str, str]]] = None,
        force: bool = False
    ) -> Any:  # GenerationResult
        """
        Generate code with caching.

        Args:
            context: Generation context
            dependency_results: Results from dependency tasks
            force: Force regeneration, ignoring cache

        Returns:
            GenerationResult (cached or freshly generated)
        """
        from forge.generators.base import GenerationResult

        # Build cache key
        key = CacheKeyBuilder.build_key(
            task_id=context.task_id,
            specification=context.specification,
            project_context=context.project_context,
            tech_stack=context.tech_stack,
            dependencies=context.dependencies,
            patterns=context.knowledgeforge_patterns,
            file_structure=context.file_structure
        )

        # Build dependency hash
        dep_hash = ""
        if dependency_results:
            dep_hash = CacheKeyBuilder.build_dependency_hash(
                context.dependencies,
                dependency_results
            )

        # Check cache (unless forced)
        if not force:
            result = self.cache.get(key, dependency_hash=dep_hash)

            if result.is_hit:
                logger.info(f"Cache hit for {context.task_id}")

                # Load files from disk
                files = self.cache.load_files(key)

                return GenerationResult(
                    success=True,
                    files=files,
                    duration_seconds=0.0,
                    metadata={
                        "cached": True,
                        "cache_key": key,
                        "cache_hit_count": result.entry.hit_count
                    }
                )
            else:
                logger.debug(f"Cache miss for {context.task_id}: {result.reason}")

        # Generate fresh
        gen_result = await self.generator.generate(context)

        # Cache successful results
        if gen_result.success and gen_result.files:
            self.cache.put(
                key=key,
                task_id=context.task_id,
                content_hash=CacheKeyBuilder.hash_content(context.specification),
                dependency_hash=dep_hash,
                files=gen_result.files,
                metadata={
                    "dependencies": context.dependencies,
                    "tech_stack": context.tech_stack,
                    "duration_seconds": gen_result.duration_seconds
                }
            )

        return gen_result
