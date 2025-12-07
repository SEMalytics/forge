# CLAUDE.md - Forge Project Development Standards

This document defines coding standards, architectural patterns, and development practices for the Forge AI Development Orchestration System.

---

## Project Context

**Forge** is an AI-powered development orchestration system that transforms natural language project descriptions into production-ready code through a 6-layer architecture integrating:
- KnowledgeForge 3.2 patterns (28 reference files)
- Compound Engineering multi-agent review system
- Flexible code generation backends (CodeGen API, Claude Code)

**Project Structure:**
```
forge-build/
├── forge/                      # Working directory (YOUR CODE HERE)
├── knowledgeforge-patterns/    # Reference: 28 KF 3.2 files (READ-ONLY)
└── compound-engineering/       # Reference: CE plugin (READ-ONLY)
```

**Always work from:** `forge/` directory  
**Reference patterns at:** `../knowledgeforge-patterns/`  
**Reference CE plugin at:** `../compound-engineering/`

---

## Python Stack Preferences

### Version Requirements
- **Python:** 3.11+ (primary), 3.8+ supported
- **Reason:** Modern type hints, performance improvements, better asyncio

### Core Libraries

**Testing & Quality:**
- `pytest` - Testing framework (with pytest-cov for coverage)
- `black` - Code formatting (non-negotiable)
- `isort` - Import sorting
- `mypy` - Static type checking
- `ruff` - Fast linting (replacing pylint for speed)

**Production Dependencies:**
- `click` - CLI framework
- `rich` - Terminal formatting and progress bars
- `pydantic` - Data validation and settings
- `anthropic` - Claude API client
- `httpx` - Async HTTP client
- `requests` - Sync HTTP fallback
- `gitpython` - Git operations
- `sentence-transformers` - Embeddings
- `tenacity` - Retry logic
- `docker` - Container management
- `pyyaml` - Configuration

### Forbidden Patterns
- ❌ Python 2 patterns (`imp`, `__future__` imports)
- ❌ `eval()` or `exec()` (security risk)
- ❌ Missing type hints on public functions
- ❌ Missing docstrings on public APIs
- ❌ Mutable default arguments
- ❌ Bare `except:` clauses

---

## Universal Coding Principles

### Architecture Patterns ✅

**SOLID Principles:**
1. **Single Responsibility** - Each module/class has one reason to change
2. **Open/Closed** - Open for extension, closed for modification
3. **Liskov Substitution** - Subtypes must be substitutable
4. **Interface Segregation** - Many specific interfaces > one general
5. **Dependency Injection** - Depend on abstractions, not concretions

