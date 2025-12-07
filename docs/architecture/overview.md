# Architecture Overview

High-level architecture and design decisions for Forge.

## System Architecture

Forge follows a modular monolith architecture with clear layer separation and plugin support for extensions.

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Interface                         │
│              (Click + Rich Formatting)                   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Orchestrator                            │
│           (Main Coordination Layer)                      │
└─────┬──────────────┬──────────────┬────────────────────┘
      │              │              │
┌─────▼─────┐  ┌────▼────┐  ┌──────▼──────┐
│  Config   │  │  State  │  │ KnowledgeF  │
│  System   │  │ Manager │  │   orge      │
└───────────┘  └─────────┘  └─────────────┘
                     │              │
              ┌──────▼────┐  ┌──────▼──────┐
              │  SQLite   │  │ Pattern     │
              │ Databases │  │  Store      │
              └───────────┘  └──────┬──────┘
                                    │
                             ┌──────▼──────┐
                             │   FTS5 +    │
                             │  Embeddings │
                             └─────────────┘
```

## Core Components

### 1. CLI Layer

**Purpose:** User interface and command handling

**Components:**
- `cli/main.py` - Command definitions (Click)
- `cli/output.py` - Formatted output (Rich)

**Responsibilities:**
- Parse command-line arguments
- Validate user input
- Display formatted results
- Handle errors gracefully

**Design Decisions:**
- **Click Framework**: Industry-standard CLI framework
- **Rich Formatting**: Beautiful, terminal-aware output
- **Context Passing**: Share orchestrator across commands

### 2. Orchestrator Layer

**Purpose:** Main coordination and workflow management

**Components:**
- `core/orchestrator.py` - Central coordinator
- `core/session.py` - Session management

**Responsibilities:**
- Coordinate between subsystems
- Manage component lifecycle
- Provide unified API
- Handle cleanup

**Design Decisions:**
- **Facade Pattern**: Simple interface to complex subsystems
- **Context Manager**: Automatic resource cleanup
- **Dependency Injection**: Configuration passed at init

### 3. Configuration Layer

**Purpose:** Multi-layered configuration management

**Components:**
- `core/config.py` - Configuration classes

**Responsibilities:**
- Load configuration from multiple sources
- Validate configuration
- Provide defaults
- Support environment variables

**Design Decisions:**
- **Pydantic Models**: Type-safe validation
- **Layered Loading**: Environment < Project < Global
- **Immutability**: Configuration read-only after load

**Configuration Hierarchy:**
```
┌──────────────────────┐
│  Environment Vars    │  ← Highest Priority
├──────────────────────┤
│  Project Config      │
│  (./forge.yaml)      │
├──────────────────────┤
│  Global Config       │
│  (~/.forge/config)   │
├──────────────────────┤
│  Built-in Defaults   │  ← Lowest Priority
└──────────────────────┘
```

### 4. State Management Layer

**Purpose:** Persistent project and task state

**Components:**
- `core/state_manager.py` - State operations
- SQLite databases - Persistent storage

**Responsibilities:**
- Store project metadata
- Track task progress
- Create checkpoints
- Support recovery

**Design Decisions:**
- **SQLite**: Embedded, zero-config database
- **Checkpoints**: Point-in-time recovery
- **Transactions**: ACID guarantees
- **JSON Blobs**: Flexible metadata storage

**Database Schema:**
```sql
projects
  ├── id (PK)
  ├── name
  ├── description
  ├── stage
  ├── created_at
  ├── updated_at
  └── metadata (JSON)

tasks
  ├── id (PK)
  ├── project_id (FK)
  ├── title
  ├── status
  ├── priority
  ├── dependencies (JSON)
  ├── generated_files (JSON)
  └── ...

checkpoints
  ├── id (PK)
  ├── project_id (FK)
  ├── stage
  ├── timestamp
  ├── state_snapshot (JSON)
  └── description
