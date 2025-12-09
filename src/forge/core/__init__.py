"""
Core components for Forge

Provides configuration, state management, orchestration, context handling,
streaming output support, caching for incremental builds, and resilience patterns.
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
from forge.core.resilience import (
    ResilienceError,
    RetryExhaustedError,
    CircuitOpenError,
    CheckpointError,
    ErrorCategory,
    ClassifiedError,
    ErrorClassifier,
    RetryStrategy,
    RetryConfig,
    RetryCalculator,
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreaker,
    Checkpoint,
    CheckpointManager,
    ResilientExecutor,
    CircuitBreakerRegistry,
    circuit_registry,
    with_retry,
    with_circuit_breaker,
    with_fallback
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
    # Resilience
    'ResilienceError',
    'RetryExhaustedError',
    'CircuitOpenError',
    'CheckpointError',
    'ErrorCategory',
    'ClassifiedError',
    'ErrorClassifier',
    'RetryStrategy',
    'RetryConfig',
    'RetryCalculator',
    'CircuitState',
    'CircuitBreakerConfig',
    'CircuitBreaker',
    'Checkpoint',
    'CheckpointManager',
    'ResilientExecutor',
    'CircuitBreakerRegistry',
    'circuit_registry',
    'with_retry',
    'with_circuit_breaker',
    'with_fallback',
]
