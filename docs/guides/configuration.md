# Configuration Guide

Complete guide to configuring Forge for your needs.

## Configuration Hierarchy

Forge uses layered configuration with the following priority (highest to lowest):

1. **Environment Variables** - Runtime overrides
2. **Project Config** - `./forge.yaml` in project directory
3. **Global Config** - `~/.forge/config.yaml` in home directory
4. **Defaults** - Built-in default values

## Creating Configuration Files

### Project Configuration

```bash
# Create forge.yaml in current directory
forge config

# Edit configuration
nano forge.yaml
```

### Global Configuration

```bash
# Create ~/.forge/config.yaml
forge config --global-config

# Edit global configuration
nano ~/.forge/config.yaml
```

## Complete Configuration Reference

### Default Configuration

```yaml
# Generator settings
generator:
  backend: codegen_api        # Code generation backend
  api_key: null              # API key (use ${CODEGEN_API_KEY})
  org_id: null               # Organization ID (use ${CODEGEN_ORG_ID})
  timeout: 300               # Request timeout in seconds
  base_url: null             # Custom API base URL

# Git settings
git:
  author_name: Forge AI      # Default commit author
  author_email: forge@ai.dev # Default commit email
  commit_format: conventional # Commit message format

# KnowledgeForge settings
knowledgeforge:
  patterns_dir: ../knowledgeforge-patterns  # Pattern directory
  embedding_model: all-MiniLM-L6-v2        # Sentence transformer model
  cache_size: 128                           # LRU cache size
  search_method: hybrid                     # Default search method

# Testing settings
testing:
  use_docker: true           # Use Docker for test isolation
  timeout: 600               # Test timeout in seconds
  min_coverage: 80.0         # Minimum coverage percentage

# Database paths
pattern_store_path: .forge/patterns.db     # Pattern database
state_db_path: .forge/state.db            # State database

# Logging
log_level: INFO                            # Log level
log_file: .forge/forge.log                # Log file path
```

## Configuration Sections

### Generator Configuration

Controls code generation backend:

```yaml
generator:
  backend: codegen_api  # or "claude_code"
  api_key: ${CODEGEN_API_KEY}
  org_id: ${CODEGEN_ORG_ID}
  timeout: 300
  base_url: https://api.codegen.ai/v1  # Optional custom URL
```

**Options:**

- `backend` - Code generator to use
  - `codegen_api` - CodeGen API backend (default)
  - `claude_code` - Claude Code CLI backend
- `api_key` - API authentication key
- `org_id` - Organization identifier
- `timeout` - Request timeout (seconds)
- `base_url` - Custom API endpoint (optional)

**Example:**

```yaml
generator:
  backend: claude_code
  timeout: 600  # 10 minutes for complex generations
```

### Git Configuration

Git operation settings:

```yaml
git:
  author_name: Your Name
  author_email: your.email@example.com
  commit_format: conventional
```

**Options:**

- `author_name` - Default commit author name
- `author_email` - Default commit author email
- `commit_format` - Commit message format
  - `conventional` - Conventional Commits format

**Example:**

```yaml
git:
  author_name: AI Assistant
  author_email: ai@mycompany.com
  commit_format: conventional
```

### KnowledgeForge Configuration

Pattern storage and search settings:

```yaml
knowledgeforge:
  patterns_dir: ../knowledgeforge-patterns
  embedding_model: all-MiniLM-L6-v2
  cache_size: 128
  search_method: hybrid
```

**Options:**

- `patterns_dir` - Directory containing .md pattern files
- `embedding_model` - Sentence transformer model name
  - `all-MiniLM-L6-v2` - Fast, good quality (default, ~90MB)
  - `all-mpnet-base-v2` - Better quality, slower (~420MB)
  - `paraphrase-multilingual-MiniLM-L12-v2` - Multilingual (~470MB)
- `cache_size` - Number of search results to cache
- `search_method` - Default search strategy
  - `hybrid` - Combines keyword + semantic (default)
  - `keyword` - Fast FTS5 search only
  - `semantic` - Embedding-based search only

**Example:**

