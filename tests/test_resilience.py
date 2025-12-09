"""
Tests for the resilience module.

Tests error classification, retry strategies, circuit breakers,
checkpoints, and resilient execution patterns.
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from forge.core.resilience import (
    ErrorCategory,
    ClassifiedError,
    ErrorClassifier,
    RetryStrategy,
    RetryConfig,
    RetryCalculator,
    RetryState,
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreaker,
    CircuitStats,
    Checkpoint,
    CheckpointManager,
    ResilientExecutor,
    CircuitBreakerRegistry,
    ResilienceError,
    RetryExhaustedError,
    CircuitOpenError,
    CheckpointError,
    with_retry,
    with_circuit_breaker,
    with_fallback,
)


# =============================================================================
# Error Classification Tests
# =============================================================================

class TestErrorClassifier:
    """Tests for ErrorClassifier."""

    def test_classify_connection_error(self):
        """Test connection errors are classified as transient."""
        error = ConnectionError("Connection refused")
        result = ErrorClassifier.classify(error)

        assert result.category == ErrorCategory.TRANSIENT
        assert result.is_retryable is True

    def test_classify_timeout_error(self):
        """Test timeout errors are classified correctly."""
        error = TimeoutError("Request timed out")
        result = ErrorClassifier.classify(error)

        assert result.category == ErrorCategory.TRANSIENT
        assert result.is_retryable is True

    def test_classify_rate_limit_error(self):
        """Test rate limit errors get longer delays."""
        error = Exception("429 Too Many Requests - rate limit exceeded")
        result = ErrorClassifier.classify(error)

        assert result.category == ErrorCategory.TRANSIENT
        assert result.is_retryable is True
        assert result.suggested_delay >= 5.0

    def test_classify_auth_error(self):
        """Test authentication errors are not retryable."""
        error = Exception("401 Unauthorized - Invalid API key")
        result = ErrorClassifier.classify(error)

        assert result.category == ErrorCategory.PERMANENT
        assert result.is_retryable is False

    def test_classify_not_found_error(self):
        """Test not found errors are not retryable."""
        error = Exception("404 Not Found")
        result = ErrorClassifier.classify(error)

        assert result.category == ErrorCategory.PERMANENT
        assert result.is_retryable is False

    def test_classify_resource_error(self):
        """Test resource errors are identified."""
        error = Exception("Out of memory error")
        result = ErrorClassifier.classify(error)

        assert result.category == ErrorCategory.RESOURCE
        assert result.is_retryable is False

    def test_classify_timeout_pattern(self):
        """Test timeout pattern in message."""
        error = Exception("Operation timed out after 30 seconds")
        result = ErrorClassifier.classify(error)

        assert result.category == ErrorCategory.TIMEOUT
        assert result.is_retryable is True

    def test_classify_unknown_error(self):
        """Test unknown errors default to retryable."""
        error = Exception("Something unexpected happened")
        result = ErrorClassifier.classify(error)

        assert result.category == ErrorCategory.UNKNOWN
        assert result.is_retryable is True

    def test_classify_503_service_unavailable(self):
        """Test 503 errors are transient."""
        error = Exception("503 Service Unavailable")
        result = ErrorClassifier.classify(error)

        assert result.category == ErrorCategory.TRANSIENT
        assert result.is_retryable is True


# =============================================================================
# Retry Strategy Tests
# =============================================================================

class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL_JITTER
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert ErrorCategory.TRANSIENT in config.retry_on

    def test_custom_config(self):
        """Test custom configuration."""
        config = RetryConfig(
            max_attempts=5,
            strategy=RetryStrategy.LINEAR,
            base_delay=2.0,
            max_delay=30.0
        )

        assert config.max_attempts == 5
        assert config.strategy == RetryStrategy.LINEAR
        assert config.base_delay == 2.0
        assert config.max_delay == 30.0


class TestRetryCalculator:
    """Tests for RetryCalculator."""

    def test_fixed_delay(self):
        """Test fixed delay strategy."""
        config = RetryConfig(strategy=RetryStrategy.FIXED, base_delay=2.0)

        delay1 = RetryCalculator.calculate_delay(config, 1)
        delay2 = RetryCalculator.calculate_delay(config, 2)
        delay3 = RetryCalculator.calculate_delay(config, 3)

        assert delay1 == 2.0
        assert delay2 == 2.0
        assert delay3 == 2.0

    def test_linear_delay(self):
        """Test linear delay strategy."""
        config = RetryConfig(strategy=RetryStrategy.LINEAR, base_delay=1.0)

        delay1 = RetryCalculator.calculate_delay(config, 1)
        delay2 = RetryCalculator.calculate_delay(config, 2)
        delay3 = RetryCalculator.calculate_delay(config, 3)

        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 3.0

    def test_exponential_delay(self):
        """Test exponential delay strategy."""
        config = RetryConfig(strategy=RetryStrategy.EXPONENTIAL, base_delay=1.0)

        delay1 = RetryCalculator.calculate_delay(config, 1)
        delay2 = RetryCalculator.calculate_delay(config, 2)
        delay3 = RetryCalculator.calculate_delay(config, 3)

        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0

    def test_exponential_jitter_delay(self):
        """Test exponential with jitter strategy."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_JITTER,
            base_delay=1.0,
            jitter_factor=0.5
        )

        delay1 = RetryCalculator.calculate_delay(config, 1)
        delay2 = RetryCalculator.calculate_delay(config, 2)

        # Should be base + some jitter
        assert 1.0 <= delay1 <= 1.5
        assert 2.0 <= delay2 <= 3.0

    def test_max_delay_cap(self):
        """Test delay is capped at max_delay."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=10.0,
            max_delay=30.0
        )

        delay5 = RetryCalculator.calculate_delay(config, 5)

        # 10 * 2^4 = 160, but should be capped at 30
        assert delay5 == 30.0

    def test_error_suggested_delay(self):
        """Test error's suggested delay is used as minimum."""
        config = RetryConfig(strategy=RetryStrategy.FIXED, base_delay=1.0)
        classified = ClassifiedError(
            original_error=Exception("rate limit"),
            category=ErrorCategory.TRANSIENT,
            is_retryable=True,
            suggested_delay=5.0
        )

        delay = RetryCalculator.calculate_delay(config, 1, classified)

        assert delay == 5.0


