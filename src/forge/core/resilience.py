"""
Enhanced Error Recovery & Retry Logic for Forge

Provides resilient execution patterns including:
- Retry strategies with exponential backoff and jitter
- Circuit breaker pattern to prevent cascading failures
- Checkpointing for resumable operations
- Error classification for appropriate handling
- Graceful degradation with fallback options
"""

import asyncio
import functools
import hashlib
import json
import random
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    TypeVar,
    Union,
)

from forge.utils.logger import logger


class ResilienceError(Exception):
    """Base exception for resilience-related errors."""
    pass


class RetryExhaustedError(ResilienceError):
    """All retry attempts have been exhausted."""

    def __init__(self, message: str, last_error: Optional[Exception] = None, attempts: int = 0):
        super().__init__(message)
        self.last_error = last_error
        self.attempts = attempts


class CircuitOpenError(ResilienceError):
    """Circuit breaker is open, operation not allowed."""

    def __init__(self, message: str, reset_time: Optional[datetime] = None):
        super().__init__(message)
        self.reset_time = reset_time


class CheckpointError(ResilienceError):
    """Error related to checkpoint operations."""
    pass


# =============================================================================
# Error Classification
# =============================================================================

class ErrorCategory(Enum):
    """Categories of errors for handling decisions."""
    TRANSIENT = "transient"          # Temporary, worth retrying (network, rate limit)
    PERMANENT = "permanent"          # Won't succeed on retry (auth, validation)
    RESOURCE = "resource"            # Resource exhaustion (memory, disk)
    TIMEOUT = "timeout"              # Operation timed out
    UNKNOWN = "unknown"              # Unclassified error


@dataclass
class ClassifiedError:
    """An error with classification metadata."""
    original_error: Exception
    category: ErrorCategory
    is_retryable: bool
    suggested_delay: float = 0.0
    message: str = ""

    def __post_init__(self):
        if not self.message:
            self.message = str(self.original_error)


