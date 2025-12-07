# Forge Architecture

## Overview

Forge is a 6-layer AI development orchestration system designed for scalability, modularity, and extensibility. Each layer has a specific responsibility and communicates through well-defined interfaces.

## Design Principles

1. **Separation of Concerns** - Each layer handles one aspect of development
2. **Progressive Enhancement** - Layers build upon previous layers
3. **Fail-Fast** - Errors caught early prevent wasted resources
4. **Parallel Execution** - Independent tasks run concurrently
5. **Pattern-Driven** - Knowledge patterns guide generation
6. **Test-Driven** - Testing integrated at every step

## Layer Architecture

```
User Input (Natural Language)
         ↓
┌────────────────────────────────────┐
│   Layer 1: Decomposition           │  ← KnowledgeForge Patterns
│   - Conversational planning        │
│   - Task breakdown                 │
│   - Dependency analysis            │
└────────────────────────────────────┘
         ↓ TaskPlan
┌────────────────────────────────────┐
│   Layer 2: Planning                │  ← Tech Stack Selection
│   - File structure design          │
│   - Technology selection           │
│   - Module organization            │
└────────────────────────────────────┘
         ↓ ProjectPlan
┌────────────────────────────────────┐
│   Layer 3: Generation              │  ← Multi-Agent Generation
│   - Parallel code generation       │
│   - Pattern application            │
│   - Quality assurance              │
└────────────────────────────────────┘
         ↓ GeneratedCode
┌────────────────────────────────────┐
│   Layer 4: Testing                 │  ← Docker Isolation
│   - Unit tests                     │
│   - Integration tests              │
│   - Security scanning              │
│   - Performance benchmarking       │
└────────────────────────────────────┘
         ↓ TestResults
┌────────────────────────────────────┐
│   Layer 5: Review                  │  ← Iterative Refinement
│   - Failure analysis               │
│   - Fix generation                 │
│   - Learning database              │
└────────────────────────────────────┘
         ↓ Fixes (if needed, loop to Layer 4)
┌────────────────────────────────────┐
│   Layer 6: Deployment              │  ← Git & Deployment
│   - Git workflows                  │
│   - PR creation                    │
│   - Deployment configs             │
└────────────────────────────────────┘
         ↓
Production-Ready Code
```

## Layer Details

### Layer 1: Decomposition

**Purpose**: Transform user requirements into actionable tasks

**Components**:
- `DecompositionLayer` - Main orchestrator
- `ConversationalPlanner` - Interactive requirement gathering
- `TaskDecomposer` - Break down into tasks
- `DependencyAnalyzer` - Build dependency graph

**Key Data Structures**:
```python
@dataclass
class Task:
    id: str
    title: str
    description: str
    dependencies: List[str]
    complexity: Complexity
    estimated_time: int  # minutes
    tech_stack: List[str]
    file_outputs: List[str]
```

**Pattern Usage**:
- Loads KB3 patterns for best practices
- Uses pattern library to identify task types
- Applies complexity estimation patterns

**Flow**:
1. User provides natural language description
2. System asks clarifying questions
3. Decomposes into tasks with KF patterns
4. Analyzes dependencies
5. Estimates complexity
6. Returns TaskPlan

### Layer 2: Planning

**Purpose**: Design project structure and select technologies

**Components**:
- `PlanningLayer` - Structure designer
- `TechStackSelector` - Technology selection
- `FileStructureGenerator` - Directory layout
- `DependencyResolver` - Package management

**Key Data Structures**:
```python
@dataclass
class ProjectPlan:
    tasks: List[Task]
    file_structure: Dict[str, FileSpec]
    tech_stack: TechStack
    dependencies: List[str]
    entry_points: List[str]
```

**Pattern Usage**:
- Project structure patterns
- Tech stack best practices
- Naming conventions

**Flow**:
1. Receives TaskPlan
2. Selects appropriate tech stack
3. Designs file structure
4. Plans module organization
5. Returns ProjectPlan

### Layer 3: Generation

**Purpose**: Generate code using AI and patterns

**Components**:
- `GenerationLayer` - Generation orchestrator
- `CodeGenAPI` - API-based generation
- `ClaudeCodeGenerator` - Claude-based generation
- `GeneratorFactory` - Provider abstraction
- `QualityChecker` - Code validation

**Providers**:
- **Anthropic Claude** (primary)
- **OpenAI GPT-4** (fallback)

