# **CLAUDE.md \- Forge Project**

**Forge** is an AI development orchestration system that transforms natural language descriptions into production-ready code through intelligent planning, parallel generation, automated testing, and multi-agent review.

---

## **Project Overview**

### **What is Forge?**

Forge is a CLI tool that orchestrates the entire software development process:

1. **Conversational Planning** \- Natural language requirements gathering  
2. **Task Decomposition** \- Breaks projects into optimal, parallelizable tasks  
3. **Code Generation** \- Generates code using CodeGen API or Claude Code  
4. **Automated Testing** \- Creates and runs comprehensive test suites  
5. **Expert Review** \- 12-agent review system (needs 8/12 approval)  
6. **Iterative Refinement** \- Auto-fixes until all tests pass  
7. **Git Integration** \- Conventional commits and PR creation  
8. **Deployment** \- Multi-platform deployment configs

### **Architecture**

```
forge-build/
├── forge/                          # Main implementation (THIS REPO)
│   ├── src/forge/
│   │   ├── core/                   # Config, state, orchestration
│   │   ├── knowledgeforge/         # Pattern store (FTS5 + embeddings)
│   │   ├── layers/                 # 6 orchestration layers
│   │   ├── generators/             # CodeGen API + Claude Code backends
│   │   ├── integrations/           # CE, Anthropic, GitHub clients
│   │   ├── git/                    # Git operations
│   │   ├── testing/                # Test generation + Docker runner
│   │   ├── cli/                    # Click CLI
│   │   └── utils/                  # Logging, errors, retries
│   ├── knowledgeforge/             # KnowledgeForge 4.0 agent specs (7 files)
│   ├── patterns/                   # Curated operational patterns
│   ├── tests/                      # Comprehensive test suite
│   ├── examples/                   # Example projects
│   ├── pyproject.toml
│   └── CLAUDE.md                   # This file
└── compound-engineering/           # Reference: CE plugin (sibling dir)
```

---

## **CLI Reference**

### **Core Workflow**

```shell
forge doctor                    # Check system dependencies
forge init <name>               # Initialize new project
forge chat                      # Interactive planning session
forge chat --repo /path         # Plan with existing codebase analysis
forge decompose "description"   # Generate task plan
forge build -p <id>             # Build project from plan
forge test -p <id>              # Run comprehensive tests
forge iterate -p <id>           # Auto-fix until tests pass
forge review file <path>        # Multi-agent code review (needs 8/12 approval)
forge deploy -p <id> --platform flyio|vercel|aws|docker|k8s
forge pr -p <id>                # Create pull request
```

### **Project Management**

```shell
forge status [project-id]       # Show project status or list all
forge stats -p <id>             # Project statistics
forge analyze [repo-path]       # Analyze codebase structure
forge search "query"            # Search KnowledgeForge patterns
```

### **Advanced Commands**

```shell
# Build options
forge build -p <id> --backend codegen_api|claude_code
forge build -p <id> --parallel --max-parallel 5
forge build -p <id> --force     # Re-run all tasks
forge build -p <id> --no-resume # Start fresh

# Worktrees for parallel execution
forge worktree create task-001 task-002
forge worktree list|status|merge|clean

# Cache management
forge cache stats|list|clear|warm

# Context management (cascading generation info)
forge context show|add|clear|stats

# Metrics and resilience
forge metrics show|cost|performance|export
forge resilience stats|checkpoints|circuits|restore

# Utilities
forge triage -p <id>            # Interactive test failure triage
forge examples                  # List example projects
forge explain <concept>         # Explain Forge concepts
```

---

## **Python Stack Standards**

### **Version Requirements**

* **Python:** 3.11+ (primary), 3.8+ compatible

### **Core Dependencies**

**Essential Libraries:**

```
[tool.poetry.dependencies]
python = "^3.11"
click = "^8.1.0"              # CLI framework
rich = "^13.0.0"              # Terminal formatting
pydantic = "^2.0.0"           # Data validation
anthropic = "^0.18.0"         # Claude API
httpx = "^0.25.0"             # Async HTTP
gitpython = "^3.1.0"          # Git operations
sentence-transformers = "^2.2.0"  # Pattern embeddings
tenacity = "^8.2.0"           # Retry logic
docker = "^7.0.0"             # Container management
pyyaml = "^6.0.0"             # Configuration
```

**Development Tools:**

