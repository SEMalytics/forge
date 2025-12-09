"""
Git integration for Forge

Provides Git operations, branch management, PR creation, and worktree management.
"""

from forge.git.repository import ForgeRepository
from forge.git.commits import CommitStrategy, ConventionalCommit
from forge.git.worktree import WorktreeManager, WorktreeInfo, WorktreeError

__all__ = [
    'ForgeRepository',
    'CommitStrategy',
    'ConventionalCommit',
    'WorktreeManager',
    'WorktreeInfo',
    'WorktreeError',
]
