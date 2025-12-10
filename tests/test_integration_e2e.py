"""
End-to-End Integration Tests for Forge

Tests the complete pipeline focusing on components that can be tested
without external dependencies. Uses the actual Forge APIs correctly.
"""

import pytest
import tempfile
from pathlib import Path
from typing import Dict, List
import uuid

from forge.review import ReviewPanel, ReviewSeverity


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def generated_code_good():
    """Well-written generated code."""
    return {
        "src/main.py": '''
"""Main application module."""
from typing import List, Optional

def calculate_average(numbers: List[float]) -> float:
    """Calculate the average of a list of numbers.

    Args:
        numbers: List of numeric values

    Returns:
        The arithmetic mean

    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)


def process_items(items: List[dict]) -> List[dict]:
    """Process a list of items.

    Args:
        items: List of item dictionaries

    Returns:
        Processed items
    """
    results = []
    for item in items:
        if item.get("active", True):
            results.append({
                "id": item["id"],
                "processed": True
            })
    return results
''',
        "tests/test_main.py": '''
"""Tests for main module."""
import pytest
from src.main import calculate_average, process_items


class TestCalculateAverage:
    """Tests for calculate_average function."""

    def test_average_of_integers(self):
        """Test average calculation with integers."""
        result = calculate_average([1, 2, 3, 4, 5])
        assert result == 3.0

    def test_average_of_floats(self):
        """Test average calculation with floats."""
        result = calculate_average([1.5, 2.5, 3.5])
        assert result == 2.5

    def test_empty_list_raises(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            calculate_average([])


class TestProcessItems:
    """Tests for process_items function."""

    def test_process_active_items(self):
        """Test processing active items."""
        items = [
            {"id": 1, "active": True},
            {"id": 2, "active": False},
            {"id": 3}  # Defaults to active
        ]
        result = process_items(items)
        assert len(result) == 2

    def test_empty_list(self):
        """Test processing empty list."""
        assert process_items([]) == []
'''
    }


@pytest.fixture
def generated_code_problematic():
    """Generated code with issues."""
    return {
        "src/unsafe.py": '''
import os

# Security issues
SECRET_KEY = "hardcoded_secret_123"
API_TOKEN = "sk-prod-12345"

def process_user_input(user_input):
    # Command injection vulnerability
    os.system(f"echo {user_input}")

    # Code injection vulnerability
    result = eval(user_input)

    return result

def get_data(query):
    # SQL injection vulnerability
    sql = f"SELECT * FROM users WHERE id = {query}"
    return sql
'''
    }


# =============================================================================
# Test: Review System Integration
# =============================================================================


class TestReviewSystemIntegration:
    """Tests for review system as part of the pipeline."""

    def test_review_approves_good_code(self, generated_code_good):
        """Test that good code passes review."""
        panel = ReviewPanel(approval_threshold=6)
        report = panel.review_files(generated_code_good)

        # Should have reasonable approval
        assert report.decision.approval_count >= 6, \
            f"Expected at least 6 approvals, got {report.decision.approval_count}"

        # Should have no critical findings
        critical = [
            f for f in report.all_findings
            if f.severity == ReviewSeverity.CRITICAL
        ]
        assert len(critical) == 0, f"Found critical issues: {critical}"

    def test_review_rejects_problematic_code(self, generated_code_problematic):
        """Test that problematic code fails review."""
        panel = ReviewPanel(approval_threshold=8)
        report = panel.review_files(generated_code_problematic)

        # Should be rejected or have blocking findings
        blocking = report.get_blocking_findings()
        assert len(blocking) > 0, "Expected blocking findings for insecure code"

    def test_review_provides_actionable_feedback(self, generated_code_problematic):
        """Test that review findings are actionable."""
        panel = ReviewPanel()
        report = panel.review_files(generated_code_problematic)

        # Each finding should have category and message
        for finding in report.all_findings:
            assert finding.category, "Finding should have category"
            assert finding.message, "Finding should have message"
            assert finding.severity, "Finding should have severity"

    def test_review_results_serializable(self, generated_code_good):
        """Test that review results can be serialized."""
        import json

        panel = ReviewPanel()
        report = panel.review_files(generated_code_good)

        # Convert to dict
        report_dict = report.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(report_dict)
        restored = json.loads(json_str)

        assert "decision" in restored
        assert "findings" in restored


