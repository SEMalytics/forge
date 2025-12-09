"""
Triage Workflow for Forge

Separates the review process into two distinct phases:
1. Finding Collection - Gather all issues without acting
2. Triage Decision - Present findings for user approval before action

This prevents over-commitment and gives users control over which
fixes to apply and in what order.
"""

import json
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from forge.layers.failure_analyzer import FixSuggestion, Priority, FailureType
from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class TriageError(ForgeError):
    """Errors during triage workflow"""
    pass


class FindingStatus(Enum):
    """Status of a finding in the triage workflow"""
    PENDING = "pending"      # Not yet reviewed
    APPROVED = "approved"    # Approved for fixing
    SKIPPED = "skipped"      # Skipped this time
    DEFERRED = "deferred"    # Deferred for later
    REJECTED = "rejected"    # Permanently rejected


class FindingCategory(Enum):
    """Categories for organizing findings"""
    CRITICAL = "critical"        # Security vulnerabilities, crashes
    FUNCTIONAL = "functional"    # Test failures, broken features
    QUALITY = "quality"          # Code quality, best practices
    PERFORMANCE = "performance"  # Performance issues
    STYLE = "style"              # Style/formatting issues


@dataclass
class TriageFinding:
    """
    A finding that needs triage decision.

    Wraps a FixSuggestion with triage metadata.
    """
    id: str
    suggestion: FixSuggestion
    category: FindingCategory
    status: FindingStatus = FindingStatus.PENDING
    user_notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    reviewed_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        """Generate a title for the finding"""
        return f"[{self.suggestion.priority.value.upper()}] {self.suggestion.root_cause[:60]}"

    @property
    def is_reviewed(self) -> bool:
        """Whether this finding has been reviewed"""
        return self.status != FindingStatus.PENDING

    @property
    def is_actionable(self) -> bool:
        """Whether this finding should be acted upon"""
        return self.status == FindingStatus.APPROVED

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'suggestion': self.suggestion.to_dict(),
            'category': self.category.value,
            'status': self.status.value,
            'user_notes': self.user_notes,
            'created_at': self.created_at,
            'reviewed_at': self.reviewed_at,
            'tags': self.tags
        }

    @classmethod
    def from_suggestion(cls, suggestion: FixSuggestion, finding_id: str) -> "TriageFinding":
        """Create a TriageFinding from a FixSuggestion"""
        # Map priority to category
        category_map = {
            Priority.CRITICAL: FindingCategory.CRITICAL,
            Priority.HIGH: FindingCategory.FUNCTIONAL,
            Priority.MEDIUM: FindingCategory.QUALITY,
            Priority.LOW: FindingCategory.STYLE,
        }

        # Override category for specific failure types
        if suggestion.failure_type == FailureType.SECURITY_VULNERABILITY:
            category = FindingCategory.CRITICAL
        elif suggestion.failure_type == FailureType.PERFORMANCE_DEGRADATION:
            category = FindingCategory.PERFORMANCE
        else:
            category = category_map.get(suggestion.priority, FindingCategory.QUALITY)

        return cls(
            id=finding_id,
            suggestion=suggestion,
            category=category
        )


@dataclass
class TriageSession:
    """
    A triage session containing findings to review.
    """
    session_id: str
    project_id: str
    findings: List[TriageFinding]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    @property
    def total_findings(self) -> int:
        return len(self.findings)

    @property
    def pending_count(self) -> int:
        return sum(1 for f in self.findings if f.status == FindingStatus.PENDING)

    @property
    def approved_count(self) -> int:
        return sum(1 for f in self.findings if f.status == FindingStatus.APPROVED)

    @property
    def skipped_count(self) -> int:
        return sum(1 for f in self.findings if f.status == FindingStatus.SKIPPED)

    @property
    def deferred_count(self) -> int:
        return sum(1 for f in self.findings if f.status == FindingStatus.DEFERRED)

    @property
    def is_complete(self) -> bool:
        return self.pending_count == 0

    def get_approved_findings(self) -> List[TriageFinding]:
        """Get all approved findings"""
        return [f for f in self.findings if f.status == FindingStatus.APPROVED]

    def get_pending_findings(self) -> List[TriageFinding]:
        """Get all pending findings"""
        return [f for f in self.findings if f.status == FindingStatus.PENDING]

    def get_deferred_findings(self) -> List[TriageFinding]:
        """Get all deferred findings"""
        return [f for f in self.findings if f.status == FindingStatus.DEFERRED]

    def get_findings_by_category(self, category: FindingCategory) -> List[TriageFinding]:
        """Get findings by category"""
        return [f for f in self.findings if f.category == category]

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'session_id': self.session_id,
            'project_id': self.project_id,
            'findings': [f.to_dict() for f in self.findings],
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'summary': {
                'total': self.total_findings,
                'pending': self.pending_count,
                'approved': self.approved_count,
                'skipped': self.skipped_count,
                'deferred': self.deferred_count
            }
        }


