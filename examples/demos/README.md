# Forge Demo Projects

This directory contains three demonstration projects that showcase Forge's capabilities at different complexity levels.

## Quick Start

Each demo includes a YAML specification file that defines the project structure, tasks, and tech stack. Forge reads these specs and generates complete, production-ready applications.

### Running a Demo

```bash
# 1. Ensure repositories are set up in CodeGen
poetry run python scripts/list_repos.py | grep forge-demo

# 2. Run a demo build (example: todo app)
poetry run forge build --project-id demo-todo-app

# 3. Monitor progress
# Forge will show real-time task completion and file generation
```

## Available Demos

### 1. Todo App ⭐ (Recommended for First Demo)

**Complexity**: Simple
**Duration**: 20-30 minutes
**Tasks**: 4 parallel tasks
**Spec**: `todo-app-spec.yaml`

A complete full-stack todo application demonstrating:
- FastAPI backend with SQLAlchemy ORM
- React frontend with TypeScript
- Comprehensive test suite (pytest + Jest)
- Docker deployment configuration

**Best for**: First-time demonstrations, basic Forge capabilities

```bash
poetry run forge build --project-id demo-todo --spec examples/demos/todo-app-spec.yaml
```

### 2. Weather Dashboard ⛅

**Complexity**: Medium
**Duration**: 25-35 minutes
**Tasks**: 5 parallel tasks
**Spec**: `weather-dashboard-spec.yaml`

A weather dashboard with external API integration:
- OpenWeatherMap API client with error handling
- Redis caching layer
- Chart.js data visualizations
- FastAPI backend
- Responsive HTML/CSS frontend

**Best for**: Showing external integrations, caching strategies, data visualization

```bash
poetry run forge build --project-id demo-weather --spec examples/demos/weather-dashboard-spec.yaml
```

### 3. Blog Platform 📝

**Complexity**: Complex
**Duration**: 30-40 minutes
**Tasks**: 6 parallel tasks
**Spec**: `blog-platform-spec.yaml`

An enterprise-level blog platform featuring:
- JWT authentication system
- Blog posts with CRUD operations
- Nested comments system
- Role-based admin panel
- PostgreSQL with Alembic migrations
- React frontend with routing

**Best for**: Demonstrating Forge's full capabilities, complex applications

```bash
poetry run forge build --project-id demo-blog --spec examples/demos/blog-platform-spec.yaml
```

## Demo Presentation Flow

### 1. Introduction (2 minutes)
- Show the YAML specification file
- Explain how simple declarations become full applications
- Highlight the task breakdown and parallel execution

### 2. Run the Build (Variable)
- Execute `forge build` command
- Show real-time progress in terminal
- Explain the 6-layer orchestration process:
  1. Planning - Understanding requirements
  2. Decomposition - Breaking into tasks
  3. Generation - Parallel code creation
  4. Testing - Automated test suite
  5. Review - Multi-agent validation
  6. Deployment - Configuration generation

### 3. Review Generated Code (5-10 minutes)
- Open the generated GitHub PR
- Walk through project structure
- Show example files (backend, frontend, tests)
- Highlight code quality and documentation

### 4. Discuss Architecture (5 minutes)
- Explain how Forge organized the application
- Show separation of concerns
- Discuss best practices applied
- Answer questions

## What Gets Generated

Each demo generates a complete, production-ready application including:

- ✅ **Backend API** - RESTful endpoints with proper validation
- ✅ **Frontend UI** - Modern component-based architecture
- ✅ **Database Models** - ORM schemas with relationships
- ✅ **API Integration** - External service clients (weather demo)
- ✅ **Authentication** - JWT auth system (blog demo)
- ✅ **Testing** - Unit and integration tests
- ✅ **Docker Config** - Multi-container deployment
- ✅ **Documentation** - README with setup instructions
- ✅ **Type Safety** - TypeScript frontend, type hints in Python
- ✅ **Error Handling** - Comprehensive error management
- ✅ **Code Quality** - Following best practices

## Customizing Demos

You can modify the YAML specs to:
- Add more tasks
- Change tech stack
- Adjust complexity
- Add new features
- Modify requirements

Example modification:
```yaml
# Add a new task to todo-app-spec.yaml
- title: Email Notifications
  description: |
    Send email notifications when tasks are due:
    - SMTP configuration
    - Email templates
    - Task reminder scheduler
  files:
    - backend/services/email_service.py
    - backend/tasks/reminder.py
    - backend/templates/task_due.html
```

## Troubleshooting

### Repository Not Set Up
```bash
# Check setup status
poetry run python scripts/list_repos.py | grep forge-demo

# If NOT_SETUP, configure manually
poetry run python scripts/setup_repository.py forge-demo-todo-app
```

### Build Fails
```bash
# Check logs in detail
poetry run forge build --project-id demo-todo --verbose

# Verify CodeGen configuration
echo $CODEGEN_API_KEY
echo $CODEGEN_ORG_ID
echo $CODEGEN_REPO_ID
```

### Agent Timeout
If generation times out, the repositories might be too large or CodeGen might be experiencing issues. Check:
1. CodeGen status page
2. Agent run logs in CodeGen UI
3. Repository size and complexity

## Demo Tips

### For Best Results:
1. ✅ **Start with Todo App** - Simplest, quickest, most reliable
2. ✅ **Have a Backup** - Pre-run a demo beforehand and show the PR
3. ✅ **Explain While It Runs** - Use build time to discuss architecture
4. ✅ **Show the Spec First** - Let audience see the input before output
5. ✅ **Monitor in UI** - Keep CodeGen web UI open to show agent progress

### Common Questions to Prepare For:
- "How does it handle edge cases?" → Show error handling in generated code
- "Can it integrate with existing code?" → Explain incremental generation
- "What about security?" → Point out input validation, SQL injection prevention
- "Does it write tests?" → Show comprehensive test suite
- "How do I customize it?" → Explain YAML spec modifications

## Repository Links

- **Todo App**: https://github.com/internexio/forge-demo-todo-app
- **Weather Dashboard**: https://github.com/internexio/forge-demo-weather-dashboard
- **Blog Platform**: https://github.com/internexio/forge-demo-blog-platform

## Status Tracking

For current setup status and detailed information, see `DEMO_SETUP_STATUS.md`.

## Additional Resources

- **Forge Documentation**: `../../docs/`
- **Setup Guide**: `../../docs/REPOSITORY_SETUP_SOLUTION.md`
- **CodeGen API**: https://docs.codegen.com/
- **GitHub Integration**: https://github.com/apps/codegen-sh
