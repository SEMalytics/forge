# Using CodeGen API with Forge

Forge supports CodeGen's agent-based code generation API as a backend for building projects.

## Quick Start

### 1. Get CodeGen Credentials

Sign up at [codegen.com](https://codegen.com) and get:
- **API Token**: From your account settings
- **Organization ID**: From your organization dashboard

### 2. Set Environment Variables

```bash
export CODEGEN_API_KEY="your-api-key-here"
export CODEGEN_ORG_ID="your-org-id-here"
```

Or add to your `.env` file:
```bash
CODEGEN_API_KEY=your-api-key-here
CODEGEN_ORG_ID=your-org-id-here
```

### 3. Configure Forge

Create or update `forge.yaml`:

```yaml
generator:
  backend: codegen_api
  api_key: ${CODEGEN_API_KEY}
  org_id: ${CODEGEN_ORG_ID}
  timeout: 600  # 10 minutes
```

Or use the global config at `~/.forge/config.yaml`:

```yaml
generator:
  backend: codegen_api
  api_key: ${CODEGEN_API_KEY}
  org_id: ${CODEGEN_ORG_ID}
```

### 4. Build Your Project

```bash
# Plan your project
forge chat

# Build with CodeGen
forge build --project your-project-id
```

Forge will automatically:
1. Create CodeGen agent runs for each task
2. Poll for completion
3. Extract generated files
4. Write them to your project directory

## How It Works

### Agent-Based Generation

CodeGen uses autonomous agents that:
- Understand project context
- Write production-ready code
- Follow best practices
- Generate tests automatically
- Handle dependencies correctly

### Parallel Execution

Forge leverages CodeGen's parallel execution:
- Independent tasks run simultaneously
- Up to 10 concurrent agent runs (respecting rate limits)
- Faster overall project generation

### Integration with KnowledgeForge

Forge enriches CodeGen prompts with:
- Relevant patterns from the pattern library
- Project context and tech stack
- Dependency information
- File structure expectations

This ensures CodeGen generates code that follows best practices and integrates seamlessly.

## Example Session

```bash
# Initialize project
forge init my-api

# Start planning conversation
forge chat

> What would you like to build?
A REST API for task management with authentication

> What tech stack?
FastAPI, PostgreSQL, SQLAlchemy, JWT

> Any specific requirements?
- CRUD operations for tasks
- User authentication
- Task filtering by status
- Due date reminders

# (conversation continues...)

done

# Build with CodeGen
forge build --project my-api-20251207

# Output:
# ⚒ Forge Build System
#
# Project: Task Management API
# Stage: planning
#
# Found 12 tasks to build
# Backend: codegen_api
#
# Creating CodeGen agent runs...
# [1/12] Generating database models... ✓
# [2/12] Generating API endpoints... ✓
# ...
# [12/12] Generating tests... ✓
#
# ✓ Build completed in 8m 42s
# ✓ Generated 28 files
```

## Advanced Configuration

### Custom API Endpoint

If you're using a self-hosted CodeGen instance:

```yaml
generator:
  backend: codegen_api
  api_key: ${CODEGEN_API_KEY}
  org_id: ${CODEGEN_ORG_ID}
  base_url: https://your-codegen-instance.com/v1
```

### Timeout Settings

Adjust timeout for complex tasks:

```yaml
generator:
  backend: codegen_api
  api_key: ${CODEGEN_API_KEY}
  org_id: ${CODEGEN_ORG_ID}
  timeout: 900  # 15 minutes for complex tasks
```

### Repository Context

If your project is already in a CodeGen-connected repository:

```yaml
generator:
  backend: codegen_api
  api_key: ${CODEGEN_API_KEY}
  org_id: ${CODEGEN_ORG_ID}
  repository_id: "your-repo-id"  # Optional: provides additional context
```

## Rate Limits

CodeGen API has rate limits:
- **Agent creation**: 10 requests per minute
- **Status checks**: 60 requests per 30 seconds

Forge automatically:
- Respects rate limits
- Implements exponential backoff
- Retries failed requests

## Troubleshooting

### "API key is required"

Make sure `CODEGEN_API_KEY` is set:

```bash
echo $CODEGEN_API_KEY
# Should output your API key

# If not set:
export CODEGEN_API_KEY="your-key"
```

### "Organization ID required"

Set `CODEGEN_ORG_ID`:

```bash
export CODEGEN_ORG_ID="your-org-id"
```

### "Rate limit exceeded"

Forge will automatically retry with exponential backoff. If you consistently hit limits:

1. Reduce `max_parallel` in config
2. Increase timeouts
3. Contact CodeGen support for higher limits

### Agent runs fail

Check the CodeGen dashboard at [codegen.com](https://codegen.com) to:
- View agent run details
- See error messages
- Review generated code
- Resume failed runs

### No files generated

CodeGen's response format may vary. If Forge isn't extracting files correctly:

1. Check `.forge/logs/` for detailed output
2. Manually review the CodeGen agent run
3. Report the issue on [GitHub](https://github.com/SEMalytics/forge/issues)

## Comparison with Claude Code

| Feature | CodeGen API | Claude Code |
|---------|-------------|-------------|
| **Execution** | Cloud-based agents | Local CLI tool |
| **Parallel tasks** | Yes (10/min) | Yes (limited by machine) |
| **Cost** | Pay per agent run | API costs only |
| **Setup** | API key only | CLI installation |
| **Web dashboard** | Yes | No |
| **Offline** | No | Yes (with local model) |

## Best Practices

1. **Start small**: Test with 2-3 tasks before full project
2. **Review output**: Check CodeGen dashboard for quality
3. **Iterate**: Use `forge iterate` to refine generated code
4. **Save sessions**: CodeGen keeps history in dashboard
5. **Monitor costs**: Track agent runs to manage expenses

## Next Steps

- [Build your first project](../README.md#usage)
- [Working with existing codebases](./existing-projects.md)
- [Testing and iteration](../ARCHITECTURE.md#layer-4-testing)
- [Deployment options](../API_REFERENCE.md#forge-deploy)

---

**Questions?** Open an issue on [GitHub](https://github.com/SEMalytics/forge/issues)
