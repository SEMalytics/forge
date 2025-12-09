"""
Tests for Caching & Incremental Builds

Tests the caching infrastructure including:
- CacheEntry creation and serialization
- CacheKeyBuilder hash generation
- GenerationCache storage and retrieval
- Cache invalidation strategies
- IncrementalBuildDetector change detection
- CachedGenerator wrapper
"""

import pytest
import time
from pathlib import Path
from datetime import datetime, timedelta
import json
import shutil
from unittest.mock import Mock, AsyncMock

from forge.core.cache import (
    CacheError,
    CacheStatus,
    CacheEntry,
    CacheLookupResult,
    CacheKeyBuilder,
    GenerationCache,
    IncrementalBuildDetector,
    CachedGenerator
)


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_creation_with_defaults(self):
        """Test creating entry with minimal args."""
        entry = CacheEntry(
            key="test-key",
            task_id="task-001",
            content_hash="abc123",
            dependency_hash="def456"
        )

        assert entry.key == "test-key"
        assert entry.task_id == "task-001"
        assert entry.files == {}
        assert entry.hit_count == 0
        assert not entry.is_expired

    def test_creation_with_files(self):
        """Test creating entry with files."""
        entry = CacheEntry(
            key="test-key",
            task_id="task-001",
            content_hash="abc123",
            dependency_hash="def456",
            files={
                "src/main.py": "print('hello')",
                "src/utils.py": "def helper(): pass"
            }
        )

        assert len(entry.files) == 2
        assert "src/main.py" in entry.files

    def test_is_expired(self):
        """Test expiration detection."""
        # Not expired
        entry = CacheEntry(
            key="test",
            task_id="task",
            content_hash="abc",
            dependency_hash="def",
            ttl_seconds=3600
        )
        assert not entry.is_expired

        # Expired (set created_at in the past)
        old_date = (datetime.now() - timedelta(hours=2)).isoformat()
        entry.created_at = old_date
        entry.ttl_seconds = 3600  # 1 hour TTL
        assert entry.is_expired

    def test_age_seconds(self):
        """Test age calculation."""
        entry = CacheEntry(
            key="test",
            task_id="task",
            content_hash="abc",
            dependency_hash="def"
        )

        # Just created, should be very small
        assert entry.age_seconds < 1.0

    def test_touch(self):
        """Test touch updates access time and hit count."""
        entry = CacheEntry(
            key="test",
            task_id="task",
            content_hash="abc",
            dependency_hash="def"
        )

        original_accessed = entry.accessed_at
        original_hits = entry.hit_count

        time.sleep(0.01)
        entry.touch()

        assert entry.accessed_at > original_accessed
        assert entry.hit_count == original_hits + 1

    def test_to_dict(self):
        """Test serialization."""
        entry = CacheEntry(
            key="test-key",
            task_id="task-001",
            content_hash="abc123",
            dependency_hash="def456",
            files={"main.py": "code"},
            metadata={"lang": "python"}
        )

        data = entry.to_dict()

        assert data["key"] == "test-key"
        assert data["task_id"] == "task-001"
        assert data["files"] == {"main.py": "code"}
        assert data["metadata"]["lang"] == "python"

    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "key": "test-key",
            "task_id": "task-001",
            "content_hash": "abc123",
            "dependency_hash": "def456",
            "files": {"main.py": "code"},
            "created_at": "2024-01-01T00:00:00",
            "accessed_at": "2024-01-01T00:00:00",
            "ttl_seconds": 3600,
            "hit_count": 5,
            "metadata": {}
        }

        entry = CacheEntry.from_dict(data)

        assert entry.key == "test-key"
        assert entry.hit_count == 5


