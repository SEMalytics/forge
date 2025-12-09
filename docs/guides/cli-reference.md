# CLI Reference

Complete reference for all Forge command-line commands.

## Overview

Forge provides a comprehensive CLI built with Click and Rich for beautiful, interactive command-line experiences.

## Global Options

Available for all commands:

```bash
forge [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

### --version

Show version and exit.

```bash
forge --version
# Output: forge, version 1.0.0
```

### --help

Show help message and exit.

```bash
forge --help
forge COMMAND --help
```

## Commands

### doctor

Check system dependencies and configuration.

**Usage:**
```bash
forge doctor
```

**Description:**

Performs comprehensive health check:
- Python version (requires 3.11+)
- Git installation
- Docker installation (optional)
- KnowledgeForge patterns directory
- Compound Engineering plugin
- Forge data directories

**Output:**
```
✓ Python 3.11.13
✓ git installed
✓ docker installed
✓ KnowledgeForge patterns (28 files)
✓ Compound Engineering plugin
✓ Forge data directory: .forge
✨ Forge health check complete!
```

**Exit Codes:**
- `0` - All checks passed
- `1` - One or more checks failed

**Examples:**
```bash
# Basic health check
forge doctor

# Redirect output
forge doctor > health-report.txt

# Check in CI/CD
if forge doctor; then
    echo "System ready"
fi
```

---

### init

Initialize a new Forge project.

**Usage:**
```bash
forge init PROJECT_NAME [OPTIONS]
```

**Arguments:**
- `PROJECT_NAME` - Name of the project (required)

**Options:**
- `-d, --description TEXT` - Project description

**Description:**

Creates a new project with:
- Unique project ID (slug + timestamp)
- Initial project state in database
- Planning stage
- Initial checkpoint for recovery

**Output:**
```
✓ Initialized project: Restaurant Forecasting
• ID: restaurant-forecasting-20251207
• Stage: planning
```

**Examples:**
```bash
# Simple project
forge init "My Project"

# With description
forge init "E-commerce Platform" \
  --description "Full-stack e-commerce with AI recommendations"

# Complex project
forge init "Real-time Analytics Pipeline" \
  -d "Streaming analytics with ML predictions and visualization"
```

**Notes:**
- Project ID is generated automatically from name + timestamp
- Project ID format: `lowercase-with-dashes-YYYYMMDD`
- Duplicate names allowed (timestamp ensures uniqueness)

---

### status

Show project status and details.

**Usage:**
```bash
forge status PROJECT_ID
```

**Arguments:**
- `PROJECT_ID` - Project identifier

**Description:**

Displays project information:
- Project ID
- Project name
- Current stage
- Creation timestamp
- Metadata (if any)

**Output:**
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

**Exit Codes:**
- `0` - Project found
- `1` - Project not found or error

**Examples:**
```bash
# Show project status
forge status my-project-20251207

# Capture output
forge status my-project-20251207 > project-status.txt
```

---

### search

Search KnowledgeForge patterns.

**Usage:**
```bash
forge search QUERY [OPTIONS]
```

**Arguments:**
- `QUERY` - Search query string (required)

**Options:**
- `-n, --max-results INTEGER` - Maximum results to return (default: 10)
- `-m, --method [keyword|semantic|hybrid]` - Search method (default: hybrid)

**Description:**

Search through KnowledgeForge patterns using:
- **keyword** - Fast FTS5 full-text search
- **semantic** - AI-powered similarity using embeddings
- **hybrid** - Combines both methods (recommended)

**Output:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Filename                ┃ Title               ┃ Module ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 01_Core_DataTransfer.md │ Data Transfer       │ Core   │
│ 02_Workflows_...        │ Workflow Patterns   │ ...    │
└─────────────────────────┴─────────────────────┴────────┘
```

**Examples:**
```bash
# Basic search
forge search "data pipeline"

# Keyword-only (fastest)
forge search "testing patterns" --method keyword

# Semantic search (most relevant)
forge search "secure authentication" --method semantic

# Limit results
forge search "API design" --max-results 3

# Hybrid search (default)
forge search "orchestration workflow" --method hybrid --max-results 5

# Complex query
forge search "microservices docker kubernetes deployment"
```

**Search Tips:**
- Use specific terms for better results
- Combine related concepts in query
- Try different methods for different needs
- Use keyword for exact matches
- Use semantic for conceptual searches
- Use hybrid for best overall results

---

### info

Show system information and statistics.

**Usage:**
```bash
forge info
```

**Description:**

Displays system status:
- Pattern count (total indexed)
- Cache statistics (size, hits, misses)
- Configuration (backend, search method)

**Output:**
```
• Patterns indexed: 28
• Cache: 0/128 entries
• Cache hit rate: 0.0%
• Backend: codegen_api
• Search method: hybrid
```

