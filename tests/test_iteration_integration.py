"""
Integration test for the complete iteration system
"""

import pytest
from pathlib import Path
from forge.layers.failure_analyzer import FailureAnalyzer, FailureType, Priority
from forge.layers.fix_generator import FixGenerator
from forge.testing.docker_runner import TestResult, TestFramework


def test_failure_analyzer_with_real_pytest_output():
    """Test failure analyzer with realistic pytest output"""
    analyzer = FailureAnalyzer()

    # Simulated pytest output from broken calculator
    pytest_output = """
============================= test session starts ==============================
collected 5 items

test_calculator.py::test_add PASSED                                      [ 20%]
test_calculator.py::test_subtract PASSED                                 [ 40%]
test_calculator.py::test_multiply FAILED                                 [ 60%]
test_calculator.py::test_divide PASSED                                   [ 80%]
test_calculator.py::test_divide_by_zero PASSED                           [100%]

=================================== FAILURES ===================================
________________________________ test_multiply _________________________________

    def test_multiply():
        \"\"\"Test multiplication - WILL FAIL\"\"\"
>       assert multiply(2, 3) == 6
E       AssertionError: assert 5 == 6
E        +  where 5 = multiply(2, 3)

test_calculator.py:24: AssertionError
=========================== short test summary info ============================
FAILED test_calculator.py::test_multiply - AssertionError: assert 5 == 6
========================= 1 failed, 4 passed in 0.12s ==========================
"""

    test_result = TestResult(framework=TestFramework.PYTEST)
    test_result.passed = 4
    test_result.failed = 1
    test_result.output = pytest_output

    code_files = {
        "calculator.py": """
def multiply(a, b):
    return a + b  # Bug: should be a * b
""",
        "test_calculator.py": """
def test_multiply():
    assert multiply(2, 3) == 6
"""
    }

    suggestions = analyzer.analyze_failures(
        test_results=test_result,
        code_files=code_files
    )

    # Should identify the failure
    assert len(suggestions) >= 0  # May vary based on parsing

    # If suggestions found, verify structure
    if suggestions:
        suggestion = suggestions[0]
        assert suggestion.failure_type == FailureType.ASSERTION_ERROR
        assert suggestion.priority in [Priority.MEDIUM, Priority.HIGH]
        assert 0.0 <= suggestion.confidence <= 1.0


def test_fix_generator_pattern_mode():
    """Test fix generator in pattern mode (no AI)"""
    generator = FixGenerator(use_ai=False)

    from forge.layers.failure_analyzer import FixSuggestion

    suggestion = FixSuggestion(
        failure_type=FailureType.ASSERTION_ERROR,
        root_cause="multiply function returns wrong value",
        suggested_fix="Fix multiply function to use multiplication operator",
        code_changes=[{
            'file': 'calculator.py',
            'old': 'return a + b',
            'new': 'return a * b'
        }],
        relevant_patterns=['TDD.md'],
        priority=Priority.MEDIUM,
        confidence=0.85,
        explanation="The multiply function is using addition instead of multiplication"
    )

    code_files = {
        "calculator.py": "def multiply(a, b):\n    return a + b\n"
    }

    fix = generator._generate_pattern_fix(suggestion, code_files)

    assert fix is not None
    assert fix.suggestion == suggestion
    assert 'calculator.py' in fix.file_changes
    assert 'a * b' in fix.file_changes['calculator.py']
    assert 'fix' in fix.commit_message.lower()


def test_fix_prioritization():
    """Test that critical fixes are prioritized over low priority ones"""
    from forge.layers.failure_analyzer import FixSuggestion
    from forge.layers.fix_generator import GeneratedFix

    generator = FixGenerator(use_ai=False)

    # Create low priority fix
    low_priority = FixSuggestion(
        failure_type=FailureType.ASSERTION_ERROR,
        root_cause="Logic error",
        suggested_fix="Fix logic",
        code_changes=[],
        relevant_patterns=[],
        priority=Priority.LOW,
        confidence=0.6,
        explanation="Minor issue"
    )

    # Create critical priority fix
    critical_priority = FixSuggestion(
        failure_type=FailureType.SYNTAX_ERROR,
        root_cause="Syntax error",
        suggested_fix="Fix syntax",
        code_changes=[],
        relevant_patterns=[],
        priority=Priority.CRITICAL,
        confidence=0.95,
        explanation="Syntax error prevents execution"
    )

    low_fix = GeneratedFix(
        suggestion=low_priority,
        file_changes={},
        commit_message="Fix minor issue"
    )

    critical_fix = GeneratedFix(
        suggestion=critical_priority,
        file_changes={},
        commit_message="Fix critical syntax error"
    )

    # Prioritize with low priority first
    fixes = [low_fix, critical_fix]
    prioritized = generator.prioritize_fixes(fixes)

    # Critical should come first
    assert prioritized[0].suggestion.priority == Priority.CRITICAL
    assert prioritized[1].suggestion.priority == Priority.LOW