```yaml
knowledgeforge:
  patterns_dir: /absolute/path/to/patterns
  embedding_model: all-mpnet-base-v2  # Higher quality
  cache_size: 256  # Larger cache
  search_method: semantic  # Prefer semantic search
```

### Testing Configuration

Test execution settings:

```yaml
testing:
  use_docker: true
  timeout: 600
  min_coverage: 80.0
```

**Options:**

- `use_docker` - Run tests in Docker containers
- `timeout` - Test execution timeout (seconds)
- `min_coverage` - Minimum required code coverage (%)

**Example:**

```yaml
testing:
  use_docker: false  # Disable Docker
  timeout: 1200  # 20 minutes
  min_coverage: 85.0  # Higher coverage requirement
```

### Database Configuration

SQLite database paths:

```yaml
pattern_store_path: .forge/patterns.db
state_db_path: .forge/state.db
```

**Options:**

- `pattern_store_path` - Pattern database location
- `state_db_path` - State database location

**Example:**

```yaml
pattern_store_path: /var/forge/patterns.db  # Absolute path
state_db_path: /var/forge/state.db
```

### Logging Configuration

Logging settings:

```yaml
log_level: INFO
log_file: .forge/forge.log
```

**Options:**

- `log_level` - Logging verbosity
  - `DEBUG` - Detailed debugging information
  - `INFO` - General information (default)
  - `WARNING` - Warning messages only
  - `ERROR` - Error messages only
- `log_file` - Log file path (null to disable file logging)

**Example:**

```yaml
log_level: DEBUG  # Verbose logging
log_file: /var/log/forge.log  # Custom log location
```

## Environment Variables

### Variable Substitution

Use `${VARIABLE_NAME}` syntax in YAML:

```yaml
generator:
  api_key: ${CODEGEN_API_KEY}
  org_id: ${CODEGEN_ORG_ID}

custom_setting: ${MY_CUSTOM_VAR:default_value}  # With default
```

### Setting Variables

#### In Shell

```bash
# Temporary (current session)
export CODEGEN_API_KEY="your-key-here"
export CODEGEN_ORG_ID="your-org-id"

# Permanent (add to ~/.zshrc or ~/.bashrc)
echo 'export CODEGEN_API_KEY="your-key"' >> ~/.zshrc
echo 'export CODEGEN_ORG_ID="your-org"' >> ~/.zshrc

# Reload shell
source ~/.zshrc
```

#### In .env File

```bash
# Create .env file
cat > .env <<EOF
CODEGEN_API_KEY=your-key-here
CODEGEN_ORG_ID=your-org-id
EOF

# Load before running
source .env
forge doctor
```

#### In Docker

```dockerfile
ENV CODEGEN_API_KEY=your-key
ENV CODEGEN_ORG_ID=your-org
```

### Common Variables

- `CODEGEN_API_KEY` - CodeGen API authentication key
- `CODEGEN_ORG_ID` - CodeGen organization identifier
- `LOG_LEVEL` - Override log level
- `FORGE_CONFIG` - Custom config file path

## Configuration Examples

### Development Setup

```yaml
# forge.yaml for development
generator:
  backend: claude_code  # Local Claude Code
  timeout: 600

git:
  author_name: Dev Team
  author_email: dev@company.com

knowledgeforge:
  search_method: hybrid
  cache_size: 256  # Larger cache

testing:
  use_docker: false  # Faster without Docker
  min_coverage: 70.0  # Lower requirement for dev

log_level: DEBUG  # Verbose logging
```

### Production Setup

```yaml
# ~/.forge/config.yaml for production
generator:
  backend: codegen_api
  api_key: ${CODEGEN_API_KEY}
  org_id: ${CODEGEN_ORG_ID}
  timeout: 300

git:
  author_name: Forge CI
  author_email: ci@company.com
  commit_format: conventional

knowledgeforge:
  patterns_dir: /opt/forge/patterns
  embedding_model: all-MiniLM-L6-v2
  cache_size: 512  # Production cache
  search_method: hybrid

testing:
  use_docker: true  # Isolation required
  timeout: 600
  min_coverage: 90.0  # High coverage

pattern_store_path: /var/forge/patterns.db
state_db_path: /var/forge/state.db
log_level: INFO
log_file: /var/log/forge/forge.log
```

