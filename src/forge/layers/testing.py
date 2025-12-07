"""
Testing orchestration layer

Coordinates all testing phases:
1. Unit tests
2. Integration tests
3. Security scanning
4. Performance benchmarking

Provides comprehensive test reporting and validation.
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from forge.testing.generator import TestGenerator, TestType
from forge.testing.docker_runner import DockerTestRunner, TestResult, TestFramework
from forge.testing.security_scanner import SecurityScanner, ScanResult, Severity
from forge.testing.performance import PerformanceBenchmark, BenchmarkResult, PerformanceThresholds
from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class TestingError(ForgeError):
    """Errors during testing orchestration"""
    pass


@dataclass
class TestingConfig:
    """Testing configuration"""
    run_unit_tests: bool = True
    run_integration_tests: bool = True
    run_security_scan: bool = True
    run_performance_tests: bool = False

    generate_tests: bool = True
    use_docker: bool = True

    min_coverage: float = 80.0
    security_required: bool = True

    performance_thresholds: Optional[PerformanceThresholds] = None


@dataclass
class ComprehensiveTestReport:
    """Complete testing report"""
    project_id: str

    # Test execution
    unit_test_result: Optional[TestResult] = None
    integration_test_result: Optional[TestResult] = None

    # Security
    security_scan_result: Optional[ScanResult] = None

    # Performance
    performance_results: List[BenchmarkResult] = field(default_factory=list)

    # Overall
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    coverage_percent: Optional[float] = None

    duration_seconds: float = 0.0

    # Status
    all_passed: bool = False
    security_passed: bool = False
    performance_passed: bool = False

    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'project_id': self.project_id,
            'unit_tests': self.unit_test_result.__dict__ if self.unit_test_result else None,
            'integration_tests': self.integration_test_result.__dict__ if self.integration_test_result else None,
            'security': self.security_scan_result.to_dict() if self.security_scan_result else None,
            'performance': [r.to_dict() for r in self.performance_results],
            'summary': {
                'total_tests': self.total_tests,
                'passed_tests': self.passed_tests,
                'failed_tests': self.failed_tests,
                'coverage_percent': self.coverage_percent,
                'duration_seconds': round(self.duration_seconds, 2),
                'all_passed': self.all_passed,
                'security_passed': self.security_passed,
                'performance_passed': self.performance_passed
            },
            'errors': self.errors
        }


class TestingOrchestrator:
    """
    Orchestrates comprehensive testing workflow.

    Phases:
    1. Test Generation - Generate tests from code
    2. Unit Testing - Run unit tests in Docker
    3. Integration Testing - Run integration tests
    4. Security Scanning - Scan for vulnerabilities
    5. Performance Testing - Run benchmarks
    6. Report Generation - Aggregate results
    """

    def __init__(
        self,
        config: Optional[TestingConfig] = None,
        console: Optional[Console] = None,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize testing orchestrator.

        Args:
            config: Testing configuration
            console: Rich console for output
            output_dir: Directory for test outputs
        """
        self.config = config or TestingConfig()
        self.console = console or Console()
        self.output_dir = output_dir or Path(".forge/test-results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.test_generator = TestGenerator()
        self.docker_runner = DockerTestRunner()
        self.security_scanner = SecurityScanner()
        self.performance_benchmark = PerformanceBenchmark()

        logger.info("Initialized TestingOrchestrator")

    async def test_project(
        self,
        project_id: str,
        code_files: Dict[str, str],
        tech_stack: Optional[List[str]] = None,
        project_context: str = ""
    ) -> ComprehensiveTestReport:
        """
        Run comprehensive testing for project.

        Args:
            project_id: Project identifier
            code_files: Dictionary mapping file paths to code content
            tech_stack: Technologies used
            project_context: Project description

        Returns:
            Comprehensive test report

        Raises:
            TestingError: If testing fails critically
        """
        logger.info(f"Starting comprehensive testing for project {project_id}")

        start_time = time.time()
        report = ComprehensiveTestReport(project_id=project_id)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=self.console
        ) as progress:

            # Phase 1: Generate Tests
            if self.config.generate_tests:
                task_id = progress.add_task("Generating tests...", total=100)
                try:
                    test_files = await self._generate_tests(
                        code_files, tech_stack, project_context, progress, task_id
                    )
                    progress.update(task_id, completed=100, description="✓ Tests generated")
                except Exception as e:
                    progress.update(task_id, description=f"✗ Test generation failed: {e}")
                    report.errors.append(f"Test generation: {e}")
                    test_files = {}
            else:
                test_files = {}

            # Phase 2: Unit Tests
            if self.config.run_unit_tests and test_files:
                task_id = progress.add_task("Running unit tests...", total=100)
                try:
                    report.unit_test_result = await self._run_unit_tests(
                        test_files, code_files, progress, task_id
                    )
                    progress.update(task_id, completed=100, description="✓ Unit tests complete")
                except Exception as e:
                    progress.update(task_id, description=f"✗ Unit tests failed: {e}")
                    report.errors.append(f"Unit tests: {e}")

            # Phase 3: Integration Tests
            if self.config.run_integration_tests and test_files:
                task_id = progress.add_task("Running integration tests...", total=100)
                try:
                    report.integration_test_result = await self._run_integration_tests(
                        test_files, code_files, progress, task_id
                    )
                    progress.update(task_id, completed=100, description="✓ Integration tests complete")
                except Exception as e:
                    progress.update(task_id, description=f"✗ Integration tests failed: {e}")
                    report.errors.append(f"Integration tests: {e}")

            # Phase 4: Security Scanning
            if self.config.run_security_scan:
                task_id = progress.add_task("Running security scan...", total=100)
                try:
                    report.security_scan_result = await self._run_security_scan(
                        code_files, progress, task_id
                    )
                    progress.update(task_id, completed=100, description="✓ Security scan complete")
                except Exception as e:
                    progress.update(task_id, description=f"✗ Security scan failed: {e}")
                    report.errors.append(f"Security scan: {e}")

            # Phase 5: Performance Testing
            if self.config.run_performance_tests:
                task_id = progress.add_task("Running performance tests...", total=100)
                try:
                    report.performance_results = await self._run_performance_tests(
                        code_files, progress, task_id
                    )
                    progress.update(task_id, completed=100, description="✓ Performance tests complete")
                except Exception as e:
                    progress.update(task_id, description=f"✗ Performance tests failed: {e}")
                    report.errors.append(f"Performance tests: {e}")

        # Calculate summary
        report.duration_seconds = time.time() - start_time
        self._calculate_summary(report)

        # Display results
        self._display_results(report)

        # Save report
        self._save_report(report)

        return report

    async def _generate_tests(
        self,
        code_files: Dict[str, str],
        tech_stack: Optional[List[str]],
        project_context: str,
        progress: Progress,
        task_id: TaskID
    ) -> Dict[str, str]:
        """Generate tests from code"""
        progress.update(task_id, completed=10)

        test_files = self.test_generator.generate_tests(
            code_files=code_files,
            tech_stack=tech_stack,
            project_context=project_context,
            test_types=[TestType.UNIT, TestType.INTEGRATION]
        )

        progress.update(task_id, completed=90)

        logger.info(f"Generated {len(test_files)} test files")
        return test_files

    async def _run_unit_tests(
        self,
        test_files: Dict[str, str],
        source_files: Dict[str, str],
        progress: Progress,
        task_id: TaskID
    ) -> TestResult:
        """Run unit tests"""
        progress.update(task_id, completed=10)

        # Filter unit tests
        unit_tests = {
            path: content for path, content in test_files.items()
            if 'unit' in path or 'test_' in path
        }

        result = await self.docker_runner.run_tests(
            test_files=unit_tests,
            source_files=source_files,
            framework=None  # Auto-detect
        )

        progress.update(task_id, completed=90)

        logger.info(
            f"Unit tests: {result.passed} passed, {result.failed} failed, "
            f"coverage: {result.coverage_percent}%"
        )

        return result

    async def _run_integration_tests(
        self,
        test_files: Dict[str, str],
        source_files: Dict[str, str],
        progress: Progress,
        task_id: TaskID
    ) -> TestResult:
        """Run integration tests"""
        progress.update(task_id, completed=10)

        # Filter integration tests
        integration_tests = {
            path: content for path, content in test_files.items()
            if 'integration' in path or 'e2e' in path
        }

        if not integration_tests:
            # No integration tests found
            return TestResult(framework=TestFramework.PYTEST)

        result = await self.docker_runner.run_tests(
            test_files=integration_tests,
            source_files=source_files,
            framework=None  # Auto-detect
        )

        progress.update(task_id, completed=90)

        logger.info(
            f"Integration tests: {result.passed} passed, {result.failed} failed"
        )

        return result

    async def _run_security_scan(
        self,
        code_files: Dict[str, str],
        progress: Progress,
        task_id: TaskID
    ) -> ScanResult:
        """Run security scan"""
        progress.update(task_id, completed=10)

        # Run scan in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.security_scanner.scan,
            code_files,
            None  # dependencies
        )

        progress.update(task_id, completed=90)

        logger.info(
            f"Security scan: {result.total_count} vulnerabilities found "
            f"({result.critical_count} critical, {result.high_count} high)"
        )

        return result

    async def _run_performance_tests(
        self,
        code_files: Dict[str, str],
        progress: Progress,
        task_id: TaskID
    ) -> List[BenchmarkResult]:
        """Run performance tests"""
        progress.update(task_id, completed=10)

        results = []

        # This is a simplified implementation
        # In a real scenario, you would:
        # 1. Identify performance-critical functions
        # 2. Create benchmark scenarios
        # 3. Run load tests

        # Example: Benchmark a simple function
        async def sample_function():
            await asyncio.sleep(0.01)  # Simulate work

        result = await self.performance_benchmark.benchmark_function(
            name="sample_benchmark",
            func=sample_function,
            iterations=100,
            concurrency=10,
            thresholds=self.config.performance_thresholds
        )

        results.append(result)

        progress.update(task_id, completed=90)

        logger.info(f"Performance tests: {len(results)} benchmarks completed")

        return results

    def _calculate_summary(self, report: ComprehensiveTestReport):
        """Calculate summary statistics"""
        # Test counts
        if report.unit_test_result:
            report.total_tests += report.unit_test_result.total
            report.passed_tests += report.unit_test_result.passed
            report.failed_tests += report.unit_test_result.failed

        if report.integration_test_result:
            report.total_tests += report.integration_test_result.total
            report.passed_tests += report.integration_test_result.passed
            report.failed_tests += report.integration_test_result.failed

        # Coverage
        if report.unit_test_result and report.unit_test_result.coverage_percent:
            report.coverage_percent = report.unit_test_result.coverage_percent

        # Overall pass/fail
        report.all_passed = (
            report.failed_tests == 0 and
            (report.coverage_percent or 0) >= self.config.min_coverage
        )

        # Security pass/fail
        if report.security_scan_result:
            if self.config.security_required:
                report.security_passed = report.security_scan_result.is_secure
            else:
                report.security_passed = True
        else:
            report.security_passed = not self.config.security_required

        # Performance pass/fail
        if report.performance_results:
            report.performance_passed = all(r.passed for r in report.performance_results)
        else:
            report.performance_passed = True

    def _display_results(self, report: ComprehensiveTestReport):
        """Display test results"""
        self.console.print()
        self.console.print(Panel(
            f"[bold]Testing Report: {report.project_id}[/bold]",
            border_style="blue"
        ))

        # Summary table
        summary_table = Table(title="Summary", show_header=False)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value")

        summary_table.add_row("Total Tests", str(report.total_tests))
        summary_table.add_row("Passed", f"[green]{report.passed_tests}[/green]")
        summary_table.add_row("Failed", f"[red]{report.failed_tests}[/red]" if report.failed_tests else "0")

        if report.coverage_percent is not None:
            coverage_style = "green" if report.coverage_percent >= self.config.min_coverage else "yellow"
            summary_table.add_row(
                "Coverage",
                f"[{coverage_style}]{report.coverage_percent:.1f}%[/{coverage_style}]"
            )

        summary_table.add_row("Duration", f"{report.duration_seconds:.2f}s")

        self.console.print(summary_table)
        self.console.print()

        # Security results
        if report.security_scan_result:
            security_status = "✓ PASS" if report.security_passed else "✗ FAIL"
            security_style = "green" if report.security_passed else "red"

            self.console.print(f"[bold]Security Scan [{security_style}]{security_status}[/{security_style}][/bold]")
            self.console.print(f"  Vulnerabilities: {report.security_scan_result.total_count}")
            self.console.print(f"  Critical: {report.security_scan_result.critical_count}")
            self.console.print(f"  High: {report.security_scan_result.high_count}")
            self.console.print(f"  OWASP Score: {report.security_scan_result.owasp_score:.1f}/100")
            self.console.print()

        # Performance results
        if report.performance_results:
            perf_status = "✓ PASS" if report.performance_passed else "✗ FAIL"
            perf_style = "green" if report.performance_passed else "red"

            self.console.print(f"[bold]Performance Tests [{perf_style}]{perf_status}[/{perf_style}][/bold]")
            for result in report.performance_results:
                self.console.print(
                    f"  {result.name}: "
                    f"P95={result.metrics.p95_ms:.2f}ms, "
                    f"RPS={result.metrics.requests_per_second:.2f}"
                )
            self.console.print()

        # Overall status
        if report.all_passed and report.security_passed and report.performance_passed:
            self.console.print("[bold green]✓ ALL TESTS PASSED[/bold green]")
        else:
            self.console.print("[bold red]✗ TESTS FAILED[/bold red]")
            if report.errors:
                self.console.print("\n[bold]Errors:[/bold]")
                for error in report.errors:
                    self.console.print(f"  - {error}")

        self.console.print()

    def _save_report(self, report: ComprehensiveTestReport):
        """Save test report to file"""
        import json
        from datetime import datetime

        # JSON report
        json_path = self.output_dir / f"{report.project_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        json_path.write_text(json.dumps(report.to_dict(), indent=2))

        # Markdown report
        md_path = self.output_dir / f"{report.project_id}-report.md"
        md_content = self._generate_markdown_report(report)
        md_path.write_text(md_content)

        logger.info(f"Test report saved to {json_path} and {md_path}")

    def _generate_markdown_report(self, report: ComprehensiveTestReport) -> str:
        """Generate markdown report"""
        lines = [
            f"# Testing Report: {report.project_id}",
            "",
            "## Summary",
            f"- **Total Tests**: {report.total_tests}",
            f"- **Passed**: {report.passed_tests}",
            f"- **Failed**: {report.failed_tests}",
        ]

        if report.coverage_percent is not None:
            lines.append(f"- **Coverage**: {report.coverage_percent:.1f}%")

        lines.extend([
            f"- **Duration**: {report.duration_seconds:.2f}s",
            f"- **Status**: {'✓ PASS' if report.all_passed else '✗ FAIL'}",
            ""
        ])

        # Unit tests
        if report.unit_test_result:
            lines.extend([
                "## Unit Tests",
                f"- Passed: {report.unit_test_result.passed}",
                f"- Failed: {report.unit_test_result.failed}",
                f"- Skipped: {report.unit_test_result.skipped}",
                ""
            ])

        # Integration tests
        if report.integration_test_result and report.integration_test_result.total > 0:
            lines.extend([
                "## Integration Tests",
                f"- Passed: {report.integration_test_result.passed}",
                f"- Failed: {report.integration_test_result.failed}",
                ""
            ])

        # Security
        if report.security_scan_result:
            lines.extend([
                "## Security Scan",
                f"- **Status**: {'✓ PASS' if report.security_passed else '✗ FAIL'}",
                f"- Total Vulnerabilities: {report.security_scan_result.total_count}",
                f"- Critical: {report.security_scan_result.critical_count}",
                f"- High: {report.security_scan_result.high_count}",
                f"- OWASP Score: {report.security_scan_result.owasp_score:.1f}/100",
                ""
            ])

        # Performance
        if report.performance_results:
            lines.extend([
                "## Performance Tests",
                f"- **Status**: {'✓ PASS' if report.performance_passed else '✗ FAIL'}",
                ""
            ])
            for result in report.performance_results:
                lines.extend([
                    f"### {result.name}",
                    f"- P95 Latency: {result.metrics.p95_ms:.2f}ms",
                    f"- Throughput: {result.metrics.requests_per_second:.2f} req/s",
                    f"- Success Rate: {result.metrics.success_rate:.2f}%",
                    ""
                ])

        return "\n".join(lines)

    def close(self):
        """Close resources"""
        if self.test_generator:
            self.test_generator.close()
        if self.docker_runner:
            self.docker_runner.cleanup()
