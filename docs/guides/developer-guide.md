# Developer Guide

Complete guide for developers contributing to Forge or building on top of it.

## Development Setup

### Prerequisites

- Python 3.11+
- Poetry 2.2+
- Git
- Code editor (VS Code, PyCharm, etc.)

### Initial Setup

```bash
# Clone repository (or navigate to forge directory)
cd /path/to/forge

# Install dependencies including dev tools
poetry install

# Activate virtual environment
poetry shell

# Verify installation
forge --version
pytest -v
```

### Development Tools

```bash
# Formatting
poetry run black src/forge tests

# Linting
poetry run ruff check src/forge

# Type checking
poetry run mypy src/forge

# Testing
poetry run pytest -v --cov=src/forge

# All checks
poetry run black src/forge tests && \
  poetry run ruff check src/forge && \
  poetry run mypy src/forge && \
  poetry run pytest -v
```

## Project Structure

```
forge/
├── src/forge/              # Source code
│   ├── core/              # Core functionality
│   ├── knowledgeforge/    # Pattern system
│   ├── cli/               # CLI interface
│   └── utils/             # Utilities
├── tests/                 # Test suite
├── docs/                  # Documentation
├── pyproject.toml         # Dependencies
└── README.md              # Main readme
```

## Code Style

### Python Style Guide

Follow PEP 8 with these specifics:

**Line Length:**
```python
# Maximum 100 characters
MAX_LINE_LENGTH = 100
```

**Imports:**
```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import click
from rich.console import Console

# Local
from forge.core.config import ForgeConfig
from forge.utils.logger import logger
```

**Type Hints:**
```python
def create_project(
    name: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None
) -> ProjectState:
    """Create new project with metadata."""
    pass
```

**Docstrings:**
```python
def search_patterns(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search KnowledgeForge patterns.

    Args:
        query: Search query string
        max_results: Maximum results to return

    Returns:
        List of pattern dictionaries

    Raises:
        PatternStoreError: If search fails

    Example:
        >>> patterns = search_patterns("orchestration", 5)
        >>> len(patterns) <= 5
        True
    """
    pass
```

### Formatting

Use Black for code formatting:

```bash
# Format all code
poetry run black src/forge tests

# Check without modifying
poetry run black --check src/forge

# Format specific file
poetry run black src/forge/core/config.py
```

### Linting

Use Ruff for fast linting:

```bash
# Check all code
poetry run ruff check src/forge

# Auto-fix issues
poetry run ruff check --fix src/forge

# Check specific file
poetry run ruff check src/forge/core/orchestrator.py
```

### Type Checking

Use mypy for type checking:

```bash
# Check all code
poetry run mypy src/forge

# Strict mode
poetry run mypy --strict src/forge

# Specific file
poetry run mypy src/forge/core/state_manager.py
```

## Testing

### Writing Tests

**Test Structure:**
```python
# tests/test_module.py
import pytest
from forge.module import Class

@pytest.fixture
def instance():
    """Create instance for testing."""
    return Class()

def test_method_success(instance):
    """Test method with valid input."""
    # Arrange
    input_data = "test"

    # Act
    result = instance.method(input_data)

    # Assert
    assert result is not None
    assert isinstance(result, str)

def test_method_error(instance):
    """Test method error handling."""
    with pytest.raises(ValueError):
        instance.method(None)
```

**Fixtures:**
```python
@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database."""
    db_path = tmp_path / "test.db"
    return StateManager(str(db_path))

@pytest.fixture
def sample_patterns(tmp_path):
    """Create sample pattern files."""
    patterns_dir = tmp_path / "patterns"
    patterns_dir.mkdir()

    pattern = patterns_dir / "test.md"
    pattern.write_text("# Test Pattern\nContent")

    return patterns_dir
```

### Running Tests

```bash
# All tests
poetry run pytest

# Verbose output
poetry run pytest -v

# Specific test file
poetry run pytest tests/test_config.py

# Specific test
poetry run pytest tests/test_config.py::test_default_config

# With coverage
poetry run pytest --cov=src/forge --cov-report=html

# Failed tests only
poetry run pytest --lf

# Stop on first failure
poetry run pytest -x
```

