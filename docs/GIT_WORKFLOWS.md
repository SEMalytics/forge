# Git Workflows, PR Creation, and Deployment

## Overview

Forge provides comprehensive Git workflow automation with support for:
- Conventional commits
- Branch management with `forge/*` naming
- Automated PR creation with checklists
- Multi-platform deployment configurations
- GitHub integration

## Architecture

### Components

1. **Git Repository** (`git/repository.py`)
   - Branch management
   - Commit operations
   - Status tracking
   - Conflict detection
   - Push/pull operations

2. **Commit Strategies** (`git/commits.py`)
   - Conventional commit format
   - Auto-generated commit messages
   - Task-based commits
   - Fix commits
   - Commit merging

3. **GitHub Client** (`integrations/github_client.py`)
   - Create PRs with checklists
   - Add labels and reviewers
   - Comment on PRs
   - Merge PRs
   - Issue management

4. **Deployment Generator** (`layers/deployment.py`)
   - fly.io configurations
   - Vercel configurations
   - AWS Lambda (SAM)
   - Docker/Docker Compose
   - Kubernetes manifests

## Usage

### Creating Pull Requests

```bash
# Create PR for current project
forge pr --project-id my-project

# Create PR with custom title
forge pr --project-id my-project --title "feat: add authentication"

# Add reviewers and labels
forge pr --project-id my-project \
  --reviewers alice,bob \
  --labels bug,urgent

# Create draft PR
forge pr --project-id my-project --draft
```

The `pr` command automatically:
1. Creates a commit for uncommitted changes
2. Pushes the branch to remote
3. Generates a comprehensive PR description
4. Adds a review checklist
5. Links related issues

### Deployment Configuration

```bash
# Generate fly.io deployment config
forge deploy --project-id my-api --platform flyio

# Generate Vercel config for Node.js app
forge deploy --project-id my-app \
  --platform vercel \
  --runtime node \
  --port 3000

# Generate Docker config
forge deploy --project-id my-service --platform docker

# Generate Kubernetes manifests
forge deploy --project-id my-service --platform k8s

# Generate config and create PR
forge deploy --project-id my-api \
  --platform flyio \
  --create-pr
```

### Programmatic Usage

#### Git Operations

```python
from forge.git.repository import ForgeRepository

# Initialize repository
repo = ForgeRepository(".")

# Get status
status = repo.get_status()
print(f"Branch: {status.branch}")
print(f"Staged files: {len(status.staged_files)}")

# Create feature branch
branch = repo.create_feature_branch("authentication")
# Creates: forge/authentication-20250107-143000

# Add files and commit
repo.add_files(["auth/login.py", "auth/register.py"])
repo.commit("feat(auth): add authentication system")

# Push to remote
repo.push(set_upstream=True)

# Detect conflicts
conflicts = repo.detect_conflicts()
if conflicts:
    print(f"Conflicts in: {', '.join(conflicts)}")
```

#### Conventional Commits

```python
from forge.git.commits import ConventionalCommit, CommitType, CommitStrategy

# Create conventional commit
commit = ConventionalCommit(
    type=CommitType.FEAT,
    description="add user authentication",
    scope="auth",
    body="Implemented JWT-based authentication",
    issues=["123"],
    breaking=False
)

# Format commit message
message = commit.format()
# Output:
# feat(auth): add user authentication
#
# Implemented JWT-based authentication
#
# Closes #123

# Auto-generate from task
commit = CommitStrategy.from_task(
    task_description="Add database migration",
    files_changed=["migrations/001_users.sql"],
    scope="database"
)

# Auto-generate from files
commit = CommitStrategy.from_changes(
    files_changed=["test_auth.py", "test_user.py"]
)
# Infers type=TEST, scope from files
```

#### GitHub PR Creation

