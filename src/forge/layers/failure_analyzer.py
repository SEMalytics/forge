"""
Failure analysis and root cause identification

Analyzes test failures to:
- Extract error messages and stack traces
- Identify root causes
- Categorize failure types
- Load relevant troubleshooting patterns
- Generate targeted fix suggestions
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from forge.knowledgeforge.pattern_store import PatternStore
from forge.testing.docker_runner import TestResult
from forge.testing.security_scanner import ScanResult, Vulnerability
from forge.testing.performance import BenchmarkResult
from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class AnalysisError(ForgeError):
    """Errors during failure analysis"""
    pass


class FailureType(Enum):
    """Types of test failures"""
    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    ASSERTION_ERROR = "assertion_error"
    TYPE_ERROR = "type_error"
    NAME_ERROR = "name_error"
    ATTRIBUTE_ERROR = "attribute_error"
    KEY_ERROR = "key_error"
    INDEX_ERROR = "index_error"
    VALUE_ERROR = "value_error"
    ZERO_DIVISION_ERROR = "zero_division_error"
    TIMEOUT_ERROR = "timeout_error"
    NETWORK_ERROR = "network_error"
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    UNKNOWN = "unknown"


class Priority(Enum):
    """Fix priority levels"""
    CRITICAL = "critical"  # Blocks all functionality
    HIGH = "high"          # Blocks major features
    MEDIUM = "medium"      # Degrades functionality
    LOW = "low"            # Minor issues


@dataclass
class StackFrame:
    """Represents a stack trace frame"""
    file_path: str
    line_number: int
    function_name: str
    code_line: Optional[str] = None


@dataclass
class FailureDetails:
    """Detailed information about a failure"""
    failure_type: FailureType
    error_message: str
    stack_trace: List[StackFrame]
    failing_file: str
    failing_line: int
    test_name: str
    context: Dict = field(default_factory=dict)


@dataclass
class FixSuggestion:
    """Suggested fix for a failure"""
    failure_type: FailureType
    root_cause: str
    suggested_fix: str
    code_changes: List[Dict]  # [{"file": path, "old": str, "new": str}]
    relevant_patterns: List[str]
    priority: Priority
    confidence: float  # 0.0-1.0
    explanation: str

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'failure_type': self.failure_type.value,
            'root_cause': self.root_cause,
            'suggested_fix': self.suggested_fix,
            'code_changes': self.code_changes,
            'relevant_patterns': self.relevant_patterns,
            'priority': self.priority.value,
            'confidence': self.confidence,
            'explanation': self.explanation
        }


class FailureAnalyzer:
    """
    Analyze test failures and generate fix suggestions.

    Features:
    - Parse error messages and stack traces
    - Identify root causes
    - Categorize failure types
    - Load relevant troubleshooting patterns
    - Generate targeted fix suggestions
    - Prioritize fixes by impact
    """

    # Common error patterns
    ERROR_PATTERNS = {
        FailureType.SYNTAX_ERROR: [
            r'SyntaxError:',
            r'invalid syntax',
            r'unexpected EOF',
            r'unmatched'
        ],
        FailureType.IMPORT_ERROR: [
            r'ImportError:',
            r'ModuleNotFoundError:',
            r'No module named',
            r'cannot import name'
        ],
        FailureType.ASSERTION_ERROR: [
            r'AssertionError:',
            r'assert .+ == .+',
            r'Expected .+ but got'
        ],
        FailureType.TYPE_ERROR: [
            r'TypeError:',
            r'not supported between',
            r'takes .+ arguments but .+ were given',
            r'object is not callable'
        ],
        FailureType.NAME_ERROR: [
            r'NameError:',
            r'name .+ is not defined'
        ],
        FailureType.ATTRIBUTE_ERROR: [
            r'AttributeError:',
            r'has no attribute',
            r'object has no attribute'
        ],
        FailureType.KEY_ERROR: [
            r'KeyError:',
            r'key not found'
        ],
        FailureType.INDEX_ERROR: [
            r'IndexError:',
            r'list index out of range',
            r'tuple index out of range'
        ],
        FailureType.VALUE_ERROR: [
            r'ValueError:',
            r'invalid literal',
            r'could not convert'
        ],
        FailureType.TIMEOUT_ERROR: [
            r'TimeoutError:',
            r'timeout',
            r'timed out'
        ],
        FailureType.NETWORK_ERROR: [
            r'ConnectionError:',
            r'NetworkError:',
            r'connection refused',
            r'connection reset'
        ],
        FailureType.ZERO_DIVISION_ERROR: [
            r'ZeroDivisionError:',
            r'division by zero',
            r'divide by zero'
        ]
    }

    # Fix templates by failure type
    FIX_TEMPLATES = {
        FailureType.IMPORT_ERROR: {
            'root_cause': 'Missing or incorrect import',
            'suggestions': [
                'Install missing package: pip install {package}',
                'Fix import path',
                'Check package name spelling',
                'Verify package is in requirements.txt'
            ]
        },
        FailureType.NAME_ERROR: {
            'root_cause': 'Undefined variable or function',
            'suggestions': [
                'Define the variable before use',
                'Check variable name spelling',
                'Import required function/class',
                'Fix scope issues (local vs global)'
            ]
        },
        FailureType.ATTRIBUTE_ERROR: {
            'root_cause': 'Accessing non-existent attribute',
            'suggestions': [
                'Check attribute name spelling',
                'Verify object type',
                'Add attribute to class',
                'Use hasattr() for defensive coding'
            ]
        },
        FailureType.TYPE_ERROR: {
            'root_cause': 'Incorrect type operation',
            'suggestions': [
                'Add type conversion',
                'Fix function arguments',
                'Check data types',
                'Use type hints for clarity'
            ]
        },
        FailureType.ASSERTION_ERROR: {
            'root_cause': 'Test expectation not met',
            'suggestions': [
                'Fix logic bug in implementation',
                'Update test expectations if correct',
                'Check edge cases',
                'Review algorithm correctness'
            ]
        }
    }

    def __init__(
        self,
        pattern_store: Optional[PatternStore] = None
    ):
        """
        Initialize failure analyzer.

        Args:
            pattern_store: KnowledgeForge pattern store
        """
        self.pattern_store = pattern_store or PatternStore()
        logger.info("Initialized FailureAnalyzer")

    def analyze_failures(
        self,
        test_results: Optional[TestResult] = None,
        security_results: Optional[ScanResult] = None,
        performance_results: Optional[List[BenchmarkResult]] = None,
        code_files: Optional[Dict[str, str]] = None
    ) -> List[FixSuggestion]:
        """
        Analyze failures and generate fix suggestions.

        Args:
            test_results: Test execution results
            security_results: Security scan results
            performance_results: Performance benchmark results
            code_files: Dictionary mapping file paths to code content

        Returns:
            List of FixSuggestion objects prioritized by impact
        """
        logger.info("Analyzing failures")

        all_suggestions = []

        # Analyze test failures
        if test_results and test_results.failed > 0:
            test_suggestions = self._analyze_test_failures(
                test_results, code_files or {}
            )
            all_suggestions.extend(test_suggestions)

        # Analyze security issues
        if security_results and not security_results.is_secure:
            security_suggestions = self._analyze_security_failures(
                security_results, code_files or {}
            )
            all_suggestions.extend(security_suggestions)

        # Analyze performance issues
        if performance_results:
            perf_suggestions = self._analyze_performance_failures(
                performance_results, code_files or {}
            )
            all_suggestions.extend(perf_suggestions)

        # Sort by priority and confidence
        all_suggestions.sort(
            key=lambda s: (
                ['critical', 'high', 'medium', 'low'].index(s.priority.value),
                -s.confidence
            )
        )

        logger.info(f"Generated {len(all_suggestions)} fix suggestions")
        return all_suggestions

    def _analyze_test_failures(
        self,
        test_results: TestResult,
        code_files: Dict[str, str]
    ) -> List[FixSuggestion]:
        """Analyze test failures"""
        suggestions = []

        # Parse test output for failure details
        failure_details = self._parse_test_output(test_results.output)

        for failure in failure_details:
            # Categorize failure type
            failure_type = self._categorize_failure(failure.error_message)

            # Generate fix suggestion
            suggestion = self._generate_fix_suggestion(
                failure, failure_type, code_files
            )

            if suggestion:
                suggestions.append(suggestion)

        return suggestions

    def _parse_test_output(self, output: str) -> List[FailureDetails]:
        """Parse test output to extract failure details"""
        failures = []

        # Parse pytest output
        if 'FAILED' in output or 'ERROR' in output:
            failures.extend(self._parse_pytest_output(output))

        # Parse jest output
        elif 'FAIL' in output or '×' in output:
            failures.extend(self._parse_jest_output(output))

        return failures

    def _parse_pytest_output(self, output: str) -> List[FailureDetails]:
        """Parse pytest failure output"""
        failures = []
        lines = output.split('\n')

        current_test = None
        current_error = []
        stack_trace = []

        for i, line in enumerate(lines):
            # Detect test failure header
            if 'FAILED' in line or 'ERROR' in line:
                # Parse test name
                match = re.search(r'(\w+\.py)::(test_\w+)', line)
                if match:
                    current_test = match.group(2)

            # Collect error message
            elif current_test and (line.strip().startswith('E ') or 'Error:' in line):
                current_error.append(line.strip())

            # Parse stack trace
            elif current_test and re.match(r'\s+File ".*", line \d+', line):
                # Extract file, line, function
                match = re.search(r'File "(.+)", line (\d+), in (\w+)', line)
                if match:
                    file_path, line_num, func_name = match.groups()
                    code_line = lines[i + 1].strip() if i + 1 < len(lines) else None

                    stack_trace.append(StackFrame(
                        file_path=file_path,
                        line_number=int(line_num),
                        function_name=func_name,
                        code_line=code_line
                    ))

            # End of failure block
            elif current_test and line.strip() == '' and current_error:
                if stack_trace:
                    failures.append(FailureDetails(
                        failure_type=FailureType.UNKNOWN,
                        error_message=' '.join(current_error),
                        stack_trace=stack_trace,
                        failing_file=stack_trace[-1].file_path if stack_trace else '',
                        failing_line=stack_trace[-1].line_number if stack_trace else 0,
                        test_name=current_test
                    ))

                current_test = None
                current_error = []
                stack_trace = []

        return failures

    def _parse_jest_output(self, output: str) -> List[FailureDetails]:
        """Parse jest failure output"""
        failures = []
        lines = output.split('\n')

        current_test = None
        current_error = []

        for line in lines:
            # Detect test failure
            if '×' in line or 'FAIL' in line:
                match = re.search(r'(test_\w+|it .+)', line)
                if match:
                    current_test = match.group(1)

            # Collect error
            elif current_test and ('Error:' in line or 'Expected' in line):
                current_error.append(line.strip())

            # End of error block
            elif current_test and line.strip() == '' and current_error:
                failures.append(FailureDetails(
                    failure_type=FailureType.UNKNOWN,
                    error_message=' '.join(current_error),
                    stack_trace=[],
                    failing_file='',
                    failing_line=0,
                    test_name=current_test
                ))

                current_test = None
                current_error = []

        return failures

    def _categorize_failure(self, error_message: str) -> FailureType:
        """Categorize failure type from error message"""
        for failure_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_message, re.IGNORECASE):
                    return failure_type

        return FailureType.UNKNOWN

    def _generate_fix_suggestion(
        self,
        failure: FailureDetails,
        failure_type: FailureType,
        code_files: Dict[str, str]
    ) -> Optional[FixSuggestion]:
        """Generate fix suggestion for a failure"""
        # Get fix template
        template = self.FIX_TEMPLATES.get(failure_type, {
            'root_cause': 'Test failure',
            'suggestions': ['Review error and fix implementation']
        })

        # Load relevant troubleshooting patterns
        patterns = self._load_relevant_patterns(failure_type, failure.error_message)

        # Determine priority
        priority = self._determine_priority(failure_type, failure)

        # Generate specific fix
        suggested_fix = self._generate_specific_fix(failure, failure_type)

        # Prepare code changes
        code_changes = self._prepare_code_changes(failure, code_files)

        # Calculate confidence
        confidence = self._calculate_confidence(failure_type, patterns, code_changes)

        return FixSuggestion(
            failure_type=failure_type,
            root_cause=template['root_cause'],
            suggested_fix=suggested_fix,
            code_changes=code_changes,
            relevant_patterns=[p['filename'] for p in patterns],
            priority=priority,
            confidence=confidence,
            explanation=self._generate_explanation(failure, failure_type)
        )

    def _load_relevant_patterns(
        self, failure_type: FailureType, error_message: str
    ) -> List[Dict]:
        """Load relevant troubleshooting patterns"""
        # Search for troubleshooting patterns
        query = f"troubleshooting {failure_type.value} {error_message[:50]}"

        patterns = self.pattern_store.search(
            query=query,
            max_results=5,
            method='hybrid'
        )

        return patterns

    def _determine_priority(
        self, failure_type: FailureType, failure: FailureDetails
    ) -> Priority:
        """Determine fix priority"""
        # Critical errors block everything
        if failure_type in [FailureType.SYNTAX_ERROR, FailureType.IMPORT_ERROR]:
            return Priority.CRITICAL

        # High priority for common runtime errors
        if failure_type in [FailureType.NAME_ERROR, FailureType.ATTRIBUTE_ERROR]:
            return Priority.HIGH

        # Medium for logic errors
        if failure_type == FailureType.ASSERTION_ERROR:
            return Priority.MEDIUM

        return Priority.LOW

    def _generate_specific_fix(
        self, failure: FailureDetails, failure_type: FailureType
    ) -> str:
        """Generate specific fix description"""
        if failure_type == FailureType.IMPORT_ERROR:
            # Try to extract package name
            match = re.search(r"No module named '(\w+)'", failure.error_message)
            if match:
                package = match.group(1)
                return f"Install missing package: pip install {package}"

        elif failure_type == FailureType.NAME_ERROR:
            # Try to extract variable name
            match = re.search(r"name '(\w+)' is not defined", failure.error_message)
            if match:
                var_name = match.group(1)
                return f"Define variable '{var_name}' before use or check spelling"

        elif failure_type == FailureType.ATTRIBUTE_ERROR:
            # Try to extract attribute
            match = re.search(r"has no attribute '(\w+)'", failure.error_message)
            if match:
                attr = match.group(1)
                return f"Add attribute '{attr}' to class or check spelling"

        # Fallback to template
        template = self.FIX_TEMPLATES.get(failure_type, {})
        return template.get('suggestions', ['Review and fix'])[0]

    def _prepare_code_changes(
        self, failure: FailureDetails, code_files: Dict[str, str]
    ) -> List[Dict]:
        """Prepare suggested code changes"""
        changes = []

        # If we have stack trace info, suggest changes
        if failure.stack_trace and failure.failing_file in code_files:
            file_content = code_files[failure.failing_file]
            lines = file_content.split('\n')

            if 0 <= failure.failing_line - 1 < len(lines):
                old_line = lines[failure.failing_line - 1]

                # Suggest fix based on failure type
                new_line = self._suggest_line_fix(old_line, failure.failure_type)

                if new_line != old_line:
                    changes.append({
                        'file': failure.failing_file,
                        'line': failure.failing_line,
                        'old': old_line,
                        'new': new_line
                    })

        return changes

    def _suggest_line_fix(self, line: str, failure_type: FailureType) -> str:
        """Suggest fix for a specific line"""
        # This is a simplified implementation
        # A full implementation would use AST parsing and more sophisticated analysis

        if failure_type == FailureType.IMPORT_ERROR:
            # Suggest adding import (placeholder)
            return line  # TODO: Implement smart import suggestion

        elif failure_type == FailureType.SYNTAX_ERROR:
            # Try to fix common syntax errors
            # Remove trailing commas, fix brackets, etc.
            return line  # TODO: Implement syntax fix

        return line

    def _calculate_confidence(
        self,
        failure_type: FailureType,
        patterns: List[Dict],
        code_changes: List[Dict]
    ) -> float:
        """Calculate confidence in fix suggestion"""
        confidence = 0.5  # Base confidence

        # Higher confidence for well-known error types
        if failure_type in self.FIX_TEMPLATES:
            confidence += 0.2

        # Higher confidence if we have relevant patterns
        if patterns:
            confidence += min(0.2, len(patterns) * 0.05)

        # Higher confidence if we can suggest specific code changes
        if code_changes:
            confidence += 0.1

        return min(1.0, confidence)

    def _generate_explanation(
        self, failure: FailureDetails, failure_type: FailureType
    ) -> str:
        """Generate human-readable explanation"""
        explanation = f"The test '{failure.test_name}' failed with a {failure_type.value}. "

        if failure.stack_trace:
            frame = failure.stack_trace[-1]
            explanation += f"The error occurred in {frame.file_path} at line {frame.line_number} "
            explanation += f"in function '{frame.function_name}'. "

        explanation += failure.error_message[:200]

        return explanation

    def _analyze_security_failures(
        self, scan_result: ScanResult, code_files: Dict[str, str]
    ) -> List[FixSuggestion]:
        """Analyze security vulnerabilities"""
        suggestions = []

        for vuln in scan_result.vulnerabilities:
            # Skip low severity issues for now
            if vuln.severity.value in ['info', 'low']:
                continue

            suggestion = FixSuggestion(
                failure_type=FailureType.SECURITY_VULNERABILITY,
                root_cause=vuln.description,
                suggested_fix=vuln.recommendation,
                code_changes=[{
                    'file': vuln.file_path,
                    'line': vuln.line_number,
                    'old': '# Security issue',
                    'new': f'# {vuln.recommendation}'
                }],
                relevant_patterns=['Security.md', 'OWASP.md'],
                priority=Priority.CRITICAL if vuln.severity.value == 'critical' else Priority.HIGH,
                confidence=0.8,
                explanation=f"Security vulnerability: {vuln.description}"
            )

            suggestions.append(suggestion)

        return suggestions

    def _analyze_performance_failures(
        self, results: List[BenchmarkResult], code_files: Dict[str, str]
    ) -> List[FixSuggestion]:
        """Analyze performance issues"""
        suggestions = []

        for result in results:
            if not result.passed:
                # Performance threshold violated
                for violation in result.threshold_violations:
                    suggestion = FixSuggestion(
                        failure_type=FailureType.PERFORMANCE_DEGRADATION,
                        root_cause=violation,
                        suggested_fix=self._suggest_performance_fix(violation),
                        code_changes=[],
                        relevant_patterns=['Performance.md'],
                        priority=Priority.MEDIUM,
                        confidence=0.6,
                        explanation=f"Performance issue in {result.name}: {violation}"
                    )

                    suggestions.append(suggestion)

        return suggestions

    def _suggest_performance_fix(self, violation: str) -> str:
        """Suggest fix for performance violation"""
        if 'response time' in violation.lower():
            return "Optimize algorithm, add caching, or reduce database queries"
        elif 'throughput' in violation.lower():
            return "Optimize resource usage, add parallelization, or scale horizontally"
        elif 'memory' in violation.lower():
            return "Reduce memory usage, fix memory leaks, or optimize data structures"
        elif 'cpu' in violation.lower():
            return "Optimize CPU-intensive operations or use more efficient algorithms"
        else:
            return "Review and optimize code for better performance"

    def close(self):
        """Close pattern store"""
        if self.pattern_store:
            self.pattern_store.close()
