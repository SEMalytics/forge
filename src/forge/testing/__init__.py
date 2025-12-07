"""
Automated testing and validation system

Provides test generation, Docker-isolated execution, security scanning,
and performance benchmarking.
"""

from .generator import TestGenerator, TestType, TestableEntity, Language
from .docker_runner import DockerTestRunner, TestFramework, TestResult
from .security_scanner import SecurityScanner, ScanResult, Vulnerability, Severity
from .performance import PerformanceBenchmark, BenchmarkResult, PerformanceMetrics, PerformanceThresholds

__all__ = [
    # Generator
    'TestGenerator',
    'TestType',
    'TestableEntity',
    'Language',

    # Docker Runner
    'DockerTestRunner',
    'TestFramework',
    'TestResult',

    # Security Scanner
    'SecurityScanner',
    'ScanResult',
    'Vulnerability',
    'Severity',

    # Performance
    'PerformanceBenchmark',
    'BenchmarkResult',
    'PerformanceMetrics',
    'PerformanceThresholds',
]
