"""
Generation orchestration layer

Handles task execution with dependency management, parallel execution,
and progress tracking.
"""

import asyncio
import time
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.console import Console
from rich.table import Table

from forge.generators.base import CodeGenerator, GenerationContext, GenerationResult, GeneratorError
from forge.integrations.compound_engineering import Task
from forge.core.state_manager import StateManager
from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class GenerationError(ForgeError):
    """Errors during generation orchestration"""
    pass


def _build_codebase_context(max_files: int = 20, max_size_per_file: int = 1000) -> Dict[str, str]:
    """
    Build codebase context from existing project files.

    Args:
        max_files: Maximum number of files to include
        max_size_per_file: Maximum characters per file

    Returns:
        Dictionary mapping file paths to content snippets
    """
    file_structure = {}
    cwd = Path.cwd()

    # Key files to include for context
    important_patterns = [
        "README.md",
        "pyproject.toml",
        "src/forge/core/*.py",
        "src/forge/cli/*.py",
        "src/forge/generators/base.py",
        "src/forge/integrations/*.py",
    ]

    file_count = 0
    for pattern in important_patterns:
        if file_count >= max_files:
            break

        for file_path in cwd.glob(pattern):
            if file_count >= max_files:
                break

            if file_path.is_file() and file_path.suffix in ['.py', '.md', '.toml', '.yaml', '.json']:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    relative_path = str(file_path.relative_to(cwd))

                    # Include snippet for context
                    file_structure[relative_path] = content[:max_size_per_file]
                    file_count += 1
                except Exception as e:
                    logger.debug(f"Skipping {file_path}: {e}")
                    continue

    return file_structure


