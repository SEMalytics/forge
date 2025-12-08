#!/usr/bin/env python3
"""
Test the /repos endpoint to see actual repository data.
"""

import asyncio
import os
import httpx
from rich.console import Console
from rich.json import JSON
from rich.table import Table

console = Console()


async def test_repos():
    """Test the repos endpoint and display data."""

    api_key = os.getenv("CODEGEN_API_KEY")
    org_id = os.getenv("CODEGEN_ORG_ID", "5249")

    if not api_key:
        console.print("[red]Error: CODEGEN_API_KEY not set[/red]")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    url = f"https://api.codegen.com/v1/organizations/{org_id}/repos"

    console.print(f"[cyan]Fetching repositories from:[/cyan] {url}")
    console.print()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            console.print("[bold]Response structure:[/bold]")
            import json
            console.print(json.dumps(data, indent=2))
            console.print()

            # Extract items
            items = data.get("items", [])
            total = data.get("total", 0)

            console.print(f"[green]Found {total} repositories[/green]")
            console.print()

            if items:
                # Create table
                table = Table(title="Available Repositories")

                # Get all possible keys from first item
                sample_keys = list(items[0].keys())
                console.print(f"[dim]Available fields: {', '.join(sample_keys)}[/dim]")
                console.print()

                # Add columns for important fields
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Full Name", style="blue")

                # Check for other useful fields
                if "url" in sample_keys or "github_url" in sample_keys:
                    table.add_column("URL", style="magenta")
                if "status" in sample_keys:
                    table.add_column("Status", style="yellow")

                # Add rows
                for repo in items:
                    row = [
                        str(repo.get("id", "N/A")),
                        repo.get("name", "N/A"),
                        repo.get("full_name") or repo.get("fullName") or "N/A",
                    ]

                    if "url" in sample_keys or "github_url" in sample_keys:
                        row.append(repo.get("url") or repo.get("github_url") or "N/A")
                    if "status" in sample_keys:
                        row.append(repo.get("status", "N/A"))

                    table.add_row(*row)

                console.print(table)
                console.print()

                # Show full data for first repo
                console.print("[bold]Full data for first repository:[/bold]")
                console.print(json.dumps(items[0], indent=2))

    except httpx.HTTPStatusError as e:
        console.print(f"[red]HTTP Error: {e.response.status_code}[/red]")
        console.print(f"[red]{e.response.text}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(test_repos())
