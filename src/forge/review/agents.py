"""
Review Agents for Multi-Agent Code Review

Implements 12 specialized expert reviewers that evaluate code
from different perspectives.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class ReviewSeverity(Enum):
    """Severity levels for review findings."""
    CRITICAL = "critical"    # Must fix before approval
    HIGH = "high"            # Should fix, blocks approval
    MEDIUM = "medium"        # Should fix, doesn't block
    LOW = "low"              # Nice to have
    INFO = "info"            # Informational only


@dataclass
class ReviewFinding:
    """
    A single finding from a review.

    Attributes:
        severity: Severity level
        category: Category of the finding
        message: Description of the issue
        file_path: Optional file path
        line_number: Optional line number
        suggestion: Optional fix suggestion
        code_snippet: Optional relevant code
    """
    severity: ReviewSeverity
    category: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity.value,
            "category": self.category,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "suggestion": self.suggestion,
            "code_snippet": self.code_snippet
        }


@dataclass
class ReviewResult:
    """
    Result of a single agent's review.

    Attributes:
        agent_name: Name of the reviewing agent
        agent_expertise: Area of expertise
        approved: Whether the agent approves the code
        confidence: Confidence in the review (0-1)
        findings: List of findings
        summary: Brief summary of the review
        review_time_seconds: Time taken to review
        metadata: Additional metadata
    """
    agent_name: str
    agent_expertise: str
    approved: bool
    confidence: float
    findings: List[ReviewFinding]
    summary: str
    review_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def critical_count(self) -> int:
        """Count of critical findings."""
        return sum(1 for f in self.findings if f.severity == ReviewSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        """Count of high severity findings."""
        return sum(1 for f in self.findings if f.severity == ReviewSeverity.HIGH)

    @property
    def blocking_count(self) -> int:
        """Count of blocking findings (critical + high)."""
        return self.critical_count + self.high_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "agent_expertise": self.agent_expertise,
            "approved": self.approved,
            "confidence": self.confidence,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
            "review_time_seconds": self.review_time_seconds,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "blocking_count": self.blocking_count
        }


class ReviewAgent(ABC):
    """
    Base class for review agents.

    Each agent specializes in a particular aspect of code review
    and provides findings and an approval decision.
    """

    def __init__(self, name: str, expertise: str):
        """
        Initialize review agent.

        Args:
            name: Agent name
            expertise: Area of expertise
        """
        self.name = name
        self.expertise = expertise
        self._patterns: Dict[str, List[Tuple[str, ReviewSeverity, str]]] = {}

    @abstractmethod
    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """
        Review code and return findings.

        Args:
            code: Source code to review
            file_path: Optional file path for context
            context: Optional additional context

        Returns:
            ReviewResult with findings and approval decision
        """
        pass

    def _check_patterns(
        self,
        code: str,
        file_path: Optional[str] = None
    ) -> List[ReviewFinding]:
        """
        Check code against registered patterns.

        Args:
            code: Source code
            file_path: Optional file path

        Returns:
            List of findings
        """
        findings = []
        lines = code.split('\n')

        for category, patterns in self._patterns.items():
            for pattern, severity, message in patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append(ReviewFinding(
                            severity=severity,
                            category=category,
                            message=message,
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip()
                        ))

        return findings

    def _calculate_approval(
        self,
        findings: List[ReviewFinding],
        max_critical: int = 0,
        max_high: int = 0
    ) -> Tuple[bool, float]:
        """
        Calculate approval based on findings.

        Args:
            findings: List of findings
            max_critical: Maximum allowed critical findings
            max_high: Maximum allowed high findings

        Returns:
            Tuple of (approved, confidence)
        """
        critical = sum(1 for f in findings if f.severity == ReviewSeverity.CRITICAL)
        high = sum(1 for f in findings if f.severity == ReviewSeverity.HIGH)
        medium = sum(1 for f in findings if f.severity == ReviewSeverity.MEDIUM)

        approved = critical <= max_critical and high <= max_high

        # Calculate confidence based on finding counts
        if not findings:
            confidence = 0.95  # High confidence when no issues found
        else:
            penalty = critical * 0.3 + high * 0.15 + medium * 0.05
            confidence = max(0.1, min(0.95, 0.9 - penalty))

        return approved, confidence


# =============================================================================
# Expert Reviewer Implementations
# =============================================================================

class SecurityReviewer(ReviewAgent):
    """
    Security Expert Reviewer

    Checks for OWASP vulnerabilities, injection attacks, authentication
    issues, and other security concerns.
    """

    def __init__(self):
        super().__init__("SecurityExpert", "Security & Vulnerability Analysis")
        self._patterns = {
            "injection": [
                (r"eval\s*\(", ReviewSeverity.CRITICAL, "Potential code injection via eval()"),
                (r"exec\s*\(", ReviewSeverity.CRITICAL, "Potential code injection via exec()"),
                (r"subprocess\..*shell\s*=\s*True", ReviewSeverity.HIGH, "Shell injection risk with shell=True"),
                (r"os\.system\s*\(", ReviewSeverity.HIGH, "Potential command injection via os.system()"),
                (r"__import__\s*\(", ReviewSeverity.MEDIUM, "Dynamic import may allow code injection"),
            ],
            "secrets": [
                (r"(password|secret|api_key|apikey|token)\s*=\s*['\"][^'\"]+['\"]", ReviewSeverity.CRITICAL, "Hardcoded secret detected"),
                (r"(aws_access_key|aws_secret)", ReviewSeverity.CRITICAL, "AWS credentials in code"),
                (r"-----BEGIN.*PRIVATE KEY-----", ReviewSeverity.CRITICAL, "Private key in code"),
            ],
            "sql": [
                (r"execute\s*\(\s*['\"].*%s", ReviewSeverity.HIGH, "Potential SQL injection with string formatting"),
                (r"f['\"].*SELECT.*{", ReviewSeverity.HIGH, "Potential SQL injection with f-string"),
                (r"\.format\(.*\).*(?:SELECT|INSERT|UPDATE|DELETE)", ReviewSeverity.HIGH, "Potential SQL injection with .format()"),
            ],
            "crypto": [
                (r"md5\s*\(", ReviewSeverity.MEDIUM, "MD5 is cryptographically weak"),
                (r"sha1\s*\(", ReviewSeverity.MEDIUM, "SHA1 is cryptographically weak"),
                (r"random\.(random|randint|choice)", ReviewSeverity.MEDIUM, "Use secrets module for security-sensitive randomness"),
            ],
            "auth": [
                (r"verify\s*=\s*False", ReviewSeverity.HIGH, "SSL verification disabled"),
                (r"CORS\(.*\*.*\)", ReviewSeverity.MEDIUM, "Overly permissive CORS configuration"),
            ]
        }

    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Review code for security issues."""
        import time
        start = time.perf_counter()

        findings = self._check_patterns(code, file_path)

        # Additional security checks
        if "pickle.load" in code or "pickle.loads" in code:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.HIGH,
                category="deserialization",
                message="Unsafe deserialization with pickle - can execute arbitrary code",
                file_path=file_path
            ))

        if "yaml.load(" in code and "Loader=" not in code:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.HIGH,
                category="deserialization",
                message="Unsafe YAML loading - use yaml.safe_load() or specify Loader",
                file_path=file_path
            ))

        approved, confidence = self._calculate_approval(findings)
        duration = time.perf_counter() - start

        return ReviewResult(
            agent_name=self.name,
            agent_expertise=self.expertise,
            approved=approved,
            confidence=confidence,
            findings=findings,
            summary=self._generate_summary(findings),
            review_time_seconds=duration
        )

    def _generate_summary(self, findings: List[ReviewFinding]) -> str:
        """Generate review summary."""
        if not findings:
            return "No security issues detected."

        critical = sum(1 for f in findings if f.severity == ReviewSeverity.CRITICAL)
        high = sum(1 for f in findings if f.severity == ReviewSeverity.HIGH)

        parts = []
        if critical:
            parts.append(f"{critical} critical")
        if high:
            parts.append(f"{high} high severity")

        return f"Found {', '.join(parts)} security issues." if parts else f"Found {len(findings)} security concerns."


