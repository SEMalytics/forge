"""
Tests for Context Manager

Tests the context cascading functionality including:
- Context item creation and management
- Reference tracking between items
- Token counting and windowing
- Summarization
- Persistence
"""

import pytest
from pathlib import Path
from datetime import datetime
import json
import tempfile
from unittest.mock import Mock, patch

from forge.core.context import (
    ContextManager,
    ContextItem,
    ContextType,
    ContextWindow,
    ContextError
)


class TestContextType:
    """Tests for ContextType enum."""

    def test_all_types_defined(self):
        """Test all expected context types exist."""
        expected = [
            'specification',
            'architecture',
            'generated_code',
            'test_result',
            'review_feedback',
            'user_input',
            'system',
            'summary'
        ]

        actual = [t.value for t in ContextType]
        assert set(expected) == set(actual)

    def test_type_from_string(self):
        """Test creating type from string value."""
        assert ContextType('specification') == ContextType.SPECIFICATION
        assert ContextType('architecture') == ContextType.ARCHITECTURE
        assert ContextType('generated_code') == ContextType.GENERATED_CODE


class TestContextItem:
    """Tests for ContextItem dataclass."""

    def test_creation_with_all_fields(self):
        """Test creating item with all fields."""
        item = ContextItem(
            id="test-001",
            content="def hello(): pass",
            context_type=ContextType.GENERATED_CODE,
            references=["ref-001", "ref-002"],
            source="task-001",
            tags=["python"],
            metadata={"language": "python"}
        )

        assert item.id == "test-001"
        assert item.context_type == ContextType.GENERATED_CODE
        assert item.source == "task-001"
        assert len(item.references) == 2
        assert item.metadata.get("language") == "python"

    def test_content_hash(self):
        """Test content hash property."""
        item = ContextItem(
            id="test",
            content="test content",
            context_type=ContextType.USER_INPUT
        )

        hash1 = item.content_hash

        # Same content should have same hash
        item2 = ContextItem(
            id="test2",
            content="test content",
            context_type=ContextType.USER_INPUT
        )

        assert item.content_hash == item2.content_hash

    def test_effective_content_returns_content_when_no_summary(self):
        """Test effective_content returns content when no summary."""
        item = ContextItem(
            id="test",
            content="original content",
            context_type=ContextType.USER_INPUT
        )

        assert item.effective_content == "original content"

    def test_effective_content_returns_summary_for_large_content(self):
        """Test effective_content returns summary for large content."""
        item = ContextItem(
            id="test",
            content="x" * 10000,
            context_type=ContextType.USER_INPUT,
            token_count=3000,  # > 500
            summary="Summary of content"
        )

        assert item.effective_content == "Summary of content"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        item = ContextItem(
            id="item-123",
            content="Design doc",
            context_type=ContextType.ARCHITECTURE,
            source="user"
        )

        data = item.to_dict()

        assert data['id'] == "item-123"
        assert data['context_type'] == 'architecture'
        assert data['content'] == "Design doc"
        assert data['source'] == "user"
        assert 'created_at' in data

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'id': 'item-123',
            'context_type': 'specification',
            'content': 'Test spec',
            'created_at': '2024-01-01T00:00:00',
            'token_count': 10,
            'references': ['ref-1'],
            'referenced_by': [],
            'source': 'user',
            'tags': [],
            'metadata': {},
            'is_active': True,
            'priority': 0
        }

        item = ContextItem.from_dict(data)

        assert item.id == 'item-123'
        assert item.context_type == ContextType.SPECIFICATION
        assert item.content == 'Test spec'
        assert item.references == ['ref-1']