```
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"             # Testing framework
pytest-cov = "^4.1.0"         # Coverage reports
pytest-asyncio = "^0.21.0"    # Async test support
black = "^23.0.0"             # Code formatting
isort = "^5.12.0"             # Import sorting
mypy = "^1.5.0"               # Static type checking
ruff = "^0.1.0"               # Fast linting (replaces pylint)
```

### **Forbidden Patterns**

**Never use:**

* ❌ Python 2 patterns or imports  
* ❌ `eval()` or `exec()` (security risk)  
* ❌ `imp` module (deprecated)  
* ❌ Missing type hints on public functions  
* ❌ Missing docstrings on public APIs  
* ❌ Mutable default arguments  
* ❌ Bare `except:` clauses

---

## **Code Style Standards**

### **File Organization**

```py
"""
Module docstring explaining purpose.

This module implements [feature] following patterns from:
- KnowledgeForge pattern: 00_KB3_Core.md
- Architecture: 6-layer orchestration

Example:
    Basic usage example
    
    >>> from forge.core.config import ForgeConfig
    >>> config = ForgeConfig.load()
"""

# Standard library imports
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports
import click
from anthropic import Anthropic
from rich.console import Console

# Local imports
from forge.core.config import ForgeConfig
from forge.utils.logger import get_logger

logger = get_logger(__name__)
```

### **Type Hints \- REQUIRED**

All public functions must have complete type annotations with Google-style docstrings.

### **Docstring Standards \- Google Style**

```py
def orchestrate_build(
    project_id: str,
    parallel: bool = True,
    max_workers: int = 5
) -> BuildResult:
    """
    Orchestrate complete project build process.
    
    Coordinates all 6 layers of the Forge pipeline:
    1. Planning - Requirements gathering
    2. Decomposition - Task breakdown
    3. Generation - Parallel code generation
    4. Testing - Automated test suite
    5. Review - Multi-agent validation
    6. Deployment - Platform configuration
    
    Args:
        project_id: Unique project identifier
        parallel: Enable parallel task execution (default: True)
        max_workers: Maximum parallel workers (default: 5)
    
    Returns:
        BuildResult with:
            - success: bool
            - generated_files: Dict[str, str]
            - test_results: TestResults
            - review_status: ReviewStatus
    
    Raises:
        ProjectNotFoundError: If project_id doesn't exist
        BuildFailedError: If build fails after max retries
        
    Example:
        >>> result = orchestrate_build('my-api', parallel=True)
        >>> if result.success:
        ...     print(f"Built {len(result.generated_files)} files")
    
    Note:
        Large projects (>50 tasks) may take several hours.
        Progress is checkpointed for recovery.
    """
    pass
```

### **Naming Conventions**

* **Modules:** `lowercase_with_underscores.py`  
* **Classes:** `PascalCase`  
* **Functions/Methods:** `lowercase_with_underscores`  
* **Constants:** `UPPERCASE_WITH_UNDERSCORES`  
* **Private:** `_leading_underscore`  
* **Protected:** `_single_leading_underscore`  
* **Magic:** `__double_leading_underscore__`

### **Code Organization**

**Maximum Complexity:**

* Functions: **\< 50 lines** (extract helpers if longer)  
* Classes: **\< 300 lines** (split if larger)  
* Nesting depth: **\< 4 levels** (extract functions)  
* Function parameters: **\< 7** (use dataclasses)

---

## **Architecture Patterns**

### **Universal Principles (Applied to Forge)**

**SOLID Principles:**

1. **Single Responsibility** \- Each layer has one purpose  
2. **Open/Closed** \- Plugin architecture for generators  
3. **Liskov Substitution** \- Generator backends are substitutable  
4. **Interface Segregation** \- Clean abstractions (CodeGenerator ABC)  
5. **Dependency Injection** \- Config/dependencies passed explicitly

**Core Patterns:**

* ✅ **DRY** \- Pattern store prevents duplication  
* ✅ **KISS** \- Simple, composable layers  
* ✅ **YAGNI** \- Build what's needed, when needed  
* ✅ **Separation of Concerns** \- 6 distinct layers  
* ✅ **Composition over Inheritance** \- Prefer composition  
* ✅ **Fail Fast** \- Validate early, fail clearly

### **Forge-Specific Patterns**

**1\. Layered Architecture**

