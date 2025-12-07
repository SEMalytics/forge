# API Reference

Complete reference for Forge CLI and Python API.

## CLI Commands

### Core Commands

#### `forge init`

Initialize a new project.

```bash
forge init <project-id>

Options:
  --description TEXT    Project description
  --tech-stack TEXT     Comma-separated tech stack
  --template TEXT       Project template name
```

Examples:
```bash
forge init my-api
forge init todo-app --description "Task management system"
forge init ml-service --tech-stack python,fastapi,tensorflow
```

#### `forge chat`

Start interactive planning session.

```bash
forge chat

Options:
  --project-id TEXT     Continue existing project
  --save-plan           Save plan to file
```

#### `forge decompose`

Generate task plan from description.

```bash
forge decompose <description>

Options:
  --tech-stack TEXT     Technology preferences
  --complexity TEXT     Target complexity (simple/medium/complex)
  --output FILE         Save plan to file
```

Examples:
```bash
forge decompose "RESTful API for task management"
forge decompose "ML pipeline for sales forecasting" --tech-stack python,prophet
```

#### `forge build`

Build project from task plan.

```bash
forge build --project <project-id>

Options:
  -p, --project TEXT    Project ID [required]
  --parallel            Enable parallel generation
  --max-workers INT     Number of parallel workers (default: 4)
  --provider TEXT       Generation provider (anthropic/openai)
```

Examples:
```bash
forge build --project my-api
forge build --project ml-service --parallel --max-workers 8
```

#### `forge test`

Run comprehensive tests.

```bash
forge test --project <project-id>

Options:
  -p, --project TEXT      Project ID [required]
  --unit-only             Run only unit tests
  --integration-only      Run only integration tests
  --no-security           Skip security scan
  --no-performance        Skip performance tests
  --timeout INT           Test timeout in seconds (default: 300)
```

Examples:
```bash
forge test --project my-api
forge test --project ml-service --unit-only
forge test --project web-app --no-performance
```

#### `forge iterate`

Iterate until tests pass.

```bash
forge iterate --project <project-id>

Options:
  -p, --project-id TEXT   Project ID [required]
  --max-iterations INT    Maximum iterations (default: 5)
```

Examples:
```bash
forge iterate --project my-api
forge iterate --project ml-service --max-iterations 10
```

### Git Commands

#### `forge pr`

Create pull request.

```bash
forge pr --project <project-id>

Options:
  -p, --project-id TEXT   Project ID [required]
  --title TEXT            PR title (auto-generated if omitted)
  --base TEXT             Base branch (default: main)
  --draft                 Create as draft PR
  --reviewers TEXT        Comma-separated reviewers
  --labels TEXT           Comma-separated labels
```

Examples:
```bash
forge pr --project my-api
forge pr --project my-api --reviewers alice,bob --labels feature,api
forge pr --project my-api --title "feat: add authentication" --draft
```

#### `forge deploy`

Generate deployment configuration.

```bash
forge deploy --project <project-id> --platform <platform>

Options:
  -p, --project-id TEXT         Project ID [required]
  --platform [flyio|vercel|aws|docker|k8s]  Platform [required]
  --runtime TEXT                Runtime (python/node/go)
  --port INT                    Application port (default: 8080)
  --region TEXT                 Deployment region
  --create-pr                   Create PR with configs
```

Examples:
```bash
forge deploy --project my-api --platform flyio
forge deploy --project web-app --platform vercel --runtime node
forge deploy --project ml-service --platform k8s --create-pr
```

### Utility Commands

#### `forge status`

Show project status.

```bash
forge status --project <project-id>

Options:
  -p, --project TEXT    Project ID
  --verbose             Show detailed status
```

#### `forge info`

Show system information.

```bash
forge info

Options:
  --json                Output as JSON
```

#### `forge doctor`

Check system dependencies.

```bash
forge doctor

Options:
  --fix                 Attempt to fix issues
```

#### `forge search`

Search KnowledgeForge patterns.

```bash
forge search <query>

Options:
  --limit INT           Maximum results (default: 10)
  --category TEXT       Filter by category
```

Examples:
```bash
forge search "authentication"
forge search "database migration" --limit 5
forge search "API design" --category patterns
```

#### `forge config`

Manage configuration.

```bash
forge config

Options:
  --show                Show current configuration
  --set KEY VALUE       Set configuration value
  --reset               Reset to defaults
```

Examples:
```bash
forge config --show
forge config --set generator.provider anthropic
forge config --set testing.timeout 600
```

## Python API

### State Management

```python
from forge.core.state_manager import StateManager

# Initialize
state = StateManager()

# Save task plan
state.save_task_plan(project_id, task_plan)

# Load task plan
task_plan = state.load_task_plan(project_id)

# List projects
projects = state.list_projects()
```

