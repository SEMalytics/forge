"""
Tests for Streaming Output & Progress Tracking

Tests the streaming infrastructure including:
- StreamEvent creation and serialization
- StreamEmitter event emission
- ProgressState tracking
- ProgressTracker multi-task management
- Stream handlers (Buffer, Console, Callback)
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from forge.core.streaming import (
    StreamEventType,
    StreamEvent,
    StreamEmitter,
    ProgressState,
    ProgressTracker,
    ConsoleStreamHandler,
    BufferStreamHandler,
    CallbackStreamHandler
)


class TestStreamEventType:
    """Tests for StreamEventType enum."""

    def test_all_event_types_exist(self):
        """Test all expected event types are defined."""
        expected = [
            'started', 'progress', 'stage_change', 'completed', 'failed', 'cancelled',
            'token', 'chunk', 'file_started', 'file_completed', 'file_content',
            'status', 'warning', 'error', 'log'
        ]

        actual = [t.value for t in StreamEventType]
        assert set(expected) == set(actual)

    def test_event_type_values(self):
        """Test event type enum values."""
        assert StreamEventType.STARTED.value == "started"
        assert StreamEventType.PROGRESS.value == "progress"
        assert StreamEventType.COMPLETED.value == "completed"


class TestStreamEvent:
    """Tests for StreamEvent dataclass."""

    def test_creation_with_defaults(self):
        """Test creating event with minimal args."""
        event = StreamEvent(event_type=StreamEventType.STARTED)

        assert event.event_type == StreamEventType.STARTED
        assert event.timestamp > 0
        assert event.progress is None
        assert event.message is None

    def test_creation_with_all_fields(self):
        """Test creating event with all fields."""
        event = StreamEvent(
            event_type=StreamEventType.PROGRESS,
            progress=0.5,
            stage="generation",
            message="Generating code...",
            content="def hello(): pass",
            file_path="src/hello.py",
            task_id="task-001",
            metadata={"tokens": 100}
        )

        assert event.progress == 0.5
        assert event.stage == "generation"
        assert event.message == "Generating code..."
        assert event.content == "def hello(): pass"
        assert event.file_path == "src/hello.py"
        assert event.task_id == "task-001"
        assert event.metadata["tokens"] == 100

    def test_to_dict(self):
        """Test serialization to dictionary."""
        event = StreamEvent(
            event_type=StreamEventType.COMPLETED,
            progress=1.0,
            message="Done"
        )

        data = event.to_dict()

        assert data['event_type'] == 'completed'
        assert data['progress'] == 1.0
        assert data['message'] == 'Done'
        assert 'timestamp' in data


class TestStreamEmitter:
    """Tests for StreamEmitter class."""

    @pytest.fixture
    def emitter(self):
        """Create test emitter."""
        return StreamEmitter(task_id="test-task")

    @pytest.fixture
    def buffer_handler(self):
        """Create buffer handler."""
        return BufferStreamHandler()

    @pytest.mark.asyncio
    async def test_started_event(self, emitter, buffer_handler):
        """Test emitting started event."""
        emitter.add_handler(buffer_handler)

        await emitter.started("Starting...")

        assert len(buffer_handler.events) == 1
        event = buffer_handler.events[0]
        assert event.event_type == StreamEventType.STARTED
        assert event.message == "Starting..."
        assert event.progress == 0.0

    @pytest.mark.asyncio
    async def test_progress_event(self, emitter, buffer_handler):
        """Test emitting progress event."""
        emitter.add_handler(buffer_handler)

        await emitter.progress(0.5, "Half done")

        event = buffer_handler.events[0]
        assert event.event_type == StreamEventType.PROGRESS
        assert event.progress == 0.5
        assert event.message == "Half done"

    @pytest.mark.asyncio
    async def test_progress_clamped(self, emitter, buffer_handler):
        """Test that progress is clamped to 0.0-1.0."""
        emitter.add_handler(buffer_handler)

        await emitter.progress(1.5)  # Too high
        await emitter.progress(-0.5)  # Too low

        assert buffer_handler.events[0].progress == 1.0
        assert buffer_handler.events[1].progress == 0.0

    @pytest.mark.asyncio
    async def test_stage_event(self, emitter, buffer_handler):
        """Test emitting stage change event."""
        emitter.add_handler(buffer_handler)

        await emitter.stage("generation", "Generating code...")

        event = buffer_handler.events[0]
        assert event.event_type == StreamEventType.STAGE_CHANGE
        assert event.stage == "generation"
        assert emitter._current_stage == "generation"

    @pytest.mark.asyncio
    async def test_completed_event(self, emitter, buffer_handler):
        """Test emitting completed event."""
        emitter.add_handler(buffer_handler)

        await emitter.started()
        await asyncio.sleep(0.01)  # Small delay for duration
        await emitter.completed("All done", metadata={"files": 5})

        event = buffer_handler.events[-1]
        assert event.event_type == StreamEventType.COMPLETED
        assert event.progress == 1.0
        assert event.message == "All done"
        assert "duration_seconds" in event.metadata

    @pytest.mark.asyncio
    async def test_failed_event(self, emitter, buffer_handler):
        """Test emitting failed event."""
        emitter.add_handler(buffer_handler)

        await emitter.failed("Something went wrong")

        event = buffer_handler.events[0]
        assert event.event_type == StreamEventType.FAILED
        assert event.message == "Something went wrong"

    @pytest.mark.asyncio
    async def test_cancelled_event(self, emitter, buffer_handler):
        """Test emitting cancelled event."""
        emitter.add_handler(buffer_handler)

        emitter.cancel()
        await emitter.cancelled()

        assert emitter.is_cancelled is True
        event = buffer_handler.events[0]
        assert event.event_type == StreamEventType.CANCELLED

    @pytest.mark.asyncio
    async def test_token_event(self, emitter, buffer_handler):
        """Test emitting token event."""
        emitter.add_handler(buffer_handler)

        await emitter.token("def")
        await emitter.token(" hello")

        assert len(buffer_handler.events) == 2
        assert buffer_handler.events[0].content == "def"
        assert buffer_handler.events[1].content == " hello"

    @pytest.mark.asyncio
    async def test_chunk_event(self, emitter, buffer_handler):
        """Test emitting chunk event."""
        emitter.add_handler(buffer_handler)

        await emitter.chunk("def hello():\n    pass\n")

        event = buffer_handler.events[0]
        assert event.event_type == StreamEventType.CHUNK
        assert "def hello()" in event.content

    @pytest.mark.asyncio
    async def test_file_events(self, emitter, buffer_handler):
        """Test file-related events."""
        emitter.add_handler(buffer_handler)

        await emitter.file_started("src/main.py")
        await emitter.file_content("src/main.py", "print('hello')")
        await emitter.file_completed("src/main.py", size=14)

        assert len(buffer_handler.events) == 3
        assert buffer_handler.events[0].event_type == StreamEventType.FILE_STARTED
        assert buffer_handler.events[1].event_type == StreamEventType.FILE_CONTENT
        assert buffer_handler.events[2].event_type == StreamEventType.FILE_COMPLETED
        assert buffer_handler.events[2].metadata.get("size") == 14

    @pytest.mark.asyncio
    async def test_status_warning_error_log(self, emitter, buffer_handler):
        """Test status, warning, error, and log events."""
        emitter.add_handler(buffer_handler)

        await emitter.status("Processing...")
        await emitter.warning("Low memory")
        await emitter.error("File not found")
        await emitter.log("Debug info", level="debug")

        types = [e.event_type for e in buffer_handler.events]
        assert StreamEventType.STATUS in types
        assert StreamEventType.WARNING in types
        assert StreamEventType.ERROR in types
        assert StreamEventType.LOG in types

    @pytest.mark.asyncio
    async def test_task_id_propagation(self, emitter, buffer_handler):
        """Test that task_id is propagated to events."""
        emitter.add_handler(buffer_handler)

        await emitter.progress(0.5)

        assert buffer_handler.events[0].task_id == "test-task"

    @pytest.mark.asyncio
    async def test_multiple_handlers(self, emitter):
        """Test with multiple handlers."""
        handler1 = BufferStreamHandler()
        handler2 = BufferStreamHandler()

        emitter.add_handler(handler1)
        emitter.add_handler(handler2)

        await emitter.progress(0.5)

        assert len(handler1.events) == 1
        assert len(handler2.events) == 1

    @pytest.mark.asyncio
    async def test_remove_handler(self, emitter, buffer_handler):
        """Test removing handler."""
        emitter.add_handler(buffer_handler)
        emitter.remove_handler(buffer_handler)

        await emitter.progress(0.5)

        assert len(buffer_handler.events) == 0

    @pytest.mark.asyncio
    async def test_handler_error_doesnt_break_emission(self, emitter):
        """Test that handler errors don't break other handlers."""
        bad_handler = Mock()
        bad_handler.handle_event = AsyncMock(side_effect=Exception("Handler error"))

        good_handler = BufferStreamHandler()

        emitter.add_handler(bad_handler)
        emitter.add_handler(good_handler)

        await emitter.progress(0.5)

        # Good handler should still receive event
        assert len(good_handler.events) == 1


