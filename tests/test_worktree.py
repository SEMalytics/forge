"""
Tests for Git Worktree Manager

Tests the worktree management functionality including:
- Worktree creation and removal
- Listing and status
- Branch management
- Task assignment tracking
- Cleanup operations
"""

import pytest
from pathlib import Path
import subprocess
import shutil
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from forge.git.worktree import (
    WorktreeManager,
    WorktreeInfo,
    WorktreeTask,
    WorktreeError
)


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_dir, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir, check=True, capture_output=True
    )

    # Create initial commit
    (repo_dir / "README.md").write_text("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir, check=True, capture_output=True
    )

    # Create main branch reference
    subprocess.run(
        ["git", "branch", "-M", "main"],
        cwd=repo_dir, check=True, capture_output=True
    )

    return repo_dir


@pytest.fixture
def worktree_base(tmp_path):
    """Create temporary worktree base directory."""
    wt_base = tmp_path / "forge-worktrees"
    wt_base.mkdir()
    return wt_base


@pytest.fixture
def manager(temp_git_repo, worktree_base):
    """Create WorktreeManager for testing."""
    return WorktreeManager(
        repo_path=str(temp_git_repo),
        worktree_base=worktree_base
    )


class TestWorktreeInfo:
    """Tests for WorktreeInfo dataclass."""

    def test_name_property(self):
        """Test name extraction from path."""
        info = WorktreeInfo(
            path=Path("/tmp/forge-worktrees/forge-task-001"),
            branch="forge/task-001",
            head="abc123"
        )
        assert info.name == "forge-task-001"

    def test_is_forge_worktree_with_prefix(self):
        """Test forge worktree detection with prefix."""
        info = WorktreeInfo(
            path=Path("/tmp/forge-task-001"),
            branch="forge/task-001",
            head="abc123"
        )
        assert info.is_forge_worktree is True

    def test_is_forge_worktree_with_path(self):
        """Test forge worktree detection with path."""
        info = WorktreeInfo(
            path=Path("/tmp/forge-worktrees/my-task"),
            branch="feature/my-task",
            head="abc123"
        )
        assert info.is_forge_worktree is True

    def test_is_not_forge_worktree(self):
        """Test non-forge worktree detection."""
        info = WorktreeInfo(
            path=Path("/home/user/project"),
            branch="main",
            head="abc123"
        )
        assert info.is_forge_worktree is False

    def test_to_dict(self):
        """Test serialization to dictionary."""
        info = WorktreeInfo(
            path=Path("/tmp/forge-task-001"),
            branch="forge/task-001",
            head="abc123",
            is_locked=True,
            lock_reason="In use"
        )
        data = info.to_dict()

        assert data['path'] == "/tmp/forge-task-001"
        assert data['branch'] == "forge/task-001"
        assert data['head'] == "abc123"
        assert data['is_locked'] is True
        assert data['lock_reason'] == "In use"
        assert data['is_forge_worktree'] is True


