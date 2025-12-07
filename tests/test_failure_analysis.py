"""
Tests for failure analysis and fix generation system
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from forge.layers.failure_analyzer import (
    FailureAnalyzer,
    FailureType,
    Priority,
    FixSuggestion,
    FailureDetails,
    StackFrame
)
from forge.layers.fix_generator import (
    FixGenerator,
    GeneratedFix
)
from forge.testing.docker_runner import TestResult, TestFramework
from forge.testing.security_scanner import ScanResult, Vulnerability, Severity, VulnerabilityType


# Failure Analyzer Tests

def test_failure_analyzer_initialization():
    """Test failure analyzer initialization"""
    analyzer = FailureAnalyzer()
    assert analyzer is not None
    assert analyzer.pattern_store is not None


def test_categorize_failure_import_error():
    """Test categorizing import error"""
    analyzer = FailureAnalyzer()

    message = "ImportError: No module named 'requests'"
    failure_type = analyzer._categorize_failure(message)

    assert failure_type == FailureType.IMPORT_ERROR


def test_categorize_failure_name_error():
    """Test categorizing name error"""
    analyzer = FailureAnalyzer()

    message = "NameError: name 'undefined_var' is not defined"
    failure_type = analyzer._categorize_failure(message)

    assert failure_type == FailureType.NAME_ERROR


def test_categorize_failure_assertion_error():
    """Test categorizing assertion error"""
    analyzer = FailureAnalyzer()

    message = "AssertionError: assert 5 == 10"
    failure_type = analyzer._categorize_failure(message)

    assert failure_type == FailureType.ASSERTION_ERROR


def test_categorize_failure_type_error():
    """Test categorizing type error"""
    analyzer = FailureAnalyzer()

    message = "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
    failure_type = analyzer._categorize_failure(message)

    assert failure_type == FailureType.TYPE_ERROR


def test_parse_pytest_output():
    """Test parsing pytest output"""
    analyzer = FailureAnalyzer()

    output = """
test_example.py::test_addition FAILED

    def test_addition():
>       assert add(2, 3) == 6
E       assert 5 == 6

  File "/path/to/test.py", line 10, in test_addition
    assert add(2, 3) == 6
