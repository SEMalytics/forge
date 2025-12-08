"""
Git utility functions for repository detection and management.
"""

import re
from pathlib import Path
from typing import Optional, Tuple
import subprocess


def get_git_remote_url(directory: Path = Path.cwd()) -> Optional[str]:
    """
    Get the git remote URL for the current directory.

    Args:
        directory: Directory to check (defaults to current working directory)

    Returns:
        Remote URL or None if not a git repo
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
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


def get_github_repo_info(directory: Path = Path.cwd()) -> Optional[Tuple[str, str]]:
    """
    Get GitHub repository owner and name for the current directory.

    Args:
        directory: Directory to check (defaults to current working directory)

    Returns:
        Tuple of (owner, repo_name) or None
    """
    url = get_git_remote_url(directory)
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