class TestRetryState:
    """Tests for RetryState."""

    def test_initial_state(self):
        """Test initial retry state."""
        state = RetryState()

        assert state.attempt == 0
        assert state.total_delay == 0.0
        assert len(state.errors) == 0

    def test_record_error(self):
        """Test recording errors."""
        state = RetryState()
        error = ClassifiedError(
            original_error=Exception("test"),
            category=ErrorCategory.TRANSIENT,
            is_retryable=True
        )

        state.record_error(error, 1.5)

        assert len(state.errors) == 1
        assert state.total_delay == 1.5

    def test_elapsed_seconds(self):
        """Test elapsed time calculation."""
        state = RetryState()
        time.sleep(0.1)

        assert state.elapsed_seconds >= 0.1


# =============================================================================
# Circuit Breaker Tests
# =============================================================================

class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.reset_timeout == 30.0
        assert config.half_open_max_calls == 3


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    @pytest.fixture
    def circuit(self):
        """Create circuit breaker for testing."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            reset_timeout=0.1  # Short timeout for testing
        )
        return CircuitBreaker("test-circuit", config)

    @pytest.mark.asyncio
    async def test_initial_state_closed(self, circuit):
        """Test circuit starts in closed state."""
        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_allows_requests_when_closed(self, circuit):
        """Test requests allowed when closed."""
        result = await circuit.allow_request()
        assert result is True

    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self, circuit):
        """Test circuit opens after failure threshold."""
        for _ in range(3):
            await circuit.record_failure()

        assert circuit.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_rejects_when_open(self, circuit):
        """Test requests rejected when open."""
        # Open the circuit
        for _ in range(3):
            await circuit.record_failure()

        with pytest.raises(CircuitOpenError):
            await circuit.allow_request()

    @pytest.mark.asyncio
    async def test_transitions_to_half_open(self, circuit):
        """Test circuit transitions to half-open after timeout."""
        # Open the circuit
        for _ in range(3):
            await circuit.record_failure()

        assert circuit.state == CircuitState.OPEN

        # Wait for reset timeout
        await asyncio.sleep(0.15)

        # Next request should transition to half-open
        await circuit.allow_request()
        assert circuit.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_closes_after_success_threshold(self, circuit):
        """Test circuit closes after success threshold in half-open."""
        # Open the circuit
        for _ in range(3):
            await circuit.record_failure()

        await asyncio.sleep(0.15)

        # Transition to half-open and record successes
        await circuit.allow_request()
        await circuit.record_success()
        await circuit.record_success()

        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reopens_on_half_open_failure(self, circuit):
        """Test circuit reopens on failure in half-open."""
        # Open the circuit
        for _ in range(3):
            await circuit.record_failure()

        await asyncio.sleep(0.15)

        # Transition to half-open
        await circuit.allow_request()
        assert circuit.state == CircuitState.HALF_OPEN

        # Failure returns to open
        await circuit.record_failure()
        assert circuit.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_stats_tracking(self, circuit):
        """Test statistics are tracked."""
        await circuit.allow_request()
        await circuit.record_success()
        await circuit.record_failure()

        stats = circuit.stats
        assert stats.total_calls == 2
        assert stats.successful_calls == 1
        assert stats.failed_calls == 1

    def test_manual_reset(self, circuit):
        """Test manual reset to closed."""
        # Open circuit manually
        circuit._state = CircuitState.OPEN

        circuit.reset()

        assert circuit.state == CircuitState.CLOSED


# =============================================================================
# Checkpoint Tests
# =============================================================================

class TestCheckpoint:
    """Tests for Checkpoint dataclass."""

    def test_create_checkpoint(self):
        """Test checkpoint creation."""
        cp = Checkpoint(
            checkpoint_id="cp-123",
            operation_id="op-456",
            stage="generation",
            state={"progress": 50}
        )

        assert cp.checkpoint_id == "cp-123"
        assert cp.operation_id == "op-456"
        assert cp.stage == "generation"
        assert cp.state["progress"] == 50

    def test_to_dict(self):
        """Test checkpoint serialization."""
        cp = Checkpoint(
            checkpoint_id="cp-123",
            operation_id="op-456",
            stage="generation",
            state={"key": "value"}
        )

        data = cp.to_dict()

        assert data["checkpoint_id"] == "cp-123"
        assert data["stage"] == "generation"
        assert "created_at" in data

    def test_from_dict(self):
        """Test checkpoint deserialization."""
        data = {
            "checkpoint_id": "cp-123",
            "operation_id": "op-456",
            "stage": "testing",
            "state": {"result": True},
            "created_at": "2024-01-01T00:00:00"
        }

        cp = Checkpoint.from_dict(data)

        assert cp.checkpoint_id == "cp-123"
        assert cp.stage == "testing"
        assert cp.state["result"] is True


class TestCheckpointManager:
    """Tests for CheckpointManager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create checkpoint manager with temp directory."""
        return CheckpointManager(checkpoint_dir=tmp_path / "checkpoints")

    def test_save_checkpoint(self, manager):
        """Test saving a checkpoint."""
        cp = manager.save(
            operation_id="test-op",
            stage="planning",
            state={"tasks": 5}
        )

        assert cp.operation_id == "test-op"
        assert cp.stage == "planning"
        assert cp.checkpoint_id is not None
        assert len(cp.checkpoint_id) > 0

    def test_load_latest(self, manager):
        """Test loading latest checkpoint."""
        manager.save("test-op", "stage1", {"step": 1})
        time.sleep(0.01)
        manager.save("test-op", "stage2", {"step": 2})

        latest = manager.load_latest("test-op")

        assert latest is not None
        assert latest.stage == "stage2"
        assert latest.state["step"] == 2

    def test_load_by_stage(self, manager):
        """Test loading checkpoint by stage."""
        manager.save("test-op", "planning", {"plan": "A"})
        manager.save("test-op", "generation", {"files": 10})

        cp = manager.load_by_stage("test-op", "planning")

        assert cp is not None
        assert cp.stage == "planning"
        assert cp.state["plan"] == "A"

    def test_list_checkpoints(self, manager):
        """Test listing all checkpoints."""
        manager.save("test-op", "stage1", {})
        manager.save("test-op", "stage2", {})
        manager.save("test-op", "stage3", {})

        checkpoints = manager.list_checkpoints("test-op")

        assert len(checkpoints) == 3

    def test_delete_checkpoints(self, manager):
        """Test deleting all checkpoints for operation."""
        manager.save("test-op", "stage1", {})
        manager.save("test-op", "stage2", {})

        count = manager.delete_checkpoints("test-op")

        assert count == 2
        assert manager.load_latest("test-op") is None

    def test_cleanup_old_checkpoints(self, manager):
        """Test cleanup of old checkpoints."""
        # Set low max for testing
        manager.max_checkpoints = 2

        manager.save("test-op", "stage1", {})
        time.sleep(0.01)
        manager.save("test-op", "stage2", {})
        time.sleep(0.01)
        manager.save("test-op", "stage3", {})

        checkpoints = manager.list_checkpoints("test-op")

        # Should only keep 2 most recent
        assert len(checkpoints) == 2

    def test_load_nonexistent(self, manager):
        """Test loading nonexistent checkpoint returns None."""
        result = manager.load_latest("nonexistent-op")
        assert result is None


# =============================================================================
# Resilient Executor Tests
# =============================================================================

class TestResilientExecutor:
    """Tests for ResilientExecutor."""

    @pytest.fixture
    def executor(self):
        """Create executor with test config."""
        config = RetryConfig(max_attempts=3, base_delay=0.01, max_delay=0.1)
        return ResilientExecutor(retry_config=config)

    @pytest.mark.asyncio
    async def test_successful_execution(self, executor):
        """Test successful operation execution."""
        async def operation():
            return "success"

        result = await executor.execute(operation)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_retries_on_transient_error(self, executor):
        """Test retries on transient errors."""
        attempts = [0]

        async def flaky_operation():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ConnectionError("Connection failed")
            return "success"

        result = await executor.execute(flaky_operation)

        assert result == "success"
        assert attempts[0] == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self, executor):
        """Test no retry on permanent errors."""
        attempts = [0]

        async def bad_request():
            attempts[0] += 1
            raise Exception("401 Unauthorized")

        with pytest.raises(Exception, match="401"):
            await executor.execute(bad_request)

        assert attempts[0] == 1

    @pytest.mark.asyncio
    async def test_exhausted_retries(self, executor):
        """Test RetryExhaustedError after max attempts."""
        async def always_fails():
            raise ConnectionError("Always fails")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await executor.execute(always_fails)

        assert exc_info.value.attempts == 3

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self, executor):
        """Test fallback is used when retries exhausted."""
        async def fails():
            raise ConnectionError("Failed")

        async def fallback():
            return "fallback_result"

        result = await executor.execute(fails, fallback=fallback)

        assert result == "fallback_result"

    @pytest.mark.asyncio
    async def test_on_retry_callback(self, executor):
        """Test retry callback is called."""
        callbacks = []

        async def flaky():
            if len(callbacks) < 2:
                raise ConnectionError("Fail")
            return "success"

        async def on_retry(attempt, error):
            callbacks.append((attempt, error.category))

        await executor.execute(flaky, on_retry=on_retry)

        assert len(callbacks) == 2
        assert callbacks[0][0] == 1
        assert callbacks[1][0] == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test executor with circuit breaker."""
        config = RetryConfig(max_attempts=2, base_delay=0.01)
        circuit = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=2)
        )
        executor = ResilientExecutor(retry_config=config, circuit_breaker=circuit)

        async def fails():
            raise ConnectionError("Failed")

        # First execution exhausts retries
        with pytest.raises(RetryExhaustedError):
            await executor.execute(fails)

        # Circuit should now be open
        assert circuit.state == CircuitState.OPEN

    def test_sync_execution(self, executor):
        """Test synchronous execution."""
        def sync_operation():
            return "sync_result"

        result = executor.execute_sync(sync_operation)

        assert result == "sync_result"

    def test_sync_retry(self, executor):
        """Test synchronous retry behavior."""
        attempts = [0]

        def flaky_sync():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionError("Fail")
            return "success"

        result = executor.execute_sync(flaky_sync)

        assert result == "success"
        assert attempts[0] == 2