class PerformanceReviewer(ReviewAgent):
    """
    Performance Expert Reviewer

    Checks for performance issues, algorithmic complexity,
    and optimization opportunities.
    """

    def __init__(self):
        super().__init__("PerformanceExpert", "Performance & Optimization")
        self._patterns = {
            "complexity": [
                (r"for.*for.*for", ReviewSeverity.MEDIUM, "Triple nested loop - O(n^3) complexity"),
                (r"while.*while", ReviewSeverity.MEDIUM, "Nested while loops may indicate performance issue"),
            ],
            "inefficiency": [
                (r"\+\s*=.*\+.*in\s+.*loop", ReviewSeverity.MEDIUM, "String concatenation in loop - use join()"),
                (r"list\(.*\).*\[0\]", ReviewSeverity.LOW, "Consider using next(iter()) instead of list()[0]"),
                (r"\.append\(.*\).*for.*in", ReviewSeverity.LOW, "Consider list comprehension instead of append in loop"),
            ],
            "memory": [
                (r"range\(\d{6,}\)", ReviewSeverity.MEDIUM, "Large range may consume significant memory"),
                (r"\*\s*\d{6,}", ReviewSeverity.MEDIUM, "Large list multiplication may consume significant memory"),
            ]
        }

    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Review code for performance issues."""
        import time
        start = time.perf_counter()

        findings = self._check_patterns(code, file_path)

        # Check for global variable usage in hot paths
        if re.search(r"global\s+\w+", code):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category="globals",
                message="Global variable usage may impact performance",
                file_path=file_path
            ))

        # Check for synchronous I/O in async context
        if "async def" in code and ("open(" in code or "requests." in code):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.MEDIUM,
                category="async",
                message="Synchronous I/O in async function blocks event loop",
                file_path=file_path,
                suggestion="Use aiofiles for file I/O or httpx/aiohttp for HTTP"
            ))

        approved, confidence = self._calculate_approval(findings, max_high=2)
        duration = time.perf_counter() - start

        return ReviewResult(
            agent_name=self.name,
            agent_expertise=self.expertise,
            approved=approved,
            confidence=confidence,
            findings=findings,
            summary=self._generate_summary(findings),
            review_time_seconds=duration
        )

    def _generate_summary(self, findings: List[ReviewFinding]) -> str:
        """Generate review summary."""
        if not findings:
            return "No significant performance issues detected."
        return f"Found {len(findings)} performance concerns to address."


class ArchitectureReviewer(ReviewAgent):
    """
    Architecture Expert Reviewer

    Evaluates code architecture, SOLID principles,
    design patterns, and structural concerns.
    """

    def __init__(self):
        super().__init__("ArchitectureExpert", "Architecture & Design Patterns")
        self._patterns = {
            "coupling": [
                (r"from\s+\.\.\.\.", ReviewSeverity.MEDIUM, "Deep relative imports indicate tight coupling"),
            ],
            "god_class": [
                (r"class\s+\w+.*:.*\n(?:.*\n){500,}", ReviewSeverity.HIGH, "Very large class - consider splitting"),
            ]
        }

    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Review code for architectural issues."""
        import time
        start = time.perf_counter()

        findings = self._check_patterns(code, file_path)

        # Count methods in classes
        class_matches = re.findall(r"class\s+(\w+)", code)
        for class_name in class_matches:
            # Find class body and count methods
            pattern = rf"class\s+{class_name}.*?(?=\nclass\s|\Z)"
            match = re.search(pattern, code, re.DOTALL)
            if match:
                class_body = match.group()
                method_count = len(re.findall(r"\n\s+def\s+", class_body))
                if method_count > 20:
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.MEDIUM,
                        category="god_class",
                        message=f"Class '{class_name}' has {method_count} methods - consider splitting",
                        file_path=file_path
                    ))

        # Check for circular import patterns
        imports = re.findall(r"from\s+(\S+)\s+import|import\s+(\S+)", code)
        if len(imports) > 20:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category="dependencies",
                message=f"High number of imports ({len(imports)}) - check for unnecessary dependencies",
                file_path=file_path
            ))

        # Check for missing abstraction
        if code.count("if isinstance(") > 3:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.MEDIUM,
                category="abstraction",
                message="Multiple isinstance checks suggest missing polymorphism/abstraction",
                file_path=file_path,
                suggestion="Consider using abstract base classes or protocols"
            ))

        approved, confidence = self._calculate_approval(findings, max_high=1)
        duration = time.perf_counter() - start

        return ReviewResult(
            agent_name=self.name,
            agent_expertise=self.expertise,
            approved=approved,
            confidence=confidence,
            findings=findings,
            summary=self._generate_summary(findings),
            review_time_seconds=duration
        )

    def _generate_summary(self, findings: List[ReviewFinding]) -> str:
        """Generate review summary."""
        if not findings:
            return "Architecture follows good design principles."
        return f"Found {len(findings)} architectural concerns."