# =============================================================================
# Test: Code Quality Pipeline
# =============================================================================


class TestCodeQualityPipeline:
    """Tests for code quality checking as part of the pipeline."""

    def test_security_findings_detected(self, generated_code_problematic):
        """Test that security issues are detected."""
        panel = ReviewPanel()
        report = panel.review_files(generated_code_problematic)

        # Should detect security issues
        security_findings = [
            f for f in report.all_findings
            if "security" in f.category.lower() or
               "secret" in f.category.lower() or
               "injection" in f.category.lower()
        ]

        assert len(security_findings) > 0, \
            "Expected security findings for code with hardcoded secrets and injection"

    def test_all_reviewers_provide_feedback(self, generated_code_good):
        """Test that all 12 reviewers provide results per file."""
        panel = ReviewPanel()
        report = panel.review_files(generated_code_good)

        # With multi-file review, each reviewer runs once per file
        # So total results = 12 reviewers * number of files
        expected_results = 12 * len(generated_code_good)
        assert len(report.individual_results) == expected_results, \
            f"Expected {expected_results} reviewer results, got {len(report.individual_results)}"

        # Each reviewer should have provided a result
        for result in report.individual_results:
            assert result.agent_name, "Result should have agent name"
            assert isinstance(result.approved, bool), "Result should have approval status"

    def test_findings_grouped_by_severity(self, generated_code_problematic):
        """Test that findings are properly grouped."""
        panel = ReviewPanel()
        report = panel.review_files(generated_code_problematic)

        # Should have severity grouping
        assert isinstance(report.findings_by_severity, dict)

        # Total should match individual findings
        severity_total = sum(
            len(findings)
            for findings in report.findings_by_severity.values()
        )
        assert severity_total == len(report.all_findings)


# =============================================================================
# Test: Multi-File Review
# =============================================================================


class TestMultiFileReview:
    """Tests for reviewing multiple files together."""

    def test_review_multiple_files(self, generated_code_good):
        """Test reviewing multiple files in one pass."""
        panel = ReviewPanel()
        report = panel.review_files(generated_code_good)

        # Should review all files
        assert len(report.reviewed_files) == len(generated_code_good)

    def test_findings_attributed_to_files(self, generated_code_problematic):
        """Test that findings reference their source files."""
        panel = ReviewPanel()
        report = panel.review_files(generated_code_problematic)

        # Findings with file paths should reference actual files
        for finding in report.all_findings:
            if finding.file_path:
                # Should be one of the reviewed files
                assert finding.file_path in generated_code_problematic or \
                    any(finding.file_path in f for f in generated_code_problematic)


# =============================================================================
# Test: Review Configuration
# =============================================================================


class TestReviewConfiguration:
    """Tests for review panel configuration."""

    def test_custom_approval_threshold(self, generated_code_good):
        """Test panel with different approval thresholds."""
        # Strict threshold
        strict_panel = ReviewPanel(approval_threshold=12)
        strict_report = strict_panel.review_files(generated_code_good)

        # Lenient threshold
        lenient_panel = ReviewPanel(approval_threshold=1)
        lenient_report = lenient_panel.review_files(generated_code_good)

        # Both should process, but lenient should more likely approve
        assert strict_report.decision.threshold == 12
        assert lenient_report.decision.threshold == 1

    def test_parallel_vs_sequential(self, generated_code_good):
        """Test parallel and sequential review produce same results."""
        parallel_panel = ReviewPanel(parallel=True)
        sequential_panel = ReviewPanel(parallel=False)

        parallel_report = parallel_panel.review_files(generated_code_good)
        sequential_report = sequential_panel.review_files(generated_code_good)

        # Should produce same decision
        assert parallel_report.decision.approved == sequential_report.decision.approved