**Additional Patterns:**
- **DRY (Don't Repeat Yourself)** - Extract common logic
- **KISS (Keep It Simple)** - Simplest solution that works
- **YAGNI (You Aren't Gonna Need It)** - Don't add until needed
- **Separation of Concerns** - Clear boundaries between components
- **Composition over Inheritance** - Prefer composition
- **Fail Fast** - Detect and report errors immediately
- **Defensive Programming** - Validate inputs, handle edge cases

### Anti-Patterns ❌

**Avoid:**
- God objects/functions (>300 lines, >10 responsibilities)
- Copy-paste programming (extract to functions)
- Magic numbers/strings (use constants)
- Deep nesting (>3 levels - extract functions)
- Tight coupling (use dependency injection)
- Global state abuse (pass dependencies explicitly)
- Silent failures (log errors, raise exceptions)
- Premature optimization (profile first)

---

## Forge-Specific Standards

### Module Organization

```python
"""
Module docstring explaining purpose.

References KnowledgeForge patterns:
- Pattern files used (e.g., 00_KB3_Core.md)
- Integration patterns
- Design decisions

Example:
    Basic usage example here
"""

from typing import List, Dict, Optional  # Standard library
import asyncio                            # Standard library
from pathlib import Path                  # Standard library

from anthropic import Anthropic           # Third-party
import click                              # Third-party
from rich.console import Console          # Third-party

from forge.core.config import ForgeConfig # Local imports last
from forge.utils.logger import get_logger # Local imports last

logger = get_logger(__name__)
```

### Type Hints - REQUIRED

```python
# ✅ CORRECT - Full type annotations
def search_patterns(
    query: str,
    max_results: int = 10,
    method: str = 'hybrid'
) -> List[Dict[str, str]]:
    """
    Search KnowledgeForge patterns.
    
    Args:
        query: Search query string
        max_results: Maximum results to return (default: 10)
        method: Search method - 'keyword', 'semantic', or 'hybrid'
    
    Returns:
        List of pattern dictionaries with 'filename', 'title', 'content'
    
    Raises:
        ValueError: If method is invalid
    """
    pass

# ❌ WRONG - Missing type hints
def search_patterns(query, max_results=10):
    pass
```

### Docstring Standards

Use **Google-style** docstrings:

```python
def decompose_project(
    description: str,
    tech_stack: List[str],
    use_ce: bool = True
) -> List[Task]:
    """
    Break project into optimal tasks using KF patterns.
    
    Applies patterns from:
    - 02_Workflows_Orchestration.md (task coordination)
    - 00_KB3_ImplementationGuide.md (best practices)
    
    Args:
        description: Natural language project description
        tech_stack: List of technologies (e.g., ['python', 'fastapi'])
        use_ce: Whether to use Compound Engineering (default: True)
    
    Returns:
        List of Task objects with dependencies and KF patterns
    
    Raises:
        ValueError: If description is empty
        TimeoutError: If CE plugin times out
    
    Example:
        >>> decomposer = TaskDecomposer(pattern_store)
        >>> tasks = decomposer.decompose(
        ...     "Build REST API",
        ...     tech_stack=['python', 'fastapi']
        ... )
        >>> len(tasks)
        5
    """
    pass
```

### Error Handling

**Use specific exceptions:**

```python
# ✅ CORRECT - Specific exceptions with context
from forge.utils.errors import (
    PatternNotFoundError,
    CompoundEngineeringError,
    GenerationError
)

def load_pattern(filename: str) -> str:
    """Load KF pattern file."""
    pattern_path = Path(f"../knowledgeforge-patterns/{filename}")
    
    if not pattern_path.exists():
        raise PatternNotFoundError(
            f"Pattern file not found: {filename}\n"
            f"Expected location: {pattern_path}\n"
            f"Available patterns: {list_available_patterns()}"
        )
    
    try:
        return pattern_path.read_text()
    except Exception as e:
        logger.error(f"Failed to read pattern {filename}: {e}")
        raise PatternNotFoundError(f"Cannot read {filename}: {e}") from e

# ❌ WRONG - Generic exception, no context
def load_pattern(filename):
    try:
        return open(filename).read()
    except:
        raise Exception("Failed")
```

**Never silence errors:**

```python
# ✅ CORRECT - Log and re-raise or handle appropriately
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    # Either re-raise...
    raise
    # ...or handle gracefully with fallback
    result = fallback_operation()

# ❌ WRONG - Silent failure
try:
    risky_operation()
except:
    pass
```

### KnowledgeForge Pattern Integration

**Always reference KF patterns:**

```python
class PatternStore:
    """
    Hybrid pattern storage with FTS5 + embeddings.
    
    Implementation follows patterns from:
    - 01_Core_DataTransfer.md (compression and chunking)
    - 00_KB3_Fundamentals.md (workflow-first architecture)
    
    Pattern files are loaded from: ../knowledgeforge-patterns/
    """
    
    def __init__(self, db_path: str = ".forge/patterns.db"):
        self.patterns_dir = Path("../knowledgeforge-patterns")
        
        # Validate KF patterns are available
        if not self.patterns_dir.exists():
            raise FileNotFoundError(
                f"KnowledgeForge patterns not found at {self.patterns_dir}\n"
                f"Setup: cp /mnt/project/*.md ../knowledgeforge-patterns/"
            )
```

**Apply patterns in implementation:**

```python
class TaskDecomposer:
    """
    Task decomposition using KF orchestration patterns.
    
    Follows 02_Workflows_Orchestration.md patterns:
    - Sequential dependency chains
    - Parallel execution opportunities
    - Checkpoint-based recovery
    """
    
    def _identify_parallel_tasks(self, tasks: List[Task]) -> List[List[Task]]:
        """
        Identify tasks that can run in parallel.
        
        Pattern: Workflow Orchestration (02_Workflows_Orchestration.md)
        - Tasks with no shared dependencies can run in parallel
        - Respects dependency graph topology
        """
        # Implementation following KF patterns
        pass
```

### Asynchronous Code

**Use async/await for I/O operations:**

```python
# ✅ CORRECT - Async for I/O-bound operations
async def generate_code(
    self,
    task: Task,
    context: GenerationContext
) -> GenerationResult:
    """Generate code using CodeGen API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            self.api_url,
            json=self._build_request(task, context),
            timeout=300.0
        )
        return self._parse_response(response)

# Use in orchestrator
async def execute_tasks(tasks: List[Task]) -> List[GenerationResult]:
    """Execute tasks in parallel."""
    return await asyncio.gather(*[
        generate_code(task) for task in tasks
        if not task.dependencies
    ])
```

### Configuration Management

**Use layered configuration:**

```python
from pydantic import BaseModel, Field
from typing import Optional
import os

class GeneratorConfig(BaseModel):
    """Generator configuration with validation."""
    
    backend: str = Field(
        default="codegen_api",
        description="Backend: 'codegen_api' or 'claude_code'"
    )
    api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("CODEGEN_API_KEY"),
        description="API key (from env: CODEGEN_API_KEY)"
    )
    timeout: int = Field(
        default=300,
        gt=0,
        description="Request timeout in seconds"
    )
    
    class Config:
        env_prefix = "FORGE_GENERATOR_"
        validate_assignment = True
```

### Logging Standards

```python
import logging
from rich.logging import RichHandler

# Configure at module level
logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False):
    """Configure logging with Rich handler."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

# Use structured logging
logger.info("Starting task decomposition", extra={
    "project_id": project.id,
    "task_count": len(tasks)
})

logger.error(
    "Generation failed",
    exc_info=True,
    extra={"task_id": task.id, "backend": backend}
)
```

---

## Testing Standards

### Test Coverage Requirements

- **Minimum coverage:** 80% across all modules
- **Critical paths:** 100% coverage (core orchestration, state management)
- **Unit tests:** Every public function
- **Integration tests:** Component interactions
- **End-to-end tests:** Complete workflows

### Test Organization

```python
# tests/test_pattern_store.py
import pytest
from pathlib import Path
from forge.knowledgeforge.pattern_store import PatternStore

@pytest.fixture
def pattern_store():
    """Create test pattern store with test data."""
    # Use temporary database
    store = PatternStore(db_path=":memory:")
    return store

class TestPatternStore:
    """Tests for PatternStore hybrid search."""
    
    def test_search_keyword_returns_results(self, pattern_store):
        """Test keyword search finds relevant patterns."""
        # Arrange
        query = "orchestration workflow"
        
        # Act
        results = pattern_store.search(query, max_results=5)
        
        # Assert
        assert len(results) > 0
        assert all('filename' in r for r in results)
        assert any('orchestration' in r['title'].lower() for r in results)
    
    def test_search_semantic_finds_similar(self, pattern_store):
        """Test semantic search finds conceptually similar patterns."""
        # Arrange
        query = "coordinating multiple AI agents"
        
        # Act
        results = pattern_store.search(query, max_results=5)
        
        # Assert
        assert len(results) > 0
        # Should find agent coordination patterns
        assert any('agent' in r['filename'].lower() for r in results)
    
    @pytest.mark.parametrize("invalid_query", ["", "   ", None])
    def test_search_validates_input(self, pattern_store, invalid_query):
        """Test search validates query input."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            pattern_store.search(invalid_query)
```

### Test Naming Convention

```python
# Pattern: test_{method_name}_{scenario}_{expected_outcome}

def test_decompose_simple_project_returns_tasks():
    """Test decomposition of simple project returns task list."""
    pass

def test_decompose_with_invalid_description_raises_error():
    """Test decomposition with empty description raises ValueError."""
    pass

def test_decompose_large_project_creates_parallel_tasks():
    """Test large project creates tasks with parallel execution."""
    pass
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch, AsyncMock

@pytest.mark.asyncio
async def test_generate_code_calls_api():
    """Test code generation makes API request."""
    # Arrange
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.json.return_value = {
        'output': '## File: test.py\n```python\npass\n```',
        'tokens_used': 150
    }
    mock_client.post.return_value = mock_response
    
    # Act
    with patch('httpx.AsyncClient', return_value=mock_client):
        generator = CodeGenAPIGenerator(api_key="test", org_id="test")
        result = await generator.generate(test_context)
    
    # Assert
    assert result.success
    assert 'test.py' in result.files
    mock_client.post.assert_called_once()
```

---

## Code Quality Automation

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: ["--fix"]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### pyproject.toml Configuration

```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true

[tool.ruff]
line-length = 100
target-version = "py311"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=forge",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
    "-v"
]
```

---

## Security Principles

### Input Validation

```python
from pydantic import BaseModel, validator, Field

class ProjectRequest(BaseModel):
    """Validated project creation request."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10)
    tech_stack: List[str] = Field(default_factory=list, max_items=20)
    
    @validator('name')
    def validate_name(cls, v):
        """Validate project name is safe."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError(
                "Project name must be alphanumeric with - or _ only"
            )
        return v.lower()
    
    @validator('tech_stack')
    def validate_tech_stack(cls, v):
        """Validate tech stack items."""
        allowed = {'python', 'javascript', 'go', 'rust', 'java', 'typescript'}
        for item in v:
            if item.lower() not in allowed:
                raise ValueError(f"Unknown technology: {item}")
        return [item.lower() for item in v]
```

### Secret Management

```python
import os
from typing import Optional

# ✅ CORRECT - Environment variables, never hardcoded
class ForgeConfig:
    @property
    def anthropic_api_key(self) -> Optional[str]:
        """Get Anthropic API key from environment."""
        key = os.getenv('ANTHROPIC_API_KEY')
        if key:
            # Validate format without exposing value
            if not key.startswith('sk-ant-'):
                raise ValueError("Invalid Anthropic API key format")
        return key

# ❌ WRONG - Hardcoded secrets
API_KEY = "sk-ant-api03-xxxxx"  # NEVER DO THIS
```

### Safe Command Execution

```python
import subprocess
from typing import List

# ✅ CORRECT - List arguments, timeout, validation
def run_git_command(args: List[str], timeout: int = 30) -> str:
    """Run git command safely."""
    # Validate command
    if not args or args[0] != 'git':
        raise ValueError("Only git commands allowed")
    
    # Use list arguments (prevents shell injection)
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True
    )
    return result.stdout

# ❌ WRONG - Shell=True is dangerous
subprocess.run(f"git {user_input}", shell=True)  # NEVER DO THIS
```

---

## Performance Guidelines

### Profile Before Optimizing

```python
import cProfile
import pstats
from functools import wraps

def profile_function(func):
    """Decorator to profile function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 functions
        
        return result
    return wrapper

@profile_function
def expensive_operation():
    """Profile this to find bottlenecks."""
    pass
```

### Efficient Data Structures

```python
# ✅ CORRECT - Use appropriate data structures
from collections import defaultdict, deque

# Fast lookups
pattern_index: Dict[str, Pattern] = {}  # O(1) lookup

# Fast insertions at both ends
task_queue: deque[Task] = deque()

# Group by key efficiently
tasks_by_priority: defaultdict[int, List[Task]] = defaultdict(list)

# ❌ WRONG - Inefficient for use case
def find_task(tasks: List[Task], task_id: str) -> Optional[Task]:
    for task in tasks:  # O(n) lookup when dict would be O(1)
        if task.id == task_id:
            return task
```

### Caching

```python
from functools import lru_cache
from typing import List, Dict

# Cache expensive pattern searches
@lru_cache(maxsize=128)
def search_patterns(query: str, max_results: int) -> tuple:
    """Search with LRU cache for repeated queries."""
    results = expensive_search(query, max_results)
    return tuple(results)  # Must be immutable for caching

# Cache property computations
from functools import cached_property

class Project:
    @cached_property
    def dependency_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph once, cache result."""
        return self._build_dependency_graph()
```

---

## Git Commit Standards

### Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(pattern-store): add semantic search with embeddings

Implement hybrid search combining FTS5 keyword search with
sentence-transformers semantic search. Patterns are indexed
on first run with embeddings cached in SQLite.

Follows patterns from:
- 01_Core_DataTransfer.md (efficient storage)
- 00_KB3_Fundamentals.md (search optimization)

Closes #12
```

```
fix(decomposition): handle circular dependencies in task graph

Added topological sort validation to detect cycles before
execution. Raises CircularDependencyError with clear path
description.

Fixes #24
```

---

## Documentation Standards

### README Structure

```markdown
# Forge - AI Development Orchestration

One-line description.

## Quick Start

5-minute setup guide.

## Features

What it does.

## Installation

Step-by-step.

## Usage

Common commands with examples.

## Architecture

High-level overview.

## Development

How to contribute.

## License

MIT
```

### API Documentation

Use **Sphinx** with Google-style docstrings:

```python
def decompose_project(
    description: str,
    tech_stack: List[str],
    use_ce: bool = True
) -> List[Task]:
    """
    Break project into optimal tasks using KF patterns.
    
    This function applies patterns from KnowledgeForge 3.2 to intelligently
    decompose a project description into executable tasks with proper
    dependency ordering and parallel execution opportunities.
    
    Args:
        description: Natural language project description
        tech_stack: List of technologies (e.g., ['python', 'fastapi'])
        use_ce: Whether to use Compound Engineering for planning
    
    Returns:
        List of Task objects with:
            - Unique task IDs
            - Dependency relationships
            - Relevant KF patterns
            - Estimated durations
    
    Raises:
        ValueError: If description is empty or invalid
        TimeoutError: If Compound Engineering plugin times out
        PatternNotFoundError: If required patterns are missing
    
    Example:
        >>> from forge.layers.decomposition import TaskDecomposer
        >>> from forge.knowledgeforge import PatternStore
        >>> 
        >>> store = PatternStore()
        >>> decomposer = TaskDecomposer(store)
        >>> 
        >>> tasks = decomposer.decompose(
        ...     "Build REST API for todo app",
        ...     tech_stack=['python', 'fastapi', 'postgresql']
        ... )
        >>> 
        >>> for task in tasks:
        ...     print(f"{task.id}: {task.title}")
        task-001: Database Schema Design
        task-002: API Endpoint Implementation
        task-003: Authentication System
    
    Note:
        Compound Engineering integration is optional. If CE plugin is
        unavailable, falls back to basic pattern-based decomposition.
    
    See Also:
        - :class:`Task`: Task data structure
        - :class:`PatternStore`: Pattern search and retrieval
        - :func:`build_dependency_graph`: Dependency graph builder
    """
    pass
```

---

## Code Review Checklist

Before submitting code:

### Functionality
- [ ] Code works as intended
- [ ] Edge cases handled
- [ ] Errors handled gracefully
- [ ] No silent failures

### Quality
- [ ] Type hints on all public functions
- [ ] Docstrings on all public APIs
- [ ] No code duplication
- [ ] No magic numbers/strings
- [ ] Maximum 3 levels of nesting
- [ ] Functions < 50 lines
- [ ] Classes < 300 lines

### Testing
- [ ] Unit tests for all functions
- [ ] Integration tests for components
- [ ] >80% code coverage
- [ ] All tests pass
- [ ] Tests are descriptive

### Documentation
- [ ] README updated if needed
- [ ] API docs updated
- [ ] Comments explain "why" not "what"
- [ ] KF patterns referenced

### Style
- [ ] Black formatted
- [ ] isort sorted imports
- [ ] Ruff linting passes
- [ ] mypy type checking passes
- [ ] No unused imports

### Security
- [ ] Input validation
- [ ] No hardcoded secrets
- [ ] Safe command execution
- [ ] Dependencies audited

### Performance
- [ ] Appropriate data structures
- [ ] No premature optimization
- [ ] Caching where appropriate
- [ ] Profiled if performance-critical

### Git
- [ ] Conventional commit format
- [ ] Clear commit message
- [ ] Logical commit granularity
- [ ] No merge conflicts

---

## Quick Reference

### Import Order (isort)
1. Standard library
2. Third-party packages
3. Local imports

### Line Length
- **Maximum:** 100 characters
- **Docstrings:** 80 characters

### Naming Conventions
- **Modules:** `lowercase_with_underscores.py`
- **Classes:** `PascalCase`
- **Functions:** `lowercase_with_underscores`
- **Constants:** `UPPERCASE_WITH_UNDERSCORES`
- **Private:** `_leading_underscore`

### Files to Ignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.pytest_cache/
.coverage
htmlcov/

# Forge
.forge/
*.db
*.db-journal

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

---

## Claude Code Best Practices

When using Claude Code to build Forge, follow these proven patterns:

### Setup & Configuration

**CLAUDE.md Optimization:**
- This file is automatically pulled into context on every Claude Code session
- Keep it concise and actionable (Claude Code reads it every time)
- Use `#` key during sessions to add useful patterns Claude discovers
- Include common bash commands, core utilities, and testing instructions
- Document unexpected behaviors or project-specific quirks

**Tool Permissions:**
- Use `/permissions` command to allowlist safe tools:
  - `Edit` - Allow file edits without prompting
  - `Bash(git commit:*)` - Allow git commits
  - `Bash(pytest:*)` - Allow running tests
- Check `.claude/settings.json` into git for team consistency
- For Forge: allowlist poetry, pytest, git, and forge CLI commands

**Environment Setup:**
```bash
# Install gh CLI for GitHub operations
brew install gh
gh auth login

# Configure MCP servers in .mcp.json (check into git)
# Example: Puppeteer for UI testing, if needed
```

### Recommended Workflows for Forge

**1. Explore, Plan, Code, Commit** (Best for new features)
```
You: Read the pattern store implementation and the KF patterns 
     about data storage. Don't write any code yet.

Claude: [reads files and patterns]

You: Think hard about the best approach to add semantic search 
     with embeddings. Make a detailed plan.

Claude: [uses extended thinking, creates plan]

You: Looks good. Implement the plan, running tests after each 
     major component.

Claude: [implements, tests, iterates]

You: Commit the changes with a conventional commit message 
     and create a PR.
```

**Key tips:**
- Use "think", "think hard", "think harder", or "ultrathink" for increasing reasoning depth
- Explicitly tell Claude not to code during exploration phase
- Ask for plans before implementation on complex features
- Use subagents for verification: "Use a subagent to verify this approach against KF patterns"

**2. Test-Driven Development** (Best for well-defined features)
```
You: We're doing TDD. Write tests for the pattern search functionality 
     based on these requirements: [paste requirements]. Don't create 
     any implementation code or mocks yet.

Claude: [writes tests]

You: Run the tests and confirm they fail. Don't implement anything.

Claude: [runs tests, shows failures]

You: Good. Commit these tests.

Claude: [commits]

You: Now implement code to pass the tests. Don't modify the tests. 
     Keep iterating until all tests pass.

Claude: [implements, runs tests, fixes, iterates until passing]

You: Use a subagent to verify the implementation isn't overfitting 
     to the tests.

Claude: [verification]

You: Commit the implementation.
```

**3. Visual Development** (For CLI output/UI work)
```
You: Here's a mock of how the progress bar should look: [paste image]
     Implement it, take a screenshot of the result, and iterate 
     until it matches the mock.

Claude: [implements, screenshots, compares, iterates]
```

**4. Safe YOLO Mode** (For routine tasks)
```bash
# For fixing lint errors or generating boilerplate
# Run in Docker container without internet for safety
claude --dangerously-skip-permissions \
  -p "Fix all ruff linting errors in src/forge/"

# Or use checked-in allowlist for semi-automated workflows
claude -p "Run black on all Python files and commit if changed"
```

### Forge-Specific Patterns

**Git Operations:**
```
# Claude handles most git workflows
You: What changes were made to pattern_store.py since v1.0?
You: Write a commit message for these changes
You: Resolve this rebase conflict
You: Create a PR titled "feat(search): add semantic search"
```

**Codebase Q&A:**
```
# Great for onboarding or understanding
You: How does the pattern store indexing work?
You: What edge cases does the state manager handle?
You: Why are we using FTS5 instead of regular SQL queries?
You: Show me all places we use the CompoundEngineering client
```

**GitHub Integration:**
```
You: Create an issue for adding Docker support to the test runner
You: Fix the comments on PR #42 and push changes
You: Categorize all open issues by adding appropriate labels
You: Fix the failing CI build on the main branch
```

**Working with KF Patterns:**
```
# Reference patterns explicitly
You: Read 01_Core_DataTransfer.md and implement compression 
     following those patterns exactly.

You: Apply the testing patterns from 04_TestScenarios.md to 
     create comprehensive tests for the generator factory.

You: Check if our implementation follows the architecture 
     described in 00_KB3_Core.md. List any deviations.
```

### Optimization Techniques

**Be Specific:**
```
❌ Poor: "add tests for foo.py"
✅ Good: "Write comprehensive pytest tests for foo.py covering:
         - Happy path with valid input
         - Edge cases (empty input, max size, special characters)
         - Error conditions (missing dependencies, timeouts)
         - Use fixtures for pattern_store, don't use mocks
         - Aim for >90% coverage"
```

**Use Images:**
```
# Screenshot architectural diagrams
You: Here's the Forge architecture diagram [paste image]. 
     Verify our current implementation matches this design.

# Share error screenshots
You: Here's the error I'm getting [paste screenshot]. 
     Debug and fix it.
```

**File References:**
```
# Use tab-completion to reference files
You: Read <tab>src/forge/core/config.py<tab> and explain 
     the configuration hierarchy.

# Reference multiple files
You: Compare the implementations in pattern_store.py and 
     search_engine.py. Are they consistent?
```

**URLs:**
```
You: Read https://docs.anthropic.com/claude/reference and 
     verify our client implementation is correct.

# Add domains to allowlist to avoid repeated permission prompts
/permissions add https://docs.anthropic.com
```

**Course Correction:**
```
# If Claude starts going wrong direction:
Press ESC to interrupt
"Stop. Let's take a different approach. Instead of..."

# Or go back and try again:
Double-tap ESC to edit previous prompt
Edit your instruction
Press Enter to retry with better guidance
```

**Context Management:**
```
# Long sessions fill context with irrelevant content
# Reset between distinct tasks
/clear

# Then start fresh on next task
You: Now let's work on the deployment layer...
```

**Complex Workflows - Use Checklists:**
```
You: Create a checklist in TASKS.md of all files that need 
     to be migrated from the old architecture to new. Then 
     work through them one by one, checking each off as you 
     complete and verify it.

# Claude creates checklist, then:
# - Migrates file
# - Tests it
# - Checks it off
# - Moves to next
# This prevents forgetting steps in complex workflows
```

**Data Input Methods:**
```bash
# Pipe data to Claude
cat error.log | claude -p "Analyze these errors and suggest fixes"

# Or tell Claude to fetch
You: Run the tests and analyze any failures

# Or paste directly
You: Here's the stack trace: [paste]

# Or give file path
You: Analyze the performance data in ../benchmarks/results.json
```

### Multi-Claude Workflows

**Code + Review Pattern:**
```bash
# Terminal 1: Implementation
cd forge
claude
You: Implement semantic search with embeddings

# Terminal 2: Review
cd forge
claude
You: Review the changes in src/forge/knowledgeforge/. 
     Check against patterns in ../knowledgeforge-patterns/
     Focus on: correctness, KF pattern compliance, performance

# Terminal 1: Revisions
You: Address the review comments about caching strategy
```

**Parallel Development with Git Worktrees:**
```bash
# Create worktrees for independent tasks
git worktree add ../forge-testing feature/test-framework
git worktree add ../forge-deployment feature/deployment
git worktree add ../forge-docs feature/documentation

# Terminal 1
cd ../forge-testing
claude
You: Implement the Docker test runner

# Terminal 2  
cd ../forge-deployment
claude
You: Add fly.io deployment configuration

# Terminal 3
cd ../forge-docs
claude
You: Write comprehensive API documentation

# Clean up when done
git worktree remove ../forge-testing
```

**Headless Automation:**
```bash
# Batch processing example
# 1. Generate task list
claude -p "List all Python files in src/ that need docstrings" > tasks.txt

# 2. Process each task
while read file; do
  claude -p "Add comprehensive Google-style docstrings to $file" \
    --allowedTools Edit Bash(pytest:*) Bash(git:*)
done < tasks.txt

# 3. Review and commit
claude -p "Review all docstring changes, run tests, commit if passing"

# CI Integration
# .github/workflows/claude-review.yml
- name: Claude Code Review
  run: |
    claude -p "Review PR changes for: type hints, docstrings, \
               KF pattern compliance. Output issues in JSON" \
      --output-format stream-json \
      | jq '.issues[]' \
      | gh pr comment --body-file -
```

### Custom Slash Commands for Forge

Create `.claude/commands/` with Forge-specific workflows:

**`.claude/commands/fix-issue.md`:**
```markdown
Analyze and fix GitHub issue: $ARGUMENTS

Steps:
1. Use `gh issue view $ARGUMENTS` for details
2. Search codebase for relevant files
3. Check KF patterns in ../knowledgeforge-patterns/
4. Implement fix following patterns
5. Write tests (pytest, >80% coverage)
6. Run: black, isort, mypy, ruff
7. Run tests: pytest -v
8. Commit with conventional format
9. Push and create PR referencing issue

KF Pattern Compliance:
- Reference relevant patterns in commit message
- Follow architecture from 00_KB3_Core.md
- Use patterns from appropriate modules
```

**`.claude/commands/new-module.md`:**
```markdown
Create new module: $ARGUMENTS

Template:
1. Read CLAUDE.md for project standards
2. Create module structure:
   - src/forge/{module}/
   - tests/test_{module}/
   - Add to pyproject.toml if needed
3. Follow patterns from similar modules
4. Include:
   - Type hints on all functions
   - Google-style docstrings
   - Comprehensive tests (>80% coverage)
   - KF pattern references in docstrings
5. Run quality checks:
   - black, isort, mypy, ruff
   - pytest with coverage
6. Commit: "feat({module}): $ARGUMENTS"
```

### Session Management Tips

**Start Sessions Right:**
```
# Good first message sets context
You: I'm working on the Forge pattern store. Reference files 
     are in ../knowledgeforge-patterns/. We follow the standards 
     in CLAUDE.md. I need to add semantic search functionality.

# vs just:
You: add semantic search  # Missing context
```

**Use Auto-Accept Wisely:**
```
# Shift+Tab toggles auto-accept mode
# Good for: routine refactoring, formatting, simple fixes
# Bad for: new features, complex logic, anything risky

# Recommended: Start with manual approval, then auto-accept 
# once you see Claude is on the right track
```

**Interrupt Strategically:**
```
# ESC during tool calls: Stop current action
# ESC during thinking: Stop and redirect
# ESC during edits: Prevent unwanted changes

# Use when:
# - Claude is editing wrong files
# - Approach is incorrect
# - You realize requirements changed
```

### Forge Build Sessions - Practical Examples

**Phase 1 Example Session:**
```
You: I'm building Phase 1 of Forge. Reference the complete 
     implementation plan at ../forge_complete_implementation_plan.md
     and follow standards in CLAUDE.md.
     
     First, think hard about the best order to implement these 
     components. Don't write code yet.

Claude: [analyzes, creates implementation order]

You: Good plan. Start with the configuration system. Create 
     src/forge/core/config.py following the spec exactly, 
     including full type hints and docstrings.

Claude: [implements]

You: Run mypy and fix any type errors. Then write comprehensive 
     tests in tests/test_config.py.

Claude: [tests]

You: All tests passing? Good. Commit this with a proper 
     conventional commit message.

Claude: [commits]

You: Now move to pattern_store.py. This is complex, so use a 
     subagent to verify your approach matches the spec before 
     implementing.
```

**Debugging Example:**
```
You: The pattern store search is returning no results. Debug this:
     1. Check if patterns are being indexed
     2. Verify FTS5 table is created correctly  
     3. Test both keyword and semantic search separately
     4. Add debug logging to see what's happening
     
     Use subagents to investigate different hypotheses in parallel.

Claude: [systematic debugging]

You: Found it! Fix the issue and add a test to prevent regression.
```

**Refactoring Example:**
```
You: The generator abstraction is getting complex. Refactor it:
     1. Read current implementation
     2. Read 00_KB3_Core.md for architecture guidance
     3. Think hard about a cleaner design
     4. Create plan with before/after structure
     5. Don't implement until I approve the plan

Claude: [analysis and plan]

You: Good plan but keep the factory pattern. Implement the 
     refactoring, running tests after each change to ensure 
     nothing breaks.

Claude: [refactors incrementally with tests]
```

---

## Resources

### Official Documentation
- **Python:** https://docs.python.org/3/
- **pytest:** https://docs.pytest.org/
- **Click:** https://click.palletsprojects.com/
- **Pydantic:** https://docs.pydantic.dev/

### Forge Documentation
- `forge_master_setup_guide.md` - Setup and session guide
- `forge_quickstart_simplified.md` - Build instructions
- `forge_complete_implementation_plan.md` - Technical spec

### KnowledgeForge Patterns
- All 28 patterns in: `../knowledgeforge-patterns/`
- Core architecture: `00_KB3_Core.md`
- Implementation guide: `00_KB3_ImplementationGuide.md`

### Tools
- **Black:** Automatic code formatting
- **isort:** Import sorting
- **mypy:** Static type checking
- **Ruff:** Fast Python linter
- **pytest:** Testing framework

---

**Remember:** Quality over speed. Write code that your future self will thank you for.
