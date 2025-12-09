# Forge Demo - Copy-Paste Prompts & Commands

Quick reference for running and presenting Forge demos. Each section contains ready-to-use commands and talking points.

---

## Demo 1: Todo App (Simple) ⭐

### Run Command
```bash
poetry run forge build --project-id demo-todo-app --spec examples/demos/todo-app-spec.yaml
```

### Presentation Opening
```
"I'm going to show you how Forge transforms a simple YAML specification
into a complete full-stack application. This todo app will have a FastAPI
backend, React frontend, comprehensive tests, and Docker deployment - all
generated from a 92-line YAML file."
```

### During Build (While Running)
```
"Forge is now breaking this project into 4 parallel tasks:
1. Backend API with SQLite database and CRUD endpoints
2. Frontend React app with TypeScript
3. Comprehensive test suite with pytest and Jest
4. Docker configuration for deployment

Each task is being generated independently, which is why this completes
in 20-30 minutes instead of hours."
```

### After Completion
```
"Let's look at what was generated. You'll see:
- Complete FastAPI backend with SQLAlchemy models
- React components with proper TypeScript typing
- Over 90% test coverage
- Production-ready Docker Compose setup
- All following industry best practices"
```

### Key Stats to Mention
- **4 parallel tasks**
- **~50-60 files generated**
- **1,500+ lines of production code**
- **20-30 minute generation time**
- **Zero manual coding required**

---

## Demo 2: Weather Dashboard (Medium) ⛅

### Run Command
```bash
poetry run forge build --project-id demo-weather-dashboard --spec examples/demos/weather-dashboard-spec.yaml
```

### Presentation Opening
```
"This demo showcases Forge's ability to integrate external APIs and implement
caching strategies. We're building a weather dashboard that connects to
OpenWeatherMap, implements Redis caching, and visualizes data with Chart.js -
all from a 108-line specification."
```

### During Build (While Running)
```
"Forge is creating 5 parallel tasks:
1. OpenWeatherMap API integration with error handling and retry logic
2. Redis caching layer with TTL and invalidation strategies
3. Data visualization frontend with Chart.js
4. FastAPI backend with RESTful endpoints
5. Docker Compose configuration with Redis + Backend + Frontend

Notice how Forge handles complex dependencies - the caching layer integrates
seamlessly with both the API client and the backend server."
```

### After Completion
```
"What makes this impressive is the production-ready patterns:
- Automatic retry logic for API failures
- Intelligent caching to respect rate limits
- Error handling for network issues
- Responsive data visualizations
- Environment-based configuration

This is code you could deploy immediately."
```

### Key Stats to Mention
- **5 parallel tasks**
- **~70-80 files generated**
- **2,000+ lines of code**
- **25-35 minute generation time**
- **External API integration + caching**

---

## Demo 3: Blog Platform (Complex) 📝

### Run Command
```bash
poetry run forge build --project-id demo-blog-platform --spec examples/demos/blog-platform-spec.yaml
```

### Presentation Opening
```
"Now we're going enterprise-level. This blog platform includes JWT authentication,
role-based access control, complex data relationships, and database migrations.
It's the kind of project that would typically take a team weeks to scaffold -
Forge will generate it in 30-40 minutes from a 135-line spec."
```

### During Build (While Running)
```
"Forge is orchestrating 6 complex tasks in parallel:
1. JWT authentication system with password hashing and token validation
2. Blog post management with CRUD, drafts, and categories
3. Nested comments system with moderation
4. Admin panel with role-based permissions
5. React frontend with routing and authentication
6. PostgreSQL database with Alembic migrations

Each task understands its dependencies. For example, the comment system
knows about the user and post models, and the admin panel enforces
role-based access control across all features."
```

### After Completion
```
"This is production-grade code. Look at:
- Secure JWT authentication following best practices
- SQL injection prevention with SQLAlchemy ORM
- Properly structured database migrations
- Role-based access control (RBAC)
- Comprehensive error handling
- Type safety throughout (TypeScript + Python type hints)

This is the kind of architecture senior engineers design."
```

### Key Stats to Mention
- **6 parallel tasks**
- **~100-120 files generated**
- **3,500+ lines of code**
- **30-40 minute generation time**
- **Enterprise-level complexity**

---

## Quick Verification Commands

### Check Repository Setup Status
```bash
poetry run python scripts/list_repos.py | grep forge-demo
```