class TestContextManager:
    """Tests for ContextManager class."""

    @pytest.fixture
    def manager(self):
        """Create test ContextManager."""
        return ContextManager()

    def test_initialization(self, manager):
        """Test manager initializes correctly."""
        assert manager._items == {}
        assert manager.max_tokens == 8000

    def test_add_item(self, manager):
        """Test adding context item."""
        item = manager.add(
            id="spec-001",
            content="Build a REST API",
            context_type=ContextType.SPECIFICATION
        )

        assert item.id == "spec-001"
        assert item.id in manager._items
        assert manager._items[item.id] == item

    def test_add_item_with_source(self, manager):
        """Test adding context with source."""
        item = manager.add(
            id="arch-001",
            content="Microservices design",
            context_type=ContextType.ARCHITECTURE,
            source="task-001"
        )

        assert item.source == "task-001"

    def test_add_item_with_references(self, manager):
        """Test adding context that references other items."""
        # Add first item
        spec = manager.add(
            id="spec-001",
            content="Build a REST API",
            context_type=ContextType.SPECIFICATION
        )

        # Add item that references first
        arch = manager.add(
            id="arch-001",
            content="Based on specification, use FastAPI",
            context_type=ContextType.ARCHITECTURE,
            references=["spec-001"]
        )

        assert spec.id in arch.references
        assert arch.id in spec.referenced_by

    def test_add_with_string_type(self, manager):
        """Test adding with string type."""
        item = manager.add(
            id="test-001",
            content="Test content",
            context_type="user_input"
        )

        assert item.context_type == ContextType.USER_INPUT

    def test_get_item(self, manager):
        """Test retrieving context by ID."""
        manager.add(
            id="test-001",
            content="Test",
            context_type=ContextType.USER_INPUT
        )

        retrieved = manager.get("test-001")
        assert retrieved is not None
        assert retrieved.id == "test-001"

        not_found = manager.get("nonexistent")
        assert not_found is None

    def test_get_by_type(self, manager):
        """Test retrieving context by type."""
        manager.add("spec-1", "Spec 1", ContextType.SPECIFICATION)
        manager.add("spec-2", "Spec 2", ContextType.SPECIFICATION)
        manager.add("arch-1", "Arch 1", ContextType.ARCHITECTURE)

        specs = manager.get_by_type(ContextType.SPECIFICATION)
        assert len(specs) == 2

        archs = manager.get_by_type(ContextType.ARCHITECTURE)
        assert len(archs) == 1

    def test_get_by_tag(self, manager):
        """Test retrieving context by tag."""
        manager.add("item-1", "Content 1", ContextType.USER_INPUT, tags=["python"])
        manager.add("item-2", "Content 2", ContextType.USER_INPUT, tags=["python", "api"])
        manager.add("item-3", "Content 3", ContextType.USER_INPUT, tags=["java"])

        python_items = manager.get_by_tag("python")
        assert len(python_items) == 2

    def test_get_by_source(self, manager):
        """Test retrieving context by source."""
        manager.add("item-1", "Content 1", ContextType.GENERATED_CODE, source="task-1")
        manager.add("item-2", "Content 2", ContextType.TEST_RESULT, source="task-1")
        manager.add("item-3", "Content 3", ContextType.GENERATED_CODE, source="task-2")

        task1_items = manager.get_by_source("task-1")
        assert len(task1_items) == 2

    def test_remove_item(self, manager):
        """Test removing context item."""
        manager.add("test-001", "Test", ContextType.USER_INPUT)
        assert "test-001" in manager._items

        result = manager.remove("test-001")

        assert result is True
        assert "test-001" not in manager._items

    def test_remove_cleans_references(self, manager):
        """Test that removing item cleans up references."""
        manager.add("spec-001", "Spec", ContextType.SPECIFICATION)
        manager.add(
            "arch-001",
            "Arch",
            ContextType.ARCHITECTURE,
            references=["spec-001"]
        )

        spec = manager.get("spec-001")
        assert "arch-001" in spec.referenced_by

        # Remove arch item
        manager.remove("arch-001")

        # Reference should be cleaned
        spec = manager.get("spec-001")
        assert "arch-001" not in spec.referenced_by

    def test_update_item(self, manager):
        """Test updating context content."""
        manager.add("test-001", "Original", ContextType.SPECIFICATION)

        manager.update("test-001", content="Updated content")

        updated = manager.get("test-001")
        assert updated.content == "Updated content"

    def test_update_recalculates_tokens(self, manager):
        """Test that updating content recalculates tokens."""
        manager.add("test-001", "Short", ContextType.SPECIFICATION)
        item = manager.get("test-001")
        original_tokens = item.token_count

        manager.update("test-001", content="Much longer content " * 50)

        updated = manager.get("test-001")
        assert updated.token_count > original_tokens

    def test_update_priority(self, manager):
        """Test updating item priority."""
        manager.add("test-001", "Content", ContextType.USER_INPUT)

        manager.update("test-001", priority=10)

        updated = manager.get("test-001")
        assert updated.priority == 10

    def test_update_is_active(self, manager):
        """Test deactivating item."""
        manager.add("test-001", "Content", ContextType.USER_INPUT)

        manager.update("test-001", is_active=False)

        updated = manager.get("test-001")
        assert updated.is_active is False

    def test_clear_all(self, manager):
        """Test clearing all context."""
        manager.add("item-1", "1", ContextType.SPECIFICATION)
        manager.add("item-2", "2", ContextType.ARCHITECTURE)

        assert len(manager._items) == 2

        manager.clear()

        assert len(manager._items) == 0

    def test_clear_by_type(self, manager):
        """Test clearing context by type."""
        manager.add("spec-1", "1", ContextType.SPECIFICATION)
        manager.add("spec-2", "2", ContextType.SPECIFICATION)
        manager.add("arch-1", "3", ContextType.ARCHITECTURE)

        manager.clear_by_type(ContextType.SPECIFICATION)

        assert len(manager._items) == 1
        remaining = list(manager._items.values())[0]
        assert remaining.context_type == ContextType.ARCHITECTURE