class TaskStatus(Enum):
    """Task generation status"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class TaskExecution:
    """Tracks execution of a single task"""
    task: Task
    status: TaskStatus = TaskStatus.QUEUED
    result: Optional[GenerationResult] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress_task_id: Optional[TaskID] = None

    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    @property
    def is_ready(self) -> bool:
        """Check if task is ready to execute"""
        return self.status == TaskStatus.QUEUED


class GenerationOrchestrator:
    """
    Orchestrates code generation across multiple tasks.

    Features:
    - Dependency-aware task ordering
    - Parallel execution for independent tasks
    - Real-time progress tracking
    - Result aggregation
    - Error recovery
    """

    def __init__(
        self,
        generator: CodeGenerator,
        state_manager: Optional[StateManager] = None,
        console: Optional[Console] = None,
        max_parallel: int = 3
    ):
        """
        Initialize generation orchestrator.

        Args:
            generator: Code generator to use
            state_manager: State manager for persistence
            console: Rich console for output
            max_parallel: Maximum parallel tasks (if generator supports it)
        """
        self.generator = generator
        self.state_manager = state_manager or StateManager()
        self.console = console or Console()
        self.max_parallel = max_parallel if generator.supports_parallel() else 1

        logger.info(f"Initialized GenerationOrchestrator (max_parallel={self.max_parallel})")

    async def generate_project(
        self,
        project_id: str,
        tasks: List[Task],
        project_context: str
    ) -> Dict[str, GenerationResult]:
        """
        Generate code for all project tasks.

        Args:
            project_id: Project ID
            tasks: List of tasks to generate
            project_context: Project context/description

        Returns:
            Dictionary mapping task IDs to generation results

        Raises:
            GenerationError: If generation fails
        """
        logger.info(f"Generating project {project_id} with {len(tasks)} tasks")

        # Validate dependencies
        self._validate_dependencies(tasks)

        # Create task executions
        executions = {
            task.id: TaskExecution(task=task)
            for task in tasks
        }

        # Execute tasks with progress tracking
        results = await self._execute_with_progress(
            project_id=project_id,
            executions=executions,
            project_context=project_context
        )

        # Display summary
        self._display_summary(results)

        return results

    def _validate_dependencies(self, tasks: List[Task]):
        """
        Validate task dependencies.

        Args:
            tasks: Tasks to validate

        Raises:
            GenerationError: If dependencies are invalid
        """
        task_ids = {task.id for task in tasks}

        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    raise GenerationError(
                        f"Task {task.id} has invalid dependency: {dep_id}"
                    )

        logger.debug("Task dependencies validated")

    async def _execute_with_progress(
        self,
        project_id: str,
        executions: Dict[str, TaskExecution],
        project_context: str
    ) -> Dict[str, GenerationResult]:
        """
        Execute tasks with progress tracking.

        Args:
            project_id: Project ID
            executions: Task executions
            project_context: Project context

        Returns:
            Dictionary mapping task IDs to results
        """
        results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:

            # Create progress tasks
            for execution in executions.values():
                execution.progress_task_id = progress.add_task(
                    f"{execution.task.id}: {execution.task.title}",
                    total=100,
                    visible=True
                )

            # Execute tasks
            if self.max_parallel > 1:
                results = await self._execute_parallel(
                    project_id, executions, project_context, progress
                )
            else:
                results = await self._execute_sequential(
                    project_id, executions, project_context, progress
                )

        return results

    async def _execute_parallel(
        self,
        project_id: str,
        executions: Dict[str, TaskExecution],
        project_context: str,
        progress: Progress
    ) -> Dict[str, GenerationResult]:
        """Execute tasks in parallel respecting dependencies"""
        results = {}
        completed: Set[str] = set()
        in_progress: Set[str] = set()

        while len(completed) < len(executions):
            # Find ready tasks
            ready_tasks = []
            for task_id, execution in executions.items():
                if task_id in completed or task_id in in_progress:
                    continue

                # Check if all dependencies are complete
                deps_complete = all(
                    dep in completed
                    for dep in execution.task.dependencies
                )

                if deps_complete:
                    ready_tasks.append((task_id, execution))

            # Limit parallel execution
            ready_tasks = ready_tasks[:self.max_parallel - len(in_progress)]

            if not ready_tasks and not in_progress:
                # Deadlock - no tasks ready and none in progress
                raise GenerationError("Dependency deadlock detected")

            # Start ready tasks
            tasks_to_await = []
            for task_id, execution in ready_tasks:
                in_progress.add(task_id)
                task = self._execute_task(
                    project_id, execution, project_context, progress, results
                )
                tasks_to_await.append((task_id, task))

            # Wait for any task to complete
            if tasks_to_await:
                for task_id, coro in tasks_to_await:
                    try:
                        await coro
                        completed.add(task_id)
                        in_progress.remove(task_id)
                    except Exception as e:
                        logger.error(f"Task {task_id} failed: {e}")
                        completed.add(task_id)
                        in_progress.remove(task_id)

            # Small delay to avoid busy loop
            await asyncio.sleep(0.1)

        return results

    async def _execute_sequential(
        self,
        project_id: str,
        executions: Dict[str, TaskExecution],
        project_context: str,
        progress: Progress
    ) -> Dict[str, GenerationResult]:
        """Execute tasks sequentially in dependency order"""
        results = {}
        completed: Set[str] = set()

        # Topological sort
        ordered_tasks = self._topological_sort(list(executions.values()))

        for execution in ordered_tasks:
            await self._execute_task(
                project_id, execution, project_context, progress, results
            )
            completed.add(execution.task.id)

        return results

    def _topological_sort(self, executions: List[TaskExecution]) -> List[TaskExecution]:
        """Sort tasks by dependencies using topological sort"""
        from collections import deque

        # Build adjacency list and in-degree map
        in_degree = {exec.task.id: 0 for exec in executions}
        exec_map = {exec.task.id: exec for exec in executions}

        for execution in executions:
            for dep in execution.task.dependencies:
                in_degree[execution.task.id] += 1

        # Find tasks with no dependencies
        queue = deque([
            exec for exec in executions
            if in_degree[exec.task.id] == 0
        ])

        result = []

        while queue:
            execution = queue.popleft()
            result.append(execution)

            # Reduce in-degree for dependent tasks
            for other_exec in executions:
                if execution.task.id in other_exec.task.dependencies:
                    in_degree[other_exec.task.id] -= 1
                    if in_degree[other_exec.task.id] == 0:
                        queue.append(other_exec)

        if len(result) != len(executions):
            raise GenerationError("Circular dependency detected")

        return result

    async def _execute_task(
        self,
        project_id: str,
        execution: TaskExecution,
        project_context: str,
        progress: Progress,
        results: Dict[str, GenerationResult]
    ):
        """Execute a single task"""
        task = execution.task

        try:
            # Update status
            execution.status = TaskStatus.IN_PROGRESS
            execution.started_at = time.time()

            # Update progress
            if execution.progress_task_id is not None:
                progress.update(
                    execution.progress_task_id,
                    description=f"{task.id}: {task.title} [yellow]⧗ In Progress[/yellow]",
                    completed=10
                )

            # Build generation context with codebase file structure
            codebase_context = _build_codebase_context()
            logger.debug(f"Including {len(codebase_context)} files in generation context")

            context = GenerationContext(
                task_id=task.id,
                specification=task.description,
                project_context=project_context,
                tech_stack=getattr(task, 'tech_stack', []),
                dependencies=task.dependencies,
                knowledgeforge_patterns=task.kf_patterns,
                file_structure=codebase_context,
                metadata={
                    "title": task.title,
                    "priority": task.priority,
                    "complexity": task.estimated_complexity
                }
            )

            # Generate code
            logger.info(f"Generating code for task {task.id}")

            result = await self.generator.generate(context)

            # Update execution
            execution.result = result
            execution.completed_at = time.time()

            if result.success:
                execution.status = TaskStatus.COMPLETE
                results[task.id] = result

                # Update progress
                if execution.progress_task_id is not None:
                    duration_str = f"({execution.duration:.0f}s)" if execution.duration else ""
                    progress.update(
                        execution.progress_task_id,
                        description=f"{task.id}: {task.title} [green]✓ Complete[/green] {duration_str}",
                        completed=100
                    )

                # Save to state manager
                if self.state_manager:
                    self._save_task_result(project_id, task, result)

            else:
                execution.status = TaskStatus.FAILED
                logger.error(f"Task {task.id} failed: {result.error}")

                # Update progress
                if execution.progress_task_id is not None:
                    progress.update(
                        execution.progress_task_id,
                        description=f"{task.id}: {task.title} [red]✗ Failed[/red]",
                        completed=100
                    )

        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.completed_at = time.time()

            logger.error(f"Task {task.id} execution failed: {e}")

            # Update progress
            if execution.progress_task_id is not None:
                progress.update(
                    execution.progress_task_id,
                    description=f"{task.id}: {task.title} [red]✗ Error[/red]",
                    completed=100
                )

    def _save_task_result(
        self,
        project_id: str,
        task: Task,
        result: GenerationResult
    ):
        """Save task generation result to state"""
        try:
            self.state_manager.update_task_status(
                project_id=project_id,
                task_id=task.id,
                status="complete" if result.success else "failed",
                metadata={
                    "generation_result": result.to_dict(),
                    "files_generated": list(result.files.keys())
                }
            )
        except Exception as e:
            logger.warning(f"Failed to save task result: {e}")

    def _display_summary(self, results: Dict[str, GenerationResult]):
        """Display generation summary"""
        self.console.print("\n[bold]Generation Summary:[/bold]\n")

        # Create summary table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Task ID")
        table.add_column("Status")
        table.add_column("Files")
        table.add_column("Duration")
        table.add_column("Tokens")

        total_files = 0
        total_duration = 0.0
        total_tokens = 0
        success_count = 0

        for task_id, result in results.items():
            if result.success:
                status = "[green]✓ Success[/green]"
                success_count += 1
            else:
                status = "[red]✗ Failed[/red]"

            file_count = len(result.files)
            total_files += file_count

            duration = f"{result.duration_seconds:.1f}s"
            total_duration += result.duration_seconds

            tokens = str(result.tokens_used) if result.tokens_used else "-"
            if result.tokens_used:
                total_tokens += result.tokens_used

            table.add_row(
                task_id,
                status,
                str(file_count),
                duration,
                tokens
            )

        self.console.print(table)

        # Overall stats
        self.console.print(f"\n[bold]Overall:[/bold]")
        self.console.print(f"  Tasks: {success_count}/{len(results)} successful")
        self.console.print(f"  Files: {total_files} generated")
        self.console.print(f"  Duration: {total_duration:.1f}s")
        if total_tokens > 0:
            self.console.print(f"  Tokens: {total_tokens:,}")
        self.console.print()

    def close(self):
        """Close state manager"""
        if self.state_manager:
            self.state_manager.close()