**Key Features**:
- **Parallel Generation** - Multiple tasks simultaneously
- **Pattern Integration** - KF patterns in prompts
- **Context Management** - Cross-file dependencies
- **Quality Checks** - Syntax validation, best practices

**Flow**:
1. Receives ProjectPlan
2. Groups tasks by dependencies
3. Generates code in parallel waves
4. Validates each output
5. Returns GeneratedCode

### Layer 4: Testing

**Purpose**: Comprehensive testing and validation

**Components**:
- `TestingOrchestrator` - Test coordination
- `DockerRunner` - Isolated test execution
- `TestGenerator` - Test code generation
- `SecurityScanner` - Vulnerability detection
- `PerformanceBenchmark` - Performance testing

**Test Types**:
1. **Unit Tests** - Individual function/class testing
2. **Integration Tests** - Component interaction testing
3. **Security Scans** - Vulnerability detection
4. **Performance Tests** - Latency/throughput benchmarks

**Docker Isolation**:
- Each test suite runs in isolated container
- Clean environment per test
- Reproducible results
- Resource limits

**Flow**:
1. Receives GeneratedCode
2. Generates test code
3. Builds Docker environment
4. Runs test suites
5. Scans for vulnerabilities
6. Benchmarks performance
7. Returns ComprehensiveTestReport

### Layer 5: Review

**Purpose**: Iterative refinement until tests pass

**Components**:
- `ReviewLayer` - Iteration controller
- `FailureAnalyzer` - Root cause detection
- `FixGenerator` - AI-powered fix generation
- `LearningDatabase` - Success pattern storage

**Iteration Process**:
1. Run tests
2. Analyze failures (14 failure types)
3. Generate fixes (top 3 per iteration)
4. Apply fixes
5. Repeat (max 5 iterations)

**Failure Types**:
- Syntax errors
- Import errors
- Type errors
- Logic errors (assertions)
- Security vulnerabilities
- Performance degradation

**Learning System**:
- Stores successful fix patterns
- Tracks fix success rate
- Calculates average iterations
- Improves over time

**Flow**:
1. Receives test failures
2. Categorizes and analyzes
3. Generates targeted fixes
4. Applies fixes
5. Re-runs tests
6. Updates learning database

### Layer 6: Deployment

**Purpose**: Git workflows and deployment automation

**Components**:
- `ForgeRepository` - Git operations
- `GitHubClient` - PR management
- `DeploymentGenerator` - Platform configs
- `ConventionalCommit` - Commit formatting

**Features**:
- **Branch Management** - `forge/*` naming
- **Conventional Commits** - Structured messages
- **PR Creation** - With checklists
- **Multi-Platform** - 5 deployment targets

**Platforms**:
1. fly.io
2. Vercel
3. AWS Lambda
4. Docker/Docker Compose
5. Kubernetes

**Flow**:
1. Create feature branch
2. Generate deployment configs
3. Commit with conventional format
4. Push to remote
5. Create PR with checklist

## Data Flow

### Complete Build Flow

```
User Description
    ↓
┌─────────────────────┐
│ 1. Decomposition    │
└─────────────────────┘
    ↓ TaskPlan
┌─────────────────────┐
│ 2. Planning         │
└─────────────────────┘
    ↓ ProjectPlan
┌─────────────────────┐
│ 3. Generation       │  ← Parallel execution
└─────────────────────┘
    ↓ GeneratedCode
┌─────────────────────┐
│ 4. Testing          │  ← Docker isolation
└─────────────────────┘
    ↓ TestResults
    │
    ├─ Tests Pass ──────────────┐
    │                            ↓
    └─ Tests Fail          ┌─────────────────────┐
        ↓                  │ 6. Deployment       │
   ┌─────────────────────┐└─────────────────────┘
   │ 5. Review & Fix     │     ↓
   └─────────────────────┘  Production
        ↓
   (Loop to Testing)
```

### State Management

Forge maintains state across layers using `StateManager`:

```python
class StateManager:
    def save_task_plan(project_id: str, plan: TaskPlan)
    def load_task_plan(project_id: str) -> TaskPlan

    def save_project_plan(project_id: str, plan: ProjectPlan)
    def load_project_plan(project_id: str) -> ProjectPlan

    def save_generated_code(project_id: str, code: GeneratedCode)
    def load_generated_code(project_id: str) -> GeneratedCode

    def save_test_results(project_id: str, results: TestResults)
    def load_test_results(project_id: str) -> TestResults
```