### Test Coverage

```bash
# Generate coverage report
poetry run pytest --cov=src/forge --cov-report=html

# View report
open htmlcov/index.html

# Check coverage threshold
poetry run pytest --cov=src/forge --cov-fail-under=80
```

## Adding New Features

### 1. Plan the Feature

**Questions to answer:**
- What problem does this solve?
- How does it fit into the architecture?
- What are the dependencies?
- What tests are needed?
- What documentation is required?

### 2. Create a Branch

```bash
# Create feature branch
git checkout -b feature/my-new-feature

# Create fix branch
git checkout -b fix/bug-description
```

### 3. Implement the Feature

**Example: Adding a new CLI command**

```python
# src/forge/cli/main.py

@cli.command()
@click.argument('input')
@click.option('--output', '-o', help='Output file')
@click.pass_context
def new_command(ctx, input, output):
    """New command description."""
    orchestrator = ctx.obj['orchestrator']

    try:
        # Implementation
        result = orchestrator.do_something(input)

        # Output
        console.print(f"✓ Success: {result}")

        if output:
            Path(output).write_text(result)

    except Exception as e:
        print_error(f"Failed: {e}")
        sys.exit(1)
```

### 4. Add Tests

```python
# tests/test_new_feature.py

def test_new_command_success():
    """Test new command with valid input."""
    # Implementation
    pass

def test_new_command_error():
    """Test new command error handling."""
    # Implementation
    pass
```

### 5. Update Documentation

```markdown
# docs/guides/cli-reference.md

### new-command

Description of new command.

**Usage:**
\`\`\`bash
forge new-command INPUT [OPTIONS]
\`\`\`

**Examples:**
\`\`\`bash
forge new-command "test"
\`\`\`
```

### 6. Test Thoroughly

```bash
# Run tests
poetry run pytest -v

# Check coverage
poetry run pytest --cov=src/forge

# Manual testing
poetry run forge new-command "test"
```

### 7. Submit Changes

```bash
# Ensure tests pass
poetry run pytest -v

# Format code
poetry run black src/forge tests

# Lint code
poetry run ruff check src/forge

# Commit changes
git add .
git commit -m "feat: add new command for X

- Implement new_command CLI command
- Add tests with >80% coverage
- Update CLI reference documentation"

# Push branch
git push origin feature/my-new-feature
```

## Code Organization

### Adding a New Module

```bash
# Create module file
touch src/forge/module_name.py

# Add to package
# Update src/forge/__init__.py if needed

# Create tests
touch tests/test_module_name.py
```

### Module Template

```python
"""
Module description.

This module provides...
"""

from typing import Optional, List, Dict
import logging

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class ModuleName:
    """Module description."""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize module.

        Args:
            config: Optional configuration
        """
        self.config = config or {}
        logger.info("Initialized ModuleName")

    def method_name(self, param: str) -> str:
        """
        Method description.

        Args:
            param: Parameter description

        Returns:
            Return value description

        Raises:
            ForgeError: If operation fails
        """
        try:
            # Implementation
            result = param.upper()
            logger.debug(f"Processed: {result}")
            return result
        except Exception as e:
            logger.error(f"Method failed: {e}")
            raise ForgeError(f"Operation failed: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Cleanup
        pass
```

## Working with Dependencies

### Adding Dependencies

```bash
# Add production dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Add with version constraint
poetry add "package-name>=1.0,<2.0"

# Update dependencies
poetry update

# Show outdated
poetry show --outdated
```

### Dependency Guidelines

**DO:**
- Use well-maintained packages
- Pin major versions
- Check license compatibility
- Review security advisories

**DON'T:**
- Add unnecessary dependencies
- Use deprecated packages
- Mix incompatible licenses
- Ignore security warnings

## Debugging

### Using Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

### Logging

