"""
Streaming Output & Progress Tracking for Forge

Provides real-time streaming of generation output and progress tracking
so users can see what's happening during long-running operations.

Features:
- Event-based streaming protocol
- Progress tracking with stages and percentages
- Cancelable operations
- Rich terminal output integration
- Log streaming
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Dict, List, Optional, Any, Callable, AsyncIterator,
    Protocol, runtime_checkable, Union
)
from enum import Enum
from datetime import datetime
import time

from forge.utils.logger import logger


class StreamEventType(Enum):
    """Types of stream events"""
    # Progress events
    STARTED = "started"
    PROGRESS = "progress"
    STAGE_CHANGE = "stage_change"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    # Content events
    TOKEN = "token"  # Single token streamed
    CHUNK = "chunk"  # Text chunk
    FILE_STARTED = "file_started"
    FILE_COMPLETED = "file_completed"
    FILE_CONTENT = "file_content"

    # Status events
    STATUS = "status"
    WARNING = "warning"
    ERROR = "error"
    LOG = "log"


@dataclass
class StreamEvent:
    """
    A single event in the output stream.

    Events are emitted during generation to provide real-time feedback.
    """
    event_type: StreamEventType
    timestamp: float = field(default_factory=time.time)

    # Progress data
    progress: Optional[float] = None  # 0.0 to 1.0
    stage: Optional[str] = None
    message: Optional[str] = None

    # Content data
    content: Optional[str] = None
    file_path: Optional[str] = None

    # Metadata
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "progress": self.progress,
            "stage": self.stage,
            "message": self.message,
            "content": self.content,
            "file_path": self.file_path,
            "task_id": self.task_id,
            "metadata": self.metadata
        }


@runtime_checkable
class StreamHandler(Protocol):
    """Protocol for handling stream events"""

    async def handle_event(self, event: StreamEvent) -> None:
        """Handle a stream event"""
        ...


class StreamEmitter:
    """
    Emits stream events to registered handlers.

    Use this in generators to emit progress and content events.
    """

    def __init__(self, task_id: Optional[str] = None):
        self.task_id = task_id
        self._handlers: List[StreamHandler] = []
        self._cancelled = False
        self._started_at: Optional[float] = None
        self._current_stage: Optional[str] = None

    def add_handler(self, handler: StreamHandler) -> None:
        """Add an event handler"""
        self._handlers.append(handler)

    def remove_handler(self, handler: StreamHandler) -> None:
        """Remove an event handler"""
        if handler in self._handlers:
            self._handlers.remove(handler)

    @property
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled"""
        return self._cancelled

    def cancel(self) -> None:
        """Cancel the operation"""
        self._cancelled = True
        logger.info(f"Operation cancelled: {self.task_id}")

    async def _emit(self, event: StreamEvent) -> None:
        """Emit event to all handlers"""
        if event.task_id is None:
            event.task_id = self.task_id

        for handler in self._handlers:
            try:
                await handler.handle_event(event)
            except Exception as e:
                logger.warning(f"Handler error: {e}")

    async def started(self, message: str = "Starting...") -> None:
        """Emit started event"""
        self._started_at = time.time()
        await self._emit(StreamEvent(
            event_type=StreamEventType.STARTED,
            message=message,
            progress=0.0
        ))

    async def progress(
        self,
        progress: float,
        message: Optional[str] = None
    ) -> None:
        """Emit progress event (0.0 to 1.0)"""
        await self._emit(StreamEvent(
            event_type=StreamEventType.PROGRESS,
            progress=min(max(progress, 0.0), 1.0),
            message=message,
            stage=self._current_stage
        ))

    async def stage(self, stage_name: str, message: Optional[str] = None) -> None:
        """Emit stage change event"""
        self._current_stage = stage_name
        await self._emit(StreamEvent(
            event_type=StreamEventType.STAGE_CHANGE,
            stage=stage_name,
            message=message or f"Stage: {stage_name}"
        ))

    async def completed(
        self,
        message: str = "Completed",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit completed event"""
        duration = time.time() - self._started_at if self._started_at else 0
        await self._emit(StreamEvent(
            event_type=StreamEventType.COMPLETED,
            message=message,
            progress=1.0,
            metadata={
                **(metadata or {}),
                "duration_seconds": duration
            }
        ))

    async def failed(self, error: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Emit failed event"""
        await self._emit(StreamEvent(
            event_type=StreamEventType.FAILED,
            message=error,
            metadata=metadata or {}
        ))

    async def cancelled(self) -> None:
        """Emit cancelled event"""
        await self._emit(StreamEvent(
            event_type=StreamEventType.CANCELLED,
            message="Operation cancelled"
        ))

    async def token(self, token: str) -> None:
        """Emit single token"""
        await self._emit(StreamEvent(
            event_type=StreamEventType.TOKEN,
            content=token
        ))

    async def chunk(self, chunk: str) -> None:
        """Emit text chunk"""
        await self._emit(StreamEvent(
            event_type=StreamEventType.CHUNK,
            content=chunk
        ))

    async def file_started(self, file_path: str) -> None:
        """Emit file generation started"""
        await self._emit(StreamEvent(
            event_type=StreamEventType.FILE_STARTED,
            file_path=file_path,
            message=f"Generating: {file_path}"
        ))

    async def file_content(self, file_path: str, content: str) -> None:
        """Emit file content chunk"""
        await self._emit(StreamEvent(
            event_type=StreamEventType.FILE_CONTENT,
            file_path=file_path,
            content=content
        ))

    async def file_completed(self, file_path: str, size: Optional[int] = None) -> None:
        """Emit file generation completed"""
        await self._emit(StreamEvent(
            event_type=StreamEventType.FILE_COMPLETED,
            file_path=file_path,
            message=f"Completed: {file_path}",
            metadata={"size": size} if size else {}
        ))

    async def status(self, message: str) -> None:
        """Emit status message"""
        await self._emit(StreamEvent(
            event_type=StreamEventType.STATUS,
            message=message
        ))

    async def warning(self, message: str) -> None:
        """Emit warning"""
        await self._emit(StreamEvent(
            event_type=StreamEventType.WARNING,
            message=message
        ))

    async def error(self, message: str) -> None:
        """Emit error"""
        await self._emit(StreamEvent(
            event_type=StreamEventType.ERROR,
            message=message
        ))

    async def log(self, message: str, level: str = "info") -> None:
        """Emit log message"""
        await self._emit(StreamEvent(
            event_type=StreamEventType.LOG,
            message=message,
            metadata={"level": level}
        ))


@dataclass
class ProgressState:
    """
    Tracks progress of a multi-stage operation.

    Used to maintain state across multiple tasks/stages.
    """
    total_tasks: int = 0
    completed_tasks: int = 0
    current_task: Optional[str] = None
    current_stage: Optional[str] = None

    stages: List[str] = field(default_factory=list)
    stage_weights: Dict[str, float] = field(default_factory=dict)
    stage_progress: Dict[str, float] = field(default_factory=dict)

    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Check if all tasks are complete"""
        return self.completed_tasks >= self.total_tasks

    @property
    def overall_progress(self) -> float:
        """Calculate overall progress (0.0 to 1.0)"""
        if self.total_tasks == 0:
            return 0.0

        task_progress = self.completed_tasks / self.total_tasks

        # Add current task's stage progress if available
        if self.current_stage and self.current_stage in self.stage_progress:
            stage_contrib = self.stage_progress[self.current_stage] / self.total_tasks
            return min(task_progress + stage_contrib, 1.0)

        return task_progress

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds"""
        if self.started_at is None:
            return 0.0

        end_time = self.completed_at or time.time()
        return end_time - self.started_at

    @property
    def estimated_remaining(self) -> Optional[float]:
        """Estimate remaining time in seconds"""
        progress = self.overall_progress
        if progress <= 0 or self.elapsed_seconds <= 0:
            return None

        # Simple linear estimate
        total_estimated = self.elapsed_seconds / progress
        return max(total_estimated - self.elapsed_seconds, 0)

    def start(self) -> None:
        """Mark operation as started"""
        self.started_at = time.time()

    def complete_task(self, task_id: str) -> None:
        """Mark a task as complete"""
        self.completed_tasks += 1
        if self.completed_tasks >= self.total_tasks:
            self.completed_at = time.time()

    def set_stage(self, stage: str, progress: float = 0.0) -> None:
        """Set current stage and its progress"""
        self.current_stage = stage
        self.stage_progress[stage] = progress

    def add_error(self, error: str) -> None:
        """Add an error"""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning"""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "current_task": self.current_task,
            "current_stage": self.current_stage,
            "overall_progress": self.overall_progress,
            "elapsed_seconds": self.elapsed_seconds,
            "estimated_remaining": self.estimated_remaining,
            "is_complete": self.is_complete,
            "errors": self.errors,
            "warnings": self.warnings
        }


class ProgressTracker:
    """
    High-level progress tracking for multi-task operations.

    Manages multiple StreamEmitters and aggregates progress.
    """

    def __init__(
        self,
        total_tasks: int,
        stages: Optional[List[str]] = None,
        stage_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize progress tracker.

        Args:
            total_tasks: Total number of tasks
            stages: List of stage names for each task
            stage_weights: Optional weights for stages (must sum to 1.0)
        """
        self.state = ProgressState(
            total_tasks=total_tasks,
            stages=stages or [],
            stage_weights=stage_weights or {}
        )

        self._handlers: List[StreamHandler] = []
        self._cancelled = False
        self._lock = asyncio.Lock()

    def add_handler(self, handler: StreamHandler) -> None:
        """Add progress handler"""
        self._handlers.append(handler)

    @property
    def is_cancelled(self) -> bool:
        """Check if cancelled"""
        return self._cancelled

    def cancel(self) -> None:
        """Cancel all tasks"""
        self._cancelled = True

    async def _emit_progress(self) -> None:
        """Emit current progress state"""
        event = StreamEvent(
            event_type=StreamEventType.PROGRESS,
            progress=self.state.overall_progress,
            stage=self.state.current_stage,
            message=f"{self.state.completed_tasks}/{self.state.total_tasks} tasks",
            metadata=self.state.to_dict()
        )

        for handler in self._handlers:
            try:
                await handler.handle_event(event)
            except Exception as e:
                logger.warning(f"Handler error: {e}")

    async def start(self) -> None:
        """Start tracking"""
        self.state.start()

        event = StreamEvent(
            event_type=StreamEventType.STARTED,
            message=f"Starting {self.state.total_tasks} tasks",
            progress=0.0
        )

        for handler in self._handlers:
            await handler.handle_event(event)

    async def start_task(self, task_id: str) -> StreamEmitter:
        """
        Start a task and return its emitter.

        Args:
            task_id: Task identifier

        Returns:
            StreamEmitter for the task
        """
        async with self._lock:
            self.state.current_task = task_id

        emitter = StreamEmitter(task_id=task_id)

        # Forward events to our handlers
        class TaskHandler:
            def __init__(self, tracker: 'ProgressTracker'):
                self.tracker = tracker

            async def handle_event(self, event: StreamEvent) -> None:
                # Update stage progress
                if event.event_type == StreamEventType.STAGE_CHANGE:
                    async with self.tracker._lock:
                        self.tracker.state.set_stage(event.stage or "", 0.0)

                elif event.event_type == StreamEventType.PROGRESS:
                    async with self.tracker._lock:
                        if self.tracker.state.current_stage:
                            self.tracker.state.stage_progress[
                                self.tracker.state.current_stage
                            ] = event.progress or 0.0

                # Forward to main handlers
                for handler in self.tracker._handlers:
                    await handler.handle_event(event)

        emitter.add_handler(TaskHandler(self))
        return emitter

    async def complete_task(self, task_id: str) -> None:
        """Mark task as complete"""
        async with self._lock:
            self.state.complete_task(task_id)

        await self._emit_progress()

    async def fail_task(self, task_id: str, error: str) -> None:
        """Mark task as failed"""
        async with self._lock:
            self.state.add_error(f"{task_id}: {error}")

        event = StreamEvent(
            event_type=StreamEventType.ERROR,
            task_id=task_id,
            message=error
        )

        for handler in self._handlers:
            await handler.handle_event(event)

    async def complete(self) -> None:
        """Mark all tracking as complete"""
        self.state.completed_at = time.time()

        event = StreamEvent(
            event_type=StreamEventType.COMPLETED,
            progress=1.0,
            message=f"Completed {self.state.completed_tasks}/{self.state.total_tasks} tasks",
            metadata=self.state.to_dict()
        )

        for handler in self._handlers:
            await handler.handle_event(event)


class ConsoleStreamHandler:
    """
    Stream handler that outputs to Rich console.

    Provides real-time progress bars, status updates, and streaming text.
    """

    def __init__(
        self,
        console: Optional[Any] = None,
        show_progress: bool = True,
        show_tokens: bool = False,
        show_files: bool = True,
        show_logs: bool = True
    ):
        """
        Initialize console handler.

        Args:
            console: Rich console instance (creates one if not provided)
            show_progress: Show progress bars
            show_tokens: Show individual tokens (verbose)
            show_files: Show file generation status
            show_logs: Show log messages
        """
        if console is None:
            from rich.console import Console
            console = Console()

        self.console = console
        self.show_progress = show_progress
        self.show_tokens = show_tokens
        self.show_files = show_files
        self.show_logs = show_logs

        self._progress = None
        self._task_id = None
        self._current_file = None
        self._token_buffer = []

    async def handle_event(self, event: StreamEvent) -> None:
        """Handle stream event"""
        if event.event_type == StreamEventType.STARTED:
            self._handle_started(event)

        elif event.event_type == StreamEventType.PROGRESS:
            self._handle_progress(event)

        elif event.event_type == StreamEventType.STAGE_CHANGE:
            self._handle_stage_change(event)

        elif event.event_type == StreamEventType.COMPLETED:
            self._handle_completed(event)

        elif event.event_type == StreamEventType.FAILED:
            self._handle_failed(event)

        elif event.event_type == StreamEventType.CANCELLED:
            self._handle_cancelled(event)

        elif event.event_type == StreamEventType.TOKEN:
            self._handle_token(event)

        elif event.event_type == StreamEventType.CHUNK:
            self._handle_chunk(event)

        elif event.event_type == StreamEventType.FILE_STARTED:
            self._handle_file_started(event)

        elif event.event_type == StreamEventType.FILE_COMPLETED:
            self._handle_file_completed(event)

        elif event.event_type == StreamEventType.STATUS:
            self._handle_status(event)

        elif event.event_type == StreamEventType.WARNING:
            self._handle_warning(event)

        elif event.event_type == StreamEventType.ERROR:
            self._handle_error(event)

        elif event.event_type == StreamEventType.LOG:
            self._handle_log(event)

    def _handle_started(self, event: StreamEvent) -> None:
        """Handle started event"""
        if self.show_progress:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console,
                transient=True
            )
            self._progress.start()
            self._task_id = self._progress.add_task(
                event.message or "Processing...",
                total=100
            )
        else:
            self.console.print(f"[bold green]▶[/bold green] {event.message}")

    def _handle_progress(self, event: StreamEvent) -> None:
        """Handle progress event"""
        if self._progress and self._task_id is not None and event.progress is not None:
            self._progress.update(
                self._task_id,
                completed=int(event.progress * 100),
                description=event.message or "Processing..."
            )

    def _handle_stage_change(self, event: StreamEvent) -> None:
        """Handle stage change"""
        if self._progress and self._task_id is not None:
            self._progress.update(
                self._task_id,
                description=f"[{event.stage}] {event.message or ''}"
            )
        else:
            self.console.print(f"[cyan]→[/cyan] {event.stage}: {event.message or ''}")

    def _handle_completed(self, event: StreamEvent) -> None:
        """Handle completed event"""
        if self._progress:
            self._progress.stop()
            self._progress = None

        duration = event.metadata.get("duration_seconds", 0)
        self.console.print(
            f"[bold green]✓[/bold green] {event.message} "
            f"[dim]({duration:.1f}s)[/dim]"
        )

    def _handle_failed(self, event: StreamEvent) -> None:
        """Handle failed event"""
        if self._progress:
            self._progress.stop()
            self._progress = None

        self.console.print(f"[bold red]✗[/bold red] {event.message}")

    def _handle_cancelled(self, event: StreamEvent) -> None:
        """Handle cancelled event"""
        if self._progress:
            self._progress.stop()
            self._progress = None

        self.console.print(f"[yellow]⚠[/yellow] {event.message}")

    def _handle_token(self, event: StreamEvent) -> None:
        """Handle token event"""
        if self.show_tokens and event.content:
            self._token_buffer.append(event.content)
            # Flush buffer periodically
            if len(self._token_buffer) >= 10:
                self.console.print("".join(self._token_buffer), end="")
                self._token_buffer = []

    def _handle_chunk(self, event: StreamEvent) -> None:
        """Handle chunk event"""
        if event.content:
            self.console.print(event.content, end="")

    def _handle_file_started(self, event: StreamEvent) -> None:
        """Handle file started"""
        if self.show_files:
            self._current_file = event.file_path
            self.console.print(f"[dim]  → Generating: {event.file_path}[/dim]")

    def _handle_file_completed(self, event: StreamEvent) -> None:
        """Handle file completed"""
        if self.show_files:
            size = event.metadata.get("size")
            size_str = f" ({size} bytes)" if size else ""
            self.console.print(f"[green]  ✓[/green] {event.file_path}{size_str}")
            self._current_file = None

    def _handle_status(self, event: StreamEvent) -> None:
        """Handle status message"""
        self.console.print(f"[blue]ℹ[/blue] {event.message}")

    def _handle_warning(self, event: StreamEvent) -> None:
        """Handle warning"""
        self.console.print(f"[yellow]⚠[/yellow] {event.message}")

    def _handle_error(self, event: StreamEvent) -> None:
        """Handle error"""
        self.console.print(f"[red]✗[/red] {event.message}")

    def _handle_log(self, event: StreamEvent) -> None:
        """Handle log message"""
        if self.show_logs:
            level = event.metadata.get("level", "info")
            color = {
                "debug": "dim",
                "info": "blue",
                "warning": "yellow",
                "error": "red"
            }.get(level, "white")

            self.console.print(f"[{color}]{event.message}[/{color}]")


class BufferStreamHandler:
    """
    Stream handler that buffers events.

    Useful for testing or collecting events for later processing.
    """

    def __init__(self):
        self.events: List[StreamEvent] = []
        self.content_buffer: str = ""

    async def handle_event(self, event: StreamEvent) -> None:
        """Buffer event"""
        self.events.append(event)

        if event.content:
            self.content_buffer += event.content

    def get_events_by_type(self, event_type: StreamEventType) -> List[StreamEvent]:
        """Get events of a specific type"""
        return [e for e in self.events if e.event_type == event_type]

    def clear(self) -> None:
        """Clear buffer"""
        self.events.clear()
        self.content_buffer = ""


class CallbackStreamHandler:
    """
    Stream handler that calls a callback function.

    Useful for custom handling or forwarding events.
    """

    def __init__(self, callback: Callable[[StreamEvent], None]):
        self.callback = callback

    async def handle_event(self, event: StreamEvent) -> None:
        """Call callback with event"""
        if asyncio.iscoroutinefunction(self.callback):
            await self.callback(event)
        else:
            self.callback(event)
