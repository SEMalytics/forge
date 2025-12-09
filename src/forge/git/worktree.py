"""
Git Worktree Manager for Forge

Provides git worktree management for parallel task execution.
Each task can run in its own isolated worktree, enabling:
- Parallel code generation without conflicts
- Isolated testing per task
- Clean merge workflow
- Easy cleanup
"""

import subprocess
import shutil
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class WorktreeError(ForgeError):
    """Worktree operation errors"""
    pass


@dataclass
class WorktreeInfo:
    """Information about a git worktree"""
    path: Path
    branch: str
    head: str
    is_bare: bool = False
    is_detached: bool = False
    is_locked: bool = False
    lock_reason: Optional[str] = None
    prunable: bool = False

    @property
    def name(self) -> str:
        """Get worktree name from path"""
        return self.path.name

    @property
    def is_forge_worktree(self) -> bool:
        """Check if this is a forge-managed worktree"""
        return self.path.name.startswith("forge-") or "/forge-worktrees/" in str(self.path)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'path': str(self.path),
            'branch': self.branch,
            'head': self.head,
            'name': self.name,
            'is_bare': self.is_bare,
            'is_detached': self.is_detached,
            'is_locked': self.is_locked,
            'lock_reason': self.lock_reason,
            'prunable': self.prunable,
            'is_forge_worktree': self.is_forge_worktree
        }


@dataclass
class WorktreeTask:
    """A task assigned to a worktree"""
    task_id: str
    worktree: WorktreeInfo
    branch: str
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict] = None


