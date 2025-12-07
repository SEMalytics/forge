# Forge Foundation - Quick Start Guide

## Installation & Setup

### 1. Add Poetry to PATH

```bash
export PATH="/Users/davidpedersen/.local/bin:$PATH"

# Add to your shell profile for persistence
echo 'export PATH="/Users/davidpedersen/.local/bin:$PATH"' >> ~/.zshrc
```

### 2. Verify Installation

```bash
cd /Users/davidpedersen/Scripts/forge-build/forge

# Check Poetry
poetry --version
# Output: Poetry (version 2.2.1)

# Check Forge
poetry run forge --version
# Output: forge, version 1.0.0
```

### 3. Run System Health Check

```bash
poetry run forge doctor
```

Expected output:
```
✓ Python 3.11.13
✓ git installed
✓ docker installed
✓ KnowledgeForge patterns (28 files)
✓ Compound Engineering plugin
✨ Forge health check complete!
```

## Basic Usage

### Create Your First Project

```bash
# Initialize a new project
poetry run forge init "My ML Pipeline" \
  --description "Machine learning data pipeline for predictions"

# Output shows:
# ✓ Initialized project: My ML Pipeline
# • ID: my-ml-pipeline-20251207
# • Stage: planning
```

### Search KnowledgeForge Patterns

```bash
# Hybrid search (best results)
poetry run forge search "data pipeline orchestration"

# Keyword-only search (fastest)
poetry run forge search "testing patterns" --method keyword

# Semantic search (most relevant)
poetry run forge search "secure authentication" --method semantic

# Limit results
poetry run forge search "API design" --max-results 5
```

### Check Project Status

```bash
# Get project details
poetry run forge status my-ml-pipeline-20251207

# Output shows:
# ┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Property ┃ Value                 ┃
# ┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
# │ ID       │ my-ml-pipeline-...    │
# │ Name     │ My ML Pipeline        │
# │ Stage    │ planning              │
# │ Created  │ 2025-12-07 12:00:00   │
# └──────────┴───────────────────────┘
```

### View System Information

```bash
poetry run forge info

# Output shows:
# • Patterns indexed: 28
# • Cache: 0/128 entries
# • Backend: codegen_api
# • Search method: hybrid
```

## Configuration

### Create Default Configuration

```bash
# Project-specific config (./forge.yaml)
poetry run forge config

# Global config (~/.forge/config.yaml)
poetry run forge config --global-config
```

### Example Configuration File

Edit `forge.yaml`:

```yaml
generator:
  backend: codegen_api
  api_key: ${CODEGEN_API_KEY}
  org_id: ${CODEGEN_ORG_ID}
  timeout: 300

git:
  author_name: Your Name
  author_email: your.email@example.com
  commit_format: conventional

knowledgeforge:
  patterns_dir: ../knowledgeforge-patterns
  embedding_model: all-MiniLM-L6-v2
  cache_size: 128
  search_method: hybrid

testing:
  use_docker: true
  timeout: 600
  min_coverage: 80.0

log_level: INFO
```

### Environment Variables

Set these in your shell or `.env` file:

```bash
export CODEGEN_API_KEY="your-api-key-here"
export CODEGEN_ORG_ID="your-org-id-here"
```

## Development Workflow

### Activate Virtual Environment

```bash
# Enter Poetry shell (recommended for development)
poetry shell

# Now you can run commands directly:
forge doctor
forge search "patterns"

# Exit shell when done
exit
```

### Run Tests

```bash
# All tests
poetry run pytest

# Verbose output
poetry run pytest -v

# With coverage
poetry run pytest --cov=src/forge --cov-report=html

# Specific test file
poetry run pytest tests/test_pattern_store.py -v

# Specific test
poetry run pytest tests/test_config.py::test_default_config -v
```

### Code Quality

```bash
# Format code
poetry run black src/forge tests

# Lint code
poetry run ruff check src/forge

# Type checking
poetry run mypy src/forge
```

## Python API Usage

