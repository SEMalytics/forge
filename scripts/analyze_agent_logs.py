#!/usr/bin/env python3
"""
Analyze agent run logs to understand execution flow and identify issues.
"""

import asyncio
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
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


async def analyze_logs(agent_run_id: int, show_all: bool = False):
    """Analyze agent run logs."""

    api_key = os.getenv("CODEGEN_API_KEY")
    org_id = os.getenv("CODEGEN_ORG_ID")

    if not api_key:
        console.print("[red]Error: CODEGEN_API_KEY not set[/red]")
        return

    client = CodeGenClient(api_token=api_key, org_id=org_id)

    console.print(f"[cyan]Fetching logs for agent run {agent_run_id}...[/cyan]")
    console.print()

    try:
        # Get agent run details first
        status = await client.get_agent_run_status(str(agent_run_id))
        console.print("[bold]Agent Run Status:[/bold]")
        console.print(f"  Status: {status.get('status')}")
        console.print(f"  Repository ID: {status.get('repository_id')}")
        console.print(f"  Created: {status.get('created_at')}")
        console.print()

        # Get logs
        all_logs = []
        skip = 0
        limit = 100

        while True:
            logs = await client.get_agent_run_logs(str(agent_run_id), skip=skip, limit=limit)
            if not logs:
                break
            all_logs.extend(logs)
            skip += limit
            if len(logs) < limit:
                break

        console.print(f"[bold]Retrieved {len(all_logs)} log entries[/bold]")
        console.print()

        # Categorize logs
        git_logs = []
        error_logs = []
        action_logs = []
        file_logs = []

        for log in all_logs:
            log_type = log.get('type', '')
            message = log.get('message', '')
            tool_name = log.get('tool_name', '')

            if log_type == 'ERROR':
                error_logs.append(log)
            elif 'git' in tool_name.lower() or 'git' in message.lower():
                git_logs.append(log)
            elif 'file' in tool_name.lower() or 'write' in tool_name.lower():
                file_logs.append(log)
            elif log_type == 'ACTION':
                action_logs.append(log)

        # Display summary
        console.print("[bold cyan]Log Summary:[/bold cyan]")
        console.print(f"  Total logs: {len(all_logs)}")
        console.print(f"  Error logs: {len(error_logs)}")
        console.print(f"  Git-related logs: {len(git_logs)}")
        console.print(f"  File operation logs: {len(file_logs)}")
        console.print(f"  Action logs: {len(action_logs)}")
        console.print()

        # Show errors
        if error_logs:
            console.print(Panel("[bold red]ERRORS FOUND[/bold red]", expand=False))
            for i, log in enumerate(error_logs[:5], 1):
                console.print(f"[red]Error {i}:[/red]")
                console.print(f"  Message: {log.get('message')}")
                console.print(f"  Timestamp: {log.get('timestamp')}")
                if log.get('tool_name'):
                    console.print(f"  Tool: {log.get('tool_name')}")
                if log.get('observation'):
                    console.print(f"  Observation: {log.get('observation')}")
                console.print()

        # Show git operations
        if git_logs:
            console.print(Panel("[bold green]GIT OPERATIONS[/bold green]", expand=False))
            for i, log in enumerate(git_logs[:10], 1):
                console.print(f"[green]Git Op {i}:[/green]")
                console.print(f"  Tool: {log.get('tool_name')}")
                console.print(f"  Timestamp: {log.get('timestamp')}")
                if log.get('tool_input'):
                    console.print("  Input:")
                    console.print(f"    {log.get('tool_input')}")
                if log.get('tool_output'):
                    console.print("  Output:")
                    console.print(f"    {log.get('tool_output')}")
                console.print()
        else:
            console.print("[yellow]No git operations found in logs[/yellow]")
            console.print()

        # Show file operations
        if file_logs:
            console.print(Panel("[bold blue]FILE OPERATIONS[/bold blue]", expand=False))
            console.print(f"[blue]Found {len(file_logs)} file operations[/blue]")
            for i, log in enumerate(file_logs[:5], 1):
                console.print(f"  {i}. {log.get('tool_name')} - {log.get('timestamp')}")
            console.print()

        # Show all logs if requested
        if show_all:
            console.print(Panel("[bold]ALL LOGS[/bold]", expand=False))
            for i, log in enumerate(all_logs, 1):
                console.print(f"\n[cyan]Log {i}:[/cyan]")
                console.print(json.dumps(log, indent=2))

        # Analysis
        console.print(Panel("[bold yellow]ANALYSIS[/bold yellow]", expand=False))

        if status.get('repository_id') is None:
            console.print("[red]❌ repository_id is NULL - agent not connected to repository[/red]")
        else:
            console.print(f"[green]✓ repository_id set: {status.get('repository_id')}[/green]")

        if not git_logs:
            console.print("[yellow]⚠ No git operations detected - this explains why code wasn't pushed[/yellow]")
        else:
            console.print(f"[green]✓ Found {len(git_logs)} git operations[/green]")

        if error_logs:
            console.print(f"[red]❌ {len(error_logs)} errors occurred during execution[/red]")
        else:
            console.print("[green]✓ No errors detected[/green]")

        console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[red]Usage: python analyze_agent_logs.py <agent_run_id> [--all][/red]")
        console.print("Example: python analyze_agent_logs.py 146040")
        sys.exit(1)

    agent_run_id = int(sys.argv[1])
    show_all = "--all" in sys.argv

    asyncio.run(analyze_logs(agent_run_id, show_all))
