"""
Tests for task decomposition layer
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from forge.integrations.compound_engineering import (
    CompoundEngineeringClient,
    Task,
    CompoundEngineeringError
)
from forge.layers.decomposition import TaskDecomposer, DecompositionError


# Fixtures

@pytest.fixture
def sample_task():
    """Create a sample task for testing"""
    return Task(
        id="task-001",
        title="Project Setup",
        description="Initialize project structure",
        dependencies=[],
        priority=1,
        estimated_complexity="low",
        acceptance_criteria=[
            "Project initialized",
            "Dependencies installed"
        ],
        tags=["setup"]
    )


@pytest.fixture
def sample_tasks():
    """Create sample task list with dependencies"""
    return [
        Task(
            id="task-001",
            title="Setup",
            description="Setup project",
            dependencies=[],
            priority=1,
            tags=["setup"]
        ),
        Task(
            id="task-002",
            title="Core Implementation",
            description="Build core features",
            dependencies=["task-001"],
            priority=2,
            tags=["implementation"]
        ),
        Task(
            id="task-003",
            title="Testing",
            description="Add tests",
            dependencies=["task-002"],
            priority=3,
            tags=["testing"]
        )
    ]


@pytest.fixture
def ce_client():
    """Create CE client for testing"""
    return CompoundEngineeringClient()


@pytest.fixture
def mock_pattern_store():
    """Mock pattern store"""
    store = Mock()
    store.search.return_value = [
        {
            "filename": "api-design-patterns.md",
            "title": "API Design Patterns",
            "content": "REST API best practices...",
            "score": 0.85
        },
        {
            "filename": "testing-strategies.md",
            "title": "Testing Strategies",
            "content": "Unit and integration testing...",
            "score": 0.75
        }
    ]
    return store


@pytest.fixture
def task_decomposer(mock_pattern_store):
    """Create task decomposer with mocked dependencies"""
    with patch('forge.layers.decomposition.StateManager'):
        decomposer = TaskDecomposer(pattern_store=mock_pattern_store)
        return decomposer


# CompoundEngineeringClient Tests

def test_ce_client_initialization(ce_client):
    """Test CE client initialization"""
    assert ce_client is not None
    assert ce_client.ce_plugin_path is not None


def test_ce_client_basic_plan(ce_client):
    """Test basic planning without CE plugin"""
    tasks = ce_client.plan("Build a REST API", tech_stack=["Python", "FastAPI"])

    assert len(tasks) > 0
    assert all(isinstance(task, Task) for task in tasks)
    assert tasks[0].id == "task-001"
    assert "setup" in tasks[0].tags[0].lower() or "project" in tasks[0].title.lower()


def test_ce_client_validate_dependencies_valid(sample_tasks):
    """Test dependency validation with valid dependencies"""
    ce_client = CompoundEngineeringClient()
    assert ce_client.validate_task_dependencies(sample_tasks) is True


def test_ce_client_validate_dependencies_circular():
    """Test dependency validation detects circular dependencies"""
    circular_tasks = [
        Task(id="task-001", title="A", description="A", dependencies=["task-002"], priority=1),
        Task(id="task-002", title="B", description="B", dependencies=["task-001"], priority=2)
    ]

    ce_client = CompoundEngineeringClient()
    assert ce_client.validate_task_dependencies(circular_tasks) is False


def test_ce_client_validate_dependencies_invalid_ref():
    """Test dependency validation detects invalid references"""
    invalid_tasks = [
        Task(id="task-001", title="A", description="A", dependencies=["task-999"], priority=1)
    ]

    ce_client = CompoundEngineeringClient()
    assert ce_client.validate_task_dependencies(invalid_tasks) is False


def test_ce_client_execution_order(sample_tasks):
    """Test task execution order sorting"""
    ce_client = CompoundEngineeringClient()
    ordered = ce_client.get_task_execution_order(sample_tasks)

    assert len(ordered) == len(sample_tasks)
    assert ordered[0].id == "task-001"  # No dependencies, comes first
    assert ordered[1].id == "task-002"  # Depends on 001
    assert ordered[2].id == "task-003"  # Depends on 002


def test_ce_client_execution_order_invalid():
    """Test execution order fails with circular dependencies"""
    circular_tasks = [
        Task(id="task-001", title="A", description="A", dependencies=["task-002"], priority=1),
        Task(id="task-002", title="B", description="B", dependencies=["task-001"], priority=2)
    ]

    ce_client = CompoundEngineeringClient()

    with pytest.raises(CompoundEngineeringError):
        ce_client.get_task_execution_order(circular_tasks)


def test_task_to_dict(sample_task):
    """Test task serialization to dict"""
    task_dict = sample_task.to_dict()

    assert task_dict["id"] == "task-001"
    assert task_dict["title"] == "Project Setup"
    assert task_dict["priority"] == 1
    assert "setup" in task_dict["tags"]
    assert len(task_dict["acceptance_criteria"]) == 2


def test_ce_style_plan_extracts_features():
    """Test CE-style planning extracts features from description"""
    ce_client = CompoundEngineeringClient()

    description = "Build a REST API with user authentication and database storage"
    tasks = ce_client._ce_style_plan(description, tech_stack=["Python"])

    # Should have setup + features + testing + docs
    assert len(tasks) >= 4

    # Check that features are extracted
    task_titles = [t.title.lower() for t in tasks]
    task_content = " ".join(task_titles)

    # Should contain some common features
    assert any(keyword in task_content for keyword in ["api", "auth", "database", "setup", "test"])


# TaskDecomposer Tests

def test_decomposer_initialization(task_decomposer):
    """Test task decomposer initialization"""
    assert task_decomposer is not None
    assert task_decomposer.pattern_store is not None
    assert task_decomposer.ce_client is not None


def test_decomposer_decompose(task_decomposer):
    """Test basic decomposition"""
    tasks = task_decomposer.decompose(
        "Build a todo list API",
        tech_stack=["Python", "FastAPI"]
    )

    assert len(tasks) > 0
    assert all(isinstance(task, Task) for task in tasks)

    # Check KF patterns were added
    assert any(task.kf_patterns for task in tasks)


def test_decomposer_pattern_search_query(task_decomposer):
    """Test pattern search query building"""
    query = task_decomposer._build_pattern_search_query(
        "REST API",
        tech_stack=["Python", "FastAPI"]
    )

    assert "REST API" in query
    assert "Python" in query
    assert "FastAPI" in query


def test_decomposer_extract_task_keywords():
    """Test keyword extraction from tasks"""
    task = Task(
        id="test",
        title="API Authentication",
        description="Implement JWT authentication for the API",
        dependencies=[],
        priority=1,
        tags=["security", "api"]
    )

    decomposer = TaskDecomposer()
    keywords = decomposer._extract_task_keywords(task)

    assert "api" in keywords
    assert "authentication" in keywords or "auth" in keywords
    assert "security" in keywords


def test_decomposer_categorize_pattern():
    """Test pattern categorization"""
    pattern = {
        "filename": "api-testing-guide.md",
        "title": "API Testing Best Practices",
        "content": "This guide covers testing REST APIs with unit tests and integration tests..."
    }

    decomposer = TaskDecomposer()
    categories = decomposer._categorize_pattern(pattern)

    assert "api" in categories
    assert "testing" in categories


def test_decomposer_find_relevant_patterns(mock_pattern_store):
    """Test finding relevant patterns for a task"""
    task = Task(
        id="task-002",
        title="Build REST API",
        description="Create RESTful endpoints",
        dependencies=[],
        priority=2,
        tags=["api", "implementation"]
    )

    patterns = [
        {
            "filename": "api-design-patterns.md",
            "title": "API Design",
            "content": "REST API design patterns and best practices",
            "score": 0.9
        },
        {
            "filename": "database-optimization.md",
            "title": "Database Optimization",
            "content": "Query optimization techniques",
            "score": 0.5
        }
    ]

    decomposer = TaskDecomposer(pattern_store=mock_pattern_store)
    relevant = decomposer._find_relevant_patterns(task, patterns, ["Python"])

    # Should find the API pattern as relevant
    assert len(relevant) > 0


def test_decomposer_get_task_summary(sample_tasks):
    """Test task summary generation"""
    decomposer = TaskDecomposer()
    summary = decomposer.get_task_summary(sample_tasks)

    assert summary["total_tasks"] == 3
    assert "by_priority" in summary
    assert "by_complexity" in summary
    assert "by_tag" in summary
    assert summary["avg_dependencies"] >= 0


def test_decomposer_calculate_max_depth(sample_tasks):
    """Test max dependency depth calculation"""
    decomposer = TaskDecomposer()
    depth = decomposer._calculate_max_depth(sample_tasks)

    # task-001 -> task-002 -> task-003 = depth of 2
    assert depth == 2


def test_decomposer_visualize_dependency_graph(sample_tasks):
    """Test dependency graph visualization"""
    decomposer = TaskDecomposer()
    graph = decomposer.visualize_dependency_graph(sample_tasks)

    assert "task-001" in graph
    assert "task-002" in graph
    assert "task-003" in graph
    assert "depends on" in graph.lower()


def test_decomposer_save_decomposition(task_decomposer, sample_tasks, tmp_path):
    """Test saving decomposition to project"""
    # Mock state manager
    mock_state = Mock()
    mock_state.checkpoint = Mock()
    mock_state.create_task = Mock()

    task_decomposer.state_manager = mock_state

    # Save decomposition
    task_decomposer._save_decomposition("test-project", sample_tasks, [])

    # Verify checkpoint was created
    mock_state.checkpoint.assert_called_once()

    # Verify tasks were created
    assert mock_state.create_task.call_count == len(sample_tasks)


def test_decomposer_with_project_id(task_decomposer):
    """Test decomposition with project ID saves to state"""
    # Mock state manager
    mock_state = Mock()
    mock_state.checkpoint = Mock()
    mock_state.create_task = Mock()

    task_decomposer.state_manager = mock_state

    # Decompose with project ID
    tasks = task_decomposer.decompose(
        "Build API",
        tech_stack=["Python"],
        project_id="test-project-001"
    )

    # Should have saved to state
    assert mock_state.checkpoint.called
    assert mock_state.create_task.called


# Integration Tests

def test_full_decomposition_workflow():
    """Test complete decomposition workflow"""
    with patch('forge.layers.decomposition.StateManager'):
        with patch('forge.layers.decomposition.PatternStore') as MockStore:
            # Setup mock pattern store
            mock_store = MockStore.return_value
            mock_store.search.return_value = [
                {
                    "filename": "api-patterns.md",
                    "title": "API Patterns",
                    "content": "REST API patterns",
                    "score": 0.8
                }
            ]

            decomposer = TaskDecomposer(pattern_store=mock_store)

            # Decompose
            tasks = decomposer.decompose(
                "Build a REST API with authentication",
                tech_stack=["Python", "FastAPI", "PostgreSQL"]
            )

            # Verify results
            assert len(tasks) > 0
            assert all(isinstance(task, Task) for task in tasks)

            # Verify patterns were searched
            mock_store.search.assert_called()

            # Verify tasks have structure
            for task in tasks:
                assert task.id
                assert task.title
                assert task.description
                assert isinstance(task.priority, int)


def test_decompose_with_empty_description():
    """Test decomposition with empty description still works"""
    decomposer = TaskDecomposer()

    # Empty description should still generate basic tasks
    tasks = decomposer.decompose("")

    # Should have at least basic tasks
    assert len(tasks) > 0
    assert all(isinstance(task, Task) for task in tasks)


def test_complex_dependency_graph():
    """Test complex task dependency graph"""
    tasks = [
        Task(id="task-001", title="A", description="A", dependencies=[], priority=1),
        Task(id="task-002", title="B", description="B", dependencies=["task-001"], priority=2),
        Task(id="task-003", title="C", description="C", dependencies=["task-001"], priority=2),
        Task(id="task-004", title="D", description="D", dependencies=["task-002", "task-003"], priority=3),
    ]

    ce_client = CompoundEngineeringClient()

    # Validate dependencies
    assert ce_client.validate_task_dependencies(tasks) is True

    # Get execution order
    ordered = ce_client.get_task_execution_order(tasks)

    # task-001 must come first
    assert ordered[0].id == "task-001"

    # task-002 and task-003 can be in any order but after task-001
    assert ordered[1].id in ["task-002", "task-003"]
    assert ordered[2].id in ["task-002", "task-003"]

    # task-004 must come last
    assert ordered[3].id == "task-004"


def test_task_with_multiple_patterns():
    """Test task enrichment with multiple patterns"""
    patterns = [
        {"filename": f"pattern-{i}.md", "title": f"Pattern {i}", "content": "API testing", "score": 0.8}
        for i in range(10)
    ]

    task = Task(
        id="task-001",
        title="API Testing",
        description="Test the API endpoints",
        dependencies=[],
        priority=1,
        tags=["testing", "api"]
    )

    decomposer = TaskDecomposer()
    relevant = decomposer._find_relevant_patterns(task, patterns, ["Python"])

    # Should limit to top 3 patterns
    assert len(relevant) <= 3
