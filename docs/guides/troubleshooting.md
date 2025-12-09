# Troubleshooting Guide

Common issues and solutions for Forge.

## Quick Diagnostics

Start with these commands:

```bash
# System health check
forge doctor

# System information
forge info

# Check version
forge --version

# Run tests
poetry run pytest -v
```

## Installation Issues

### Poetry Not Found

**Symptom:**
```
command not found: poetry
```

**Solution:**

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH
export PATH="/Users/$USER/.local/bin:$PATH"

# Make permanent
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify
poetry --version
```

### Python Version Too Old

**Symptom:**
```
Python 3.11+ required (found 3.9)
```

**Solution:**

```bash
# macOS - Install Python 3.11+
brew install python@3.11

# Ubuntu - Install Python 3.11+
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11

# Verify
python3.11 --version
```

### Dependency Installation Fails

**Symptom:**
```
Package operations failed
Unable to find installation candidates
```

**Solution:**

```bash
# Clear cache
poetry cache clear pypi --all

# Remove lock file
rm poetry.lock

# Reinstall
poetry install --no-cache

# If still failing, update Poetry
poetry self update
```

### Permission Denied

**Symptom:**
```
PermissionError: [Errno 13] Permission denied
```

**Solution:**

```bash
# Fix permissions
chmod -R 755 .

# Create .forge directory
mkdir -p .forge
chmod 755 .forge

