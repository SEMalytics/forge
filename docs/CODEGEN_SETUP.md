# CodeGen Setup Guide

This guide helps you configure Forge to work with CodeGen's API.

## Prerequisites

1. **CodeGen Account**: Sign up at [codegen.com](https://codegen.com)
2. **GitHub App Installed**: Install at [github.com/apps/codegen-sh](https://github.com/apps/codegen-sh)
3. **API Token**: Get your token from [codegen.com/token](https://codegen.com/token)

## Configuration Steps

### 1. Get Your API Credentials

```bash
# Your API token (from https://codegen.com/token)
CODEGEN_API_KEY=sk-xxxxx

# Your organization ID (from https://codegen.com/settings)
CODEGEN_ORG_ID=5249
```

### 2. Find Your Repository ID (CRITICAL)

The `repo_id` is a **unique integer** that identifies your repository within CodeGen. Using the wrong `repo_id` causes agents to work on the wrong codebase.

#### Method 1: Web UI (Easiest)

1. Go to: [codegen.com/repos](https://codegen.com/repos)
2. Click on your repository
3. Look at the URL: `https://www.codegen.com/repos/{repo_name}/...`
4. Or find it in repository settings

#### Method 2: Using Forge Script

```bash
# List all repositories with their IDs
poetry run python scripts/list_repos.py
```

Output:
```
Found 3 repositories:

┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┓
┃ ID     ┃ Name             ┃ Full Name                 ┃ Language ┃ Status    ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━┩
│ 184372 │ SEMalytics-forge │ internexio/SEMalytics-fo… │ PYTHON   │ SETUP     │
└────────┴──────────────────┴───────────────────────────┴──────────┴───────────┘
```

The first column is your `repo_id`.

#### Method 3: API Call

```bash
# List all repositories in your organization
curl -s "https://api.codegen.com/v1/organizations/$CODEGEN_ORG_ID/repos" \
  -H "Authorization: Bearer $CODEGEN_API_KEY" | jq '.items[] | {id, name, full_name}'
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```bash
# Anthropic API (for Claude)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# CodeGen API
CODEGEN_API_KEY=sk-77fa5fb1-xxxx-xxxx-xxxx-xxxxxxxxxxxx
CODEGEN_ORG_ID=5249
CODEGEN_REPO_ID=184372  # Your repository ID

# GitHub API
GITHUB_TOKEN=ghp_xxxxx
```

### 4. Set Up Your Repository

Repositories need **setup commands** configured before agents can push code. Setup commands are initialization scripts (like `poetry install` or `npm install`) that run when the sandbox is created.

#### Option A: Web UI (Recommended)

1. Go to [codegen.com/repos](https://codegen.com/repos)
2. Select your repository
3. Navigate to "Setup Commands"
4. Click "Generate Setup Commands" (or enter manually)
5. Wait for the agent to analyze your repo (~1-3 minutes)
6. Review and save the generated commands

#### Option B: Using Forge Script

```bash
# Automatically generate setup commands via API
poetry run python scripts/setup_repository.py SEMalytics-forge

# Or with custom instructions
poetry run python scripts/setup_repository.py SEMalytics-forge "Use poetry for dependency management"
```

### 5. Verify Configuration

Run the health check:

```bash
poetry run forge doctor
```

Expected output:
```
✓ CODEGEN_API_KEY is set
✓ CodeGen API: Connected (org: 5249)
✓ CODEGEN_ORG_ID is set: 5249
✓ CODEGEN_REPO_ID is set: 184372
```

Check repository status:

```bash
poetry run python scripts/list_repos.py
```

Look for your repository - the status should be **SETUP** (not NOT_SETUP).

## Troubleshooting

### Issue: Agents work on wrong repository

**Cause**: `CODEGEN_REPO_ID` not set or incorrect

**Solution**:
1. Run `poetry run python scripts/list_repos.py`
2. Copy the correct `id` for your repository
3. Update `CODEGEN_REPO_ID` in `.env`

### Issue: Repository shows "NOT_SETUP" status

**Cause**: Setup commands not configured

**Solution**:
1. Go to [codegen.com/repos](https://codegen.com/repos)
2. Select your repository → Setup Commands
3. Generate or manually configure setup commands
4. Wait for setup to complete

Or use the script:
```bash
poetry run python scripts/setup_repository.py <repo_name_or_id>
```

### Issue: Agent completes but doesn't push code

**Cause**: Repository not properly linked or setup incomplete

**Solution**:
1. Verify GitHub App is installed: [github.com/apps/codegen-sh](https://github.com/apps/codegen-sh)
2. Check repository has proper permissions
3. Ensure setup commands are configured
4. Verify `setup_status` is not "NOT_SETUP"

### Issue: Authentication errors

**Cause**: Invalid or expired API token

**Solution**:
1. Get fresh token from [codegen.com/token](https://codegen.com/token)
2. Update `CODEGEN_API_KEY` in `.env`
3. Test with `poetry run forge doctor`

## Advanced Configuration

### Multiple Repositories

If you work with multiple repositories, you can:

1. **Override per build**:
   ```bash
   CODEGEN_REPO_ID=123456 poetry run forge build --project-id my-project
   ```

2. **Project-specific .env**:
   Create `.env.local` in project directories
   ```bash
   # .env.local
   CODEGEN_REPO_ID=123456  # Override for this project
   ```

### Auto-Detect Repository

Forge can auto-detect your repository based on git remote:

```bash
# If git remote matches a CodeGen repository, it will be used
git remote -v
# origin  https://github.com/internexio/SEMalytics-forge.git (fetch)
```

This matches `internexio/SEMalytics-forge` in CodeGen automatically.

## Security Notes

- **Never commit `.env`**: It's already in `.gitignore`
- **Rotate tokens regularly**: Generate new tokens periodically
- **Use minimal permissions**: GitHub token only needs repo access
- **Project isolation**: Use different tokens for different projects

## Next Steps

Once configured, you can:

1. **Start a build**:
   ```bash
   poetry run forge build --project-id my-project
   ```

2. **Monitor agent runs**:
   ```bash
   poetry run python scripts/check_agent_run.py <agent_run_id>
   ```

3. **Debug issues**:
   ```bash
   poetry run python scripts/analyze_agent_logs.py <agent_run_id>
   ```

## Resources

- **CodeGen Docs**: [docs.codegen.com](https://docs.codegen.com)
- **API Reference**: [docs.codegen.com/api-reference](https://docs.codegen.com/api-reference)
- **GitHub Integration**: [docs.codegen.com/integrations/github](https://docs.codegen.com/integrations/github)
- **Support**: Contact CodeGen support or check Forge GitHub issues