```python
from forge.integrations.github_client import GitHubClient

# Initialize client (requires GITHUB_TOKEN env var)
github = GitHubClient("owner/repo")

# Create PR with checklist
pr = github.create_pr_with_checklist(
    title="feat: add authentication system",
    description="Adds JWT-based authentication",
    head="forge/auth-123456",
    base="main",
    checklist_items=[
        "Review authentication logic",
        "Test login/logout flows",
        "Verify token expiration"
    ],
    issues=["42"],
    labels=["feature", "auth"],
    reviewers=["alice", "bob"]
)

print(f"Created PR: {pr.html_url}")

# Add comment to PR
github.comment_on_pr(
    pr_number=pr.number,
    comment="Please review the authentication implementation"
)

# Merge PR
github.merge_pr(
    pr_number=pr.number,
    merge_method="squash",
    commit_title="feat: add authentication system"
)
```

#### Deployment Configuration

```python
from forge.layers.deployment import DeploymentGenerator, DeploymentConfig, Platform
from pathlib import Path

# Initialize generator
generator = DeploymentGenerator(Path("./my-project"))

# Create deployment config
config = DeploymentConfig(
    platform=Platform.FLYIO,
    project_name="my-api",
    runtime="python",
    entry_point="app.py",
    environment_vars={
        "PORT": "8080",
        "DATABASE_URL": "postgres://..."
    },
    port=8080,
    region="lax"
)

# Generate configurations
files = generator.generate_configs(config)

for file in files:
    print(f"Generated: {file}")
# Output:
# Generated: fly.toml
# Generated: Dockerfile
```

## Conventional Commit Format

Forge follows the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code formatting
- **refactor**: Code restructuring
- **perf**: Performance improvements
- **test**: Test additions/changes
- **build**: Build system changes
- **ci**: CI/CD changes
- **chore**: Maintenance tasks
- **revert**: Revert previous commit

### Examples

```
feat(auth): add JWT authentication

Implemented token-based authentication using JWT.

Closes #123
```

```
fix(api): resolve race condition in user creation

The user creation endpoint had a race condition when
multiple requests arrived simultaneously.

Fixes #456
```

```
feat!: redesign API endpoints

BREAKING CHANGE: API endpoints have been redesigned.
See migration guide for details.
```

## Branch Naming Convention

Forge uses the `forge/*` naming pattern for feature branches:

```
forge/{feature-name}-{timestamp}
```

Examples:
- `forge/authentication-20250107-143000`
- `forge/deploy-flyio-20250107-150000`
- `forge/fix-login-bug-20250107-160000`

Benefits:
- Clear identification of Forge-generated branches
- Unique timestamps prevent conflicts
- Easy filtering in git commands

## Deployment Platforms

### fly.io

Generated files:
- `fly.toml` - Fly.io configuration
- `Dockerfile` - Container definition

Deployment steps:
```bash
fly apps create my-app
fly deploy
```

### Vercel

Generated files:
- `vercel.json` - Vercel configuration

Deployment steps:
```bash
vercel
```

### AWS Lambda

Generated files:
- `template.yaml` - SAM template

Deployment steps:
```bash
sam build
sam deploy --guided
```

### Docker

Generated files:
- `Dockerfile` - Container definition
- `docker-compose.yml` - Compose configuration
- `.dockerignore` - Ignore patterns

Deployment steps:
```bash
docker-compose build
docker-compose up
```

### Kubernetes

Generated files:
- `k8s/deployment.yaml` - Deployment manifest
- `k8s/service.yaml` - Service manifest

Deployment steps:
```bash
docker build -t my-app:latest .
kubectl apply -f k8s/
```

## PR Checklist Template

Default checklist items added to every PR:
- [ ] Code follows project conventions
- [ ] Tests pass
- [ ] Documentation updated if needed
- [ ] No breaking changes (or documented)

Custom checklists can be provided:
```python
github.create_pr_with_checklist(
    # ...
    checklist_items=[
        "Review security implications",
        "Test with production data",
        "Update changelog"
    ]
)
```

## Environment Variables

### GitHub Authentication

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

Required permissions:
- `repo` - Full repository access
- `workflow` - Workflow access (if using GitHub Actions)

### Git Configuration