# =============================================================================
# Decorator Tests
# =============================================================================

class TestDecorators:
    """Tests for resilience decorators."""

    @pytest.mark.asyncio
    async def test_with_retry_decorator(self):
        """Test @with_retry decorator."""
        attempts = [0]

        @with_retry(max_attempts=3, base_delay=0.01)
        async def flaky_function():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionError("Fail")
            return "success"

        result = await flaky_function()

        assert result == "success"
        assert attempts[0] == 2

    @pytest.mark.asyncio
    async def test_with_circuit_breaker_decorator(self):
        """Test @with_circuit_breaker decorator."""
        @with_circuit_breaker("test-decorator", failure_threshold=2)
        async def protected_function():
            return "protected"

        result = await protected_function()
        assert result == "protected"

    @pytest.mark.asyncio
    async def test_with_fallback_decorator(self):
        """Test @with_fallback decorator."""
        async def fallback_func():
            return "fallback"

        @with_fallback(fallback_func)
        async def main_func():
            raise ValueError("Main failed")

        result = await main_func()
        assert result == "fallback"

    def test_with_retry_sync(self):
        """Test @with_retry on sync function."""
        attempts = [0]

        @with_retry(max_attempts=2, base_delay=0.01)
        def sync_flaky():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionError("Fail")
            return "done"

        result = sync_flaky()

        assert result == "done"
        assert attempts[0] == 2


