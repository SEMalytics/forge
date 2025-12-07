# API Overview

Forge provides a comprehensive Python API for programmatic access to all functionality.

## Quick Start

```python
from forge.core.orchestrator import Orchestrator
from forge.core.config import ForgeConfig

# Initialize Forge
config = ForgeConfig.load()
orchestrator = Orchestrator(config)

# Create a project
project = orchestrator.create_project(
    name="My API",
    description="RESTful API for mobile app"
)

# Search patterns
patterns = orchestrator.search_patterns("REST API", max_results=5)

# Clean up
orchestrator.close()
```

## Module Organization

### Core Modules

**forge.core** - Core orchestration functionality

- `config` - Configuration management
- `orchestrator` - Main coordinator
- `state_manager` - Project and task state
- `session` - Session management

### KnowledgeForge Modules

**forge.knowledgeforge** - Pattern storage and search

- `pattern_store` - Hybrid storage system
- `search_engine` - Unified search interface
- `embeddings` - Vector embeddings
- `cache` - LRU caching

### CLI Modules

**forge.cli** - Command-line interface

- `main` - CLI entry point
- `output` - Rich formatting

### Utility Modules

**forge.utils** - Shared utilities

- `logger` - Structured logging
- `errors` - Custom exceptions

## Module Details

### forge.core.config

Configuration management with layered loading.

```python
from forge.core.config import ForgeConfig, GeneratorConfig

# Load configuration
config = ForgeConfig.load()

# Access settings
print(config.generator.backend)
print(config.knowledgeforge.search_method)

# Create custom config
config = ForgeConfig(
    generator=GeneratorConfig(backend="claude_code")
)

# Save configuration
config.save("forge.yaml")
```

**Key Classes:**
- `ForgeConfig` - Main configuration
- `GeneratorConfig` - Generator settings
- `GitConfig` - Git settings
- `KnowledgeForgeConfig` - Pattern settings
- `TestingConfig` - Testing settings

### forge.core.orchestrator

Main coordination layer.

```python
from forge.core.orchestrator import Orchestrator

# Create orchestrator
with Orchestrator() as orch:
    # Create project
    project = orch.create_project(
        name="Project",
        description="Description"
    )

    # Search patterns
    patterns = orch.search_patterns("query")

    # Get status
    status = orch.get_system_status()
```

**Key Classes:**
- `Orchestrator` - Main coordinator

**Key Methods:**
- `create_project()` - Create new project
- `get_project()` - Retrieve project
- `search_patterns()` - Search patterns
- `get_system_status()` - System information

### forge.core.state_manager

Project and task state management.

```python
from forge.core.state_manager import StateManager, TaskState

with StateManager() as state:
    # Create project
    project = state.create_project(
        project_id="test-001",
        name="Test",
        description="Test project"
    )

    # Create task
    task = TaskState(
        id="task-001",
        project_id="test-001",
        title="Implement feature",
        status="pending",
        priority=1,
        dependencies=[],
        generated_files={},
        test_results=None,
        commits=[]
    )
    state.create_task(task)

    # Create checkpoint
    state.checkpoint(
        project_id="test-001",
        stage="planning",
        state={"key": "value"},
        description="Planning complete"
    )
```

**Key Classes:**
- `StateManager` - State management
- `ProjectState` - Project representation
- `TaskState` - Task representation
- `Checkpoint` - Recovery point

**Key Methods:**
- `create_project()` - Create project
- `get_project()` - Get project
- `update_project_stage()` - Update stage
- `create_task()` - Create task
- `update_task_status()` - Update task
- `checkpoint()` - Create checkpoint
- `get_latest_checkpoint()` - Get checkpoint

### forge.knowledgeforge.pattern_store

Hybrid pattern storage with FTS5 and embeddings.

```python
from forge.knowledgeforge.pattern_store import PatternStore

with PatternStore() as store:
    # Get pattern count
    count = store.get_pattern_count()

    # Search patterns
    results = store.search(
        query="orchestration",
        max_results=10,
        method="hybrid"
    )

    # Get specific pattern
    pattern = store.get_pattern_by_filename("01_Core_DataTransfer.md")

    # Get all patterns
    all_patterns = store.get_all_patterns()
```

**Key Classes:**
- `PatternStore` - Pattern storage and search

**Key Methods:**
- `search()` - Search patterns
- `get_pattern_by_filename()` - Get by filename
- `get_all_patterns()` - Get all patterns
- `get_pattern_count()` - Get count

### forge.knowledgeforge.search_engine

Unified search interface with caching.

