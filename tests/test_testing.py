"""
Tests for testing system
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from forge.testing.generator import (
    TestGenerator,
    TestType,
    Language,
    TestableEntity,
    TestGenerationError
)
from forge.testing.docker_runner import (
    DockerTestRunner,
    TestFramework,
    TestResult,
    DockerConfig
)
from forge.testing.security_scanner import (
    SecurityScanner,
    ScanResult,
    Vulnerability,
    Severity,
    VulnerabilityType
)
from forge.testing.performance import (
    PerformanceBenchmark,
    BenchmarkResult,
    PerformanceMetrics,
    PerformanceThresholds,
    BenchmarkType
)


# Test Generator Tests

def test_test_generator_initialization():
    """Test test generator initialization"""
    generator = TestGenerator()
    assert generator is not None
    assert generator.pattern_store is not None


def test_detect_language_python():
    """Test language detection for Python"""
    generator = TestGenerator()

    assert generator._detect_language("test.py") == Language.PYTHON
    assert generator._detect_language("module.py") == Language.PYTHON


def test_detect_language_javascript():
    """Test language detection for JavaScript"""
    generator = TestGenerator()

    assert generator._detect_language("test.js") == Language.JAVASCRIPT
    assert generator._detect_language("test.jsx") == Language.JAVASCRIPT
    assert generator._detect_language("test.ts") == Language.TYPESCRIPT
    assert generator._detect_language("test.tsx") == Language.TYPESCRIPT


def test_extract_python_entities():
    """Test extracting Python functions"""
    generator = TestGenerator()

    code = """
def hello_world():
    return "Hello"

async def async_func(param1, param2: str) -> bool:
    return True

class MyClass:
    pass

def _private_func():
    pass
"""

    entities = generator._extract_python_entities("test.py", code)

    # Should find 2 public functions and 1 class (not private function)
    assert len(entities) == 3

    # Check function extraction
    hello = [e for e in entities if e.name == "hello_world"][0]
    assert hello.type == "function"
    assert not hello.is_async

    async_f = [e for e in entities if e.name == "async_func"][0]
    assert async_f.type == "function"
    assert async_f.is_async
    assert len(async_f.parameters) == 2

    # Check class extraction
    my_class = [e for e in entities if e.name == "MyClass"][0]
    assert my_class.type == "class"


def test_extract_javascript_entities():
    """Test extracting JavaScript functions"""
    generator = TestGenerator()

    code = """
function regularFunc(a, b) {
    return a + b;
}

async function asyncFunc() {
    return await something();
}

const arrowFunc = (x) => x * 2;

class MyClass {
    constructor() {}
}
"""

    entities = generator._extract_javascript_entities("test.js", code)

    # Should find functions and class
    assert len(entities) > 0

    # Check for function names
    names = [e.name for e in entities]
    assert "regularFunc" in names or "asyncFunc" in names


def test_generate_python_tests():
    """Test generating Python test cases"""
    generator = TestGenerator()

    entity = TestableEntity(
        name="calculate",
        type="function",
        signature="def calculate(x, y)",
        file_path="math.py",
        line_number=10,
        parameters=["x", "y"]
    )

    test_cases = generator._generate_python_tests(entity, TestType.UNIT, [])

    # Should generate at least success and error tests
    assert len(test_cases) >= 2
    assert any("success" in tc.name for tc in test_cases)
    assert any("error" in tc.name for tc in test_cases)


def test_get_test_file_path_python():
    """Test test file path generation for Python"""
    generator = TestGenerator()

    path = generator._get_test_file_path("src/module.py", Language.PYTHON)
    assert path == "tests/test_module.py"


def test_get_test_file_path_javascript():
    """Test test file path generation for JavaScript"""
    generator = TestGenerator()

    path = generator._get_test_file_path("src/component.js", Language.JAVASCRIPT)
    assert path == "tests/component.test.js"


def test_generate_tests_integration():
    """Test full test generation workflow"""
    generator = TestGenerator()

    code_files = {
        "calculator.py": """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
    }

    test_files = generator.generate_tests(
        code_files=code_files,
        tech_stack=["Python"],
        project_context="Math library",
        test_types=[TestType.UNIT]
    )

    # Should generate test file
    assert len(test_files) > 0
    assert any("test" in path for path in test_files.keys())

    # Check test content
    test_content = list(test_files.values())[0]
    assert "import pytest" in test_content or "def test_" in test_content


# Docker Test Runner Tests

def test_docker_runner_initialization():
    """Test Docker test runner initialization"""
    runner = DockerTestRunner(docker_available=False)
    assert runner is not None
    assert runner.docker_available is False


def test_detect_framework_pytest():
    """Test framework detection for pytest"""
    runner = DockerTestRunner(docker_available=False)

    test_files = {
        "test_example.py": "import pytest\n\ndef test_something():\n    assert True"
    }

    framework = runner._detect_framework(test_files)
    assert framework == TestFramework.PYTEST


