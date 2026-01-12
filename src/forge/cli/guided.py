"""
Guided interactive chat with smart suggestions.

Provides an intelligent startup experience that:
- Analyzes the repository context
- Reviews recent changes (commits, uncommitted work)
- Proposes numbered action options
- Guides users through a menu-driven workflow
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.markdown import Markdown

from anthropic import Anthropic

console = Console()


def get_git_status(repo_path: Path) -> Dict[str, Any]:
    """
    Get comprehensive git status for the repository.

    Returns:
        Dictionary with:
        - is_git_repo: bool
        - branch: current branch name
        - uncommitted_files: list of modified/added/deleted files
        - has_uncommitted: bool
        - recent_commits: list of recent commit info
        - has_remote: bool
        - ahead_behind: tuple of (ahead, behind) counts
    """
    result = {
        "is_git_repo": False,
        "branch": None,
        "uncommitted_files": [],
        "has_uncommitted": False,
        "recent_commits": [],
        "has_remote": False,
        "ahead_behind": (0, 0),
        "diff_summary": "",
    }

    if not (repo_path / ".git").exists():
        return result

    result["is_git_repo"] = True

    try:
        # Get current branch
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        result["branch"] = branch.stdout.strip() or "HEAD detached"

        # Get uncommitted changes
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if status.stdout.strip():
            files = []
            for line in status.stdout.strip().split("\n"):
                if line:
                    status_code = line[:2]
                    filename = line[3:]
                    change_type = "modified"
                    if "A" in status_code:
                        change_type = "added"
                    elif "D" in status_code:
                        change_type = "deleted"
                    elif "?" in status_code:
                        change_type = "untracked"
                    files.append({"file": filename, "type": change_type})
            result["uncommitted_files"] = files[:10]  # Limit to 10
            result["has_uncommitted"] = True

        # Get diff summary for uncommitted changes
        if result["has_uncommitted"]:
            diff = subprocess.run(
                ["git", "diff", "--stat", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            result["diff_summary"] = diff.stdout.strip()[-500:] if diff.stdout else ""

        # Get recent commits (last 5)
        log = subprocess.run(
            ["git", "log", "--oneline", "-5", "--no-decorate"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if log.stdout.strip():
            commits = []
            for line in log.stdout.strip().split("\n"):
                if line:
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1][:60]
                        })
            result["recent_commits"] = commits

        # Check for remote
        remote = subprocess.run(
            ["git", "remote"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        result["has_remote"] = bool(remote.stdout.strip())

        # Get ahead/behind if remote exists
        if result["has_remote"]:
            rev_list = subprocess.run(
                ["git", "rev-list", "--left-right", "--count", f"HEAD...@{{upstream}}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if rev_list.returncode == 0 and rev_list.stdout.strip():
                parts = rev_list.stdout.strip().split()
                if len(parts) == 2:
                    result["ahead_behind"] = (int(parts[0]), int(parts[1]))

    except Exception as e:
        # Silently handle git errors
        pass

    return result


def get_recent_file_changes(repo_path: Path, hours: int = 24) -> List[Dict[str, Any]]:
    """
    Get files changed in the last N hours (from git log).

    Returns list of recently modified files with change info.
    """
    try:
        since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
        result = subprocess.run(
            ["git", "log", f"--since={since}", "--name-status", "--pretty=format:"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        files = {}
        for line in result.stdout.strip().split("\n"):
            if line and "\t" in line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    change_type = parts[0]
                    filename = parts[-1]
                    if filename not in files:
                        files[filename] = change_type

        return [{"file": f, "type": t} for f, t in list(files.items())[:10]]
    except Exception:
        return []


async def generate_suggestions(
    client: Anthropic,
    model: str,
    repo_context: Optional[str],
    git_status: Dict[str, Any],
    recent_files: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """
    Use AI to generate smart suggestions based on repo context.

    Returns list of suggestions with:
    - title: short title
    - description: longer description
    - context: what triggered this suggestion
    """
    # Build context for AI
    context_parts = []

    if repo_context:
        context_parts.append(f"Repository Analysis:\n{repo_context[:2000]}")

    if git_status["has_uncommitted"]:
        files_str = "\n".join([f"  - {f['type']}: {f['file']}" for f in git_status["uncommitted_files"]])
        context_parts.append(f"Uncommitted Changes:\n{files_str}")
        if git_status["diff_summary"]:
            context_parts.append(f"Diff Summary:\n{git_status['diff_summary'][:500]}")

    if git_status["recent_commits"]:
        commits_str = "\n".join([f"  - {c['hash']}: {c['message']}" for c in git_status["recent_commits"]])
        context_parts.append(f"Recent Commits:\n{commits_str}")

    if recent_files:
        files_str = "\n".join([f"  - {f['file']}" for f in recent_files])
        context_parts.append(f"Recently Modified Files (24h):\n{files_str}")

    full_context = "\n\n".join(context_parts) if context_parts else "No specific context available."

    prompt = f"""Based on this repository context, suggest exactly 5 actionable development tasks.
Focus on practical improvements the developer can make right now.

{full_context}

Generate 5 suggestions in this exact JSON format (no markdown, just JSON array):
[
  {{"title": "Short title (max 50 chars)", "description": "One sentence description", "context": "Why this is suggested"}},
  ...
]

Prioritize:
1. If there are uncommitted changes, suggest completing/improving that work
2. If there are recent commits, suggest related follow-ups (tests, docs, refactoring)
3. General improvements based on the codebase (testing, performance, documentation)
4. New features or enhancements that fit the project

