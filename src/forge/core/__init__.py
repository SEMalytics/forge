"""
Core components for Forge

Provides configuration, state management, orchestration, context handling,
streaming output support, and caching for incremental builds.
"""

from forge.core.config import ForgeConfig
from forge.core.state_manager import StateManager
from forge.core.context import ContextManager, ContextItem, ContextType, ContextWindow, ContextError
from forge.core.streaming import (
    StreamEventType,
    StreamEvent,
    StreamEmitter,
    StreamHandler,
    ProgressState,
    ProgressTracker,
    ConsoleStreamHandler,
    BufferStreamHandler,
    CallbackStreamHandler
)
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

__all__ = [
    # Config
    'ForgeConfig',
    'StateManager',
    # Context
    'ContextManager',
    'ContextItem',
    'ContextType',
    'ContextWindow',
    'ContextError',
    # Streaming
    'StreamEventType',
    'StreamEvent',
    'StreamEmitter',
    'StreamHandler',
    'ProgressState',
    'ProgressTracker',
    'ConsoleStreamHandler',
    'BufferStreamHandler',
    'CallbackStreamHandler',
    # Cache
    'CacheError',
    'CacheStatus',
    'CacheEntry',
    'CacheLookupResult',
    'CacheKeyBuilder',
    'GenerationCache',
    'IncrementalBuildDetector',
    'CachedGenerator',
]