**Examples:**
```bash
# Show system info
forge info

# Monitor cache performance
watch -n 5 forge info

# Export to file
forge info > system-status.txt
```

---

### config

Create default configuration file.

**Usage:**
```bash
forge config [OPTIONS]
```

**Options:**
- `-g, --global-config` - Create global config instead of project config

**Description:**

Creates configuration file:
- **Without flag**: Creates `./forge.yaml` (project config)
- **With --global-config**: Creates `~/.forge/config.yaml` (global config)

Configuration includes:
- Generator settings
- Git configuration
- KnowledgeForge settings
- Testing configuration
- Database paths
- Logging settings

**Output:**
```
✓ Created configuration file: forge.yaml
```

**Examples:**
```bash
# Project config
forge config

# Global config
forge config --global-config

# Create and edit
forge config && nano forge.yaml
```

**Configuration Hierarchy:**
1. Environment variables (highest priority)
2. Project config (`./forge.yaml`)
3. Global config (`~/.forge/config.yaml`)
4. Defaults (lowest priority)

---

## Environment Variables

Forge supports environment variable substitution in config files:

```yaml
generator:
  api_key: ${CODEGEN_API_KEY}
  org_id: ${CODEGEN_ORG_ID}
```

**Supported Variables:**
- `CODEGEN_API_KEY` - CodeGen API key
- `CODEGEN_ORG_ID` - CodeGen organization ID
- Any custom variables you define

**Setting Variables:**
```bash
# In shell
export CODEGEN_API_KEY="your-key"
export CODEGEN_ORG_ID="your-org"

# In .env file (load with source)
echo "CODEGEN_API_KEY=your-key" >> .env
source .env

# Permanent (add to ~/.zshrc or ~/.bashrc)
echo 'export CODEGEN_API_KEY="your-key"' >> ~/.zshrc
```

## Output Formats

### Tables

Formatted with Rich tables:
- Project status
- Pattern search results
- System information

### Colors

- ✓ Green - Success messages
- ✗ Red - Error messages
- ⚠ Yellow - Warning messages
- • Blue - Info messages

### Progress

For long-running operations (future):
- Progress bars
- Spinners
- Status updates

## Exit Codes

Standard exit codes:

- `0` - Success
- `1` - General error
- `2` - Invalid usage
- `130` - Interrupted (Ctrl+C)

## Shell Integration

### Bash/Zsh Completion

```bash
# Generate completion script (future feature)
forge --completion bash > ~/.forge-completion.sh
source ~/.forge-completion.sh
```

### Aliases

Useful aliases:

```bash
# Add to ~/.zshrc or ~/.bashrc
alias f='forge'
alias fd='forge doctor'
alias fi='forge init'
alias fs='forge search'
alias fst='forge status'
alias finfo='forge info'
```

## Debugging

### Verbose Output

Enable debug logging:

```bash
# Set log level in config
log_level: DEBUG

# Or use environment variable
LOG_LEVEL=DEBUG forge doctor
```

### Error Messages

Errors show:
- Error type
- Error message
- Relevant context

Example:
```
✗ Failed to initialize project: Project ID already exists
```

## Tips & Best Practices

### Use Poetry Shell

```bash
poetry shell
forge doctor  # No 'poetry run' needed
```

### Command Chaining

```bash
# Create and check status
forge init "My Project" && \
  forge status my-project-20251207

# Search and save
forge search "testing" --max-results 5 > testing-patterns.txt
```

### Scripting

```bash
#!/bin/bash
# Create multiple projects

projects=(
    "Analytics Pipeline"
    "Payment Service"
    "User Authentication"
)

for project in "${projects[@]}"; do
    forge init "$project"
done
```

### Error Handling

```bash
# Check if command succeeded
if forge doctor; then
    echo "System healthy"
    forge init "New Project"
else
    echo "System check failed"
    exit 1
fi
```

## Common Workflows

### Daily Usage

```bash
# Morning routine
forge doctor               # Health check
forge info                 # System status

# During development
forge search "relevant patterns"
forge status current-project
```

### Project Setup

```bash
# 1. Create project
forge init "Project Name" --description "Description"

# 2. Search relevant patterns
forge search "project keywords" --max-results 10

# 3. Review patterns
cat patterns/relevant-pattern.md

# 4. Check status
forge status project-name-20251207
```

### Debugging

```bash
# 1. Health check
forge doctor

# 2. Check system
forge info

# 3. Test search
forge search "test query"

# 4. Verify config
cat forge.yaml
```

## See Also

- [User Guide](user-guide.md) - Complete user documentation
- [Configuration Guide](configuration.md) - Detailed configuration
- [Troubleshooting](troubleshooting.md) - Common issues
- [API Reference](../api/overview.md) - Python API
