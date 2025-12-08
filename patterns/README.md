# Forge Patterns

This directory contains reusable patterns and best practices for the Forge AI-powered software factory.

## Pattern Categories

### Architecture (`architecture/`)
Core architectural patterns for building software with Forge:
- **6-layer-architecture.md** - The foundational 6-layer architecture
- **task-decomposition.md** - Breaking down complex projects into tasks
- **parallel-generation.md** - Distributed code generation strategies
- **state-management.md** - Managing project state across layers

### Development (`development/`)
Development patterns and best practices:
- **conventional-commits.md** - Commit message format and strategies
- **pr-workflows.md** - Pull request automation patterns
- **code-generation.md** - Effective prompts for code generation
- **tech-stack-selection.md** - Choosing the right technology stack

### Testing (`testing/`)
Testing patterns and strategies:
- **docker-testing.md** - Isolated Docker-based testing
- **test-generation.md** - Auto-generating comprehensive tests
- **security-scanning.md** - Security vulnerability detection
- **performance-testing.md** - Performance benchmarking patterns

### Deployment (`deployment/`)
Deployment patterns for different platforms:
- **multi-platform.md** - Deploying to multiple platforms
- **flyio.md** - Fly.io deployment best practices
- **vercel.md** - Vercel deployment patterns
- **docker.md** - Docker and Docker Compose patterns
- **kubernetes.md** - Kubernetes deployment strategies

### Troubleshooting (`troubleshooting/`)
Common issues and resolution patterns:
- **api-errors.md** - API error handling and retries
- **docker-issues.md** - Docker-related troubleshooting
- **git-conflicts.md** - Resolving merge conflicts
- **test-failures.md** - Debugging test failures

## Using Patterns

### From CLI

Search for patterns:
```bash
forge search "deployment strategies"
forge search "error handling"
```

Get pattern explanations:
```bash
forge explain "conventional commits"
forge explain "docker testing"
```

### From Python API

```python
from forge.knowledgeforge.pattern_store import PatternStore

# Initialize pattern store
store = PatternStore()

# Search for patterns
results = store.search("testing strategies", limit=5)

for match in results:
    print(f"{match.title}: {match.relevance_score:.2f}")
    print(match.content)
```

## Creating New Patterns

Each pattern should follow this structure:

```markdown
# Pattern Title

## Context
When to use this pattern and what problem it solves

## Problem
The specific problem this pattern addresses

## Solution
The pattern implementation details

## Examples
Concrete examples of the pattern in use

## Related Patterns
Links to related patterns

## References
External resources and documentation
```

## Pattern Organization

Patterns are organized by:
1. **Category** - Architecture, Development, Testing, Deployment, Troubleshooting
2. **Difficulty** - Beginner, Intermediate, Advanced
3. **Tags** - Searchable keywords for quick discovery

## Contributing Patterns

To add a new pattern:
1. Choose the appropriate category directory
2. Follow the pattern template structure
3. Add searchable tags and metadata
4. Include concrete examples
5. Link to related patterns
