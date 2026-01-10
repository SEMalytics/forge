"""
Automated testing and validation system

Provides test generation, Docker-isolated execution, security scanning,
and performance benchmarking.
"""

from .generator import TestSuiteGenerator, TestCaseType, CodeEntity, Language
from .docker_runner import DockerTestRunner, SupportedFramework, ExecutionResult
from .security_scanner import SecurityScanner, ScanResult, Vulnerability, Severity
from .performance import PerformanceBenchmark, BenchmarkResult, PerformanceMetrics, PerformanceThresholds

__all__ = [
    # Generator
    'TestSuiteGenerator',
    'TestCaseType',
    'CodeEntity',
    'Language',

    # Docker Runner
    'DockerTestRunner',
    'SupportedFramework',
    'ExecutionResult',

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