class TestCacheKeyBuilder:
    """Tests for CacheKeyBuilder."""

    def test_hash_content(self):
        """Test content hashing."""
        hash1 = CacheKeyBuilder.hash_content("hello world")
        hash2 = CacheKeyBuilder.hash_content("hello world")
        hash3 = CacheKeyBuilder.hash_content("different")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 16  # Truncated

    def test_hash_list(self):
        """Test list hashing is order-independent."""
        hash1 = CacheKeyBuilder.hash_list(["a", "b", "c"])
        hash2 = CacheKeyBuilder.hash_list(["c", "a", "b"])

        assert hash1 == hash2  # Same items, different order

    def test_hash_dict(self):
        """Test dictionary hashing."""
        hash1 = CacheKeyBuilder.hash_dict({"a": "1", "b": "2"})
        hash2 = CacheKeyBuilder.hash_dict({"b": "2", "a": "1"})

        assert hash1 == hash2  # Same items, different order

    def test_build_key(self):
        """Test building complete cache key."""
        key = CacheKeyBuilder.build_key(
            task_id="task-001",
            specification="Build a REST API",
            project_context="Python project"
        )

        assert key.startswith("task-001")
        assert "-" in key

    def test_build_key_with_options(self):
        """Test key includes optional components."""
        key1 = CacheKeyBuilder.build_key(
            task_id="task",
            specification="spec",
            project_context="context",
            tech_stack=["python"]
        )

        key2 = CacheKeyBuilder.build_key(
            task_id="task",
            specification="spec",
            project_context="context",
            tech_stack=["python", "fastapi"]
        )

        assert key1 != key2  # Different tech stack

    def test_build_key_deterministic(self):
        """Test key building is deterministic."""
        kwargs = {
            "task_id": "task-001",
            "specification": "Build API",
            "project_context": "Python",
            "tech_stack": ["python", "fastapi"],
            "dependencies": ["task-000"],
            "patterns": ["00_KB3_Core.md"]
        }

        key1 = CacheKeyBuilder.build_key(**kwargs)
        key2 = CacheKeyBuilder.build_key(**kwargs)

        assert key1 == key2

    def test_build_dependency_hash(self):
        """Test dependency hash building."""
        results = {
            "task-a": {"main.py": "code a"},
            "task-b": {"utils.py": "code b"}
        }

        hash1 = CacheKeyBuilder.build_dependency_hash(
            ["task-a", "task-b"],
            results
        )

        hash2 = CacheKeyBuilder.build_dependency_hash(
            ["task-b", "task-a"],  # Different order
            results
        )

        assert hash1 == hash2  # Order independent


class TestCacheLookupResult:
    """Tests for CacheLookupResult."""

    def test_hit_result(self):
        """Test hit result."""
        entry = CacheEntry(
            key="test",
            task_id="task",
            content_hash="abc",
            dependency_hash="def"
        )

        result = CacheLookupResult(
            status=CacheStatus.HIT,
            entry=entry
        )

        assert result.is_hit
        assert result.entry is not None

    def test_miss_result(self):
        """Test miss result."""
        result = CacheLookupResult(
            status=CacheStatus.MISS,
            reason="Key not found"
        )

        assert not result.is_hit
        assert result.reason == "Key not found"