class TestingReviewer(ReviewAgent):
    """
    Testing Expert Reviewer

    Evaluates test coverage, test quality, edge case handling,
    and testing best practices.
    """

    def __init__(self):
        super().__init__("TestingExpert", "Testing & Quality Assurance")

    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Review code for testing issues."""
        import time
        start = time.perf_counter()

        findings = []
        is_test_file = file_path and ("test_" in file_path or "_test.py" in file_path)

        if is_test_file:
            # Review test file
            findings.extend(self._review_test_file(code, file_path))
        else:
            # Review production code for testability
            findings.extend(self._review_testability(code, file_path))

        approved, confidence = self._calculate_approval(findings, max_high=2)
        duration = time.perf_counter() - start

        return ReviewResult(
            agent_name=self.name,
            agent_expertise=self.expertise,
            approved=approved,
            confidence=confidence,
            findings=findings,
            summary=self._generate_summary(findings, is_test_file),
            review_time_seconds=duration
        )

    def _review_test_file(self, code: str, file_path: Optional[str]) -> List[ReviewFinding]:
        """Review a test file."""
        findings = []

        # Check for assertions
        test_functions = re.findall(r"def\s+(test_\w+)", code)
        for test_name in test_functions:
            # Find test body
            pattern = rf"def\s+{test_name}.*?(?=\n    def\s|\nclass\s|\Z)"
            match = re.search(pattern, code, re.DOTALL)
            if match:
                test_body = match.group()
                if "assert" not in test_body and "pytest.raises" not in test_body:
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.HIGH,
                        category="assertions",
                        message=f"Test '{test_name}' has no assertions",
                        file_path=file_path
                    ))

        # Check for magic numbers in tests
        if re.search(r"assert.*==\s*\d{3,}", code):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category="readability",
                message="Magic numbers in assertions - consider using named constants",
                file_path=file_path
            ))

        # Check for proper test isolation
        if "global" in code:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.MEDIUM,
                category="isolation",
                message="Global state in tests may cause flaky tests",
                file_path=file_path
            ))

        return findings

    def _review_testability(self, code: str, file_path: Optional[str]) -> List[ReviewFinding]:
        """Review production code for testability."""
        findings = []

        # Check for hard-to-test patterns
        if "datetime.now()" in code or "time.time()" in code:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category="testability",
                message="Direct time calls are hard to test - consider dependency injection",
                file_path=file_path,
                suggestion="Pass time/datetime as parameter or use a clock abstraction"
            ))

        # Check for singleton patterns (hard to test)
        if re.search(r"_instance\s*=\s*None", code) and "__new__" in code:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category="testability",
                message="Singleton pattern can make testing difficult",
                file_path=file_path
            ))

        # Check for functions without return values that could be tested
        void_functions = re.findall(r"def\s+(\w+)\([^)]*\)\s*:\s*\n(?:(?!\s*return\s+\S).*\n)*(?:\s*return\s*\n|\Z)", code)
        # This is informational only

        return findings

    def _generate_summary(self, findings: List[ReviewFinding], is_test: bool) -> str:
        """Generate review summary."""
        if not findings:
            return "Tests are well-structured." if is_test else "Code is testable."
        return f"Found {len(findings)} testing-related concerns."


class DocumentationReviewer(ReviewAgent):
    """
    Documentation Expert Reviewer

    Evaluates docstrings, comments, type hints,
    and documentation quality.
    """

    def __init__(self):
        super().__init__("DocumentationExpert", "Documentation & Clarity")

    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Review code for documentation issues."""
        import time
        start = time.perf_counter()

        findings = []

        # Check for module docstring
        if not code.strip().startswith('"""') and not code.strip().startswith("'''"):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category="module_doc",
                message="Missing module docstring",
                file_path=file_path
            ))

        # Check public functions for docstrings
        public_functions = re.findall(r"\ndef\s+([a-z]\w*)\s*\(", code)
        for func_name in public_functions:
            if not func_name.startswith("_"):
                # Check if function has docstring
                pattern = rf"def\s+{func_name}\s*\([^)]*\).*?:\s*\n(\s*)(['\"]{{3}})"
                if not re.search(pattern, code):
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.LOW,
                        category="function_doc",
                        message=f"Public function '{func_name}' missing docstring",
                        file_path=file_path
                    ))

        # Check for type hints on public functions
        func_defs = re.findall(r"def\s+([a-z]\w*)\s*\(([^)]*)\)", code)
        for func_name, params in func_defs:
            if not func_name.startswith("_") and params.strip():
                # Check for type hints in parameters
                if ":" not in params and params != "self":
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.LOW,
                        category="type_hints",
                        message=f"Function '{func_name}' missing type hints",
                        file_path=file_path
                    ))

        # Check for TODO/FIXME comments
        todos = re.findall(r"#\s*(TODO|FIXME|XXX|HACK):\s*(.+)", code, re.IGNORECASE)
        for tag, comment in todos:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.INFO,
                category="todo",
                message=f"{tag}: {comment.strip()}",
                file_path=file_path
            ))

        approved, confidence = self._calculate_approval(findings, max_high=5)
        duration = time.perf_counter() - start

        return ReviewResult(
            agent_name=self.name,
            agent_expertise=self.expertise,
            approved=approved,
            confidence=confidence,
            findings=findings,
            summary=self._generate_summary(findings),
            review_time_seconds=duration
        )

    def _generate_summary(self, findings: List[ReviewFinding]) -> str:
        """Generate review summary."""
        doc_issues = [f for f in findings if f.category in ("module_doc", "function_doc", "type_hints")]
        if not doc_issues:
            return "Documentation is adequate."
        return f"Found {len(doc_issues)} documentation gaps."