class TestContextWindow:
    """Tests for ContextWindow class."""

    def test_creation(self):
        """Test creating context window."""
        items = [
            ContextItem(
                id="spec-1",
                content="Spec",
                context_type=ContextType.SPECIFICATION
            ),
            ContextItem(
                id="arch-1",
                content="Arch",
                context_type=ContextType.ARCHITECTURE
            )
        ]

        window = ContextWindow(
            items=items,
            total_tokens=100,
            max_tokens=4000
        )

        assert len(window.items) == 2
        assert window.max_tokens == 4000
        assert window.total_tokens == 100

    def test_truncated_flag(self):
        """Test truncated flag."""
        items = [ContextItem("1", "content", ContextType.USER_INPUT)]

        window = ContextWindow(
            items=items,
            total_tokens=100,
            max_tokens=4000,
            truncated=True,
            excluded_ids=["excluded-1"]
        )

        assert window.truncated is True
        assert "excluded-1" in window.excluded_ids

    def test_to_prompt(self):
        """Test converting window to prompt string."""
        items = [
            ContextItem("spec-1", "Build REST API", ContextType.SPECIFICATION),
            ContextItem("arch-1", "Use FastAPI", ContextType.ARCHITECTURE)
        ]

        window = ContextWindow(items=items, total_tokens=100, max_tokens=4000)
        prompt = window.to_prompt()

        assert "Build REST API" in prompt
        assert "Use FastAPI" in prompt

    def test_to_prompt_with_metadata(self):
        """Test prompt generation with metadata."""
        items = [
            ContextItem(
                id="spec-1",
                content="Content",
                context_type=ContextType.SPECIFICATION,
                source="user"
            )
        ]

        window = ContextWindow(items=items, total_tokens=100, max_tokens=4000)
        prompt = window.to_prompt(include_metadata=True)

        assert "spec-1" in prompt
        assert "specification" in prompt
        assert "user" in prompt


class TestContextManagerWindow:
    """Tests for context window generation."""

    @pytest.fixture
    def manager(self):
        """Create test manager with items."""
        mgr = ContextManager()

        # Add various items
        mgr.add("spec-1", "Spec content", ContextType.SPECIFICATION, source="p1")
        mgr.add("arch-1", "Arch content", ContextType.ARCHITECTURE, source="p1")
        mgr.add("code-1", "Code", ContextType.GENERATED_CODE, source="task-1")
        mgr.add("test-1", "Tests passed", ContextType.TEST_RESULT, source="task-1")
        mgr.add("spec-2", "Other spec", ContextType.SPECIFICATION, source="p2")

        return mgr

    def test_get_all_context(self, manager):
        """Test getting all context as window."""
        window = manager.get_all_context()
        assert len(window.items) == 5

    def test_get_all_context_by_type(self, manager):
        """Test getting context filtered by type."""
        window = manager.get_all_context(
            include_type=[ContextType.SPECIFICATION, ContextType.ARCHITECTURE]
        )
        assert len(window.items) == 3  # 2 specs + 1 arch

    def test_get_all_context_exclude_type(self, manager):
        """Test getting context with excluded types."""
        window = manager.get_all_context(
            exclude_type=[ContextType.TEST_RESULT]
        )
        assert len(window.items) == 4

    def test_get_context_for_target(self, manager):
        """Test getting context for specific target."""
        # Get context for task-1 source
        window = manager.get_context_for("task-1")

        # Should include items with source=task-1 plus system/spec items
        assert len(window.items) >= 2

    def test_get_context_respects_token_limit(self, manager):
        """Test that window respects token limit."""
        # Add large items
        for i in range(10):
            manager.add(
                f"large-{i}",
                "x" * 1000,
                ContextType.GENERATED_CODE,
                source="big"
            )

        window = manager.get_all_context(max_tokens=500)

        # Should have fewer items due to token limit
        assert window.total_tokens <= 500
        assert window.truncated is True

    def test_get_context_priority_ordering(self, manager):
        """Test that window orders by priority."""
        manager.add("low-pri", "Low", ContextType.USER_INPUT, priority=1)
        manager.add("high-pri", "High", ContextType.USER_INPUT, priority=10)

        window = manager.get_all_context()

        # Find positions
        ids = [i.id for i in window.items]
        high_idx = ids.index("high-pri")
        low_idx = ids.index("low-pri")

        # High priority should come first
        assert high_idx < low_idx


