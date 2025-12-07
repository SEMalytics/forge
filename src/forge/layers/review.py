"""
Iterative refinement controller

Manages the fix-test-iterate cycle:
- Run tests
- Analyze failures
- Generate fixes
- Apply fixes
- Re-run tests
- Track learning
- Build fix pattern database
"""

import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from forge.layers.failure_analyzer import FailureAnalyzer, FixSuggestion, Priority
from forge.layers.fix_generator import FixGenerator, GeneratedFix
from forge.layers.testing import TestingOrchestrator, TestingConfig, ComprehensiveTestReport
from forge.core.state_manager import StateManager
from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class ReviewError(ForgeError):
    """Errors during review iteration"""
    pass


@dataclass
class IterationResult:
    """Result of a single iteration"""
    iteration_number: int
    tests_passed: int
    tests_failed: int
    fixes_attempted: int
    fixes_successful: int
    duration_seconds: float
    test_report: Optional[ComprehensiveTestReport] = None
    suggestions: List[FixSuggestion] = field(default_factory=list)
    applied_fixes: List[GeneratedFix] = field(default_factory=list)


@dataclass
class ReviewSummary:
    """Complete review session summary"""
    project_id: str
    total_iterations: int
    final_status: str  # 'passed', 'failed', 'max_iterations'
    iterations: List[IterationResult]
    total_duration_seconds: float
    learning_database_updated: bool = False

    @property
    def success(self) -> bool:
        """Whether all tests eventually passed"""
        return self.final_status == 'passed'

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'project_id': self.project_id,
            'total_iterations': self.total_iterations,
            'final_status': self.final_status,
            'success': self.success,
            'total_duration_seconds': round(self.total_duration_seconds, 2),
            'learning_database_updated': self.learning_database_updated,
            'iterations': [
                {
                    'iteration': it.iteration_number,
                    'tests_passed': it.tests_passed,
                    'tests_failed': it.tests_failed,
                    'fixes_attempted': it.fixes_attempted,
                    'fixes_successful': it.fixes_successful,
                    'duration_seconds': round(it.duration_seconds, 2)
                }
                for it in self.iterations
            ]
        }