class ErrorHandlingReviewer(ReviewAgent):
    """
    Error Handling Expert Reviewer

    Evaluates exception handling, error recovery,
    and robustness patterns.
    """

    def __init__(self):
        super().__init__("ErrorHandlingExpert", "Error Handling & Recovery")
        self._patterns = {
            "bare_except": [
                (r"except\s*:", ReviewSeverity.HIGH, "Bare except catches all exceptions including KeyboardInterrupt"),
            ],
            "pass_except": [
                (r"except.*:\s*\n\s*pass", ReviewSeverity.MEDIUM, "Silent exception swallowing - consider logging"),
            ],
            "broad_except": [
                (r"except\s+Exception\s*:", ReviewSeverity.LOW, "Catching broad Exception - consider specific exceptions"),
            ]
        }

    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Review code for error handling issues."""
        import time
        start = time.perf_counter()

        findings = self._check_patterns(code, file_path)

        # Check for raise without exception info
        if re.search(r"raise\s*\n", code) or re.search(r"raise\s+\w+\(\s*\)", code):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category="raise",
                message="Raising exception without message or context",
                file_path=file_path,
                suggestion="Include descriptive error message"
            ))

        # Check for exception chaining
        if "raise " in code and " from " not in code:
            # Count raises that could benefit from chaining
            except_blocks = re.findall(r"except.*:.*?raise\s+\w+", code, re.DOTALL)
            for block in except_blocks:
                if "from" not in block:
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.LOW,
                        category="chaining",
                        message="Consider using 'raise ... from' for exception chaining",
                        file_path=file_path
                    ))
                    break  # Only report once

        # Check for missing finally in resource handling
        try_blocks = code.count("try:")
        finally_blocks = code.count("finally:")
        if try_blocks > 0 and finally_blocks == 0:
            # Check if there's resource handling that needs cleanup
            if "open(" in code or "connect(" in code or "acquire(" in code:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.MEDIUM,
                    category="cleanup",
                    message="Resource handling without finally block - consider context managers",
                    file_path=file_path,
                    suggestion="Use 'with' statement or add finally block for cleanup"
                ))

        approved, confidence = self._calculate_approval(findings)
        duration = time.perf_counter() - start

        return ReviewResult(
            agent_name=self.name,
            agent_expertise=self.expertise,
            approved=approved,
            confidence=confidence,
            findings=findings,
            summary=self._generate_summary(findings),
            review_time_seconds=duration
        )

    def _generate_summary(self, findings: List[ReviewFinding]) -> str:
        """Generate review summary."""
        if not findings:
            return "Error handling looks robust."
        blocking = sum(1 for f in findings if f.severity in (ReviewSeverity.CRITICAL, ReviewSeverity.HIGH))
        if blocking:
            return f"Found {blocking} significant error handling issues."
        return f"Found {len(findings)} error handling suggestions."


class CodeStyleReviewer(ReviewAgent):
    """
    Code Style Expert Reviewer

    Evaluates code formatting, naming conventions,
    PEP 8 compliance, and style consistency.
    """

    def __init__(self):
        super().__init__("CodeStyleExpert", "Code Style & Conventions")
        self._patterns = {
            "naming": [
                (r"def\s+[A-Z]", ReviewSeverity.LOW, "Function name should be lowercase_with_underscores"),
                (r"class\s+[a-z]", ReviewSeverity.LOW, "Class name should be PascalCase"),
                (r"\b[a-z]\s*=", ReviewSeverity.INFO, "Single-letter variable names reduce readability"),
            ],
            "line_length": [
                (r".{121,}", ReviewSeverity.LOW, "Line exceeds 120 characters"),
            ],
            "whitespace": [
                (r"[^\s]==[^\s]", ReviewSeverity.INFO, "Missing spaces around comparison operator"),
                (r",\S", ReviewSeverity.INFO, "Missing space after comma"),
            ]
        }

    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Review code for style issues."""
        import time
        start = time.perf_counter()

        findings = self._check_patterns(code, file_path)

        # Limit single-letter variable findings
        single_letter_count = sum(1 for f in findings if "Single-letter" in f.message)
        if single_letter_count > 3:
            findings = [f for f in findings if "Single-letter" not in f.message]
            findings.append(ReviewFinding(
                severity=ReviewSeverity.INFO,
                category="naming",
                message=f"Found {single_letter_count} single-letter variable names",
                file_path=file_path
            ))

        # Check for consistent string quotes
        single_quotes = len(re.findall(r"'[^']*'", code))
        double_quotes = len(re.findall(r'"[^"]*"', code))
        if single_quotes > 5 and double_quotes > 5:
            ratio = min(single_quotes, double_quotes) / max(single_quotes, double_quotes)
            if ratio > 0.3:  # Mixed usage
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.INFO,
                    category="consistency",
                    message="Inconsistent string quote style - prefer one style",
                    file_path=file_path
                ))

        # Check for trailing whitespace
        if re.search(r" +\n", code):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.INFO,
                category="whitespace",
                message="Trailing whitespace detected",
                file_path=file_path
            ))

        approved, confidence = self._calculate_approval(findings, max_high=10)
        duration = time.perf_counter() - start

        return ReviewResult(
            agent_name=self.name,
            agent_expertise=self.expertise,
            approved=approved,
            confidence=confidence,
            findings=findings,
            summary=self._generate_summary(findings),
            review_time_seconds=duration
        )

    def _generate_summary(self, findings: List[ReviewFinding]) -> str:
        """Generate review summary."""
        if not findings:
            return "Code style is consistent and clean."
        return f"Found {len(findings)} style suggestions."