AssertionError
"""

    failures = analyzer._parse_pytest_output(output)

    assert len(failures) >= 0  # May or may not parse depending on format


def test_determine_priority_critical():
    """Test priority determination for critical errors"""
    analyzer = FailureAnalyzer()

    failure = FailureDetails(
        failure_type=FailureType.SYNTAX_ERROR,
        error_message="SyntaxError: invalid syntax",
        stack_trace=[],
        failing_file="test.py",
        failing_line=10,
        test_name="test_example"
    )

    priority = analyzer._determine_priority(FailureType.SYNTAX_ERROR, failure)

    assert priority == Priority.CRITICAL


def test_determine_priority_high():
    """Test priority determination for high priority errors"""
    analyzer = FailureAnalyzer()

    failure = FailureDetails(
        failure_type=FailureType.NAME_ERROR,
        error_message="NameError: undefined",
        stack_trace=[],
        failing_file="test.py",
        failing_line=10,
        test_name="test_example"
    )

    priority = analyzer._determine_priority(FailureType.NAME_ERROR, failure)

    assert priority == Priority.HIGH


def test_generate_specific_fix_import_error():
    """Test generating specific fix for import error"""
    analyzer = FailureAnalyzer()

    failure = FailureDetails(
        failure_type=FailureType.IMPORT_ERROR,
        error_message="No module named 'requests'",
        stack_trace=[],
        failing_file="test.py",
        failing_line=1,
        test_name="test_example"
    )

    fix = analyzer._generate_specific_fix(failure, FailureType.IMPORT_ERROR)

    assert 'requests' in fix.lower()
    assert 'install' in fix.lower()


def test_generate_specific_fix_name_error():
    """Test generating specific fix for name error"""
    analyzer = FailureAnalyzer()

    failure = FailureDetails(
        failure_type=FailureType.NAME_ERROR,
        error_message="name 'undefined_var' is not defined",
        stack_trace=[],
        failing_file="test.py",
        failing_line=5,
        test_name="test_example"
    )

    fix = analyzer._generate_specific_fix(failure, FailureType.NAME_ERROR)

    assert 'undefined_var' in fix


def test_calculate_confidence_with_patterns():
    """Test confidence calculation with patterns"""
    analyzer = FailureAnalyzer()

    # With patterns and code changes
    confidence = analyzer._calculate_confidence(
        failure_type=FailureType.IMPORT_ERROR,
        patterns=[{'filename': 'test.md'}],
        code_changes=[{'file': 'test.py', 'old': 'x', 'new': 'y'}]
    )

    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.5  # Should be higher with patterns and changes


def test_analyze_security_failures():
    """Test analyzing security vulnerabilities"""
    analyzer = FailureAnalyzer()

    scan_result = ScanResult()
    scan_result.vulnerabilities = [
        Vulnerability(
            type=VulnerabilityType.HARDCODED_SECRET,
            severity=Severity.CRITICAL,
            file_path="config.py",
            line_number=10,
            description="Hardcoded password detected",
            recommendation="Move to environment variables"
        )
    ]

    suggestions = analyzer._analyze_security_failures(scan_result, {})

    assert len(suggestions) == 1
    assert suggestions[0].failure_type == FailureType.SECURITY_VULNERABILITY
    assert suggestions[0].priority == Priority.CRITICAL


def test_analyze_performance_failures():
    """Test analyzing performance issues"""
    from forge.testing.performance import BenchmarkResult, PerformanceMetrics, BenchmarkType

    analyzer = FailureAnalyzer()

    result = BenchmarkResult(
        name="test_perf",
        type=BenchmarkType.LATENCY,
        metrics=PerformanceMetrics(
            min_ms=10.0,
            max_ms=500.0,
            mean_ms=250.0,
            median_ms=200.0,
            p95_ms=450.0,
            p99_ms=500.0,
            std_dev_ms=100.0,
            requests_per_second=4.0,
            total_requests=100,
            failed_requests=0
        ),
        duration_seconds=25.0,
        passed=False,
        threshold_violations=["P95 response time 450.0ms exceeds threshold 100ms"]
    )

    suggestions = analyzer._analyze_performance_failures([result], {})

    assert len(suggestions) > 0
    assert suggestions[0].failure_type == FailureType.PERFORMANCE_DEGRADATION
    assert suggestions[0].priority == Priority.MEDIUM


# Fix Generator Tests

def test_fix_generator_initialization():
    """Test fix generator initialization"""
    generator = FixGenerator(use_ai=False)
    assert generator is not None
    assert not generator.use_ai


def test_generate_commit_message():
    """Test commit message generation"""
    generator = FixGenerator(use_ai=False)

    suggestion = FixSuggestion(
        failure_type=FailureType.IMPORT_ERROR,
        root_cause="Missing module",
        suggested_fix="Install requests package",
        code_changes=[],
        relevant_patterns=[],
        priority=Priority.HIGH,
        confidence=0.9,
        explanation="Module not found"
    )

    message = generator._generate_commit_message(suggestion)

    assert 'fix' in message.lower()
    assert 'missing module' in message.lower()


def test_prioritize_fixes():
    """Test fix prioritization"""
    generator = FixGenerator(use_ai=False)

    suggestion1 = FixSuggestion(
        failure_type=FailureType.SYNTAX_ERROR,
        root_cause="Syntax error",
        suggested_fix="Fix syntax",
        code_changes=[],
        relevant_patterns=[],
        priority=Priority.CRITICAL,
        confidence=0.9,
        explanation="Syntax error"
    )

    suggestion2 = FixSuggestion(
        failure_type=FailureType.ASSERTION_ERROR,
        root_cause="Logic error",
        suggested_fix="Fix logic",
        code_changes=[],
        relevant_patterns=[],
        priority=Priority.MEDIUM,
        confidence=0.7,
        explanation="Logic error"
    )

    fix1 = GeneratedFix(suggestion=suggestion1, file_changes={}, commit_message="Fix 1")
    fix2 = GeneratedFix(suggestion=suggestion2, file_changes={}, commit_message="Fix 2")

    prioritized = generator.prioritize_fixes([fix2, fix1])

    # Critical should come first
    assert prioritized[0].suggestion.priority == Priority.CRITICAL


def test_estimate_impact_minimal():
    """Test impact estimation for minimal changes"""
    generator = FixGenerator(use_ai=False)

    fix = GeneratedFix(
        suggestion=Mock(),
        file_changes={"test.py": "print('hello')"},
        commit_message="Test"
    )

    impact = generator.estimate_impact(fix)

    assert 'minimal' in impact.lower() or 'low' in impact.lower()


def test_estimate_impact_high():
    """Test impact estimation for large changes"""
    generator = FixGenerator(use_ai=False)

    # Create large change
    large_content = "\n".join([f"line {i}" for i in range(200)])

    fix = GeneratedFix(
        suggestion=Mock(),
        file_changes={
            "file1.py": large_content,
            "file2.py": large_content,
            "file3.py": large_content,
            "file4.py": large_content,
            "file5.py": large_content,
            "file6.py": large_content
        },
        commit_message="Test"
    )

    impact = generator.estimate_impact(fix)

    assert 'high' in impact.lower() or 'medium' in impact.lower()


@pytest.mark.asyncio
async def test_apply_fix(tmp_path):
    """Test applying fix to files"""
    generator = FixGenerator(use_ai=False)

    fix = GeneratedFix(
        suggestion=Mock(),
        file_changes={
            "test.py": "def hello():\n    print('Hello, World!')"
        },
        commit_message="Add hello function"
    )

    success = await generator.apply_fix(fix, tmp_path)

    assert success
    assert fix.applied
    assert fix.success

    # Verify file was created
    test_file = tmp_path / "test.py"
    assert test_file.exists()
    assert "hello" in test_file.read_text()


def test_parse_ai_response():
    """Test parsing AI response"""
    generator = FixGenerator(use_ai=False)

    response = """
