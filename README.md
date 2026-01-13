# Forge - AI Development Orchestration

Transform natural language descriptions into production-ready code with intelligent task decomposition, distributed generation, and automated testing.

## Quick Start

```bash
# Install
git clone https://github.com/SEMalytics/forge.git
cd forge
poetry install
pip install -e .

# Verify
forge --version
forge doctor

# Build a project
forge init my-project
forge chat
forge build --project my-project
forge iterate --project my-project
```

See [Installation Guide](./docs/guides/installation.md) for detailed setup.

## Features

- **12-Agent Review System** — Security, performance, architecture experts vote on code (8/12 approval threshold)
- **Automated Iteration** — Detects issues, generates fixes, loops until tests pass
- **Multi-Framework Testing** — pytest, jest, go test with Docker isolation
- **Pattern-Based Generation** — 40+ engineering patterns via KnowledgeForge
- **Git Integration** — Conventional commits, branch management, PR creation
- **Multi-Platform Deploy** — fly.io, Vercel, AWS, Docker, Kubernetes

## Demo

Try Forge with intentionally vulnerable code:

```bash
git clone https://github.com/SEMalytics/forge-demo.git
cd forge-demo

forge review panel                    # Show 12 expert agents
forge review directory demos          # Detect vulnerabilities
forge init "Demo" -i demo -d "Demo"
forge iterate -p demo -d demos        # Auto-fix loop
```

See [forge-demo](https://github.com/SEMalytics/forge-demo) for full documentation.

## KnowledgeForge as Claude Project

The `knowledgeforge/` directory can be deployed as a standalone **Claude Project**:

1. Go to [claude.ai](https://claude.ai) → Create Project
2. Paste `00_Project_Instructions.md` into **Project Instructions**
3. Upload remaining `.md` files to **Project Knowledge**
4. Start chatting with PDIA method, 4 agent modes, and coordination patterns

See [knowledgeforge/README.md](./knowledgeforge/README.md) or browse on [GitHub](https://github.com/SEMalytics/forge/tree/main/knowledgeforge).

## Documentation

**Getting Started:**
- [Installation](./docs/guides/installation.md) — Setup and requirements
- [Quick Start](./docs/guides/quickstart.md) — Get running in 5 minutes
- [CLI Reference](./docs/guides/cli-reference.md) — All commands
- [Configuration](./docs/guides/configuration.md) — Config options

**Guides:**
- [Existing Projects](./docs/guides/existing-projects.md) — Add Forge to existing codebases
- [Using CodeGen](./docs/guides/using-codegen.md) — CodeGen API integration
- [Troubleshooting](./docs/guides/troubleshooting.md) — Common issues

**Architecture & API:**
- [Architecture](./docs/ARCHITECTURE.md) — System design (6-layer pipeline)
- [API Reference](./docs/API_REFERENCE.md) — Python API
- [Failure Analysis](./docs/FAILURE_ANALYSIS_SYSTEM.md) — How auto-fix works
- [Git Workflows](./docs/GIT_WORKFLOWS.md) — Git integration

**Development:**
- [Developer Guide](./docs/guides/developer-guide.md) — Contributing
- [Development Notes](./docs/DEVELOPMENT_NOTES.md) — Internal docs

See [docs/README.md](./docs/README.md) for complete index.

## CLI Commands

```bash
# Core workflow
forge init <project>           # Initialize project
forge chat                     # Interactive planning
forge build -p <id>            # Generate code
forge test -p <id>             # Run tests
forge iterate -p <id>          # Auto-fix loop

# Review
forge review panel             # Show 12 agents
forge review file <path>       # Review single file
forge review directory <dir>   # Review directory

# Utilities
forge status                   # Project status
forge doctor                   # Check dependencies
forge deploy -p <id>           # Generate deploy config
```

## Requirements

- Python 3.11 or 3.12 (not 3.13+)
- Docker (optional, for isolated testing)
- `ANTHROPIC_API_KEY` environment variable

## License

MIT — See [LICENSE](./LICENSE)

## Links

- [Documentation](./docs/)
- [Demo Repository](https://github.com/SEMalytics/forge-demo)
- [KnowledgeForge Specs](./knowledgeforge/)
- [GitHub Issues](https://github.com/SEMalytics/forge/issues)

---

Built with [Claude](https://anthropic.com) by [SEMalytics](https://github.com/SEMalytics)

---

## About SEMalytics

Forge is built by [SEMalytics](https://semalytics.com)—applying cognitive science and AI orchestration to real development problems.

**Related Projects:**
- **[KnowledgeForge](knowledgeforge/)** — The multi-agent methodology powering Forge's 12-agent review system
- **[Concept Clarity](https://github.com/SEMalytics/concept-clarity)** — Measure message clarity across communications
- **Communications Optimization System (COS)** — Personality-aware B2B content analysis

[Learn more at SEMalytics →](https://semalytics.com)

---

<p align="center">
  <sub>Built by <a href="https://semalytics.com">SEMalytics</a> · AI that ships.</sub>
</p>
