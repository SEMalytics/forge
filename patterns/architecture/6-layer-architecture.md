# 6-Layer Architecture Pattern

**Category**: Architecture
**Difficulty**: Intermediate
**Tags**: architecture, layers, design, system-design, workflow

## Context

When building complex software systems with Forge, you need a clear architectural pattern that separates concerns, enables parallel execution, and supports iterative refinement.

## Problem

Building software involves multiple stages: understanding requirements, planning, generating code, testing, fixing issues, and deploying. Without a clear architecture, these stages become tangled, making it hard to debug, optimize, or extend the system.

## Solution

Forge uses a 6-layer architecture where each layer has a specific responsibility:

```
┌──────────────────────────────────────────────────────────────┐
│                 Layer 6: Deployment Layer                     │
│          Git Workflows • PR Creation • Multi-Platform         │
├──────────────────────────────────────────────────────────────┤
│                 Layer 5: Review Layer                         │
│       Iterative Refinement • Failure Analysis • Learning      │
├──────────────────────────────────────────────────────────────┤
│                 Layer 4: Testing Layer                        │
│    Unit • Integration • Security • Performance • Docker       │
├──────────────────────────────────────────────────────────────┤
│                 Layer 3: Generation Layer                     │
│      Distributed Code Generation • Parallel Execution         │
├──────────────────────────────────────────────────────────────┤
│                 Layer 2: Planning Layer                       │
│        Tech Stack Selection • Architecture Design            │
├──────────────────────────────────────────────────────────────┤
│                 Layer 1: Decomposition Layer                  │
│          Task Breakdown • Dependency Analysis                │
└──────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**Layer 1: Decomposition**
- Input: High-level project description
- Output: Structured task plan with dependencies
- Purpose: Break complex projects into manageable tasks
- Technology: LLM-powered task decomposition

**Layer 2: Planning**
- Input: Task plan
- Output: Tech stack decisions, file structure
- Purpose: Make architectural decisions
- Technology: Pattern-based planning with knowledge integration

**Layer 3: Generation**
- Input: Task plan + tech stack
- Output: Complete codebase
- Purpose: Generate all project files
- Technology: Parallel distributed generation

**Layer 4: Testing**
- Input: Generated code
- Output: Test results, coverage reports
- Purpose: Validate correctness and quality
- Technology: Docker-isolated testing environment

**Layer 5: Review**
- Input: Test failures
- Output: Fixed code
- Purpose: Iteratively improve until tests pass
- Technology: Failure analysis + learning database

**Layer 6: Deployment**
- Input: Working code
- Output: Deployment configs, PRs, releases
- Purpose: Ship to production
- Technology: Multi-platform config generation + Git automation

## Data Flow

```
User Description
    ↓
[Layer 1] → Task Plan
    ↓
[Layer 2] → Tech Stack + Architecture
    ↓
[Layer 3] → Generated Code
    ↓
[Layer 4] → Test Results
    ↓ (if failures)
[Layer 5] → Fixed Code → [Layer 4]
    ↓ (if passing)
[Layer 6] → Deployed Application
```

## Examples

### Example 1: Simple REST API

```bash
# Layer 1: Decompose
forge decompose "Build a REST API for task management"
# → Creates 5 tasks: models, routes, middleware, tests, docs

# Layer 2: Plan
# → Selects: Python + FastAPI + PostgreSQL

# Layer 3: Generate
forge build --project task-api
# → Generates: app.py, models.py, routes.py, tests/

# Layer 4: Test
forge test --project task-api
# → Runs: unit tests, integration tests, security scan

# Layer 5: Iterate (if tests fail)
forge iterate --project task-api
# → Fixes errors, reruns tests

# Layer 6: Deploy
forge pr --project task-api
forge deploy --project task-api --platform flyio
```

### Example 2: ML Pipeline

```bash
# Layer 1: Complex decomposition with 15 tasks
forge decompose "ML pipeline for sales forecasting with Prophet"

# Layers 2-6: Fully automated
forge build --project ml-pipeline
forge test --project ml-pipeline
forge iterate --project ml-pipeline --max-iterations 10
forge deploy --project ml-pipeline --platform aws
```

## Benefits

1. **Separation of Concerns**: Each layer has one job
2. **Testability**: Each layer can be tested independently
3. **Parallelization**: Layer 3 can generate files in parallel
4. **Iterative Improvement**: Layer 5 learns from failures
5. **Flexibility**: Swap implementations without changing other layers
6. **Debugging**: Easy to pinpoint which layer has issues

## Trade-offs

**Pros:**
- Clear boundaries between stages
- Easy to extend with new capabilities
- Enables parallel execution
- Supports learning and improvement

**Cons:**
- More complex than a single-stage pipeline
- Requires state management between layers
- May be overkill for trivial projects

## Implementation

```python
from forge.layers import (
    DecompositionLayer,
    PlanningLayer,
    GenerationLayer,
    TestingOrchestrator,
    ReviewLayer,
    DeploymentGenerator
)

# Layer 1
decomposer = DecompositionLayer()
task_plan = decomposer.decompose_to_tasks(description)

# Layer 2
planner = PlanningLayer()
tech_stack = planner.plan_tech_stack(task_plan)

# Layer 3
generator = GenerationLayer()
code = await generator.generate_project(task_plan, parallel=True)

# Layer 4
tester = TestingOrchestrator()
results = await tester.test_project(project_id, code)

# Layer 5 (if tests fail)
if not results.all_passed:
    reviewer = ReviewLayer()
    fixed_code = await reviewer.iterate_until_passing(project_id)

# Layer 6
deployer = DeploymentGenerator(project_path)
deployer.generate_configs(config)
```

## Related Patterns

- **task-decomposition.md** - Details on Layer 1
- **parallel-generation.md** - Details on Layer 3
- **state-management.md** - Managing data between layers
- **failure-analysis.md** - Details on Layer 5

## References

- [Architecture Documentation](../../docs/ARCHITECTURE.md)
- [API Reference](../../docs/API_REFERENCE.md)
- Microservices Architecture Patterns
- Hexagonal Architecture (Ports & Adapters)
