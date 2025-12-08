"""
Git utility functions for repository detection and management.
"""

import re
from pathlib import Path
from typing import Optional, Tuple
import subprocess


def get_git_remote_url(directory: Path = Path.cwd(), remote: str = "origin") -> Optional[str]:
    """
    Get the git remote URL for the current directory.

    Args:
        directory: Directory to check (defaults to current working directory)
        remote: Remote name to check (defaults to "origin")

    Returns:
        Remote URL or None if not a git repo
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", remote],
            cwd=directory,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        return None


def get_all_git_remotes(directory: Path = Path.cwd()) -> dict[str, str]:
    """
    Get all git remotes for the current directory.

    Args:
        directory: Directory to check (defaults to current working directory)

    Returns:
        Dictionary mapping remote names to URLs
    """
    remotes = {}
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=directory,
            capture_output=True,
            text=True,
            check=True
        )

        # Parse output: "origin  git@github.com:user/repo.git (fetch)"
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    remote_name = parts[0]
                    remote_url = parts[1]
                    # Only keep fetch URLs (skip push duplicates)
                    if "(fetch)" in line:
                        remotes[remote_name] = remote_url

        return remotes
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}


def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Parse GitHub URL to extract owner and repo name.

    Handles both HTTPS and SSH URLs:
    - https://github.com/owner/repo.git
    - git@github.com:owner/repo.git

    Args:
        url: Git remote URL

    Returns:
        Tuple of (owner, repo_name) or None if not a GitHub URL
    """
    if not url:
        return None

    # HTTPS format: https://github.com/owner/repo.git
    https_match = re.match(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
    if https_match:
        return https_match.group(1), https_match.group(2)

    # SSH format: git@github.com:owner/repo.git
    ssh_match = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", url)
    if ssh_match:
        return ssh_match.group(1), ssh_match.group(2)

    return None


def get_preferred_remote(directory: Path = Path.cwd()) -> Optional[str]:
    """
    Get the preferred git remote for CodeGen integration.

    Priority:
    1. 'internexio' remote (for personal CodeGen accounts)
    2. 'origin' remote (fallback)

    Args:
        directory: Directory to check (defaults to current working directory)

    Returns:
        Remote name or None
    """
    remotes = get_all_git_remotes(directory)

    # Prefer internexio for personal CodeGen accounts
    if "internexio" in remotes:
        return "internexio"

    # Fall back to origin
    if "origin" in remotes:
        return "origin"

    return None


def get_github_repo_info(directory: Path = Path.cwd()) -> Optional[Tuple[str, str]]:
    """
    Get GitHub repository owner and name for the current directory.

    Uses preferred remote (internexio > origin) for CodeGen integration.

    Args:
        directory: Directory to check (defaults to current working directory)

    Returns:
        Tuple of (owner, repo_name) or None
    """
    # Get preferred remote for CodeGen
    preferred = get_preferred_remote(directory)
    if not preferred:
        return None

    url = get_git_remote_url(directory, remote=preferred)
    if not url:
        return None

    return parse_github_url(url)


def format_repo_identifier(owner: str, repo: str) -> str:
    """
    Format repository identifier for display/matching.

    Args:
        owner: Repository owner
        repo: Repository name

    Returns:
        Formatted string: "owner/repo"
    """
    return f"{owner}/{repo}"
