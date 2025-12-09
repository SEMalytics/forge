# Forge Quick Demos (Under 5 Minutes) ⚡

Ultra-fast demos perfect for testing Forge, quick presentations, or when you need immediate results.

---

## Overview

These three demos are designed to complete in **3-5 minutes each**. Each is a single-task project that generates production-ready code quickly.

### When to Use Quick Demos

- ✅ **Testing Forge setup** - Verify everything works before longer demos
- ✅ **Time-constrained presentations** - When you have <10 minutes
- ✅ **First-time Forge users** - Build confidence with quick wins
- ✅ **Development verification** - Test after Forge updates
- ✅ **Live coding demos** - Show results in real-time

---

## Quick Demo 1: Hello World API ⚡

### What It Generates
A minimal FastAPI application with health check and hello world endpoints.

### Run Command
```bash
export CODEGEN_REPO_ID=184842 && poetry run forge build --project-id quick-hello-api --spec examples/demos/hello-api-spec.yaml
```

### Generated Files
- `main.py` - FastAPI application with 2 endpoints
- `requirements.txt` - Dependencies (fastapi, uvicorn)
- `README.md` - Run instructions
- `.gitignore` - Python gitignore

### Key Features
- GET `/hello` - Returns {"message": "Hello, World!"}
- GET `/health` - Health check endpoint
- CORS middleware configured
- Uvicorn server configuration
- Ready to run with `uvicorn main:app`

### Demo Script
```
"Let me show you how fast Forge works. I'm going to generate a complete
API in the next 3-4 minutes. Watch the terminal..."

[Run command]

"Forge is creating a FastAPI application with proper structure, middleware,
and documentation. This isn't just a skeleton - it's production-ready code."

[After completion]

"Done! We now have a working API with health checks, CORS configured, and
comprehensive documentation. Let's look at what was generated..."
```

### Stats
- **Tasks**: 1
- **Files**: ~5
- **Lines of Code**: ~100
- **Duration**: 3-5 minutes
- **Best For**: Backend demos, API generation showcase

---

## Quick Demo 2: Landing Page ⚡

### What It Generates
A modern, responsive static landing page with pure HTML/CSS/JavaScript.

### Run Command
```bash
export CODEGEN_REPO_ID=184843 && poetry run forge build --project-id quick-landing-page --spec examples/demos/landing-page-spec.yaml
```

### Generated Files
- `index.html` - Semantic HTML5 structure
- `css/styles.css` - Modern responsive CSS
- `js/script.js` - Vanilla JavaScript
- `README.md` - Instructions
- `.gitignore` - Standard gitignore

### Key Features
- Hero section with CTA button
- Features section with 3 cards
- Contact form (frontend)
- Responsive navigation
- Footer with social links
- Mobile-responsive (flexbox/grid)
- Smooth scroll behavior
- Modern gradient backgrounds

### Demo Script
```
"Forge isn't just for complex applications. Watch me generate a beautiful
landing page in under 5 minutes - pure HTML, CSS, and JavaScript."

[Run command]

"No frameworks, no build tools - just clean, modern web development.
Forge understands what makes a good landing page: responsive design,
proper semantics, and smooth interactions."

[After completion - open in browser]

"Look at this! Fully responsive, professional design, and we can open it
right in the browser. Try resizing - see how it adapts to mobile."
```

### Stats
- **Tasks**: 1
- **Files**: ~5
- **Lines of Code**: ~200
- **Duration**: 3-5 minutes
- **Best For**: Frontend demos, visual presentations, immediate results

---

## Quick Demo 3: CLI Calculator Tool ⚡

### What It Generates
A professional command-line calculator with Click framework.

### Run Command
```bash
export CODEGEN_REPO_ID=184844 && poetry run forge build --project-id quick-cli-tool --spec examples/demos/cli-tool-spec.yaml
```

### Generated Files
- `calculator/cli.py` - Click-based CLI
- `calculator/__init__.py` - Package init
- `setup.py` - Installation config
- `requirements.txt` - Dependencies (click, pytest)
- `tests/test_cli.py` - Test suite
- `README.md` - Usage guide
- `.gitignore` - Python gitignore

### Key Features
- Subcommands: add, subtract, multiply, divide
- Colorized output with click.style()
- Error handling (division by zero)
- Input validation
- --verbose flag
- Comprehensive help text
- Installable as CLI tool
- Test suite included

### Demo Script
```
"Developer tools are just as important as web apps. Let me generate a
professional CLI calculator with Click in about 4 minutes."

[Run command]

"Forge is creating a command-line tool with proper argument parsing,
help text, colored output, and even tests."

[After completion - run commands]

"Let's try it out:
  python calculator/cli.py add 5 3
  python calculator/cli.py divide 10 2 --verbose

See the colored output? The help text? This is a professional CLI tool."
```

### Stats
- **Tasks**: 1
- **Files**: ~8
- **Lines of Code**: ~250
- **Duration**: 3-5 minutes
- **Best For**: Developer tool demos, CLI generation showcase

---

## Comparison: Quick vs Full Demos