You can also use Forge programmatically:

```python
from forge.core.config import ForgeConfig
from forge.core.orchestrator import Orchestrator

# Load configuration
config = ForgeConfig.load()

# Create orchestrator
with Orchestrator(config) as orchestrator:
    # Create project
    project = orchestrator.create_project(
        name="My Project",
        description="A test project"
    )
    print(f"Created: {project.id}")

    # Search patterns
    patterns = orchestrator.search_patterns(
        query="data pipeline",
        max_results=5
    )
    for pattern in patterns:
        print(f"- {pattern['filename']}: {pattern['title']}")

    # Get system status
    status = orchestrator.get_system_status()
    print(f"Patterns: {status['pattern_count']}")
```

### Pattern Store API

```python
from forge.knowledgeforge.pattern_store import PatternStore

# Create pattern store
with PatternStore() as store:
    # Get pattern count
    count = store.get_pattern_count()
    print(f"Total patterns: {count}")

    # Get all patterns
    patterns = store.get_all_patterns()

    # Get specific pattern
    pattern = store.get_pattern_by_filename('01_Core_DataTransfer.md')
    if pattern:
        print(pattern['title'])
        print(pattern['content'][:200])

    # Search patterns
    results = store.search('orchestration', max_results=10, method='hybrid')
```

### State Manager API

```python
from forge.core.state_manager import StateManager, TaskState

# Create state manager
with StateManager() as state:
    # Create project
    project = state.create_project(
        project_id="test-001",
        name="Test Project",
        description="Testing state management"
    )

    # Create task
    task = TaskState(
        id="task-001",
        project_id="test-001",
        title="Implement feature",
        status="pending",
        priority=1,
        dependencies=[],
        generated_files={},
        test_results=None,
        commits=[]
    )
    state.create_task(task)

    # Create checkpoint
    state.checkpoint(
        project_id="test-001",
        stage="planning",
        state={"key": "value"},
        description="Planning complete"
    )

    # Get project tasks
    tasks = state.get_project_tasks("test-001")
    print(f"Tasks: {len(tasks)}")
```

## Troubleshooting

### Pattern Store Issues

If patterns aren't found:

```bash
# Check patterns directory
ls ../knowledgeforge-patterns/*.md

# Should show 28 .md files
# If not, copy patterns:
mkdir -p ../knowledgeforge-patterns
# Copy your KF pattern files there
```

### Database Issues

Remove and reinitialize:

```bash
rm -rf .forge/
poetry run forge doctor
```

### Import Errors

Reinstall dependencies:

```bash
poetry install --no-cache
```

### Permission Errors

Ensure directories are writable:

```bash
chmod 755 .forge/
```

## File Locations

- **Databases**: `.forge/patterns.db`, `.forge/state.db`
- **Sessions**: `.forge/sessions/*.json`
- **Logs**: `.forge/forge.log` (if enabled)
- **Config**: `./forge.yaml` (project) or `~/.forge/config.yaml` (global)
- **Patterns**: `../knowledgeforge-patterns/*.md` (referenced)

## Next Steps

Once you're comfortable with the foundation:

1. Explore the pattern search capabilities
2. Create test projects to understand the workflow
3. Review the implementation plan (`../forge_complete_implementation_plan.md`)
4. Start building Layer 1 (Conversational Planning)

## Support

- **Documentation**: See `README.md` for detailed info
- **Build Summary**: See `BUILD_SUMMARY.md` for implementation details
- **Tests**: Run `pytest -v` to see all test cases
- **Source Code**: Browse `src/forge/` for implementation

---

**Quick Command Reference**

```bash
# Health check
forge doctor

# Create project
forge init "Project Name" --description "Description"

# Search patterns
forge search "query" [--method hybrid|keyword|semantic] [--max-results N]

# Project status
forge status <project-id>

# System info
forge info

# Configuration
forge config [--global-config]

# Run tests
pytest -v
pytest --cov=src/forge

# Code quality
black src/forge tests
ruff check src/forge
```
