# Forge - AI Development Orchestration

Transform natural language descriptions into production-ready code with intelligent task decomposition, distributed generation, and automated testing.

## Quick Start

```bash
# Install
poetry install

# Initialize project
forge init my-project

# Start conversational planning
forge chat

# Build from description
forge build --project my-project

# Test comprehensively
forge test --project my-project

# Iterate until tests pass
forge iterate --project my-project

# Deploy to platform
forge deploy --project my-project --platform flyio
```

## Features

### 🎯 Intelligent Planning
- **Conversational interface** for requirements gathering
- **Automatic task decomposition** with dependency tracking
- **Smart tech stack selection** based on requirements
- **Complexity estimation** for accurate planning

### 🏗️ Distributed Generation
- **Multi-agent code generation** with Claude/GPT-4
- **Parallel execution** for faster builds
- **Pattern-based generation** using KnowledgeForge
- **Consistent code quality** across modules

### 🧪 Comprehensive Testing
- **Automated test generation** for all code
- **Multi-framework support** (pytest, jest, go test)
- **Security scanning** for vulnerabilities
- **Performance benchmarking** with thresholds
- **Docker-based isolation** for reproducibility

### 🔄 Iterative Refinement
- **Automatic failure analysis** with root cause detection
- **AI-powered fix generation** using patterns
- **Progressive iteration** until tests pass
- **Learning database** for continuous improvement