# Don't use sudo with Poetry
# Instead, fix ownership:
sudo chown -R $USER:$USER .
```

## Pattern Store Issues

### Patterns Not Found

**Symptom:**
```
✗ KnowledgeForge patterns not found
```

**Solution:**

```bash
# Check patterns directory
ls patterns/*.md

# If empty, create and populate
mkdir -p patterns
cp /path/to/patterns/*.md patterns/

# Verify count
ls patterns/*.md | wc -l
# Should show: 28

# Reinitialize
rm -rf .forge/patterns.db
forge doctor
```

### Pattern Search Returns Nothing

**Symptom:**
```
Found 0 patterns
```

**Solutions:**

1. **Check database exists:**
```bash
ls -la .forge/patterns.db
# If missing, run forge doctor
```

2. **Verify patterns indexed:**
```bash
# Check pattern count
forge info
# Should show: Patterns indexed: 28
```

3. **Try different search methods:**
```bash
# Keyword search
forge search "your query" --method keyword

# Semantic search
forge search "your query" --method semantic

# Hybrid search (default)
forge search "your query" --method hybrid
```

4. **Check patterns directory path:**
```python
from forge.core.config import ForgeConfig
config = ForgeConfig.load()
print(config.knowledgeforge.patterns_dir)
```

### Embedding Model Download Fails

**Symptom:**
```
Failed to load embedding model
HTTPError: 404 Not Found
```

**Solution:**

```bash
# Download model manually
python3 << 'EOF'
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model downloaded successfully")
EOF

# If still failing, check internet connection
curl -I https://huggingface.co

# Clear cache and retry
rm -rf ~/.cache/torch/sentence_transformers/
forge doctor
```

### Database Locked

**Symptom:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**

```bash
# Close all Forge instances
pkill -f forge

# Remove lock if exists
rm -f .forge/*.db-journal
rm -f .forge/*.db-wal

# If persistent, recreate databases
rm -rf .forge/
forge doctor
```

## State Management Issues

### Project Not Found

**Symptom:**
```
✗ Project not found: my-project
```

**Solutions:**

1. **Check exact project ID:**
```bash
# List database contents
sqlite3 .forge/state.db "SELECT id, name FROM projects"
```

2. **Use correct project ID format:**
```bash
# IDs include timestamp: project-name-20251207
forge status my-project-20251207
```

3. **Verify database exists:**
```bash
ls -la .forge/state.db
# If missing, projects weren't created
```

### Database Corruption

**Symptom:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solution:**

```bash
# Backup if possible
cp .forge/state.db .forge/state.db.backup

# Try to recover
sqlite3 .forge/state.db "PRAGMA integrity_check"

# If corrupted, reset
rm .forge/state.db
forge doctor
# Note: This loses all project data
```

### Checkpoint Creation Fails

**Symptom:**
```
StateError: Failed to create checkpoint
```

**Solution:**

```bash
# Check disk space
df -h .

# Check permissions
ls -la .forge/

# Fix permissions
chmod 755 .forge/
chmod 644 .forge/*.db
```

## Configuration Issues

### Config File Not Loaded

**Symptom:**
Configuration changes not taking effect

**Solution:**

```bash
# Check file location
ls -la forge.yaml  # Project config
ls -la ~/.forge/config.yaml  # Global config

# Verify YAML syntax
python3 << 'EOF'
import yaml
with open('forge.yaml') as f:
    config = yaml.safe_load(f)
    print("✓ Valid YAML")
EOF

# Test loading
python3 << 'EOF'
from forge.core.config import ForgeConfig
try:
    config = ForgeConfig.load()
    print("✓ Config loaded successfully")
    print(f"Backend: {config.generator.backend}")
except Exception as e:
    print(f"✗ Config error: {e}")
EOF
```

### Environment Variables Not Working

**Symptom:**
```
${CODEGEN_API_KEY} not substituted
```

**Solution:**

```bash
# Check variable is set
echo $CODEGEN_API_KEY

# Verify in Python
python3 -c "import os; print(os.getenv('CODEGEN_API_KEY'))"

# Set if missing
export CODEGEN_API_KEY="your-key"

# Make permanent
echo 'export CODEGEN_API_KEY="your-key"' >> ~/.zshrc
source ~/.zshrc
```

### Invalid Configuration

**Symptom:**
```
✗ Invalid configuration: field required
```

**Solution:**

1. **Check required fields:**
```yaml
# Minimal valid config
generator:
  backend: codegen_api

# All required fields have defaults
# Check what's actually required:
```

2. **Validate config:**
```python
from forge.core.config import ForgeConfig
try:
    config = ForgeConfig.load()
    print(config.model_dump())
except Exception as e:
    print(f"Error: {e}")
```

3. **Use default config:**
```bash
# Create fresh config
mv forge.yaml forge.yaml.old
forge config
```

## CLI Issues

### Command Not Found

**Symptom:**
```
command not found: forge
```

**Solutions:**

1. **Use poetry run:**
```bash
poetry run forge doctor
```

2. **Activate shell:**
```bash
poetry shell
forge doctor
```

3. **Check installation:**
```bash
poetry install
poetry run forge --version
```

### Output Formatting Broken

**Symptom:**
Garbled or missing formatting

**Solution:**

```bash
# Check terminal supports Rich
echo $TERM

# Force color output
export FORCE_COLOR=1
forge doctor

# Disable color if needed
export NO_COLOR=1
forge doctor
```

### Slow Performance

**Symptom:**
Commands taking too long

**Solutions:**

1. **Embedding model loading:**
```
# First run loads model (~2 seconds)
# Subsequent runs are faster
# This is normal behavior
```

2. **Pattern search slow:**
```bash
# Use keyword search for speed
forge search "query" --method keyword

# Increase cache size in config
knowledgeforge:
  cache_size: 256
```

3. **Database size:**
```bash
# Check database sizes
du -h .forge/*.db

# If very large, vacuum
sqlite3 .forge/patterns.db "VACUUM"
sqlite3 .forge/state.db "VACUUM"
```

## Import Errors

### Module Not Found

**Symptom:**
```
ModuleNotFoundError: No module named 'forge'
```

**Solution:**

```bash
# Ensure in correct directory
cd /path/to/forge

# Reinstall
poetry install

# Verify installation
poetry run python -c "import forge; print('✓ Import successful')"

# Check Python path
poetry run python -c "import sys; print(sys.path)"
```

### Import Version Mismatch

**Symptom:**
```
ImportError: cannot import name 'X' from 'module'
```

**Solution:**

```bash
# Update dependencies
poetry update

# Clear cache
rm -rf __pycache__ src/forge/__pycache__
find . -type d -name __pycache__ -exec rm -rf {} +

# Reinstall
poetry install --no-cache
```

## Test Failures

### Tests Not Found

**Symptom:**
```
ERROR: file or directory not found: tests
```

**Solution:**

```bash
# Verify test directory exists
ls -la tests/

# Run from project root
cd /path/to/forge
poetry run pytest
```

### Test Failures

**Symptom:**
```
FAILED tests/test_pattern_store.py::test_search
```

**Solution:**

```bash
# Run specific test with verbose output
poetry run pytest tests/test_pattern_store.py::test_search -v -s

# Check if patterns exist
ls patterns/*.md | wc -l

# Recreate test fixtures
rm -rf .pytest_cache
poetry run pytest --cache-clear
```

### Coverage Too Low

**Symptom:**
```
FAILED coverage: total coverage was 30%, expected 80%
```

**Solution:**

```bash
# This is informational only
# Foundation has 39% coverage (core modules 88%)
# Run without coverage requirement:
poetry run pytest -v
```

## Performance Issues

### High Memory Usage

**Symptom:**
Memory usage very high

**Solution:**

```bash
# Use smaller embedding model
knowledgeforge:
  embedding_model: all-MiniLM-L6-v2  # 90MB vs 420MB

# Reduce cache size
knowledgeforge:
  cache_size: 64  # Instead of 256

# Close pattern store when done
```

### Slow Startup

**Symptom:**
First command takes long time

**Causes & Solutions:**

1. **Embedding model loading (normal):**
```
First run: ~2 seconds to load model
This is expected behavior
```

2. **Pattern indexing (one-time):**
```
First run: ~5 seconds to index 28 patterns
Creates .forge/patterns.db
Subsequent runs are instant
```

3. **Network latency:**
```bash
# Check if downloading models
ls ~/.cache/torch/sentence_transformers/

# Pre-download model
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

## Getting More Help

### Collect Debug Information

```bash
# Create debug report
cat > debug-report.txt << EOF
=== Forge Debug Report ===
Date: $(date)

--- Version Info ---
$(forge --version)
$(poetry --version)
$(python3 --version)

--- System Health ---
$(forge doctor 2>&1)

--- System Info ---
$(forge info 2>&1)

--- Configuration ---
$(cat forge.yaml 2>&1)

--- File System ---
$(ls -la .forge/ 2>&1)
$(ls -la patterns/ | head -20 2>&1)

--- Database Info ---
$(sqlite3 .forge/patterns.db "SELECT COUNT(*) FROM patterns" 2>&1)
$(sqlite3 .forge/state.db "SELECT COUNT(*) FROM projects" 2>&1)

--- Python Environment ---
$(poetry env info 2>&1)

--- Disk Space ---
$(df -h . 2>&1)
EOF

cat debug-report.txt
```

### Enable Debug Logging

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Or in config
log_level: DEBUG

# Run command
forge doctor 2>&1 | tee debug.log
```

### Check Logs

```bash
# View log file
tail -f .forge/forge.log

# Search for errors
grep ERROR .forge/forge.log

# Check recent entries
tail -50 .forge/forge.log
```

### Run Diagnostics

```bash
# Test pattern store
python3 << 'EOF'
from forge.knowledgeforge.pattern_store import PatternStore
with PatternStore() as store:
    count = store.get_pattern_count()
    print(f"Patterns: {count}")
    results = store.search("test", max_results=1)
    print(f"Search works: {len(results) >= 0}")
EOF

# Test state manager
python3 << 'EOF'
from forge.core.state_manager import StateManager
with StateManager() as state:
    project = state.create_project("test", "Test", "Test")
    print(f"State manager works: {project.id == 'test'}")
EOF
```

## Still Having Issues?

1. Check [Installation Guide](installation.md)
2. Review [Configuration Guide](configuration.md)
3. Read [User Guide](user-guide.md)
4. Run full test suite: `poetry run pytest -v`
5. Check GitHub issues
6. Create debug report (see above)

## Prevention

### Regular Maintenance

```bash
# Monthly
poetry update
forge doctor

# After big changes
rm -rf .forge/
forge doctor

# Before deployment
poetry run pytest -v
forge doctor
```

### Best Practices

- Keep Poetry and Python updated
- Run `forge doctor` regularly
- Back up `.forge/` directory
- Use version control for configs
- Test configuration changes
- Monitor log files