def test_detect_framework_jest():
    """Test framework detection for Jest"""
    runner = DockerTestRunner(docker_available=False)

    test_files = {
        "example.test.js": "describe('test', () => {\n  test('works', () => {});\n});"
    }

    framework = runner._detect_framework(test_files)
    assert framework == TestFramework.JEST


def test_parse_pytest_output():
    """Test parsing pytest output"""
    runner = DockerTestRunner(docker_available=False)

    stdout = """
collected 10 items

test_example.py::test_one PASSED
test_example.py::test_two FAILED
test_example.py::test_three SKIPPED

======== 8 passed, 1 failed, 1 skipped in 2.34s ========
TOTAL coverage: 85%
"""

    result = runner._parse_pytest_output(stdout, "", 2.34)

    assert result.passed == 8
    assert result.failed == 1
    assert result.skipped == 1
    assert result.coverage_percent == 85.0


def test_parse_jest_output():
    """Test parsing Jest output"""
    runner = DockerTestRunner(docker_available=False)

    stdout = """
Tests:       8 passed, 2 failed, 10 total
All files    |     85% |
"""

    result = runner._parse_jest_output(stdout, "", 3.0)

    assert result.passed == 8
    assert result.total == 10


def test_docker_config():
    """Test Docker configuration"""
    config = DockerConfig(
        image="python:3.11",
        memory_limit="1g",
        cpu_limit="2.0"
    )

    assert config.image == "python:3.11"
    assert config.memory_limit == "1g"
    assert config.cpu_limit == "2.0"


@pytest.mark.asyncio
async def test_run_tests_locally():
    """Test running tests locally without Docker"""
    runner = DockerTestRunner(docker_available=False)

    # This would require actual test execution
    # Skip for now as it's integration-level
    pass


# Security Scanner Tests

def test_security_scanner_initialization():
    """Test security scanner initialization"""
    scanner = SecurityScanner(enable_external_tools=False)
    assert scanner is not None
    assert not scanner.bandit_available
    assert not scanner.semgrep_available


def test_detect_hardcoded_password():
    """Test detecting hardcoded passwords"""
    scanner = SecurityScanner(enable_external_tools=False)

    code_files = {
        "config.py": """
DATABASE_PASSWORD = "super_secret_123"
API_KEY = "sk_test_abcdefghijklmnop"
"""
    }

    vulnerabilities = scanner._detect_secrets(code_files)

    # Should detect password and API key
    assert len(vulnerabilities) >= 2
    assert all(v.type == VulnerabilityType.HARDCODED_SECRET for v in vulnerabilities)
    assert all(v.severity == Severity.CRITICAL for v in vulnerabilities)


def test_detect_dangerous_functions():
    """Test detecting dangerous function usage"""
    scanner = SecurityScanner(enable_external_tools=False)

    code_files = {
        "unsafe.py": """
import os
result = eval(user_input)
os.system("rm -rf /")
"""
    }

    vulnerabilities = scanner._pattern_based_detection(code_files)

    # Should detect eval and os.system
    assert len(vulnerabilities) >= 2
    eval_vuln = [v for v in vulnerabilities if 'eval' in v.description.lower()]
    assert len(eval_vuln) > 0
    assert eval_vuln[0].severity == Severity.CRITICAL


def test_detect_sql_injection():
    """Test detecting SQL injection vulnerabilities"""
    scanner = SecurityScanner(enable_external_tools=False)

    code_files = {
        "database.py": """
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)
"""
    }

    vulnerabilities = scanner._pattern_based_detection(code_files)

    # Should detect SQL injection
    sql_vulns = [v for v in vulnerabilities if v.type == VulnerabilityType.SQL_INJECTION]
    assert len(sql_vulns) > 0


def test_calculate_owasp_score():
    """Test OWASP score calculation"""
    scanner = SecurityScanner(enable_external_tools=False)

    # No vulnerabilities = 100
    assert scanner._calculate_owasp_score([]) == 100.0

    # Critical vulnerability
    vulnerabilities = [
        Vulnerability(
            type=VulnerabilityType.SQL_INJECTION,
            severity=Severity.CRITICAL,
            file_path="test.py",
            line_number=10,
            description="SQL injection",
            recommendation="Use parameterized queries"
        )
    ]
    score = scanner._calculate_owasp_score(vulnerabilities)
    assert score == 80.0  # 100 - 20 for critical


def test_scan_result():
    """Test scan result aggregation"""
    result = ScanResult()

    result.vulnerabilities = [
        Vulnerability(
            type=VulnerabilityType.XSS,
            severity=Severity.CRITICAL,
            file_path="test.py",
            line_number=1,
            description="XSS",
            recommendation="Sanitize"
        ),
        Vulnerability(
            type=VulnerabilityType.XSS,
            severity=Severity.HIGH,
            file_path="test.py",
            line_number=2,
            description="XSS",
            recommendation="Sanitize"
        )
    ]

    assert result.critical_count == 1
    assert result.high_count == 1
    assert result.total_count == 2
    assert not result.is_secure  # Has critical


