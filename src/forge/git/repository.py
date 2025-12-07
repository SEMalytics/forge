"""
Git repository operations

Provides comprehensive Git integration:
- Branch management with forge/* naming
- Conventional commits
- Conflict detection
- Push operations with safety checks
"""

import os
import subprocess
import re
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class GitError(ForgeError):
    """Git operation errors"""
    pass


@dataclass
class GitStatus:
    """Current repository status"""
    branch: str
    is_clean: bool
    staged_files: List[str]
    unstaged_files: List[str]
    untracked_files: List[str]
    ahead: int
    behind: int
    has_conflicts: bool


@dataclass
class CommitInfo:
    """Commit information"""
    sha: str
    message: str
    author: str
    date: str
    files_changed: int


class ForgeRepository:
    """
    Git repository manager for Forge.

    Features:
    - Branch management with forge/* naming convention
    - Conventional commits with issue linking
    - Conflict detection and resolution
    - Safe push operations
    - Commit squashing
    """

    def __init__(self, repo_path: str = "."):
        """
        Initialize repository.

        Args:
            repo_path: Path to git repository
        """
        self.repo_path = Path(repo_path).resolve()

        if not self._is_git_repo():
            raise GitError(f"Not a git repository: {self.repo_path}")

        logger.info(f"Initialized ForgeRepository at {self.repo_path}")

    def _is_git_repo(self) -> bool:
        """Check if path is a git repository"""
        return (self.repo_path / ".git").exists()

    def _run_git(
        self,
        command: List[str],
        check: bool = True,
        capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run git command.

        Args:
            command: Git command and arguments
            check: Raise exception on error
            capture_output: Capture stdout/stderr

        Returns:
            CompletedProcess result
        """
        full_command = ["git"] + command

        try:
            result = subprocess.run(
                full_command,
                cwd=self.repo_path,
                check=check,
                capture_output=capture_output,
                text=True
            )
            return result

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(full_command)}")
            logger.error(f"Error: {e.stderr}")
            raise GitError(f"Git command failed: {e.stderr}")

    def get_current_branch(self) -> str:
        """Get current branch name"""
        result = self._run_git(["branch", "--show-current"])
        return result.stdout.strip()

    def get_status(self) -> GitStatus:
        """
        Get repository status.

        Returns:
            GitStatus with detailed repository state
        """
        # Get current branch
        branch = self.get_current_branch()

        # Get status
        result = self._run_git(["status", "--porcelain"])
        status_lines = result.stdout.strip().split("\n") if result.stdout.strip() else []

        staged = []
        unstaged = []
        untracked = []

        for line in status_lines:
            if not line:
                continue

            status_code = line[:2]
            file_path = line[3:]

            if status_code[0] in ['M', 'A', 'D', 'R', 'C']:
                staged.append(file_path)
            if status_code[1] in ['M', 'D']:
                unstaged.append(file_path)
            if status_code == '??':
                untracked.append(file_path)

        # Get ahead/behind info
        ahead = 0
        behind = 0
        try:
            result = self._run_git(["rev-list", "--count", "--left-right", f"@{{u}}...HEAD"])
            parts = result.stdout.strip().split("\t")
            if len(parts) == 2:
                behind = int(parts[0])
                ahead = int(parts[1])
        except (GitError, ValueError):
            pass

        # Check for conflicts
        has_conflicts = any("UU" in line for line in status_lines)

        return GitStatus(
            branch=branch,
            is_clean=len(status_lines) == 0,
            staged_files=staged,
            unstaged_files=unstaged,
            untracked_files=untracked,
            ahead=ahead,
            behind=behind,
            has_conflicts=has_conflicts
        )

    def create_feature_branch(self, name: str, base: str = "main") -> str:
        """
        Create forge feature branch.

        Args:
            name: Feature name (will be prefixed with forge/)
            base: Base branch to branch from

        Returns:
            Full branch name
        """
        # Generate branch name: forge/{name}-{timestamp}
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"forge/{name}-{timestamp}"

        # Ensure base branch exists
        try:
            self._run_git(["rev-parse", "--verify", base])
        except GitError:
            logger.warning(f"Base branch {base} not found, using current branch")
            base = self.get_current_branch()

        # Create and checkout branch
        self._run_git(["checkout", "-b", branch_name, base])

        logger.info(f"Created feature branch: {branch_name}")
        return branch_name

    def checkout(self, branch: str, create: bool = False):
        """
        Checkout branch.

        Args:
            branch: Branch name
            create: Create branch if it doesn't exist
        """
        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(branch)

        self._run_git(args)
        logger.info(f"Checked out branch: {branch}")

    def add_files(self, files: List[str]):
        """
        Add files to staging area.

        Args:
            files: List of file paths to add
        """
        if not files:
            return

        self._run_git(["add"] + files)
        logger.debug(f"Added {len(files)} files to staging area")

    def commit(
        self,
        message: str,
        author: Optional[str] = None,
        sign: bool = False
    ) -> str:
        """
        Create commit.

        Args:
            message: Commit message
            author: Optional author override
            sign: Sign commit with GPG

        Returns:
            Commit SHA
        """
        args = ["commit", "-m", message]

        if author:
            args.extend(["--author", author])

        if sign:
            args.append("-S")

        self._run_git(args)

        # Get commit SHA
        result = self._run_git(["rev-parse", "HEAD"])
        sha = result.stdout.strip()

        logger.info(f"Created commit: {sha[:8]} - {message.split(chr(10))[0]}")
        return sha

    def push(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
        set_upstream: bool = False
    ):
        """
        Push commits to remote.

        Args:
            remote: Remote name
            branch: Branch to push (defaults to current)
            force: Force push
            set_upstream: Set upstream tracking
        """
        if branch is None:
            branch = self.get_current_branch()

        args = ["push"]

        if set_upstream:
            args.extend(["-u"])

        if force:
            logger.warning(f"Force pushing to {remote}/{branch}")
            args.append("--force-with-lease")

        args.extend([remote, branch])

        self._run_git(args)
        logger.info(f"Pushed {branch} to {remote}")

    def pull(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        rebase: bool = False
    ):
        """
        Pull changes from remote.

        Args:
            remote: Remote name
            branch: Branch to pull (defaults to current)
            rebase: Use rebase instead of merge
        """
        if branch is None:
            branch = self.get_current_branch()

        args = ["pull"]

        if rebase:
            args.append("--rebase")

        args.extend([remote, branch])

        self._run_git(args)
        logger.info(f"Pulled {branch} from {remote}")

    def detect_conflicts(self) -> List[str]:
        """
        Detect conflicted files.

        Returns:
            List of files with conflicts
        """
        result = self._run_git(["diff", "--name-only", "--diff-filter=U"])
        conflicted = result.stdout.strip().split("\n") if result.stdout.strip() else []

        if conflicted:
            logger.warning(f"Detected {len(conflicted)} conflicted files")

        return conflicted

    def squash_commits(
        self,
        count: int,
        message: str
    ) -> str:
        """
        Squash last N commits.

        Args:
            count: Number of commits to squash
            message: New commit message

        Returns:
            New commit SHA
        """
        # Reset soft to keep changes
        self._run_git(["reset", "--soft", f"HEAD~{count}"])

        # Create new commit
        sha = self.commit(message)

        logger.info(f"Squashed {count} commits into {sha[:8]}")
        return sha

    def get_commit_history(
        self,
        count: int = 10,
        branch: Optional[str] = None
    ) -> List[CommitInfo]:
        """
        Get commit history.

        Args:
            count: Number of commits to retrieve
            branch: Branch to get history from (defaults to current)

        Returns:
            List of CommitInfo objects
        """
        args = [
            "log",
            f"-{count}",
            "--pretty=format:%H|%s|%an|%ai|%N"
        ]

        if branch:
            args.append(branch)

        result = self._run_git(args)
        commits = []

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|")
            if len(parts) >= 4:
                # Get files changed
                files_result = self._run_git(
                    ["show", "--stat", "--oneline", parts[0]],
                    check=False
                )
                files_changed = len(
                    [l for l in files_result.stdout.split("\n")
                     if "|" in l]
                )

                commits.append(CommitInfo(
                    sha=parts[0],
                    message=parts[1],
                    author=parts[2],
                    date=parts[3],
                    files_changed=files_changed
                ))

        return commits

    def get_changed_files(
        self,
        from_ref: str = "HEAD",
        to_ref: Optional[str] = None
    ) -> List[str]:
        """
        Get changed files between refs.

        Args:
            from_ref: Starting ref
            to_ref: Ending ref (defaults to working tree)

        Returns:
            List of changed file paths
        """
        args = ["diff", "--name-only", from_ref]

        if to_ref:
            args.append(to_ref)

        result = self._run_git(args)
        files = result.stdout.strip().split("\n") if result.stdout.strip() else []

        return files

    def get_file_diff(self, file_path: str) -> str:
        """
        Get diff for specific file.

        Args:
            file_path: Path to file

        Returns:
            Diff output
        """
        result = self._run_git(["diff", file_path])
        return result.stdout

    def stash(self, message: Optional[str] = None) -> bool:
        """
        Stash current changes.

        Args:
            message: Optional stash message

        Returns:
            True if stashed, False if nothing to stash
        """
        args = ["stash", "push"]

        if message:
            args.extend(["-m", message])

        result = self._run_git(args)

        if "No local changes" in result.stdout:
            return False

        logger.info("Stashed changes")
        return True

    def stash_pop(self):
        """Pop most recent stash"""
        self._run_git(["stash", "pop"])
        logger.info("Popped stash")

    def get_remote_url(self, remote: str = "origin") -> str:
        """
        Get remote URL.

        Args:
            remote: Remote name

        Returns:
            Remote URL
        """
        result = self._run_git(["remote", "get-url", remote])
        return result.stdout.strip()

    def parse_github_repo(self) -> Optional[Tuple[str, str]]:
        """
        Parse GitHub owner/repo from remote URL.

        Returns:
            (owner, repo) tuple or None
        """
        try:
            url = self.get_remote_url()

            # Parse various GitHub URL formats
            patterns = [
                r'github\.com[:/]([^/]+)/([^/\.]+)',
                r'github\.com/([^/]+)/([^/]+)\.git'
            ]

            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return (match.group(1), match.group(2))

            return None

        except GitError:
            return None

    def get_branch_list(
        self,
        remote: bool = False,
        merged: bool = False
    ) -> List[str]:
        """
        Get list of branches.

        Args:
            remote: List remote branches
            merged: Only show merged branches

        Returns:
            List of branch names
        """
        args = ["branch"]

        if remote:
            args.append("-r")

        if merged:
            args.append("--merged")

        result = self._run_git(args)

        branches = []
        for line in result.stdout.strip().split("\n"):
            # Remove leading * and whitespace
            branch = line.strip().lstrip("* ")
            if branch and "->" not in branch:  # Skip HEAD -> main pointers
                branches.append(branch)

        return branches

    def delete_branch(
        self,
        branch: str,
        force: bool = False,
        remote: bool = False
    ):
        """
        Delete branch.

        Args:
            branch: Branch name
            force: Force deletion
            remote: Delete remote branch
        """
        if remote:
            self._run_git(["push", "origin", "--delete", branch])
            logger.info(f"Deleted remote branch: {branch}")
        else:
            flag = "-D" if force else "-d"
            self._run_git(["branch", flag, branch])
            logger.info(f"Deleted local branch: {branch}")

    def merge(
        self,
        branch: str,
        no_ff: bool = True,
        message: Optional[str] = None
    ):
        """
        Merge branch.

        Args:
            branch: Branch to merge
            no_ff: No fast-forward
            message: Merge commit message
        """
        args = ["merge"]

        if no_ff:
            args.append("--no-ff")

        if message:
            args.extend(["-m", message])

        args.append(branch)

        self._run_git(args)
        logger.info(f"Merged {branch}")

    def tag(
        self,
        name: str,
        message: Optional[str] = None,
        sign: bool = False
    ):
        """
        Create tag.

        Args:
            name: Tag name
            message: Tag message
            sign: Sign tag with GPG
        """
        args = ["tag"]

        if message:
            args.extend(["-a", name, "-m", message])
        else:
            args.append(name)

        if sign:
            args.append("-s")

        self._run_git(args)
        logger.info(f"Created tag: {name}")

    def get_tags(self) -> List[str]:
        """Get list of tags"""
        result = self._run_git(["tag", "-l"])
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
