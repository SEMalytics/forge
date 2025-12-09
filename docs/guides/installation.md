# Installation Guide

Complete guide to installing Forge on your system.

## Prerequisites

### Required
- **Python 3.11 or higher**
- **Git** (for version control)

### Optional
- **Docker** (for isolated testing)
- **Poetry** (will be installed if not present)

## System Requirements

- **OS**: macOS, Linux, or Windows (with WSL2)
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 500MB for dependencies + embeddings model

## Installation Steps

### 1. Install Poetry

Poetry is Forge's dependency manager.

#### macOS/Linux

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

#### Add Poetry to PATH

```bash
export PATH="/Users/$USER/.local/bin:$PATH"

# Make permanent (zsh)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc

# Make permanent (bash)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

#### Verify Installation

```bash
poetry --version
# Output: Poetry (version 2.2.1)
```

### 2. Clone/Download Forge

```bash
cd /path/to/your/projects
# If you have Forge in a directory already:
cd forge
```

### 3. Install Dependencies

```bash
# Install all dependencies
poetry install

# This will:
# - Create a virtual environment
# - Install 63+ dependencies
# - Install Forge CLI
# - Download embedding model (~90MB)
```

Expected output:
```
Updating dependencies
Resolving dependencies...
Package operations: 63 installs, 0 updates, 0 removals
...
Installing the current project: forge (1.0.0)
```

**Note**: First install will download the sentence-transformers model (~90MB). This is normal and only happens once.

### 4. Verify Installation

```bash
# Check Forge version
poetry run forge --version
# Output: forge, version 1.0.0

# Run system health check
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

### 5. Set Up KnowledgeForge Patterns

Forge requires KnowledgeForge patterns in a sibling directory:

```bash
# Create patterns directory
mkdir -p patterns

# Copy your .md pattern files there
cp /path/to/patterns/*.md patterns/

# Verify patterns
ls patterns/*.md | wc -l
# Should show: 28
```

### 6. Optional: Configure Forge

Create a configuration file:

```bash
# Project config (recommended)
poetry run forge config

# Global config (applies to all projects)
poetry run forge config --global-config
```

This creates `forge.yaml` with default settings.

## Post-Installation

### Activate Virtual Environment (Optional)

For easier command usage without `poetry run`:

```bash
poetry shell

# Now you can run commands directly:
forge doctor
forge search "patterns"

# Exit when done:
exit
```

### Configure Environment Variables

If using CodeGen API:

```bash
# Add to ~/.zshrc or ~/.bashrc
export CODEGEN_API_KEY="your-api-key"
export CODEGEN_ORG_ID="your-org-id"
```

### Test the Installation

Run the test suite:

```bash
poetry run pytest -v

# Expected: 26 passed in ~17s
```

## Docker Installation (Optional)

For isolated testing capabilities:

### macOS

```bash
brew install --cask docker
# Or download from: https://www.docker.com/products/docker-desktop
```

### Linux

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io

# Enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
```

### Verify Docker

```bash
docker --version
docker run hello-world
```

## Troubleshooting Installation

### Poetry Installation Issues

If `curl` command fails:

```bash
# Download installer manually
wget https://install.python-poetry.org -O install-poetry.py
python3 install-poetry.py
```

### Python Version Issues

Check Python version:

```bash
python3 --version
# Must be 3.11 or higher
```

If too old, install Python 3.11+:

```bash
# macOS
brew install python@3.11

# Ubuntu
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.11
```

### Dependency Installation Failures

Clear cache and retry:

```bash
poetry cache clear pypi --all
poetry install --no-cache
```

### Pattern Store Issues

If patterns aren't found:

```bash
# Check directory structure
ls -la patterns/

# Should show .md files
# If not, create and populate:
mkdir -p patterns
# Copy your pattern files
```

### Permission Errors

```bash
# Ensure Forge directory is writable
chmod -R 755 .

# Create .forge directory manually
mkdir -p .forge
chmod 755 .forge
```

### ImportError Issues

Ensure you're using Poetry's environment:

```bash
# Show which Python
poetry run which python

# Should point to Poetry's virtual environment
# Example: ~/.cache/pypoetry/virtualenvs/forge-*/bin/python
```

## Uninstalling

### Remove Forge

```bash
# Remove virtual environment
poetry env remove python

# Remove installed files
rm -rf .venv/
rm -rf dist/
rm -rf *.egg-info/
```

### Remove Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 - --uninstall
```

### Remove Data

```bash
# Remove project data
rm -rf .forge/

# Remove global config
rm -rf ~/.forge/
```

## Next Steps

After successful installation:

1. Read the [Quick Start Guide](quickstart.md)
2. Follow the [Tutorial](tutorial.md)
3. Review the [User Guide](user-guide.md)
4. Configure Forge: [Configuration Guide](configuration.md)

## Platform-Specific Notes

### macOS

- Use `zsh` (default shell)
- Homebrew recommended for dependencies
- Docker Desktop provides easy Docker setup

### Linux

- Use `bash` or `zsh`
- Package manager varies by distribution
- Docker requires additional setup

### Windows (WSL2)

- Install WSL2 first
- Use Ubuntu 20.04+ in WSL
- Follow Linux instructions within WSL

## Updating Forge

```bash
# Update dependencies
poetry update

# Update to specific version
poetry add forge@^1.1.0

# Check for updates
poetry show --outdated
```

## Getting Help

If you encounter issues:

1. Run `forge doctor` to check system health
2. Check [Troubleshooting Guide](troubleshooting.md)
3. Review error messages carefully
4. Run tests: `poetry run pytest -v`
5. Check Python version: `python3 --version`

## Verification Checklist

After installation, verify:

- [ ] `poetry --version` shows Poetry 2.2.1+
- [ ] `poetry run forge --version` shows forge 1.0.0
- [ ] `poetry run forge doctor` passes all checks
- [ ] `ls patterns/*.md` shows 28 files
- [ ] `poetry run pytest` shows 26 tests passing
- [ ] `.forge/patterns.db` exists after running `forge doctor`

Once all items are checked, you're ready to use Forge!