class TestProgressState:
    """Tests for ProgressState dataclass."""

    def test_initial_state(self):
        """Test initial state values."""
        state = ProgressState(total_tasks=5)

        assert state.total_tasks == 5
        assert state.completed_tasks == 0
        assert state.overall_progress == 0.0
        assert state.is_complete is False

    def test_overall_progress(self):
        """Test progress calculation."""
        state = ProgressState(total_tasks=4)

        state.complete_task("task-1")
        assert state.overall_progress == 0.25

        state.complete_task("task-2")
        assert state.overall_progress == 0.5

    def test_is_complete(self):
        """Test completion detection."""
        state = ProgressState(total_tasks=2)

        assert state.is_complete is False

        state.complete_task("task-1")
        state.complete_task("task-2")

        assert state.is_complete is True

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        state = ProgressState()

        assert state.elapsed_seconds == 0.0

        state.start()
        time.sleep(0.01)

        assert state.elapsed_seconds > 0

    def test_estimated_remaining(self):
        """Test time estimation."""
        state = ProgressState(total_tasks=4)

        # No estimate without progress
        assert state.estimated_remaining is None

        state.start()
        time.sleep(0.01)
        state.complete_task("task-1")

        # Now we should have an estimate
        remaining = state.estimated_remaining
        assert remaining is not None
        assert remaining >= 0

    def test_set_stage(self):
        """Test setting stage progress."""
        state = ProgressState()

        state.set_stage("generation", 0.5)

        assert state.current_stage == "generation"
        assert state.stage_progress["generation"] == 0.5

    def test_add_error_warning(self):
        """Test adding errors and warnings."""
        state = ProgressState()

        state.add_error("Error 1")
        state.add_warning("Warning 1")

        assert "Error 1" in state.errors
        assert "Warning 1" in state.warnings

    def test_to_dict(self):
        """Test serialization."""
        state = ProgressState(total_tasks=5)
        state.complete_task("task-1")

        data = state.to_dict()

        assert data['total_tasks'] == 5
        assert data['completed_tasks'] == 1
        assert data['overall_progress'] == 0.2
        assert data['is_complete'] is False