class ErrorClassifier:
    """
    Classifies errors to determine appropriate handling.

    Uses pattern matching on error types and messages to categorize
    errors and determine retry eligibility.
    """

    # Error patterns mapped to categories
    TRANSIENT_PATTERNS = [
        "rate limit",
        "too many requests",
        "429",
        "503",
        "502",
        "504",
        "connection reset",
        "connection refused",
        "temporary",
        "temporarily unavailable",
        "try again",
        "overloaded",
        "capacity",
    ]

    PERMANENT_PATTERNS = [
        "401",
        "403",
        "404",
        "invalid api key",
        "authentication",
        "authorization",
        "permission denied",
        "not found",
        "invalid",
        "malformed",
        "bad request",
        "400",
    ]

    TIMEOUT_PATTERNS = [
        "timeout",
        "timed out",
        "deadline exceeded",
        "took too long",
    ]

    RESOURCE_PATTERNS = [
        "out of memory",
        "memory error",
        "disk full",
        "no space",
        "resource exhausted",
        "quota exceeded",
    ]

    # Exception types that are typically transient
    TRANSIENT_EXCEPTIONS = (
        ConnectionError,
        ConnectionResetError,
        ConnectionRefusedError,
        TimeoutError,
        asyncio.TimeoutError,
    )

    @classmethod
    def classify(cls, error: Exception) -> ClassifiedError:
        """
        Classify an error and determine handling strategy.

        Args:
            error: The exception to classify

        Returns:
            ClassifiedError with category and retry info
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Check for transient exception types
        if isinstance(error, cls.TRANSIENT_EXCEPTIONS):
            return ClassifiedError(
                original_error=error,
                category=ErrorCategory.TRANSIENT,
                is_retryable=True,
                suggested_delay=1.0,
                message=f"Transient error ({error_type}): {error}"
            )

        # Check timeout patterns
        if any(p in error_str for p in cls.TIMEOUT_PATTERNS):
            return ClassifiedError(
                original_error=error,
                category=ErrorCategory.TIMEOUT,
                is_retryable=True,
                suggested_delay=2.0,
                message=f"Timeout error: {error}"
            )

        # Check resource patterns
        if any(p in error_str for p in cls.RESOURCE_PATTERNS):
            return ClassifiedError(
                original_error=error,
                category=ErrorCategory.RESOURCE,
                is_retryable=False,
                message=f"Resource error: {error}"
            )

        # Check permanent patterns
        if any(p in error_str for p in cls.PERMANENT_PATTERNS):
            return ClassifiedError(
                original_error=error,
                category=ErrorCategory.PERMANENT,
                is_retryable=False,
                message=f"Permanent error: {error}"
            )

        # Check transient patterns (rate limits get longer delays)
        for pattern in cls.TRANSIENT_PATTERNS:
            if pattern in error_str:
                delay = 5.0 if "rate limit" in error_str or "429" in error_str else 1.0
                return ClassifiedError(
                    original_error=error,
                    category=ErrorCategory.TRANSIENT,
                    is_retryable=True,
                    suggested_delay=delay,
                    message=f"Transient error: {error}"
                )

        # Default to unknown but retryable (conservative)
        return ClassifiedError(
            original_error=error,
            category=ErrorCategory.UNKNOWN,
            is_retryable=True,
            suggested_delay=1.0,
            message=f"Unknown error ({error_type}): {error}"
        )


# =============================================================================
# Retry Strategies
# =============================================================================

class RetryStrategy(Enum):
    """Available retry strategies."""
    FIXED = "fixed"                    # Fixed delay between retries
    LINEAR = "linear"                  # Linearly increasing delay
    EXPONENTIAL = "exponential"        # Exponential backoff
    EXPONENTIAL_JITTER = "exponential_jitter"  # Exponential with random jitter


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER
    base_delay: float = 1.0           # Base delay in seconds
    max_delay: float = 60.0           # Maximum delay cap
    jitter_factor: float = 0.5        # Random jitter range (0-1)
    retry_on: Optional[Set[ErrorCategory]] = None  # Categories to retry

    def __post_init__(self):
        if self.retry_on is None:
            self.retry_on = {ErrorCategory.TRANSIENT, ErrorCategory.TIMEOUT, ErrorCategory.UNKNOWN}


class RetryCalculator:
    """Calculates retry delays based on strategy."""

    @staticmethod
    def calculate_delay(
        config: RetryConfig,
        attempt: int,
        classified_error: Optional[ClassifiedError] = None
    ) -> float:
        """
        Calculate delay before next retry attempt.

        Args:
            config: Retry configuration
            attempt: Current attempt number (1-based)
            classified_error: Optional classified error for hints

        Returns:
            Delay in seconds
        """
        # Use error's suggested delay as minimum if available
        base = config.base_delay
        if classified_error and classified_error.suggested_delay > base:
            base = classified_error.suggested_delay

        if config.strategy == RetryStrategy.FIXED:
            delay = base

        elif config.strategy == RetryStrategy.LINEAR:
            delay = base * attempt

        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = base * (2 ** (attempt - 1))

        elif config.strategy == RetryStrategy.EXPONENTIAL_JITTER:
            exp_delay = base * (2 ** (attempt - 1))
            jitter = random.uniform(0, config.jitter_factor * exp_delay)
            delay = exp_delay + jitter

        else:
            delay = base

        return min(delay, config.max_delay)


@dataclass
class RetryState:
    """Tracks state across retry attempts."""
    attempt: int = 0
    total_delay: float = 0.0
    errors: List[ClassifiedError] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)

    @property
    def elapsed_seconds(self) -> float:
        """Get total elapsed time."""
        return (datetime.now() - self.started_at).total_seconds()

    def record_error(self, error: ClassifiedError, delay: float) -> None:
        """Record an error and delay."""
        self.errors.append(error)
        self.total_delay += delay


# =============================================================================
# Circuit Breaker
# =============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests allowed
    OPEN = "open"          # Failures exceeded threshold, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5        # Failures before opening
    success_threshold: int = 2        # Successes in half-open before closing
    reset_timeout: float = 30.0       # Seconds before half-open from open
    half_open_max_calls: int = 3      # Max concurrent calls in half-open


@dataclass
class CircuitStats:
    """Statistics for circuit breaker."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    Tracks failures and temporarily blocks requests when a service
    appears to be failing, allowing it time to recover.
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Identifier for this circuit
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0
        self._stats = CircuitStats()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def stats(self) -> CircuitStats:
        """Get circuit statistics."""
        return self._stats

    def _should_reset(self) -> bool:
        """Check if circuit should transition to half-open."""
        if self._state != CircuitState.OPEN:
            return False

        if self._last_failure_time is None:
            return True

        elapsed = (datetime.now() - self._last_failure_time).total_seconds()
        return elapsed >= self.config.reset_timeout

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        if self._state != new_state:
            logger.info(
                f"Circuit '{self.name}' transitioning: {self._state.value} -> {new_state.value}"
            )
            self._state = new_state
            self._stats.state_changes += 1

            if new_state == CircuitState.CLOSED:
                self._failure_count = 0
                self._success_count = 0
            elif new_state == CircuitState.HALF_OPEN:
                self._half_open_calls = 0
                self._success_count = 0

    async def allow_request(self) -> bool:
        """
        Check if a request should be allowed.

        Returns:
            True if request is allowed

        Raises:
            CircuitOpenError: If circuit is open
        """
        async with self._lock:
            # Check for reset timeout
            if self._should_reset():
                self._transition_to(CircuitState.HALF_OPEN)

            if self._state == CircuitState.CLOSED:
                return True

            elif self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                else:
                    self._stats.rejected_calls += 1
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' half-open, max test calls reached"
                    )

            else:  # OPEN
                self._stats.rejected_calls += 1
                reset_time = None
                if self._last_failure_time:
                    reset_time = self._last_failure_time + timedelta(
                        seconds=self.config.reset_timeout
                    )
                raise CircuitOpenError(
                    f"Circuit '{self.name}' is open",
                    reset_time=reset_time
                )

    async def record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            self._stats.total_calls += 1
            self._stats.successful_calls += 1
            self._stats.last_success_time = datetime.now()

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)

    async def record_failure(self, error: Optional[Exception] = None) -> None:
        """Record a failed call."""
        async with self._lock:
            self._stats.total_calls += 1
            self._stats.failed_calls += 1
            self._stats.last_failure_time = datetime.now()
            self._last_failure_time = datetime.now()

            if self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

            elif self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open returns to open
                self._transition_to(CircuitState.OPEN)

    def reset(self) -> None:
        """Manually reset circuit to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        logger.info(f"Circuit '{self.name}' manually reset to CLOSED")


# =============================================================================
# Checkpoint Manager
# =============================================================================

@dataclass
class Checkpoint:
    """A saved checkpoint of operation state."""
    checkpoint_id: str
    operation_id: str
    stage: str
    state: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "operation_id": self.operation_id,
            "stage": self.stage,
            "state": self.state,
            "created_at": self.created_at,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        """Create from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            operation_id=data["operation_id"],
            stage=data["stage"],
            state=data["state"],
            created_at=data.get("created_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )


class CheckpointManager:
    """
    Manages checkpoints for resumable operations.

    Saves operation state to disk for recovery after failures,
    enabling operations to resume from where they left off.
    """

    def __init__(
        self,
        checkpoint_dir: Optional[Path] = None,
        max_checkpoints_per_operation: int = 10
    ):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoint storage
            max_checkpoints_per_operation: Max checkpoints to keep per operation
        """
        self.checkpoint_dir = checkpoint_dir or Path(".forge/checkpoints")
        self.max_checkpoints = max_checkpoints_per_operation
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _operation_dir(self, operation_id: str) -> Path:
        """Get directory for operation checkpoints."""
        # Sanitize operation_id for filesystem
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in operation_id)
        return self.checkpoint_dir / safe_id

    def _generate_checkpoint_id(self, operation_id: str, stage: str) -> str:
        """Generate unique checkpoint ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        content = f"{operation_id}:{stage}:{timestamp}"
        hash_suffix = hashlib.sha256(content.encode()).hexdigest()[:8]
        return f"{stage}_{timestamp}_{hash_suffix}"

    def save(
        self,
        operation_id: str,
        stage: str,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Checkpoint:
        """
        Save a checkpoint.

        Args:
            operation_id: Unique operation identifier
            stage: Current stage/step name
            state: State data to checkpoint
            metadata: Optional metadata

        Returns:
            Created checkpoint
        """
        checkpoint_id = self._generate_checkpoint_id(operation_id, stage)

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            operation_id=operation_id,
            stage=stage,
            state=state,
            metadata=metadata or {}
        )

        # Ensure operation directory exists
        op_dir = self._operation_dir(operation_id)
        op_dir.mkdir(parents=True, exist_ok=True)

        # Save checkpoint
        checkpoint_path = op_dir / f"{checkpoint_id}.json"
        checkpoint_path.write_text(json.dumps(checkpoint.to_dict(), indent=2))

        # Cleanup old checkpoints
        self._cleanup_old_checkpoints(operation_id)

        logger.debug(f"Saved checkpoint {checkpoint_id} for {operation_id}")
        return checkpoint

    def load_latest(self, operation_id: str) -> Optional[Checkpoint]:
        """
        Load the latest checkpoint for an operation.

        Args:
            operation_id: Operation identifier

        Returns:
            Latest checkpoint or None
        """
        op_dir = self._operation_dir(operation_id)

        if not op_dir.exists():
            return None

        checkpoints = list(op_dir.glob("*.json"))
        if not checkpoints:
            return None

        # Sort by modification time, newest first
        checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        try:
            data = json.loads(checkpoints[0].read_text())
            return Checkpoint.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None

    def load_by_stage(self, operation_id: str, stage: str) -> Optional[Checkpoint]:
        """
        Load the latest checkpoint for a specific stage.

        Args:
            operation_id: Operation identifier
            stage: Stage name

        Returns:
            Checkpoint for stage or None
        """
        op_dir = self._operation_dir(operation_id)

        if not op_dir.exists():
            return None

        # Find checkpoints for this stage
        checkpoints = list(op_dir.glob(f"{stage}_*.json"))
        if not checkpoints:
            return None

        checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        try:
            data = json.loads(checkpoints[0].read_text())
            return Checkpoint.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None

    def list_checkpoints(self, operation_id: str) -> List[Checkpoint]:
        """
        List all checkpoints for an operation.

        Args:
            operation_id: Operation identifier

        Returns:
            List of checkpoints, newest first
        """
        op_dir = self._operation_dir(operation_id)

        if not op_dir.exists():
            return []

        checkpoints = []
        for path in sorted(op_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(path.read_text())
                checkpoints.append(Checkpoint.from_dict(data))
            except Exception:
                continue

        return checkpoints

    def delete_checkpoints(self, operation_id: str) -> int:
        """
        Delete all checkpoints for an operation.

        Args:
            operation_id: Operation identifier

        Returns:
            Number of checkpoints deleted
        """
        op_dir = self._operation_dir(operation_id)

        if not op_dir.exists():
            return 0

        count = 0
        for path in op_dir.glob("*.json"):
            path.unlink()
            count += 1

        # Remove directory if empty
        try:
            op_dir.rmdir()
        except OSError:
            pass

        return count

    def _cleanup_old_checkpoints(self, operation_id: str) -> None:
        """Remove old checkpoints exceeding max limit."""
        op_dir = self._operation_dir(operation_id)

        checkpoints = list(op_dir.glob("*.json"))
        if len(checkpoints) <= self.max_checkpoints:
            return

        # Sort by modification time, oldest first
        checkpoints.sort(key=lambda p: p.stat().st_mtime)

        # Delete oldest checkpoints
        to_delete = len(checkpoints) - self.max_checkpoints
        for path in checkpoints[:to_delete]:
            path.unlink()
            logger.debug(f"Cleaned up old checkpoint: {path.name}")


# =============================================================================
# Resilient Executor
# =============================================================================

T = TypeVar('T')


class ResilientExecutor:
    """
    Executes operations with retry, circuit breaker, and checkpoint support.

    Combines all resilience patterns into a unified executor that handles
    failures gracefully and provides recovery capabilities.
    """

    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        checkpoint_manager: Optional[CheckpointManager] = None
    ):
        """
        Initialize resilient executor.

        Args:
            retry_config: Retry configuration
            circuit_breaker: Circuit breaker instance
            checkpoint_manager: Checkpoint manager instance
        """
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = circuit_breaker
        self.checkpoint_manager = checkpoint_manager

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_id: Optional[str] = None,
        stage: Optional[str] = None,
        fallback: Optional[Callable[[], Awaitable[T]]] = None,
        on_retry: Optional[Callable[[int, ClassifiedError], Awaitable[None]]] = None
    ) -> T:
        """
        Execute an operation with resilience patterns.

        Args:
            operation: Async callable to execute
            operation_id: Optional ID for checkpointing
            stage: Optional stage name for checkpointing
            fallback: Optional fallback operation if all retries fail
            on_retry: Optional callback on retry (attempt, error)

        Returns:
            Operation result

        Raises:
            RetryExhaustedError: If all retries fail and no fallback
            CircuitOpenError: If circuit breaker is open
        """
        retry_state = RetryState()

        while retry_state.attempt < self.retry_config.max_attempts:
            retry_state.attempt += 1

            try:
                # Check circuit breaker
                if self.circuit_breaker:
                    await self.circuit_breaker.allow_request()

                # Execute operation
                result = await operation()

                # Record success
                if self.circuit_breaker:
                    await self.circuit_breaker.record_success()

                # Save checkpoint on success
                if self.checkpoint_manager and operation_id and stage:
                    self.checkpoint_manager.save(
                        operation_id=operation_id,
                        stage=stage,
                        state={"completed": True, "attempts": retry_state.attempt},
                        metadata={"elapsed": retry_state.elapsed_seconds}
                    )

                return result

            except CircuitOpenError:
                # Don't retry circuit breaker errors
                raise

            except Exception as e:
                # Classify error
                classified = ErrorClassifier.classify(e)

                # Record failure with circuit breaker
                if self.circuit_breaker:
                    await self.circuit_breaker.record_failure(e)

                # Check if retryable
                if not classified.is_retryable:
                    logger.warning(f"Non-retryable error: {classified.message}")
                    raise

                if classified.category not in self.retry_config.retry_on:
                    logger.warning(f"Error category {classified.category} not in retry set")
                    raise

                # Calculate delay
                delay = RetryCalculator.calculate_delay(
                    self.retry_config,
                    retry_state.attempt,
                    classified
                )

                retry_state.record_error(classified, delay)

                # Check if we have retries left
                if retry_state.attempt >= self.retry_config.max_attempts:
                    break

                # Notify retry callback
                if on_retry:
                    await on_retry(retry_state.attempt, classified)

                logger.info(
                    f"Retry {retry_state.attempt}/{self.retry_config.max_attempts} "
                    f"after {delay:.1f}s: {classified.message}"
                )

                # Wait before retry
                await asyncio.sleep(delay)

        # All retries exhausted
        last_error = retry_state.errors[-1] if retry_state.errors else None

        # Try fallback
        if fallback:
            logger.info("Attempting fallback operation")
            try:
                return await fallback()
            except Exception as fb_error:
                logger.error(f"Fallback also failed: {fb_error}")

        raise RetryExhaustedError(
            f"Operation failed after {retry_state.attempt} attempts",
            last_error=last_error.original_error if last_error else None,
            attempts=retry_state.attempt
        )

    def execute_sync(
        self,
        operation: Callable[[], T],
        operation_id: Optional[str] = None,
        stage: Optional[str] = None,
        fallback: Optional[Callable[[], T]] = None,
        on_retry: Optional[Callable[[int, ClassifiedError], None]] = None
    ) -> T:
        """
        Execute a synchronous operation with resilience patterns.

        Args:
            operation: Sync callable to execute
            operation_id: Optional ID for checkpointing
            stage: Optional stage name for checkpointing
            fallback: Optional fallback operation if all retries fail
            on_retry: Optional callback on retry (attempt, error)

        Returns:
            Operation result
        """
        retry_state = RetryState()

        while retry_state.attempt < self.retry_config.max_attempts:
            retry_state.attempt += 1

            try:
                result = operation()

                # Save checkpoint on success
                if self.checkpoint_manager and operation_id and stage:
                    self.checkpoint_manager.save(
                        operation_id=operation_id,
                        stage=stage,
                        state={"completed": True, "attempts": retry_state.attempt}
                    )

                return result

            except Exception as e:
                classified = ErrorClassifier.classify(e)

                if not classified.is_retryable:
                    raise

                if classified.category not in self.retry_config.retry_on:
                    raise

                delay = RetryCalculator.calculate_delay(
                    self.retry_config,
                    retry_state.attempt,
                    classified
                )

                retry_state.record_error(classified, delay)

                if retry_state.attempt >= self.retry_config.max_attempts:
                    break

                if on_retry:
                    on_retry(retry_state.attempt, classified)

                logger.info(
                    f"Retry {retry_state.attempt}/{self.retry_config.max_attempts} "
                    f"after {delay:.1f}s"
                )

                time.sleep(delay)

        # All retries exhausted
        last_error = retry_state.errors[-1] if retry_state.errors else None

        if fallback:
            try:
                return fallback()
            except Exception:
                pass

        raise RetryExhaustedError(
            f"Operation failed after {retry_state.attempt} attempts",
            last_error=last_error.original_error if last_error else None,
            attempts=retry_state.attempt
        )


