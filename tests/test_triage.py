"""
Tests for Triage Workflow

Tests the triage system including:
- Session creation and management
- Finding status transitions
- Batch and sequential triage modes
- Auto-triage functionality
- Session persistence
"""

import pytest
from pathlib import Path
import tempfile
import json
from unittest.mock import Mock, patch
from datetime import datetime

from forge.layers.triage import (
    TriageWorkflow,
    TriageSession,
    TriageFinding,
    TriageError,
    FindingStatus,
    FindingCategory
)
from forge.layers.failure_analyzer import (
    FixSuggestion,
    FailureType,
    Priority
)


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory for triage sessions."""
    storage_dir = tmp_path / "triage"
    storage_dir.mkdir()
    return storage_dir


@pytest.fixture
def mock_console():
    """Create mock console for testing."""
    console = Mock()
    console.print = Mock()
    console.status = Mock()
    return console


@pytest.fixture
def sample_suggestions():
    """Create sample fix suggestions for testing."""
    return [
        FixSuggestion(
            failure_type=FailureType.IMPORT_ERROR,
            root_cause="Missing module 'requests'",
            suggested_fix="Install requests package",
            code_changes=[{'file': 'requirements.txt', 'old': '', 'new': 'requests==2.28.0'}],
            relevant_patterns=["dependency-management.md"],
            priority=Priority.HIGH,
            confidence=0.9,
            explanation="Module not found in dependencies"
        ),
        FixSuggestion(
            failure_type=FailureType.ASSERTION_ERROR,
            root_cause="Test expects 6 but got 5",
            suggested_fix="Fix add function logic",
            code_changes=[{'file': 'calculator.py', 'old': 'return a + b', 'new': 'return a + b + 1'}],
            relevant_patterns=["testing.md"],
            priority=Priority.MEDIUM,
            confidence=0.7,
            explanation="Arithmetic logic error"
        ),
        FixSuggestion(
            failure_type=FailureType.SECURITY_VULNERABILITY,
            root_cause="Hardcoded password in config",
            suggested_fix="Move to environment variable",
            code_changes=[{'file': 'config.py', 'old': 'pass = "secret"', 'new': 'pass = os.getenv("PASSWORD")'}],
            relevant_patterns=["security.md"],
            priority=Priority.CRITICAL,
            confidence=0.95,
            explanation="Security best practice violation"
        )
    ]


@pytest.fixture
def workflow(temp_storage, mock_console):
    """Create TriageWorkflow instance for testing."""
    return TriageWorkflow(
        console=mock_console,
        storage_dir=temp_storage,
        auto_approve_threshold=0.0  # Disable auto-approve for tests
    )


class TestTriageFinding:
    """Tests for TriageFinding dataclass."""

    def test_from_suggestion_high_priority(self, sample_suggestions):
        """Test creating finding from high priority suggestion."""
        suggestion = sample_suggestions[0]
        finding = TriageFinding.from_suggestion(suggestion, "finding-001")

        assert finding.id == "finding-001"
        assert finding.suggestion == suggestion
        assert finding.category == FindingCategory.FUNCTIONAL
        assert finding.status == FindingStatus.PENDING
        assert finding.is_reviewed is False
        assert finding.is_actionable is False

    def test_from_suggestion_critical_priority(self, sample_suggestions):
        """Test creating finding from critical priority suggestion."""
        suggestion = sample_suggestions[2]
        finding = TriageFinding.from_suggestion(suggestion, "finding-002")

        assert finding.category == FindingCategory.CRITICAL
        assert finding.suggestion.priority == Priority.CRITICAL

    def test_from_suggestion_security_vulnerability(self, sample_suggestions):
        """Test that security vulnerabilities get CRITICAL category."""
        suggestion = sample_suggestions[2]
        finding = TriageFinding.from_suggestion(suggestion, "finding-003")

        # Security vulnerabilities should be categorized as critical
        assert finding.category == FindingCategory.CRITICAL

    def test_title_property(self, sample_suggestions):
        """Test finding title generation."""
        suggestion = sample_suggestions[0]
        finding = TriageFinding.from_suggestion(suggestion, "finding-001")

        assert "[HIGH]" in finding.title
        assert "Missing module" in finding.title

    def test_is_reviewed_after_approval(self, sample_suggestions):
        """Test is_reviewed after status change."""
        finding = TriageFinding.from_suggestion(sample_suggestions[0], "finding-001")
        assert finding.is_reviewed is False

        finding.status = FindingStatus.APPROVED
        assert finding.is_reviewed is True

    def test_is_actionable_when_approved(self, sample_suggestions):
        """Test is_actionable property."""
        finding = TriageFinding.from_suggestion(sample_suggestions[0], "finding-001")

        finding.status = FindingStatus.APPROVED
        assert finding.is_actionable is True

        finding.status = FindingStatus.SKIPPED
        assert finding.is_actionable is False

    def test_to_dict(self, sample_suggestions):
        """Test serialization to dictionary."""
        finding = TriageFinding.from_suggestion(sample_suggestions[0], "finding-001")
        finding.user_notes = "Review later"
        finding.tags = ["urgent", "dependency"]

        data = finding.to_dict()

        assert data['id'] == "finding-001"
        assert data['status'] == "pending"
        assert data['user_notes'] == "Review later"
        assert data['tags'] == ["urgent", "dependency"]
        assert 'suggestion' in data
        assert 'created_at' in data


class TestTriageSession:
    """Tests for TriageSession dataclass."""

    def test_create_session(self, sample_suggestions):
        """Test creating a triage session."""
        findings = [
            TriageFinding.from_suggestion(s, f"finding-{i}")
            for i, s in enumerate(sample_suggestions)
        ]

        session = TriageSession(
            session_id="test-session",
            project_id="test-project",
            findings=findings
        )

        assert session.session_id == "test-session"
        assert session.total_findings == 3
        assert session.pending_count == 3
        assert session.approved_count == 0
        assert session.is_complete is False

    def test_get_approved_findings(self, sample_suggestions):
        """Test getting approved findings."""
        findings = [
            TriageFinding.from_suggestion(s, f"finding-{i}")
            for i, s in enumerate(sample_suggestions)
        ]
        findings[0].status = FindingStatus.APPROVED

        session = TriageSession(
            session_id="test-session",
            project_id="test-project",
            findings=findings
        )

        approved = session.get_approved_findings()
        assert len(approved) == 1
        assert approved[0].id == "finding-0"

    def test_get_pending_findings(self, sample_suggestions):
        """Test getting pending findings."""
        findings = [
            TriageFinding.from_suggestion(s, f"finding-{i}")
            for i, s in enumerate(sample_suggestions)
        ]
        findings[0].status = FindingStatus.APPROVED

        session = TriageSession(
            session_id="test-session",
            project_id="test-project",
            findings=findings
        )

        pending = session.get_pending_findings()
        assert len(pending) == 2

    def test_get_deferred_findings(self, sample_suggestions):
        """Test getting deferred findings."""
        findings = [
            TriageFinding.from_suggestion(s, f"finding-{i}")
            for i, s in enumerate(sample_suggestions)
        ]
        findings[1].status = FindingStatus.DEFERRED

        session = TriageSession(
            session_id="test-session",
            project_id="test-project",
            findings=findings
        )

        deferred = session.get_deferred_findings()
        assert len(deferred) == 1
        assert deferred[0].id == "finding-1"

    def test_is_complete(self, sample_suggestions):
        """Test session completion status."""
        findings = [
            TriageFinding.from_suggestion(s, f"finding-{i}")
            for i, s in enumerate(sample_suggestions)
        ]

        session = TriageSession(
            session_id="test-session",
            project_id="test-project",
            findings=findings
        )

        assert session.is_complete is False

        # Mark all as reviewed
        for f in findings:
            f.status = FindingStatus.APPROVED

        assert session.is_complete is True

    def test_to_dict(self, sample_suggestions):
        """Test session serialization."""
        findings = [
            TriageFinding.from_suggestion(s, f"finding-{i}")
            for i, s in enumerate(sample_suggestions)
        ]
        findings[0].status = FindingStatus.APPROVED

        session = TriageSession(
            session_id="test-session",
            project_id="test-project",
            findings=findings
        )

        data = session.to_dict()

        assert data['session_id'] == "test-session"
        assert data['project_id'] == "test-project"
        assert len(data['findings']) == 3
        assert data['summary']['total'] == 3
        assert data['summary']['approved'] == 1
        assert data['summary']['pending'] == 2


class TestTriageWorkflow:
    """Tests for TriageWorkflow class."""

    def test_initialization(self, temp_storage, mock_console):
        """Test workflow initialization."""
        workflow = TriageWorkflow(
            console=mock_console,
            storage_dir=temp_storage
        )

        assert workflow.console == mock_console
        assert workflow.storage_dir == temp_storage
        assert workflow._current_session is None

    def test_create_session(self, workflow, sample_suggestions):
        """Test creating a new triage session."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=sample_suggestions
        )

        assert session is not None
        assert session.project_id == "test-project"
        assert session.total_findings == 3
        assert workflow._current_session == session

    def test_create_session_with_custom_id(self, workflow, sample_suggestions):
        """Test creating session with custom ID."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=sample_suggestions,
            session_id="custom-session-id"
        )

        assert session.session_id == "custom-session-id"

    def test_session_sorted_by_priority(self, workflow, sample_suggestions):
        """Test that findings are sorted by priority."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=sample_suggestions
        )

        # First finding should be CRITICAL (security)
        assert session.findings[0].suggestion.priority == Priority.CRITICAL
        # Second should be HIGH (import error)
        assert session.findings[1].suggestion.priority == Priority.HIGH
        # Third should be MEDIUM (assertion error)
        assert session.findings[2].suggestion.priority == Priority.MEDIUM

    def test_session_persisted(self, workflow, sample_suggestions, temp_storage):
        """Test that session is saved to storage."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=sample_suggestions
        )

        # Check file exists
        session_file = temp_storage / f"{session.session_id}.json"
        assert session_file.exists()

        # Verify content
        data = json.loads(session_file.read_text())
        assert data['project_id'] == "test-project"
        assert len(data['findings']) == 3

    def test_get_approved_suggestions(self, workflow, sample_suggestions):
        """Test getting approved suggestions."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=sample_suggestions
        )

        # Approve first finding
        session.findings[0].status = FindingStatus.APPROVED

        approved = workflow.get_approved_suggestions(session)

        assert len(approved) == 1
        assert approved[0] == session.findings[0].suggestion

    def test_auto_triage_critical(self, workflow, sample_suggestions):
        """Test auto-triage with critical priority."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=sample_suggestions
        )

        # Auto-approve critical only
        session = workflow.auto_triage(
            session,
            approve_critical=True,
            approve_high=False,
            min_confidence=0.0
        )

        # Only critical should be approved
        assert session.approved_count == 1
        assert session.findings[0].status == FindingStatus.APPROVED  # CRITICAL
        assert session.findings[1].status == FindingStatus.PENDING   # HIGH
        assert session.findings[2].status == FindingStatus.PENDING   # MEDIUM

    def test_auto_triage_critical_and_high(self, workflow, sample_suggestions):
        """Test auto-triage with critical and high priority."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=sample_suggestions
        )

        session = workflow.auto_triage(
            session,
            approve_critical=True,
            approve_high=True,
            min_confidence=0.0
        )

        # Critical and high should be approved
        assert session.approved_count == 2
        approved_priorities = [f.suggestion.priority for f in session.get_approved_findings()]
        assert Priority.CRITICAL in approved_priorities
        assert Priority.HIGH in approved_priorities

    def test_auto_triage_with_confidence_threshold(self, workflow, sample_suggestions):
        """Test auto-triage respects confidence threshold."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=sample_suggestions
        )

        # High confidence threshold
        session = workflow.auto_triage(
            session,
            approve_critical=True,
            approve_high=True,
            min_confidence=0.92  # Only security (0.95) meets this
        )

        # Only high-confidence critical should be approved
        assert session.approved_count == 1

    def test_auto_triage_no_session_raises_error(self, workflow):
        """Test auto_triage raises error when no session."""
        with pytest.raises(TriageError):
            workflow.auto_triage(approve_critical=True)

    def test_list_sessions(self, workflow, sample_suggestions, temp_storage):
        """Test listing sessions."""
        # Create multiple sessions
        workflow.create_session("project-1", sample_suggestions[:1])
        workflow.create_session("project-2", sample_suggestions[1:])

        # List all
        sessions = workflow.list_sessions()
        assert len(sessions) == 2

        # List by project
        project_1_sessions = workflow.list_sessions(project_id="project-1")
        assert len(project_1_sessions) == 1
        assert project_1_sessions[0]['project_id'] == "project-1"

    def test_run_interactive_triage_no_session_raises_error(self, workflow):
        """Test interactive triage raises error when no session."""
        with pytest.raises(TriageError):
            workflow.run_interactive_triage()


class TestFindingCategories:
    """Tests for finding category assignment."""

    def test_security_vulnerability_is_critical(self):
        """Test security vulnerabilities are categorized as critical."""
        suggestion = FixSuggestion(
            failure_type=FailureType.SECURITY_VULNERABILITY,
            root_cause="SQL injection vulnerability",
            suggested_fix="Use parameterized queries",
            code_changes=[],
            relevant_patterns=[],
            priority=Priority.HIGH,  # Even if priority is HIGH
            confidence=0.9,
            explanation="Security issue"
        )

        finding = TriageFinding.from_suggestion(suggestion, "test")
        assert finding.category == FindingCategory.CRITICAL

    def test_performance_degradation_is_performance(self):
        """Test performance issues are categorized correctly."""
        suggestion = FixSuggestion(
            failure_type=FailureType.PERFORMANCE_DEGRADATION,
            root_cause="Slow query",
            suggested_fix="Add index",
            code_changes=[],
            relevant_patterns=[],
            priority=Priority.MEDIUM,
            confidence=0.8,
            explanation="Performance issue"
        )

        finding = TriageFinding.from_suggestion(suggestion, "test")
        assert finding.category == FindingCategory.PERFORMANCE

    def test_critical_priority_is_critical_category(self):
        """Test critical priority maps to critical category."""
        suggestion = FixSuggestion(
            failure_type=FailureType.SYNTAX_ERROR,
            root_cause="Syntax error",
            suggested_fix="Fix syntax",
            code_changes=[],
            relevant_patterns=[],
            priority=Priority.CRITICAL,
            confidence=0.95,
            explanation="Parse error"
        )

        finding = TriageFinding.from_suggestion(suggestion, "test")
        assert finding.category == FindingCategory.CRITICAL

    def test_low_priority_is_style_category(self):
        """Test low priority maps to style category."""
        suggestion = FixSuggestion(
            failure_type=FailureType.ASSERTION_ERROR,
            root_cause="Minor style issue",
            suggested_fix="Fix formatting",
            code_changes=[],
            relevant_patterns=[],
            priority=Priority.LOW,
            confidence=0.6,
            explanation="Style issue"
        )

        finding = TriageFinding.from_suggestion(suggestion, "test")
        assert finding.category == FindingCategory.STYLE


class TestSessionPersistence:
    """Tests for session persistence and loading."""

    def test_save_and_load_session(self, workflow, sample_suggestions, temp_storage):
        """Test saving and loading session maintains data."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=sample_suggestions,
            session_id="persist-test"
        )

        # Modify session
        session.findings[0].status = FindingStatus.APPROVED
        session.findings[0].user_notes = "Looks good"
        workflow._save_session(session)

        # Verify file content
        session_file = temp_storage / "persist-test.json"
        data = json.loads(session_file.read_text())

        assert data['findings'][0]['status'] == "approved"
        assert data['findings'][0]['user_notes'] == "Looks good"

    def test_list_sessions_returns_metadata(self, workflow, sample_suggestions):
        """Test list_sessions returns proper metadata."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=sample_suggestions
        )
        session.findings[0].status = FindingStatus.APPROVED
        workflow._save_session(session)

        sessions = workflow.list_sessions()

        assert len(sessions) == 1
        assert sessions[0]['project_id'] == "test-project"
        assert sessions[0]['summary']['total'] == 3
        assert sessions[0]['summary']['approved'] == 1


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_suggestions_list(self, workflow):
        """Test creating session with no suggestions."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=[]
        )

        assert session.total_findings == 0
        assert session.is_complete is True  # No pending = complete

    def test_single_suggestion(self, workflow, sample_suggestions):
        """Test with single suggestion."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=[sample_suggestions[0]]
        )

        assert session.total_findings == 1
        assert session.pending_count == 1

    def test_close_saves_current_session(self, workflow, sample_suggestions, temp_storage):
        """Test close() saves current session."""
        session = workflow.create_session(
            project_id="test-project",
            suggestions=sample_suggestions
        )
        session.findings[0].status = FindingStatus.APPROVED

        workflow.close()

        # Verify session was saved
        session_file = temp_storage / f"{session.session_id}.json"
        data = json.loads(session_file.read_text())
        assert data['findings'][0]['status'] == "approved"

    def test_workflow_with_auto_approve_threshold(self, temp_storage, mock_console, sample_suggestions):
        """Test workflow respects auto_approve_threshold."""
        workflow = TriageWorkflow(
            console=mock_console,
            storage_dir=temp_storage,
            auto_approve_threshold=0.92
        )

        session = workflow.create_session(
            project_id="test-project",
            suggestions=sample_suggestions
        )

        # High confidence suggestion (0.95) should be auto-approvable
        # when running through sequential triage
        assert session.findings[0].suggestion.confidence == 0.95  # Security

    def test_finding_status_transitions(self, sample_suggestions):
        """Test valid status transitions."""
        finding = TriageFinding.from_suggestion(sample_suggestions[0], "test")

        # PENDING -> APPROVED
        finding.status = FindingStatus.APPROVED
        assert finding.status == FindingStatus.APPROVED

        # Can transition to other states
        finding.status = FindingStatus.DEFERRED
        assert finding.status == FindingStatus.DEFERRED

        finding.status = FindingStatus.REJECTED
        assert finding.status == FindingStatus.REJECTED