### CI/CD Setup

```yaml
# forge.yaml for CI/CD
generator:
  backend: codegen_api
  api_key: ${CI_CODEGEN_API_KEY}
  org_id: ${CI_CODEGEN_ORG_ID}
  timeout: 600  # Longer for CI

testing:
  use_docker: true
  timeout: 1200  # 20 minutes
  min_coverage: 85.0

log_level: INFO
log_file: null  # Log to stdout in CI
```

## Configuration Validation

Forge validates configuration on load using Pydantic.

### Common Validation Errors

**Missing Required Fields:**
```
✗ Invalid configuration: field required
```

**Invalid Values:**
```
✗ Invalid configuration: value is not a valid enumeration member
```

**Type Errors:**
```
✗ Invalid configuration: value is not a valid integer
```

### Debugging Configuration

```python
from forge.core.config import ForgeConfig

# Load and print config
config = ForgeConfig.load()
print(config.model_dump())

# Check specific values
print(f"Backend: {config.generator.backend}")
print(f"Patterns dir: {config.knowledgeforge.patterns_dir}")
print(f"Search method: {config.knowledgeforge.search_method}")
```

## Advanced Configuration

### Custom Patterns Directory

```yaml
knowledgeforge:
  patterns_dir: /custom/path/to/patterns
```

Then populate with patterns:

```bash
mkdir -p /custom/path/to/patterns
cp *.md /custom/path/to/patterns/
```

### Multiple Environments

```bash
# Development
cp forge.dev.yaml forge.yaml
forge doctor

# Production
cp forge.prod.yaml forge.yaml
forge doctor

# Or use different directories
cd ~/projects/dev && forge doctor
cd ~/projects/prod && forge doctor
```

### Programmatic Configuration

```python
from forge.core.config import ForgeConfig, GeneratorConfig

# Create custom config
config = ForgeConfig(
    generator=GeneratorConfig(
        backend="claude_code",
        timeout=600
    )
)

# Save to file
config.save("custom-config.yaml")

# Use custom config
from forge.core.orchestrator import Orchestrator
orchestrator = Orchestrator(config)
```

## Best Practices

### Security

✅ **DO:**
- Use environment variables for secrets
- Add `.env` to `.gitignore`
- Use global config for shared settings
- Rotate API keys regularly

❌ **DON'T:**
- Commit API keys to version control
- Share configuration files with secrets
- Use plain text for sensitive values

### Organization

✅ **DO:**
- Use project config for project-specific settings
- Use global config for user preferences
- Document non-obvious settings
- Keep configurations minimal

❌ **DON'T:**
- Duplicate settings across configs
- Override defaults unnecessarily
- Use absolute paths when relative work

### Performance

✅ **DO:**
- Use hybrid search for best results
- Increase cache size for heavy use
- Use keyword search for speed
- Adjust timeouts for your use case

❌ **DON'T:**
- Set cache too small (< 64)
- Use very short timeouts
- Disable caching entirely

## Troubleshooting

### Configuration Not Loading

Check file locations:

```bash
# Project config
ls -la forge.yaml

# Global config
ls -la ~/.forge/config.yaml

# Verify paths
pwd
```

### Environment Variables Not Working

Verify substitution:

```bash
# Check variable is set
echo $CODEGEN_API_KEY

# Test in Python
python3 -c "import os; print(os.getenv('CODEGEN_API_KEY'))"
```

### Invalid Configuration

Validate manually:

```python
from forge.core.config import ForgeConfig

try:
    config = ForgeConfig.load()
    print("✓ Configuration valid")
except Exception as e:
    print(f"✗ Configuration error: {e}")
```

## See Also

- [CLI Reference](cli-reference.md) - Command-line usage
- [API Reference](../api/core.md) - Configuration API
- [Troubleshooting](troubleshooting.md) - Common issues
- [Developer Guide](developer-guide.md) - Advanced topics