# =============================================================================
# Decorators
# =============================================================================

def with_retry(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> Callable:
    """
    Decorator to add retry logic to a function.

    Args:
        max_attempts: Maximum retry attempts
        strategy: Retry strategy to use
        base_delay: Base delay between retries
        max_delay: Maximum delay cap

    Returns:
        Decorated function
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        strategy=strategy,
        base_delay=base_delay,
        max_delay=max_delay
    )

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                executor = ResilientExecutor(retry_config=config)
                return await executor.execute(lambda: func(*args, **kwargs))
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                executor = ResilientExecutor(retry_config=config)
                return executor.execute_sync(lambda: func(*args, **kwargs))
            return sync_wrapper

    return decorator


def with_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    reset_timeout: float = 30.0
) -> Callable:
    """
    Decorator to add circuit breaker to a function.

    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening
        reset_timeout: Seconds before testing recovery

    Returns:
        Decorated function
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        reset_timeout=reset_timeout
    )
    circuit = CircuitBreaker(name, config)

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                await circuit.allow_request()
                try:
                    result = await func(*args, **kwargs)
                    await circuit.record_success()
                    return result
                except Exception as e:
                    await circuit.record_failure(e)
                    raise
            return async_wrapper
        else:
            raise ValueError("Circuit breaker decorator only supports async functions")

    return decorator