class TestContextManagerReferences:
    """Tests for reference tracking."""

    @pytest.fixture
    def manager(self):
        """Create test manager."""
        return ContextManager()

    def test_get_references(self, manager):
        """Test getting items that this item references."""
        manager.add("spec-1", "Spec", ContextType.SPECIFICATION)
        manager.add("arch-1", "Arch", ContextType.ARCHITECTURE)
        manager.add(
            "code-1",
            "Code",
            ContextType.GENERATED_CODE,
            references=["spec-1", "arch-1"]
        )

        refs = manager.get_references("code-1")

        assert len(refs) == 2
        ref_ids = [r.id for r in refs]
        assert "spec-1" in ref_ids
        assert "arch-1" in ref_ids

    def test_get_referenced_by(self, manager):
        """Test getting items that reference this item."""
        spec = manager.add("spec-1", "Spec", ContextType.SPECIFICATION)
        manager.add(
            "arch-1",
            "Arch based on spec",
            ContextType.ARCHITECTURE,
            references=["spec-1"]
        )
        manager.add(
            "code-1",
            "Code based on spec",
            ContextType.GENERATED_CODE,
            references=["spec-1"]
        )

        refs = manager.get_referenced_by("spec-1")

        assert len(refs) == 2
        ref_ids = [r.id for r in refs]
        assert "arch-1" in ref_ids
        assert "code-1" in ref_ids


class TestContextManagerSummarization:
    """Tests for context summarization."""

    @pytest.fixture
    def manager(self):
        """Create test manager."""
        return ContextManager()

    def test_auto_summarize_large_content(self, manager):
        """Test automatic summarization for large content."""
        long_content = """
        # Project Architecture

        This is a very long piece of content that describes
        the architecture of a system in great detail. It includes
        information about databases, APIs, authentication,
        and many other components.

        ## Database Layer
        Uses PostgreSQL with SQLAlchemy ORM.

        ## API Layer
        FastAPI with automatic OpenAPI docs.
        """ * 20

        item = manager.add(
            "arch-001",
            long_content,
            ContextType.ARCHITECTURE,
            summarize=True
        )

        assert item.summary is not None
        assert len(item.summary) < len(item.content)

    def test_summarize_method(self, manager):
        """Test manual summarization."""
        manager.add(
            "spec-001",
            """
            # API Specification

            This API provides user management features.

            ## Endpoints
            - GET /users
            - POST /users
            - GET /users/{id}

            ## Authentication
            Uses JWT tokens.
            """,
            ContextType.SPECIFICATION
        )

        summary = manager.summarize("spec-001")

        assert summary is not None
        item = manager.get("spec-001")
        assert item.summary == summary


class TestContextManagerPersistence:
    """Tests for context persistence."""

    @pytest.fixture
    def manager(self):
        """Create test manager."""
        return ContextManager()

    def test_save_and_load(self, manager, tmp_path):
        """Test saving and loading context."""
        # Add some items
        manager.add("spec-1", "Spec", ContextType.SPECIFICATION, source="p1")
        manager.add("arch-1", "Arch", ContextType.ARCHITECTURE, source="p1")

        # Save
        save_path = tmp_path / "context"
        manager.save(save_path)

        assert (save_path / "context.json").exists()

        # Create new manager and load
        new_manager = ContextManager()
        count = new_manager.load(save_path)

        assert count == 2
        assert len(new_manager._items) == 2

    def test_save_preserves_references(self, manager, tmp_path):
        """Test that save preserves reference relationships."""
        manager.add("spec-1", "Spec", ContextType.SPECIFICATION)
        manager.add(
            "arch-1",
            "Arch",
            ContextType.ARCHITECTURE,
            references=["spec-1"]
        )

        save_path = tmp_path / "context"
        manager.save(save_path)

        new_manager = ContextManager()
        new_manager.load(save_path)

        loaded_arch = new_manager.get("arch-1")
        assert "spec-1" in loaded_arch.references

    def test_load_nonexistent_file(self, manager, tmp_path):
        """Test loading from nonexistent path."""
        count = manager.load(tmp_path / "nonexistent")
        assert count == 0