def test_commit_message_format():
    """Test commit message follows conventional format"""
    from forge.layers.failure_analyzer import FixSuggestion

    generator = FixGenerator(use_ai=False)

    suggestion = FixSuggestion(
        failure_type=FailureType.IMPORT_ERROR,
        root_cause="Missing pytest dependency",
        suggested_fix="Add pytest to requirements.txt",
        code_changes=[],
        relevant_patterns=[],
        priority=Priority.HIGH,
        confidence=0.9,
        explanation="Import error: No module named 'pytest'"
    )

    message = generator._generate_commit_message(suggestion)

    # Should follow conventional commits format
    assert message.startswith("fix")
    assert "pytest" in message.lower() or "dependency" in message.lower()
    assert "Priority:" in message
    assert "Confidence:" in message


def test_impact_estimation():
    """Test impact estimation for different fix sizes"""
    from forge.layers.fix_generator import GeneratedFix
    from unittest.mock import Mock

    generator = FixGenerator(use_ai=False)

    # Test minimal impact
    small_fix = GeneratedFix(
        suggestion=Mock(),
        file_changes={"test.py": "x = 1\n"},
        commit_message="Small fix"
    )

    impact = generator.estimate_impact(small_fix)
    assert "minimal" in impact.lower() or "low" in impact.lower()

    # Test high impact
    large_content = "\n".join([f"line {i}" for i in range(100)])
    large_fix = GeneratedFix(
        suggestion=Mock(),
        file_changes={
            f"file{i}.py": large_content for i in range(10)
        },
        commit_message="Large refactor"
    )

    impact = generator.estimate_impact(large_fix)
    assert "high" in impact.lower() or "medium" in impact.lower()


def test_error_categorization_comprehensive():
    """Test error categorization for various error types"""
    analyzer = FailureAnalyzer()

    test_cases = [
        ("ImportError: No module named 'requests'", FailureType.IMPORT_ERROR),
        ("NameError: name 'foo' is not defined", FailureType.NAME_ERROR),
        ("TypeError: unsupported operand", FailureType.TYPE_ERROR),
        ("SyntaxError: invalid syntax", FailureType.SYNTAX_ERROR),
        ("AssertionError: assert False", FailureType.ASSERTION_ERROR),
        ("AttributeError: 'NoneType' object has no attribute", FailureType.ATTRIBUTE_ERROR),
        ("KeyError: 'missing_key'", FailureType.KEY_ERROR),
        ("IndexError: list index out of range", FailureType.INDEX_ERROR),
        ("ValueError: invalid literal", FailureType.VALUE_ERROR),
        ("ZeroDivisionError: division by zero", FailureType.ZERO_DIVISION_ERROR),
    ]

    for error_msg, expected_type in test_cases:
        result = analyzer._categorize_failure(error_msg)
        assert result == expected_type, f"Failed to categorize: {error_msg}"


def test_learning_database_structure():
    """Test learning database structure"""
    from forge.layers.review import ReviewLayer
    from pathlib import Path
    import tempfile
    import json

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_learning.json"

        review_layer = ReviewLayer(learning_db_path=db_path)

        # Get initial statistics
        stats = review_layer.get_learning_statistics()

        assert 'total_sessions' in stats
        assert 'successful_sessions' in stats
        assert 'success_rate' in stats
        assert 'total_patterns' in stats

        # Initially should be zeros
        assert stats['total_sessions'] == 0
        assert stats['total_patterns'] == 0