class APIDesignReviewer(ReviewAgent):
    """
    API Design Expert Reviewer

    Evaluates API contracts, interfaces, parameter design,
    and public API quality.
    """

    def __init__(self):
        super().__init__("APIDesignExpert", "API Design & Contracts")

    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Review code for API design issues."""
        import time
        start = time.perf_counter()

        findings = []

        # Check for too many parameters
        func_defs = re.findall(r"def\s+(\w+)\s*\(([^)]*)\)", code)
        for func_name, params in func_defs:
            param_count = len([p for p in params.split(",") if p.strip() and p.strip() != "self"])
            if param_count > 7:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.MEDIUM,
                    category="parameters",
                    message=f"Function '{func_name}' has {param_count} parameters - consider using a config object",
                    file_path=file_path
                ))
            elif param_count > 5:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.LOW,
                    category="parameters",
                    message=f"Function '{func_name}' has {param_count} parameters - consider grouping",
                    file_path=file_path
                ))

        # Check for mutable default arguments
        mutable_defaults = re.findall(r"def\s+\w+\([^)]*=\s*(\[\]|\{\}|\blist\(\)|\bdict\(\))", code)
        if mutable_defaults:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.HIGH,
                category="defaults",
                message="Mutable default argument - use None and create in function body",
                file_path=file_path,
                suggestion="def func(param=None): param = param or []"
            ))

        # Check for public API without return type hints
        public_funcs = re.findall(r"def\s+([a-z]\w*)\s*\([^)]*\)\s*:", code)
        for func_name in public_funcs:
            if not func_name.startswith("_"):
                pattern = rf"def\s+{func_name}\s*\([^)]*\)\s*->"
                if not re.search(pattern, code):
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.LOW,
                        category="type_hints",
                        message=f"Public function '{func_name}' missing return type hint",
                        file_path=file_path
                    ))

        # Check for inconsistent return types
        func_pattern = r"def\s+(\w+)[^:]+:\s*\n((?:(?!\ndef\s).*\n)*)"
        for match in re.finditer(func_pattern, code):
            func_name, body = match.groups()
            returns = re.findall(r"return\s+(.+)", body)
            if len(returns) > 1:
                # Check if some returns are None-ish and some are not
                has_none = any(r.strip() in ("None", "") for r in returns)
                has_value = any(r.strip() not in ("None", "") for r in returns)
                if has_none and has_value:
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.LOW,
                        category="consistency",
                        message=f"Function '{func_name}' has inconsistent return types (some None, some value)",
                        file_path=file_path
                    ))

        approved, confidence = self._calculate_approval(findings)
        duration = time.perf_counter() - start

        return ReviewResult(
            agent_name=self.name,
            agent_expertise=self.expertise,
            approved=approved,
            confidence=confidence,
            findings=findings,
            summary=self._generate_summary(findings),
            review_time_seconds=duration
        )

    def _generate_summary(self, findings: List[ReviewFinding]) -> str:
        """Generate review summary."""
        if not findings:
            return "API design is clean and consistent."
        blocking = sum(1 for f in findings if f.severity in (ReviewSeverity.CRITICAL, ReviewSeverity.HIGH))
        if blocking:
            return f"Found {blocking} API design issues requiring attention."
        return f"Found {len(findings)} API design suggestions."


class ConcurrencyReviewer(ReviewAgent):
    """
    Concurrency Expert Reviewer

    Evaluates threading, async patterns, race conditions,
    and concurrency safety.
    """

    def __init__(self):
        super().__init__("ConcurrencyExpert", "Concurrency & Threading")
        self._patterns = {
            "race_condition": [
                (r"global\s+\w+.*\n.*threading", ReviewSeverity.HIGH, "Global variable with threading - potential race condition"),
            ],
            "deadlock": [
                (r"\.acquire\(\).*\.acquire\(\)", ReviewSeverity.HIGH, "Multiple lock acquisitions - potential deadlock"),
            ]
        }

    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Review code for concurrency issues."""
        import time
        start = time.perf_counter()

        findings = self._check_patterns(code, file_path)

        # Check for shared mutable state without locks
        if "threading" in code or "multiprocessing" in code:
            # Look for class attributes that might be shared
            class_attrs = re.findall(r"class\s+\w+.*?:\s*\n(\s+\w+\s*=\s*\[\]|\s+\w+\s*=\s*\{\})", code)
            if class_attrs:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.MEDIUM,
                    category="shared_state",
                    message="Mutable class attributes may be shared across threads",
                    file_path=file_path,
                    suggestion="Use instance attributes or protect with locks"
                ))

        # Check for async/await issues
        if "async def" in code:
            # Check for blocking calls in async
            blocking_calls = ["time.sleep", "requests.", "urllib.", "open("]
            for call in blocking_calls:
                if call in code:
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.MEDIUM,
                        category="blocking",
                        message=f"Blocking call '{call}' in async context",
                        file_path=file_path,
                        suggestion="Use async equivalents (asyncio.sleep, aiohttp, aiofiles)"
                    ))

            # Check for missing await
            async_calls = re.findall(r"(\w+)\s*\(\s*\)(?!\s*[,\)])", code)
            # This is a simple heuristic - not perfect

        # Check for thread-unsafe operations
        if "threading.Thread" in code:
            if "daemon=True" not in code and "daemon = True" not in code:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.INFO,
                    category="daemon",
                    message="Consider setting daemon=True for background threads",
                    file_path=file_path
                ))

        approved, confidence = self._calculate_approval(findings)
        duration = time.perf_counter() - start

        return ReviewResult(
            agent_name=self.name,
            agent_expertise=self.expertise,
            approved=approved,
            confidence=confidence,
            findings=findings,
            summary=self._generate_summary(findings),
            review_time_seconds=duration
        )

    def _generate_summary(self, findings: List[ReviewFinding]) -> str:
        """Generate review summary."""
        if not findings:
            return "No concurrency issues detected."
        blocking = sum(1 for f in findings if f.severity in (ReviewSeverity.CRITICAL, ReviewSeverity.HIGH))
        if blocking:
            return f"Found {blocking} potential concurrency bugs."
        return f"Found {len(findings)} concurrency suggestions."