class TestGenerationCache:
    """Tests for GenerationCache."""

    @pytest.fixture
    def cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        return tmp_path / "cache"

    @pytest.fixture
    def cache(self, cache_dir):
        """Create cache instance."""
        return GenerationCache(cache_dir=cache_dir)

    def test_initialization(self, cache, cache_dir):
        """Test cache initializes correctly."""
        assert cache.cache_dir == cache_dir
        assert cache_dir.exists()

    def test_put_and_get(self, cache):
        """Test storing and retrieving entry."""
        # Store entry
        entry = cache.put(
            key="test-key",
            task_id="task-001",
            content_hash="abc123",
            dependency_hash="def456",
            files={"main.py": "print('hello')"}
        )

        assert entry.key == "test-key"

        # Retrieve entry
        result = cache.get("test-key")

        assert result.is_hit
        assert result.entry.task_id == "task-001"

    def test_get_miss(self, cache):
        """Test cache miss."""
        result = cache.get("nonexistent-key")

        assert result.status == CacheStatus.MISS
        assert not result.is_hit

    def test_get_stale(self, cache):
        """Test stale entry detection."""
        # Store entry with short TTL
        cache.put(
            key="stale-key",
            task_id="task",
            content_hash="abc",
            dependency_hash="def",
            files={},
            ttl_seconds=0  # Immediately expired
        )

        # Wait a tiny bit
        time.sleep(0.01)

        result = cache.get("stale-key")
        assert result.status == CacheStatus.STALE

    def test_get_invalid_dependency(self, cache):
        """Test dependency validation."""
        cache.put(
            key="dep-key",
            task_id="task",
            content_hash="abc",
            dependency_hash="original-hash",
            files={}
        )

        # Get with different dependency hash
        result = cache.get("dep-key", dependency_hash="different-hash")

        assert result.status == CacheStatus.INVALID
        assert "Dependencies changed" in result.reason

    def test_load_files(self, cache):
        """Test loading cached files from disk."""
        files = {
            "src/main.py": "print('hello')",
            "src/utils.py": "def helper(): pass"
        }

        cache.put(
            key="files-key",
            task_id="task",
            content_hash="abc",
            dependency_hash="def",
            files=files
        )

        loaded = cache.load_files("files-key")

        assert len(loaded) == 2
        assert loaded["src/main.py"] == "print('hello')"

    def test_invalidate(self, cache):
        """Test invalidating entry."""
        cache.put(
            key="to-remove",
            task_id="task",
            content_hash="abc",
            dependency_hash="def",
            files={}
        )

        result = cache.invalidate("to-remove")
        assert result is True

        # Entry should be gone
        lookup = cache.get("to-remove")
        assert lookup.status == CacheStatus.MISS

    def test_invalidate_by_task(self, cache):
        """Test invalidating all entries for a task."""
        # Create multiple entries for same task
        for i in range(3):
            cache.put(
                key=f"task-entry-{i}",
                task_id="my-task",
                content_hash=f"hash-{i}",
                dependency_hash="def",
                files={}
            )

        # Add entry for different task
        cache.put(
            key="other-entry",
            task_id="other-task",
            content_hash="abc",
            dependency_hash="def",
            files={}
        )

        count = cache.invalidate_by_task("my-task")
        assert count == 3

        # Other task entry should remain
        result = cache.get("other-entry")
        assert result.is_hit

    def test_invalidate_by_dependency(self, cache):
        """Test invalidating dependent entries."""
        # Entry that depends on upstream
        cache.put(
            key="downstream",
            task_id="downstream-task",
            content_hash="abc",
            dependency_hash="def",
            files={},
            metadata={"dependencies": ["upstream-task"]}
        )

        # Entry without that dependency
        cache.put(
            key="independent",
            task_id="independent-task",
            content_hash="abc",
            dependency_hash="def",
            files={},
            metadata={"dependencies": []}
        )

        count = cache.invalidate_by_dependency("upstream-task")
        assert count == 1

        # Independent entry should remain
        result = cache.get("independent")
        assert result.is_hit

    def test_clear(self, cache):
        """Test clearing all entries."""
        for i in range(5):
            cache.put(
                key=f"entry-{i}",
                task_id=f"task-{i}",
                content_hash=f"hash-{i}",
                dependency_hash="def",
                files={}
            )

        count = cache.clear()
        assert count == 5

        stats = cache.get_stats()
        assert stats["entries"] == 0

    def test_cleanup_expired(self, cache):
        """Test cleaning up expired entries."""
        # Expired entry
        cache.put(
            key="expired",
            task_id="task",
            content_hash="abc",
            dependency_hash="def",
            files={},
            ttl_seconds=0
        )

        # Valid entry
        cache.put(
            key="valid",
            task_id="task",
            content_hash="abc",
            dependency_hash="def",
            files={},
            ttl_seconds=3600
        )

        time.sleep(0.01)
        count = cache.cleanup_expired()

        assert count == 1
        assert cache.get("valid").is_hit
        assert not cache.get("expired").is_hit

    def test_eviction(self, cache_dir):
        """Test LRU eviction when cache is full."""
        cache = GenerationCache(cache_dir=cache_dir, max_entries=3)

        # Fill cache
        for i in range(3):
            cache.put(
                key=f"entry-{i}",
                task_id=f"task-{i}",
                content_hash=f"hash-{i}",
                dependency_hash="def",
                files={}
            )

        # Access entry-1 to make it more recent
        cache.get("entry-1")

        # Add new entry, should evict entry-0 (oldest)
        cache.put(
            key="new-entry",
            task_id="new-task",
            content_hash="new-hash",
            dependency_hash="def",
            files={}
        )

        assert not cache.get("entry-0").is_hit  # Evicted
        assert cache.get("entry-1").is_hit  # Still there
        assert cache.get("new-entry").is_hit

    def test_get_stats(self, cache):
        """Test statistics tracking."""
        cache.put(
            key="entry",
            task_id="task",
            content_hash="abc",
            dependency_hash="def",
            files={"main.py": "code"}
        )

        # Generate some hits/misses
        cache.get("entry")  # Hit
        cache.get("entry")  # Hit
        cache.get("nonexistent")  # Miss

        stats = cache.get_stats()

        assert stats["entries"] == 1
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(2/3)
        assert stats["disk_usage_mb"] > 0

    def test_list_entries(self, cache):
        """Test listing entries."""
        for i in range(5):
            cache.put(
                key=f"entry-{i}",
                task_id=f"task-{i % 2}",  # Alternating task IDs
                content_hash=f"hash-{i}",
                dependency_hash="def",
                files={}
            )
            time.sleep(0.01)  # Ensure different timestamps

        # List all
        all_entries = cache.list_entries()
        assert len(all_entries) == 5

        # List by task
        task0_entries = cache.list_entries(task_id="task-0")
        assert len(task0_entries) == 3

        # List with limit
        limited = cache.list_entries(limit=2)
        assert len(limited) == 2

    def test_persistence(self, cache_dir):
        """Test cache persists across instances."""
        # Create and populate cache
        cache1 = GenerationCache(cache_dir=cache_dir)
        cache1.put(
            key="persistent",
            task_id="task",
            content_hash="abc",
            dependency_hash="def",
            files={"main.py": "code"}
        )

        # Create new instance
        cache2 = GenerationCache(cache_dir=cache_dir)

        result = cache2.get("persistent")
        assert result.is_hit