| Aspect | Quick Demos (⚡) | Full Demos (📚) |
|--------|------------------|-----------------|
| **Duration** | 3-5 minutes | 20-40 minutes |
| **Tasks** | 1 task | 4-6 tasks |
| **Files** | 5-8 files | 50-120 files |
| **Code Lines** | 100-250 | 1,500-3,500 |
| **Complexity** | Minimal | Enterprise-level |
| **Best For** | Testing, quick shows | Full presentations |
| **Wow Factor** | Speed | Comprehensiveness |

---

## Demo Strategy

### For Technical Audiences
1. **Start with**: CLI Calculator (shows code quality)
2. **Then show**: Hello API (shows backend generation)
3. **Finish with**: Full demo (Todo App or Blog Platform)

### For Non-Technical Audiences
1. **Start with**: Landing Page (immediate visual)
2. **Then show**: Hello API (explain backend concepts)
3. **Finish with**: Full demo if time permits

### For Time-Constrained Presentations (<15 min)
1. **Quick demo**: Landing Page (5 min)
2. **Talk about** full demos using pre-generated examples
3. **Q&A**: Use extra time for questions

---

## Testing Strategy

Before any presentation, test Forge with a quick demo:

```bash
# Run this 1 hour before your presentation
export CODEGEN_REPO_ID=184842
poetry run forge build --project-id test-forge --spec examples/demos/hello-api-spec.yaml
```

**If it succeeds**: Forge is working, proceed with confidence
**If it fails**: Troubleshoot before the presentation, or use pre-generated PRs as backup

---

## Copy-Paste Commands

### Test All Quick Demos
```bash
# Test 1: Hello API
export CODEGEN_REPO_ID=184842 && poetry run forge build --project-id test-hello --spec examples/demos/hello-api-spec.yaml

# Test 2: Landing Page
export CODEGEN_REPO_ID=184843 && poetry run forge build --project-id test-landing --spec examples/demos/landing-page-spec.yaml

# Test 3: CLI Tool
export CODEGEN_REPO_ID=184844 && poetry run forge build --project-id test-cli --spec examples/demos/cli-tool-spec.yaml
```

### Monitor Progress
```bash
# Watch for PR creation
watch -n 2 'gh pr list --repo internexio/forge-demo-hello-api'
watch -n 2 'gh pr list --repo internexio/forge-demo-landing-page'
watch -n 2 'gh pr list --repo internexio/forge-demo-cli-tool'
```

---

## Repository Information

| Demo | GitHub | CodeGen ID | Setup URL |
|------|--------|------------|-----------|
| **Hello API** | [forge-demo-hello-api](https://github.com/internexio/forge-demo-hello-api) | 184842 | [Setup](https://codegen.com/repos/184842/setup-commands) |
| **Landing Page** | [forge-demo-landing-page](https://github.com/internexio/forge-demo-landing-page) | 184843 | [Setup](https://codegen.com/repos/184843/setup-commands) |
| **CLI Tool** | [forge-demo-cli-tool](https://github.com/internexio/forge-demo-cli-tool) | 184844 | [Setup](https://codegen.com/repos/184844/setup-commands) |

---

## Setup Status

All three repositories have setup command generation in progress:
- **Agent 146277** (hello-api) - https://codegen.com/agent/trace/146277
- **Agent 146278** (landing-page) - https://codegen.com/agent/trace/146278
- **Agent 146279** (cli-tool) - https://codegen.com/agent/trace/146279

---

## Tips for Success

### Do's ✅
- Use quick demos to **test Forge before presentations**
- **Open generated files** to show code quality
- **Run the applications** live when possible (especially Landing Page)
- **Explain what's happening** during the 3-5 minute wait
- **Have backup** - pre-run demos and save PR links

### Don'ts ❌
- Don't dismiss quick demos as "too simple" - they showcase speed
- Don't skip showing the generated code - that's the value
- Don't rely only on quick demos for technical audiences
- Don't forget to set CODEGEN_REPO_ID environment variable

---

## Example Presentation (10 minutes total)

```
[0:00-0:30] Introduction
"Forge generates production-ready code from simple YAML specs."

[0:30-1:00] Show the spec file
"Here's the entire specification - just 40 lines describing a landing page."

[1:00-1:30] Run the build
"Watch this..." [Execute command]

[1:30-5:00] Explain while building (3.5 min)
"Forge is analyzing requirements, planning the structure, generating HTML
with semantic markup, CSS with responsive design, JavaScript for interactions,
and documentation. All following modern best practices."

[5:00-8:00] Review generated code (3 min)
[Open PR, show files, open landing page in browser]
"Look at this HTML - semantic elements, accessibility attributes.
The CSS - mobile-first, using modern grid and flexbox.
And it works perfectly across devices."

[8:00-10:00] Q&A (2 min)
Answer questions, mention full demos for complex applications
```

---

## Emergency Backup

If live demo fails, have these ready:

1. **Pre-generated PRs** - Run once beforehand, save links
2. **Screenshots** - Capture spec file, terminal output, generated code, running app
3. **Video recording** - Record one successful run (2-3 minutes)

---

**Remember**: Quick demos are perfect for proving Forge works. Use them strategically to build confidence before showing more complex capabilities! ⚡
