#!/usr/bin/env python3
"""
Check what repository an agent run is using.
"""

import asyncio
import os
import httpx
import sys
from pathlib import Path
from rich.console import Console
from rich.json import JSON
from dotenv import load_dotenv

# Load environment variables from .env file
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

console = Console()


async def check_agent_run(agent_run_id: int):
    """Check agent run details."""

    api_key = os.getenv("CODEGEN_API_KEY")
    org_id = os.getenv("CODEGEN_ORG_ID", "5249")

    if not api_key:
        console.print("[red]Error: CODEGEN_API_KEY not set[/red]")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    url = f"https://api.codegen.com/v1/organizations/{org_id}/agent/run/{agent_run_id}"

    console.print(f"[cyan]Fetching agent run {agent_run_id}...[/cyan]")
    console.print(f"URL: {url}")
    console.print()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            console.print("[bold]Agent Run Details:[/bold]")
            console.print()

            # Show key fields
            console.print(f"[cyan]ID:[/cyan] {data.get('id')}")
            console.print(f"[cyan]Status:[/cyan] {data.get('status')}")
            console.print(f"[cyan]Repository ID:[/cyan] {data.get('repository_id')}")
            console.print(f"[cyan]Created:[/cyan] {data.get('created_at')}")
            console.print()

            # If repository_id exists, try to get repository details
            repo_id = data.get('repository_id')
            if repo_id:
                repo_url = f"https://api.codegen.com/v1/organizations/{org_id}/repos"
                repo_response = await client.get(repo_url, headers=headers)
                repos = repo_response.json().get('items', [])

                matching_repo = next((r for r in repos if r.get('id') == repo_id), None)
                if matching_repo:
                    console.print(f"[green]Repository:[/green] {matching_repo.get('full_name')}")
                    console.print(f"[green]Repository Name:[/green] {matching_repo.get('name')}")
                else:
                    console.print(f"[yellow]Repository ID {repo_id} not found in org repos[/yellow]")
            else:
                console.print("[yellow]No repository_id in agent run[/yellow]")

            console.print()
            console.print("[bold]Full Response:[/bold]")
            import json
            console.print(json.dumps(data, indent=2))

    except httpx.HTTPStatusError as e:
        console.print(f"[red]HTTP Error: {e.response.status_code}[/red]")
        console.print(f"[red]{e.response.text}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[red]Usage: python check_agent_run.py <agent_run_id>[/red]")
        console.print("Example: python check_agent_run.py 145801")
        sys.exit(1)

    agent_run_id = int(sys.argv[1])
    asyncio.run(check_agent_run(agent_run_id))
