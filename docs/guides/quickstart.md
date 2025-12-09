# Quick Start Guide

Get up and running with Forge in 5 minutes.

## Prerequisites

- Python 3.11+ installed
- Poetry installed (see [Installation Guide](installation.md))
- KnowledgeForge patterns in `patterns/`

## 5-Minute Quick Start

### Step 1: Verify Installation (30 seconds)

```bash
cd /path/to/forge

# Check Forge is working
poetry run forge --version
# Output: forge, version 1.0.0

# Run health check
poetry run forge doctor
```

Expected output:
```
✓ Python 3.11.13
✓ git installed
✓ docker installed
✓ KnowledgeForge patterns (28 files)
✨ Forge health check complete!
```

### Step 2: Create Your First Project (1 minute)

```bash
# Create a new project
poetry run forge init "Restaurant Forecasting" \
  --description "ML system for predicting restaurant demand"
```

Output:
```
✓ Initialized project: Restaurant Forecasting
• ID: restaurant-forecasting-20251207
• Stage: planning
```

**What happened:**
- Project created in SQLite database
- Unique ID generated with timestamp
- Initial checkpoint created
- Project stage set to "planning"

### Step 3: Search KnowledgeForge Patterns (1 minute)

```bash
# Search for relevant patterns
poetry run forge search "data pipeline"

# More specific search
poetry run forge search "machine learning orchestration" --max-results 5

# Try different search methods
poetry run forge search "API design" --method semantic
```

Output shows:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Filename                ┃ Title               ┃ Module ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 01_Core_DataTransfer.md │ Data Transfer       │ Core   │
│ 02_Workflows_...        │ Workflow Patterns   │ ...    │
└─────────────────────────┴─────────────────────┴────────┘
```

**Search methods:**
- `keyword` - Fast FTS5 full-text search
- `semantic` - AI-powered similarity search
- `hybrid` - Best of both (default)

### Step 4: Check Project Status (30 seconds)

```bash
# View project details
poetry run forge status restaurant-forecasting-20251207
```

Output:
```
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property ┃ Value                           ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ID       │ restaurant-forecasting-20251207 │
│ Name     │ Restaurant Forecasting          │
│ Stage    │ planning                        │
│ Created  │ 2025-12-07 12:00:00            │
└──────────┴─────────────────────────────────┘
```

### Step 5: View System Information (30 seconds)

```bash
# Get system stats
poetry run forge info
```

Output:
```
• Patterns indexed: 28
• Cache: 0/128 entries
• Cache hit rate: 0.0%
• Backend: codegen_api
• Search method: hybrid
```

## Common Workflows

### Activate Poetry Shell (Recommended)

Instead of typing `poetry run` each time:

```bash
# Activate Poetry shell
poetry shell

# Now run commands directly
forge doctor
forge search "patterns"
forge info

# Exit when done
exit
```

### Search Patterns by Topic

```bash
# Find testing patterns
forge search "testing unit integration" --method keyword

# Find security patterns
forge search "authentication authorization security" --max-results 3

# Find orchestration patterns
forge search "workflow orchestration deployment" --method hybrid
```

### Explore Pattern Content

After finding patterns, view them:

```bash
# Pattern files are in sibling directory
cat patterns/01_Core_DataTransfer.md
less patterns/02_Workflows_Orchestration.md

# Or use your favorite editor
code patterns/
```

### Create Multiple Projects

```bash
# E-commerce platform
forge init "E-commerce Platform" \
  --description "Full-stack e-commerce with AI recommendations"

# Data pipeline
forge init "Analytics Pipeline" \
  --description "Real-time analytics data processing"

# Microservices
forge init "Payment Service" \
  --description "Secure payment processing microservice"
```

## Using the Python API

For programmatic access:

```python
from forge.core.orchestrator import Orchestrator
from forge.core.config import ForgeConfig

# Initialize
config = ForgeConfig.load()
orchestrator = Orchestrator(config)

# Create project
project = orchestrator.create_project(
    name="My API",
    description="RESTful API for mobile app"
)
print(f"Created: {project.id}")

# Search patterns
patterns = orchestrator.search_patterns(
    query="REST API design",
    max_results=5
)