```py
# Each layer is independent and testable
class PlanningLayer:
    """Layer 1: Conversational planning."""
    pass

class DecompositionLayer:
    """Layer 2: Task breakdown."""
    pass

class GenerationLayer:
    """Layer 3: Code generation."""
    pass

# Orchestrator coordinates layers
class ForgeOrchestrator:
    def __init__(
        self,
        planning: PlanningLayer,
        decomposition: DecompositionLayer,
        generation: GenerationLayer
    ):
        self.planning = planning
        self.decomposition = decomposition
        self.generation = generation
```

**2\. Plugin Architecture**

```py
# Abstract base class defines interface
class CodeGenerator(ABC):
    @abstractmethod
    async def generate(self, context: GenerationContext) -> GenerationResult:
        """Generate code."""
        pass

# Concrete implementations
class CodeGenAPIGenerator(CodeGenerator):
    """CodeGen API backend."""
    pass

class ClaudeCodeGenerator(CodeGenerator):
    """Claude Code CLI backend."""
    pass

# Factory creates instances
class GeneratorFactory:
    @staticmethod
    def create(backend: GeneratorBackend, **kwargs) -> CodeGenerator:
        """Factory method."""
        pass
```

**3\. State Management with Checkpoints**

```py
# All state is recoverable
class StateManager:
    def checkpoint(self, project_id: str, stage: str, state: Dict):
        """Create recovery checkpoint."""
        pass
    
    def restore(self, project_id: str, checkpoint_id: int) -> Dict:
        """Restore from checkpoint."""
        pass
```

**4\. Pattern-Driven Development**

```py
# Reference KnowledgeForge patterns
class PatternStore:
    """
    Hybrid search over patterns.

    Patterns located at:
    - knowledgeforge/      (KF 4.0 agent specifications)
    - patterns/            (Curated operational patterns)
    Uses FTS5 + sentence-transformers for hybrid search.
    """

    def search(self, query: str, method: str = 'hybrid') -> List[Dict]:
        """Search patterns using keyword + semantic search."""
        pass
```

---

## **Error Handling**

### **Exception Hierarchy**

```py
# Base exception
class ForgeError(Exception):
    """Base exception for all Forge errors."""
    pass

# Specific exceptions
class PatternNotFoundError(ForgeError):
    """KnowledgeForge pattern not found."""
    pass

class GenerationError(ForgeError):
    """Code generation failed."""
    pass

class ReviewFailedError(ForgeError):
    """Multi-agent review rejected code."""
    pass
```

### **Error Handling Pattern**

```py
# ✅ CORRECT - Specific exceptions with context
from forge.utils.errors import PatternNotFoundError
import logging

logger = logging.getLogger(__name__)

def load_pattern(filename: str) -> str:
    """Load pattern file from knowledgeforge/ or patterns/ directory."""
    # Check KF 4.0 specs first, then operational patterns
    search_paths = [
        Path(f"knowledgeforge/{filename}"),
        Path(f"patterns/{filename}"),
    ]

    for pattern_path in search_paths:
        if pattern_path.exists():
            break
    else:
        kf_patterns = list(Path("knowledgeforge").glob("*.md"))
        op_patterns = list(Path("patterns").rglob("*.md"))
        raise PatternNotFoundError(
            f"Pattern not found: {filename}\n"
            f"Searched: {[str(p) for p in search_paths]}\n"
            f"Available: {len(kf_patterns)} KF specs, {len(op_patterns)} patterns"
        )
    
    try:
        return pattern_path.read_text()
    except Exception as e:
        logger.error(f"Failed to read {filename}", exc_info=True)
        raise PatternNotFoundError(f"Cannot read {filename}: {e}") from e

# ❌ WRONG - Silent failure
def load_pattern(filename):
    try:
        return open(filename).read()
    except:
        return None  # Silently fails!
```

---

## **Testing Standards**

### **Coverage Requirements**

* **Minimum:** 80% across all modules  
* **Critical paths:** 90%+ (orchestration, state management, generators)  
* **Target:** 85%+ overall

### **Test Organization**

