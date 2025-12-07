# Troubleshooting Guide

Common issues and solutions for Forge.

## Quick Diagnostics

Run the doctor command to check your system:

```bash
forge doctor
```

This checks:
- Python version
- Required dependencies
- API key configuration
- Docker availability
- Pattern files
- Disk space

## Common Issues

### Installation Issues

#### Issue: `poetry install` fails

**Symptoms**:
```
No module named 'poetry'
```

**Solution**:
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Verify
poetry --version
```

#### Issue: Python version mismatch

**Symptoms**:
```
Error: Python 3.11+ required, found 3.9
```

**Solution**:
```bash
# Install Python 3.11
# macOS:
brew install python@3.11

# Linux:
sudo apt install python3.11

# Set Poetry to use 3.11
poetry env use python3.11
```

### Pattern Issues

#### Issue: Pattern files not found

**Symptoms**:
```
FileNotFoundError: Pattern file not found: 00_KB3_Core.md
Expected location: ../knowledgeforge-patterns/00_KB3_Core.md
```

**Solution**:
```bash
# Clone patterns repository
cd ..
git clone https://github.com/your-org/knowledgeforge-patterns.git

# Verify
ls ../knowledgeforge-patterns/*.md

# Or set custom path
export FORGE_PATTERNS_DIR=/path/to/patterns
```

#### Issue: Pattern search returns no results

**Symptoms**:
```
Warning: No relevant patterns found for query
```

**Solution**:
```bash
# Rebuild pattern embeddings cache
rm -rf ~/.forge/cache/embeddings
forge search "test query"

# The first search will rebuild the cache
```

### API Key Issues

#### Issue: Missing API key

**Symptoms**:
```
GitHubError: GitHub token required.
Set GITHUB_TOKEN environment variable or pass token parameter
```

**Solution**:
```bash
# Set for current session
export ANTHROPIC_API_KEY=your_key_here
export GITHUB_TOKEN=ghp_your_token_here

# Set permanently (add to ~/.bashrc or ~/.zshrc)
echo 'export ANTHROPIC_API_KEY=your_key_here' >> ~/.bashrc
source ~/.bashrc
```

#### Issue: Invalid API key

**Symptoms**:
```
API Error: Invalid authentication credentials
```

**Solution**:
```bash
# Verify key is correct
echo $ANTHROPIC_API_KEY  # Should show your key

# Test with curl
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json" \
  -d '{"model": "claude-3-sonnet-20240229", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 10}'

# Should return valid response, not 401
```

### Docker Issues

#### Issue: Docker daemon not running

**Symptoms**:
```
TestingError: Docker daemon not available
Please start Docker and try again
```

**Solution**:
```bash
# macOS: Start Docker Desktop application

# Linux: Start Docker service
sudo systemctl start docker

# Verify
docker ps  # Should show container list
```

#### Issue: Permission denied

**Symptoms**:
```
docker: Got permission denied while trying to connect
```

**Solution**:
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Or use sudo
sudo docker ps
```

#### Issue: Container build fails

**Symptoms**:
```
ERROR: failed to solve: failed to fetch
```

**Solution**:
```bash
# Check Docker disk space
docker system df

# Clean up if needed
docker system prune -a

# Retry build
forge test --project my-project
```

### Generation Issues

#### Issue: Code generation timeout

**Symptoms**:
```
GenerationError: API request timed out after 120s
```

**Solution**:
```bash
# Increase timeout in config
forge config --set generator.timeout 300

# Or reduce complexity
# - Break into smaller tasks
# - Use simpler tech stack
```

#### Issue: API rate limit exceeded

**Symptoms**:
```
API Error: Rate limit exceeded. Retry after 60s
```

**Solution**:
```bash
# Wait and retry
sleep 60
forge build --project my-project

# Or reduce parallel workers
forge build --project my-project --max-workers 2
```

#### Issue: Invalid generated code

**Symptoms**:
```
Syntax error in generated file: app.py
```

**Solution**:
```bash
# Use iterative refinement
forge iterate --project my-project

# This will automatically fix syntax errors
```

### Testing Issues

#### Issue: Tests fail to run

**Symptoms**:
```
TestingError: No test framework detected
```

**Solution**:
```bash
# Ensure requirements file exists
cat .forge/output/my-project/requirements.txt

# Add test framework if missing
echo "pytest>=7.0.0" >> .forge/output/my-project/requirements.txt

# Rebuild Docker image
forge test --project my-project
```

#### Issue: Tests timeout

**Symptoms**:
```
TestingError: Tests exceeded 300s timeout
```

**Solution**:
```bash
# Increase timeout
forge test --project my-project --timeout 600

# Or set in config
forge config --set testing.timeout 600
```

#### Issue: Security scan false positives

**Symptoms**:
```
Security vulnerability: Hardcoded secret in config.py
(But it's a placeholder, not real secret)
```

**Solution**:
```bash
# Skip security scan
forge test --project my-project --no-security

# Or add to allowlist in code:
# # nosec - This is a placeholder value
SECRET_KEY = "placeholder"
```

### Git Issues

#### Issue: Not a git repository

**Symptoms**:
```
GitError: Not a git repository: /path/to/project
```

**Solution**:
```bash
# Initialize git
cd .forge/output/my-project
git init
git add .
git commit -m "Initial commit"

# Add remote
git remote add origin https://github.com/user/repo.git
```

#### Issue: Branch already exists

**Symptoms**:
```
fatal: A branch named 'forge/feature-123' already exists
```

**Solution**:
```bash
# Delete existing branch
git branch -D forge/feature-123

# Or checkout existing
git checkout forge/feature-123
```

#### Issue: PR creation fails

**Symptoms**:
```
GitHubError: Could not parse GitHub repository from remote URL
```

**Solution**:
```bash
# Verify remote URL
git remote get-url origin

# Should be GitHub URL like:
# git@github.com:owner/repo.git
# or
# https://github.com/owner/repo.git

# Set if missing
git remote add origin git@github.com:owner/repo.git
```

### Deployment Issues

#### Issue: Platform config generation fails

**Symptoms**:
```
DeploymentError: Project path does not exist: /path/to/project
```

**Solution**:
```bash
# Verify project exists
ls .forge/output/my-project

# Use correct project ID
forge deploy --project-id my-project --platform flyio
```

#### Issue: Deployment fails

**Symptoms**:
```
Error: fly.toml not found
```

**Solution**:
```bash
# Generate configs first
forge deploy --project my-project --platform flyio

# Then deploy
cd .forge/output/my-project
fly deploy
```

## Performance Issues

### Slow pattern search

**Solution**:
```bash
# Enable caching
forge config --set knowledgeforge.cache_embeddings true

# Rebuild cache
rm -rf ~/.forge/cache/embeddings
forge search "test"  # First search rebuilds cache
```

### Slow code generation

**Solutions**:
```bash
# Enable parallel generation
forge config --set generator.parallel true
forge config --set generator.max_workers 8

# Use faster model (if available)
forge config --set generator.model claude-3-haiku-20240307
```

### High memory usage

**Solutions**:
```bash
# Reduce parallel workers
forge config --set generator.max_workers 2

# Clear cache
rm -rf ~/.forge/cache/*

# Process tasks sequentially
forge build --project my-project --max-workers 1
```

## Debug Techniques

### Enable debug logging

```bash
# Set log level
export FORGE_LOG_LEVEL=DEBUG

# Run command
forge build --project my-project

# Logs show detailed information:
# DEBUG: Loading pattern: 00_KB3_Core.md
# DEBUG: API request to anthropic
# DEBUG: Generated 245 lines of code
```

### Inspect state

```bash
# View project state
cat .forge/state/my-project/task_plan.json

# View test results
cat .forge/state/my-project/test_results.json

# View generated code
ls -la .forge/output/my-project/
```

### Profile performance

```python
import cProfile
import pstats
from forge.layers.generation import GenerationLayer

profiler = cProfile.Profile()
profiler.enable()

# Run operation
generator = GenerationLayer()
result = generator.generate_project(plan)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

## Getting Help

### Check documentation

1. [Architecture](./ARCHITECTURE.md) - System design
2. [API Reference](./API_REFERENCE.md) - Command details
3. [Git Workflows](./GIT_WORKFLOWS.md) - Git integration

### Search patterns

```bash
# Search for relevant troubleshooting patterns
forge search "error handling"
forge search "debugging techniques"
```

### Report issues

If none of the above solutions work:

1. **Gather information**:
   ```bash
   forge info --json > system-info.json
   forge doctor > doctor-output.txt
   ```

2. **Create minimal reproduction**:
   - Simplest project that shows the issue
   - Complete command sequence
   - Error messages

3. **Report**:
   - GitHub Issues: https://github.com/your-org/forge/issues
   - Include system info and reproduction steps
   - Attach logs if relevant

## Common Error Messages

### "No module named 'forge'"

**Cause**: Not in Poetry environment

**Fix**:
```bash
poetry shell
# or
poetry run forge <command>
```

### "Task decomposition failed"

**Cause**: Description too vague or complex

**Fix**:
- Be more specific in description
- Break into smaller pieces
- Provide tech stack hints

### "API quota exceeded"

**Cause**: Too many API calls

**Fix**:
- Wait for quota reset
- Use caching when possible
- Reduce parallel workers

### "Test framework not detected"

**Cause**: Missing test dependencies

**Fix**:
- Add pytest/jest to requirements
- Ensure test files follow naming convention
- Check test framework documentation

## Prevention

### Best Practices

1. **Use doctor regularly**:
   ```bash
   forge doctor
   ```

2. **Keep dependencies updated**:
   ```bash
   poetry update
   ```

3. **Clear cache periodically**:
   ```bash
   rm -rf ~/.forge/cache/*
   ```

4. **Monitor API usage**:
   - Track API calls
   - Set rate limit alerts
   - Use caching effectively

5. **Backup project state**:
   ```bash
   cp -r .forge/state .forge/state.backup
   ```

## Still Having Issues?

1. Run full diagnostic:
   ```bash
   forge doctor --verbose > diagnostic.txt
   ```

2. Check logs:
   ```bash
   tail -f ~/.forge/logs/forge.log
   ```

3. Try safe mode (minimal features):
   ```bash
   export FORGE_SAFE_MODE=true
   forge build --project my-project
   ```

4. Contact support with:
   - `diagnostic.txt`
   - Complete error message
   - Steps to reproduce
   - System information