### Monitor Active Agent Runs
```bash
# Todo App (if running)
poetry run python scripts/check_agent_run.py <AGENT_ID>

# Or check all recent runs
curl -H "Authorization: Bearer $CODEGEN_API_KEY" \
  https://api.codegen.com/v1/organizations/5249/agent/runs | jq '.[:3]'
```

### View Generated PR
The build output will include a PR URL. Alternatively:
```bash
# Replace REPO_NAME with forge-demo-todo-app, etc.
gh pr list --repo internexio/REPO_NAME
```

---

## Troubleshooting Commands

### If Repository Shows NOT_SETUP
```bash
# Manually configure setup commands
poetry run python scripts/setup_repository.py forge-demo-todo-app
poetry run python scripts/setup_repository.py forge-demo-weather-dashboard
poetry run python scripts/setup_repository.py forge-demo-blog-platform
```

### If Build Fails
```bash
# Run with verbose logging
poetry run forge build --project-id demo-todo --spec examples/demos/todo-app-spec.yaml --verbose

# Check agent run details
poetry run python scripts/check_agent_run.py <AGENT_ID>
```

### Verify CodeGen Configuration
```bash
# Check environment variables
echo "API Key: ${CODEGEN_API_KEY:0:10}..."
echo "Org ID: $CODEGEN_ORG_ID"
echo "Repo ID: $CODEGEN_REPO_ID"

# Test API connectivity
curl -H "Authorization: Bearer $CODEGEN_API_KEY" \
  https://api.codegen.com/v1/organizations/5249/repositories | jq '.[0]'
```

---

## Presentation Flow Template

### 1. Introduction (2 min)
```
"Forge is an AI development orchestration system. Instead of writing code
line by line, you describe what you want in a YAML file, and Forge generates
production-ready applications. Let me show you."
```

### 2. Show the Spec (2 min)
```
"Here's the entire specification for [demo name]. Notice how simple it is:
- Project description
- Tech stack list
- Task breakdown with file paths

That's it. No boilerplate, no configuration hell, just intent."
```

### 3. Run the Build (Variable)
```
[Run the command]

"While this generates, let me explain what's happening under the hood:
- Layer 1: Planning - Understanding requirements
- Layer 2: Decomposition - Breaking into optimal tasks
- Layer 3: Generation - Parallel code creation
- Layer 4: Testing - Automated test suite
- Layer 5: Review - Multi-agent validation
- Layer 6: Deployment - Configuration generation

[Point out task completion in real-time]"
```

### 4. Review Generated Code (5 min)
```
"Let's look at what Forge created. [Open PR]

Notice:
- Clean project structure
- Comprehensive documentation
- Industry best practices
- Type safety throughout
- Security considerations
- Production-ready configuration

This isn't template code - it's thoughtfully architected for this specific
use case."
```

### 5. Q&A Topics to Prepare
```
Q: "Can it integrate with existing code?"
A: "Yes, Forge can work incrementally. You can specify existing files to
   extend or generate new modules that integrate with your current codebase."

Q: "What about security?"
A: "Forge implements security best practices by default - SQL injection
   prevention, XSS protection, secure password hashing, input validation,
   and proper authentication flows."

Q: "Does it write tests?"
A: "Every build includes a comprehensive test suite. You'll see unit tests,
   integration tests, and often >80% code coverage."

Q: "Can I customize the generated code?"
A: "Absolutely. The generated code is yours to modify. More importantly,
   you can customize the YAML spec to change the architecture, add features,
   or adjust the tech stack before generation."

Q: "How much does this cost?"
A: "Forge uses the CodeGen API. Pricing depends on your usage tier. For
   reference, these demos cost approximately $X-Y per build."
```

---

## Demo Comparison Matrix

| Feature | Todo App | Weather Dashboard | Blog Platform |
|---------|----------|-------------------|---------------|
| **Complexity** | Simple | Medium | Complex |
| **Duration** | 20-30 min | 25-35 min | 30-40 min |
| **Tasks** | 4 | 5 | 6 |
| **Files** | ~50-60 | ~70-80 | ~100-120 |
| **Code Lines** | ~1,500 | ~2,000 | ~3,500 |
| **Best For** | First demo | Technical audience | Full capabilities |
| **Highlights** | Full-stack basics | External APIs, caching | Auth, RBAC, migrations |
| **Tech Stack** | FastAPI, React, SQLite | FastAPI, Redis, Chart.js | FastAPI, PostgreSQL, JWT |