class TestWorktreeManager:
    """Tests for WorktreeManager class."""

    def test_initialization(self, manager, temp_git_repo, worktree_base):
        """Test manager initialization."""
        assert manager.repo_path == temp_git_repo
        assert manager.worktree_base == worktree_base

    def test_initialization_not_git_repo(self, tmp_path, worktree_base):
        """Test initialization fails for non-git directory."""
        non_git = tmp_path / "not-a-repo"
        non_git.mkdir()

        with pytest.raises(WorktreeError, match="Not a git repository"):
            WorktreeManager(repo_path=str(non_git))

    def test_list_worktrees(self, manager, temp_git_repo):
        """Test listing worktrees."""
        worktrees = manager.list_worktrees()

        # Should have at least the main worktree
        assert len(worktrees) >= 1

        # Main worktree should be listed
        main_wt = [wt for wt in worktrees if wt.path == temp_git_repo]
        assert len(main_wt) == 1
        assert main_wt[0].branch == "main"

    def test_create_worktree(self, manager, worktree_base):
        """Test creating a worktree."""
        wt = manager.create_worktree(name="test-task")

        assert wt.path.exists()
        assert wt.path.name == "forge-test-task"
        assert "forge/test-task" in wt.branch
        assert wt.path.parent == worktree_base

        # Verify it's a valid git worktree
        git_file = wt.path / ".git"
        assert git_file.exists()

    def test_create_worktree_with_custom_branch(self, manager):
        """Test creating worktree with custom branch name."""
        wt = manager.create_worktree(
            name="feature",
            branch="custom/feature-branch"
        )

        assert wt.branch == "custom/feature-branch"

    def test_create_worktree_force_existing(self, manager):
        """Test force creating worktree over existing one."""
        # Create first worktree
        manager.create_worktree(name="duplicate")

        # Should fail without force
        with pytest.raises(WorktreeError, match="already exists"):
            manager.create_worktree(name="duplicate")

        # Should succeed with force
        wt = manager.create_worktree(name="duplicate", force=True)
        assert wt.path.exists()

    def test_create_worktrees_for_tasks(self, manager):
        """Test creating multiple worktrees for tasks."""
        task_ids = ["task-001", "task-002", "task-003"]
        worktrees = manager.create_worktrees_for_tasks(task_ids)

        assert len(worktrees) == 3
        assert all(task_id in worktrees for task_id in task_ids)

        for task_id, wt in worktrees.items():
            assert wt.path.exists()
            assert task_id in wt.path.name

    def test_remove_worktree(self, manager):
        """Test removing a worktree."""
        wt = manager.create_worktree(name="to-remove")
        assert wt.path.exists()

        manager.remove_worktree("to-remove")
        assert not wt.path.exists()

    def test_get_worktree(self, manager):
        """Test getting worktree by name."""
        created = manager.create_worktree(name="findme")

        found = manager.get_worktree("findme")
        assert found is not None
        assert found.path == created.path

        not_found = manager.get_worktree("doesnt-exist")
        assert not_found is None

    def test_get_forge_worktrees(self, manager):
        """Test getting only forge-managed worktrees."""
        # Create some forge worktrees
        manager.create_worktree(name="forge-task-1")
        manager.create_worktree(name="forge-task-2")

        forge_wts = manager.get_forge_worktrees()

        # Should only include forge worktrees, not main repo
        for wt in forge_wts:
            assert wt.is_forge_worktree


class TestWorktreeOperations:
    """Tests for worktree operations."""

    def test_run_in_worktree(self, manager):
        """Test running command in worktree."""
        wt = manager.create_worktree(name="run-test")

        result = manager.run_in_worktree("run-test", ["pwd"])
        assert str(wt.path) in result.stdout

    def test_commit_in_worktree(self, manager):
        """Test committing in worktree."""
        wt = manager.create_worktree(name="commit-test")

        # Create a file in worktree
        test_file = wt.path / "new-file.txt"
        test_file.write_text("Test content")

        # Commit
        sha = manager.commit_in_worktree(
            name="commit-test",
            message="Add test file"
        )

        assert sha is not None
        assert len(sha) == 40  # Full SHA

    def test_lock_unlock_worktree(self, manager):
        """Test locking and unlocking worktree."""
        wt = manager.create_worktree(name="lock-test")

        # Lock
        manager.lock_worktree("lock-test", reason="Testing")

        # Verify locked
        wt_info = manager.get_worktree("lock-test")
        assert wt_info.is_locked is True

        # Unlock
        manager.unlock_worktree("lock-test")

        wt_info = manager.get_worktree("lock-test")
        assert wt_info.is_locked is False


class TestTaskAssignment:
    """Tests for task-worktree assignment tracking."""

    def test_task_assignment_tracking(self, manager):
        """Test that task assignments are tracked."""
        task_ids = ["task-a", "task-b"]
        worktrees = manager.create_worktrees_for_tasks(task_ids)

        assignments = manager.get_task_assignments()

        assert "task-a" in assignments
        assert "task-b" in assignments
        assert assignments["task-a"].worktree.path == worktrees["task-a"].path

    def test_get_worktree_for_task(self, manager):
        """Test getting worktree for specific task."""
        manager.create_worktrees_for_tasks(["my-task"])

        wt = manager.get_worktree_for_task("my-task")
        assert wt is not None
        assert "my-task" in wt.path.name

        wt_none = manager.get_worktree_for_task("unknown-task")
        assert wt_none is None

    def test_mark_task_status(self, manager):
        """Test updating task status."""
        manager.create_worktrees_for_tasks(["status-task"])

        manager.mark_task_status("status-task", "running")
        assert manager._task_assignments["status-task"].status == "running"
        assert manager._task_assignments["status-task"].started_at is not None

        manager.mark_task_status("status-task", "completed", result={"success": True})
        assert manager._task_assignments["status-task"].status == "completed"
        assert manager._task_assignments["status-task"].completed_at is not None
        assert manager._task_assignments["status-task"].result == {"success": True}