for pattern in patterns:
    print(f"- {pattern['filename']}: {pattern['title']}")

# Clean up
orchestrator.close()
```

## Configuration Quick Setup

### Create Default Configuration

```bash
# Project-specific config
forge config

# Edit forge.yaml
nano forge.yaml
```

### Basic Configuration

Edit `forge.yaml`:

```yaml
generator:
  backend: codegen_api
  timeout: 300

knowledgeforge:
  patterns_dir: patterns
  search_method: hybrid
  cache_size: 128

log_level: INFO
```

### Environment Variables

For API keys:

```bash
# Add to ~/.zshrc or ~/.bashrc
export CODEGEN_API_KEY="your-key-here"
export CODEGEN_ORG_ID="your-org-id"

# Reload shell
source ~/.zshrc
```

## Testing Your Setup

### Run Tests

```bash
# All tests
poetry run pytest

# Verbose output
poetry run pytest -v

# Specific test
poetry run pytest tests/test_pattern_store.py -v
```

Expected: `26 passed in ~17s`

### Verify Pattern Store

```python
from forge.knowledgeforge.pattern_store import PatternStore

# Open pattern store
store = PatternStore()

# Check count
count = store.get_pattern_count()
print(f"Patterns indexed: {count}")  # Should be 28

# Test search
results = store.search("orchestration", max_results=3)
for r in results:
    print(f"- {r['filename']}")

store.close()
```

## Next Steps

Now that you're up and running:

### 1. Learn More
- Read the [User Guide](user-guide.md) for detailed documentation
- Review [CLI Reference](cli-reference.md) for all commands
- Explore [Configuration Guide](configuration.md) for customization

### 2. Try Advanced Features
- **Pattern Search**: [Pattern Search Guide](pattern-search.md)
- **Python API**: [API Examples](../api/examples.md)
- **Configuration**: [Configuration Guide](configuration.md)

### 3. Explore the Codebase
- Browse `src/forge/` for implementation
- Read `tests/` for usage examples
- Review architecture in `docs/architecture/`

### 4. Build Something
Follow the [Tutorial](tutorial.md) to build a complete project.

## Quick Reference

### Essential Commands

```bash
# Health check
forge doctor

# Create project
forge init "Project Name" --description "Description"

# Search patterns
forge search "query" [--method keyword|semantic|hybrid] [--max-results N]

# Project status
forge status <project-id>

# System info
forge info

# Configuration
forge config [--global-config]
```

### File Locations

- **Databases**: `.forge/patterns.db`, `.forge/state.db`
- **Config**: `./forge.yaml` (project) or `~/.forge/config.yaml` (global)
- **Patterns**: `patterns/*.md`
- **Logs**: `.forge/forge.log`

### Getting Help

```bash
# Command help
forge --help
forge search --help
forge init --help

# Run doctor
forge doctor

# Check version
forge --version
```

## Troubleshooting

### Patterns Not Found

```bash
# Check patterns directory
ls patterns/*.md

# Should show 28 files
# If not:
mkdir -p patterns
# Copy your .md files there
```

### Database Errors

```bash
# Reset databases
rm -rf .forge/
forge doctor  # Recreates databases
```

### Import Errors

```bash
# Reinstall dependencies
poetry install --no-cache
```

### Permission Issues

```bash
# Fix permissions
chmod -R 755 .forge/
```

## Tips & Best Practices

### 💡 Use Poetry Shell

```bash
poetry shell  # Activate once
forge doctor  # Run commands without 'poetry run'
```

### 💡 Explore Patterns

The 28 KnowledgeForge patterns contain valuable best practices:

```bash
# List all patterns
ls patterns/

# Search for specific topics
forge search "your topic" --max-results 10
```

### 💡 Check System Status

Regularly run `forge doctor` to ensure everything is working:

```bash
forge doctor
```

### 💡 Use Hybrid Search

Hybrid search combines speed and accuracy:

```bash
forge search "query" --method hybrid  # Best results
```

## Summary

You've now:
- ✅ Verified Forge installation
- ✅ Created your first project
- ✅ Searched KnowledgeForge patterns
- ✅ Checked project status
- ✅ Viewed system information

Ready to dive deeper? Check out the [User Guide](user-guide.md)!
