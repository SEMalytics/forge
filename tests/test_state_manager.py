"""
Tests for state manager
"""

import pytest
from pathlib import Path
from forge.core.state_manager import StateManager, ProjectState, TaskState


@pytest.fixture
def state_manager(tmp_path):
    """Create temporary state manager"""
    db_path = tmp_path / "state.db"
    return StateManager(str(db_path))


def test_create_project(state_manager):
    """Test project creation"""
    project = state_manager.create_project(
        project_id="test-project",
        name="Test Project",
        description="A test project"
    )

    assert project.id == "test-project"
    assert project.name == "Test Project"
    assert project.stage == "planning"
    assert isinstance(project, ProjectState)


def test_get_project(state_manager):
    """Test getting project by ID"""
    # Create project
    state_manager.create_project(
        project_id="test-project",
        name="Test Project",
        description="A test project"
    )

    # Get project
    project = state_manager.get_project("test-project")

    assert project is not None
    assert project.id == "test-project"
    assert project.name == "Test Project"


def test_get_nonexistent_project(state_manager):
    """Test getting non-existent project"""
    project = state_manager.get_project("nonexistent")
    assert project is None


def test_update_project_stage(state_manager):
    """Test updating project stage"""
    # Create project
    state_manager.create_project(
        project_id="test-project",
        name="Test Project",
        description="A test project"
    )

    # Update stage
    state_manager.update_project_stage("test-project", "generation")

    # Verify update
    project = state_manager.get_project("test-project")
    assert project.stage == "generation"


def test_create_task(state_manager):
    """Test task creation"""
    # Create project first
    state_manager.create_project(
        project_id="test-project",
        name="Test Project",
        description="A test project"
    )

    # Create task
    task = TaskState(
        id="task-001",
        project_id="test-project",
        title="Test Task",
        status="pending",
        priority=1,
        dependencies=[],
        generated_files={},
        test_results=None,
        commits=[]
    )

    state_manager.create_task(task)

    # Verify task was created
    tasks = state_manager.get_project_tasks("test-project")
    assert len(tasks) == 1
    assert tasks[0].id == "task-001"
    assert tasks[0].title == "Test Task"


def test_update_task_status(state_manager):
    """Test updating task status"""
    # Create project and task
    state_manager.create_project(
        project_id="test-project",
        name="Test Project",
        description="A test project"
    )

    task = TaskState(
        id="task-001",
        project_id="test-project",
        title="Test Task",
        status="pending",
        priority=1,
        dependencies=[],
        generated_files={},
        test_results=None,
        commits=[]
    )
    state_manager.create_task(task)

    # Update status
    state_manager.update_task_status(
        task_id="task-001",
        status="complete",
        duration=120.5
    )

    # Verify update
    tasks = state_manager.get_project_tasks("test-project")
    assert tasks[0].status == "complete"
    assert tasks[0].duration_seconds == 120.5


def test_checkpoint(state_manager):
    """Test checkpoint creation"""
    # Create project
    state_manager.create_project(
        project_id="test-project",
        name="Test Project",
        description="A test project"
    )

    # Create checkpoint
    state_manager.checkpoint(
        project_id="test-project",
        stage="planning",
        state={"key": "value"},
        description="Test checkpoint"
    )

    # Get latest checkpoint
    checkpoint = state_manager.get_latest_checkpoint("test-project")

    assert checkpoint is not None
    assert checkpoint.project_id == "test-project"
    assert checkpoint.stage == "planning"
    assert checkpoint.description == "Test checkpoint"
    assert checkpoint.state_snapshot == {"key": "value"}


def test_save_test_results(state_manager):
    """Test saving test results"""
    # Create project and task
    state_manager.create_project(
        project_id="test-project",
        name="Test Project",
        description="A test project"
    )

    task = TaskState(
        id="task-001",
        project_id="test-project",
        title="Test Task",
        status="pending",
        priority=1,
        dependencies=[],
        generated_files={},
        test_results=None,
        commits=[]
    )
    state_manager.create_task(task)

    # Save test results
    state_manager.save_test_results(
        task_id="task-001",
        test_type="unit",
        passed=10,
        failed=2,
        coverage=85.5,
        duration=15.3
    )

    # Results are saved successfully (no error)


def test_context_manager(tmp_path):
    """Test state manager as context manager"""
    db_path = tmp_path / "state.db"

    with StateManager(str(db_path)) as state_manager:
        project = state_manager.create_project(
            project_id="test-project",
            name="Test Project",
            description="A test project"
        )
        assert project.id == "test-project"

    # Database should be closed after context