# =============================================================================
# Circuit Breaker Registry Tests
# =============================================================================

class TestCircuitBreakerRegistry:
    """Tests for CircuitBreakerRegistry."""

    @pytest.fixture
    def registry(self):
        """Create fresh registry for testing."""
        reg = CircuitBreakerRegistry()
        reg._circuits = {}  # Clear any existing circuits
        return reg

    def test_get_or_create(self, registry):
        """Test getting or creating circuit."""
        circuit = registry.get_or_create("api-calls")

        assert circuit is not None
        assert circuit.name == "api-calls"

        # Getting again returns same instance
        circuit2 = registry.get_or_create("api-calls")
        assert circuit2 is circuit

    def test_get_nonexistent(self, registry):
        """Test getting nonexistent circuit returns None."""
        result = registry.get("nonexistent")
        assert result is None

    def test_list_circuits(self, registry):
        """Test listing all circuits."""
        registry.get_or_create("circuit-1")
        registry.get_or_create("circuit-2")

        circuits = registry.list_circuits()

        assert "circuit-1" in circuits
        assert "circuit-2" in circuits

    def test_reset_all(self, registry):
        """Test resetting all circuits."""
        circuit1 = registry.get_or_create("c1")
        circuit2 = registry.get_or_create("c2")

        # Open both circuits
        circuit1._state = CircuitState.OPEN
        circuit2._state = CircuitState.OPEN

        registry.reset_all()

        assert circuit1.state == CircuitState.CLOSED
        assert circuit2.state == CircuitState.CLOSED

    def test_get_stats(self, registry):
        """Test getting stats for all circuits."""
        circuit = registry.get_or_create("stats-test")
        circuit._stats.total_calls = 10
        circuit._stats.successful_calls = 8

        stats = registry.get_stats()

        assert "stats-test" in stats
        assert stats["stats-test"]["total_calls"] == 10


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================