class TestProgressTracker:
    """Tests for ProgressTracker class."""

    @pytest.fixture
    def tracker(self):
        """Create test tracker."""
        return ProgressTracker(
            total_tasks=3,
            stages=["preparation", "generation", "validation"]
        )

    @pytest.fixture
    def buffer_handler(self):
        """Create buffer handler."""
        return BufferStreamHandler()

    @pytest.mark.asyncio
    async def test_start(self, tracker, buffer_handler):
        """Test starting tracker."""
        tracker.add_handler(buffer_handler)

        await tracker.start()

        assert tracker.state.started_at is not None
        event = buffer_handler.events[0]
        assert event.event_type == StreamEventType.STARTED

    @pytest.mark.asyncio
    async def test_start_task(self, tracker, buffer_handler):
        """Test starting a task."""
        tracker.add_handler(buffer_handler)

        emitter = await tracker.start_task("task-001")

        assert emitter is not None
        assert emitter.task_id == "task-001"
        assert tracker.state.current_task == "task-001"

    @pytest.mark.asyncio
    async def test_complete_task(self, tracker, buffer_handler):
        """Test completing a task."""
        tracker.add_handler(buffer_handler)

        await tracker.start()
        await tracker.complete_task("task-001")

        assert tracker.state.completed_tasks == 1

    @pytest.mark.asyncio
    async def test_fail_task(self, tracker, buffer_handler):
        """Test failing a task."""
        tracker.add_handler(buffer_handler)

        await tracker.fail_task("task-001", "Error occurred")

        assert "task-001: Error occurred" in tracker.state.errors

        error_events = buffer_handler.get_events_by_type(StreamEventType.ERROR)
        assert len(error_events) == 1

    @pytest.mark.asyncio
    async def test_complete_all(self, tracker, buffer_handler):
        """Test completing all tasks."""
        tracker.add_handler(buffer_handler)

        await tracker.start()
        await tracker.complete_task("task-1")
        await tracker.complete_task("task-2")
        await tracker.complete_task("task-3")
        await tracker.complete()

        completed_events = buffer_handler.get_events_by_type(StreamEventType.COMPLETED)
        assert len(completed_events) == 1
        assert tracker.state.is_complete

    @pytest.mark.asyncio
    async def test_cancellation(self, tracker):
        """Test cancellation."""
        assert tracker.is_cancelled is False

        tracker.cancel()

        assert tracker.is_cancelled is True

    @pytest.mark.asyncio
    async def test_task_emitter_events_forwarded(self, tracker, buffer_handler):
        """Test that task emitter events are forwarded to tracker handlers."""
        tracker.add_handler(buffer_handler)

        emitter = await tracker.start_task("task-001")
        await emitter.progress(0.5, "Half done")

        # Event should be forwarded to tracker's handler
        progress_events = buffer_handler.get_events_by_type(StreamEventType.PROGRESS)
        assert len(progress_events) >= 1