```python
from forge.utils.logger import logger

# Debug level
logger.debug("Detailed information")

# Info level
logger.info("General information")

# Warning level
logger.warning("Warning message")

# Error level
logger.error("Error message")

# With exception info
try:
    dangerous_operation()
except Exception as e:
    logger.exception("Operation failed")
```

### Debug Configuration

```yaml
# forge.yaml
log_level: DEBUG  # Enable debug logging
log_file: debug.log
```

## Performance Profiling

### Time Profiling

```python
import time

start = time.time()
# Operation
duration = time.time() - start
print(f"Took {duration:.2f}s")
```

### Memory Profiling

```bash
# Install memory profiler
poetry add --group dev memory-profiler

# Profile script
python -m memory_profiler script.py
```

### Database Profiling

```python
import sqlite3

# Enable query logging
conn.set_trace_callback(print)

# Analyze query plan
cursor.execute("EXPLAIN QUERY PLAN SELECT ...")
```

## Best Practices

### Error Handling

```python
# Specific exceptions
try:
    operation()
except PatternStoreError as e:
    logger.error(f"Pattern error: {e}")
    raise
except ConfigurationError as e:
    logger.error(f"Config error: {e}")
    sys.exit(1)
except Exception as e:
    logger.exception("Unexpected error")
    raise ForgeError(f"Operation failed: {e}")
```

### Resource Management

```python
# Use context managers
with Orchestrator() as orch:
    project = orch.create_project("Name", "Desc")

# Or explicit cleanup
orch = Orchestrator()
try:
    project = orch.create_project("Name", "Desc")
finally:
    orch.close()
```

### Configuration

```python
# Load from environment
config = ForgeConfig.load()

# Don't hard-code values
# BAD:
api_key = "hardcoded-key"

# GOOD:
api_key = config.generator.api_key
```

### Testing

```python
# Use fixtures
@pytest.fixture
def temp_db(tmp_path):
    db = StateManager(str(tmp_path / "test.db"))
    yield db
    db.close()

# Test edge cases
def test_empty_input():
    assert process("") == ""

def test_none_input():
    with pytest.raises(ValueError):
        process(None)
```

## Documentation

### Adding Documentation

```bash
# Add guide
touch docs/guides/new-guide.md

# Add API docs
touch docs/api/new-module.md

# Update index
# Edit docs/README.md
```

### Documentation Style

```markdown
# Page Title

Brief introduction.

## Section

Content with examples.

### Subsection

More detailed content.

**Usage:**
\`\`\`bash
forge command
\`\`\`

**Example:**
\`\`\`python
from forge import Module
module = Module()
\`\`\`

## See Also

- [Related Guide](other-guide.md)
```

## Git Workflow

### Commit Messages

Follow Conventional Commits:

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

**Examples:**
```
feat(cli): add search command

- Implement pattern search CLI command
- Add tests with 90% coverage
- Update documentation

Closes #123

fix(state): handle missing project gracefully

- Return None instead of raising
- Add test for missing project
- Update error messages

docs(api): add examples for orchestrator

- Add usage examples
- Update API reference
- Fix typos
```

### Branch Naming

```
feature/description
fix/bug-description
docs/documentation-update
refactor/code-improvement
```

## Continuous Integration

### Pre-commit Checks

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
poetry run black src/forge tests
poetry run ruff check src/forge
poetry run pytest -v
EOF

chmod +x .git/hooks/pre-commit
```

### CI/CD Pipeline (future)

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest -v
```

## Release Process

### Version Bumping

```bash
# Update version in pyproject.toml
# Update CHANGELOG.md

# Commit
git commit -m "chore: bump version to 1.1.0"

# Tag
git tag -a v1.1.0 -m "Version 1.1.0"

# Push
git push origin main --tags
```

### Building

```bash
# Build package
poetry build

# Check dist/
ls dist/
# forge-1.0.0-py3-none-any.whl
# forge-1.0.0.tar.gz
```

## See Also

- [Architecture Overview](../architecture/overview.md)
- [API Reference](../api/overview.md)
- [Testing Guide](testing.md)
- [Troubleshooting](troubleshooting.md)