Be specific to THIS project, not generic advice."""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        # Parse JSON from response
        import json
        # Try to find JSON array in response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            suggestions = json.loads(json_match.group(0))
            return suggestions[:5]
    except Exception as e:
        console.print(f"[dim]Could not generate AI suggestions: {e}[/dim]")

    # Fallback suggestions
    return get_fallback_suggestions(git_status)


def get_fallback_suggestions(git_status: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate fallback suggestions when AI is unavailable."""
    suggestions = []

    if git_status["has_uncommitted"]:
        suggestions.append({
            "title": "Review and commit current changes",
            "description": "You have uncommitted work that may need attention",
            "context": f"{len(git_status['uncommitted_files'])} files changed"
        })

    suggestions.extend([
        {
            "title": "Add or improve tests",
            "description": "Increase test coverage for recent changes",
            "context": "Testing best practice"
        },
        {
            "title": "Improve documentation",
            "description": "Update README or add code comments",
            "context": "Documentation maintenance"
        },
        {
            "title": "Refactor for clarity",
            "description": "Improve code organization and readability",
            "context": "Code quality"
        },
        {
            "title": "Add a new feature",
            "description": "Describe a feature you'd like to implement",
            "context": "Feature development"
        }
    ])

    return suggestions[:5]


def display_suggestions(suggestions: List[Dict[str, str]], git_status: Dict[str, Any]) -> None:
    """Display suggestions as a numbered menu."""

    # Status header
    if git_status["is_git_repo"]:
        status_parts = [f"[cyan]{git_status['branch']}[/cyan]"]
        if git_status["has_uncommitted"]:
            status_parts.append(f"[yellow]{len(git_status['uncommitted_files'])} uncommitted[/yellow]")
        ahead, behind = git_status["ahead_behind"]
        if ahead > 0:
            status_parts.append(f"[green]↑{ahead}[/green]")
        if behind > 0:
            status_parts.append(f"[red]↓{behind}[/red]")

        console.print(f"\n[bold]Branch:[/bold] {' • '.join(status_parts)}")

    # Recent commits
    if git_status["recent_commits"]:
        console.print("\n[bold]Recent commits:[/bold]")
        for commit in git_status["recent_commits"][:3]:
            console.print(f"  [dim]{commit['hash']}[/dim] {commit['message']}")

    # Uncommitted changes
    if git_status["has_uncommitted"]:
        console.print("\n[bold]Uncommitted changes:[/bold]")
        for f in git_status["uncommitted_files"][:5]:
            color = {"added": "green", "deleted": "red", "modified": "yellow", "untracked": "dim"}.get(f["type"], "white")
            console.print(f"  [{color}]{f['type']:10}[/{color}] {f['file']}")
        if len(git_status["uncommitted_files"]) > 5:
            console.print(f"  [dim]... and {len(git_status['uncommitted_files']) - 5} more[/dim]")

    # Suggestions menu
    console.print("\n[bold]What would you like to work on?[/bold]\n")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Num", style="cyan bold", width=4)
    table.add_column("Title", style="bold")
    table.add_column("Context", style="dim")

    for i, suggestion in enumerate(suggestions, 1):
        table.add_row(
            f"[{i}]",
            suggestion["title"],
            suggestion.get("context", "")[:40]
        )

    console.print(table)
    console.print("\n[dim]Enter a number, or type your own request[/dim]")


def parse_user_selection(user_input: str, suggestions: List[Dict[str, str]]) -> Tuple[bool, Optional[str]]:
    """
    Parse user input - either a number selection or custom text.

    Returns:
        (is_selection, content)
        - If number: (True, suggestion description)
        - If custom: (False, user's text)
    """
    user_input = user_input.strip()

    # Check if it's a number
    if user_input.isdigit():
        num = int(user_input)
        if 1 <= num <= len(suggestions):
            suggestion = suggestions[num - 1]
            return (True, f"{suggestion['title']}: {suggestion['description']}")

    # Check for [N] format
    match = re.match(r'\[?(\d+)\]?', user_input)
    if match:
        num = int(match.group(1))
        if 1 <= num <= len(suggestions):
            suggestion = suggestions[num - 1]
            return (True, f"{suggestion['title']}: {suggestion['description']}")

    # Custom input
    return (False, user_input)


async def guided_startup(
    api_key: str,
    model: str,
    repo_path: Path,
    repo_context: Optional[str] = None
) -> Optional[str]:
    """
    Run the guided startup flow.

    Returns:
        The selected/entered task description, or None if cancelled.
    """
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML

    console.print("\n[bold blue]Analyzing your project...[/bold blue]")

    # Get git status
    git_status = get_git_status(repo_path)
    recent_files = get_recent_file_changes(repo_path) if git_status["is_git_repo"] else []

    # Generate AI suggestions
    client = Anthropic(api_key=api_key)

    with console.status("[bold green]Generating suggestions..."):
        suggestions = await generate_suggestions(
            client, model, repo_context, git_status, recent_files
        )

    # Display suggestions
    display_suggestions(suggestions, git_status)

    # Get user selection
    session = PromptSession()

    try:
        user_input = await session.prompt_async(
            HTML('\n<ansigreen><b>Your choice</b></ansigreen>: ')
        )

        if not user_input.strip():
            return None

        if user_input.lower() in ['exit', 'quit', 'q']:
            return None

        is_selection, content = parse_user_selection(user_input, suggestions)

        if is_selection:
            console.print(f"\n[green]→[/green] {content}\n")

        return content

    except (EOFError, KeyboardInterrupt):
        return None