class TestIncrementalBuildDetector:
    """Tests for IncrementalBuildDetector."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create cache for detector."""
        return GenerationCache(cache_dir=tmp_path / "cache")

    @pytest.fixture
    def detector(self, cache):
        """Create detector instance."""
        return IncrementalBuildDetector(cache)

    def test_detect_all_changed_when_empty(self, detector):
        """Test all tasks need rebuild when cache is empty."""
        tasks = [
            {"id": "task-1", "specification": "spec 1", "project_context": "ctx"},
            {"id": "task-2", "specification": "spec 2", "project_context": "ctx"}
        ]

        dep_graph = {"task-1": [], "task-2": ["task-1"]}

        changes = detector.detect_changes(tasks, dep_graph)

        assert "task-1" in changes
        assert "task-2" in changes

    def test_detect_cached_unchanged(self, cache, detector):
        """Test cached tasks are not marked as changed."""
        # Pre-cache task-1
        key = CacheKeyBuilder.build_key(
            task_id="task-1",
            specification="spec 1",
            project_context="ctx"
        )
        cache.put(
            key=key,
            task_id="task-1",
            content_hash="abc",
            dependency_hash="",
            files={"main.py": "code"}
        )

        tasks = [
            {"id": "task-1", "specification": "spec 1", "project_context": "ctx"},
            {"id": "task-2", "specification": "spec 2", "project_context": "ctx"}
        ]

        dep_graph = {"task-1": [], "task-2": []}

        changes = detector.detect_changes(tasks, dep_graph)

        assert "task-1" not in changes  # Cached
        assert "task-2" in changes  # Not cached

    def test_propagate_changes_to_dependents(self, detector, cache):
        """Test changes propagate to dependent tasks."""
        # Cache the downstream task
        downstream_key = CacheKeyBuilder.build_key(
            task_id="downstream",
            specification="downstream spec",
            project_context="ctx",
            dependencies=["upstream"]
        )
        cache.put(
            key=downstream_key,
            task_id="downstream",
            content_hash="abc",
            dependency_hash="",
            files={"output.py": "code"}
        )

        tasks = [
            {"id": "upstream", "specification": "spec", "project_context": "ctx"},
            {"id": "downstream", "specification": "downstream spec", "project_context": "ctx"}
        ]

        dep_graph = {
            "upstream": [],
            "downstream": ["upstream"]
        }

        changes = detector.detect_changes(tasks, dep_graph)

        # Upstream is not cached, so it changes
        assert "upstream" in changes
        # Downstream IS cached, but should be marked due to upstream dependency
        assert "downstream" in changes
        assert "Dependency" in changes["downstream"]

    def test_get_build_order(self, detector):
        """Test topological ordering of tasks."""
        changes = {
            "task-a": "Not cached",
            "task-b": "Not cached",
            "task-c": "Not cached"
        }

        dep_graph = {
            "task-a": [],
            "task-b": ["task-a"],
            "task-c": ["task-b"]
        }

        order = detector.get_build_order(changes, dep_graph)

        assert order.index("task-a") < order.index("task-b")
        assert order.index("task-b") < order.index("task-c")

    def test_detect_circular_dependency(self, detector):
        """Test circular dependency detection."""
        changes = {
            "task-a": "Not cached",
            "task-b": "Not cached"
        }

        dep_graph = {
            "task-a": ["task-b"],
            "task-b": ["task-a"]  # Circular!
        }

        with pytest.raises(CacheError, match="Circular dependency"):
            detector.get_build_order(changes, dep_graph)


