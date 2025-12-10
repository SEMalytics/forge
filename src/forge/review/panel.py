"""
Review Panel - Voting System for Multi-Agent Code Review

Orchestrates 12 expert reviewers and implements voting-based
approval system with configurable threshold (default 8/12).
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from forge.review.agents import (
    APIDesignReviewer,
    ArchitectureReviewer,
    CodeStyleReviewer,
    ConcurrencyReviewer,
    DataValidationReviewer,
    DocumentationReviewer,
    ErrorHandlingReviewer,
    IntegrationReviewer,
    MaintainabilityReviewer,
    PerformanceReviewer,
    ReviewAgent,
    ReviewFinding,
    ReviewResult,
    ReviewSeverity,
    SecurityReviewer,
    TestingReviewer,
)


class ReviewVote(Enum):
    """Possible vote outcomes from a reviewer."""

    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass
class PanelDecision:
    """Final decision from the review panel."""

    approved: bool
    approval_count: int
    rejection_count: int
    abstain_count: int
    threshold: int
    total_reviewers: int
    confidence: float
    blocking_findings: List[ReviewFinding]
    summary: str

    @property
    def approval_percentage(self) -> float:
        """Calculate approval percentage."""
        voting_reviewers = self.approval_count + self.rejection_count
        if voting_reviewers == 0:
            return 0.0
        return (self.approval_count / voting_reviewers) * 100

    @property
    def met_threshold(self) -> bool:
        """Check if approval threshold was met."""
        return self.approval_count >= self.threshold


@dataclass
class ReviewReport:
    """Comprehensive review report from all agents."""

    decision: PanelDecision
    individual_results: List[ReviewResult]
    all_findings: List[ReviewFinding]
    findings_by_severity: Dict[str, List[ReviewFinding]]
    findings_by_category: Dict[str, List[ReviewFinding]]
    total_review_time_seconds: float
    reviewed_files: List[str]
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))

    def get_critical_findings(self) -> List[ReviewFinding]:
        """Get all critical severity findings."""
        return self.findings_by_severity.get(ReviewSeverity.CRITICAL.value, [])

    def get_high_findings(self) -> List[ReviewFinding]:
        """Get all high severity findings."""
        return self.findings_by_severity.get(ReviewSeverity.HIGH.value, [])

    def get_blocking_findings(self) -> List[ReviewFinding]:
        """Get findings that would block approval."""
        critical = self.get_critical_findings()
        high = self.get_high_findings()
        return critical + high

    def format_summary(self) -> str:
        """Format a human-readable summary."""
        lines = [
            "=" * 60,
            "REVIEW PANEL REPORT",
            "=" * 60,
            "",
            f"Decision: {'APPROVED' if self.decision.approved else 'REJECTED'}",
            f"Votes: {self.decision.approval_count} approve, "
            f"{self.decision.rejection_count} reject, "
            f"{self.decision.abstain_count} abstain",
            f"Threshold: {self.decision.threshold}/{self.decision.total_reviewers} required",
            f"Confidence: {self.decision.confidence:.1%}",
            "",
            "-" * 60,
            "FINDINGS SUMMARY",
            "-" * 60,
        ]

        for severity in ReviewSeverity:
            findings = self.findings_by_severity.get(severity.value, [])
            if findings:
                lines.append(f"  {severity.value.upper()}: {len(findings)}")

        lines.append("")
        lines.append(f"Total review time: {self.total_review_time_seconds:.2f}s")
        lines.append(f"Files reviewed: {len(self.reviewed_files)}")

        if self.decision.blocking_findings:
            lines.extend([
                "",
                "-" * 60,
                "BLOCKING ISSUES",
                "-" * 60,
            ])
            for finding in self.decision.blocking_findings[:10]:  # Limit to 10
                lines.append(f"  [{finding.severity.value.upper()}] {finding.category}")
                lines.append(f"    {finding.message}")
                if finding.file_path:
                    loc = finding.file_path
                    if finding.line_number:
                        loc += f":{finding.line_number}"
                    lines.append(f"    Location: {loc}")
                lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization."""
        return {
            "decision": {
                "approved": self.decision.approved,
                "approval_count": self.decision.approval_count,
                "rejection_count": self.decision.rejection_count,
                "abstain_count": self.decision.abstain_count,
                "threshold": self.decision.threshold,
                "total_reviewers": self.decision.total_reviewers,
                "confidence": self.decision.confidence,
                "approval_percentage": self.decision.approval_percentage,
                "summary": self.decision.summary,
            },
            "findings": {
                "total": len(self.all_findings),
                "by_severity": {
                    severity: len(findings)
                    for severity, findings in self.findings_by_severity.items()
                },
                "by_category": {
                    category: len(findings)
                    for category, findings in self.findings_by_category.items()
                },
            },
            "individual_results": [
                {
                    "agent": result.agent_name,
                    "expertise": result.agent_expertise,
                    "approved": result.approved,
                    "confidence": result.confidence,
                    "findings_count": len(result.findings),
                    "summary": result.summary,
                }
                for result in self.individual_results
            ],
            "metadata": {
                "timestamp": self.timestamp,
                "total_review_time_seconds": self.total_review_time_seconds,
                "reviewed_files": self.reviewed_files,
            },
        }


