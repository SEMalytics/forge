# Conventional Commits Pattern

**Category**: Development
**Difficulty**: Beginner
**Tags**: git, commits, versioning, changelog, automation

## Context

When working with Git in Forge, you need a consistent commit message format that enables automation, changelog generation, and semantic versioning.

## Problem

Inconsistent commit messages make it hard to:
- Understand what changed and why
- Generate changelogs automatically
- Determine semantic version bumps
- Search through project history
- Automate release processes

## Solution

Use the Conventional Commits specification for all commit messages:

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: New feature for the user
- **fix**: Bug fix for the user
- **docs**: Documentation changes
- **style**: Formatting, missing semicolons, etc (no code change)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvement
- **test**: Adding or updating tests
- **build**: Build system or dependencies
- **ci**: CI/CD configuration changes
- **chore**: Maintenance tasks, tooling

### Scope

Optional component name (auth, api, cli, testing, etc)

### Description

- Use imperative mood: "add feature" not "added feature"
- Don't capitalize first letter
- No period at the end
- Max 72 characters

### Breaking Changes

Add `!` after type/scope or add `BREAKING CHANGE:` footer

## Examples

### Basic Commits

```bash
# Feature
feat(api): add user authentication endpoint

# Bug fix
fix(auth): handle expired JWT tokens correctly

# Documentation
docs: update API reference for deployment commands

# Refactoring
refactor(cli): extract command validation logic

# Performance
perf(generation): enable parallel code generation
```

### With Body

```bash
feat(deployment): add Kubernetes config generation

Generates deployment.yaml and service.yaml files for Kubernetes
deployment. Includes configurable replicas, resources, and
environment variables.

Closes #123
```

### Breaking Changes

```bash
feat(api)!: change task plan JSON schema

BREAKING CHANGE: Task plan schema now requires `dependencies` field.
Migration guide available in docs/MIGRATION.md
```

## Forge Automation

Forge automates conventional commits:

### Auto-Generation from Changes

```bash
# Forge analyzes changed files and generates commit message
forge pr --project my-api
# → Generates: "feat(api): add user management endpoints"
```

### Auto-Generation from Tasks

```python
from forge.git.commits import CommitStrategy

# Generate commit from task
commit = CommitStrategy.from_task(
    task_description="Add authentication system",
    files_changed=["auth/login.py", "auth/middleware.py"],
    scope="auth"
)

print(commit.format())
# → "feat(auth): add authentication system"
```

### Auto-Generation from Fixes

```python
# Generate fix commit
commit = CommitStrategy.from_fix(
    issue="123",
    description="handle null values in user profile",
    files_changed=["api/users.py"]
)

print(commit.format())
# → "fix(api): handle null values in user profile\n\nCloses #123"
```

## Best Practices

### 1. One Logical Change Per Commit

```bash
# Good: Single purpose
feat(auth): add JWT token validation

# Bad: Multiple unrelated changes
feat(auth): add JWT validation and fix user profile bug and update docs
```

### 2. Write Clear Descriptions

```bash
# Good: Specific and actionable
fix(api): prevent race condition in concurrent requests

# Bad: Vague
fix: fix bug
```

### 3. Use Scope for Large Projects

```bash
# For monorepos or large projects
feat(cli): add deploy command
feat(api): add health check endpoint
feat(testing): add security scanner
```

### 4. Include Issue References

```bash
feat(deployment): add Vercel config generation

Closes #45
Relates-to: #32
```

### 5. Explain "Why" in Body

```bash
refactor(generation): switch to async generation

The previous synchronous approach blocked the main thread
during large file generation. Async generation improves
responsiveness and enables better progress reporting.
```

## Semantic Versioning Impact

Conventional commits enable automatic version bumps:

```
feat → MINOR version bump (0.1.0 → 0.2.0)
fix  → PATCH version bump (0.1.0 → 0.1.1)
feat! or BREAKING CHANGE → MAJOR version bump (0.1.0 → 1.0.0)
```

## CLI Usage

```bash
# Manual commit with conventional format
git commit -m "feat(deployment): add fly.io support"

# Let Forge generate it
forge pr --project my-api
# Automatically analyzes changes and creates conventional commit

# View commit strategy
forge stats --project my-api
# Shows commit history with conventional format
```

## Python API

```python
from forge.git.commits import ConventionalCommit, CommitType

# Create commit
commit = ConventionalCommit(
    type=CommitType.FEAT,
    scope="api",
    description="add rate limiting middleware",
    body="Implements token bucket algorithm with configurable limits",
    issues=["45"],
    breaking=False
)

# Format for git
message = commit.format()

# Parse existing commit
parsed = ConventionalCommit.parse("feat(api): add auth\n\nCloses #123")
print(parsed.type)  # CommitType.FEAT
print(parsed.issues)  # ["123"]
```

## Integration with Forge Workflows

### PR Creation

```bash
forge pr --project my-api
# 1. Analyzes all commits since branch creation
# 2. Generates PR title from commits
# 3. Creates checklist based on changes
# 4. Links all referenced issues
```

### Deployment

```bash
forge deploy --project my-api --platform flyio --create-pr
# 1. Commits deployment configs with conventional message
# 2. Creates PR with deployment checklist
# 3. Links to deployment documentation
```

## Related Patterns

- **pr-workflows.md** - Pull request automation
- **git-workflows.md** - Complete Git integration
- **changelog-generation.md** - Automatic changelog creation

## References

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Git Workflows Documentation](../../docs/GIT_WORKFLOWS.md)
- [Forge Commits Module](../../src/forge/git/commits.py)