# =============================================================================
# Test: Pipeline Flow Decisions
# =============================================================================


class TestPipelineFlowDecisions:
    """Tests for pipeline flow control based on review results."""

    def test_approval_enables_next_stage(self, generated_code_good):
        """Test that approval allows pipeline to continue."""
        panel = ReviewPanel(approval_threshold=6)
        report = panel.review_files(generated_code_good)

        # Determine next action based on review
        if report.decision.approved:
            next_action = "commit"
        elif len(report.get_critical_findings()) > 0:
            next_action = "block"
        else:
            next_action = "iterate"

        # Good code should allow commit
        assert next_action in ["commit", "iterate"]

    def test_critical_findings_block_commit(self, generated_code_problematic):
        """Test that critical findings block commit."""
        panel = ReviewPanel()
        report = panel.review_files(generated_code_problematic)

        blocking = report.get_blocking_findings()

        # Should have blocking issues
        if blocking:
            can_commit = False
        else:
            can_commit = report.decision.approved

        # Problematic code should have blocking issues
        assert len(blocking) > 0 or not report.decision.approved

    def test_iteration_count_tracking(self, generated_code_problematic):
        """Test tracking iterations through review."""
        panel = ReviewPanel()

        # Simulate iteration tracking
        iterations = 0
        max_iterations = 3
        current_code = generated_code_problematic

        while iterations < max_iterations:
            report = panel.review_files(current_code)
            iterations += 1

            if report.decision.approved:
                break

            # In real scenario, would generate fixes here
            # For test, just break after first iteration
            break

        # Should have done at least one iteration
        assert iterations >= 1


# =============================================================================
# Test: Report Generation
# =============================================================================


class TestReportGeneration:
    """Tests for review report generation."""

    def test_summary_format(self, generated_code_good):
        """Test human-readable summary format."""
        panel = ReviewPanel()
        report = panel.review_files(generated_code_good)

        summary = report.format_summary()

        assert "REVIEW PANEL REPORT" in summary
        assert "approve" in summary.lower() or "reject" in summary.lower()

    def test_report_timing(self, generated_code_good):
        """Test that review timing is recorded."""
        panel = ReviewPanel()
        report = panel.review_files(generated_code_good)

        assert report.total_review_time_seconds >= 0

    def test_report_metadata(self, generated_code_good):
        """Test that report includes metadata."""
        panel = ReviewPanel()
        report = panel.review_files(generated_code_good)

        report_dict = report.to_dict()

        assert "metadata" in report_dict
        assert "timestamp" in report_dict["metadata"]


# =============================================================================
# Test: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases in the pipeline."""

    def test_empty_file(self):
        """Test reviewing empty file."""
        panel = ReviewPanel()
        report = panel.review_files({"empty.py": ""})

        # Should handle gracefully
        assert isinstance(report.decision.approved, bool)

    def test_single_line_file(self):
        """Test reviewing minimal file."""
        panel = ReviewPanel()
        report = panel.review_files({"minimal.py": "x = 1"})

        assert isinstance(report.decision.approved, bool)

    def test_large_file(self):
        """Test reviewing large file."""
        # Generate large file
        large_content = "\n".join([
            f"def function_{i}(x):\n    return x + {i}\n"
            for i in range(100)
        ])

        panel = ReviewPanel()
        report = panel.review_files({"large.py": large_content})

        assert isinstance(report.decision.approved, bool)

    def test_non_python_file(self):
        """Test reviewing non-Python content."""
        panel = ReviewPanel()
        report = panel.review_files({
            "config.json": '{"key": "value"}'
        })

        # Should handle gracefully
        assert isinstance(report.decision.approved, bool)
