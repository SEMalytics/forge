"""
Performance benchmarking and profiling

Provides:
- Load testing for APIs and services
- Response time measurement
- Memory profiling
- CPU profiling
- Bottleneck detection
"""

import time
import asyncio
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class PerformanceError(ForgeError):
    """Errors during performance testing"""
    pass


class BenchmarkType(Enum):
    """Benchmark types"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    MEMORY = "memory"
    CPU = "cpu"
    LOAD = "load"


@dataclass
class PerformanceMetrics:
    """Performance measurement metrics"""
    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
    requests_per_second: float
    total_requests: int
    failed_requests: int
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None

    @property
    def success_rate(self) -> float:
        """Success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return ((self.total_requests - self.failed_requests) / self.total_requests) * 100

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'min_ms': round(self.min_ms, 2),
            'max_ms': round(self.max_ms, 2),
            'mean_ms': round(self.mean_ms, 2),
            'median_ms': round(self.median_ms, 2),
            'p95_ms': round(self.p95_ms, 2),
            'p99_ms': round(self.p99_ms, 2),
            'std_dev_ms': round(self.std_dev_ms, 2),
            'requests_per_second': round(self.requests_per_second, 2),
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'success_rate': round(self.success_rate, 2),
            'memory_mb': round(self.memory_mb, 2) if self.memory_mb else None,
            'cpu_percent': round(self.cpu_percent, 2) if self.cpu_percent else None
        }


@dataclass
class BenchmarkResult:
    """Benchmark execution result"""
    name: str
    type: BenchmarkType
    metrics: PerformanceMetrics
    duration_seconds: float
    passed: bool
    threshold_violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'type': self.type.value,
            'metrics': self.metrics.to_dict(),
            'duration_seconds': round(self.duration_seconds, 2),
            'passed': self.passed,
            'threshold_violations': self.threshold_violations
        }


@dataclass
class PerformanceThresholds:
    """Performance requirement thresholds"""
    max_response_time_ms: Optional[float] = None
    min_requests_per_second: Optional[float] = None
    max_memory_mb: Optional[float] = None
    max_cpu_percent: Optional[float] = None
    min_success_rate: float = 95.0

    def check(self, metrics: PerformanceMetrics) -> List[str]:
        """Check if metrics meet thresholds"""
        violations = []

        if self.max_response_time_ms and metrics.p95_ms > self.max_response_time_ms:
            violations.append(
                f"P95 response time {metrics.p95_ms:.2f}ms exceeds "
                f"threshold {self.max_response_time_ms}ms"
            )

        if self.min_requests_per_second and metrics.requests_per_second < self.min_requests_per_second:
            violations.append(
                f"Throughput {metrics.requests_per_second:.2f} req/s below "
                f"threshold {self.min_requests_per_second} req/s"
            )

        if self.max_memory_mb and metrics.memory_mb and metrics.memory_mb > self.max_memory_mb:
            violations.append(
                f"Memory usage {metrics.memory_mb:.2f}MB exceeds "
                f"threshold {self.max_memory_mb}MB"
            )

        if self.max_cpu_percent and metrics.cpu_percent and metrics.cpu_percent > self.max_cpu_percent:
            violations.append(
                f"CPU usage {metrics.cpu_percent:.2f}% exceeds "
                f"threshold {self.max_cpu_percent}%"
            )

        if metrics.success_rate < self.min_success_rate:
            violations.append(
                f"Success rate {metrics.success_rate:.2f}% below "
                f"threshold {self.min_success_rate}%"
            )

        return violations