```python
from forge.knowledgeforge.search_engine import SearchEngine
from forge.knowledgeforge.pattern_store import PatternStore

store = PatternStore()
engine = SearchEngine(store)

# Search with caching
results = engine.search("query", max_results=10)

# Different search methods
keyword_results = engine.search("query", method="keyword")
semantic_results = engine.search("query", method="semantic")

# Get cache stats
stats = engine.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']}")

# Clear cache
engine.clear_cache()
```

**Key Classes:**
- `SearchEngine` - Unified search with caching

**Key Methods:**
- `search()` - Search patterns
- `search_by_topic()` - Search by topic
- `search_by_module()` - Search by module
- `get_related_patterns()` - Find related patterns
- `get_cache_stats()` - Cache statistics
- `clear_cache()` - Clear cache

### forge.knowledgeforge.embeddings

Vector embedding management.

```python
from forge.knowledgeforge.embeddings import EmbeddingManager

# Create manager
embeddings = EmbeddingManager()

# Encode single text
embedding = embeddings.encode("sample text")

# Encode batch
texts = ["text 1", "text 2", "text 3"]
batch_embeddings = embeddings.encode_batch(texts)

# Calculate similarity
similarity = embeddings.cosine_similarity(embedding1, embedding2)

# Find most similar
indices = embeddings.find_most_similar(
    query_embedding,
    candidate_embeddings,
    top_k=5
)
```

**Key Classes:**
- `EmbeddingManager` - Embedding operations

**Key Methods:**
- `encode()` - Encode single text
- `encode_batch()` - Encode multiple texts
- `cosine_similarity()` - Calculate similarity
- `find_most_similar()` - Find top matches

### forge.utils.logger

Structured logging with Rich.

```python
from forge.utils.logger import setup_logger, logger

# Setup custom logger
custom_logger = setup_logger(
    name="my_app",
    level=logging.DEBUG,
    log_file=Path("app.log")
)

# Use default logger
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")
```

**Key Functions:**
- `setup_logger()` - Create configured logger
- `logger` - Default logger instance

### forge.utils.errors

Custom exception hierarchy.

```python
from forge.utils.errors import (
    ForgeError,
    ConfigurationError,
    PatternStoreError,
    StateError
)

# Raise specific errors
raise ConfigurationError("Invalid config")
raise PatternStoreError("Pattern not found")
raise StateError("Invalid state transition")

# Catch Forge errors
try:
    # Forge operations
    pass
except ForgeError as e:
    print(f"Forge error: {e}")
```

**Key Classes:**
- `ForgeError` - Base exception
- `ConfigurationError` - Config errors
- `PatternStoreError` - Pattern errors
- `GenerationError` - Generation errors
- `TestExecutionError` - Test errors
- `StateError` - State errors
- `GitError` - Git errors
- `IntegrationError` - Integration errors

## Usage Patterns

### Context Managers

Most classes support context managers:

```python
# Orchestrator
with Orchestrator() as orch:
    project = orch.create_project("Name", "Description")

# Pattern Store
with PatternStore() as store:
    results = store.search("query")

# State Manager
with StateManager() as state:
    project = state.create_project("id", "name", "desc")
```

### Error Handling

```python
from forge.utils.errors import ForgeError

try:
    with Orchestrator() as orch:
        project = orch.create_project("Name", "Desc")
except ConfigurationError as e:
    print(f"Config error: {e}")
except StateError as e:
    print(f"State error: {e}")
except ForgeError as e:
    print(f"General error: {e}")
```

### Async Support

Currently synchronous API. Async support planned for future versions.

## Examples

See [API Examples](examples.md) for complete working examples:

- Creating and managing projects
- Searching patterns
- Working with state
- Custom configuration
- Error handling
- Batch operations

## Type Hints

All modules include comprehensive type hints:

```python
from typing import Optional, List, Dict
from forge.core.orchestrator import Orchestrator

def create_projects(
    orch: Orchestrator,
    names: List[str]
) -> List[ProjectState]:
    """Create multiple projects."""
    projects = []
    for name in names:
        project = orch.create_project(name, f"Project: {name}")
        projects.append(project)
    return projects
```

## API Stability

**Current Version: 1.0.0**

- Core API: Stable
- Breaking changes: Major version bump
- Deprecations: Announced in advance
- Documentation: Updated with changes

## Next Steps

- [Core API Reference](core.md) - Core modules in detail
- [KnowledgeForge API](knowledgeforge.md) - Pattern system API
- [API Examples](examples.md) - Working code examples
- [Developer Guide](../guides/developer-guide.md) - Contributing

## Getting Help

- Check module docstrings: `help(Orchestrator)`
- Review source code: `src/forge/`
- Run tests for examples: `tests/`
- Read user guide: [User Guide](../guides/user-guide.md)