```bash
# Set git author (optional, uses git config by default)
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

## Best Practices

### Commit Messages

1. **Use imperative mood**: "add feature" not "added feature"
2. **Capitalize first letter**: "Add feature" not "add feature"
3. **No period at end**: "Add feature" not "Add feature."
4. **Limit subject to 50 characters**
5. **Wrap body at 72 characters**
6. **Separate subject from body with blank line**

### Branch Management

1. **Create feature branches from main/develop**
2. **Keep branches focused on single feature**
3. **Delete branches after merging**
4. **Use descriptive branch names**

### Pull Requests

1. **Write clear PR titles**
2. **Provide context in description**
3. **Link related issues**
4. **Add appropriate labels**
5. **Request relevant reviewers**
6. **Resolve conflicts before merging**

### Deployment

1. **Test configurations locally**
2. **Review generated files before deploying**
3. **Use environment variables for secrets**
4. **Set appropriate resource limits**
5. **Document deployment process**

## Troubleshooting

### PR Creation Fails

**Issue**: `GitHubError: Could not parse GitHub repository`

**Solution**: Ensure remote URL is a GitHub repository:
```bash
git remote get-url origin
# Should be: git@github.com:owner/repo.git
```

### Commit Validation Fails

**Issue**: `Commit message does not follow conventional format`

**Solution**: Use conventional commit format:
```bash
# Correct
git commit -m "feat: add new feature"

# Incorrect
git commit -m "added some stuff"
```

### Deployment Config Generation Fails

**Issue**: `DeploymentError: Project path does not exist`

**Solution**: Ensure project exists in `.forge/output`:
```bash
ls .forge/output/my-project
```

### GitHub Token Errors

**Issue**: `GitHubError: GitHub token required`

**Solution**: Set GITHUB_TOKEN environment variable:
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

## Testing

Run Git workflow tests:
```bash
poetry run pytest tests/test_git_workflows.py -v
```

Test coverage:
- **git/commits.py**: 82%
- **git/repository.py**: 23% (requires git repo)
- **integrations/github_client.py**: 53%
- **layers/deployment.py**: 91%

## Examples

### Complete Workflow Example

```python
from forge.git.repository import ForgeRepository
from forge.git.commits import CommitStrategy, CommitType, ConventionalCommit
from forge.integrations.github_client import GitHubClient
from forge.layers.deployment import DeploymentGenerator, DeploymentConfig, Platform
from pathlib import Path

# 1. Initialize repository
repo = ForgeRepository(".")

# 2. Create feature branch
branch = repo.create_feature_branch("add-authentication")

# 3. Make changes (your code here)
# ...

# 4. Create commit
commit = ConventionalCommit(
    type=CommitType.FEAT,
    description="add user authentication",
    scope="auth",
    body="Implemented JWT-based authentication with refresh tokens",
    issues=["123"]
)

# 5. Add and commit files
repo.add_files(["auth/login.py", "auth/register.py", "auth/tokens.py"])
repo.commit(commit.format())

# 6. Generate deployment config
generator = DeploymentGenerator(Path("."))
config = DeploymentConfig(
    platform=Platform.FLYIO,
    project_name="my-api",
    runtime="python",
    entry_point="app.py",
    environment_vars={"PORT": "8080"},
    port=8080
)
generator.generate_configs(config)

# 7. Commit deployment config
repo.add_files(["fly.toml", "Dockerfile"])
deploy_commit = ConventionalCommit(
    type=CommitType.BUILD,
    description="add fly.io deployment config",
    scope="deploy"
)
repo.commit(deploy_commit.format())

# 8. Push branch
repo.push(set_upstream=True)

# 9. Create PR
github = GitHubClient("owner/repo")
pr = github.create_pr_with_checklist(
    title="feat: add user authentication",
    description="Adds JWT-based authentication with refresh tokens",
    head=branch,
    base="main",
    checklist_items=[
        "Review authentication logic",
        "Test login/logout flows",
        "Verify token refresh mechanism",
        "Review deployment configuration"
    ],
    issues=["123"],
    labels=["feature", "auth"],
    reviewers=["alice", "bob"]
)

print(f"Created PR: {pr.html_url}")
```

## Related Documentation

- [Implementation Guide](../knowledgeforge-patterns/00_KB3_ImplementationGuide_3.2_GitIntegration.md)
- [Failure Analysis System](./FAILURE_ANALYSIS_SYSTEM.md)
- [CLI Reference](./CLI_REFERENCE.md)
