#!/usr/bin/env python3
"""
Helper script to list and verify CodeGen repositories.

Usage:
    python scripts/check_codegen_repos.py

Or with poetry:
    poetry run python scripts/check_codegen_repos.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from forge.integrations.codegen_client import CodeGenClient, CodeGenError
from rich.console import Console
from rich.table import Table

console = Console()


async def check_repositories():
    """Check and list available CodeGen repositories."""

    # Get credentials
    api_key = os.getenv("CODEGEN_API_KEY")
    org_id = os.getenv("CODEGEN_ORG_ID")

    if not api_key:
        console.print("[red]Error: CODEGEN_API_KEY not set[/red]")
        console.print("Set it with: export CODEGEN_API_KEY=your-key")
        return False

    console.print(f"[cyan]Checking CodeGen repositories...[/cyan]")
    console.print(f"Organization ID: {org_id or 'auto-detect'}")
    console.print()

    try:
        # Create client
        client = CodeGenClient(
            api_token=api_key,
            org_id=org_id
        )

        # List repositories
        repos = await client.list_repositories()

        if not repos:
            console.print("[yellow]No repositories found[/yellow]")
            console.print()
            console.print("To add a repository:")
            console.print("1. Go to https://codegen.com/repos")
            console.print("2. Click 'Add Repository'")
            console.print("3. Connect your GitHub account")
            console.print("4. Select SEMalytics/forge repository")
            return False

        # Create table
        table = Table(title="Available CodeGen Repositories")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("URL", style="blue")
        table.add_column("Status", style="magenta")

        forge_repo = None
        for repo in repos:
            repo_id = str(repo.get("id", "N/A"))
            name = repo.get("name", "unknown")
            url = repo.get("url", repo.get("github_url", "N/A"))
            status = repo.get("status", "active")

            table.add_row(repo_id, name, url, status)

            # Check if this matches forge
            if "forge" in name.lower():
                forge_repo = repo

        console.print(table)
        console.print()

        # Check for Forge repository
        if forge_repo:
            console.print(f"[green]✓ Found Forge repository:[/green]")
            console.print(f"  ID: {forge_repo.get('id')}")
            console.print(f"  Name: {forge_repo.get('name')}")
            console.print()
            console.print("[cyan]To use this repository, add to your ~/.zshrc:[/cyan]")
            console.print(f"export CODEGEN_REPO_ID={forge_repo.get('id')}")
        else:
            console.print("[yellow]⚠ No Forge repository found[/yellow]")
            console.print()
            console.print("Steps to add Forge repository:")
            console.print("1. Go to https://github.com/apps/codegen-sh")
            console.print("2. Click 'Configure' next to your organization")
            console.print("3. Select 'SEMalytics/forge' repository")
            console.print("4. Go to https://codegen.com/repos to verify")
            console.print()
            console.print("Alternatively, you can manually set any repo ID:")
            console.print("export CODEGEN_REPO_ID=<repo_id>")

        return True

    except CodeGenError as e:
        console.print(f"[red]CodeGen API Error: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False


if __name__ == "__main__":
    success = asyncio.run(check_repositories())
    sys.exit(0 if success else 1)
