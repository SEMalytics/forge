"""
Context Manager for Forge

Provides context cascading and management for multi-stage generation.
Allows documents and specifications to build on each other, passing
refined context through the generation pipeline.

Key Features:
- Context storage with metadata and relationships
- Automatic summarization for large contexts
- Reference tracking between context items
- Token-aware context windowing
- Persistence and recovery
"""

import json
import hashlib
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from enum import Enum

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class ContextError(ForgeError):
    """Context management errors"""
    pass


class ContextType(Enum):
    """Types of context items"""
    SPECIFICATION = "specification"
    ARCHITECTURE = "architecture"
    GENERATED_CODE = "generated_code"
    TEST_RESULT = "test_result"
    REVIEW_FEEDBACK = "review_feedback"
    USER_INPUT = "user_input"
    SYSTEM = "system"
    SUMMARY = "summary"


@dataclass
class ContextItem:
    """A single context item with metadata"""
    id: str
    content: str
    context_type: ContextType
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Relationships
    references: List[str] = field(default_factory=list)  # IDs of referenced items
    referenced_by: List[str] = field(default_factory=list)  # IDs that reference this

    # Metadata
    summary: Optional[str] = None
    token_count: Optional[int] = None
    source: Optional[str] = None  # e.g., "task-001", "user", "system"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # State
    is_active: bool = True  # Whether to include in context windows
    priority: int = 0  # Higher priority = more likely to be included

    @property
    def content_hash(self) -> str:
        """Get hash of content for change detection"""
        return hashlib.md5(self.content.encode()).hexdigest()[:12]

    @property
    def effective_content(self) -> str:
        """Get content to use (summary if available and content is large)"""
        if self.summary and self.token_count and self.token_count > 500:
            return self.summary
        return self.content

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'content': self.content,
            'context_type': self.context_type.value,
            'created_at': self.created_at,
            'references': self.references,
            'referenced_by': self.referenced_by,
            'summary': self.summary,
            'token_count': self.token_count,
            'source': self.source,
            'tags': self.tags,
            'metadata': self.metadata,
            'is_active': self.is_active,
            'priority': self.priority
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextItem':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            content=data['content'],
            context_type=ContextType(data['context_type']),
            created_at=data.get('created_at', datetime.now().isoformat()),
            references=data.get('references', []),
            referenced_by=data.get('referenced_by', []),
            summary=data.get('summary'),
            token_count=data.get('token_count'),
            source=data.get('source'),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            is_active=data.get('is_active', True),
            priority=data.get('priority', 0)
        )


@dataclass
class ContextWindow:
    """A window of context items for a specific purpose"""
    items: List[ContextItem]
    total_tokens: int
    max_tokens: int
    truncated: bool = False
    excluded_ids: List[str] = field(default_factory=list)

    def to_prompt(self, include_metadata: bool = False) -> str:
        """Format context window as prompt text"""
        parts = []

        for item in self.items:
            if include_metadata:
                header = f"## {item.id} ({item.context_type.value})"
                if item.source:
                    header += f" [source: {item.source}]"
                parts.append(header)

            parts.append(item.effective_content)
            parts.append("")  # Blank line between items

        return "\n".join(parts)