class WorktreeManager:
    """
    Git worktree manager for parallel task execution.

    Features:
    - Create worktrees for parallel tasks
    - Track worktree-task assignments
    - Automatic cleanup of completed worktrees
    - Branch management per worktree
    - Merge workflow support
    """

    def __init__(
        self,
        repo_path: str = ".",
        worktree_base: Optional[Path] = None
    ):
        """
        Initialize worktree manager.

        Args:
            repo_path: Path to main git repository
            worktree_base: Base directory for worktrees (default: ../forge-worktrees)
        """
        self.repo_path = Path(repo_path).resolve()

        if not self._is_git_repo():
            raise WorktreeError(f"Not a git repository: {self.repo_path}")

        # Set worktree base directory
        if worktree_base:
            self.worktree_base = Path(worktree_base).resolve()
        else:
            # Default: sibling directory to repo
            self.worktree_base = self.repo_path.parent / "forge-worktrees"

        self._task_assignments: Dict[str, WorktreeTask] = {}

        logger.info(f"Initialized WorktreeManager for {self.repo_path}")
        logger.info(f"Worktree base: {self.worktree_base}")

    def _is_git_repo(self) -> bool:
        """Check if path is a git repository"""
        return (self.repo_path / ".git").exists() or (self.repo_path / ".git").is_file()

    def _run_git(
        self,
        command: List[str],
        cwd: Optional[Path] = None,
        check: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run git command.

        Args:
            command: Git command and arguments
            cwd: Working directory (default: repo_path)
            check: Raise exception on error

        Returns:
            CompletedProcess result
        """
        full_command = ["git"] + command

        try:
            result = subprocess.run(
                full_command,
                cwd=cwd or self.repo_path,
                check=check,
                capture_output=True,
                text=True
            )
            return result

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(full_command)}")
            logger.error(f"Error: {e.stderr}")
            raise WorktreeError(f"Git command failed: {e.stderr}")

    def list_worktrees(self) -> List[WorktreeInfo]:
        """
        List all worktrees for this repository.

        Returns:
            List of WorktreeInfo objects
        """
        result = self._run_git(["worktree", "list", "--porcelain"])
        worktrees = []
        current_worktree: Dict[str, Any] = {}

        for line in result.stdout.strip().split("\n"):
            if not line:
                if current_worktree:
                    worktrees.append(self._parse_worktree_info(current_worktree))
                    current_worktree = {}
                continue

            if line.startswith("worktree "):
                current_worktree['path'] = line[9:]
            elif line.startswith("HEAD "):
                current_worktree['head'] = line[5:]
            elif line.startswith("branch "):
                current_worktree['branch'] = line[7:]
            elif line == "bare":
                current_worktree['is_bare'] = True
            elif line == "detached":
                current_worktree['is_detached'] = True
            elif line.startswith("locked"):
                current_worktree['is_locked'] = True
                if " " in line:
                    current_worktree['lock_reason'] = line.split(" ", 1)[1]
            elif line == "prunable":
                current_worktree['prunable'] = True

        # Don't forget last worktree
        if current_worktree:
            worktrees.append(self._parse_worktree_info(current_worktree))

        return worktrees

    def _parse_worktree_info(self, data: Dict[str, Any]) -> WorktreeInfo:
        """Parse worktree data into WorktreeInfo"""
        return WorktreeInfo(
            path=Path(data.get('path', '')),
            branch=data.get('branch', '').replace('refs/heads/', ''),
            head=data.get('head', ''),
            is_bare=data.get('is_bare', False),
            is_detached=data.get('is_detached', False),
            is_locked=data.get('is_locked', False),
            lock_reason=data.get('lock_reason'),
            prunable=data.get('prunable', False)
        )

    def create_worktree(
        self,
        name: str,
        branch: Optional[str] = None,
        base_branch: str = "main",
        force: bool = False
    ) -> WorktreeInfo:
        """
        Create a new worktree.

        Args:
            name: Worktree name (will be prefixed with forge-)
            branch: Branch name (default: forge/{name})
            base_branch: Branch to base from
            force: Force creation even if branch exists

        Returns:
            WorktreeInfo for the new worktree
        """
        # Ensure worktree base exists
        self.worktree_base.mkdir(parents=True, exist_ok=True)

        # Generate names
        worktree_name = f"forge-{name}" if not name.startswith("forge-") else name
        worktree_path = self.worktree_base / worktree_name

        if branch is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            branch = f"forge/{name}-{timestamp}"

        # Check if worktree already exists
        if worktree_path.exists():
            if force:
                logger.warning(f"Removing existing worktree: {worktree_path}")
                self.remove_worktree(worktree_name, force=True)
            else:
                raise WorktreeError(f"Worktree already exists: {worktree_path}")

        # Check if branch exists
        branch_exists = self._branch_exists(branch)

        try:
            if branch_exists:
                # Use existing branch
                self._run_git([
                    "worktree", "add",
                    str(worktree_path),
                    branch
                ])
            else:
                # Create new branch from base
                self._run_git([
                    "worktree", "add",
                    "-b", branch,
                    str(worktree_path),
                    base_branch
                ])

            logger.info(f"Created worktree: {worktree_path} (branch: {branch})")

            # Return info about the new worktree
            return WorktreeInfo(
                path=worktree_path,
                branch=branch,
                head=self._get_head(worktree_path)
            )

        except WorktreeError as e:
            # Clean up on failure
            if worktree_path.exists():
                shutil.rmtree(worktree_path)
            raise

    def create_worktrees_for_tasks(
        self,
        task_ids: List[str],
        base_branch: str = "main"
    ) -> Dict[str, WorktreeInfo]:
        """
        Create worktrees for multiple tasks.

        Args:
            task_ids: List of task identifiers
            base_branch: Base branch for all worktrees

        Returns:
            Dictionary mapping task_id to WorktreeInfo
        """
        worktrees = {}

        for task_id in task_ids:
            try:
                worktree = self.create_worktree(
                    name=task_id,
                    base_branch=base_branch
                )
                worktrees[task_id] = worktree

                # Track assignment
                self._task_assignments[task_id] = WorktreeTask(
                    task_id=task_id,
                    worktree=worktree,
                    branch=worktree.branch
                )

            except WorktreeError as e:
                logger.error(f"Failed to create worktree for {task_id}: {e}")
                # Continue with other tasks
                continue

        logger.info(f"Created {len(worktrees)} worktrees for tasks")
        return worktrees

    def remove_worktree(
        self,
        name: str,
        force: bool = False
    ):
        """
        Remove a worktree.

        Args:
            name: Worktree name
            force: Force removal even if dirty
        """
        worktree_name = f"forge-{name}" if not name.startswith("forge-") else name
        worktree_path = self.worktree_base / worktree_name

        args = ["worktree", "remove"]
        if force:
            args.append("--force")
        args.append(str(worktree_path))

        try:
            self._run_git(args)
            logger.info(f"Removed worktree: {worktree_path}")

            # Clean up task assignment
            for task_id, task in list(self._task_assignments.items()):
                if task.worktree.path == worktree_path:
                    del self._task_assignments[task_id]

        except WorktreeError:
            # Try manual removal if git command fails
            if worktree_path.exists():
                shutil.rmtree(worktree_path)
                logger.info(f"Manually removed worktree directory: {worktree_path}")

    def clean_worktrees(
        self,
        completed_only: bool = True,
        delete_branches: bool = False
    ) -> int:
        """
        Clean up forge worktrees.

        Args:
            completed_only: Only remove completed/merged worktrees
            delete_branches: Also delete associated branches

        Returns:
            Number of worktrees removed
        """
        worktrees = self.list_worktrees()
        removed = 0

        for wt in worktrees:
            if not wt.is_forge_worktree:
                continue

            # Skip main worktree
            if wt.path == self.repo_path:
                continue

            should_remove = False

            if completed_only:
                # Check if branch is merged
                if self._is_branch_merged(wt.branch):
                    should_remove = True
                # Check if worktree is prunable
                elif wt.prunable:
                    should_remove = True
            else:
                should_remove = True

            if should_remove:
                try:
                    # Get branch before removing worktree
                    branch = wt.branch

                    # Remove worktree
                    self.remove_worktree(wt.name, force=True)
                    removed += 1

                    # Optionally delete branch
                    if delete_branches and branch:
                        self._delete_branch(branch)

                except Exception as e:
                    logger.warning(f"Failed to remove worktree {wt.name}: {e}")

        # Prune worktree list
        self._run_git(["worktree", "prune"])

        logger.info(f"Cleaned {removed} worktrees")
        return removed

    def get_worktree(self, name: str) -> Optional[WorktreeInfo]:
        """
        Get worktree by name.

        Args:
            name: Worktree name

        Returns:
            WorktreeInfo or None
        """
        worktree_name = f"forge-{name}" if not name.startswith("forge-") else name
        worktree_path = self.worktree_base / worktree_name

        for wt in self.list_worktrees():
            if wt.path == worktree_path:
                return wt

        return None

    def get_worktree_for_task(self, task_id: str) -> Optional[WorktreeInfo]:
        """
        Get worktree assigned to a task.

        Args:
            task_id: Task identifier

        Returns:
            WorktreeInfo or None
        """
        if task_id in self._task_assignments:
            return self._task_assignments[task_id].worktree
        return None

    def lock_worktree(self, name: str, reason: Optional[str] = None):
        """
        Lock a worktree to prevent removal.

        Args:
            name: Worktree name
            reason: Lock reason
        """
        worktree_name = f"forge-{name}" if not name.startswith("forge-") else name
        worktree_path = self.worktree_base / worktree_name

        args = ["worktree", "lock"]
        if reason:
            args.extend(["--reason", reason])
        args.append(str(worktree_path))

        self._run_git(args)
        logger.info(f"Locked worktree: {worktree_path}")

    def unlock_worktree(self, name: str):
        """
        Unlock a worktree.

        Args:
            name: Worktree name
        """
        worktree_name = f"forge-{name}" if not name.startswith("forge-") else name
        worktree_path = self.worktree_base / worktree_name

        self._run_git(["worktree", "unlock", str(worktree_path)])
        logger.info(f"Unlocked worktree: {worktree_path}")

    def move_worktree(self, name: str, new_path: Path):
        """
        Move a worktree to a new location.

        Args:
            name: Worktree name
            new_path: New path for worktree
        """
        worktree_name = f"forge-{name}" if not name.startswith("forge-") else name
        worktree_path = self.worktree_base / worktree_name

        self._run_git([
            "worktree", "move",
            str(worktree_path),
            str(new_path)
        ])
        logger.info(f"Moved worktree to: {new_path}")

    def run_in_worktree(
        self,
        name: str,
        command: List[str]
    ) -> subprocess.CompletedProcess:
        """
        Run a command in a worktree.

        Args:
            name: Worktree name
            command: Command to run

        Returns:
            CompletedProcess result
        """
        worktree_name = f"forge-{name}" if not name.startswith("forge-") else name
        worktree_path = self.worktree_base / worktree_name

        if not worktree_path.exists():
            raise WorktreeError(f"Worktree not found: {worktree_path}")

        result = subprocess.run(
            command,
            cwd=worktree_path,
            capture_output=True,
            text=True
        )

        return result

    def commit_in_worktree(
        self,
        name: str,
        message: str,
        files: Optional[List[str]] = None
    ) -> str:
        """
        Create a commit in a worktree.

        Args:
            name: Worktree name
            message: Commit message
            files: Files to add (default: all changes)

        Returns:
            Commit SHA
        """
        worktree_name = f"forge-{name}" if not name.startswith("forge-") else name
        worktree_path = self.worktree_base / worktree_name

        # Add files
        if files:
            self._run_git(["add"] + files, cwd=worktree_path)
        else:
            self._run_git(["add", "-A"], cwd=worktree_path)

        # Commit
        self._run_git(["commit", "-m", message], cwd=worktree_path)

        # Get SHA
        result = self._run_git(["rev-parse", "HEAD"], cwd=worktree_path)
        sha = result.stdout.strip()

        logger.info(f"Created commit in {name}: {sha[:8]}")
        return sha

    def merge_worktree(
        self,
        name: str,
        target_branch: str = "main",
        delete_after: bool = True
    ) -> bool:
        """
        Merge worktree branch into target branch.

        Args:
            name: Worktree name
            target_branch: Branch to merge into
            delete_after: Delete worktree after merge

        Returns:
            True if merge successful
        """
        worktree = self.get_worktree(name)
        if not worktree:
            raise WorktreeError(f"Worktree not found: {name}")

        branch = worktree.branch

        # Switch to target branch in main repo
        self._run_git(["checkout", target_branch])

        try:
            # Merge
            self._run_git([
                "merge", "--no-ff",
                "-m", f"Merge {branch} into {target_branch}",
                branch
            ])

            logger.info(f"Merged {branch} into {target_branch}")

            # Clean up
            if delete_after:
                self.remove_worktree(name, force=True)
                self._delete_branch(branch)

            return True

        except WorktreeError as e:
            logger.error(f"Merge failed: {e}")
            return False

    def get_forge_worktrees(self) -> List[WorktreeInfo]:
        """Get only forge-managed worktrees"""
        return [wt for wt in self.list_worktrees() if wt.is_forge_worktree]

    def _branch_exists(self, branch: str) -> bool:
        """Check if branch exists"""
        result = self._run_git(
            ["rev-parse", "--verify", f"refs/heads/{branch}"],
            check=False
        )
        return result.returncode == 0

    def _is_branch_merged(self, branch: str, target: str = "main") -> bool:
        """Check if branch is merged into target"""
        result = self._run_git(
            ["branch", "--merged", target],
            check=False
        )
        merged_branches = result.stdout.strip().split("\n")
        return any(branch in b for b in merged_branches)

    def _delete_branch(self, branch: str, force: bool = False):
        """Delete a branch"""
        flag = "-D" if force else "-d"
        try:
            self._run_git(["branch", flag, branch])
            logger.info(f"Deleted branch: {branch}")
        except WorktreeError:
            logger.warning(f"Could not delete branch: {branch}")

    def _get_head(self, worktree_path: Path) -> str:
        """Get HEAD commit for a worktree"""
        result = self._run_git(["rev-parse", "HEAD"], cwd=worktree_path)
        return result.stdout.strip()

    def get_task_assignments(self) -> Dict[str, WorktreeTask]:
        """Get current task-worktree assignments"""
        return self._task_assignments.copy()

    def mark_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict] = None
    ):
        """
        Update task status.

        Args:
            task_id: Task identifier
            status: New status
            result: Task result data
        """
        if task_id not in self._task_assignments:
            logger.warning(f"Task not found in assignments: {task_id}")
            return

        task = self._task_assignments[task_id]
        task.status = status

        if status == "running" and not task.started_at:
            task.started_at = datetime.now().isoformat()
        elif status in ("completed", "failed"):
            task.completed_at = datetime.now().isoformat()

        if result:
            task.result = result

        logger.debug(f"Task {task_id} status: {status}")