```

### 5. KnowledgeForge Layer

**Purpose:** Pattern storage and search

**Components:**
- `knowledgeforge/pattern_store.py` - Hybrid storage
- `knowledgeforge/search_engine.py` - Unified search
- `knowledgeforge/embeddings.py` - Vector embeddings
- `knowledgeforge/cache.py` - LRU caching

**Responsibilities:**
- Index pattern files
- Fast keyword search (FTS5)
- Semantic search (embeddings)
- Cache frequent searches
- Track usage patterns

**Design Decisions:**
- **Hybrid Search**: FTS5 + Embeddings for best results
- **SQLite FTS5**: Fast full-text search
- **Sentence Transformers**: Offline embeddings
- **LRU Cache**: Frequently accessed patterns
- **Usage Tracking**: Optimize cache strategy

**Search Architecture:**
```
┌─────────────┐
│   Query     │
└──────┬──────┘
       │
   ┌───▼────┐
   │ Cache? │──Yes──► Return Cached
   └───┬────┘
       │No
   ┌───▼────────┐
   │   Method   │
   └─┬──────┬───┘
     │      │
┌────▼──┐ ┌▼────────┐
│ FTS5  │ │Embedding│
│Search │ │ Search  │
└───┬───┘ └┬────────┘
    │      │
    └──┬───┘
   ┌───▼──────┐
   │  Merge & │
   │Deduplicate│
   └───┬──────┘
   ┌───▼────┐
   │ Cache  │
   └───┬────┘
   ┌───▼────┐
   │ Return │
   └────────┘
```

### 6. Utilities Layer

**Purpose:** Shared functionality

**Components:**
- `utils/logger.py` - Structured logging
- `utils/errors.py` - Custom exceptions

**Responsibilities:**
- Logging with Rich formatting
- Exception hierarchy
- Common utilities

**Design Decisions:**
- **Rich Logging**: Beautiful, readable logs
- **Exception Hierarchy**: Specific error types
- **Minimal Dependencies**: Keep utils simple

## Design Patterns

### Facade Pattern

**Orchestrator** provides simple interface to complex subsystems:

```python
# Complex subsystems hidden behind simple API
orchestrator = Orchestrator()
project = orchestrator.create_project("Name", "Desc")
patterns = orchestrator.search_patterns("query")
```

### Repository Pattern

**StateManager** abstracts database operations:

```python
# Database details hidden
state = StateManager()
project = state.create_project(id, name, desc)
task = state.get_task(task_id)
```

### Strategy Pattern

**SearchEngine** supports multiple search strategies:

```python
# Different strategies for different needs
results = search_engine.search("query", method="keyword")
results = search_engine.search("query", method="semantic")
results = search_engine.search("query", method="hybrid")
```

### Factory Pattern (Future)

Generator backends will use factory pattern:

```python
# Create appropriate generator
generator = GeneratorFactory.create(backend_type, config)
```

### Context Manager Pattern

Most classes support resource management:

```python
with Orchestrator() as orch:
    # Resources automatically cleaned up
    project = orch.create_project("Name", "Desc")
# Cleanup happens here
```

## Data Flow

### Project Creation Flow

```
User Command
    │
    ├─► CLI Parser (Click)
    │
    ├─► Orchestrator.create_project()
    │       │
    │       ├─► Generate project ID
    │       │
    │       ├─► StateManager.create_project()
    │       │       │
    │       │       └─► SQLite INSERT
    │       │
    │       └─► StateManager.checkpoint()
    │               │
    │               └─► SQLite INSERT checkpoint
    │
    └─► Display Result (Rich)
```

### Pattern Search Flow

```
User Query
    │
    ├─► CLI Parser
    │
    ├─► Orchestrator.search_patterns()
    │       │
    │       └─► SearchEngine.search()
    │               │
    │               ├─► Check Cache
    │               │   └─► Cache Hit? Return
    │               │
    │               ├─► PatternStore.search()
    │               │   │
    │               │   ├─► Keyword Search (FTS5)
    │               │   │   └─► SELECT ... MATCH ...
    │               │   │
    │               │   ├─► Semantic Search (Embeddings)
    │               │   │   └─► Cosine Similarity
    │               │   │
    │               │   └─► Merge Results
    │               │
    │               └─► Cache Results
    │
    └─► Display Results (Rich Table)