```py
# tests/test_pattern_store.py
import pytest
from pathlib import Path
from forge.knowledgeforge.pattern_store import PatternStore

@pytest.fixture
def pattern_store():
    """Create test pattern store."""
    # Use in-memory database for tests
    return PatternStore(db_path=":memory:")

@pytest.fixture
def mock_patterns(tmp_path):
    """Create mock KF pattern files."""
    patterns_dir = tmp_path / "patterns"
    patterns_dir.mkdir()
    
    # Create test patterns
    (patterns_dir / "00_KB3_Core.md").write_text("# Core\nTest pattern")
    
    return patterns_dir

class TestPatternStore:
    """Test suite for PatternStore."""
    
    def test_search_finds_relevant_patterns(self, pattern_store):
        """Test hybrid search returns relevant results."""
        # Arrange
        query = "orchestration workflow"
        
        # Act
        results = pattern_store.search(query, max_results=5)
        
        # Assert
        assert len(results) > 0
        assert all('filename' in r for r in results)
        assert any('orchestration' in r['title'].lower() for r in results)
    
    @pytest.mark.asyncio
    async def test_async_search(self, pattern_store):
        """Test async search operations."""
        results = await pattern_store.search_async("async patterns")
        assert isinstance(results, list)
    
    @pytest.mark.parametrize("invalid_query", ["", "   ", None])
    def test_search_validates_input(self, pattern_store, invalid_query):
        """Test search validates query input."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            pattern_store.search(invalid_query)
```

### **Test Naming Convention**

```
test_{method_name}_{scenario}_{expected_outcome}
```

Examples:

* `test_generate_creates_valid_code`  
* `test_generate_with_invalid_spec_raises_error`  
* `test_generate_respects_timeout`  
* `test_generate_retries_on_failure`

---

## **Configuration**

### **Layered Configuration System**

```py
# Supports: global config + project config + env vars
class ForgeConfig:
    """
    Configuration hierarchy:
    1. ~/.forge/config.yaml (global)
    2. ./forge.yaml (project)
    3. Environment variables (highest priority)
    """
    
    @classmethod
    def load(cls) -> "ForgeConfig":
        """Load config with layering."""
        pass
```

### **Example Configuration**

```
# ~/.forge/config.yaml (global)
generator:
  backend: codegen_api
  api_key: ${CODEGEN_API_KEY}  # From env var
  timeout: 300

git:
  author_name: Forge AI
  author_email: forge@ai.dev
  commit_format: conventional

github:
  token: ${GITHUB_TOKEN}

pattern_store:
  path: .forge/patterns.db
  embedding_model: all-MiniLM-L6-v2
```

```
# ./forge.yaml (project-specific)
project:
  name: restaurant-forecasting
  tech_stack:
    - python
    - fastapi
    - postgresql
  
patterns:
  priority:
    - 00_KB3_Security.md
    - 04_TestScenarios.md
    - 01_Core_DataTransfer.md

testing:
  framework: pytest
  coverage_target: 85
  docker_isolation: true
```

---

## **Async/Await Patterns**

```py
# Use async for I/O-bound operations
import asyncio
from typing import List

async def generate_code_parallel(tasks: List[Task]) -> List[GenerationResult]:
    """Generate code for multiple tasks in parallel."""
    async def generate_one(task: Task) -> GenerationResult:
        generator = GeneratorFactory.create(...)
        return await generator.generate(task)
    
    # Execute in parallel
    results = await asyncio.gather(*[
        generate_one(task) for task in tasks
    ])
    
    return results

# Use in sync context
def build_project(tasks: List[Task]) -> List[GenerationResult]:
    """Synchronous wrapper."""
    return asyncio.run(generate_code_parallel(tasks))
```

---

## **Logging Standards**

```py
import logging
from rich.logging import RichHandler

# Configure at module level
logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False):
    """Configure logging with Rich handler."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=True
        )]
    )

# Use structured logging
logger.info(
    "Starting code generation",
    extra={
        "project_id": project.id,
        "task_count": len(tasks),
        "parallel": True
    }
)

# Error logging with context
logger.error(
    "Generation failed",
    exc_info=True,
    extra={
        "task_id": task.id,
        "backend": "codegen_api",
        "retry_count": 3
    }
)
```

---

## **Security Principles**

### **Input Validation**

```py
from pydantic import BaseModel, Field, validator

class ProjectRequest(BaseModel):
    """Validated project creation request."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10)
    tech_stack: List[str] = Field(default_factory=list, max_items=20)
    
    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Ensure safe project name."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Name must be alphanumeric with - or _")
        return v.lower()
```

### **Secret Management**

```py
# ✅ CORRECT - Environment variables only
import os

api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not set")

# ❌ WRONG - Hardcoded secrets
API_KEY = "sk-ant-xxxxx"  # NEVER DO THIS
```

### **Safe Command Execution**