class ReviewLayer:
    """
    Iterative refinement controller.

    Features:
    - Automated fix-test iteration
    - Smart fix prioritization
    - Learning from successful fixes
    - Pattern database building
    - Progress tracking
    - Rollback on failure
    """

    def __init__(
        self,
        testing_config: Optional[TestingConfig] = None,
        console: Optional[Console] = None,
        state_manager: Optional[StateManager] = None,
        learning_db_path: Optional[Path] = None
    ):
        """
        Initialize review layer.

        Args:
            testing_config: Testing configuration
            console: Rich console for output
            state_manager: State manager for persistence
            learning_db_path: Path to learning database
        """
        self.testing_config = testing_config or TestingConfig()
        self.console = console or Console()
        self.state_manager = state_manager or StateManager()
        self.learning_db_path = learning_db_path or Path(".forge/learning/fixes.json")
        self.learning_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.analyzer = FailureAnalyzer()
        self.fix_generator = FixGenerator()
        self.test_orchestrator = TestingOrchestrator(
            config=self.testing_config,
            console=self.console
        )

        logger.info("Initialized ReviewLayer")

    async def iterate_until_passing(
        self,
        project_id: str,
        code_files: Dict[str, str],
        tech_stack: Optional[List[str]] = None,
        project_context: str = "",
        max_iterations: int = 5,
        output_dir: Optional[Path] = None
    ) -> ReviewSummary:
        """
        Iterate until all tests pass or max iterations reached.

        Args:
            project_id: Project identifier
            code_files: Initial code files
            tech_stack: Technologies used
            project_context: Project description
            max_iterations: Maximum iteration attempts
            output_dir: Directory for code output

        Returns:
            ReviewSummary with complete iteration history

        Raises:
            ReviewError: If iteration fails critically
        """
        logger.info(
            f"Starting review iteration for {project_id} "
            f"(max {max_iterations} iterations)"
        )

        start_time = time.time()

        # Setup output directory
        if output_dir is None:
            output_dir = Path(".forge/output") / project_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write initial code files
        current_files = code_files.copy()
        self._write_files(current_files, output_dir)

        # Track iterations
        iterations: List[IterationResult] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=self.console
        ) as progress:

            overall_task = progress.add_task(
                "Review iteration", total=max_iterations
            )

            for iteration_num in range(1, max_iterations + 1):
                self.console.print(f"\n[bold cyan]Iteration {iteration_num}/{max_iterations}[/bold cyan]\n")

                # Run iteration
                iteration_result = await self._run_iteration(
                    iteration_num=iteration_num,
                    project_id=project_id,
                    current_files=current_files,
                    tech_stack=tech_stack,
                    project_context=project_context,
                    output_dir=output_dir,
                    progress=progress
                )

                iterations.append(iteration_result)

                # Update progress
                progress.update(overall_task, advance=1)

                # Check if all tests passed
                if iteration_result.tests_failed == 0:
                    self.console.print("\n[bold green]✓ All tests passing![/bold green]\n")

                    summary = ReviewSummary(
                        project_id=project_id,
                        total_iterations=iteration_num,
                        final_status='passed',
                        iterations=iterations,
                        total_duration_seconds=time.time() - start_time
                    )

                    # Update learning database
                    self._update_learning_database(summary)
                    summary.learning_database_updated = True

                    return summary

                # Display iteration summary
                self._display_iteration_summary(iteration_result)

        # Max iterations reached without passing
        self.console.print("\n[bold yellow]⚠ Maximum iterations reached[/bold yellow]\n")

        summary = ReviewSummary(
            project_id=project_id,
            total_iterations=max_iterations,
            final_status='max_iterations',
            iterations=iterations,
            total_duration_seconds=time.time() - start_time
        )

        return summary

    async def _run_iteration(
        self,
        iteration_num: int,
        project_id: str,
        current_files: Dict[str, str],
        tech_stack: Optional[List[str]],
        project_context: str,
        output_dir: Path,
        progress: Progress
    ) -> IterationResult:
        """Run a single iteration"""
        start_time = time.time()

        # Step 1: Run tests
        test_task = progress.add_task(f"  Running tests...", total=100)

        test_report = await self.test_orchestrator.test_project(
            project_id=project_id,
            code_files=current_files,
            tech_stack=tech_stack,
            project_context=project_context
        )

        progress.update(test_task, completed=100, description="  ✓ Tests complete")

        # Check if tests passed
        if test_report.all_passed and test_report.security_passed:
            return IterationResult(
                iteration_number=iteration_num,
                tests_passed=test_report.passed_tests,
                tests_failed=test_report.failed_tests,
                fixes_attempted=0,
                fixes_successful=0,
                duration_seconds=time.time() - start_time,
                test_report=test_report
            )

        # Step 2: Analyze failures
        analysis_task = progress.add_task(f"  Analyzing failures...", total=100)

        suggestions = self.analyzer.analyze_failures(
            test_results=test_report.unit_test_result,
            security_results=test_report.security_scan_result,
            performance_results=test_report.performance_results,
            code_files=current_files
        )

        progress.update(analysis_task, completed=100, description=f"  ✓ {len(suggestions)} issues identified")

        # Step 3: Generate fixes
        fix_task = progress.add_task(f"  Generating fixes...", total=100)

        fixes = await self.fix_generator.generate_fixes(
            suggestions=suggestions,
            code_files=current_files,
            project_context=project_context
        )

        # Prioritize fixes
        fixes = self.fix_generator.prioritize_fixes(fixes)

        progress.update(fix_task, completed=100, description=f"  ✓ {len(fixes)} fixes generated")

        # Step 4: Apply fixes
        apply_task = progress.add_task(f"  Applying fixes...", total=len(fixes) if fixes else 1)

        applied_fixes = []
        successful_fixes = 0

        for fix in fixes[:3]:  # Apply top 3 fixes per iteration
            success = await self.fix_generator.apply_fix(fix, output_dir)

            if success:
                # Update current_files with changes
                for file_path, new_content in fix.file_changes.items():
                    current_files[file_path] = new_content

                applied_fixes.append(fix)
                successful_fixes += 1

            progress.update(apply_task, advance=1)

        progress.update(apply_task, description=f"  ✓ {successful_fixes} fixes applied")

        return IterationResult(
            iteration_number=iteration_num,
            tests_passed=test_report.passed_tests,
            tests_failed=test_report.failed_tests,
            fixes_attempted=len(applied_fixes),
            fixes_successful=successful_fixes,
            duration_seconds=time.time() - start_time,
            test_report=test_report,
            suggestions=suggestions,
            applied_fixes=applied_fixes
        )

    def _write_files(self, files: Dict[str, str], output_dir: Path):
        """Write code files to output directory"""
        for file_path, content in files.items():
            full_path = output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

    def _display_iteration_summary(self, result: IterationResult):
        """Display summary of iteration"""
        # Create summary table
        table = Table(title=f"Iteration {result.iteration_number} Summary", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value")

        # Test results
        table.add_row("Tests Passed", f"[green]{result.tests_passed}[/green]")
        table.add_row("Tests Failed", f"[red]{result.tests_failed}[/red]" if result.tests_failed else "0")

        # Fix results
        table.add_row("Fixes Attempted", str(result.fixes_attempted))
        table.add_row("Fixes Successful", f"[green]{result.fixes_successful}[/green]")

        # Duration
        table.add_row("Duration", f"{result.duration_seconds:.1f}s")

        self.console.print(table)
        self.console.print()

        # Show applied fixes
        if result.applied_fixes:
            self.console.print("[bold]Applied Fixes:[/bold]")
            for fix in result.applied_fixes:
                impact = self.fix_generator.estimate_impact(fix)
                self.console.print(f"  • {fix.commit_message.split(chr(10))[0]} ({impact})")
            self.console.print()

    def _update_learning_database(self, summary: ReviewSummary):
        """Update learning database with successful fixes"""
        try:
            # Load existing database
            if self.learning_db_path.exists():
                data = json.loads(self.learning_db_path.read_text())
            else:
                data = {
                    'successful_patterns': [],
                    'fix_statistics': {
                        'total_sessions': 0,
                        'successful_sessions': 0,
                        'total_fixes_applied': 0,
                        'avg_iterations_to_success': 0.0
                    }
                }

            # Extract successful fix patterns
            for iteration in summary.iterations:
                for fix in iteration.applied_fixes:
                    if fix.success:
                        pattern = {
                            'failure_type': fix.suggestion.failure_type.value,
                            'root_cause': fix.suggestion.root_cause,
                            'fix_applied': fix.suggestion.suggested_fix,
                            'confidence': fix.suggestion.confidence,
                            'priority': fix.suggestion.priority.value,
                            'success': True
                        }
                        data['successful_patterns'].append(pattern)

            # Update statistics
            data['fix_statistics']['total_sessions'] += 1
            if summary.success:
                data['fix_statistics']['successful_sessions'] += 1

            data['fix_statistics']['total_fixes_applied'] += sum(
                it.fixes_successful for it in summary.iterations
            )

            if summary.success:
                current_avg = data['fix_statistics']['avg_iterations_to_success']
                total_successful = data['fix_statistics']['successful_sessions']

                # Update running average
                data['fix_statistics']['avg_iterations_to_success'] = (
                    (current_avg * (total_successful - 1) + summary.total_iterations) /
                    total_successful
                )

            # Save database
            self.learning_db_path.write_text(json.dumps(data, indent=2))

            logger.info(f"Updated learning database: {self.learning_db_path}")

        except Exception as e:
            logger.error(f"Failed to update learning database: {e}")

    def get_learning_statistics(self) -> Dict:
        """Get learning database statistics"""
        if not self.learning_db_path.exists():
            return {
                'total_sessions': 0,
                'successful_sessions': 0,
                'success_rate': 0.0,
                'total_patterns': 0
            }

        try:
            data = json.loads(self.learning_db_path.read_text())

            stats = data['fix_statistics']
            success_rate = (
                stats['successful_sessions'] / stats['total_sessions']
                if stats['total_sessions'] > 0 else 0.0
            )

            return {
                'total_sessions': stats['total_sessions'],
                'successful_sessions': stats['successful_sessions'],
                'success_rate': success_rate,
                'total_patterns': len(data['successful_patterns']),
                'avg_iterations_to_success': stats['avg_iterations_to_success']
            }

        except Exception as e:
            logger.error(f"Failed to read learning database: {e}")
            return {}

    def close(self):
        """Close resources"""
        if self.analyzer:
            self.analyzer.close()
        if self.fix_generator:
            self.fix_generator.close()
        if self.test_orchestrator:
            self.test_orchestrator.close()