class TestCachedGenerator:
    """Tests for CachedGenerator wrapper."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create cache."""
        return GenerationCache(cache_dir=tmp_path / "cache")

    @pytest.fixture
    def mock_generator(self):
        """Create mock generator."""
        generator = Mock()
        generator.generate = AsyncMock()
        return generator

    @pytest.fixture
    def cached_gen(self, mock_generator, cache):
        """Create cached generator."""
        return CachedGenerator(mock_generator, cache)

    @pytest.mark.asyncio
    async def test_cache_miss_generates(self, cached_gen, mock_generator):
        """Test generation happens on cache miss."""
        from forge.generators.base import GenerationContext, GenerationResult

        context = GenerationContext(
            task_id="task-001",
            specification="Build API",
            project_context="Python project"
        )

        mock_generator.generate.return_value = GenerationResult(
            success=True,
            files={"main.py": "code"},
            duration_seconds=1.0
        )

        result = await cached_gen.generate(context)

        assert result.success
        mock_generator.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit_skips_generation(self, cached_gen, mock_generator, cache):
        """Test generation is skipped on cache hit."""
        from forge.generators.base import GenerationContext, GenerationResult

        context = GenerationContext(
            task_id="task-001",
            specification="Build API",
            project_context="Python project"
        )

        # Pre-populate cache
        key = CacheKeyBuilder.build_key(
            task_id=context.task_id,
            specification=context.specification,
            project_context=context.project_context,
            tech_stack=context.tech_stack,
            dependencies=context.dependencies,
            patterns=context.knowledgeforge_patterns,
            file_structure=context.file_structure
        )

        cache.put(
            key=key,
            task_id=context.task_id,
            content_hash=CacheKeyBuilder.hash_content(context.specification),
            dependency_hash="",
            files={"main.py": "cached code"}
        )

        result = await cached_gen.generate(context)

        assert result.success
        assert result.metadata.get("cached") is True
        assert "cached code" in result.files["main.py"]
        mock_generator.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_force_bypasses_cache(self, cached_gen, mock_generator, cache):
        """Test force flag bypasses cache."""
        from forge.generators.base import GenerationContext, GenerationResult

        context = GenerationContext(
            task_id="task-001",
            specification="Build API",
            project_context="Python project"
        )

        # Pre-populate cache
        key = CacheKeyBuilder.build_key(
            task_id=context.task_id,
            specification=context.specification,
            project_context=context.project_context,
            tech_stack=context.tech_stack,
            dependencies=context.dependencies,
            patterns=context.knowledgeforge_patterns,
            file_structure=context.file_structure
        )

        cache.put(
            key=key,
            task_id=context.task_id,
            content_hash="abc",
            dependency_hash="",
            files={"main.py": "old code"}
        )

        mock_generator.generate.return_value = GenerationResult(
            success=True,
            files={"main.py": "new code"},
            duration_seconds=1.0
        )

        result = await cached_gen.generate(context, force=True)

        assert result.success
        assert "cached" not in result.metadata
        mock_generator.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_caches_successful_result(self, cached_gen, mock_generator, cache):
        """Test successful results are cached."""
        from forge.generators.base import GenerationContext, GenerationResult

        context = GenerationContext(
            task_id="task-001",
            specification="Build API",
            project_context="Python project"
        )

        mock_generator.generate.return_value = GenerationResult(
            success=True,
            files={"main.py": "generated code"},
            duration_seconds=1.0
        )

        await cached_gen.generate(context)

        # Check it was cached
        stats = cache.get_stats()
        assert stats["entries"] == 1

    @pytest.mark.asyncio
    async def test_does_not_cache_failures(self, cached_gen, mock_generator, cache):
        """Test failed results are not cached."""
        from forge.generators.base import GenerationContext, GenerationResult

        context = GenerationContext(
            task_id="task-001",
            specification="Build API",
            project_context="Python project"
        )

        mock_generator.generate.return_value = GenerationResult(
            success=False,
            error="Generation failed"
        )

        await cached_gen.generate(context)

        # Should not be cached
        stats = cache.get_stats()
        assert stats["entries"] == 0


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create cache."""
        return GenerationCache(cache_dir=tmp_path / "cache")

    def test_empty_files(self, cache):
        """Test caching with no files."""
        cache.put(
            key="empty",
            task_id="task",
            content_hash="abc",
            dependency_hash="def",
            files={}
        )

        loaded = cache.load_files("empty")
        assert loaded == {}

    def test_special_characters_in_content(self, cache):
        """Test content with special characters."""
        files = {
            "main.py": "def hello():\n\t\"\"\"Say hello\"\"\"\n\tprint('Hello 世界!')"
        }

        cache.put(
            key="special",
            task_id="task",
            content_hash="abc",
            dependency_hash="def",
            files=files
        )

        loaded = cache.load_files("special")
        assert "世界" in loaded["main.py"]

    def test_deep_file_paths(self, cache):
        """Test deeply nested file paths."""
        files = {
            "src/components/ui/forms/input/TextField.tsx": "code"
        }

        cache.put(
            key="deep",
            task_id="task",
            content_hash="abc",
            dependency_hash="def",
            files=files
        )

        loaded = cache.load_files("deep")
        assert "src/components/ui/forms/input/TextField.tsx" in loaded

    def test_path_traversal_protection(self, cache):
        """Test that path traversal is prevented."""
        files = {
            "../../../etc/passwd": "malicious"
        }

        cache.put(
            key="traversal",
            task_id="task",
            content_hash="abc",
            dependency_hash="def",
            files=files
        )

        # Should sanitize path
        loaded = cache.load_files("traversal")
        assert "../" not in list(loaded.keys())[0] if loaded else True

    def test_invalidate_nonexistent(self, cache):
        """Test invalidating nonexistent entry."""
        result = cache.invalidate("does-not-exist")
        assert result is False

    def test_concurrent_access(self, cache):
        """Test behavior with rapid access patterns."""
        # Rapid put/get cycles
        for i in range(50):
            cache.put(
                key=f"rapid-{i}",
                task_id=f"task-{i}",
                content_hash=f"hash-{i}",
                dependency_hash="def",
                files={"main.py": f"code-{i}"}
            )
            cache.get(f"rapid-{i}")

        stats = cache.get_stats()
        assert stats["entries"] == 50
        assert stats["hits"] == 50