### Task Decomposition

```python
from forge.layers.decomposition import DecompositionLayer

# Initialize
decomposer = DecompositionLayer()

# Decompose description
task_plan = decomposer.decompose_to_tasks(
    description="Build a REST API for task management",
    tech_stack_hint=["python", "fastapi"],
    complexity="medium"
)

# Access tasks
for task in task_plan.tasks:
    print(f"{task.title}: {task.estimated_time}min")
```

### Code Generation

```python
from forge.layers.generation import GenerationLayer
from forge.generators.factory import GeneratorFactory

# Initialize
generator = GenerationLayer(
    provider="anthropic",
    model="claude-sonnet-4-20250514"
)

# Generate code
generated = await generator.generate_project(
    project_plan=project_plan,
    parallel=True,
    max_workers=4
)

# Access files
for file_path, content in generated.files.items():
    print(f"Generated: {file_path}")
```

### Testing

```python
from forge.layers.testing import TestingOrchestrator, TestingConfig

# Configure testing
config = TestingConfig(
    run_security=True,
    run_performance=True,
    timeout=300
)

# Initialize orchestrator
tester = TestingOrchestrator(config=config)

# Run tests
report = await tester.test_project(
    project_id="my-api",
    code_files=code_files,
    tech_stack=["python", "fastapi"]
)

# Check results
if report.all_passed:
    print("All tests passed!")
else:
    print(f"Failed: {report.failed_tests}")
```

### Git Operations

```python
from forge.git.repository import ForgeRepository
from forge.git.commits import ConventionalCommit, CommitType

# Initialize repository
repo = ForgeRepository(".")

# Create feature branch
branch = repo.create_feature_branch("authentication")

# Create commit
commit = ConventionalCommit(
    type=CommitType.FEAT,
    description="add user authentication",
    scope="auth",
    issues=["123"]
)

# Add and commit
repo.add_files(["auth/login.py", "auth/register.py"])
repo.commit(commit.format())

# Push
repo.push(set_upstream=True)
```

### GitHub Integration

```python
from forge.integrations.github_client import GitHubClient

# Initialize (requires GITHUB_TOKEN env var)
github = GitHubClient("owner/repo")

# Create PR
pr = github.create_pr_with_checklist(
    title="feat: add authentication",
    description="Adds JWT-based authentication",
    head="forge/auth-123",
    base="main",
    checklist_items=[
        "Review auth logic",
        "Test login flow"
    ],
    labels=["feature"],
    reviewers=["alice"]
)

print(f"PR created: {pr.html_url}")
```

### Deployment

```python
from forge.layers.deployment import DeploymentGenerator, DeploymentConfig, Platform
from pathlib import Path

# Initialize
generator = DeploymentGenerator(Path("./my-project"))

# Create config
config = DeploymentConfig(
    platform=Platform.FLYIO,
    project_name="my-api",
    runtime="python",
    entry_point="app.py",
    environment_vars={"PORT": "8080"},
    port=8080
)

# Generate configs
files = generator.generate_configs(config)

for file in files:
    print(f"Generated: {file}")
```

## Configuration File

`.forge/config.yaml`:

```yaml
# Project settings
project:
  name: my-api
  description: Task management API
  tech_stack:
    - python
    - fastapi
    - postgresql

# Generator settings
generator:
  provider: anthropic  # or openai
  model: claude-sonnet-4-20250514
  max_tokens: 4096
  temperature: 0.7
  parallel: true
  max_workers: 4

# Testing settings
testing:
  run_unit: true
  run_integration: true
  run_security: true
  run_performance: true
  timeout: 300
  docker_enabled: true

# Git settings
git:
  default_branch: main
  conventional_commits: true
  auto_pr: false

# Deployment settings
deployment:
  platform: flyio
  region: lax
  auto_deploy: false

# KnowledgeForge settings
knowledgeforge:
  patterns_dir: ../knowledgeforge-patterns
  cache_embeddings: true
  max_patterns: 10
```

## Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY=your_anthropic_key

# Optional
export OPENAI_API_KEY=your_openai_key
export GITHUB_TOKEN=your_github_token

# Configuration overrides
export FORGE_PATTERNS_DIR=/path/to/patterns
export FORGE_MAX_WORKERS=8
export FORGE_CACHE_DIR=~/.forge/cache
```

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Configuration error
- `3` - API error
- `4` - Test failure
- `130` - User interrupt (Ctrl+C)

## Related Documentation

- [Architecture](./ARCHITECTURE.md)
- [Git Workflows](./GIT_WORKFLOWS.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