State stored in `.forge/state/<project_id>/`:
- `task_plan.json`
- `project_plan.json`
- `generated_code/`
- `test_results.json`

## Cross-Cutting Concerns

### Knowledge Management

**PatternStore** - Centralized pattern access
```python
class PatternStore:
    def search_patterns(query: str) -> List[Pattern]
    def get_pattern_by_id(id: str) -> Pattern
    def get_similar_patterns(pattern: Pattern) -> List[Pattern]
```

Uses semantic search with embeddings for relevance.

### Error Handling

**ForgeError** - Base exception class
```python
class ForgeError(Exception):
    """Base exception for Forge"""

class DecompositionError(ForgeError):
    """Task decomposition errors"""

class GenerationError(ForgeError):
    """Code generation errors"""

class TestingError(ForgeError):
    """Testing errors"""
```

All errors include:
- Clear error message
- Fix suggestions
- Documentation links
- Example solutions

### Logging

Structured logging throughout:
```python
logger.info("Starting code generation", extra={
    "project_id": project_id,
    "task_count": len(tasks),
    "provider": "anthropic"
})
```

Log levels:
- `DEBUG` - Detailed diagnostic info
- `INFO` - Normal operation milestones
- `WARNING` - Unexpected but handled
- `ERROR` - Operation failures
- `CRITICAL` - System failures

## Performance Optimizations

### Parallel Execution

Tasks executed in dependency waves:
```
Wave 1: [Task A, Task B, Task C]  ← No dependencies
   ↓
Wave 2: [Task D, Task E]           ← Depend on Wave 1
   ↓
Wave 3: [Task F]                   ← Depends on Wave 2
```

Max parallelism: 4 workers (configurable)

### Caching

**Pattern Embeddings** - Cached to avoid recomputation
```
~/.forge/cache/
  embeddings/
    patterns.pkl
    last_updated.txt
```

**Test Results** - Cached until code changes
```
.forge/cache/<project_id>/
  test_results_<hash>.json
```

### Memory Management

**Streaming** - Large files processed incrementally
**Batching** - Tasks grouped to reduce API calls
**Cleanup** - Temporary files deleted after use

## Extension Points

### Custom Generators

```python
class CustomGenerator(BaseGenerator):
    def generate_code(
        self,
        task: Task,
        context: GenerationContext
    ) -> GeneratedCode:
        # Custom generation logic
        pass

# Register
GeneratorFactory.register("custom", CustomGenerator)
```

### Custom Test Frameworks

```python
class CustomTestRunner(BaseTestRunner):
    def run_tests(
        self,
        code_dir: Path,
        test_dir: Path
    ) -> TestResult:
        # Custom test execution
        pass
```

### Custom Deployment Platforms

```python
class CustomPlatform(DeploymentGenerator):
    def generate_configs(
        self,
        config: DeploymentConfig
    ) -> List[Path]:
        # Generate platform configs
        pass
```

## Security Considerations

### API Key Management
- Never logged or stored in files
- Environment variables only
- Encrypted in memory if possible

### Code Execution
- All tests run in isolated Docker containers
- Resource limits enforced
- Network isolation optional

### Generated Code
- Security scanning mandatory
- Vulnerability database checks
- Best practice validation

## Scalability

### Horizontal Scaling
- Stateless generation workers
- Task queue for distribution
- Shared state storage

### Vertical Scaling
- Configurable worker count
- Memory limits per task
- Timeout controls

## Monitoring

### Metrics Collected
- Task completion time
- API call count/latency
- Test pass rate
- Fix success rate
- Memory usage
- Error rates

### Health Checks
- Pattern store connectivity
- API provider status
- Docker daemon status
- Disk space available

## Future Architecture

### Planned Enhancements
1. **Web UI** - Visual project planning
2. **Cloud Execution** - Serverless generation
3. **Team Features** - Shared projects
4. **Plugin System** - Third-party extensions
5. **IDE Integration** - VSCode/PyCharm plugins

### Architecture Evolution
- Microservices for layers
- Message queue between layers
- Distributed state management
- Multi-tenancy support

## Related Documentation

- [Git Workflows](./GIT_WORKFLOWS.md)
- [Failure Analysis](./FAILURE_ANALYSIS_SYSTEM.md)
- [Testing System](./TESTING_SYSTEM.md)
- [API Reference](./API_REFERENCE.md)
