#!/usr/bin/env python3
"""
Generate setup commands for a CodeGen repository.

This script triggers CodeGen to analyze a repository and generate
appropriate setup commands (like `poetry install` or `npm install`).
Setup commands are required to change repository status from NOT_SETUP.
"""

import asyncio
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Load environment variables from .env file
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from forge.integrations.codegen_client import CodeGenClient

console = Console()


async def setup_repository(repo_identifier: str, custom_prompt: str = None):
    """
    Generate setup commands for a repository.

    Args:
        repo_identifier: Repository name or ID
        custom_prompt: Optional custom instructions for setup generation
    """

    api_key = os.getenv("CODEGEN_API_KEY")
    org_id = os.getenv("CODEGEN_ORG_ID")

    if not api_key:
        console.print("[red]Error: CODEGEN_API_KEY not set[/red]")
        return

    client = CodeGenClient(api_token=api_key, org_id=org_id)

    try:
        # Try to parse as integer ID first
        try:
            repo_id = int(repo_identifier)
            console.print(f"[cyan]Using repository ID: {repo_id}[/cyan]")
        except ValueError:
            # Treat as name, find the repository
            console.print(f"[cyan]Looking up repository: {repo_identifier}[/cyan]")
            repo = await client.find_repository_by_name(repo_identifier)

            if not repo:
                console.print(f"[red]Repository '{repo_identifier}' not found[/red]")
                console.print("\n[yellow]Available repositories:[/yellow]")
                repos = await client.list_repositories()
                for r in repos:
                    console.print(f"  - {r.get('full_name')} (ID: {r.get('id')}) - {r.get('setup_status')}")
                return

            repo_id = repo['id']
            console.print(f"[green]Found: {repo.get('full_name')} (ID: {repo_id})[/green]")
            console.print(f"[yellow]Current status: {repo.get('setup_status')}[/yellow]")

        console.print()
        console.print(Panel("[bold]Generating Setup Commands[/bold]", expand=False))
        console.print()

        # Generate setup commands
        result = await client.generate_setup_commands(
            repo_id=repo_id,
            prompt=custom_prompt
        )

        console.print("[green]✓ Setup command generation started![/green]")
        console.print()
        console.print(f"  Agent Run ID: {result.get('agent_run_id')}")
        console.print(f"  Status: {result.get('status')}")
        if result.get('url'):
            console.print(f"  URL: {result.get('url')}")

        console.print()
        console.print("[cyan]The agent is now analyzing your repository...[/cyan]")
        console.print("[cyan]Setup commands will be automatically configured when complete.[/cyan]")
        console.print()
        console.print("[yellow]Note: This typically takes 1-3 minutes.[/yellow]")
        console.print("[yellow]Repository status will change from NOT_SETUP after completion.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[red]Usage: python setup_repository.py <repo_name_or_id> [custom_prompt][/red]")
        console.print()
        console.print("[bold]Examples:[/bold]")
        console.print("  python setup_repository.py SEMalytics-forge")
        console.print("  python setup_repository.py 184372")
        console.print("  python setup_repository.py forge 'Use poetry for dependency management'")
        console.print()
        sys.exit(1)

    repo_identifier = sys.argv[1]
    custom_prompt = sys.argv[2] if len(sys.argv) > 2 else None

    asyncio.run(setup_repository(repo_identifier, custom_prompt))