class TestBufferStreamHandler:
    """Tests for BufferStreamHandler."""

    @pytest.mark.asyncio
    async def test_buffers_events(self):
        """Test that handler buffers events."""
        handler = BufferStreamHandler()

        await handler.handle_event(StreamEvent(StreamEventType.STARTED))
        await handler.handle_event(StreamEvent(StreamEventType.PROGRESS, progress=0.5))
        await handler.handle_event(StreamEvent(StreamEventType.COMPLETED))

        assert len(handler.events) == 3

    @pytest.mark.asyncio
    async def test_content_buffer(self):
        """Test content accumulation."""
        handler = BufferStreamHandler()

        await handler.handle_event(StreamEvent(StreamEventType.TOKEN, content="def "))
        await handler.handle_event(StreamEvent(StreamEventType.TOKEN, content="hello"))
        await handler.handle_event(StreamEvent(StreamEventType.TOKEN, content="()"))

        assert handler.content_buffer == "def hello()"

    @pytest.mark.asyncio
    async def test_get_events_by_type(self):
        """Test filtering events by type."""
        handler = BufferStreamHandler()

        await handler.handle_event(StreamEvent(StreamEventType.STARTED))
        await handler.handle_event(StreamEvent(StreamEventType.PROGRESS))
        await handler.handle_event(StreamEvent(StreamEventType.PROGRESS))
        await handler.handle_event(StreamEvent(StreamEventType.COMPLETED))

        progress = handler.get_events_by_type(StreamEventType.PROGRESS)
        assert len(progress) == 2

    def test_clear(self):
        """Test clearing buffer."""
        handler = BufferStreamHandler()
        handler.events.append(StreamEvent(StreamEventType.STARTED))
        handler.content_buffer = "content"

        handler.clear()

        assert len(handler.events) == 0
        assert handler.content_buffer == ""


class TestCallbackStreamHandler:
    """Tests for CallbackStreamHandler."""

    @pytest.mark.asyncio
    async def test_calls_sync_callback(self):
        """Test that sync callback is called."""
        events_received = []

        def callback(event):
            events_received.append(event)

        handler = CallbackStreamHandler(callback)

        await handler.handle_event(StreamEvent(StreamEventType.STARTED))

        assert len(events_received) == 1

    @pytest.mark.asyncio
    async def test_calls_async_callback(self):
        """Test that async callback is called."""
        events_received = []

        async def callback(event):
            events_received.append(event)

        handler = CallbackStreamHandler(callback)

        await handler.handle_event(StreamEvent(StreamEventType.STARTED))

        assert len(events_received) == 1