class PerformanceBenchmark:
    """
    Performance benchmarking and profiling.

    Features:
    - Load testing with configurable concurrency
    - Response time percentiles
    - Memory and CPU profiling
    - Bottleneck detection
    - Threshold validation
    """

    def __init__(
        self,
        enable_profiling: bool = True,
        profile_output_dir: Optional[Path] = None
    ):
        """
        Initialize performance benchmark.

        Args:
            enable_profiling: Enable memory/CPU profiling
            profile_output_dir: Directory for profile outputs
        """
        self.enable_profiling = enable_profiling
        self.profile_output_dir = profile_output_dir or Path(".forge/profiles")
        self.profile_output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized PerformanceBenchmark (profiling={enable_profiling})")

    async def benchmark_function(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
        concurrency: int = 1,
        thresholds: Optional[PerformanceThresholds] = None
    ) -> BenchmarkResult:
        """
        Benchmark a function.

        Args:
            name: Benchmark name
            func: Function to benchmark (can be async)
            iterations: Number of iterations
            concurrency: Concurrent executions
            thresholds: Performance thresholds

        Returns:
            Benchmark result
        """
        logger.info(f"Running benchmark: {name} ({iterations} iterations, concurrency={concurrency})")

        start_time = time.time()
        latencies = []
        failed = 0

        # Start profiling
        if self.enable_profiling:
            memory_samples = []
            cpu_samples = []
            profiler_task = asyncio.create_task(
                self._profile_resources(memory_samples, cpu_samples)
            )
        else:
            memory_samples = []
            cpu_samples = []
            profiler_task = None

        # Run benchmark
        try:
            if asyncio.iscoroutinefunction(func):
                latencies, failed = await self._benchmark_async(
                    func, iterations, concurrency
                )
            else:
                latencies, failed = await self._benchmark_sync(
                    func, iterations, concurrency
                )
        finally:
            # Stop profiling
            if profiler_task:
                profiler_task.cancel()
                try:
                    await profiler_task
                except asyncio.CancelledError:
                    pass

        duration = time.time() - start_time

        # Calculate metrics
        metrics = self._calculate_metrics(
            latencies=latencies,
            total_requests=iterations,
            failed_requests=failed,
            duration_seconds=duration,
            memory_samples=memory_samples,
            cpu_samples=cpu_samples
        )

        # Check thresholds
        violations = []
        if thresholds:
            violations = thresholds.check(metrics)

        result = BenchmarkResult(
            name=name,
            type=BenchmarkType.LATENCY,
            metrics=metrics,
            duration_seconds=duration,
            passed=len(violations) == 0,
            threshold_violations=violations
        )

        logger.info(
            f"Benchmark complete: {name} - "
            f"Mean: {metrics.mean_ms:.2f}ms, P95: {metrics.p95_ms:.2f}ms, "
            f"RPS: {metrics.requests_per_second:.2f}"
        )

        return result

    async def _benchmark_async(
        self,
        func: Callable,
        iterations: int,
        concurrency: int
    ) -> tuple[List[float], int]:
        """Benchmark async function"""
        latencies = []
        failed = 0

        # Create batches for concurrency
        batches = [iterations // concurrency] * concurrency
        batches[-1] += iterations % concurrency  # Add remainder to last batch

        async def run_batch(batch_size: int):
            nonlocal failed
            batch_latencies = []

            for _ in range(batch_size):
                start = time.perf_counter()
                try:
                    await func()
                    latency = (time.perf_counter() - start) * 1000  # Convert to ms
                    batch_latencies.append(latency)
                except Exception as e:
                    logger.debug(f"Benchmark iteration failed: {e}")
                    failed += 1

            return batch_latencies

        # Run batches concurrently
        tasks = [run_batch(batch_size) for batch_size in batches]
        results = await asyncio.gather(*tasks)

        # Flatten results
        for batch_latencies in results:
            latencies.extend(batch_latencies)

        return latencies, failed

    async def _benchmark_sync(
        self,
        func: Callable,
        iterations: int,
        concurrency: int
    ) -> tuple[List[float], int]:
        """Benchmark sync function"""
        # Run sync function in executor to avoid blocking
        loop = asyncio.get_event_loop()

        async def run_sync():
            start = time.perf_counter()
            try:
                await loop.run_in_executor(None, func)
                return (time.perf_counter() - start) * 1000
            except Exception as e:
                logger.debug(f"Benchmark iteration failed: {e}")
                return None

        # Run with concurrency
        latencies = []
        failed = 0

        for i in range(0, iterations, concurrency):
            batch_size = min(concurrency, iterations - i)
            tasks = [run_sync() for _ in range(batch_size)]
            results = await asyncio.gather(*tasks)

            for latency in results:
                if latency is not None:
                    latencies.append(latency)
                else:
                    failed += 1

        return latencies, failed

    async def _profile_resources(
        self,
        memory_samples: List[float],
        cpu_samples: List[float]
    ):
        """Profile memory and CPU usage"""
        try:
            import psutil
            process = psutil.Process()

            while True:
                try:
                    # Sample memory
                    mem_info = process.memory_info()
                    memory_mb = mem_info.rss / 1024 / 1024
                    memory_samples.append(memory_mb)

                    # Sample CPU
                    cpu_percent = process.cpu_percent(interval=0.1)
                    cpu_samples.append(cpu_percent)

                except Exception as e:
                    logger.debug(f"Resource sampling failed: {e}")

                await asyncio.sleep(0.1)

        except ImportError:
            logger.warning("psutil not available, skipping resource profiling")
        except asyncio.CancelledError:
            pass

    def _calculate_metrics(
        self,
        latencies: List[float],
        total_requests: int,
        failed_requests: int,
        duration_seconds: float,
        memory_samples: List[float],
        cpu_samples: List[float]
    ) -> PerformanceMetrics:
        """Calculate performance metrics from samples"""
        if not latencies:
            # No successful requests
            return PerformanceMetrics(
                min_ms=0.0,
                max_ms=0.0,
                mean_ms=0.0,
                median_ms=0.0,
                p95_ms=0.0,
                p99_ms=0.0,
                std_dev_ms=0.0,
                requests_per_second=0.0,
                total_requests=total_requests,
                failed_requests=failed_requests
            )

        sorted_latencies = sorted(latencies)

        # Calculate percentiles
        def percentile(data: List[float], p: float) -> float:
            if not data:
                return 0.0
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = f + 1
            if c >= len(data):
                return data[-1]
            return data[f] + (k - f) * (data[c] - data[f])

        return PerformanceMetrics(
            min_ms=min(latencies),
            max_ms=max(latencies),
            mean_ms=statistics.mean(latencies),
            median_ms=statistics.median(latencies),
            p95_ms=percentile(sorted_latencies, 95),
            p99_ms=percentile(sorted_latencies, 99),
            std_dev_ms=statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
            requests_per_second=(total_requests - failed_requests) / duration_seconds,
            total_requests=total_requests,
            failed_requests=failed_requests,
            memory_mb=statistics.mean(memory_samples) if memory_samples else None,
            cpu_percent=statistics.mean(cpu_samples) if cpu_samples else None
        )

    async def load_test(
        self,
        name: str,
        endpoint_func: Callable,
        duration_seconds: int = 60,
        target_rps: int = 100,
        thresholds: Optional[PerformanceThresholds] = None
    ) -> BenchmarkResult:
        """
        Run load test.

        Args:
            name: Test name
            endpoint_func: Function to call (simulates endpoint)
            duration_seconds: Test duration
            target_rps: Target requests per second
            thresholds: Performance thresholds

        Returns:
            Benchmark result
        """
        logger.info(f"Starting load test: {name} ({duration_seconds}s @ {target_rps} RPS)")

        start_time = time.time()
        latencies = []
        failed = 0

        # Start profiling
        if self.enable_profiling:
            memory_samples = []
            cpu_samples = []
            profiler_task = asyncio.create_task(
                self._profile_resources(memory_samples, cpu_samples)
            )
        else:
            memory_samples = []
            cpu_samples = []
            profiler_task = None

        try:
            # Calculate delay between requests
            delay = 1.0 / target_rps

            request_count = 0
            end_time = start_time + duration_seconds

            while time.time() < end_time:
                request_start = time.perf_counter()

                try:
                    if asyncio.iscoroutinefunction(endpoint_func):
                        await endpoint_func()
                    else:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, endpoint_func)

                    latency = (time.perf_counter() - request_start) * 1000
                    latencies.append(latency)
                    request_count += 1

                except Exception as e:
                    logger.debug(f"Request failed: {e}")
                    failed += 1
                    request_count += 1

                # Rate limiting
                elapsed = time.perf_counter() - request_start
                sleep_time = max(0, delay - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        finally:
            if profiler_task:
                profiler_task.cancel()
                try:
                    await profiler_task
                except asyncio.CancelledError:
                    pass

        actual_duration = time.time() - start_time

        # Calculate metrics
        metrics = self._calculate_metrics(
            latencies=latencies,
            total_requests=request_count,
            failed_requests=failed,
            duration_seconds=actual_duration,
            memory_samples=memory_samples,
            cpu_samples=cpu_samples
        )

        # Check thresholds
        violations = []
        if thresholds:
            violations = thresholds.check(metrics)

        result = BenchmarkResult(
            name=name,
            type=BenchmarkType.LOAD,
            metrics=metrics,
            duration_seconds=actual_duration,
            passed=len(violations) == 0,
            threshold_violations=violations
        )

        logger.info(
            f"Load test complete: {name} - "
            f"Actual RPS: {metrics.requests_per_second:.2f}, "
            f"P95: {metrics.p95_ms:.2f}ms, "
            f"Success: {metrics.success_rate:.1f}%"
        )

        return result

    def detect_bottlenecks(
        self,
        results: List[BenchmarkResult]
    ) -> List[str]:
        """
        Detect performance bottlenecks from benchmark results.

        Args:
            results: List of benchmark results

        Returns:
            List of bottleneck descriptions
        """
        bottlenecks = []

        for result in results:
            metrics = result.metrics

            # High latency variance indicates inconsistent performance
            if metrics.std_dev_ms > metrics.mean_ms * 0.5:
                bottlenecks.append(
                    f"{result.name}: High latency variance "
                    f"(σ={metrics.std_dev_ms:.2f}ms, μ={metrics.mean_ms:.2f}ms) "
                    f"suggests resource contention or garbage collection"
                )

            # Large P99-P95 gap indicates tail latency issues
            if metrics.p99_ms > metrics.p95_ms * 1.5:
                bottlenecks.append(
                    f"{result.name}: Large tail latency gap "
                    f"(P99={metrics.p99_ms:.2f}ms, P95={metrics.p95_ms:.2f}ms) "
                    f"suggests occasional blocking operations"
                )

            # High memory usage
            if metrics.memory_mb and metrics.memory_mb > 500:
                bottlenecks.append(
                    f"{result.name}: High memory usage ({metrics.memory_mb:.2f}MB) "
                    f"may indicate memory leaks or inefficient data structures"
                )

            # High CPU usage
            if metrics.cpu_percent and metrics.cpu_percent > 80:
                bottlenecks.append(
                    f"{result.name}: High CPU usage ({metrics.cpu_percent:.2f}%) "
                    f"suggests CPU-bound operations that could be optimized"
                )

            # Low success rate
            if metrics.success_rate < 99.0:
                bottlenecks.append(
                    f"{result.name}: Low success rate ({metrics.success_rate:.2f}%) "
                    f"indicates reliability issues"
                )

        return bottlenecks

    def generate_report(
        self,
        results: List[BenchmarkResult],
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate performance report.

        Args:
            results: Benchmark results
            output_path: Optional path to save report

        Returns:
            Report content
        """
        report_lines = [
            "# Performance Benchmark Report",
            "",
            "## Summary",
            f"- **Total Benchmarks**: {len(results)}",
            f"- **Passed**: {sum(1 for r in results if r.passed)}",
            f"- **Failed**: {sum(1 for r in results if not r.passed)}",
            "",
        ]

        # Bottleneck analysis
        bottlenecks = self.detect_bottlenecks(results)
        if bottlenecks:
            report_lines.extend([
                "## Bottlenecks Detected",
                ""
            ])
            for bottleneck in bottlenecks:
                report_lines.append(f"- {bottleneck}")
            report_lines.append("")

        # Individual results
        report_lines.extend([
            "## Benchmark Results",
            ""
        ])

        for result in results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            report_lines.extend([
                f"### {result.name} [{status}]",
                "",
                f"**Type**: {result.type.value}",
                f"**Duration**: {result.duration_seconds:.2f}s",
                "",
                "**Metrics**:",
                f"- Min: {result.metrics.min_ms:.2f}ms",
                f"- Mean: {result.metrics.mean_ms:.2f}ms",
                f"- Median: {result.metrics.median_ms:.2f}ms",
                f"- P95: {result.metrics.p95_ms:.2f}ms",
                f"- P99: {result.metrics.p99_ms:.2f}ms",
                f"- Max: {result.metrics.max_ms:.2f}ms",
                f"- Throughput: {result.metrics.requests_per_second:.2f} req/s",
                f"- Success Rate: {result.metrics.success_rate:.2f}%",
            ])

            if result.metrics.memory_mb:
                report_lines.append(f"- Memory: {result.metrics.memory_mb:.2f}MB")
            if result.metrics.cpu_percent:
                report_lines.append(f"- CPU: {result.metrics.cpu_percent:.2f}%")

            if result.threshold_violations:
                report_lines.extend(["", "**Threshold Violations**:"])
                for violation in result.threshold_violations:
                    report_lines.append(f"- {violation}")

            report_lines.append("")

        report = "\n".join(report_lines)

        if output_path:
            output_path.write_text(report)
            logger.info(f"Performance report saved to {output_path}")

        return report