def with_fallback(
    fallback_func: Callable,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator to provide fallback on failure.

    Args:
        fallback_func: Function to call on failure
        exceptions: Exception types to catch

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"Falling back due to: {e}")
                    if asyncio.iscoroutinefunction(fallback_func):
                        return await fallback_func(*args, **kwargs)
                    return fallback_func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"Falling back due to: {e}")
                    return fallback_func(*args, **kwargs)
            return sync_wrapper

    return decorator


# =============================================================================
# Circuit Breaker Registry
# =============================================================================

class CircuitBreakerRegistry:
    """
    Global registry for circuit breakers.

    Allows sharing circuit breakers across different parts of the application.
    """

    _instance: Optional['CircuitBreakerRegistry'] = None
    _circuits: Dict[str, CircuitBreaker] = {}

    def __new__(cls) -> 'CircuitBreakerRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._circuits = {}
        return cls._instance

    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Get existing or create new circuit breaker.

        Args:
            name: Circuit breaker name
            config: Optional configuration for new circuit

        Returns:
            Circuit breaker instance
        """
        if name not in self._circuits:
            self._circuits[name] = CircuitBreaker(name, config)
        return self._circuits[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self._circuits.get(name)

    def list_circuits(self) -> Dict[str, CircuitBreaker]:
        """Get all registered circuits."""
        return dict(self._circuits)

    def reset_all(self) -> None:
        """Reset all circuits to closed state."""
        for circuit in self._circuits.values():
            circuit.reset()

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all circuits."""
        return {
            name: {
                "state": circuit.state.value,
                "total_calls": circuit.stats.total_calls,
                "successful": circuit.stats.successful_calls,
                "failed": circuit.stats.failed_calls,
                "rejected": circuit.stats.rejected_calls
            }
            for name, circuit in self._circuits.items()
        }


# Global registry instance
circuit_registry = CircuitBreakerRegistry()
