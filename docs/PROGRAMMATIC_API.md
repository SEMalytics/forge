# Forge Programmatic API Guide

This guide documents how to access Forge functionality directly via Python imports rather than through the CLI.

## Table of Contents

1. [Directory Structure](#1-directory-structure)
2. [CLI Commands → Functions Mapping](#2-cli-commands--underlying-functions-mapping)
3. [Core Classes & Import Paths](#3-core-classes--direct-import-paths)
4. [Authentication & Configuration](#4-authentication--configuration-requirements)
5. [Complete Usage Example](#5-complete-programmatic-usage-example)
6. [Key Function Signatures](#6-key-function-signatures)
7. [Repository Access](#7-repository-access)
8. [Dependencies](#8-dependencies-for-programmatic-usage)

---

## 1. Directory Structure

```
/Users/dp/Scripts/forge/
├── src/forge/                    # Main source code
│   ├── cli/                      # Click CLI interface
│   │   ├── main.py              # CLI commands (entry point)
│   │   ├── interactive.py       # Interactive chat mode
│   │   └── output.py            # Rich console output helpers
│   │
│   ├── core/                     # Core infrastructure
│   │   ├── config.py            # ForgeConfig (Pydantic models)
│   │   ├── orchestrator.py      # Main Orchestrator class
│   │   ├── state_manager.py     # SQLite state persistence
│   │   ├── session.py           # Session management
│   │   ├── cache.py             # Caching/incremental builds
│   │   ├── context.py           # Context cascading
│   │   ├── streaming.py         # Streaming output
│   │   ├── resilience.py        # Error recovery/retry
│   │   └── metrics.py           # Telemetry/cost tracking
│   │
│   ├── generators/               # Code generation backends
│   │   ├── base.py              # Abstract CodeGenerator class
│   │   ├── factory.py           # GeneratorFactory
│   │   ├── codegen_api.py       # CodeGen API backend
│   │   └── claude_code.py       # Claude Code CLI backend
│   │
│   ├── integrations/             # External API clients
│   │   ├── codegen_client.py    # CodeGenClient (API wrapper)
│   │   ├── codegen_setup.py     # Repository setup utilities
│   │   ├── github_client.py     # GitHub API client
│   │   └── compound_engineering.py  # CE planning client
│   │
│   ├── layers/                   # Orchestration layers
│   │   ├── planning.py          # PlanningAgent (Claude chat)
│   │   ├── decomposition.py     # TaskDecomposer
│   │   ├── generation.py        # GenerationOrchestrator
│   │   ├── testing.py           # Testing orchestration
│   │   ├── review.py            # Review orchestration
│   │   ├── repository_analyzer.py  # Codebase analysis
│   │   ├── triage.py            # Interactive fix approval
│   │   └── failure_analyzer.py  # Failure analysis
│   │
│   ├── review/                   # Multi-agent review system
│   │   ├── agents.py            # 12 expert reviewer agents
│   │   └── panel.py             # ReviewPanel voting system
│   │
│   ├── knowledgeforge/           # Pattern store
│   │   ├── pattern_store.py     # SQLite + FTS5 patterns
│   │   ├── search_engine.py     # Hybrid search
│   │   ├── embeddings.py        # Sentence transformers
│   │   └── cache.py             # Pattern cache
│   │
│   ├── git/                      # Git operations
│   │   ├── repository.py        # Git repository wrapper
│   │   ├── commits.py           # Commit management
│   │   └── worktree.py          # Git worktree support
│   │
│   ├── testing/                  # Test infrastructure
│   │   ├── generator.py         # Test generation
│   │   ├── docker_runner.py     # Docker isolation
│   │   ├── security_scanner.py  # Security testing
│   │   └── performance.py       # Performance testing
│   │
│   └── utils/                    # Utilities
│       ├── logger.py            # Logging setup
│       ├── errors.py            # Exception classes
│       └── git_utils.py         # Git helper functions
│
├── knowledgeforge/               # KnowledgeForge 4.0 specs
├── patterns/                     # Operational patterns
├── tests/                        # Test suite
└── pyproject.toml               # Poetry config
```

---

## 2. CLI Commands → Underlying Functions Mapping

| CLI Command | Underlying Function/Class | Module |
|-------------|---------------------------|--------|
| `forge doctor` | Various checks inline | `cli/main.py:doctor()` |
| `forge init <name>` | `Orchestrator.create_project()` | `core/orchestrator.py` |
| `forge status [id]` | `Orchestrator.get_project()`, `StateManager.list_projects()` | `core/orchestrator.py`, `core/state_manager.py` |
| `forge search <query>` | `Orchestrator.search_patterns()` | `core/orchestrator.py` |
| `forge info` | `Orchestrator.get_system_status()` | `core/orchestrator.py` |
| `forge config` | `ForgeConfig.create_default()` | `core/config.py` |
| `forge analyze <path>` | `RepositoryAnalyzer.analyze()` | `layers/repository_analyzer.py` |
| `forge chat` | `simple_chat()` → `PlanningAgent.chat()` | `cli/interactive.py`, `layers/planning.py` |
| `forge decompose` | `TaskDecomposer.decompose()` | `layers/decomposition.py` |
| `forge build -p <id>` | `GenerationOrchestrator.generate_project()` | `layers/generation.py` |
| `forge test -p <id>` | `TestingOrchestrator` | `layers/testing.py` |

---

## 3. Core Classes & Direct Import Paths

### Configuration

```python
from forge.core.config import ForgeConfig, GeneratorConfig, GitConfig

# Load configuration (auto-merges global + project + env vars)
config = ForgeConfig.load()

# Access settings
print(config.generator.backend)  # "codegen_api"
print(config.generator.timeout)  # 7200
```

### Orchestrator

```python
from forge.core.orchestrator import Orchestrator
from forge.core.config import ForgeConfig

config = ForgeConfig.load()
orchestrator = Orchestrator(config)

# Create project
project = orchestrator.create_project(
    name="my-project",
    description="Build a REST API"
)

# Search patterns
results = orchestrator.search_patterns("authentication", max_results=5)

# Get system status
status = orchestrator.get_system_status()
```

### State Manager

```python
from forge.core.state_manager import StateManager, ProjectState, TaskState

state = StateManager(db_path=".forge/state.db")

# List all projects
projects = state.list_projects()

# Get specific project
project = state.get_project("my-project-20251210")

# Get project tasks
tasks = state.get_project_tasks("my-project-20251210")

# Update task status
state.update_task_status(
    project_id="my-project-20251210",
    task_id="task-001",
    status="complete",
    metadata={"files": ["main.py"]}
)

state.close()
```

### Code Generation

```python
import asyncio
from forge.generators.factory import GeneratorFactory, GeneratorBackend
from forge.generators.base import GenerationContext, GenerationResult

# Create generator
generator = GeneratorFactory.create(
    GeneratorBackend.CODEGEN_API,
    api_key="your-codegen-api-key",
    org_id="5249",
    timeout=7200
)

# Build context
context = GenerationContext(
    task_id="task-001",
    specification="Create a REST API endpoint for user authentication",
    project_context="Building a Python FastAPI application",
    tech_stack=["python", "fastapi", "postgresql"],
    dependencies=[],
    knowledgeforge_patterns=["security", "api-design"]
)

# Generate code
async def generate():
    result: GenerationResult = await generator.generate(context)
    if result.success:
        for filepath, content in result.files.items():
            print(f"Generated: {filepath}")
            print(content[:200])
    else:
        print(f"Failed: {result.error}")
    return result

result = asyncio.run(generate())
```

### CodeGen Client (Low-Level API)

```python
import asyncio
from forge.integrations.codegen_client import CodeGenClient

client = CodeGenClient(
    api_token="your-codegen-api-key",
    org_id="5249",
    timeout=7200,
    poll_interval=10
)

async def run_agent():
    # Create agent run with repository context
    agent_run_id = await client.create_agent_run(
        prompt="Create a Python function that validates email addresses",
        repository_id=184372  # internexio/SEMalytics-forge
    )
    print(f"Agent run started: {agent_run_id}")

    # Wait for completion
    result = await client.wait_for_completion(
        agent_run_id,
        on_progress=lambda s: print(f"Status: {s.get('status')}")
    )
    return result

result = asyncio.run(run_agent())
```

### Generation Orchestrator

```python
import asyncio
from forge.layers.generation import GenerationOrchestrator
from forge.generators.factory import GeneratorFactory, GeneratorBackend
from forge.core.state_manager import StateManager
from forge.integrations.compound_engineering import Task

# Setup
state = StateManager()
generator = GeneratorFactory.create(
    GeneratorBackend.CODEGEN_API,
    api_key="your-key",
    org_id="5249"
)

orchestrator = GenerationOrchestrator(
    generator=generator,
    state_manager=state,
    max_parallel=3
)

# Define tasks
tasks = [
    Task(
        id="task-001",
        title="Create User Model",
        description="Create SQLAlchemy User model with email validation",
        dependencies=[],
        priority=1,
        kf_patterns=["data-modeling"]
    ),
    Task(
        id="task-002",
        title="Create Auth Endpoints",
        description="Create login/register FastAPI endpoints",
        dependencies=["task-001"],
        priority=2,
        kf_patterns=["api-design", "security"]
    )
]

# Run generation
async def build():
    results = await orchestrator.generate_project(
        project_id="my-project",
        tasks=tasks,
        project_context="Building a FastAPI authentication service",
        resume=True
    )
    return results

results = asyncio.run(build())
orchestrator.close()
```

### Planning Agent

```python
import asyncio
from forge.layers.planning import PlanningAgent

agent = PlanningAgent(
    api_key="your-anthropic-key",
    model="claude-sonnet-4-20250514"
)

# Optional: Analyze existing repository
repo_context = agent.analyze_repository("/path/to/repo")

async def chat():
    async for chunk in agent.chat("I want to build a REST API"):
        print(chunk, end="", flush=True)

    # Get structured summary
    summary = agent.get_project_summary()
    return summary

summary = asyncio.run(chat())
print(summary)
```

### Repository Analyzer

```python
from pathlib import Path
from forge.layers.repository_analyzer import RepositoryAnalyzer, RepositoryContext

analyzer = RepositoryAnalyzer()
context: RepositoryContext = analyzer.analyze(Path("."), force=False)

print(f"Project: {context.project_name}")
print(f"Language: {context.primary_language}")
print(f"Files: {context.file_count}")
print(f"Lines: {context.total_lines}")
print(f"Test framework: {context.test_info.framework}")
print(f"Package manager: {context.dependency_info.package_manager}")
print(f"Code patterns: {context.code_patterns}")

# Convert to dictionary
context_dict = context.to_dict()
```

### Task Decomposition

```python
from forge.layers.decomposition import TaskDecomposer
from forge.knowledgeforge.pattern_store import PatternStore

store = PatternStore()
decomposer = TaskDecomposer(pattern_store=store)

tasks = decomposer.decompose(
    project_description="Build a REST API with user authentication and rate limiting",
    tech_stack=["python", "fastapi", "postgresql", "redis"]
)

for task in tasks:
    print(f"{task.id}: {task.title}")
    print(f"  Dependencies: {task.dependencies}")
    print(f"  KF Patterns: {task.kf_patterns}")

# Get summary
summary = decomposer.get_task_summary(tasks)
print(f"Total tasks: {summary['total_tasks']}")

decomposer.close()
```

### Multi-Agent Review

```python
from forge.review.panel import ReviewPanel
from forge.review.agents import ReviewResult

panel = ReviewPanel(approval_threshold=8)  # 8/12 must approve

# Review code files
code_files = {
    "src/auth.py": "def authenticate(...):\n    ...",
    "src/models.py": "class User(Base):\n    ..."
}

async def review():
    report = await panel.review(
        code_files=code_files,
        context="Authentication module for FastAPI app"
    )

    print(f"Approved: {report.decision.approved}")
    print(f"Votes: {report.decision.approval_count}/{report.decision.total_reviewers}")
    print(f"Critical findings: {len(report.get_critical_findings())}")

    for finding in report.decision.blocking_findings:
        print(f"  - {finding.message} ({finding.severity})")

    return report

report = asyncio.run(review())
```

---

## 4. Authentication & Configuration Requirements

### Environment Variables

```bash
# Required for CodeGen API backend
export CODEGEN_API_KEY="your-codegen-api-key"
export CODEGEN_ORG_ID="5249"
export CODEGEN_REPO_ID="184372"  # For internexio/SEMalytics-forge

# Required for planning/chat
export ANTHROPIC_API_KEY="your-anthropic-key"

# Optional for GitHub operations
export GITHUB_TOKEN="your-github-token"
```

### Configuration Files

```yaml
# ~/.forge/config.yaml (global)
generator:
  backend: codegen_api
  timeout: 7200

# ./forge.yaml (project)
generator:
  backend: codegen_api

knowledgeforge:
  search_method: hybrid

testing:
  min_coverage: 80.0
```

### .env File

Place in project root (auto-loaded by Forge):

```
ANTHROPIC_API_KEY=your-anthropic-key
CODEGEN_API_KEY=your-codegen-api-key
CODEGEN_ORG_ID=5249
CODEGEN_REPO_ID=184372
GITHUB_TOKEN=your-github-token
```

---

## 5. Complete Programmatic Usage Example

```python
#!/usr/bin/env python3
"""
Complete example: Programmatically use Forge to generate code
"""

import asyncio
import os
from pathlib import Path

# Ensure environment variables are loaded
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Forge imports
from forge.core.config import ForgeConfig
from forge.core.orchestrator import Orchestrator
from forge.core.state_manager import StateManager
from forge.generators.factory import GeneratorFactory, GeneratorBackend
from forge.generators.base import GenerationContext
from forge.layers.generation import GenerationOrchestrator
from forge.layers.repository_analyzer import RepositoryAnalyzer
from forge.layers.decomposition import TaskDecomposer
from forge.integrations.codegen_client import CodeGenClient
from forge.integrations.compound_engineering import Task


async def main():
    """Main entry point for programmatic Forge usage."""

    # 1. Load configuration
    config = ForgeConfig.load()
    print(f"Backend: {config.generator.backend}")

    # 2. Initialize orchestrator
    with Orchestrator(config) as orchestrator:

        # 3. Create a project
        project = orchestrator.create_project(
            name="api-service",
            description="REST API with authentication"
        )
        print(f"Created project: {project.id}")

        # 4. Analyze existing codebase (optional)
        analyzer = RepositoryAnalyzer()
        repo_context = analyzer.analyze(Path.cwd())
        print(f"Analyzed: {repo_context.project_name} ({repo_context.primary_language})")

        # 5. Decompose into tasks
        decomposer = TaskDecomposer()
        tasks = decomposer.decompose(
            project_description="Add user authentication with JWT tokens",
            tech_stack=["python", "fastapi"]
        )
        print(f"Generated {len(tasks)} tasks")
        decomposer.close()

        # 6. Create code generator
        generator = GeneratorFactory.create(
            GeneratorBackend.CODEGEN_API,
            api_key=os.getenv("CODEGEN_API_KEY"),
            org_id=os.getenv("CODEGEN_ORG_ID"),
            timeout=config.generator.timeout
        )

        # 7. Run generation
        state = StateManager()
        gen_orchestrator = GenerationOrchestrator(
            generator=generator,
            state_manager=state,
            max_parallel=3
        )

        results = await gen_orchestrator.generate_project(
            project_id=project.id,
            tasks=tasks,
            project_context=project.description
        )

        # 8. Check results
        success_count = sum(1 for r in results.values() if r.success)
        print(f"Completed: {success_count}/{len(results)} tasks")

        for task_id, result in results.items():
            if result.success:
                print(f"  {task_id}: {len(result.files)} files generated")
            else:
                print(f"  {task_id}: FAILED - {result.error}")

        gen_orchestrator.close()
        state.close()


# Alternative: Direct CodeGen API usage
async def direct_codegen_example():
    """Use CodeGen API directly without orchestration."""

    client = CodeGenClient(
        api_token=os.getenv("CODEGEN_API_KEY"),
        org_id=os.getenv("CODEGEN_ORG_ID"),
        timeout=7200
    )

    # List repositories
    repos = await client.list_repositories()
    print(f"Found {len(repos)} repositories")

    # Find specific repository
    repo = await client.find_repository_by_name("SEMalytics-forge")
    if repo:
        print(f"Found repo: {repo['full_name']} (ID: {repo['id']})")

    # Create and run agent
    result = await client.generate_code(
        prompt="Create a Python function that validates email addresses using regex",
        repository_id=int(os.getenv("CODEGEN_REPO_ID")),
        on_progress=lambda s: print(f"  Status: {s.get('status')}")
    )

    print(f"Generation complete: {result.get('status')}")
    return result


if __name__ == "__main__":
    # Run main example
    asyncio.run(main())

    # Or run direct CodeGen example
    # asyncio.run(direct_codegen_example())
```

---

## 6. Key Function Signatures

### `CodeGenClient.create_agent_run()`

```python
async def create_agent_run(
    self,
    prompt: str,                           # Task description
    repository_id: Optional[int] = None,   # CodeGen repo ID (e.g., 184372)
    image_path: Optional[Path] = None      # Optional image
) -> str:                                  # Returns agent_run_id
```

### `CodeGenClient.generate_code()`

```python
async def generate_code(
    self,
    prompt: str,
    repository_id: Optional[int] = None,
    on_progress: Optional[callable] = None  # Progress callback
) -> Dict[str, Any]:                        # Returns final result
```

### `GenerationOrchestrator.generate_project()`

```python
async def generate_project(
    self,
    project_id: str,
    tasks: List[Task],
    project_context: str,
    resume: bool = True,                    # Skip completed tasks
    force: bool = False                     # Re-run all tasks
) -> Dict[str, GenerationResult]:           # task_id -> result
```

### `RepositoryAnalyzer.analyze()`

```python
def analyze(
    self,
    repo_path: Path,
    force: bool = False                     # Ignore cache
) -> RepositoryContext:
```

### `TaskDecomposer.decompose()`

```python
def decompose(
    self,
    project_description: str,
    tech_stack: Optional[List[str]] = None,
    project_id: Optional[str] = None
) -> List[Task]:
```

---

## 7. Repository Access

Forge accesses the `internexio/SEMalytics-forge` repository via:

1. **CodeGen API** with `repo_id=184372`
2. **GitHub App** installed at https://github.com/apps/codegen-sh
3. **Environment variable** `CODEGEN_REPO_ID=184372`

To use programmatically:

```python
from forge.integrations.codegen_client import CodeGenClient

client = CodeGenClient(
    api_token="your-codegen-api-key",
    org_id="5249"
)

# Generate code in the repository
result = await client.generate_code(
    prompt="Add a new endpoint for user profile",
    repository_id=184372  # internexio/SEMalytics-forge
)
```

---

## 8. Dependencies for Programmatic Usage

```bash
# Install Forge package
cd /Users/dp/Scripts/forge
poetry install

# Or install dependencies manually
pip install click rich pydantic pyyaml sentence-transformers numpy \
    anthropic httpx gitpython tenacity docker python-dotenv
```

Then import from `forge`:

```python
from forge.core.config import ForgeConfig
from forge.integrations.codegen_client import CodeGenClient
# etc.
```

---

## Quick Reference

### Most Common Imports

```python
# Configuration
from forge.core.config import ForgeConfig

# Orchestration
from forge.core.orchestrator import Orchestrator
from forge.core.state_manager import StateManager

# Code Generation
from forge.generators.factory import GeneratorFactory, GeneratorBackend
from forge.generators.base import GenerationContext, GenerationResult
from forge.layers.generation import GenerationOrchestrator

# Direct API Access
from forge.integrations.codegen_client import CodeGenClient

# Analysis & Planning
from forge.layers.repository_analyzer import RepositoryAnalyzer
from forge.layers.planning import PlanningAgent
from forge.layers.decomposition import TaskDecomposer

# Tasks
from forge.integrations.compound_engineering import Task

# Review
from forge.review.panel import ReviewPanel
```

### Minimal Working Example

```python
import asyncio
import os
from forge.integrations.codegen_client import CodeGenClient

async def generate_code():
    client = CodeGenClient(
        api_token=os.getenv("CODEGEN_API_KEY"),
        org_id=os.getenv("CODEGEN_ORG_ID")
    )

    result = await client.generate_code(
        prompt="Create a hello world function",
        repository_id=int(os.getenv("CODEGEN_REPO_ID"))
    )

    return result

result = asyncio.run(generate_code())
print(result)
```