class TestContextManagerStatistics:
    """Tests for context statistics."""

    @pytest.fixture
    def manager(self):
        """Create manager with various items."""
        mgr = ContextManager()

        mgr.add("spec-1", "Spec 1", ContextType.SPECIFICATION)
        mgr.add("spec-2", "Spec 2", ContextType.SPECIFICATION)
        mgr.add("arch-1", "Arch", ContextType.ARCHITECTURE)
        mgr.add("code-1", "Code" * 100, ContextType.GENERATED_CODE)

        return mgr

    def test_get_stats(self, manager):
        """Test getting overall statistics."""
        stats = manager.get_stats()

        assert stats['total_items'] == 4
        assert stats['total_tokens'] > 0
        assert 'types' in stats

    def test_stats_by_type(self, manager):
        """Test statistics breakdown by type."""
        stats = manager.get_stats()

        by_type = stats['types']
        assert by_type.get('specification', 0) == 2
        assert by_type.get('architecture', 0) == 1
        assert by_type.get('generated_code', 0) == 1


class TestContextManagerMagicMethods:
    """Tests for magic methods."""

    @pytest.fixture
    def manager(self):
        """Create test manager."""
        return ContextManager()

    def test_len(self, manager):
        """Test __len__."""
        assert len(manager) == 0

        manager.add("item-1", "Content", ContextType.USER_INPUT)
        assert len(manager) == 1

        manager.add("item-2", "Content", ContextType.USER_INPUT)
        assert len(manager) == 2

    def test_contains(self, manager):
        """Test __contains__."""
        assert "item-1" not in manager

        manager.add("item-1", "Content", ContextType.USER_INPUT)
        assert "item-1" in manager

    def test_iter(self, manager):
        """Test __iter__."""
        manager.add("item-1", "Content 1", ContextType.USER_INPUT)
        manager.add("item-2", "Content 2", ContextType.USER_INPUT)

        items = list(manager)
        assert len(items) == 2

        ids = [i.id for i in items]
        assert "item-1" in ids
        assert "item-2" in ids


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def manager(self):
        """Create test manager."""
        return ContextManager()

    def test_empty_content(self, manager):
        """Test handling empty content."""
        # Should still work - just creates item with empty content
        item = manager.add("test-001", "", ContextType.USER_INPUT)
        assert item.token_count == 0

    def test_very_long_content(self, manager):
        """Test handling very long content."""
        long_content = "x" * 100000
        item = manager.add("test-001", long_content, ContextType.SPECIFICATION)

        assert item is not None
        assert item.token_count > 0

    def test_unicode_content(self, manager):
        """Test handling unicode content."""
        content = "Testing unicode: 测试内容 🚀 тест"
        item = manager.add("test-001", content, ContextType.USER_INPUT)

        assert item.content == content

    def test_remove_nonexistent(self, manager):
        """Test removing nonexistent item."""
        result = manager.remove("nonexistent")
        assert result is False

    def test_update_nonexistent(self, manager):
        """Test updating nonexistent item."""
        result = manager.update("nonexistent", content="new")
        assert result is None

    def test_get_references_nonexistent(self, manager):
        """Test getting references for nonexistent item."""
        refs = manager.get_references("nonexistent")
        assert refs == []

    def test_summarize_nonexistent(self, manager):
        """Test summarizing nonexistent item."""
        result = manager.summarize("nonexistent")
        assert result is None

    def test_deactivate_old(self, manager):
        """Test deactivating old items."""
        # Add items
        manager.add("old-1", "Old content", ContextType.USER_INPUT)
        manager.add("new-1", "New content", ContextType.USER_INPUT)

        # Deactivate items older than now (should deactivate all)
        future = datetime(2099, 1, 1).isoformat()
        manager.deactivate_old(future)

        # All items should be inactive
        for item in manager:
            assert item.is_active is False

    def test_concurrent_like_modifications(self, manager):
        """Test behavior with many rapid modifications."""
        # Add items
        ids = []
        for i in range(100):
            item = manager.add(f"item-{i}", f"Content {i}", ContextType.GENERATED_CODE)
            ids.append(item.id)

        # Remove half
        for item_id in ids[::2]:
            manager.remove(item_id)

        # Should have roughly half remaining
        assert len(manager) == 50
