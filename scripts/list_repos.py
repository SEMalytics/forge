#!/usr/bin/env python3
"""
List all CodeGen repositories and their configuration details.
"""

import asyncio
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
import json
from dotenv import load_dotenv

# Load environment variables from .env file
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from forge.integrations.codegen_client import CodeGenClient

console = Console()


async def list_repos():
    """List all repositories with full details."""

    api_key = os.getenv("CODEGEN_API_KEY")
    org_id = os.getenv("CODEGEN_ORG_ID")

    if not api_key:
        console.print("[red]Error: CODEGEN_API_KEY not set[/red]")
        return

    client = CodeGenClient(api_token=api_key, org_id=org_id)

    console.print("[cyan]Fetching repositories...[/cyan]")
    console.print()

    try:
        repos = await client.list_repositories()

        if not repos:
            console.print("[yellow]No repositories found[/yellow]")
            return

        console.print(f"[bold]Found {len(repos)} repositories:[/bold]")
        console.print()

        # Create table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("Full Name")
        table.add_column("Language")
        table.add_column("Status")

        for repo in repos:
            table.add_row(
                str(repo.get('id', 'N/A')),
                repo.get('name', 'N/A'),
                repo.get('full_name', 'N/A'),
                repo.get('language', 'N/A'),
                repo.get('setup_status', 'N/A')
            )

        console.print(table)
        console.print()

        # Show detailed info for each repo
        console.print("[bold]Detailed Repository Information:[/bold]")
        console.print()

        for repo in repos:
            console.print(f"[cyan]{'='*60}[/cyan]")
            console.print(f"[bold]{repo.get('full_name', 'Unknown')}[/bold] (ID: {repo.get('id')})")
            console.print()
            console.print(json.dumps(repo, indent=2))
            console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(list_repos())