### 🚀 Git Integration
- **Conventional commits** with auto-generation
- **Branch management** with forge/* naming
- **PR creation** with comprehensive checklists
- **Multi-platform deployment** (fly.io, Vercel, AWS, Docker, K8s)

### 📚 Knowledge Management
- **Pattern library** with 40+ engineering patterns
- **Semantic search** for relevant patterns
- **Context-aware suggestions** for best practices
- **Continuous learning** from successes

## Architecture

Forge uses a 6-layer architecture for scalable code generation:

```
┌─────────────────────────────────────────────────┐
│  1. Decomposition Layer                         │
│     Task planning, dependency analysis          │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  2. Planning Layer                               │
│     Tech stack selection, file structure        │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  3. Generation Layer                             │
│     Distributed code generation                 │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  4. Testing Layer                                │
│     Unit, integration, security, performance    │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  5. Review Layer                                 │
│     Iterative refinement, fix generation        │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  6. Deployment Layer                             │
│     Git workflows, PR creation, deployment      │
└─────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](./docs/ARCHITECTURE.md) for detailed design.

## Installation

### Requirements

- Python 3.11 or 3.12 (NOT 3.13+, as dependencies don't support it yet)
- Docker (for testing)
- Git
- API Keys:
  - `ANTHROPIC_API_KEY` for Claude (primary)
  - `OPENAI_API_KEY` for GPT-4 (optional)
  - `GITHUB_TOKEN` for PR creation (optional)

### Quick Start

```bash
# Clone repository
git clone https://github.com/SEMalytics/forge.git
cd forge

# Install with Poetry (use Python 3.11 or 3.12)
poetry env use python3.11  # If you have Python 3.13+
poetry install

# Install as CLI command (so you can type 'forge' anywhere)
pip install -e .

# Verify installation
forge --version
forge doctor
```

### Optional: Compound Engineering Plugin

For enhanced Claude Code integration, install the CE plugin:

```bash
# From inside the forge directory
git clone https://github.com/SEMalytics/compound-engineering-plugin.git compound-engineering

# Verify
forge doctor
# Should show: ✓ Compound Engineering plugin (for Claude Code integration)
```

**Note**: The CE plugin is optional. Forge has built-in CE-style planning and works perfectly without it. The plugin adds advanced features for Claude Code workflows.

## Usage

### 1. Initialize Project

```bash
forge init my-awesome-api

# Output:
# ✓ Created project structure
# ✓ Initialized state manager
# ✓ Ready for planning
```

### 2. Interactive Planning

```bash
forge chat

# Conversational interface:
# > What would you like to build?
# A REST API for managing tasks with PostgreSQL
#
# > What features do you need?
# - CRUD operations for tasks
# - User authentication with JWT
# - Task filtering and search
# - Due date reminders
#
# ✓ Generated 12 tasks
# ✓ Estimated complexity: Medium (8-12 hours)
# ✓ Recommended stack: FastAPI, PostgreSQL, SQLAlchemy
```

### 3. Build Project

```bash
forge build --project my-awesome-api

# Output:
# [1/12] Generating database models... ✓
# [2/12] Generating API endpoints... ✓
# [3/12] Generating authentication... ✓
# ...
# [12/12] Generating tests... ✓
#
# ✓ Generated 24 files
# ✓ Build completed in 3m 42s
```

### 4. Run Tests

```bash
forge test --project my-awesome-api

# Output:
# Running unit tests... ✓ 18 passed
# Running integration tests... ✓ 8 passed
# Running security scan... ✓ No vulnerabilities
# Running performance tests... ✓ All benchmarks passed
#
# ✓ All tests passed (26/26)
```

### 5. Iterate Until Passing

```bash
forge iterate --project my-awesome-api --max-iterations 5

# Output:
# Iteration 1/5
#   Running tests... ✗ 3 failed
#   Analyzing failures... ✓ 3 issues identified
#   Generating fixes... ✓ 3 fixes generated
#   Applying fixes... ✓ 3 fixes applied
#
# Iteration 2/5
#   Running tests... ✓ All tests passing!
#
# ✓ Success in 2 iterations
```

### 6. Deploy

```bash
forge deploy --project my-awesome-api --platform flyio --create-pr

# Output:
# ✓ Generated fly.toml
# ✓ Generated Dockerfile
# ✓ Created branch: forge/deploy-flyio-20250107
# ✓ Created commit
# ✓ Pushed to remote
# ✓ Created PR #42: https://github.com/owner/repo/pull/42
#
# Next Steps:
#   1. Install flyctl: curl -L https://fly.io/install.sh | sh
#   2. Create app: fly apps create my-awesome-api
#   3. Deploy: fly deploy
```

## Examples

View all examples:
```bash
forge examples
```

Build an example:
```bash
# Simple API
forge example simple-api

# ML Pipeline
forge example ml-pipeline

# Full Stack App
forge example full-stack-app
```

## CLI Reference

### Core Commands

```bash
forge init <project>              # Initialize new project
forge chat                         # Interactive planning
forge decompose <description>      # Generate task plan
forge build --project <id>         # Build project
forge test --project <id>          # Run tests
forge iterate --project <id>       # Iterate until passing
```

### Git Commands

```bash
forge pr --project <id>            # Create pull request
forge deploy --platform <name>     # Generate deployment config
```

### Utility Commands

```bash
forge status --project <id>        # Show project status
forge info                         # System information
forge doctor                       # Check dependencies
forge search <query>               # Search patterns
forge examples                     # List examples
forge explain <concept>            # Explain concept
forge stats --project <id>         # Show statistics
```

See [API_REFERENCE.md](./docs/API_REFERENCE.md) for complete documentation.

## Configuration

### Project Configuration

`.forge/config.yaml`:
```yaml
project:
  name: my-api
  description: Task management API

generator:
  provider: anthropic  # or openai
  model: claude-sonnet-4-20250514
  max_tokens: 4096

testing:
  run_security: true
  run_performance: true
  timeout: 300

deployment:
  platform: flyio
  region: lax
```

## Development

### Setup

```bash
# Install dependencies
poetry install

# Install pre-commit hooks
pre-commit install

# Run tests
poetry run pytest
```

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=forge --cov-report=html

# Specific module
poetry run pytest tests/test_git_workflows.py
```

### Code Quality

```bash
# Format code
poetry run black src/

# Sort imports
poetry run isort src/

# Type checking
poetry run mypy src/

# Linting
poetry run ruff src/
```

## Troubleshooting

See [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) for common issues and solutions.

Quick fixes:

```bash
# API key not found
export ANTHROPIC_API_KEY=your_key_here

# Docker connection failed
# macOS: Open Docker Desktop
# Linux: sudo systemctl start docker

# Pattern files included in repository at ./patterns/
# Verify with: ls patterns/
```

## Performance

Forge is optimized for speed:

- **Pattern search**: <200ms (with caching)
- **Task decomposition**: <5s for 20 tasks
- **Code generation**: ~2min/1000 LOC (parallel)
- **Test execution**: Variable (Docker startup + tests)
- **Memory usage**: <500MB typical

## Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

MIT License - see [LICENSE](./LICENSE) for details.

## Support

- **Documentation**: [docs/](./docs/)
- **Patterns**: [patterns/](./patterns/)
- **Issues**: [GitHub Issues](https://github.com/SEMalytics/forge/issues)

## Acknowledgments

- Built with [Claude](https://anthropic.com) by Anthropic
- Powered by [Poetry](https://python-poetry.org/)
- Developed by [SEMalytics](https://github.com/SEMalytics)

---

**Built with ❤️ by the Forge team**