def test_security_scan_integration():
    """Test full security scan"""
    scanner = SecurityScanner(enable_external_tools=False)

    code_files = {
        "app.py": """
password = "hardcoded123"
user_data = eval(request.get('data'))
"""
    }

    result = scanner.scan(code_files)

    assert result.total_count > 0
    assert result.secrets_found > 0
    assert result.owasp_score < 100.0


# Performance Benchmark Tests

def test_performance_benchmark_initialization():
    """Test performance benchmark initialization"""
    benchmark = PerformanceBenchmark(enable_profiling=False)
    assert benchmark is not None
    assert not benchmark.enable_profiling


def test_performance_metrics():
    """Test performance metrics calculation"""
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0]

    benchmark = PerformanceBenchmark(enable_profiling=False)
    metrics = benchmark._calculate_metrics(
        latencies=latencies,
        total_requests=5,
        failed_requests=0,
        duration_seconds=1.0,
        memory_samples=[],
        cpu_samples=[]
    )

    assert metrics.min_ms == 10.0
    assert metrics.max_ms == 50.0
    assert metrics.mean_ms == 30.0
    assert metrics.median_ms == 30.0
    assert metrics.requests_per_second == 5.0
    assert metrics.success_rate == 100.0


def test_performance_thresholds():
    """Test performance threshold checking"""
    thresholds = PerformanceThresholds(
        max_response_time_ms=100.0,
        min_requests_per_second=10.0,
        min_success_rate=95.0
    )

    # Passing metrics
    good_metrics = PerformanceMetrics(
        min_ms=10.0,
        max_ms=80.0,
        mean_ms=50.0,
        median_ms=50.0,
        p95_ms=75.0,
        p99_ms=80.0,
        std_dev_ms=15.0,
        requests_per_second=20.0,
        total_requests=100,
        failed_requests=0
    )

    violations = thresholds.check(good_metrics)
    assert len(violations) == 0

    # Failing metrics
    bad_metrics = PerformanceMetrics(
        min_ms=10.0,
        max_ms=200.0,
        mean_ms=150.0,
        median_ms=150.0,
        p95_ms=180.0,
        p99_ms=200.0,
        std_dev_ms=30.0,
        requests_per_second=5.0,
        total_requests=100,
        failed_requests=10
    )

    violations = thresholds.check(bad_metrics)
    assert len(violations) >= 2  # Response time and RPS violations


@pytest.mark.asyncio
async def test_benchmark_function():
    """Test function benchmarking"""
    benchmark = PerformanceBenchmark(enable_profiling=False)

    async def test_func():
        import asyncio
        await asyncio.sleep(0.001)  # 1ms

    result = await benchmark.benchmark_function(
        name="test",
        func=test_func,
        iterations=10,
        concurrency=2
    )

    assert result.metrics.total_requests == 10
    assert result.metrics.mean_ms >= 1.0  # At least 1ms
    assert result.duration_seconds > 0


def test_detect_bottlenecks():
    """Test bottleneck detection"""
    benchmark = PerformanceBenchmark(enable_profiling=False)

    # Create result with high variance
    result = BenchmarkResult(
        name="test",
        type=BenchmarkType.LATENCY,
        metrics=PerformanceMetrics(
            min_ms=10.0,
            max_ms=1000.0,
            mean_ms=100.0,
            median_ms=50.0,
            p95_ms=500.0,
            p99_ms=900.0,
            std_dev_ms=200.0,  # High variance
            requests_per_second=10.0,
            total_requests=100,
            failed_requests=0
        ),
        duration_seconds=10.0,
        passed=True
    )

    bottlenecks = benchmark.detect_bottlenecks([result])

    # Should detect high variance and tail latency issues
    assert len(bottlenecks) >= 2


def test_benchmark_result_to_dict():
    """Test benchmark result serialization"""
    result = BenchmarkResult(
        name="test",
        type=BenchmarkType.LOAD,
        metrics=PerformanceMetrics(
            min_ms=10.0,
            max_ms=50.0,
            mean_ms=30.0,
            median_ms=30.0,
            p95_ms=45.0,
            p99_ms=50.0,
            std_dev_ms=10.0,
            requests_per_second=100.0,
            total_requests=1000,
            failed_requests=5
        ),
        duration_seconds=10.0,
        passed=True
    )

    data = result.to_dict()

    assert data['name'] == "test"
    assert data['type'] == "load"
    assert data['passed'] is True
    assert data['metrics']['mean_ms'] == 30.0


# Integration Tests

@pytest.mark.asyncio
async def test_full_testing_workflow():
    """Test complete testing workflow"""
    # This is an integration test that would test the full orchestrator
    # Skipping actual execution as it requires Docker and other dependencies
    pass


def test_test_result_success():
    """Test result success property"""
    result = TestResult(
        framework=TestFramework.PYTEST,
        passed=10,
        failed=0,
        skipped=1
    )

    assert result.success is True
    assert result.total == 11


def test_test_result_failure():
    """Test result failure property"""
    result = TestResult(
        framework=TestFramework.PYTEST,
        passed=10,
        failed=2,
        skipped=1
    )

    assert result.success is False
    assert result.total == 13
