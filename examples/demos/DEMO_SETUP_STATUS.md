# Forge Demo Repositories - Setup Status

## Overview

Created 3 demo repositories to showcase Forge's capabilities with different complexity levels and tech stacks.

## Demo Repositories

### 1. Todo App (Simple - 4 Tasks)
- **GitHub**: https://github.com/internexio/forge-demo-todo-app
- **CodeGen ID**: 184804
- **CodeGen Setup**: https://codegen.com/repos/184804/setup-commands
- **Agent Trace**: https://codegen.com/agent/trace/146257
- **Spec File**: `examples/demos/todo-app-spec.yaml`
- **Tech Stack**: FastAPI, React, TypeScript, SQLite, Docker
- **Estimated Duration**: 20-30 minutes
- **Tasks**: Backend API, Frontend React App, Testing Suite, Docker & Deployment

**Demo Talking Points**:
- Four distinct tasks that can be generated in parallel
- Full-stack application with backend + frontend + testing + deployment
- Demonstrates realistic project structure
- Shows how Forge handles dependencies between components

### 2. Weather Dashboard (Medium - 5 Tasks)
- **GitHub**: https://github.com/internexio/forge-demo-weather-dashboard
- **CodeGen ID**: 184805
- **CodeGen Setup**: https://codegen.com/repos/184805/setup-commands
- **Agent Trace**: https://codegen.com/agent/trace/146258
- **Spec File**: `examples/demos/weather-dashboard-spec.yaml`
- **Tech Stack**: FastAPI, Redis, Chart.js, HTML/CSS, Docker
- **Estimated Duration**: 25-35 minutes
- **Tasks**: API Integration Layer, Caching & Data Processing, Web Interface & Visualization, Backend API Server, Deployment Configuration

**Demo Talking Points**:
- Five parallel tasks showing complex dependency management
- External API integration with real-world error handling (OpenWeatherMap)
- Caching layer demonstrates performance optimization
- Data visualization shows frontend capabilities
- Realistic production-ready architecture

### 3. Blog Platform (Complex - 6 Tasks)
- **GitHub**: https://github.com/internexio/forge-demo-blog-platform
- **CodeGen ID**: 184806
- **CodeGen Setup**: https://codegen.com/repos/184806/setup-commands
- **Agent Trace**: https://codegen.com/agent/trace/146259
- **Spec File**: `examples/demos/blog-platform-spec.yaml`
- **Tech Stack**: FastAPI, PostgreSQL, SQLAlchemy, JWT, React, TypeScript
- **Estimated Duration**: 30-40 minutes
- **Tasks**: Authentication System, Blog Post Management, Comment System, Admin Panel Backend, Frontend React Application, Database & Configuration

**Demo Talking Points**:
- Six parallel tasks demonstrating enterprise-scale project
- Complete authentication and authorization system with JWT
- Complex data relationships (users → posts → comments)
- Admin panel shows role-based features
- Production-ready with Alembic migrations and Docker
- Perfect example of full-stack application generation

## Setup Status (2025-12-08)

### Setup Command Generation In Progress

All three repositories have setup command generation agents running:
- **Agent 146257** (todo-app) - Status: ACTIVE
- **Agent 146258** (weather-dashboard) - Status: ACTIVE
- **Agent 146259** (blog-platform) - Status: ACTIVE

**Started**: ~16:19 UTC
**Current Status**: Agents still running (4+ minutes)

### Note on API Status Caching

Per `docs/REPOSITORY_SETUP_SOLUTION.md`, the CodeGen API may show `setup_status: "NOT_SETUP"` for several hours after setup completion due to caching. The most reliable way to verify setup is via the CodeGen UI links above.

## Recommended Setup Commands

If manual configuration is needed, here are recommended setup commands for these Python projects:

```bash
# Check Python version
python --version

# Create virtual environment
python -m venv venv

# Activate and install dependencies (when requirements.txt exists)
source venv/bin/activate && pip install -r requirements.txt || echo "No requirements.txt yet"

# Install common development tools
pip install pytest black isort mypy ruff
```

For projects with `pyproject.toml` (Poetry):
```bash
# Check Python version
python --version

# Install Poetry if needed
pip install poetry

# Install project dependencies
poetry install
```

## Using These Demos

### Running a Demo Build

Once setup is complete, you can run a demo build using:

```bash
# Example: Build the todo app demo
poetry run forge build \
  --project-id demo-todo-app \
  --spec examples/demos/todo-app-spec.yaml \
  --parallel

# Example: Build the weather dashboard demo
poetry run forge build \
  --project-id demo-weather \
  --spec examples/demos/weather-dashboard-spec.yaml \
  --parallel

# Example: Build the blog platform demo
poetry run forge build \
  --project-id demo-blog \
  --spec examples/demos/blog-platform-spec.yaml \
  --parallel
```

### Demo Workflow

1. **Show the spec file** - Explain how simple YAML defines complex projects
2. **Run forge build** - Watch parallel task generation
3. **Monitor progress** - Show real-time task completion
4. **Review generated code** - Walk through created files
5. **Show the PR** - GitHub integration with comprehensive diffs
6. **Discuss architecture** - How Forge organized the code

## Progressive Complexity

These demos are designed to showcase Forge's capabilities at different scales:

1. **Todo App** (Simple)
   - Good for first-time demonstrations
   - Shows basic full-stack generation
   - Quick to complete (~20-30 min)
   - Easy to understand architecture

2. **Weather Dashboard** (Medium)
   - Demonstrates external integrations
   - Shows caching and optimization
   - Good for technical audiences
   - Realistic production patterns

3. **Blog Platform** (Complex)
   - Enterprise-level complexity
   - Authentication and authorization
   - Complex data relationships
   - Best for showcasing Forge's full power

## Next Steps

1. ✅ **GitHub Repositories Created**
2. ✅ **CodeGen GitHub App Access Granted**
3. ✅ **Demo Specifications Written**
4. ⏳ **Setup Command Generation In Progress**
5. ⏳ **Verify Setup Completion** (check CodeGen UI)
6. ⏳ **Test Build One Demo** (todo-app recommended for first test)
7. ⏳ **Document Results** (screenshots, timing, issues)

## Troubleshooting

### If Setup Agents Don't Complete

You can manually configure setup commands via CodeGen UI:
1. Visit the setup URL for each repo (links above)
2. Configure the recommended setup commands
3. Save configuration
4. Proceed with demo builds

### If Build Fails

1. Check repository setup status in CodeGen UI
2. Verify GitHub App has access to repositories
3. Check `CODEGEN_REPO_ID` in `.env` matches target repo
4. Review agent run logs for errors

## Resources

- **Forge Documentation**: `docs/`
- **CodeGen API Docs**: https://docs.codegen.com/api-reference
- **GitHub App**: https://github.com/apps/codegen-sh
- **Repository Setup Guide**: `docs/REPOSITORY_SETUP_SOLUTION.md`