```py
import subprocess
from typing import List

# ✅ CORRECT - List arguments, timeout, validation
def run_git_command(args: List[str], timeout: int = 30) -> str:
    """Run git command safely."""
    if not args or args[0] != 'git':
        raise ValueError("Only git commands allowed")
    
    result = subprocess.run(
        args,  # List, not string
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True
    )
    return result.stdout

# ❌ WRONG - Shell injection vulnerability
subprocess.run(f"git {user_input}", shell=True)  # DANGEROUS
```

---

## **Performance Guidelines**

### **Profiling**

```py
import cProfile
import pstats

def profile_function(func):
    """Decorator to profile function."""
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
        
        return result
    return wrapper

@profile_function
def expensive_operation():
    """Profile this to find bottlenecks."""
    pass
```

### **Caching**

```py
from functools import lru_cache, cached_property

# Cache expensive pattern searches
@lru_cache(maxsize=128)
def search_patterns(query: str, max_results: int) -> tuple:
    """Cached pattern search."""
    results = _do_search(query, max_results)
    return tuple(results)  # Must be immutable

# Cache computed properties
class Project:
    @cached_property
    def dependency_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph once."""
        return self._build_graph()
```

---

## **Git Commit Standards**

### **Conventional Commits**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

* `feat`: New feature  
* `fix`: Bug fix  
* `docs`: Documentation  
* `style`: Formatting  
* `refactor`: Code restructuring  
* `test`: Adding tests  
* `chore`: Maintenance

**Example:**

```
feat(generators): add Claude Code backend support

Implement ClaudeCodeGenerator as alternative to CodeGen API.
Uses subprocess to call claude CLI and parses output.

Features:
- Workspace management
- Specification file generation
- Sequential execution
- Result collection

Closes #42
```

---

## **Code Quality Automation**

### **Pre-commit Configuration**

```
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

### **pyproject.toml**

```
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "W", "F", "I", "B", "C4", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--cov=forge",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
    "-v"
]
```

---

## **Development Workflow**

### **Local Development**

```shell
# Setup
git clone https://github.com/SEMalytics/forge.git
cd forge
poetry install

# Run quality checks
poetry run black src/
poetry run isort src/
poetry run mypy src/
poetry run ruff src/

# Run tests
poetry run pytest -v

# Try CLI
poetry run forge --version
poetry run forge doctor
```

### **Before Committing**

```shell
# Run all checks
poetry run black src/ tests/
poetry run isort src/ tests/
poetry run mypy src/
poetry run ruff check src/ tests/
poetry run pytest --cov=forge --cov-fail-under=80

# Or use pre-commit
pre-commit run --all-files
```

---

## **Quick Reference**

### **Import Order (isort)**

1. Standard library  
2. Third-party packages  
3. Local imports

### **Line Length**

* **Maximum:** 100 characters  
* **Docstrings:** 80 characters

### **File Naming**

* Tests: `test_*.py`  
* Modules: `lowercase_with_underscores.py`  
* Config: `config.py`, `settings.py`

---

## **Resources**

### **Documentation**

* **Python:** https://docs.python.org/3/  
* **pytest:** https://docs.pytest.org/  
* **Click:** https://click.palletsprojects.com/  
* **Pydantic:** https://docs.pydantic.dev/  
* **Anthropic API:** https://docs.anthropic.com/

### **Forge Documentation**

* **README.md** \- Quick start and overview  
* **ARCHITECTURE.md** \- System design  
* **API\_REFERENCE.md** \- Complete API docs  
* **CONTRIBUTING.md** \- Development guide

### **KnowledgeForge 4.0** (Agent Specifications)

Located in: `knowledgeforge/`

* `00_Project_Instructions.md` \- Core behavioral framework
* `01_Navigator_Agent.md` \- Intent routing
* `02_Builder_Agent.md` \- PDIA agent creation method
* `03_Coordination_Patterns.md` \- Multi-agent orchestration
* `04_Specification_Templates.md` \- Reusable specification formats
* `05_Expert_Agent_Example.md` \- Domain specialist pattern
* `06_Quick_Reference.md` \- Quick lookup guide

### **Operational Patterns**

Located in: `patterns/`

* `core/architecture.md` \- Five-layer system architecture
* `core/data-transfer.md` \- Compression, chunking, streaming
* `agents/catalog.md` \- Agent registry and coordination
* `workflows/orchestration.md` \- Master orchestrator pattern
* `testing/scenarios.md` \- Comprehensive test scenarios
* `operations/security.md` \- Authentication, authorization

---

**Remember:** Write code that your future self will thank you for. Clarity \> cleverness.

