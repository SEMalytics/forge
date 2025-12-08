#!/usr/bin/env python3
"""
Test CodeGen API endpoints to find repository listing.
"""

import asyncio
import os
import httpx
from rich.console import Console
from rich.table import Table

console = Console()


async def test_endpoints():
    """Test various API endpoints to find repository information."""

    api_key = os.getenv("CODEGEN_API_KEY")
    org_id = os.getenv("CODEGEN_ORG_ID", "5249")

    if not api_key:
        console.print("[red]Error: CODEGEN_API_KEY not set[/red]")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    base_url = "https://api.codegen.com/v1"

    # Endpoints to test
    endpoints = [
        # User/org info
        f"/user",
        f"/organizations/{org_id}",
        f"/organizations/{org_id}/info",

        # Repository variations
        f"/repositories",
        f"/repos",
        f"/codebases",
        f"/organizations/{org_id}/repos",
        f"/organizations/{org_id}/codebases",
        f"/organizations/{org_id}/repositories",

        # GitHub-specific
        f"/organizations/{org_id}/github/repos",
        f"/github/repos",

        # Agent-related
        f"/organizations/{org_id}/agents",
        f"/organizations/{org_id}/agent/repositories",
    ]

    console.print(f"[cyan]Testing CodeGen API endpoints...[/cyan]")
    console.print(f"Base URL: {base_url}")
    console.print(f"Organization ID: {org_id}")
    console.print()

    results = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"

            try:
                response = await client.get(url, headers=headers)
                status = response.status_code

                if status == 200:
                    data = response.json()
                    results.append({
                        "endpoint": endpoint,
                        "status": f"[green]{status} ✓[/green]",
                        "response": str(data)[:100] + "..." if len(str(data)) > 100 else str(data)
                    })
                    console.print(f"[green]✓[/green] {endpoint}: {status}")

                    # If it looks like repository data, show more detail
                    if isinstance(data, list) and data:
                        console.print(f"  Found {len(data)} items")
                        if isinstance(data[0], dict):
                            console.print(f"  Sample keys: {list(data[0].keys())[:5]}")
                    elif isinstance(data, dict):
                        console.print(f"  Keys: {list(data.keys())[:10]}")
                        # Check for repository-related keys
                        if any(k in data for k in ["repositories", "repos", "codebases", "github_repos"]):
                            console.print(f"  [yellow]⚠ Contains repository data![/yellow]")

                    console.print()

                elif status == 404:
                    results.append({
                        "endpoint": endpoint,
                        "status": f"[yellow]{status}[/yellow]",
                        "response": "Not Found"
                    })
                    console.print(f"[dim]- {endpoint}: {status} (not found)[/dim]")

                else:
                    results.append({
                        "endpoint": endpoint,
                        "status": f"[red]{status}[/red]",
                        "response": response.text[:100]
                    })
                    console.print(f"[red]✗[/red] {endpoint}: {status}")

            except httpx.HTTPStatusError as e:
                console.print(f"[red]✗[/red] {endpoint}: {e.response.status_code}")
            except Exception as e:
                console.print(f"[red]✗[/red] {endpoint}: {str(e)[:50]}")

    console.print()
    console.print("[bold]Summary of successful endpoints:[/bold]")

    table = Table()
    table.add_column("Endpoint", style="cyan")
    table.add_column("Status", style="green")

    for result in results:
        if "✓" in result["status"]:
            table.add_row(result["endpoint"], result["status"])

    console.print(table)


if __name__ == "__main__":
    asyncio.run(test_endpoints())