class TestCleanup:
    """Tests for worktree cleanup operations."""

    def test_clean_worktrees_all(self, manager):
        """Test cleaning all forge worktrees."""
        # Create some worktrees
        manager.create_worktree(name="clean-1")
        manager.create_worktree(name="clean-2")

        # Clean all
        removed = manager.clean_worktrees(completed_only=False)

        assert removed == 2

        # Verify they're gone
        forge_wts = manager.get_forge_worktrees()
        assert len(forge_wts) == 0

    def test_clean_assignment_on_remove(self, manager):
        """Test that task assignment is cleaned on removal."""
        manager.create_worktrees_for_tasks(["assigned-task"])
        assert "assigned-task" in manager.get_task_assignments()

        manager.remove_worktree("assigned-task", force=True)

        # Assignment should be cleaned up
        assert "assigned-task" not in manager.get_task_assignments()


class TestBranchOperations:
    """Tests for branch-related operations."""

    def test_branch_exists(self, manager, temp_git_repo):
        """Test branch existence check."""
        assert manager._branch_exists("main") is True
        assert manager._branch_exists("nonexistent-branch") is False

    def test_is_branch_merged(self, manager, temp_git_repo):
        """Test checking if branch is merged."""
        # main is merged into itself
        assert manager._is_branch_merged("main", "main") is True

    def test_delete_branch(self, manager, temp_git_repo):
        """Test branch deletion."""
        # Create a branch
        subprocess.run(
            ["git", "branch", "to-delete"],
            cwd=temp_git_repo, check=True, capture_output=True
        )

        assert manager._branch_exists("to-delete") is True

        manager._delete_branch("to-delete")

        assert manager._branch_exists("to-delete") is False


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_create_worktree_invalid_base_branch(self, manager):
        """Test creating worktree with invalid base branch."""
        with pytest.raises(WorktreeError):
            manager.create_worktree(
                name="invalid",
                base_branch="nonexistent-branch"
            )

    def test_remove_nonexistent_worktree(self, manager):
        """Test removing worktree that doesn't exist."""
        # Should not raise, just log warning
        manager.remove_worktree("doesnt-exist", force=True)

    def test_run_in_nonexistent_worktree(self, manager):
        """Test running command in nonexistent worktree."""
        with pytest.raises(WorktreeError, match="not found"):
            manager.run_in_worktree("doesnt-exist", ["pwd"])

    def test_worktree_name_normalization(self, manager):
        """Test that worktree names are normalized."""
        # Without forge- prefix
        wt1 = manager.create_worktree(name="task")
        assert wt1.path.name == "forge-task"

        # With forge- prefix already
        wt2 = manager.create_worktree(name="forge-another")
        assert wt2.path.name == "forge-another"

    def test_concurrent_worktree_creation(self, manager):
        """Test creating many worktrees."""
        task_ids = [f"concurrent-{i}" for i in range(5)]
        worktrees = manager.create_worktrees_for_tasks(task_ids)

        assert len(worktrees) == 5
        for task_id in task_ids:
            assert task_id in worktrees
            assert worktrees[task_id].path.exists()


class TestWorktreeTask:
    """Tests for WorktreeTask dataclass."""

    def test_worktree_task_creation(self):
        """Test creating WorktreeTask."""
        wt_info = WorktreeInfo(
            path=Path("/tmp/forge-task"),
            branch="forge/task",
            head="abc123"
        )

        task = WorktreeTask(
            task_id="test-task",
            worktree=wt_info,
            branch="forge/task"
        )

        assert task.task_id == "test-task"
        assert task.status == "pending"
        assert task.worktree == wt_info
        assert task.started_at is None
        assert task.completed_at is None
