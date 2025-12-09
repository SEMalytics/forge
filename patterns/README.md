# Forge Patterns Library

This directory contains curated operational patterns for use with the Forge code generation system. These patterns provide reference implementations for data handling, orchestration, testing, and security.

## Directory Structure

```
patterns/
├── core/                    # Core system patterns
│   ├── architecture.md      # Five-layer architecture design
│   └── data-transfer.md     # Unlimited data handling with compression/chunking
│
├── agents/                  # Agent coordination patterns
│   └── catalog.md           # Agent registry and capability matrix
│
├── architecture/            # Forge-specific architecture
│   └── 6-layer-architecture.md  # Forge's 6-layer orchestration model
│
├── workflows/               # Workflow orchestration patterns
│   └── orchestration.md     # Master orchestrator, routing, coordination
│
├── testing/                 # Testing patterns
│   └── scenarios.md         # Unit, integration, system, acceptance tests
│
├── operations/              # Operational patterns
│   ├── security.md          # Authentication, authorization, data protection
│   ├── implementation.md    # Deployment and configuration guide
│   └── git-integration.md   # Automated artifact capture and versioning
│
├── deployment/              # Deployment patterns
│   └── multi-platform.md    # Multi-platform deployment configurations
│
└── development/             # Development patterns
    └── conventional-commits.md  # Commit message standards
```

## Pattern Categories

### Core Patterns (from KnowledgeForge 3.2)
- **architecture.md**: Five-layer system architecture (Knowledge → Intelligence → Data Transfer → Orchestration → Git)
- **data-transfer.md**: Compression algorithms (pako, lz-string, native), chunking system, streaming, performance optimization

### Agent Patterns
- **catalog.md**: Agent registry, capability matrix, coordination patterns (sequential, parallel, hierarchical, pipeline)

### Workflow Patterns
- **orchestration.md**: Master orchestrator pattern, intelligent routing, resource management, circuit breaker, performance tracking

### Testing Patterns
- **scenarios.md**: Comprehensive test scenarios covering system health, agent communication, data transfer, workflow execution

### Operations Patterns
- **security.md**: Multi-layer security model, authentication methods (API key, JWT, OAuth2, mTLS), RBAC/ABAC
- **implementation.md**: Production deployment procedures, configuration management
- **git-integration.md**: Automated artifact capture, repository structure, continuous documentation

## Usage in Forge

These patterns inform Forge's:
1. **Layer 3 (Generation)**: Data transfer patterns for handling large codebases
2. **Layer 4 (Testing)**: Test scenario patterns for automated test generation
3. **Layer 5 (Refinement)**: Orchestration patterns for multi-agent review
4. **Layer 6 (Deployment)**: Git integration patterns for automated commits

## Relationship to KnowledgeForge 4.0

The patterns in this directory are **operational/infrastructure patterns**.

For **agent specification and coordination** patterns, see the KnowledgeForge 4.0 files in `../knowledgeforge/`:
- `00_Project_Instructions.md` - Core behavioral framework
- `01_Navigator_Agent.md` - Intent routing
- `02_Builder_Agent.md` - PDIA agent creation method
- `03_Coordination_Patterns.md` - Multi-agent orchestration
- `04_Specification_Templates.md` - Reusable specification formats
- `05_Expert_Agent_Example.md` - Domain specialist pattern
- `06_Quick_Reference.md` - Quick lookup guide
