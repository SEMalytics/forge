"""
Docker-isolated test execution with multi-framework support

Runs tests in isolated Docker containers for:
- Reproducible environments
- Dependency isolation
- Security boundaries
- Multi-version testing
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import subprocess

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class DockerTestError(ForgeError):
    """Errors during Docker test execution"""
    pass


class SupportedFramework(Enum):
    """Supported test frameworks"""
    PYTEST = "pytest"
    JEST = "jest"
    RSPEC = "rspec"
    GO_TEST = "go test"
    CARGO_TEST = "cargo test"
    MOCHA = "mocha"
    UNITTEST = "unittest"


@dataclass
class ExecutionResult:
    """Test execution result"""
    framework: SupportedFramework
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0
    coverage_percent: Optional[float] = None
    output: str = ""
    errors: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Total test count"""
        return self.passed + self.failed + self.skipped

    @property
    def success(self) -> bool:
        """Whether all tests passed"""
        return self.failed == 0 and self.total > 0


@dataclass
class DockerConfig:
    """Docker container configuration"""
    image: str
    work_dir: str = "/workspace"
    memory_limit: str = "512m"
    cpu_limit: str = "1.0"
    timeout_seconds: int = 600
    network_mode: str = "none"  # Isolated by default
    env_vars: Dict[str, str] = field(default_factory=dict)