class ContextManager:
    """
    Manages context for multi-stage code generation.

    Features:
    - Store and retrieve context items
    - Track references between items
    - Automatic summarization for large content
    - Token-aware context windowing
    - Persistence to disk
    """

    def __init__(
        self,
        max_tokens: int = 8000,
        auto_summarize_threshold: int = 1000,
        storage_path: Optional[Path] = None
    ):
        """
        Initialize context manager.

        Args:
            max_tokens: Maximum tokens for context windows
            auto_summarize_threshold: Token count above which to auto-summarize
            storage_path: Path for context persistence
        """
        self.max_tokens = max_tokens
        self.auto_summarize_threshold = auto_summarize_threshold
        self.storage_path = storage_path or Path(".forge/context")

        self._items: Dict[str, ContextItem] = {}
        self._summarizer: Optional[Any] = None  # Lazy-loaded summarizer

        logger.info(f"Initialized ContextManager (max_tokens={max_tokens})")

    def add(
        self,
        id: str,
        content: str,
        context_type: Union[ContextType, str] = ContextType.USER_INPUT,
        references: Optional[List[str]] = None,
        source: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: int = 0,
        summarize: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextItem:
        """
        Add a context item.

        Args:
            id: Unique identifier for this context
            content: The content to store
            context_type: Type of context
            references: IDs of other context items this references
            source: Source identifier (e.g., task ID)
            tags: Tags for filtering
            priority: Priority for inclusion in windows
            summarize: Whether to generate a summary
            metadata: Additional metadata

        Returns:
            The created ContextItem
        """
        # Convert string type to enum
        if isinstance(context_type, str):
            context_type = ContextType(context_type)

        # Estimate token count
        token_count = self._estimate_tokens(content)

        # Create item
        item = ContextItem(
            id=id,
            content=content,
            context_type=context_type,
            references=references or [],
            source=source,
            tags=tags or [],
            priority=priority,
            token_count=token_count,
            metadata=metadata or {}
        )

        # Update reference tracking
        for ref_id in item.references:
            if ref_id in self._items:
                self._items[ref_id].referenced_by.append(id)

        # Generate summary if requested or content is large
        if summarize or token_count > self.auto_summarize_threshold:
            item.summary = self._generate_summary(content)

        # Store item
        self._items[id] = item

        logger.debug(f"Added context item: {id} ({token_count} tokens)")

        return item

    def get(self, id: str) -> Optional[ContextItem]:
        """Get a context item by ID"""
        return self._items.get(id)

    def remove(self, id: str) -> bool:
        """
        Remove a context item.

        Args:
            id: Item ID to remove

        Returns:
            True if removed, False if not found
        """
        if id not in self._items:
            return False

        item = self._items[id]

        # Update reference tracking
        for ref_id in item.references:
            if ref_id in self._items:
                self._items[ref_id].referenced_by.remove(id)

        for ref_by_id in item.referenced_by:
            if ref_by_id in self._items:
                self._items[ref_by_id].references.remove(id)

        del self._items[id]
        logger.debug(f"Removed context item: {id}")

        return True

    def update(
        self,
        id: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        is_active: Optional[bool] = None,
        priority: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ContextItem]:
        """
        Update a context item.

        Args:
            id: Item ID to update
            content: New content (optional)
            summary: New summary (optional)
            is_active: New active state (optional)
            priority: New priority (optional)
            tags: New tags (optional)
            metadata: Additional metadata to merge (optional)

        Returns:
            Updated item or None if not found
        """
        item = self._items.get(id)
        if not item:
            return None

        if content is not None:
            item.content = content
            item.token_count = self._estimate_tokens(content)

        if summary is not None:
            item.summary = summary

        if is_active is not None:
            item.is_active = is_active

        if priority is not None:
            item.priority = priority

        if tags is not None:
            item.tags = tags

        if metadata is not None:
            item.metadata.update(metadata)

        return item

    def get_context_for(
        self,
        target_id: str,
        include_references: bool = True,
        include_type: Optional[List[ContextType]] = None,
        exclude_type: Optional[List[ContextType]] = None,
        max_tokens: Optional[int] = None
    ) -> ContextWindow:
        """
        Get context window for a specific target.

        Builds a context window that includes relevant items for the target,
        respecting token limits and priorities.

        Args:
            target_id: Target to get context for (e.g., task ID)
            include_references: Include items referenced by target
            include_type: Only include these types
            exclude_type: Exclude these types
            max_tokens: Override max tokens for this window

        Returns:
            ContextWindow with relevant items
        """
        max_tokens = max_tokens or self.max_tokens

        # Collect candidate items
        candidates = []

        for item in self._items.values():
            if not item.is_active:
                continue

            # Type filtering
            if include_type and item.context_type not in include_type:
                continue
            if exclude_type and item.context_type in exclude_type:
                continue

            # Check if item is relevant to target
            relevance_score = self._calculate_relevance(item, target_id, include_references)

            if relevance_score > 0:
                candidates.append((item, relevance_score))

        # Sort by relevance (descending) then priority (descending)
        candidates.sort(key=lambda x: (x[1], x[0].priority), reverse=True)

        # Build window within token limit
        window_items = []
        total_tokens = 0
        excluded_ids = []

        for item, _ in candidates:
            item_tokens = item.token_count or self._estimate_tokens(item.effective_content)

            if total_tokens + item_tokens <= max_tokens:
                window_items.append(item)
                total_tokens += item_tokens
            else:
                excluded_ids.append(item.id)

        return ContextWindow(
            items=window_items,
            total_tokens=total_tokens,
            max_tokens=max_tokens,
            truncated=len(excluded_ids) > 0,
            excluded_ids=excluded_ids
        )

    def get_all_context(
        self,
        include_type: Optional[List[ContextType]] = None,
        exclude_type: Optional[List[ContextType]] = None,
        active_only: bool = True,
        max_tokens: Optional[int] = None
    ) -> ContextWindow:
        """
        Get all context as a window.

        Args:
            include_type: Only include these types
            exclude_type: Exclude these types
            active_only: Only include active items
            max_tokens: Token limit

        Returns:
            ContextWindow with all matching items
        """
        max_tokens = max_tokens or self.max_tokens

        candidates = []

        for item in self._items.values():
            if active_only and not item.is_active:
                continue

            if include_type and item.context_type not in include_type:
                continue
            if exclude_type and item.context_type in exclude_type:
                continue

            candidates.append(item)

        # Sort by priority (descending), then creation time (ascending)
        candidates.sort(key=lambda x: (-x.priority, x.created_at))

        # Build window
        window_items = []
        total_tokens = 0
        excluded_ids = []

        for item in candidates:
            item_tokens = item.token_count or self._estimate_tokens(item.effective_content)

            if total_tokens + item_tokens <= max_tokens:
                window_items.append(item)
                total_tokens += item_tokens
            else:
                excluded_ids.append(item.id)

        return ContextWindow(
            items=window_items,
            total_tokens=total_tokens,
            max_tokens=max_tokens,
            truncated=len(excluded_ids) > 0,
            excluded_ids=excluded_ids
        )

    def get_by_type(self, context_type: ContextType) -> List[ContextItem]:
        """Get all items of a specific type"""
        return [
            item for item in self._items.values()
            if item.context_type == context_type
        ]

    def get_by_tag(self, tag: str) -> List[ContextItem]:
        """Get all items with a specific tag"""
        return [
            item for item in self._items.values()
            if tag in item.tags
        ]

    def get_by_source(self, source: str) -> List[ContextItem]:
        """Get all items from a specific source"""
        return [
            item for item in self._items.values()
            if item.source == source
        ]

    def get_references(self, id: str) -> List[ContextItem]:
        """Get items that this item references"""
        item = self._items.get(id)
        if not item:
            return []

        return [
            self._items[ref_id]
            for ref_id in item.references
            if ref_id in self._items
        ]

    def get_referenced_by(self, id: str) -> List[ContextItem]:
        """Get items that reference this item"""
        item = self._items.get(id)
        if not item:
            return []

        return [
            self._items[ref_id]
            for ref_id in item.referenced_by
            if ref_id in self._items
        ]

    def summarize(self, id: str) -> Optional[str]:
        """
        Generate or regenerate summary for an item.

        Args:
            id: Item ID to summarize

        Returns:
            Generated summary or None if failed
        """
        item = self._items.get(id)
        if not item:
            return None

        summary = self._generate_summary(item.content)
        item.summary = summary

        return summary

    def clear(self):
        """Clear all context items"""
        self._items.clear()
        logger.info("Cleared all context items")

    def clear_by_type(self, context_type: ContextType):
        """Clear all items of a specific type"""
        ids_to_remove = [
            id for id, item in self._items.items()
            if item.context_type == context_type
        ]

        for id in ids_to_remove:
            self.remove(id)

        logger.info(f"Cleared {len(ids_to_remove)} items of type {context_type.value}")

    def deactivate_old(self, older_than: str):
        """
        Deactivate items older than specified datetime.

        Args:
            older_than: ISO datetime string
        """
        count = 0
        for item in self._items.values():
            if item.created_at < older_than:
                item.is_active = False
                count += 1

        logger.info(f"Deactivated {count} items older than {older_than}")

    def save(self, path: Optional[Path] = None):
        """
        Save context to disk.

        Args:
            path: Override storage path
        """
        path = path or self.storage_path
        path.mkdir(parents=True, exist_ok=True)

        data = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'max_tokens': self.max_tokens,
            'auto_summarize_threshold': self.auto_summarize_threshold,
            'items': {id: item.to_dict() for id, item in self._items.items()}
        }

        context_file = path / "context.json"
        context_file.write_text(json.dumps(data, indent=2))

        logger.info(f"Saved {len(self._items)} context items to {context_file}")

    def load(self, path: Optional[Path] = None) -> int:
        """
        Load context from disk.

        Args:
            path: Override storage path

        Returns:
            Number of items loaded
        """
        path = path or self.storage_path
        context_file = path / "context.json"

        if not context_file.exists():
            logger.warning(f"No context file found at {context_file}")
            return 0

        try:
            data = json.loads(context_file.read_text())

            self._items.clear()
            for id, item_data in data.get('items', {}).items():
                self._items[id] = ContextItem.from_dict(item_data)

            logger.info(f"Loaded {len(self._items)} context items from {context_file}")
            return len(self._items)

        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            raise ContextError(f"Failed to load context: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about current context"""
        type_counts = {}
        total_tokens = 0
        active_count = 0

        for item in self._items.values():
            type_name = item.context_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

            if item.token_count:
                total_tokens += item.token_count

            if item.is_active:
                active_count += 1

        return {
            'total_items': len(self._items),
            'active_items': active_count,
            'total_tokens': total_tokens,
            'types': type_counts,
            'max_tokens': self.max_tokens
        }

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Rough estimate: ~4 characters per token for English
        return len(text) // 4

    def _generate_summary(self, content: str, max_length: int = 500) -> str:
        """
        Generate summary for content.

        For now, uses simple extraction. Can be enhanced with LLM summarization.

        Args:
            content: Content to summarize
            max_length: Maximum summary length

        Returns:
            Summary string
        """
        # Simple extraction-based summary
        lines = content.strip().split('\n')

        # Try to find key sections
        summary_parts = []

        # Get first non-empty line as title/intro
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                summary_parts.append(line[:200])
                break

        # Look for section headers
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                summary_parts.append(line)
                if len('\n'.join(summary_parts)) > max_length:
                    break

        summary = '\n'.join(summary_parts)

        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        return summary

    def _calculate_relevance(
        self,
        item: ContextItem,
        target_id: str,
        include_references: bool
    ) -> float:
        """
        Calculate relevance score of item to target.

        Args:
            item: Context item to score
            target_id: Target identifier
            include_references: Whether to consider reference relationships

        Returns:
            Relevance score (0-1)
        """
        score = 0.0

        # Direct match
        if item.id == target_id:
            return 1.0

        # Source match
        if item.source == target_id:
            score += 0.8

        # Reference relationship
        if include_references:
            if target_id in item.references:
                score += 0.6
            if target_id in item.referenced_by:
                score += 0.5

        # Tag match (if target_id is in tags)
        if target_id in item.tags:
            score += 0.4

        # System and specification types are generally relevant
        if item.context_type in [ContextType.SYSTEM, ContextType.SPECIFICATION]:
            score += 0.3

        # Cap at 1.0
        return min(score, 1.0)

    def __len__(self) -> int:
        """Get number of context items"""
        return len(self._items)

    def __contains__(self, id: str) -> bool:
        """Check if item exists"""
        return id in self._items

    def __iter__(self):
        """Iterate over context items"""
        return iter(self._items.values())