```

## Technology Choices

### Language & Runtime

- **Python 3.11+**: Modern Python with performance improvements
- **Type Hints**: Full type coverage for IDE support
- **Dataclasses**: Clean, efficient data structures

### Dependencies

**Core:**
- **Click**: CLI framework (industry standard)
- **Rich**: Terminal formatting (beautiful output)
- **Pydantic**: Configuration validation (type safety)
- **SQLite**: Embedded database (zero config)

**AI/ML:**
- **Sentence Transformers**: Offline embeddings
- **all-MiniLM-L6-v2**: Fast, good quality model (90MB)

**Development:**
- **Poetry**: Dependency management
- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking
- **ruff**: Fast linting

### Storage

**SQLite** for all persistence:
- Zero configuration required
- ACID transactions
- Full SQL support
- FTS5 for text search
- Portable single-file database
- No server needed

## Scalability Considerations

### Current Scale

- **Patterns**: 28 files (~2MB total)
- **Projects**: Hundreds per database
- **Search**: Sub-second responses
- **Memory**: ~200MB with model loaded

### Growth Strategy

**More Patterns (100s):**
- FTS5 scales to millions of rows
- Embedding search remains fast
- Increase cache size

**More Projects (1000s):**
- SQLite handles millions of rows
- Add indexes as needed
- Consider archiving old projects

**Distributed Deployment:**
- Each instance has own databases
- Patterns can be shared (read-only)
- State databases per instance

## Security Considerations

### API Keys

- Never store in code or config
- Use environment variables
- Support key rotation
- Warn on plain-text keys

### Database Security

- File permissions (644 for DBs)
- No remote access
- Local-only by default
- Backup encryption recommended

### Input Validation

- Pydantic for config
- SQL parameterization (no injection)
- Path validation (no traversal)
- Length limits on user input

## Performance Optimization

### Pattern Store

**Optimizations:**
- FTS5 for fast keyword search
- LRU cache for repeated searches
- Batch embedding generation
- Lazy model loading

**Metrics:**
- First load: ~2s (model loading)
- Subsequent: <100ms per search
- Cache hit: <1ms

### State Manager

**Optimizations:**
- Indexed queries
- Transaction batching
- Prepared statements
- Checkpoint compression

**Metrics:**
- Project creation: <10ms
- Task updates: <5ms
- Checkpoint creation: <20ms

## Error Handling Strategy

### Exception Hierarchy

```
ForgeError (base)
├── ConfigurationError
├── PatternStoreError
├── StateError
├── GenerationError
├── TestExecutionError
├── GitError
└── IntegrationError
```

### Error Recovery

- Checkpoints enable recovery
- Transactions ensure consistency
- Graceful degradation where possible
- Clear error messages

## Testing Strategy

### Unit Tests

- Test individual components
- Mock external dependencies
- Fast execution (<1s)
- High coverage (80%+ for core)

### Integration Tests

- Test component interactions
- Use temporary databases
- Clean up after each test
- Verify end-to-end flows

### Test Structure

```
tests/
├── test_config.py        # Configuration
├── test_state_manager.py # State management
└── test_pattern_store.py # Pattern storage
```

## Future Architecture

### Planned Enhancements

**Layer 1-6 Implementation:**
- Planning layer (conversational)
- Decomposition layer (task breakdown)
- Generation layer (code generation)
- Testing layer (automated tests)
- Review layer (code review)
- Deployment layer (deployment)

**Plugin System:**
- Generator plugins
- Deployer plugins
- Custom patterns
- Extension hooks

**API Server:**
- REST API
- WebSocket for streaming
- Authentication
- Rate limiting

## See Also

- [Pattern Store Design](pattern-store.md) - Detailed search architecture
- [State Management](state-management.md) - Database schema details
- [Database Schema](database-schema.md) - Complete schema reference
- [Developer Guide](../guides/developer-guide.md) - Contributing