class TriageWorkflow:
    """
    Interactive triage workflow for reviewing findings.

    Presents findings one-by-one and collects user decisions
    before any fixes are applied.

    Features:
    - One-by-one finding presentation
    - Batch approval options
    - Category filtering
    - Deferred items tracking
    - Session persistence
    """

    def __init__(
        self,
        console: Optional[Console] = None,
        storage_dir: Optional[Path] = None,
        auto_approve_threshold: float = 0.9  # Auto-approve high-confidence findings
    ):
        """
        Initialize triage workflow.

        Args:
            console: Rich console for output
            storage_dir: Directory for storing triage sessions
            auto_approve_threshold: Confidence threshold for auto-approval (0 to disable)
        """
        self.console = console or Console()
        self.storage_dir = storage_dir or Path(".forge/triage")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.auto_approve_threshold = auto_approve_threshold

        self._current_session: Optional[TriageSession] = None

        logger.info("Initialized TriageWorkflow")

    def create_session(
        self,
        project_id: str,
        suggestions: List[FixSuggestion],
        session_id: Optional[str] = None
    ) -> TriageSession:
        """
        Create a new triage session from fix suggestions.

        Args:
            project_id: Project identifier
            suggestions: List of fix suggestions to triage
            session_id: Optional custom session ID

        Returns:
            New TriageSession
        """
        if session_id is None:
            session_id = f"triage-{project_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Convert suggestions to findings
        findings = []
        for i, suggestion in enumerate(suggestions):
            finding_id = f"{session_id}-{i:03d}"
            finding = TriageFinding.from_suggestion(suggestion, finding_id)
            findings.append(finding)

        # Sort by priority (critical first)
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }
        findings.sort(key=lambda f: priority_order.get(f.suggestion.priority, 99))

        session = TriageSession(
            session_id=session_id,
            project_id=project_id,
            findings=findings
        )

        self._current_session = session
        self._save_session(session)

        logger.info(f"Created triage session {session_id} with {len(findings)} findings")

        return session

    def load_session(self, session_id: str) -> Optional[TriageSession]:
        """Load a triage session from storage"""
        session_file = self.storage_dir / f"{session_id}.json"

        if not session_file.exists():
            logger.warning(f"Session file not found: {session_file}")
            return None

        try:
            data = json.loads(session_file.read_text())
            # Reconstruct session (simplified - would need full reconstruction in production)
            logger.info(f"Loaded triage session: {session_id}")
            return self._current_session

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None

    def _save_session(self, session: TriageSession):
        """Save session to storage"""
        session_file = self.storage_dir / f"{session.session_id}.json"

        try:
            session_file.write_text(json.dumps(session.to_dict(), indent=2))
            logger.debug(f"Saved session to {session_file}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def run_interactive_triage(
        self,
        session: Optional[TriageSession] = None,
        batch_mode: bool = False
    ) -> TriageSession:
        """
        Run interactive triage workflow.

        Presents findings one-by-one for user decision.

        Args:
            session: Triage session to process (uses current if None)
            batch_mode: If True, show all findings at once for batch decisions

        Returns:
            Updated TriageSession with user decisions
        """
        if session is None:
            session = self._current_session

        if session is None:
            raise TriageError("No triage session available")

        self._print_session_header(session)

        if batch_mode:
            self._run_batch_triage(session)
        else:
            self._run_sequential_triage(session)

        # Mark session complete
        session.completed_at = datetime.now().isoformat()
        self._save_session(session)

        self._print_session_summary(session)

        return session

    def _run_sequential_triage(self, session: TriageSession):
        """Run triage presenting one finding at a time"""
        pending = session.get_pending_findings()
        total = len(pending)

        for i, finding in enumerate(pending, 1):
            self.console.print(f"\n[bold cyan]Finding {i}/{total}[/bold cyan]\n")

            # Display finding
            self._display_finding(finding)

            # Check for auto-approval
            if (self.auto_approve_threshold > 0 and
                finding.suggestion.confidence >= self.auto_approve_threshold):
                self.console.print(
                    f"[dim]Auto-approving (confidence: {finding.suggestion.confidence:.0%})[/dim]"
                )
                finding.status = FindingStatus.APPROVED
                finding.reviewed_at = datetime.now().isoformat()
                continue

            # Get user decision
            decision = self._get_user_decision(finding)

            # Apply decision
            self._apply_decision(finding, decision)

            # Check for early exit
            if decision.get('exit'):
                self.console.print("\n[yellow]Exiting triage (remaining findings kept as pending)[/yellow]")
                break

            # Save progress after each decision
            self._save_session(session)

    def _run_batch_triage(self, session: TriageSession):
        """Run triage showing all findings for batch decisions"""
        # Display all findings
        self._display_findings_table(session.findings)

        # Batch options
        self.console.print("\n[bold]Batch Actions:[/bold]")
        self.console.print("  [cyan]a[/cyan] - Approve all")
        self.console.print("  [cyan]c[/cyan] - Approve critical only")
        self.console.print("  [cyan]h[/cyan] - Approve high priority and above")
        self.console.print("  [cyan]s[/cyan] - Skip all")
        self.console.print("  [cyan]i[/cyan] - Review individually")

        choice = Prompt.ask(
            "\nAction",
            choices=["a", "c", "h", "s", "i"],
            default="i"
        )

        if choice == "a":
            for f in session.findings:
                if f.status == FindingStatus.PENDING:
                    f.status = FindingStatus.APPROVED
                    f.reviewed_at = datetime.now().isoformat()

        elif choice == "c":
            for f in session.findings:
                if (f.status == FindingStatus.PENDING and
                    f.suggestion.priority == Priority.CRITICAL):
                    f.status = FindingStatus.APPROVED
                    f.reviewed_at = datetime.now().isoformat()

        elif choice == "h":
            for f in session.findings:
                if (f.status == FindingStatus.PENDING and
                    f.suggestion.priority in [Priority.CRITICAL, Priority.HIGH]):
                    f.status = FindingStatus.APPROVED
                    f.reviewed_at = datetime.now().isoformat()

        elif choice == "s":
            for f in session.findings:
                if f.status == FindingStatus.PENDING:
                    f.status = FindingStatus.SKIPPED
                    f.reviewed_at = datetime.now().isoformat()

        elif choice == "i":
            self._run_sequential_triage(session)

    def _display_finding(self, finding: TriageFinding):
        """Display a single finding in detail"""
        suggestion = finding.suggestion

        # Priority badge
        priority_colors = {
            Priority.CRITICAL: "red bold",
            Priority.HIGH: "yellow",
            Priority.MEDIUM: "cyan",
            Priority.LOW: "dim"
        }
        priority_color = priority_colors.get(suggestion.priority, "white")

        # Create finding panel
        content = []
        content.append(f"[{priority_color}]Priority: {suggestion.priority.value.upper()}[/{priority_color}]")
        content.append(f"Category: {finding.category.value}")
        content.append(f"Confidence: {suggestion.confidence:.0%}")
        content.append("")
        content.append(f"[bold]Root Cause:[/bold]")
        content.append(f"  {suggestion.root_cause}")
        content.append("")
        content.append(f"[bold]Suggested Fix:[/bold]")
        content.append(f"  {suggestion.suggested_fix}")

        if suggestion.explanation:
            content.append("")
            content.append(f"[bold]Explanation:[/bold]")
            content.append(f"  {suggestion.explanation}")

        if suggestion.code_changes:
            content.append("")
            content.append(f"[bold]Files to modify:[/bold]")
            for change in suggestion.code_changes[:3]:
                content.append(f"  • {change.get('file', 'unknown')}")

        self.console.print(Panel(
            "\n".join(content),
            title=f"[bold]{finding.title}[/bold]",
            border_style="blue"
        ))

    def _display_findings_table(self, findings: List[TriageFinding]):
        """Display findings in a table format"""
        table = Table(title="Findings Overview", border_style="blue")
        table.add_column("#", style="dim", width=4)
        table.add_column("Priority", width=10)
        table.add_column("Category", width=12)
        table.add_column("Root Cause", max_width=50)
        table.add_column("Confidence", width=12, justify="right")
        table.add_column("Status", width=10)

        priority_colors = {
            Priority.CRITICAL: "red",
            Priority.HIGH: "yellow",
            Priority.MEDIUM: "cyan",
            Priority.LOW: "dim"
        }

        for i, finding in enumerate(findings, 1):
            priority = finding.suggestion.priority
            color = priority_colors.get(priority, "white")

            table.add_row(
                str(i),
                f"[{color}]{priority.value}[/{color}]",
                finding.category.value,
                finding.suggestion.root_cause[:50] + "..." if len(finding.suggestion.root_cause) > 50 else finding.suggestion.root_cause,
                f"{finding.suggestion.confidence:.0%}",
                finding.status.value
            )

        self.console.print(table)

    def _get_user_decision(self, finding: TriageFinding) -> Dict[str, Any]:
        """Get user decision for a finding"""
        self.console.print("\n[bold]Actions:[/bold]")
        self.console.print("  [green]y[/green] - Approve (apply this fix)")
        self.console.print("  [yellow]s[/yellow] - Skip (don't fix now)")
        self.console.print("  [cyan]d[/cyan] - Defer (review later)")
        self.console.print("  [red]r[/red] - Reject (never fix)")
        self.console.print("  [dim]n[/dim] - Add note")
        self.console.print("  [dim]?[/dim] - Show more details")
        self.console.print("  [dim]q[/dim] - Exit triage")

        while True:
            choice = Prompt.ask(
                "\nDecision",
                choices=["y", "s", "d", "r", "n", "?", "q"],
                default="y"
            )

            if choice == "?":
                self._show_finding_details(finding)
                continue

            if choice == "n":
                note = Prompt.ask("Note")
                finding.user_notes = note
                self.console.print(f"[dim]Note added[/dim]")
                continue

            if choice == "q":
                return {'status': None, 'exit': True}

            status_map = {
                "y": FindingStatus.APPROVED,
                "s": FindingStatus.SKIPPED,
                "d": FindingStatus.DEFERRED,
                "r": FindingStatus.REJECTED
            }

            return {'status': status_map[choice], 'exit': False}

    def _apply_decision(self, finding: TriageFinding, decision: Dict[str, Any]):
        """Apply user decision to a finding"""
        if decision.get('status'):
            finding.status = decision['status']
            finding.reviewed_at = datetime.now().isoformat()

            status_messages = {
                FindingStatus.APPROVED: "[green]✓ Approved[/green]",
                FindingStatus.SKIPPED: "[yellow]→ Skipped[/yellow]",
                FindingStatus.DEFERRED: "[cyan]⏸ Deferred[/cyan]",
                FindingStatus.REJECTED: "[red]✗ Rejected[/red]"
            }

            self.console.print(status_messages.get(finding.status, ""))

    def _show_finding_details(self, finding: TriageFinding):
        """Show expanded details for a finding"""
        suggestion = finding.suggestion

        self.console.print("\n[bold]Full Details:[/bold]\n")

        # Failure type
        self.console.print(f"Failure Type: {suggestion.failure_type.value}")

        # All code changes
        if suggestion.code_changes:
            self.console.print("\n[bold]Code Changes:[/bold]")
            for change in suggestion.code_changes:
                self.console.print(f"\nFile: {change.get('file', 'unknown')}")
                if 'old' in change and 'new' in change:
                    self.console.print("[red]- " + change['old'][:100] + "[/red]")
                    self.console.print("[green]+ " + change['new'][:100] + "[/green]")

        # Relevant patterns
        if suggestion.relevant_patterns:
            self.console.print("\n[bold]Relevant Patterns:[/bold]")
            for pattern in suggestion.relevant_patterns:
                self.console.print(f"  • {pattern}")

        self.console.print()

    def _print_session_header(self, session: TriageSession):
        """Print session header"""
        self.console.print()
        self.console.print(Panel(
            f"[bold]Project:[/bold] {session.project_id}\n"
            f"[bold]Session:[/bold] {session.session_id}\n"
            f"[bold]Findings:[/bold] {session.total_findings} total, {session.pending_count} pending",
            title="[bold cyan]⚖ Triage Session[/bold cyan]",
            border_style="cyan"
        ))

    def _print_session_summary(self, session: TriageSession):
        """Print session summary after completion"""
        self.console.print()

        summary_table = Table(title="Triage Summary", border_style="green")
        summary_table.add_column("Status", style="bold")
        summary_table.add_column("Count", justify="right")

        summary_table.add_row("Approved", f"[green]{session.approved_count}[/green]")
        summary_table.add_row("Skipped", f"[yellow]{session.skipped_count}[/yellow]")
        summary_table.add_row("Deferred", f"[cyan]{session.deferred_count}[/cyan]")
        summary_table.add_row("Pending", f"[dim]{session.pending_count}[/dim]")
        summary_table.add_row("Total", str(session.total_findings))

        self.console.print(summary_table)

        if session.approved_count > 0:
            self.console.print(
                f"\n[green]✓ {session.approved_count} fixes ready to apply[/green]"
            )
            self.console.print(
                "[dim]Run 'forge fix --session {session.session_id}' to apply approved fixes[/dim]"
            )

        if session.deferred_count > 0:
            self.console.print(
                f"\n[cyan]⏸ {session.deferred_count} findings deferred for later review[/cyan]"
            )

    def get_approved_suggestions(
        self,
        session: Optional[TriageSession] = None
    ) -> List[FixSuggestion]:
        """
        Get approved suggestions ready for fixing.

        Args:
            session: Triage session (uses current if None)

        Returns:
            List of approved FixSuggestions
        """
        if session is None:
            session = self._current_session

        if session is None:
            return []

        return [f.suggestion for f in session.get_approved_findings()]

    def auto_triage(
        self,
        session: Optional[TriageSession] = None,
        approve_critical: bool = True,
        approve_high: bool = False,
        min_confidence: float = 0.8
    ) -> TriageSession:
        """
        Automatically triage findings based on rules.

        Args:
            session: Triage session (uses current if None)
            approve_critical: Auto-approve critical priority findings
            approve_high: Auto-approve high priority findings
            min_confidence: Minimum confidence for auto-approval

        Returns:
            Updated TriageSession
        """
        if session is None:
            session = self._current_session

        if session is None:
            raise TriageError("No triage session available")

        for finding in session.get_pending_findings():
            should_approve = False

            # Check priority-based rules
            if approve_critical and finding.suggestion.priority == Priority.CRITICAL:
                should_approve = True
            elif approve_high and finding.suggestion.priority == Priority.HIGH:
                should_approve = True

            # Check confidence threshold
            if should_approve and finding.suggestion.confidence >= min_confidence:
                finding.status = FindingStatus.APPROVED
                finding.reviewed_at = datetime.now().isoformat()
                finding.user_notes = f"Auto-approved (confidence: {finding.suggestion.confidence:.0%})"

        self._save_session(session)
        return session

    def list_sessions(self, project_id: Optional[str] = None) -> List[Dict]:
        """List available triage sessions"""
        sessions = []

        for session_file in self.storage_dir.glob("triage-*.json"):
            try:
                data = json.loads(session_file.read_text())
                if project_id is None or data.get('project_id') == project_id:
                    sessions.append({
                        'session_id': data['session_id'],
                        'project_id': data['project_id'],
                        'created_at': data['created_at'],
                        'summary': data.get('summary', {})
                    })
            except Exception as e:
                logger.warning(f"Failed to read session file {session_file}: {e}")

        return sorted(sessions, key=lambda x: x['created_at'], reverse=True)

    def close(self):
        """Close resources and save current session"""
        if self._current_session:
            self._save_session(self._current_session)
