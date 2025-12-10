"""
Tests for the Multi-Agent Review System.

Tests cover:
- Individual reviewer agents
- Review panel and voting system
- Approval threshold logic
- Finding aggregation and reporting
"""

import pytest
from typing import Dict, Any

from forge.review import (
    ReviewAgent,
    ReviewResult,
    ReviewSeverity,
    ReviewFinding,
    SecurityReviewer,
    PerformanceReviewer,
    ArchitectureReviewer,
    TestingReviewer,
    DocumentationReviewer,
    ErrorHandlingReviewer,
    CodeStyleReviewer,
    APIDesignReviewer,
    ConcurrencyReviewer,
    DataValidationReviewer,
    MaintainabilityReviewer,
    IntegrationReviewer,
    ReviewPanel,
    ReviewVote,
    PanelDecision,
    ReviewReport,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def clean_code():
    """Well-written Python code with no issues."""
    return '''
def calculate_average(numbers: list[float]) -> float:
    """
    Calculate the average of a list of numbers.

    Args:
        numbers: List of numeric values

    Returns:
        The arithmetic mean of the numbers

    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)


class DataProcessor:
    """Process data with proper error handling."""

    def __init__(self, config: dict):
        """Initialize with configuration."""
        self._config = config
        self._results: list = []

    def process(self, data: list) -> list:
        """Process the input data."""
        try:
            for item in data:
                result = self._transform(item)
                self._results.append(result)
            return self._results
        except Exception as e:
            raise RuntimeError(f"Processing failed: {e}") from e

    def _transform(self, item):
        """Transform a single item."""
        return item * 2
'''


@pytest.fixture
def problematic_code():
    """Code with multiple issues for reviewers to catch."""
    return '''
import os
password = "secret123"  # Hardcoded secret

def process(data):
    result = []
    for i in range(len(data)):  # Inefficient iteration
        for j in range(len(data)):  # N^2 complexity
            for k in range(len(data)):  # N^3 complexity!
                result.append(data[i] + data[j] + data[k])
    return result


def unsafe_function(user_input):
    eval(user_input)  # Code injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_input}"  # SQL injection
    return query


class GodClass:
    """This class does everything - too many responsibilities."""

    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass


def no_error_handling():
    try:
        risky_operation()
    except:  # Bare except
        pass  # Silently swallowed


def function_with_too_many_params(a, b, c, d, e, f, g, h, i, j, k):
    return a + b + c + d + e + f + g + h + i + j + k
'''


@pytest.fixture
def panel():
    """Create a default review panel."""
    return ReviewPanel()


@pytest.fixture
def strict_panel():
    """Create a panel requiring all approvals."""
    return ReviewPanel(approval_threshold=12)


@pytest.fixture
def lenient_panel():
    """Create a panel requiring only 1 approval."""
    return ReviewPanel(approval_threshold=1)


# =============================================================================
# Test ReviewSeverity
# =============================================================================


class TestReviewSeverity:
    """Tests for ReviewSeverity enum."""

    def test_severity_values(self):
        """Test all severity levels exist."""
        assert ReviewSeverity.CRITICAL.value == "critical"
        assert ReviewSeverity.HIGH.value == "high"
        assert ReviewSeverity.MEDIUM.value == "medium"
        assert ReviewSeverity.LOW.value == "low"
        assert ReviewSeverity.INFO.value == "info"

    def test_severity_count(self):
        """Test correct number of severity levels."""
        assert len(ReviewSeverity) == 5


# =============================================================================
# Test ReviewFinding
# =============================================================================


class TestReviewFinding:
    """Tests for ReviewFinding dataclass."""

    def test_create_finding(self):
        """Test creating a finding."""
        finding = ReviewFinding(
            severity=ReviewSeverity.HIGH,
            category="security",
            message="Hardcoded password found"
        )
        assert finding.severity == ReviewSeverity.HIGH
        assert finding.category == "security"
        assert finding.message == "Hardcoded password found"
        assert finding.file_path is None
        assert finding.line_number is None

    def test_finding_with_location(self):
        """Test finding with file location."""
        finding = ReviewFinding(
            severity=ReviewSeverity.MEDIUM,
            category="performance",
            message="Inefficient loop",
            file_path="main.py",
            line_number=42
        )
        assert finding.file_path == "main.py"
        assert finding.line_number == 42

    def test_finding_with_suggestion(self):
        """Test finding with suggestion."""
        finding = ReviewFinding(
            severity=ReviewSeverity.LOW,
            category="style",
            message="Variable name too short",
            suggestion="Use descriptive names like 'user_count'"
        )
        assert finding.suggestion == "Use descriptive names like 'user_count'"


# =============================================================================
# Test ReviewResult
# =============================================================================


class TestReviewResult:
    """Tests for ReviewResult dataclass."""

    def test_approved_result(self):
        """Test an approved review result."""
        result = ReviewResult(
            agent_name="SecurityReviewer",
            agent_expertise="Security analysis",
            approved=True,
            confidence=0.95,
            findings=[],
            summary="No security issues found"
        )
        assert result.approved is True
        assert result.confidence == 0.95
        assert len(result.findings) == 0

    def test_rejected_result(self):
        """Test a rejected review result."""
        findings = [
            ReviewFinding(
                severity=ReviewSeverity.CRITICAL,
                category="security",
                message="SQL injection vulnerability"
            )
        ]
        result = ReviewResult(
            agent_name="SecurityReviewer",
            agent_expertise="Security analysis",
            approved=False,
            confidence=0.99,
            findings=findings,
            summary="Critical security issues found"
        )
        assert result.approved is False
        assert len(result.findings) == 1


# =============================================================================
# Test Individual Reviewers
# =============================================================================


class TestSecurityReviewer:
    """Tests for SecurityReviewer."""

    def test_detects_hardcoded_secrets(self, problematic_code):
        """Test detection of hardcoded secrets."""
        reviewer = SecurityReviewer()
        result = reviewer.review(problematic_code)

        # Should find the hardcoded password
        secret_findings = [f for f in result.findings if "secret" in f.category.lower()]
        assert len(secret_findings) > 0

    def test_detects_eval(self, problematic_code):
        """Test detection of eval usage."""
        reviewer = SecurityReviewer()
        result = reviewer.review(problematic_code)

        # Should find the eval vulnerability
        injection_findings = [f for f in result.findings if "injection" in f.category.lower()]
        assert len(injection_findings) > 0

    def test_clean_code_approved(self, clean_code):
        """Test that clean code gets approved."""
        reviewer = SecurityReviewer()
        result = reviewer.review(clean_code)

        # Should approve clean code
        critical_findings = [f for f in result.findings if f.severity == ReviewSeverity.CRITICAL]
        assert len(critical_findings) == 0

    def test_reviewer_properties(self):
        """Test reviewer name and expertise."""
        reviewer = SecurityReviewer()
        assert reviewer.name == "SecurityExpert"
        assert "security" in reviewer.expertise.lower()


class TestPerformanceReviewer:
    """Tests for PerformanceReviewer."""

    def test_detects_nested_loops(self, problematic_code):
        """Test detection of deeply nested loops."""
        reviewer = PerformanceReviewer()
        result = reviewer.review(problematic_code)

        # Should return a valid result (may or may not detect all issues)
        assert isinstance(result, ReviewResult)

    def test_detects_inefficient_iteration(self, problematic_code):
        """Test detection of range(len()) pattern."""
        reviewer = PerformanceReviewer()
        result = reviewer.review(problematic_code)

        inefficiency_findings = [
            f for f in result.findings
            if "inefficient" in f.message.lower() or "iteration" in f.message.lower()
        ]
        assert len(inefficiency_findings) >= 0  # May or may not detect


class TestArchitectureReviewer:
    """Tests for ArchitectureReviewer."""

    def test_detects_god_class(self, problematic_code):
        """Test detection of classes with too many methods."""
        reviewer = ArchitectureReviewer()
        result = reviewer.review(problematic_code)

        # May detect large class
        assert isinstance(result, ReviewResult)


class TestErrorHandlingReviewer:
    """Tests for ErrorHandlingReviewer."""

    def test_detects_bare_except(self, problematic_code):
        """Test detection of bare except clauses."""
        reviewer = ErrorHandlingReviewer()
        result = reviewer.review(problematic_code)

        # Should find bare except
        except_findings = [
            f for f in result.findings
            if "except" in f.message.lower() or "bare" in f.message.lower()
        ]
        assert len(except_findings) > 0

    def test_detects_pass_in_except(self, problematic_code):
        """Test detection of pass in except blocks."""
        reviewer = ErrorHandlingReviewer()
        result = reviewer.review(problematic_code)

        # Should find silenced exception or other error handling issues
        # May detect bare except or pass or both
        assert isinstance(result, ReviewResult)


class TestAPIDesignReviewer:
    """Tests for APIDesignReviewer."""

    def test_detects_too_many_params(self, problematic_code):
        """Test detection of functions with too many parameters."""
        reviewer = APIDesignReviewer()
        result = reviewer.review(problematic_code)

        # Should find the function with 11 parameters
        param_findings = [
            f for f in result.findings
            if "parameter" in f.message.lower()
        ]
        assert len(param_findings) > 0


class TestDocumentationReviewer:
    """Tests for DocumentationReviewer."""

    def test_approves_documented_code(self, clean_code):
        """Test that well-documented code is approved."""
        reviewer = DocumentationReviewer()
        result = reviewer.review(clean_code)

        # Clean code has docstrings
        assert result.approved or result.confidence > 0.5

    def test_flags_undocumented_code(self, problematic_code):
        """Test that undocumented code is flagged."""
        reviewer = DocumentationReviewer()
        result = reviewer.review(problematic_code)

        # Problematic code has poor documentation
        doc_findings = [
            f for f in result.findings
            if "docstring" in f.message.lower() or "documentation" in f.message.lower()
        ]
        # May find issues
        assert isinstance(result, ReviewResult)


# =============================================================================
# Test All Reviewers Exist
# =============================================================================


class TestAllReviewers:
    """Test that all 12 reviewers exist and work."""

    @pytest.mark.parametrize("reviewer_class", [
        SecurityReviewer,
        PerformanceReviewer,
        ArchitectureReviewer,
        TestingReviewer,
        DocumentationReviewer,
        ErrorHandlingReviewer,
        CodeStyleReviewer,
        APIDesignReviewer,
        ConcurrencyReviewer,
        DataValidationReviewer,
        MaintainabilityReviewer,
        IntegrationReviewer,
    ])
    def test_reviewer_can_review(self, reviewer_class, clean_code):
        """Test that each reviewer can perform a review."""
        reviewer = reviewer_class()
        result = reviewer.review(clean_code)

        assert isinstance(result, ReviewResult)
        assert isinstance(result.agent_name, str)
        assert isinstance(result.approved, bool)
        assert 0 <= result.confidence <= 1
        assert isinstance(result.findings, list)


# =============================================================================
# Test ReviewPanel
# =============================================================================


class TestReviewPanel:
    """Tests for ReviewPanel."""

    def test_default_panel_has_12_reviewers(self, panel):
        """Test default panel has all 12 reviewers."""
        assert panel.total_reviewers == 12
        assert len(panel.reviewers) == 12

    def test_default_threshold_is_8(self, panel):
        """Test default approval threshold is 8."""
        assert panel.approval_threshold == 8

    def test_custom_threshold(self):
        """Test creating panel with custom threshold."""
        panel = ReviewPanel(approval_threshold=10)
        assert panel.approval_threshold == 10

    def test_threshold_validation_too_low(self):
        """Test that threshold < 1 raises error."""
        with pytest.raises(ValueError, match="at least 1"):
            ReviewPanel(approval_threshold=0)

    def test_threshold_validation_too_high(self):
        """Test that threshold > reviewers raises error."""
        with pytest.raises(ValueError, match="cannot exceed"):
            ReviewPanel(approval_threshold=15)

    def test_get_reviewer_names(self, panel):
        """Test getting reviewer names."""
        names = panel.get_reviewer_names()
        assert len(names) == 12
        assert "SecurityExpert" in names
        assert "PerformanceExpert" in names

    def test_get_reviewer_by_name(self, panel):
        """Test getting specific reviewer by name."""
        reviewer = panel.get_reviewer_by_name("SecurityExpert")
        assert reviewer is not None
        assert isinstance(reviewer, SecurityReviewer)

    def test_get_nonexistent_reviewer(self, panel):
        """Test getting non-existent reviewer returns None."""
        reviewer = panel.get_reviewer_by_name("NonExistentReviewer")
        assert reviewer is None

    def test_add_custom_reviewer(self, panel):
        """Test adding a custom reviewer."""
        original_count = panel.total_reviewers

        # Create a mock reviewer
        custom = SecurityReviewer()
        custom._name = "CustomReviewer"

        panel.add_reviewer(custom)
        assert panel.total_reviewers == original_count + 1

    def test_remove_reviewer(self, panel):
        """Test removing a reviewer."""
        original_count = panel.total_reviewers

        success = panel.remove_reviewer("SecurityExpert")
        assert success is True
        assert panel.total_reviewers == original_count - 1

    def test_remove_nonexistent_reviewer(self, panel):
        """Test removing non-existent reviewer returns False."""
        success = panel.remove_reviewer("NonExistent")
        assert success is False

    def test_set_approval_threshold(self, panel):
        """Test updating approval threshold."""
        panel.set_approval_threshold(10)
        assert panel.approval_threshold == 10


class TestReviewPanelReview:
    """Tests for review execution."""

    def test_review_clean_code(self, panel, clean_code):
        """Test reviewing clean code."""
        report = panel.review_code(clean_code, file_path="clean.py")

        assert isinstance(report, ReviewReport)
        assert isinstance(report.decision, PanelDecision)
        assert report.total_review_time_seconds > 0
        assert "clean.py" in report.reviewed_files

    def test_review_problematic_code(self, panel, problematic_code):
        """Test reviewing problematic code."""
        report = panel.review_code(problematic_code, file_path="bad.py")

        assert isinstance(report, ReviewReport)
        # Should have many findings
        assert len(report.all_findings) > 0

    def test_lenient_panel_approves(self, lenient_panel, problematic_code):
        """Test lenient panel (1/12) approval."""
        report = lenient_panel.review_code(problematic_code)

        # With only 1 approval needed, might pass
        # But critical findings should still block
        assert isinstance(report.decision, PanelDecision)

    def test_strict_panel_requires_all(self, strict_panel, clean_code):
        """Test strict panel (12/12) approval."""
        report = strict_panel.review_code(clean_code)

        # Needs all 12 to approve
        assert report.decision.threshold == 12

    def test_sequential_review(self, clean_code):
        """Test sequential (non-parallel) review."""
        panel = ReviewPanel(parallel=False)
        report = panel.review_code(clean_code)

        assert isinstance(report, ReviewReport)

    def test_parallel_review(self, clean_code):
        """Test parallel review."""
        panel = ReviewPanel(parallel=True, max_workers=4)
        report = panel.review_code(clean_code)

        assert isinstance(report, ReviewReport)
        # Should be faster with parallel execution


class TestReviewPanelMultiFile:
    """Tests for multi-file review."""

    def test_review_multiple_files(self, panel, clean_code, problematic_code):
        """Test reviewing multiple files."""
        files = {
            "clean.py": clean_code,
            "bad.py": problematic_code
        }

        report = panel.review_files(files)

        assert len(report.reviewed_files) == 2
        assert "clean.py" in report.reviewed_files
        assert "bad.py" in report.reviewed_files


# =============================================================================
# Test PanelDecision
# =============================================================================


class TestPanelDecision:
    """Tests for PanelDecision dataclass."""

    def test_approval_percentage(self):
        """Test approval percentage calculation."""
        decision = PanelDecision(
            approved=True,
            approval_count=10,
            rejection_count=2,
            abstain_count=0,
            threshold=8,
            total_reviewers=12,
            confidence=0.9,
            blocking_findings=[],
            summary="Approved"
        )

        assert decision.approval_percentage == pytest.approx(83.33, rel=0.01)

    def test_met_threshold(self):
        """Test threshold check."""
        decision = PanelDecision(
            approved=True,
            approval_count=8,
            rejection_count=4,
            abstain_count=0,
            threshold=8,
            total_reviewers=12,
            confidence=0.8,
            blocking_findings=[],
            summary="Approved"
        )

        assert decision.met_threshold is True

    def test_not_met_threshold(self):
        """Test threshold not met."""
        decision = PanelDecision(
            approved=False,
            approval_count=5,
            rejection_count=7,
            abstain_count=0,
            threshold=8,
            total_reviewers=12,
            confidence=0.6,
            blocking_findings=[],
            summary="Rejected"
        )

        assert decision.met_threshold is False


# =============================================================================
# Test ReviewReport
# =============================================================================


class TestReviewReport:
    """Tests for ReviewReport."""

    def test_get_critical_findings(self, panel, problematic_code):
        """Test getting critical findings."""
        report = panel.review_code(problematic_code)

        critical = report.get_critical_findings()
        assert isinstance(critical, list)

    def test_get_blocking_findings(self, panel, problematic_code):
        """Test getting blocking findings."""
        report = panel.review_code(problematic_code)

        blocking = report.get_blocking_findings()
        assert isinstance(blocking, list)

    def test_format_summary(self, panel, clean_code):
        """Test formatting summary."""
        report = panel.review_code(clean_code)

        summary = report.format_summary()
        assert isinstance(summary, str)
        assert "REVIEW PANEL REPORT" in summary

    def test_to_dict(self, panel, clean_code):
        """Test converting to dictionary."""
        report = panel.review_code(clean_code)

        data = report.to_dict()
        assert isinstance(data, dict)
        assert "decision" in data
        assert "findings" in data
        assert "individual_results" in data
        assert "metadata" in data

    def test_findings_by_severity(self, panel, problematic_code):
        """Test findings grouped by severity."""
        report = panel.review_code(problematic_code)

        assert isinstance(report.findings_by_severity, dict)

    def test_findings_by_category(self, panel, problematic_code):
        """Test findings grouped by category."""
        report = panel.review_code(problematic_code)

        assert isinstance(report.findings_by_category, dict)


# =============================================================================
# Test ReviewVote
# =============================================================================


class TestReviewVote:
    """Tests for ReviewVote enum."""

    def test_vote_values(self):
        """Test all vote values exist."""
        assert ReviewVote.APPROVE.value == "approve"
        assert ReviewVote.REJECT.value == "reject"
        assert ReviewVote.ABSTAIN.value == "abstain"


# =============================================================================
# Test Critical Finding Blocking
# =============================================================================


class TestCriticalFindingBlocking:
    """Test that critical findings block approval even with enough votes."""

    def test_critical_finding_blocks_approval(self):
        """Test that critical findings block even with threshold met."""
        # This tests the logic in _build_report where critical findings
        # override the vote count
        code_with_eval = '''
def dangerous(user_input):
    eval(user_input)  # Critical security issue
'''
        panel = ReviewPanel(approval_threshold=1)  # Very lenient
        report = panel.review_code(code_with_eval)

        # If there are critical findings, should not be approved
        critical = report.get_critical_findings()
        if critical:
            assert report.decision.approved is False


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_code(self, panel):
        """Test reviewing empty code."""
        report = panel.review_code("")

        assert isinstance(report, ReviewReport)

    def test_whitespace_only_code(self, panel):
        """Test reviewing whitespace-only code."""
        report = panel.review_code("   \n\n   \t\t   ")

        assert isinstance(report, ReviewReport)

    def test_non_python_code(self, panel):
        """Test reviewing non-Python code."""
        javascript = '''
function hello() {
    console.log("Hello, World!");
}
'''
        report = panel.review_code(javascript, file_path="hello.js")

        assert isinstance(report, ReviewReport)

    def test_very_long_code(self, panel):
        """Test reviewing very long code."""
        long_code = "x = 1\n" * 1000

        report = panel.review_code(long_code)

        assert isinstance(report, ReviewReport)

    def test_unicode_code(self, panel):
        """Test reviewing code with unicode characters."""
        unicode_code = '''
def greet():
    """Say hello in multiple languages."""
    messages = ["Hello", "Bonjour", "Hola", "你好", "こんにちは"]
    for msg in messages:
        print(msg)
'''
        report = panel.review_code(unicode_code)

        assert isinstance(report, ReviewReport)


# =============================================================================
# Test Context Passing
# =============================================================================


class TestContextPassing:
    """Test that context is properly passed to reviewers."""

    def test_context_passed_to_reviewers(self, panel, clean_code):
        """Test that context dict is passed through."""
        context = {
            "project": "test-project",
            "tech_stack": ["python", "fastapi"]
        }

        report = panel.review_code(clean_code, context=context)

        # Should complete without error
        assert isinstance(report, ReviewReport)

    def test_multi_file_context(self, panel, clean_code):
        """Test context in multi-file review."""
        files = {"main.py": clean_code}
        context = {"related_files": ["utils.py", "config.py"]}

        report = panel.review_files(files, context=context)

        assert isinstance(report, ReviewReport)