---

## Quick Copy-Paste for Each Demo

### Todo App - Complete Script
```bash
# Set repository context
export CODEGEN_REPO_ID=184804

# Run build
poetry run forge build --project-id demo-todo-app --spec examples/demos/todo-app-spec.yaml

# Monitor (in separate terminal)
watch -n 5 'gh pr list --repo internexio/forge-demo-todo-app'
```

### Weather Dashboard - Complete Script
```bash
# Set repository context
export CODEGEN_REPO_ID=184805

# Run build
poetry run forge build --project-id demo-weather-dashboard --spec examples/demos/weather-dashboard-spec.yaml

# Monitor (in separate terminal)
watch -n 5 'gh pr list --repo internexio/forge-demo-weather-dashboard'
```

### Blog Platform - Complete Script
```bash
# Set repository context
export CODEGEN_REPO_ID=184806

# Run build
poetry run forge build --project-id demo-blog-platform --spec examples/demos/blog-platform-spec.yaml

# Monitor (in separate terminal)
watch -n 5 'gh pr list --repo internexio/forge-demo-blog-platform'
```

---

## One-Liner for Quick Demo

### Fastest Demo (Todo App)
```bash
export CODEGEN_REPO_ID=184804 && poetry run forge build --project-id demo-todo --spec examples/demos/todo-app-spec.yaml
```

### Most Impressive Demo (Blog Platform)
```bash
export CODEGEN_REPO_ID=184806 && poetry run forge build --project-id demo-blog --spec examples/demos/blog-platform-spec.yaml
```

---

## Pre-Demo Checklist

Run these commands before your presentation:

```bash
# 1. Verify all repos are set up
poetry run python scripts/list_repos.py | grep forge-demo

# 2. Check API connectivity
curl -s -H "Authorization: Bearer $CODEGEN_API_KEY" \
  https://api.codegen.com/v1/organizations/5249/repositories | jq 'length'

# 3. Verify GitHub App access
gh repo list internexio | grep forge-demo

# 4. Test a quick build (optional but recommended)
export CODEGEN_REPO_ID=184804
poetry run forge build --project-id test-run --spec examples/demos/todo-app-spec.yaml

# 5. Have CodeGen UI open in browser
open https://codegen.com/repos
```

---

## Post-Demo Follow-Up

### Share These Resources
- **Demo Repos**: https://github.com/internexio?q=forge-demo
- **Forge Documentation**: [Your docs URL]
- **CodeGen Platform**: https://codegen.com
- **Contact**: [Your contact info]

### Example Email Template
```
Subject: Forge Demo - Full-Stack Code Generation

Hi [Name],

Thanks for attending the Forge demonstration! Here are the resources we discussed:

Demo Repositories:
- Todo App: https://github.com/internexio/forge-demo-todo-app
- Weather Dashboard: https://github.com/internexio/forge-demo-weather-dashboard
- Blog Platform: https://github.com/internexio/forge-demo-blog-platform

Each repository contains the generated code and a PR showing all changes.

To try Forge yourself:
1. Clone the repo: git clone https://github.com/SEMalytics/forge.git
2. Install: poetry install
3. Configure: Set CODEGEN_API_KEY in .env
4. Run: poetry run forge build --help

Feel free to reach out with any questions!

Best regards,
[Your name]
```

---

## Emergency Backup Plan

If live demo fails, have these ready:

### Pre-Generated PR Links
```
After running demos once, save these:
- Todo App PR: https://github.com/internexio/forge-demo-todo-app/pull/X
- Weather Dashboard PR: https://github.com/internexio/forge-demo-weather-dashboard/pull/X
- Blog Platform PR: https://github.com/internexio/forge-demo-blog-platform/pull/X
```

### Screen Recording
```
Record a successful build once:
1. Terminal showing the build command and progress
2. Browser showing the generated PR
3. Code walkthrough of generated files

Duration: 5-7 minutes per demo
Tool: OBS Studio or QuickTime
```

### Static Screenshots
```
Capture:
1. YAML spec file
2. Build progress in terminal
3. Generated PR overview
4. Example generated files
5. Test coverage report
```

---

**Pro Tip**: Always run a test build 24 hours before your presentation to ensure everything works. Save the PR link as backup!