class TestConsoleStreamHandler:
    """Tests for ConsoleStreamHandler."""

    @pytest.mark.asyncio
    async def test_handles_started_without_progress(self):
        """Test handling started event without progress bar."""
        mock_console = Mock()

        handler = ConsoleStreamHandler(console=mock_console, show_progress=False)

        await handler.handle_event(StreamEvent(
            StreamEventType.STARTED,
            message="Starting..."
        ))

        mock_console.print.assert_called()

    @pytest.mark.asyncio
    async def test_handles_completed(self):
        """Test handling completed event."""
        mock_console = Mock()

        handler = ConsoleStreamHandler(console=mock_console, show_progress=False)

        await handler.handle_event(StreamEvent(
            StreamEventType.COMPLETED,
            message="Done",
            metadata={"duration_seconds": 1.5}
        ))

        mock_console.print.assert_called()

    @pytest.mark.asyncio
    async def test_handles_file_events(self):
        """Test handling file events."""
        mock_console = Mock()

        handler = ConsoleStreamHandler(console=mock_console, show_files=True)

        await handler.handle_event(StreamEvent(
            StreamEventType.FILE_STARTED,
            file_path="src/main.py"
        ))

        await handler.handle_event(StreamEvent(
            StreamEventType.FILE_COMPLETED,
            file_path="src/main.py",
            metadata={"size": 100}
        ))

        assert mock_console.print.call_count >= 2

    @pytest.mark.asyncio
    async def test_respects_show_files_flag(self):
        """Test that show_files flag is respected."""
        mock_console = Mock()

        handler = ConsoleStreamHandler(console=mock_console, show_files=False)

        await handler.handle_event(StreamEvent(
            StreamEventType.FILE_STARTED,
            file_path="src/main.py"
        ))

        # Should not print file events
        mock_console.print.assert_not_called()


class TestIntegration:
    """Integration tests for streaming system."""

    @pytest.mark.asyncio
    async def test_full_generation_flow(self):
        """Test complete generation flow with streaming."""
        buffer = BufferStreamHandler()
        emitter = StreamEmitter(task_id="integration-test")
        emitter.add_handler(buffer)

        # Simulate generation flow
        await emitter.started("Starting generation")
        await emitter.stage("preparation", "Preparing context")
        await emitter.progress(0.2)

        await emitter.stage("generation", "Generating code")
        for i in range(5):
            await emitter.progress(0.2 + i * 0.1)
            await asyncio.sleep(0.001)

        await emitter.file_started("src/main.py")
        await emitter.file_content("src/main.py", "print('hello')")
        await emitter.file_completed("src/main.py", size=14)

        await emitter.completed("Generated 1 file", metadata={"files": ["src/main.py"]})

        # Verify event sequence
        assert len(buffer.events) > 0

        event_types = [e.event_type for e in buffer.events]
        assert StreamEventType.STARTED in event_types
        assert StreamEventType.STAGE_CHANGE in event_types
        assert StreamEventType.PROGRESS in event_types
        assert StreamEventType.FILE_STARTED in event_types
        assert StreamEventType.FILE_COMPLETED in event_types
        assert StreamEventType.COMPLETED in event_types

    @pytest.mark.asyncio
    async def test_multi_task_tracking(self):
        """Test tracking multiple tasks."""
        buffer = BufferStreamHandler()
        tracker = ProgressTracker(total_tasks=3)
        tracker.add_handler(buffer)

        await tracker.start()

        # Run 3 tasks
        for i in range(3):
            task_id = f"task-{i}"
            emitter = await tracker.start_task(task_id)

            await emitter.started(f"Task {i}")
            await emitter.progress(0.5)
            await emitter.completed(f"Task {i} done")

            await tracker.complete_task(task_id)

        await tracker.complete()

        # Verify tracking state
        assert tracker.state.completed_tasks == 3
        assert tracker.state.is_complete

        # Verify events
        completed_events = buffer.get_events_by_type(StreamEventType.COMPLETED)
        assert len(completed_events) >= 1

    @pytest.mark.asyncio
    async def test_cancellation_flow(self):
        """Test cancellation during generation."""
        buffer = BufferStreamHandler()
        emitter = StreamEmitter(task_id="cancel-test")
        emitter.add_handler(buffer)

        await emitter.started("Starting")

        # Simulate cancellation
        emitter.cancel()

        assert emitter.is_cancelled

        await emitter.cancelled()

        cancel_events = buffer.get_events_by_type(StreamEventType.CANCELLED)
        assert len(cancel_events) == 1