class ReviewPanel:
    """
    Orchestrates multi-agent code review with voting system.

    The panel consists of 12 expert reviewers, each specialized in
    a different aspect of code quality. Approval requires meeting
    a configurable threshold (default 8/12 approvals).

    Example:
        >>> panel = ReviewPanel(approval_threshold=8)
        >>> report = panel.review_code(code, file_path="main.py")
        >>> if report.decision.approved:
        ...     print("Code approved!")
        ... else:
        ...     print("Code rejected")
        ...     for finding in report.decision.blocking_findings:
        ...         print(f"  - {finding.message}")
    """

    # Default reviewers in the panel
    DEFAULT_REVIEWERS = [
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
    ]

    def __init__(
        self,
        approval_threshold: int = 8,
        reviewers: Optional[List[ReviewAgent]] = None,
        parallel: bool = True,
        max_workers: int = 4,
    ):
        """
        Initialize the review panel.

        Args:
            approval_threshold: Minimum approvals needed (default: 8)
            reviewers: Custom list of reviewers (default: all 12 experts)
            parallel: Run reviews in parallel (default: True)
            max_workers: Max parallel workers (default: 4)
        """
        if reviewers is not None:
            self.reviewers = reviewers
        else:
            self.reviewers = [cls() for cls in self.DEFAULT_REVIEWERS]

        self.total_reviewers = len(self.reviewers)

        # Validate threshold
        if approval_threshold < 1:
            raise ValueError("Approval threshold must be at least 1")
        if approval_threshold > self.total_reviewers:
            raise ValueError(
                f"Approval threshold ({approval_threshold}) cannot exceed "
                f"number of reviewers ({self.total_reviewers})"
            )

        self.approval_threshold = approval_threshold
        self.parallel = parallel
        self.max_workers = max_workers

    def review_code(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ReviewReport:
        """
        Review code with all panel members.

        Args:
            code: Source code to review
            file_path: Optional file path for context
            context: Optional additional context

        Returns:
            ReviewReport with decision and all findings
        """
        start_time = time.time()

        # Collect results from all reviewers
        if self.parallel:
            results = self._review_parallel(code, file_path, context)
        else:
            results = self._review_sequential(code, file_path, context)

        total_time = time.time() - start_time

        # Build the report
        return self._build_report(
            results=results,
            file_path=file_path,
            total_time=total_time,
        )

    def review_files(
        self,
        files: Dict[str, str],
        context: Optional[Dict[str, Any]] = None,
    ) -> ReviewReport:
        """
        Review multiple files with all panel members.

        Args:
            files: Dictionary mapping file paths to code content
            context: Optional additional context

        Returns:
            Aggregated ReviewReport for all files
        """
        start_time = time.time()
        all_results: List[ReviewResult] = []

        for file_path, code in files.items():
            file_context = context.copy() if context else {}
            file_context["current_file"] = file_path
            file_context["all_files"] = list(files.keys())

            if self.parallel:
                results = self._review_parallel(code, file_path, file_context)
            else:
                results = self._review_sequential(code, file_path, file_context)

            all_results.extend(results)

        total_time = time.time() - start_time

        # Build aggregated report
        return self._build_report(
            results=all_results,
            file_path=None,
            total_time=total_time,
            reviewed_files=list(files.keys()),
        )

    def _review_sequential(
        self,
        code: str,
        file_path: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> List[ReviewResult]:
        """Run reviews sequentially."""
        results = []
        for reviewer in self.reviewers:
            result = reviewer.review(code, file_path, context)
            results.append(result)
        return results

    def _review_parallel(
        self,
        code: str,
        file_path: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> List[ReviewResult]:
        """Run reviews in parallel using thread pool."""
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_reviewer = {
                executor.submit(reviewer.review, code, file_path, context): reviewer
                for reviewer in self.reviewers
            }

            for future in as_completed(future_to_reviewer):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # If a reviewer fails, record an abstention
                    reviewer = future_to_reviewer[future]
                    results.append(ReviewResult(
                        agent_name=reviewer.name,
                        agent_expertise=reviewer.expertise,
                        approved=False,
                        confidence=0.0,
                        findings=[],
                        summary=f"Review failed with error: {str(e)}",
                        review_time_seconds=0.0,
                    ))

        return results

    def _build_report(
        self,
        results: List[ReviewResult],
        file_path: Optional[str],
        total_time: float,
        reviewed_files: Optional[List[str]] = None,
    ) -> ReviewReport:
        """Build comprehensive review report from results."""
        if reviewed_files is None:
            reviewed_files = [file_path] if file_path else []

        # Count votes
        approvals = sum(1 for r in results if r.approved)
        rejections = sum(1 for r in results if not r.approved and r.confidence > 0)
        abstentions = sum(1 for r in results if not r.approved and r.confidence == 0)

        # Collect all findings
        all_findings: List[ReviewFinding] = []
        for result in results:
            all_findings.extend(result.findings)

        # Group findings by severity
        findings_by_severity: Dict[str, List[ReviewFinding]] = {}
        for finding in all_findings:
            severity_key = finding.severity.value
            if severity_key not in findings_by_severity:
                findings_by_severity[severity_key] = []
            findings_by_severity[severity_key].append(finding)

        # Group findings by category
        findings_by_category: Dict[str, List[ReviewFinding]] = {}
        for finding in all_findings:
            if finding.category not in findings_by_category:
                findings_by_category[finding.category] = []
            findings_by_category[finding.category].append(finding)

        # Identify blocking findings (critical and high severity)
        blocking_findings = (
            findings_by_severity.get(ReviewSeverity.CRITICAL.value, []) +
            findings_by_severity.get(ReviewSeverity.HIGH.value, [])
        )

        # Calculate overall confidence
        if results:
            avg_confidence = sum(r.confidence for r in results) / len(results)
        else:
            avg_confidence = 0.0

        # Determine approval
        approved = approvals >= self.approval_threshold

        # If approved but has critical findings, reject
        critical_count = len(findings_by_severity.get(ReviewSeverity.CRITICAL.value, []))
        if approved and critical_count > 0:
            approved = False

        # Build decision summary
        if approved:
            summary = (
                f"Code approved with {approvals}/{self.total_reviewers} votes. "
                f"Average confidence: {avg_confidence:.1%}."
            )
        else:
            reasons = []
            if approvals < self.approval_threshold:
                reasons.append(
                    f"only {approvals}/{self.approval_threshold} required approvals"
                )
            if critical_count > 0:
                reasons.append(f"{critical_count} critical issues found")
            high_count = len(findings_by_severity.get(ReviewSeverity.HIGH.value, []))
            if high_count > 0:
                reasons.append(f"{high_count} high-severity issues found")

            summary = f"Code rejected: {', '.join(reasons)}."

        decision = PanelDecision(
            approved=approved,
            approval_count=approvals,
            rejection_count=rejections,
            abstain_count=abstentions,
            threshold=self.approval_threshold,
            total_reviewers=self.total_reviewers,
            confidence=avg_confidence,
            blocking_findings=blocking_findings,
            summary=summary,
        )

        return ReviewReport(
            decision=decision,
            individual_results=results,
            all_findings=all_findings,
            findings_by_severity=findings_by_severity,
            findings_by_category=findings_by_category,
            total_review_time_seconds=total_time,
            reviewed_files=reviewed_files,
        )

    def get_reviewer_names(self) -> List[str]:
        """Get names of all reviewers in the panel."""
        return [r.name for r in self.reviewers]

    def get_reviewer_by_name(self, name: str) -> Optional[ReviewAgent]:
        """Get a specific reviewer by name."""
        for reviewer in self.reviewers:
            if reviewer.name == name:
                return reviewer
        return None

    def add_reviewer(self, reviewer: ReviewAgent) -> None:
        """Add a custom reviewer to the panel."""
        self.reviewers.append(reviewer)
        self.total_reviewers = len(self.reviewers)

    def remove_reviewer(self, name: str) -> bool:
        """Remove a reviewer by name. Returns True if removed."""
        for i, reviewer in enumerate(self.reviewers):
            if reviewer.name == name:
                self.reviewers.pop(i)
                self.total_reviewers = len(self.reviewers)
                return True
        return False

    def set_approval_threshold(self, threshold: int) -> None:
        """Update the approval threshold."""
        if threshold < 1:
            raise ValueError("Approval threshold must be at least 1")
        if threshold > self.total_reviewers:
            raise ValueError(
                f"Approval threshold ({threshold}) cannot exceed "
                f"number of reviewers ({self.total_reviewers})"
            )
        self.approval_threshold = threshold


async def review_code_async(
    panel: ReviewPanel,
    code: str,
    file_path: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> ReviewReport:
    """
    Async wrapper for code review.

    Args:
        panel: ReviewPanel instance
        code: Source code to review
        file_path: Optional file path
        context: Optional context

    Returns:
        ReviewReport from the panel
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: panel.review_code(code, file_path, context)
    )


async def review_files_async(
    panel: ReviewPanel,
    files: Dict[str, str],
    context: Optional[Dict[str, Any]] = None,
) -> ReviewReport:
    """
    Async wrapper for multi-file review.

    Args:
        panel: ReviewPanel instance
        files: Dictionary of file paths to code
        context: Optional context

    Returns:
        Aggregated ReviewReport
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: panel.review_files(files, context)
    )