class TestEdgeCases:
    """Edge case and integration tests."""

    @pytest.mark.asyncio
    async def test_retry_with_checkpoint(self, tmp_path):
        """Test retry with checkpointing."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        checkpoint_mgr = CheckpointManager(checkpoint_dir=tmp_path / "cp")
        executor = ResilientExecutor(
            retry_config=config,
            checkpoint_manager=checkpoint_mgr
        )

        async def operation():
            return {"result": "success"}

        result = await executor.execute(
            operation,
            operation_id="test-op",
            stage="generation"
        )

        assert result["result"] == "success"

        # Check checkpoint was saved
        cp = checkpoint_mgr.load_latest("test-op")
        assert cp is not None
        assert cp.state["completed"] is True

    @pytest.mark.asyncio
    async def test_multiple_error_types(self):
        """Test handling different error types in sequence."""
        attempts = [0]
        errors = [
            TimeoutError("Timeout"),
            ConnectionError("Connection lost"),
            Exception("Success on third")
        ]

        config = RetryConfig(max_attempts=5, base_delay=0.01)
        executor = ResilientExecutor(retry_config=config)

        async def multi_error():
            attempts[0] += 1
            if attempts[0] <= 2:
                raise errors[attempts[0] - 1]
            return "success"

        result = await executor.execute(multi_error)

        assert result == "success"
        assert attempts[0] == 3

    @pytest.mark.asyncio
    async def test_circuit_prevents_cascade(self):
        """Test circuit breaker prevents cascading failures."""
        config = RetryConfig(max_attempts=1, base_delay=0.01)
        circuit = CircuitBreaker(
            "cascade-test",
            CircuitBreakerConfig(failure_threshold=2, reset_timeout=1.0)
        )
        executor = ResilientExecutor(retry_config=config, circuit_breaker=circuit)

        async def fails():
            raise ConnectionError("Service down")

        # First two failures open the circuit
        for _ in range(2):
            try:
                await executor.execute(fails)
            except RetryExhaustedError:
                pass

        # Third call should be rejected immediately
        with pytest.raises(CircuitOpenError):
            await executor.execute(fails)

        # Stats should show rejection
        assert circuit.stats.rejected_calls == 1

    def test_checkpoint_with_metadata(self, tmp_path):
        """Test checkpoint with metadata."""
        manager = CheckpointManager(checkpoint_dir=tmp_path / "cp")

        cp = manager.save(
            operation_id="meta-test",
            stage="testing",
            state={"progress": 100},
            metadata={"duration": 45.5, "files": ["a.py", "b.py"]}
        )

        loaded = manager.load_latest("meta-test")

        assert loaded.metadata["duration"] == 45.5
        assert len(loaded.metadata["files"]) == 2

    @pytest.mark.asyncio
    async def test_half_open_max_calls(self):
        """Test half-open state limits concurrent calls."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            half_open_max_calls=2,
            reset_timeout=0.05
        )
        circuit = CircuitBreaker("half-open-test", config)

        # Open the circuit
        await circuit.record_failure()
        assert circuit.state == CircuitState.OPEN

        # Wait for reset
        await asyncio.sleep(0.1)

        # First two calls allowed (transitions to half-open)
        await circuit.allow_request()
        await circuit.allow_request()

        # Third call rejected
        with pytest.raises(CircuitOpenError):
            await circuit.allow_request()
