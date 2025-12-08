#!/usr/bin/env python3
"""
Check current repository's CodeGen configuration status.

Usage:
    python scripts/check_repo_status.py

Or with poetry:
    poetry run python scripts/check_repo_status.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from forge.utils.git_utils import get_github_repo_info, get_git_remote_url, format_repo_identifier
from forge.integrations.codegen_client import CodeGenClient, CodeGenError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def check_status():
    """Check repository configuration status."""

    console.print("[bold cyan]Forge Repository Configuration Check[/bold cyan]")
    console.print()

    # Step 1: Check git remote
    console.print("[yellow]Step 1: Checking git remote...[/yellow]")

    remote_url = get_git_remote_url()
    if not remote_url:
        console.print("[red]✗ Not in a git repository or no remote configured[/red]")
        console.print()
        console.print("To fix:")
        console.print("  git remote add origin <your-github-url>")
        return False

    console.print(f"[green]✓ Git remote found:[/green] {remote_url}")
    console.print()

    # Step 2: Parse GitHub info
    console.print("[yellow]Step 2: Parsing GitHub repository...[/yellow]")

    github_info = get_github_repo_info()
    if not github_info:
        console.print("[red]✗ Not a GitHub repository[/red]")
        console.print()
        console.print("CodeGen only works with GitHub repositories.")
        console.print("Consider pushing to GitHub first.")
        return False

    owner, repo_name = github_info
    repo_identifier = format_repo_identifier(owner, repo_name)

    console.print(f"[green]✓ GitHub repository detected:[/green] {repo_identifier}")
    console.print()

    # Step 3: Check CodeGen credentials
    console.print("[yellow]Step 3: Checking CodeGen credentials...[/yellow]")

    api_key = os.getenv("CODEGEN_API_KEY")
    org_id = os.getenv("CODEGEN_ORG_ID")

    if not api_key:
        console.print("[red]✗ CODEGEN_API_KEY not set[/red]")
        console.print()
        console.print("Add to ~/.zshrc:")
        console.print("  export CODEGEN_API_KEY=<your-key>")
        return False

    console.print("[green]✓ CODEGEN_API_KEY is set[/green]")

    if org_id:
        console.print(f"[green]✓ CODEGEN_ORG_ID is set:[/green] {org_id}")
    else:
        console.print("[yellow]⚠ CODEGEN_ORG_ID not set (will auto-detect)[/yellow]")

    console.print()

    # Step 4: Check CodeGen repository access
    console.print("[yellow]Step 4: Checking CodeGen repository access...[/yellow]")

    try:
        client = CodeGenClient(api_token=api_key, org_id=org_id)

        # Try to find matching repository
        repo = await client.find_repository_by_name(repo_identifier)
        if not repo:
            # Try just the repo name
            repo = await client.find_repository_by_name(repo_name)

        if repo:
            console.print(f"[green]✓ CodeGen repository found![/green]")
            console.print(f"  Name: {repo.get('name')}")
            console.print(f"  ID: {repo.get('id')}")
            console.print()
            console.print("[bold green]✓ Configuration complete! Ready to build.[/bold green]")
            return True
        else:
            console.print(f"[red]✗ No CodeGen repository found for {repo_identifier}[/red]")
            console.print()

            # Show available repos
            try:
                repos = await client.list_repositories()
                if repos:
                    console.print("[cyan]Available CodeGen repositories:[/cyan]")
                    table = Table()
                    table.add_column("ID", style="cyan")
                    table.add_column("Name", style="green")

                    for r in repos:
                        table.add_row(str(r.get("id", "N/A")), r.get("name", "unknown"))

                    console.print(table)
                    console.print()
            except:
                pass

            # Show setup instructions
            console.print(Panel(
                f"""[bold]To add {repo_identifier} to CodeGen:[/bold]

1. Go to: [link]https://github.com/apps/codegen-sh[/link]
2. Click 'Configure' next to [cyan]{owner}[/cyan]
3. Select [green]{repo_identifier}[/green] repository
4. Go to [link]https://codegen.com/repos[/link] to verify

[bold yellow]Note:[/bold yellow] If the repository is in a different organization (e.g., internexio),
you'll need to either:
  • Copy the repository to {owner} organization, OR
  • Install CodeGen GitHub App for that organization
""",
                title="[bold red]Setup Required[/bold red]",
                border_style="red"
            ))
            return False

    except CodeGenError as e:
        console.print(f"[red]CodeGen API Error: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False


if __name__ == "__main__":
    success = asyncio.run(check_status())
    sys.exit(0 if success else 1)
