#!/usr/bin/env python3
"""
Test repository ID detection end-to-end.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from forge.integrations.codegen_client import CodeGenClient
from forge.utils.git_utils import get_github_repo_info, format_repo_identifier
from rich.console import Console

console = Console()


async def test_detection():
    """Test the complete repository detection flow."""

    console.print("[bold cyan]Testing Repository Detection[/bold cyan]")
    console.print()

    # Step 1: Check environment
    console.print("[yellow]Step 1: Environment Variables[/yellow]")
    api_key = os.getenv("CODEGEN_API_KEY")
    org_id = os.getenv("CODEGEN_ORG_ID")

    console.print(f"CODEGEN_API_KEY: {'✓ Set' if api_key else '✗ Not Set'}")
    console.print(f"CODEGEN_ORG_ID: {org_id or '✗ Not Set'}")
    console.print()

    if not api_key:
        console.print("[red]Error: CODEGEN_API_KEY not set[/red]")
        return False

    # Step 2: Detect git repository
    console.print("[yellow]Step 2: Git Repository Detection[/yellow]")
    github_info = get_github_repo_info()

    if not github_info:
        console.print("[red]✗ Not in a git repository or no GitHub remote found[/red]")
        return False

    owner, repo_name = github_info
    repo_identifier = format_repo_identifier(owner, repo_name)
    console.print(f"[green]✓ Detected GitHub repository:[/green] {repo_identifier}")
    console.print()

    # Step 3: Create CodeGen client
    console.print("[yellow]Step 3: CodeGen Client Initialization[/yellow]")
    client = CodeGenClient(
        api_token=api_key,
        org_id=org_id
    )
    console.print(f"[green]✓ Client initialized with org_id:[/green] {org_id or 'auto-detect'}")
    console.print()

    # Step 4: Find repository
    console.print("[yellow]Step 4: Find Repository via API[/yellow]")
    try:
        # Try exact match on full name
        repo = await client.find_repository_by_name(repo_identifier)

        if repo:
            console.print(f"[green]✓ Found repository![/green]")
            console.print(f"  ID: {repo.get('id')}")
            console.print(f"  Name: {repo.get('name')}")
            console.print(f"  Full Name: {repo.get('full_name')}")
            console.print()
            console.print("[bold green]✓ Repository detection successful![/bold green]")
            console.print()
            console.print(f"[cyan]Repository ID to use:[/cyan] {repo.get('id')}")
            return True
        else:
            console.print(f"[red]✗ Repository not found: {repo_identifier}[/red]")
            console.print()

            # List available repos
            repos = await client.list_repositories()
            if repos:
                console.print("[cyan]Available repositories:[/cyan]")
                for r in repos:
                    console.print(f"  - {r.get('full_name')} (ID: {r.get('id')})")
                console.print()
            return False

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        return False


if __name__ == "__main__":
    import subprocess

    # Source .zshrc to get environment variables
    result = subprocess.run(
        ["zsh", "-c", "source ~/.zshrc && env"],
        capture_output=True,
        text=True
    )

    # Parse environment from sourced shell
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            os.environ[key] = value

    # Run test
    success = asyncio.run(test_detection())
    sys.exit(0 if success else 1)
