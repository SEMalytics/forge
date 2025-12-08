# CodeGen Repository Setup Guide

## Problem
CodeGen agents were working on the wrong repository because no `repo_id` was specified.

## Solution: Set Up CodeGen Repository Access

### Step 1: Install GitHub App (if not done)

1. Go to: **https://github.com/apps/codegen-sh**
2. Click **"Configure"** next to your organization (SEMalytics)
3. Grant access to the **SEMalytics/forge** repository
4. Click **"Install & Authorize"**

### Step 2: Find Your Repository ID

**Option A: Via CodeGen Web Portal**

1. Go to: **https://codegen.com/repos**
2. Find "forge" or "SEMalytics/forge" in the list
3. Click on it to view details
4. The URL will show the repo ID: `https://codegen.com/repos/[REPO_ID]`
5. Or check the repository settings page for the ID

**Option B: Via Agent Trace (after running an agent)**

1. Go to: **https://codegen.com/agents**
2. Click on any recent agent run
3. Look for the "SetActiveCodebase" tool card
4. It will show which repository was loaded

### Step 3: Set Environment Variable

Add to your `~/.zshrc` (or `~/.bashrc`):

```bash
export CODEGEN_REPO_ID=<your-repo-id-here>
```

Then reload:

```bash
source ~/.zshrc
```

### Step 4: Verify Setup

Run a test build:

```bash
forge build -p forge-web-ui-20251207
```

Check the logs for:
```
INFO     Using repository ID from CODEGEN_REPO_ID: <your-repo-id>
```

or

```
INFO     Found repository 'forge' with ID: <repo-id>
```

## Alternative: Auto-Detection

If you don't set `CODEGEN_REPO_ID`, Forge will try to auto-detect by searching for:
- "forge"
- "forge-web-ui"
- "SEMalytics/forge"

However, **explicit is better than implicit** - set the env var to be sure.

## Troubleshooting

### "No matching repository found"

**Problem:** Forge couldn't find a repository matching the search terms.

**Solutions:**
1. Check https://codegen.com/repos to see what repos are available
2. Make sure GitHub App has access to SEMalytics/forge
3. Set `CODEGEN_REPO_ID` explicitly

### "Agent worked on wrong project"

**Problem:** Agent run didn't use the correct repository.

**Solutions:**
1. Check the AgentTrace at https://codegen.com/agents
2. Look at "SetActiveCodebase" tool - which repo did it load?
3. Verify `CODEGEN_REPO_ID` is set correctly
4. Make sure you ran `source ~/.zshrc` after setting the variable

### "Repositories API returns 404"

**This is expected** - CodeGen doesn't have a public repositories list API endpoint. You must:
1. Use the web portal at https://codegen.com/repos
2. Or check agent traces to see available repos

## For New Projects

When creating a new project that needs CodeGen integration:

1. **Create GitHub Repository** (if needed)
2. **Install CodeGen GitHub App** on that repo
3. **Wait a few minutes** for sync
4. **Go to https://codegen.com/repos** to verify
5. **Get the repo ID** and set `CODEGEN_REPO_ID`

## Current Setup for Forge

Based on the planning session, the Forge Web UI project should:
- Work within the existing `SEMalytics/forge` repository
- Generate files to `.forge/output/forge-web-ui-20251207/`
- Have access to existing Forge codebase for context

**Recommended environment variables:**

```bash
export CODEGEN_API_KEY=<your-api-key>
export CODEGEN_ORG_ID=5249
export CODEGEN_REPO_ID=<your-forge-repo-id>  # Get this from codegen.com/repos
export ANTHROPIC_API_KEY=<your-claude-key>
export GITHUB_TOKEN=<your-github-token>
```

All of these should already be in your `~/.zshrc` file.
