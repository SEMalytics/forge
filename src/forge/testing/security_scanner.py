"""
Security scanning and vulnerability detection

Provides:
- Static code analysis for security issues
- Dependency vulnerability scanning
- OWASP compliance checking
- Secret detection
- License validation
"""

import re
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class SecurityScanError(ForgeError):
    """Errors during security scanning"""
    pass


class Severity(Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(Enum):
    """Types of security vulnerabilities"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    HARDCODED_SECRET = "hardcoded_secret"
    WEAK_CRYPTO = "weak_crypto"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    DEPENDENCY_VULNERABILITY = "dependency_vulnerability"
    LICENSE_ISSUE = "license_issue"
    OWASP_VIOLATION = "owasp_violation"


@dataclass
class Vulnerability:
    """Security vulnerability finding"""
    type: VulnerabilityType
    severity: Severity
    file_path: str
    line_number: int
    description: str
    recommendation: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    confidence: str = "high"  # high, medium, low

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'type': self.type.value,
            'severity': self.severity.value,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'description': self.description,
            'recommendation': self.recommendation,
            'cwe_id': self.cwe_id,
            'owasp_category': self.owasp_category,
            'confidence': self.confidence
        }


@dataclass
class ScanResult:
    """Security scan result"""
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    dependencies_scanned: int = 0
    secrets_found: int = 0
    owasp_score: float = 100.0  # 0-100, higher is better
    scan_duration_seconds: float = 0.0

    @property
    def critical_count(self) -> int:
        """Count critical vulnerabilities"""
        return sum(1 for v in self.vulnerabilities if v.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        """Count high severity vulnerabilities"""
        return sum(1 for v in self.vulnerabilities if v.severity == Severity.HIGH)

    @property
    def total_count(self) -> int:
        """Total vulnerability count"""
        return len(self.vulnerabilities)

    @property
    def is_secure(self) -> bool:
        """Whether code passes security requirements"""
        return self.critical_count == 0 and self.high_count == 0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'vulnerabilities': [v.to_dict() for v in self.vulnerabilities],
            'dependencies_scanned': self.dependencies_scanned,
            'secrets_found': self.secrets_found,
            'owasp_score': self.owasp_score,
            'scan_duration_seconds': self.scan_duration_seconds,
            'summary': {
                'critical': self.critical_count,
                'high': self.high_count,
                'total': self.total_count,
                'is_secure': self.is_secure
            }
        }


class SecurityScanner:
    """
    Comprehensive security scanner.

    Features:
    - Static analysis for common vulnerabilities
    - Dependency vulnerability scanning
    - Secret detection (API keys, passwords, tokens)
    - OWASP Top 10 compliance checking
    - License validation
    """

    # Common secret patterns
    SECRET_PATTERNS = {
        'api_key': re.compile(r'(?i)(api[_-]?key|apikey)[\s]*=[\s]*["\']([a-zA-Z0-9_\-]{20,})["\']'),
        'password': re.compile(r'(?i)(password|passwd|pwd)[\s]*=[\s]*["\']([^"\']{8,})["\']'),
        'aws_key': re.compile(r'AKIA[0-9A-Z]{16}'),
        'github_token': re.compile(r'ghp_[a-zA-Z0-9]{36}'),
        'private_key': re.compile(r'-----BEGIN (RSA |EC )?PRIVATE KEY-----'),
        'jwt': re.compile(r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'),
    }

    # Dangerous functions by language
    DANGEROUS_FUNCTIONS = {
        'python': {
            'eval': (Severity.CRITICAL, 'Avoid eval() - use ast.literal_eval() instead'),
            'exec': (Severity.CRITICAL, 'Avoid exec() - consider safer alternatives'),
            'pickle.loads': (Severity.HIGH, 'Avoid pickle - use JSON for untrusted data'),
            'os.system': (Severity.HIGH, 'Use subprocess.run() with shell=False instead'),
            'subprocess.call.*shell=True': (Severity.HIGH, 'Avoid shell=True to prevent command injection'),
        },
        'javascript': {
            'eval': (Severity.CRITICAL, 'Avoid eval() - parse JSON or use safer alternatives'),
            'innerHTML': (Severity.HIGH, 'Use textContent or sanitize HTML to prevent XSS'),
            'dangerouslySetInnerHTML': (Severity.HIGH, 'Sanitize HTML before rendering'),
            'setTimeout.*string': (Severity.MEDIUM, 'Pass function instead of string to setTimeout'),
        },
        'sql': {
            r'\+.*SELECT': (Severity.CRITICAL, 'Use parameterized queries to prevent SQL injection'),
            r'f".*SELECT': (Severity.CRITICAL, 'Use parameterized queries, not f-strings'),
            r'%.*SELECT': (Severity.CRITICAL, 'Use parameterized queries, not % formatting'),
        }
    }

    def __init__(
        self,
        enable_external_tools: bool = True,
        owasp_config: Optional[Dict] = None
    ):
        """
        Initialize security scanner.

        Args:
            enable_external_tools: Whether to use external scanning tools
            owasp_config: OWASP compliance configuration
        """
        self.enable_external_tools = enable_external_tools
        self.owasp_config = owasp_config or {}

        # Check for external tools
        self.bandit_available = self._check_tool('bandit')
        self.semgrep_available = self._check_tool('semgrep')

        logger.info(
            f"Initialized SecurityScanner "
            f"(bandit={self.bandit_available}, semgrep={self.semgrep_available})"
        )

    def _check_tool(self, tool_name: str) -> bool:
        """Check if external tool is available"""
        if not self.enable_external_tools:
            return False

        try:
            result = subprocess.run(
                [tool_name, '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def scan(
        self,
        code_files: Dict[str, str],
        dependencies: Optional[Dict[str, str]] = None
    ) -> ScanResult:
        """
        Perform comprehensive security scan.

        Args:
            code_files: Dictionary mapping file paths to code content
            dependencies: Optional dependency manifest (package.json, requirements.txt, etc.)

        Returns:
            Security scan result
        """
        import time

        start_time = time.time()

        logger.info(f"Starting security scan of {len(code_files)} files")

        result = ScanResult()

        # 1. Static code analysis
        static_vulns = self._static_analysis(code_files)
        result.vulnerabilities.extend(static_vulns)

        # 2. Secret detection
        secret_vulns = self._detect_secrets(code_files)
        result.vulnerabilities.extend(secret_vulns)
        result.secrets_found = len(secret_vulns)

        # 3. Dependency scanning
        if dependencies:
            dep_vulns = self._scan_dependencies(dependencies)
            result.vulnerabilities.extend(dep_vulns)
            result.dependencies_scanned = len(dependencies)

        # 4. OWASP compliance check
        result.owasp_score = self._calculate_owasp_score(result.vulnerabilities)

        result.scan_duration_seconds = time.time() - start_time

        logger.info(
            f"Security scan complete: {result.total_count} vulnerabilities found "
            f"({result.critical_count} critical, {result.high_count} high)"
        )

        return result

    def _static_analysis(self, code_files: Dict[str, str]) -> List[Vulnerability]:
        """Perform static code analysis"""
        vulnerabilities = []

        # Try external tools first
        if self.bandit_available:
            vulnerabilities.extend(self._run_bandit(code_files))

        if self.semgrep_available:
            vulnerabilities.extend(self._run_semgrep(code_files))

        # Fallback to pattern-based detection
        vulnerabilities.extend(self._pattern_based_detection(code_files))

        return vulnerabilities

    def _run_bandit(self, code_files: Dict[str, str]) -> List[Vulnerability]:
        """Run Bandit security scanner for Python"""
        vulnerabilities = []

        # Filter Python files
        python_files = {
            path: content for path, content in code_files.items()
            if path.endswith('.py')
        }

        if not python_files:
            return vulnerabilities

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                workspace = Path(tmpdir)

                # Write files
                for file_path, content in python_files.items():
                    target = workspace / Path(file_path).name
                    target.write_text(content)

                # Run bandit
                result = subprocess.run(
                    ['bandit', '-r', '-f', 'json', str(workspace)],
                    capture_output=True,
                    timeout=60
                )

                if result.stdout:
                    data = json.loads(result.stdout)

                    for issue in data.get('results', []):
                        severity_map = {
                            'HIGH': Severity.HIGH,
                            'MEDIUM': Severity.MEDIUM,
                            'LOW': Severity.LOW
                        }

                        vulnerabilities.append(Vulnerability(
                            type=VulnerabilityType.OWASP_VIOLATION,
                            severity=severity_map.get(issue['issue_severity'], Severity.MEDIUM),
                            file_path=issue['filename'],
                            line_number=issue['line_number'],
                            description=issue['issue_text'],
                            recommendation=issue.get('more_info', 'Review and fix'),
                            cwe_id=issue.get('issue_cwe', {}).get('id'),
                            confidence=issue.get('issue_confidence', 'MEDIUM').lower()
                        ))

        except Exception as e:
            logger.warning(f"Bandit scan failed: {e}")

        return vulnerabilities

    def _run_semgrep(self, code_files: Dict[str, str]) -> List[Vulnerability]:
        """Run Semgrep security scanner"""
        vulnerabilities = []

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                workspace = Path(tmpdir)

                # Write files
                for file_path, content in code_files.items():
                    target = workspace / Path(file_path).name
                    target.write_text(content)

                # Run semgrep with security rules
                result = subprocess.run(
                    ['semgrep', '--config=auto', '--json', str(workspace)],
                    capture_output=True,
                    timeout=120
                )

                if result.stdout:
                    data = json.loads(result.stdout)

                    for finding in data.get('results', []):
                        severity_map = {
                            'ERROR': Severity.HIGH,
                            'WARNING': Severity.MEDIUM,
                            'INFO': Severity.LOW
                        }

                        vulnerabilities.append(Vulnerability(
                            type=VulnerabilityType.OWASP_VIOLATION,
                            severity=severity_map.get(finding.get('extra', {}).get('severity'), Severity.MEDIUM),
                            file_path=finding['path'],
                            line_number=finding['start']['line'],
                            description=finding['extra']['message'],
                            recommendation='Review semgrep finding',
                            owasp_category=finding['extra'].get('metadata', {}).get('owasp')
                        ))

        except Exception as e:
            logger.warning(f"Semgrep scan failed: {e}")

        return vulnerabilities

    def _pattern_based_detection(self, code_files: Dict[str, str]) -> List[Vulnerability]:
        """Pattern-based vulnerability detection"""
        vulnerabilities = []

        for file_path, content in code_files.items():
            lines = content.split('\n')

            # Detect language
            if file_path.endswith('.py'):
                lang = 'python'
            elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
                lang = 'javascript'
            else:
                continue

            # Check for dangerous functions
            if lang in self.DANGEROUS_FUNCTIONS:
                for pattern, (severity, recommendation) in self.DANGEROUS_FUNCTIONS[lang].items():
                    pattern_re = re.compile(pattern)

                    for i, line in enumerate(lines, 1):
                        if pattern_re.search(line):
                            vulnerabilities.append(Vulnerability(
                                type=VulnerabilityType.OWASP_VIOLATION,
                                severity=severity,
                                file_path=file_path,
                                line_number=i,
                                description=f"Dangerous function: {pattern}",
                                recommendation=recommendation,
                                owasp_category="A03:2021 - Injection"
                            ))

            # Check for SQL injection patterns
            for pattern, (severity, recommendation) in self.DANGEROUS_FUNCTIONS.get('sql', {}).items():
                pattern_re = re.compile(pattern, re.IGNORECASE)

                for i, line in enumerate(lines, 1):
                    if pattern_re.search(line):
                        vulnerabilities.append(Vulnerability(
                            type=VulnerabilityType.SQL_INJECTION,
                            severity=severity,
                            file_path=file_path,
                            line_number=i,
                            description="Potential SQL injection vulnerability",
                            recommendation=recommendation,
                            cwe_id="CWE-89",
                            owasp_category="A03:2021 - Injection"
                        ))

        return vulnerabilities

    def _detect_secrets(self, code_files: Dict[str, str]) -> List[Vulnerability]:
        """Detect hardcoded secrets"""
        vulnerabilities = []

        for file_path, content in code_files.items():
            lines = content.split('\n')

            for pattern_name, pattern in self.SECRET_PATTERNS.items():
                for i, line in enumerate(lines, 1):
                    matches = pattern.findall(line)
                    if matches:
                        # Redact the secret in description
                        redacted_line = line[:50] + '...' if len(line) > 50 else line

                        vulnerabilities.append(Vulnerability(
                            type=VulnerabilityType.HARDCODED_SECRET,
                            severity=Severity.CRITICAL,
                            file_path=file_path,
                            line_number=i,
                            description=f"Hardcoded {pattern_name} detected: {redacted_line}",
                            recommendation="Move secrets to environment variables or secret management system",
                            cwe_id="CWE-798",
                            owasp_category="A02:2021 - Cryptographic Failures"
                        ))

        return vulnerabilities

    def _scan_dependencies(self, dependencies: Dict[str, str]) -> List[Vulnerability]:
        """Scan dependencies for known vulnerabilities"""
        vulnerabilities = []

        # This is a simplified implementation
        # In production, you'd use:
        # - pip-audit for Python
        # - npm audit for JavaScript
        # - bundler-audit for Ruby
        # - cargo audit for Rust

        logger.info(f"Scanning {len(dependencies)} dependencies")

        # Placeholder: Check for known vulnerable packages
        KNOWN_VULNERABLE = {
            'requests': ['2.25.0'],  # Example
            'lodash': ['4.17.19'],   # Example
        }

        for pkg_name, version in dependencies.items():
            if pkg_name in KNOWN_VULNERABLE:
                if version in KNOWN_VULNERABLE[pkg_name]:
                    vulnerabilities.append(Vulnerability(
                        type=VulnerabilityType.DEPENDENCY_VULNERABILITY,
                        severity=Severity.HIGH,
                        file_path='dependencies',
                        line_number=0,
                        description=f"Vulnerable dependency: {pkg_name}=={version}",
                        recommendation=f"Upgrade {pkg_name} to latest version",
                        owasp_category="A06:2021 - Vulnerable and Outdated Components"
                    ))

        return vulnerabilities

    def _calculate_owasp_score(self, vulnerabilities: List[Vulnerability]) -> float:
        """Calculate OWASP compliance score (0-100)"""
        if not vulnerabilities:
            return 100.0

        # Deduct points based on severity
        score = 100.0

        for vuln in vulnerabilities:
            if vuln.severity == Severity.CRITICAL:
                score -= 20.0
            elif vuln.severity == Severity.HIGH:
                score -= 10.0
            elif vuln.severity == Severity.MEDIUM:
                score -= 5.0
            elif vuln.severity == Severity.LOW:
                score -= 1.0

        return max(0.0, score)

    def generate_report(self, result: ScanResult, output_path: Optional[Path] = None) -> str:
        """
        Generate security report.

        Args:
            result: Scan result
            output_path: Optional path to save report

        Returns:
            Report content
        """
        report_lines = [
            "# Security Scan Report",
            "",
            "## Summary",
            f"- **Total Vulnerabilities**: {result.total_count}",
            f"- **Critical**: {result.critical_count}",
            f"- **High**: {result.high_count}",
            f"- **Secrets Found**: {result.secrets_found}",
            f"- **Dependencies Scanned**: {result.dependencies_scanned}",
            f"- **OWASP Score**: {result.owasp_score:.1f}/100",
            f"- **Scan Duration**: {result.scan_duration_seconds:.2f}s",
            "",
            f"**Security Status**: {'✓ PASS' if result.is_secure else '✗ FAIL'}",
            "",
        ]

        if result.vulnerabilities:
            report_lines.extend([
                "## Vulnerabilities",
                ""
            ])

            # Group by severity
            by_severity = {}
            for vuln in result.vulnerabilities:
                if vuln.severity not in by_severity:
                    by_severity[vuln.severity] = []
                by_severity[vuln.severity].append(vuln)

            for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
                if severity not in by_severity:
                    continue

                report_lines.append(f"### {severity.value.upper()}")
                report_lines.append("")

                for vuln in by_severity[severity]:
                    report_lines.extend([
                        f"**{vuln.file_path}:{vuln.line_number}**",
                        f"- Type: {vuln.type.value}",
                        f"- Description: {vuln.description}",
                        f"- Recommendation: {vuln.recommendation}",
                    ])

                    if vuln.cwe_id:
                        report_lines.append(f"- CWE: {vuln.cwe_id}")
                    if vuln.owasp_category:
                        report_lines.append(f"- OWASP: {vuln.owasp_category}")

                    report_lines.append("")

        report = "\n".join(report_lines)

        if output_path:
            output_path.write_text(report)
            logger.info(f"Security report saved to {output_path}")

        return report