class DataValidationReviewer(ReviewAgent):
    """
    Data Validation Expert Reviewer

    Evaluates input validation, data sanitization,
    and boundary checking.
    """

    def __init__(self):
        super().__init__("DataValidationExpert", "Data Validation & Sanitization")

    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Review code for data validation issues."""
        import time
        start = time.perf_counter()

        findings = []

        # Check for missing input validation in public functions
        func_pattern = r"def\s+([a-z]\w*)\s*\(([^)]+)\)\s*:"
        for match in re.finditer(func_pattern, code):
            func_name, params = match.groups()
            if func_name.startswith("_"):
                continue

            # Get function body
            start_pos = match.end()
            # Find next function or end
            next_func = re.search(r"\ndef\s", code[start_pos:])
            end_pos = start_pos + next_func.start() if next_func else len(code)
            func_body = code[start_pos:end_pos]

            # Check if any validation is done
            has_validation = any(kw in func_body for kw in [
                "if not ", "if ", "raise ", "assert ", "validate", "isinstance"
            ])

            if not has_validation and len(func_body.strip()) > 50:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.LOW,
                    category="validation",
                    message=f"Function '{func_name}' may need input validation",
                    file_path=file_path
                ))

        # Check for unsafe type conversions
        unsafe_conversions = [
            (r"int\([^)]+\)(?!.*try)", "Unchecked int() conversion may raise ValueError"),
            (r"float\([^)]+\)(?!.*try)", "Unchecked float() conversion may raise ValueError"),
            (r"\[.*\]\[.*\](?!.*try)", "Unchecked list indexing may raise IndexError"),
        ]

        for pattern, message in unsafe_conversions:
            if re.search(pattern, code):
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.LOW,
                    category="type_safety",
                    message=message,
                    file_path=file_path
                ))

        # Check for missing None checks
        if ".get(" in code:
            # Check if result is used without None check
            get_uses = re.findall(r"(\w+)\.get\([^)]+\)\.(\w+)", code)
            for var, attr in get_uses:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.MEDIUM,
                    category="null_safety",
                    message=f"Chained call after .get() may fail if key is missing",
                    file_path=file_path,
                    suggestion="Use .get() with default or check for None first"
                ))

        approved, confidence = self._calculate_approval(findings, max_high=3)
        duration = time.perf_counter() - start

        return ReviewResult(
            agent_name=self.name,
            agent_expertise=self.expertise,
            approved=approved,
            confidence=confidence,
            findings=findings,
            summary=self._generate_summary(findings),
            review_time_seconds=duration
        )

    def _generate_summary(self, findings: List[ReviewFinding]) -> str:
        """Generate review summary."""
        if not findings:
            return "Data validation looks adequate."
        return f"Found {len(findings)} data validation concerns."


class MaintainabilityReviewer(ReviewAgent):
    """
    Maintainability Expert Reviewer

    Evaluates code readability, complexity, DRY principle,
    and long-term maintainability.
    """

    def __init__(self):
        super().__init__("MaintainabilityExpert", "Maintainability & Readability")

    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Review code for maintainability issues."""
        import time
        start = time.perf_counter()

        findings = []

        # Check function length
        func_pattern = r"def\s+(\w+)[^:]+:\s*\n((?:(?!\ndef\s).*\n)*)"
        for match in re.finditer(func_pattern, code):
            func_name, body = match.groups()
            line_count = len([l for l in body.split("\n") if l.strip()])
            if line_count > 50:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.MEDIUM,
                    category="function_length",
                    message=f"Function '{func_name}' is {line_count} lines - consider splitting",
                    file_path=file_path
                ))
            elif line_count > 30:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.LOW,
                    category="function_length",
                    message=f"Function '{func_name}' is {line_count} lines - could be simplified",
                    file_path=file_path
                ))

        # Check for code duplication (simple check)
        lines = [l.strip() for l in code.split("\n") if l.strip() and not l.strip().startswith("#")]
        seen: Dict[str, int] = {}
        for line in lines:
            if len(line) > 30:  # Only check substantial lines
                seen[line] = seen.get(line, 0) + 1

        duplicates = [(line, count) for line, count in seen.items() if count > 2]
        if duplicates:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category="duplication",
                message=f"Found {len(duplicates)} potentially duplicated code patterns",
                file_path=file_path,
                suggestion="Consider extracting common code into functions"
            ))

        # Check nesting depth
        max_depth = 0
        current_depth = 0
        for line in code.split("\n"):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            depth = indent // 4  # Assuming 4-space indents
            max_depth = max(max_depth, depth)

        if max_depth > 5:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.MEDIUM,
                category="complexity",
                message=f"Maximum nesting depth is {max_depth} - consider refactoring",
                file_path=file_path,
                suggestion="Use early returns, extract methods, or restructure logic"
            ))
        elif max_depth > 4:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category="complexity",
                message=f"Nesting depth of {max_depth} is getting hard to follow",
                file_path=file_path
            ))

        # Check for magic numbers
        magic_numbers = re.findall(r"[=<>+\-*/]\s*(\d{2,})\b", code)
        magic_numbers = [n for n in magic_numbers if n not in ("100", "1000", "10")]
        if len(magic_numbers) > 3:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category="magic_numbers",
                message=f"Found {len(magic_numbers)} magic numbers - consider named constants",
                file_path=file_path
            ))

        approved, confidence = self._calculate_approval(findings, max_high=2)
        duration = time.perf_counter() - start

        return ReviewResult(
            agent_name=self.name,
            agent_expertise=self.expertise,
            approved=approved,
            confidence=confidence,
            findings=findings,
            summary=self._generate_summary(findings),
            review_time_seconds=duration
        )

    def _generate_summary(self, findings: List[ReviewFinding]) -> str:
        """Generate review summary."""
        if not findings:
            return "Code is maintainable and readable."
        return f"Found {len(findings)} maintainability suggestions."