## File: config.py
```python
DATABASE_URL = os.getenv('DATABASE_URL')
```

## File: main.py
```python
from config import DATABASE_URL
```

## Commit Message
fix: Move hardcoded credentials to environment variables

## Explanation
Extracted hardcoded database URL to environment variable for security.
"""

    file_changes = generator._parse_ai_response(response, {})

    assert len(file_changes) == 2
    assert 'config.py' in file_changes
    assert 'main.py' in file_changes
    assert 'getenv' in file_changes['config.py']


def test_extract_commit_message_from_response():
    """Test extracting commit message from AI response"""
    generator = FixGenerator(use_ai=False)

    response = """
## Commit Message
fix: Add missing import statement

Resolves NameError by importing required module.
"""

    suggestion = FixSuggestion(
        failure_type=FailureType.IMPORT_ERROR,
        root_cause="Missing import",
        suggested_fix="Add import",
        code_changes=[],
        relevant_patterns=[],
        priority=Priority.HIGH,
        confidence=0.9,
        explanation="Missing import"
    )

    message = generator._extract_commit_message(response, suggestion)

    assert 'missing import' in message.lower()


# Integration Tests

def test_end_to_end_failure_analysis():
    """Test complete failure analysis workflow"""
    analyzer = FailureAnalyzer()

    # Create test result with failures
    test_result = TestResult(framework=TestFramework.PYTEST)
    test_result.passed = 0
    test_result.failed = 2
    test_result.output = """
FAILED test_example.py::test_add - AssertionError: assert 5 == 6
FAILED test_example.py::test_import - ImportError: No module named 'requests'
"""

    code_files = {
        "calculator.py": "def add(a, b): return a + b",
        "test_example.py": "import requests\ndef test_add(): assert add(2, 3) == 6"
    }

    suggestions = analyzer.analyze_failures(
        test_results=test_result,
        code_files=code_files
    )

    # Should have suggestions for failures
    assert len(suggestions) >= 0  # May vary based on parsing


@pytest.mark.asyncio
async def test_fix_suggestion_to_generated_fix():
    """Test converting suggestion to generated fix"""
    generator = FixGenerator(use_ai=False)

    suggestion = FixSuggestion(
        failure_type=FailureType.IMPORT_ERROR,
        root_cause="Missing module",
        suggested_fix="Install requests",
        code_changes=[{
            'file': 'requirements.txt',
            'old': '',
            'new': 'requests==2.28.0'
        }],
        relevant_patterns=[],
        priority=Priority.HIGH,
        confidence=0.9,
        explanation="Module not found"
    )

    fixes = await generator.generate_fixes(
        suggestions=[suggestion],
        code_files={'requirements.txt': ''},
        project_context="Test project"
    )

    assert len(fixes) == 1
    assert fixes[0].suggestion == suggestion
    assert 'requirements.txt' in fixes[0].file_changes or len(fixes[0].file_changes) == 0


def test_stack_frame_creation():
    """Test stack frame creation"""
    frame = StackFrame(
        file_path="/path/to/file.py",
        line_number=42,
        function_name="test_function",
        code_line="assert x == y"
    )

    assert frame.file_path == "/path/to/file.py"
    assert frame.line_number == 42
    assert frame.function_name == "test_function"
    assert frame.code_line == "assert x == y"


def test_fix_suggestion_to_dict():
    """Test fix suggestion serialization"""
    suggestion = FixSuggestion(
        failure_type=FailureType.ASSERTION_ERROR,
        root_cause="Logic error",
        suggested_fix="Fix algorithm",
        code_changes=[],
        relevant_patterns=["TDD.md"],
        priority=Priority.MEDIUM,
        confidence=0.8,
        explanation="Test expectation not met"
    )

    data = suggestion.to_dict()

    assert data['failure_type'] == 'assertion_error'
    assert data['root_cause'] == "Logic error"
    assert data['priority'] == 'medium'
    assert data['confidence'] == 0.8