class DockerTestRunner:
    """
    Runs tests in isolated Docker containers.

    Features:
    - Multi-framework support (pytest, jest, rspec, go test, cargo test)
    - Automatic framework detection
    - Coverage analysis
    - Performance metrics
    - Resource limits
    - Network isolation
    """

    # Default Docker images by framework
    DEFAULT_IMAGES = {
        SupportedFramework.PYTEST: "python:3.11-slim",
        SupportedFramework.UNITTEST: "python:3.11-slim",
        SupportedFramework.JEST: "node:18-alpine",
        SupportedFramework.MOCHA: "node:18-alpine",
        SupportedFramework.RSPEC: "ruby:3.2-slim",
        SupportedFramework.GO_TEST: "golang:1.21-alpine",
        SupportedFramework.CARGO_TEST: "rust:1.75-slim",
    }

    # Test commands by framework
    TEST_COMMANDS = {
        SupportedFramework.PYTEST: "pytest --cov --cov-report=json -v",
        SupportedFramework.UNITTEST: "python -m unittest discover -v",
        SupportedFramework.JEST: "npm test -- --coverage --json",
        SupportedFramework.MOCHA: "npm test",
        SupportedFramework.RSPEC: "bundle exec rspec --format json",
        SupportedFramework.GO_TEST: "go test -v -coverprofile=coverage.out ./...",
        SupportedFramework.CARGO_TEST: "cargo test --verbose",
    }

    def __init__(
        self,
        docker_available: bool = True,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize Docker test runner.

        Args:
            docker_available: Whether Docker is available
            cache_dir: Directory for caching Docker images
        """
        self.docker_available = docker_available and self._check_docker()
        self.cache_dir = cache_dir or Path.home() / ".forge" / "docker-cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized DockerTestRunner (docker={self.docker_available})")

    def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    async def run_tests(
        self,
        test_files: Dict[str, str],
        source_files: Dict[str, str],
        framework: Optional[SupportedFramework] = None,
        docker_config: Optional[DockerConfig] = None
    ) -> ExecutionResult:
        """
        Run tests in Docker container.

        Args:
            test_files: Dictionary mapping test file paths to content
            source_files: Dictionary mapping source file paths to content
            framework: Test framework (auto-detected if None)
            docker_config: Docker configuration

        Returns:
            Test execution result

        Raises:
            DockerTestError: If test execution fails
        """
        logger.info(f"Running tests for {len(test_files)} test files")

        # Detect framework if not specified
        if framework is None:
            framework = self._detect_framework(test_files)
            logger.info(f"Detected framework: {framework.value}")

        # Use default config if not provided
        if docker_config is None:
            docker_config = DockerConfig(
                image=self.DEFAULT_IMAGES[framework]
            )

        # Create temporary workspace
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Write files to workspace
            self._write_files(workspace, test_files, "tests")
            self._write_files(workspace, source_files, "src")

            # Create framework-specific setup
            self._setup_framework(workspace, framework)

            # Run tests
            if self.docker_available:
                result = await self._run_in_docker(
                    workspace, framework, docker_config
                )
            else:
                logger.warning("Docker not available, running tests locally")
                result = await self._run_locally(workspace, framework)

            return result

    def _detect_framework(self, test_files: Dict[str, str]) -> SupportedFramework:
        """Detect test framework from file extensions and content"""
        # Check file extensions
        for file_path in test_files.keys():
            path = Path(file_path)

            if path.suffix == '.py':
                # Check for pytest or unittest
                content = test_files[file_path]
                if 'import pytest' in content or 'def test_' in content:
                    return SupportedFramework.PYTEST
                elif 'import unittest' in content:
                    return SupportedFramework.UNITTEST

            elif path.suffix in ('.js', '.ts', '.jsx', '.tsx'):
                content = test_files[file_path]
                if 'jest' in content or "describe(" in content:
                    return SupportedFramework.JEST
                elif 'mocha' in content:
                    return SupportedFramework.MOCHA

            elif path.suffix == '.rb':
                return SupportedFramework.RSPEC

            elif path.suffix == '.go' and '_test' in path.stem:
                return SupportedFramework.GO_TEST

            elif path.suffix == '.rs':
                return SupportedFramework.CARGO_TEST

        # Default to pytest
        return SupportedFramework.PYTEST

    def _write_files(
        self, workspace: Path, files: Dict[str, str], subdir: str
    ):
        """Write files to workspace directory"""
        target_dir = workspace / subdir
        target_dir.mkdir(parents=True, exist_ok=True)

        for file_path, content in files.items():
            # Create file path
            path = target_dir / Path(file_path).name
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            path.write_text(content)

        logger.debug(f"Wrote {len(files)} files to {subdir}/")

    def _setup_framework(self, workspace: Path, framework: SupportedFramework):
        """Create framework-specific configuration files"""
        if framework == SupportedFramework.PYTEST:
            # Create pytest.ini
            (workspace / "pytest.ini").write_text("""[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
""")

            # Create requirements.txt
            (workspace / "requirements.txt").write_text("""pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
""")

        elif framework in (SupportedFramework.JEST, SupportedFramework.MOCHA):
            # Create package.json
            (workspace / "package.json").write_text(json.dumps({
                "name": "test-project",
                "version": "1.0.0",
                "scripts": {
                    "test": "jest" if framework == SupportedFramework.JEST else "mocha"
                },
                "devDependencies": {
                    "jest": "^29.0.0" if framework == SupportedFramework.JEST else None,
                    "mocha": "^10.0.0" if framework == SupportedFramework.MOCHA else None,
                    "@types/jest": "^29.0.0" if framework == SupportedFramework.JEST else None
                }
            }, indent=2))

            if framework == SupportedFramework.JEST:
                # Create jest.config.js
                (workspace / "jest.config.js").write_text("""module.exports = {
  testMatch: ['**/tests/**/*.test.js'],
  collectCoverage: true,
  coverageDirectory: 'coverage',
};
""")

        elif framework == SupportedFramework.RSPEC:
            # Create Gemfile
            (workspace / "Gemfile").write_text("""source 'https://rubygems.org'

gem 'rspec', '~> 3.12'
gem 'simplecov', '~> 0.22'
""")

            # Create .rspec
            (workspace / ".rspec").write_text("""--format documentation
--color
--require spec_helper
""")

        elif framework == SupportedFramework.GO_TEST:
            # Create go.mod
            (workspace / "go.mod").write_text("""module testproject

go 1.21
""")

        elif framework == SupportedFramework.CARGO_TEST:
            # Create Cargo.toml
            (workspace / "Cargo.toml").write_text("""[package]
name = "testproject"
version = "0.1.0"
edition = "2021"

[dependencies]
""")

    async def _run_in_docker(
        self,
        workspace: Path,
        framework: SupportedFramework,
        config: DockerConfig
    ) -> ExecutionResult:
        """Run tests in Docker container"""
        import time

        start_time = time.time()

        # Build command
        cmd = self._build_docker_command(workspace, framework, config)

        logger.debug(f"Running Docker command: {' '.join(cmd)}")

        try:
            # Run container
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=config.timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                raise DockerTestError(f"Test execution timeout after {config.timeout_seconds}s")

            duration = time.time() - start_time

            # Parse output
            output = stdout.decode('utf-8', errors='replace')
            errors = stderr.decode('utf-8', errors='replace')

            result = self._parse_test_output(
                framework, output, errors, duration
            )

            return result

        except Exception as e:
            logger.error(f"Docker test execution failed: {e}")
            raise DockerTestError(f"Test execution failed: {e}")

    def _build_docker_command(
        self,
        workspace: Path,
        framework: SupportedFramework,
        config: DockerConfig
    ) -> List[str]:
        """Build Docker run command"""
        cmd = [
            "docker", "run",
            "--rm",
            "-v", f"{workspace.absolute()}:{config.work_dir}",
            "-w", config.work_dir,
            "--memory", config.memory_limit,
            "--cpus", config.cpu_limit,
            "--network", config.network_mode,
        ]

        # Add environment variables
        for key, value in config.env_vars.items():
            cmd.extend(["-e", f"{key}={value}"])

        # Add image
        cmd.append(config.image)

        # Add test command
        test_cmd = self._get_test_command(framework)
        cmd.extend(["sh", "-c", test_cmd])

        return cmd

    def _get_test_command(self, framework: SupportedFramework) -> str:
        """Get test command with setup"""
        base_cmd = self.TEST_COMMANDS[framework]

        if framework == SupportedFramework.PYTEST:
            return f"pip install -q -r requirements.txt && {base_cmd}"

        elif framework in (SupportedFramework.JEST, SupportedFramework.MOCHA):
            return f"npm install --silent && {base_cmd}"

        elif framework == SupportedFramework.RSPEC:
            return f"bundle install --quiet && {base_cmd}"

        elif framework == SupportedFramework.GO_TEST:
            return f"go mod download && {base_cmd}"

        elif framework == SupportedFramework.CARGO_TEST:
            return base_cmd

        return base_cmd

    async def _run_locally(
        self, workspace: Path, framework: SupportedFramework
    ) -> ExecutionResult:
        """Run tests locally without Docker"""
        import time

        start_time = time.time()

        # Get test command
        cmd_str = self._get_test_command(framework)

        try:
            process = await asyncio.create_subprocess_shell(
                cmd_str,
                cwd=workspace,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            duration = time.time() - start_time

            output = stdout.decode('utf-8', errors='replace')
            errors = stderr.decode('utf-8', errors='replace')

            result = self._parse_test_output(
                framework, output, errors, duration
            )

            return result

        except Exception as e:
            logger.error(f"Local test execution failed: {e}")
            raise DockerTestError(f"Test execution failed: {e}")

    def _parse_test_output(
        self,
        framework: SupportedFramework,
        stdout: str,
        stderr: str,
        duration: float
    ) -> ExecutionResult:
        """Parse test output to extract results"""
        result = ExecutionResult(
            framework=framework,
            duration_seconds=duration,
            output=stdout
        )

        if framework == SupportedFramework.PYTEST:
            result = self._parse_pytest_output(stdout, stderr, duration)

        elif framework == SupportedFramework.JEST:
            result = self._parse_jest_output(stdout, stderr, duration)

        elif framework == SupportedFramework.RSPEC:
            result = self._parse_rspec_output(stdout, stderr, duration)

        elif framework == SupportedFramework.GO_TEST:
            result = self._parse_go_output(stdout, stderr, duration)

        elif framework == SupportedFramework.CARGO_TEST:
            result = self._parse_cargo_output(stdout, stderr, duration)

        # Add errors if any
        if stderr:
            result.errors.append(stderr)

        return result

    def _parse_pytest_output(
        self, stdout: str, stderr: str, duration: float
    ) -> ExecutionResult:
        """Parse pytest output"""
        result = ExecutionResult(
            framework=SupportedFramework.PYTEST,
            duration_seconds=duration,
            output=stdout
        )

        # Parse test counts (e.g., "5 passed, 2 failed in 1.23s")
        import re

        passed_match = re.search(r'(\d+) passed', stdout)
        failed_match = re.search(r'(\d+) failed', stdout)
        skipped_match = re.search(r'(\d+) skipped', stdout)

        if passed_match:
            result.passed = int(passed_match.group(1))
        if failed_match:
            result.failed = int(failed_match.group(1))
        if skipped_match:
            result.skipped = int(skipped_match.group(1))

        # Parse coverage (look for coverage.json or percentage in output)
        coverage_match = re.search(r'TOTAL.*?(\d+)%', stdout)
        if coverage_match:
            result.coverage_percent = float(coverage_match.group(1))

        if stderr:
            result.errors.append(stderr)

        return result

    def _parse_jest_output(
        self, stdout: str, stderr: str, duration: float
    ) -> ExecutionResult:
        """Parse Jest output"""
        result = ExecutionResult(
            framework=SupportedFramework.JEST,
            duration_seconds=duration,
            output=stdout
        )

        # Parse test summary
        import re

        tests_match = re.search(r'Tests:\s+(\d+) passed.*?(\d+) total', stdout)
        if tests_match:
            result.passed = int(tests_match.group(1))
            total = int(tests_match.group(2))
            result.failed = total - result.passed

        # Parse coverage
        coverage_match = re.search(r'All files.*?(\d+\.?\d*)%', stdout)
        if coverage_match:
            result.coverage_percent = float(coverage_match.group(1))

        return result

    def _parse_rspec_output(
        self, stdout: str, stderr: str, duration: float
    ) -> ExecutionResult:
        """Parse RSpec output"""
        result = ExecutionResult(
            framework=SupportedFramework.RSPEC,
            duration_seconds=duration,
            output=stdout
        )

        # Parse summary (e.g., "5 examples, 2 failures")
        import re

        examples_match = re.search(r'(\d+) examples?, (\d+) failures?', stdout)
        if examples_match:
            total = int(examples_match.group(1))
            failed = int(examples_match.group(2))
            result.passed = total - failed
            result.failed = failed

        return result

    def _parse_go_output(
        self, stdout: str, stderr: str, duration: float
    ) -> ExecutionResult:
        """Parse Go test output"""
        result = ExecutionResult(
            framework=SupportedFramework.GO_TEST,
            duration_seconds=duration,
            output=stdout
        )

        # Count PASS/FAIL lines
        passed = stdout.count('--- PASS:')
        failed = stdout.count('--- FAIL:')

        result.passed = passed
        result.failed = failed

        # Parse coverage
        import re
        coverage_match = re.search(r'coverage: ([\d.]+)% of statements', stdout)
        if coverage_match:
            result.coverage_percent = float(coverage_match.group(1))

        return result

    def _parse_cargo_output(
        self, stdout: str, stderr: str, duration: float
    ) -> ExecutionResult:
        """Parse Cargo test output"""
        result = ExecutionResult(
            framework=SupportedFramework.CARGO_TEST,
            duration_seconds=duration,
            output=stdout
        )

        # Parse test result line (e.g., "test result: ok. 5 passed; 0 failed")
        import re

        result_match = re.search(r'test result:.*?(\d+) passed; (\d+) failed', stdout)
        if result_match:
            result.passed = int(result_match.group(1))
            result.failed = int(result_match.group(2))

        return result

    def cleanup(self):
        """Clean up Docker resources"""
        if not self.docker_available:
            return

        try:
            # Remove stopped containers
            subprocess.run(
                ["docker", "container", "prune", "-f"],
                capture_output=True,
                timeout=30
            )
        except Exception as e:
            logger.warning(f"Failed to cleanup Docker resources: {e}")