class IntegrationReviewer(ReviewAgent):
    """
    Integration Expert Reviewer

    Evaluates compatibility, dependency management,
    and integration patterns.
    """

    def __init__(self):
        super().__init__("IntegrationExpert", "Integration & Compatibility")

    def review(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Review code for integration issues."""
        import time
        start = time.perf_counter()

        findings = []

        # Check for version-specific features without guards
        python_310_features = ["match ", "case "]
        python_39_features = ["dict | dict", "list | list"]
        python_38_features = [":="]

        for feature in python_310_features:
            if feature in code:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.INFO,
                    category="compatibility",
                    message=f"Pattern matching requires Python 3.10+",
                    file_path=file_path
                ))
                break

        for feature in python_38_features:
            if feature in code:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.INFO,
                    category="compatibility",
                    message=f"Walrus operator requires Python 3.8+",
                    file_path=file_path
                ))
                break

        # Check for deprecated imports/patterns
        deprecated = [
            ("from collections import ", "Mapping", "Use collections.abc.Mapping instead"),
            ("from collections import ", "Sequence", "Use collections.abc.Sequence instead"),
            ("import imp", "", "imp module is deprecated - use importlib"),
            ("from distutils", "", "distutils is deprecated - use setuptools"),
        ]

        for prefix, pattern, message in deprecated:
            if prefix in code and pattern in code:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.MEDIUM,
                    category="deprecated",
                    message=message,
                    file_path=file_path
                ))

        # Check for hardcoded paths
        if re.search(r'["\'][/\\](?:home|Users|var|tmp|etc)[/\\]', code):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.MEDIUM,
                category="portability",
                message="Hardcoded absolute path detected - use Path or os.path",
                file_path=file_path
            ))

        # Check for platform-specific code without guards
        if "os.name" not in code and "sys.platform" not in code:
            if re.search(r"os\.(fork|getuid|getgid)", code):
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.MEDIUM,
                    category="portability",
                    message="Unix-specific function without platform check",
                    file_path=file_path
                ))

        # Check for missing encoding in file operations
        if re.search(r"open\([^)]+\)(?!.*encoding)", code):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category="encoding",
                message="File open() without encoding - may have issues across platforms",
                file_path=file_path,
                suggestion="Specify encoding='utf-8' for text files"
            ))

        approved, confidence = self._calculate_approval(findings, max_high=2)
        duration = time.perf_counter() - start

        return ReviewResult(
            agent_name=self.name,
            agent_expertise=self.expertise,
            approved=approved,
            confidence=confidence,
            findings=findings,
            summary=self._generate_summary(findings),
            review_time_seconds=duration
        )

    def _generate_summary(self, findings: List[ReviewFinding]) -> str:
        """Generate review summary."""
        if not findings:
            return "Code has good integration practices."
        return f"Found {len(findings)} integration/compatibility concerns."
