"""
Interactive chat interface with Rich formatting

Provides beautiful terminal-based conversational interface for
project planning with the Forge Planning Agent.

Uses prompt_toolkit for robust input handling:
- Full editing support (backspace, delete, arrow keys)
- Proper paste handling
- Non-blocking async input
- Input history with search
"""

from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from pathlib import Path
import asyncio
from datetime import datetime
import itertools
import threading
import sys

# prompt_toolkit for robust input handling
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.input import vt100_parser

from forge.layers.planning import PlanningAgent, PlanningError
from forge.utils.logger import logger


console = Console()


async def _handle_slash_command(
    command: str,
    agent,
    repo_path: Path,
    api_key: str,
    model: str
) -> bool:
    """
    Handle slash commands for Forge actions.

    Commands:
        /build [spec]     - Generate code from spec or conversation
        /test             - Run tests
        /status           - Show project status
        /decompose [desc] - Break down a task
        /diff             - Show uncommitted changes
        /commit [msg]     - Commit changes
        /commands         - Show available commands

    Returns:
        True if command was handled, False otherwise
    """
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd in ['/commands', '/cmds', '/?']:
        _print_slash_commands()
        return True

    elif cmd == '/status':
        await _cmd_status(repo_path)
        return True

    elif cmd == '/diff':
        await _cmd_diff(repo_path)
        return True

    elif cmd == '/test':
        await _cmd_test(repo_path)
        return True

    elif cmd == '/build':
        await _cmd_build(agent, repo_path, args, api_key, model)
        return True

    elif cmd == '/decompose':
        await _cmd_decompose(agent, args, api_key, model)
        return True

    elif cmd == '/commit':
        await _cmd_commit(repo_path, args)
        return True

    elif cmd == '/push':
        await _cmd_push(repo_path)
        return True

    elif cmd == '/analyze':
        await _cmd_analyze(repo_path)
        return True

    elif cmd == '/setup':
        await _cmd_setup_codegen(repo_path)
        return True

    else:
        console.print(f"[yellow]Unknown command:[/yellow] {cmd}")
        console.print("[dim]Type /commands to see available commands[/dim]")
        return True

    return False


def _print_slash_commands():
    """Print available slash commands."""
    commands_table = Table(title="Forge Commands", border_style="cyan", show_header=True)
    commands_table.add_column("Command", style="cyan")
    commands_table.add_column("Description")

    commands_table.add_row("/build [spec]", "Generate code and write files to disk")
    commands_table.add_row("/build codegen [spec]", "Use CodeGen API backend (requires setup)")
    commands_table.add_row("/test", "Run project tests")
    commands_table.add_row("/status", "Show git status and project info")
    commands_table.add_row("/diff", "Show uncommitted changes")
    commands_table.add_row("/commit [msg]", "Commit staged changes")
    commands_table.add_row("/push", "Push commits to remote")
    commands_table.add_row("/decompose [task]", "Break down a task into steps")
    commands_table.add_row("/analyze", "Re-analyze the repository")
    commands_table.add_row("/setup", "Configure CodeGen repo for this project")
    commands_table.add_row("/commands", "Show this help")

    console.print("\n")
    console.print(commands_table)
    console.print()


def _detect_planning_complete(response: str) -> bool:
    """
    Detect if the AI response indicates planning is complete.

    Looks for common phrases that signal the planning phase is done
    and the user might want to take action.

    Args:
        response: The AI's response text

    Returns:
        True if planning appears complete
    """
    # Phrases that indicate planning is done
    completion_signals = [
        "done here",
        "finished planning",
        "planning is complete",
        "ready to implement",
        "ready to build",
        "ready to proceed",
        "let me know when you're ready",
        "whenever you're ready",
        "shall i generate",
        "shall i create",
        "would you like me to generate",
        "would you like me to create",
        "would you like me to implement",
        "i can now generate",
        "i can now create",
        "i can now implement",
        "my role as the planning agent is done",
        "that covers the plan",
        "that's the plan",
        "here's the plan",
        "the plan is ready",
        "implementation plan is complete",
    ]

    response_lower = response.lower()
    return any(signal in response_lower for signal in completion_signals)


def _show_next_steps() -> Optional[str]:
    """
    Show numbered next-step options after planning is complete.

    Returns:
        The slash command to execute, or None if user wants to continue chatting
    """
    console.print("\n[bold cyan]━━━ Ready for Next Step ━━━[/bold cyan]")
    console.print()

    options = [
        ("1", "/build", "Generate code and write files"),
        ("2", "/decompose", "Break down into detailed tasks"),
        ("3", "/test", "Run existing tests"),
        ("4", None, "Continue conversation"),
    ]

    for num, cmd, desc in options:
        if cmd:
            console.print(f"  [cyan]{num}[/cyan]) [bold]{cmd}[/bold] - {desc}")
        else:
            console.print(f"  [cyan]{num}[/cyan]) {desc}")

    console.print()

    try:
        choice = Prompt.ask(
            "[bold]Select next step[/bold]",
            choices=["1", "2", "3", "4"],
            default="4"
        )

        # Map choice to command
        choice_map = {"1": "/build", "2": "/decompose", "3": "/test", "4": None}
        return choice_map.get(choice)

    except (KeyboardInterrupt, EOFError):
        return None


async def _cmd_status(repo_path: Path):
    """Show git status and project info."""
    import subprocess

    console.print("\n[bold]Project Status[/bold]\n")

    # Git status
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout.strip():
            console.print("[bold]Uncommitted changes:[/bold]")
            for line in result.stdout.strip().split("\n")[:10]:
                console.print(f"  {line}")
        else:
            console.print("[green]✓[/green] Working directory clean")

        # Branch info
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        console.print(f"\n[bold]Branch:[/bold] {branch.stdout.strip()}")

    except Exception as e:
        console.print(f"[red]Error getting status:[/red] {e}")

    console.print()


async def _cmd_diff(repo_path: Path):
    """Show git diff."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.stdout.strip():
            console.print("\n[bold]Changes:[/bold]")
            console.print(result.stdout)
        else:
            console.print("\n[dim]No uncommitted changes[/dim]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

    console.print()


async def _cmd_test(repo_path: Path):
    """Run project tests."""
    import subprocess

    console.print("\n[bold]Running tests...[/bold]\n")

    # Detect test framework
    test_cmd = None
    if (repo_path / "pytest.ini").exists() or (repo_path / "pyproject.toml").exists():
        test_cmd = ["python", "-m", "pytest", "-v"]
    elif (repo_path / "package.json").exists():
        test_cmd = ["npm", "test"]
    elif (repo_path / "Cargo.toml").exists():
        test_cmd = ["cargo", "test"]
    else:
        # Try pytest as default
        test_cmd = ["python", "-m", "pytest", "-v"]

    try:
        with console.status("[bold green]Running tests..."):
            result = subprocess.run(
                test_cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )

        console.print(result.stdout)
        if result.stderr:
            console.print(result.stderr)

        if result.returncode == 0:
            console.print("\n[green]✓ Tests passed![/green]")
        else:
            console.print(f"\n[red]✗ Tests failed (exit code {result.returncode})[/red]")

    except subprocess.TimeoutExpired:
        console.print("[red]Tests timed out after 5 minutes[/red]")
    except Exception as e:
        console.print(f"[red]Error running tests:[/red] {e}")

    console.print()


def _parse_file_blocks(content: str) -> list[tuple[str, str, str]]:
    """
    Parse file blocks from AI-generated content.

    Expects format:
        ## File: path/to/file
        ```language
        file contents
        ```

    Returns:
        List of (file_path, language, content) tuples
    """
    import re

    files = []
    # Match: ## File: path followed by ```lang ... ```
    pattern = r'##\s*File:\s*([^\n]+)\n```(\w*)\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)

    for match in matches:
        file_path = match[0].strip().strip('`')
        language = match[1].strip()
        file_content = match[2]
        files.append((file_path, language, file_content))

    return files


def _write_files(repo_path: Path, files: list[tuple[str, str, str]]) -> list[str]:
    """
    Write files to disk.

    Args:
        repo_path: Base directory for relative paths
        files: List of (path, language, content) tuples

    Returns:
        List of successfully written file paths
    """
    written = []

    for file_path, _, content in files:
        try:
            # Handle absolute vs relative paths
            if file_path.startswith('/'):
                full_path = Path(file_path)
            else:
                full_path = repo_path / file_path

            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file
            full_path.write_text(content)
            written.append(str(file_path))

        except Exception as e:
            console.print(f"[red]✗ Failed to write {file_path}:[/red] {e}")

    return written


async def _cmd_build(agent, repo_path: Path, spec: str, api_key: str, model: str):
    """
    Generate code and write files to disk.

    This command:
    1. Uses conversation context or provided spec
    2. Asks the AI to generate complete file contents
    3. Parses the output for file blocks
    4. Writes files directly to disk
    5. Offers to commit changes

    Backends:
    - Default: Uses Claude (planning agent) for generation
    - /build codegen: Uses CodeGen API for generation
    """
    import os

    console.print("\n[bold]Code Generation[/bold]\n")

    # Check if using codegen backend
    use_codegen = False
    if spec.lower().startswith('codegen'):
        use_codegen = True
        spec = spec[7:].strip()  # Remove 'codegen' from spec

    if not spec:
        # Use conversation context
        last_response = agent.get_last_assistant_message()
        if last_response:
            console.print("[dim]Using conversation context...[/dim]\n")
            spec = f"Based on our conversation, implement the following:\n\n{last_response}"
        else:
            console.print("[yellow]No spec provided and no conversation context.[/yellow]")
            console.print("Usage: /build [codegen] <specification>")
            return

    # Use CodeGen API if requested
    if use_codegen:
        await _cmd_build_codegen(repo_path, spec, api_key)
        return

    # Generate with structured output format
    build_prompt = f"""Based on our conversation, generate the actual code implementation.

IMPORTANT: Output ONLY in this exact format for each file - I will parse and write these files automatically:

## File: <path/to/file>
```<language>
<complete file contents>
```

Create all necessary files with complete, working code. Use relative paths from the project root.

Context/Spec:
{spec}
"""

    # Collect full response for parsing
    console.print("[dim]Generating code...[/dim]")
    full_response = ""

    # Start thinking animation
    animation_task = asyncio.create_task(_animate_thinking_cursor())

    try:
        first_chunk = True
        async for chunk in agent.chat(build_prompt):
            if first_chunk:
                animation_task.cancel()
                try:
                    await animation_task
                except asyncio.CancelledError:
                    pass
                sys.stdout.write("\r" + " " * 40 + "\r")
                sys.stdout.flush()
                console.print("\n[bold green]Forge[/bold green]: ", end="")
                first_chunk = False
            console.print(chunk, end="", markup=False)
            full_response += chunk
    finally:
        if not animation_task.done():
            animation_task.cancel()

    console.print("\n")

    # Parse file blocks from response
    files = _parse_file_blocks(full_response)

    if not files:
        console.print("[yellow]No file blocks found in response.[/yellow]")
        console.print("[dim]Expected format: ## File: path followed by code blocks[/dim]")
        return

    # Show what will be written
    console.print(f"\n[bold cyan]━━━ Files to Write ({len(files)}) ━━━[/bold cyan]\n")
    for file_path, lang, content in files:
        lines = len(content.strip().split('\n'))
        console.print(f"  [cyan]•[/cyan] {file_path} [dim]({lang}, {lines} lines)[/dim]")

    console.print()

    # Confirm before writing
    confirm = Prompt.ask(
        "[bold]Write these files?[/bold]",
        choices=["y", "n"],
        default="y"
    )

    if confirm.lower() != 'y':
        console.print("[yellow]Cancelled.[/yellow]")
        return

    # Write files
    written = _write_files(repo_path, files)

    if written:
        console.print(f"\n[green]✓ Written {len(written)} file(s):[/green]")
        for path in written:
            console.print(f"  [green]•[/green] {path}")

        # Offer to commit
        console.print()
        commit_choice = Prompt.ask(
            "[bold]Commit these changes?[/bold]",
            choices=["y", "n"],
            default="y"
        )

        if commit_choice.lower() == 'y':
            # Generate commit message
            file_names = ", ".join([Path(f).name for f in written[:3]])
            if len(written) > 3:
                file_names += f" (+{len(written) - 3} more)"

            default_msg = f"Add {file_names}"
            commit_msg = Prompt.ask(
                "[bold]Commit message[/bold]",
                default=default_msg
            )

            await _cmd_commit(repo_path, commit_msg)
    else:
        console.print("[yellow]No files were written.[/yellow]")


async def _cmd_build_codegen(repo_path: Path, spec: str, api_key: str):
    """
    Generate code using CodeGen API and write files to disk.

    Uses the CodeGen API backend for code generation, which can
    leverage repository context and run agents on your codebase.

    Auto-triggers /setup if no CODEGEN_REPO_ID is configured.

    Args:
        repo_path: Project root directory
        spec: Specification for code generation
        api_key: API key (used for fallback, CodeGen uses CODEGEN_API_KEY)
    """
    import os

    console.print("[cyan]Using CodeGen API backend[/cyan]\n")

    # Check for CodeGen API key
    codegen_key = os.getenv('CODEGEN_API_KEY')
    if not codegen_key:
        console.print("[red]✗ CODEGEN_API_KEY not set[/red]")
        console.print("[dim]Set it with: export CODEGEN_API_KEY=your-key[/dim]")
        return

    # Check for repo ID - auto-setup if not configured
    repo_id = os.getenv('CODEGEN_REPO_ID')
    if not repo_id:
        console.print("[yellow]No CODEGEN_REPO_ID configured for this project.[/yellow]")
        console.print("[dim]Running setup...[/dim]\n")

        # Run setup
        repo_id = await _cmd_setup_codegen(repo_path)
        if not repo_id:
            console.print("\n[red]Setup cancelled or failed. Cannot proceed with CodeGen.[/red]")
            return

        console.print()  # Extra line after setup

    try:
        from forge.generators.codegen_api import CodeGenAPIGenerator
        from forge.generators.base import GenerationContext

        # Initialize CodeGen generator
        generator = CodeGenAPIGenerator(
            api_key=codegen_key,
            org_id=os.getenv('CODEGEN_ORG_ID'),
            timeout=300
        )

        # Build generation context
        context = GenerationContext(
            task_id="chat-build",
            specification=spec,
            project_context=f"Project at {repo_path}",
            tech_stack=[],
            dependencies=[],
            knowledgeforge_patterns=[],
            file_structure={}
        )

        console.print("[dim]Generating code via CodeGen API...[/dim]")

        # Start thinking animation
        animation_task = asyncio.create_task(_animate_thinking_cursor())

        try:
            result = await generator.generate(context)
        finally:
            animation_task.cancel()
            try:
                await animation_task
            except asyncio.CancelledError:
                pass
            sys.stdout.write("\r" + " " * 40 + "\r")
            sys.stdout.flush()

        if not result.success:
            console.print(f"\n[red]✗ Generation failed:[/red] {result.error}")
            return

        if not result.files:
            console.print("\n[yellow]No files generated.[/yellow]")
            return

        # Show what will be written
        console.print(f"\n[bold cyan]━━━ Files to Write ({len(result.files)}) ━━━[/bold cyan]\n")
        for file_path, content in result.files.items():
            lines = len(content.strip().split('\n'))
            console.print(f"  [cyan]•[/cyan] {file_path} [dim]({lines} lines)[/dim]")

        console.print()

        # Confirm before writing
        confirm = Prompt.ask(
            "[bold]Write these files?[/bold]",
            choices=["y", "n"],
            default="y"
        )

        if confirm.lower() != 'y':
            console.print("[yellow]Cancelled.[/yellow]")
            return

        # Write files
        written = []
        for file_path, content in result.files.items():
            try:
                if file_path.startswith('/'):
                    full_path = Path(file_path)
                else:
                    full_path = repo_path / file_path

                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                written.append(file_path)

            except Exception as e:
                console.print(f"[red]✗ Failed to write {file_path}:[/red] {e}")

        if written:
            console.print(f"\n[green]✓ Written {len(written)} file(s):[/green]")
            for path in written:
                console.print(f"  [green]•[/green] {path}")

            # Offer to commit
            console.print()
            commit_choice = Prompt.ask(
                "[bold]Commit these changes?[/bold]",
                choices=["y", "n"],
                default="y"
            )

            if commit_choice.lower() == 'y':
                file_names = ", ".join([Path(f).name for f in written[:3]])
                if len(written) > 3:
                    file_names += f" (+{len(written) - 3} more)"

                default_msg = f"Add {file_names}"
                commit_msg = Prompt.ask(
                    "[bold]Commit message[/bold]",
                    default=default_msg
                )

                await _cmd_commit(repo_path, commit_msg)

        await generator.close()

    except ImportError as e:
        console.print(f"[red]✗ CodeGen module not available:[/red] {e}")
        console.print("[dim]Try: pip install forge[codegen][/dim]")
    except Exception as e:
        console.print(f"[red]✗ CodeGen error:[/red] {e}")


async def _cmd_setup_codegen(repo_path: Path) -> Optional[int]:
    """
    Configure CodeGen repository for this project.

    Detects the git remote, searches for matching CodeGen repos,
    and saves the repo ID to a local .env file.

    Returns:
        The repo ID if setup was successful, None otherwise
    """
    import os
    import subprocess

    console.print("\n[bold]CodeGen Repository Setup[/bold]\n")

    # Check for CodeGen API key
    codegen_key = os.getenv('CODEGEN_API_KEY')
    if not codegen_key:
        console.print("[red]✗ CODEGEN_API_KEY not set[/red]")
        console.print("[dim]Set it with: export CODEGEN_API_KEY=your-key[/dim]")
        return None

    # Detect git remote
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            console.print("[yellow]Not a git repository or no remote configured[/yellow]")
            return None

        remote_url = result.stdout.strip()
        console.print(f"[dim]Git remote:[/dim] {remote_url}")

        # Extract owner/repo from URL
        import re
        match = re.search(r'github\.com[:/](.+?)/(.+?)(?:\.git)?$', remote_url)
        if match:
            owner, repo_name = match.groups()
            repo_name = repo_name.rstrip('.git')
            full_name = f"{owner}/{repo_name}"
            console.print(f"[dim]GitHub repo:[/dim] {full_name}\n")
        else:
            console.print("[yellow]Could not parse GitHub URL[/yellow]")
            return None

    except Exception as e:
        console.print(f"[red]Error detecting git remote:[/red] {e}")
        return None

    # Search CodeGen repos
    try:
        from forge.integrations.codegen_client import CodeGenClient

        client = CodeGenClient(
            api_token=codegen_key,
            org_id=os.getenv('CODEGEN_ORG_ID')
        )

        console.print("[dim]Searching CodeGen repositories...[/dim]")
        repos = await client.list_repositories()

        if not repos:
            console.print("\n[yellow]No repositories found in your CodeGen account.[/yellow]")
            console.print("\n[bold]To add this repository:[/bold]")
            console.print(f"  1. Go to [cyan]https://github.com/apps/codegen-sh[/cyan]")
            console.print(f"  2. Install the GitHub App for [bold]{owner}[/bold]")
            console.print(f"  3. Select [bold]{repo_name}[/bold] repository")
            console.print(f"  4. Run [cyan]/setup[/cyan] again")
            return None

        # Show available repos
        console.print(f"\n[bold]Available CodeGen Repositories ({len(repos)}):[/bold]\n")

        matching_repo = None
        for i, repo in enumerate(repos, 1):
            repo_full_name = repo.get('full_name', repo.get('name', 'Unknown'))
            repo_id = repo.get('id')
            status = repo.get('setup_status', 'unknown')

            # Check if this matches current repo
            is_match = repo_full_name.lower() == full_name.lower()
            if is_match:
                matching_repo = repo
                console.print(f"  [green]→ {i})[/green] [bold]{repo_full_name}[/bold] (ID: {repo_id}) [green]← MATCH[/green]")
            else:
                console.print(f"  [cyan]{i})[/cyan] {repo_full_name} (ID: {repo_id})")

        console.print()

        # If we found a match, offer to use it
        if matching_repo:
            repo_id = matching_repo.get('id')
            use_match = Prompt.ask(
                f"[bold]Use matched repo {full_name}?[/bold]",
                choices=["y", "n"],
                default="y"
            )

            if use_match.lower() == 'y':
                # Save to .env
                env_path = repo_path / '.env'
                _save_repo_id_to_env(env_path, repo_id, full_name)
                console.print(f"\n[green]✓ Saved CODEGEN_REPO_ID={repo_id} to .env[/green]")
                console.print("[dim]You can now use /build codegen[/dim]")

                # Also set in current environment
                os.environ['CODEGEN_REPO_ID'] = str(repo_id)
                return repo_id

        # Let user pick from list
        console.print("[bold]Enter repo number to use, or 'q' to quit:[/bold]")
        choice = Prompt.ask("Selection", default="q")

        if choice.lower() == 'q':
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(repos):
                selected = repos[idx]
                repo_id = selected.get('id')
                selected_name = selected.get('full_name', selected.get('name'))

                # Save to .env
                env_path = repo_path / '.env'
                _save_repo_id_to_env(env_path, repo_id, selected_name)
                console.print(f"\n[green]✓ Saved CODEGEN_REPO_ID={repo_id} to .env[/green]")

                # Also set in current environment
                os.environ['CODEGEN_REPO_ID'] = str(repo_id)
                return repo_id
            else:
                console.print("[red]Invalid selection[/red]")
                return None

        except ValueError:
            console.print("[red]Invalid input[/red]")
            return None

    except Exception as e:
        console.print(f"[red]Error connecting to CodeGen:[/red] {e}")
        return None


def _save_repo_id_to_env(env_path: Path, repo_id: int, repo_name: str):
    """Save or update CODEGEN_REPO_ID in .env file."""
    lines = []
    found = False

    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('CODEGEN_REPO_ID='):
                    lines.append(f"CODEGEN_REPO_ID={repo_id}  # {repo_name}\n")
                    found = True
                else:
                    lines.append(line)

    if not found:
        lines.append(f"\n# CodeGen Repository\n")
        lines.append(f"CODEGEN_REPO_ID={repo_id}  # {repo_name}\n")

    with open(env_path, 'w') as f:
        f.writelines(lines)


async def _cmd_decompose(agent, task: str, api_key: str, model: str):
    """Break down a task into implementation steps."""
    if not task:
        console.print("[yellow]Usage: /decompose <task description>[/yellow]")
        return

    console.print("\n[bold]Task Decomposition[/bold]\n")
    console.print("[bold green]Forge[/bold green]: ", end="")

    decompose_prompt = f"""Break down this task into specific, actionable implementation steps:

Task: {task}

Provide:
1. A numbered list of concrete steps
2. For each step, specify which files need to be created/modified
3. Identify any dependencies between steps
4. Estimate complexity (simple/medium/complex) for each step

Format as a clear implementation plan."""

    first_chunk = True
    async for chunk in agent.chat(decompose_prompt):
        if first_chunk:
            first_chunk = False
        console.print(chunk, end="", markup=False)

    console.print("\n")


async def _cmd_commit(repo_path: Path, message: str):
    """Commit staged changes."""
    import subprocess

    if not message:
        console.print("[yellow]Usage: /commit <commit message>[/yellow]")
        return

    try:
        # Stage all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=repo_path,
            check=True,
            timeout=10
        )

        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            console.print(f"\n[green]✓ Committed:[/green] {message}")
            console.print(result.stdout)

            # Offer to push
            push_choice = Prompt.ask(
                "[bold]Push to remote?[/bold]",
                choices=["y", "n"],
                default="n"
            )
            if push_choice.lower() == 'y':
                await _cmd_push(repo_path)
        else:
            console.print(f"[yellow]{result.stdout or result.stderr}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error committing:[/red] {e}")

    console.print()


async def _cmd_push(repo_path: Path):
    """Push commits to remote."""
    import subprocess

    console.print("\n[bold]Pushing to remote...[/bold]\n")

    try:
        # Check if there are commits to push
        status = subprocess.run(
            ["git", "status", "-sb"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )

        if "ahead" not in status.stdout:
            console.print("[dim]Nothing to push - already up to date[/dim]")
            return

        # Get current branch
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        branch_name = branch.stdout.strip()

        # Push
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            console.print(f"[green]✓ Pushed to origin/{branch_name}[/green]")
            if result.stderr:
                # Git push outputs to stderr even on success
                console.print(f"[dim]{result.stderr.strip()}[/dim]")
        else:
            console.print(f"[red]✗ Push failed:[/red]")
            console.print(result.stderr or result.stdout)

    except subprocess.TimeoutExpired:
        console.print("[red]Push timed out[/red]")
    except Exception as e:
        console.print(f"[red]Error pushing:[/red] {e}")

    console.print()


async def _cmd_analyze(repo_path: Path):
    """Re-analyze the repository."""
    from forge.layers.repository_analyzer import RepositoryAnalyzer

    console.print("\n[bold]Re-analyzing repository...[/bold]\n")

    try:
        analyzer = RepositoryAnalyzer()
        with console.status("[bold green]Analyzing..."):
            context = analyzer.analyze(repo_path, force=True)

        console.print(f"[green]✓[/green] Analyzed: [bold]{context.project_name}[/bold]")
        console.print(f"  Primary language: {context.primary_language}")
        console.print(f"  Files: {context.file_count} | Lines: {context.total_lines:,}")
        if context.code_patterns:
            console.print(f"  Patterns: {', '.join(context.code_patterns[:3])}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

    console.print()


async def _animate_thinking_cursor():
    """
    Animate an inline cursor after 'Forge:' while waiting for response.

    Shows: Forge: ⠋  →  Forge: ⠙  →  Forge: ⠹  → ...
    """
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0

    # Print initial "Forge: " with first spinner frame
    sys.stdout.write(f"\n\033[1;32mForge\033[0m: {frames[0]}")
    sys.stdout.flush()

    try:
        while True:
            await asyncio.sleep(0.08)
            idx = (idx + 1) % len(frames)
            # Move cursor back and write new frame
            sys.stdout.write(f"\b{frames[idx]}")
            sys.stdout.flush()
    except asyncio.CancelledError:
        # Clean up - erase the spinner character
        sys.stdout.write("\b \b")
        sys.stdout.flush()
        raise


class ThinkingIndicator:
    """Animated thinking indicator that shows while AI is processing."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    THINKING_MESSAGES = [
        "Thinking",
        "Analyzing",
        "Considering",
        "Processing",
        "Reasoning",
    ]

    def __init__(self, message: str = "Thinking"):
        self.message = message
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._frame_cycle = itertools.cycle(self.FRAMES)

    def _animate(self):
        """Animation loop running in background thread."""
        while not self._stop_event.is_set():
            frame = next(self._frame_cycle)
            # Write to stderr to not interfere with stdout
            sys.stderr.write(f"\r[cyan]{frame}[/cyan] {self.message}...   ")
            sys.stderr.flush()
            self._stop_event.wait(0.1)
        # Clear the line when done
        sys.stderr.write("\r" + " " * 50 + "\r")
        sys.stderr.flush()

    def start(self):
        """Start the thinking animation."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the thinking animation."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=0.5)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


class StreamingThinkingIndicator:
    """
    Thinking indicator that works with streaming responses.
    Shows animation until first token arrives, then stops.
    """

    def __init__(self):
        self.started_streaming = False
        self._spinner_task = None
        self._stop_event = asyncio.Event()

    async def show_thinking(self):
        """Show animated thinking indicator."""
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        frame_idx = 0

        while not self._stop_event.is_set():
            if not self.started_streaming:
                frame = frames[frame_idx % len(frames)]
                console.print(f"\r[cyan]{frame}[/cyan] [dim]Thinking...[/dim]", end="")
                frame_idx += 1
            await asyncio.sleep(0.1)

        # Clear thinking indicator
        if not self.started_streaming:
            console.print("\r" + " " * 30 + "\r", end="")

    def mark_streaming_started(self):
        """Called when first token is received."""
        if not self.started_streaming:
            self.started_streaming = True
            # Clear the thinking line
            console.print("\r" + " " * 30 + "\r", end="")

    def stop(self):
        """Stop the indicator."""
        self._stop_event.set()

# Shift+Enter escape sequences for modern terminals with extended keyboard support
# These are sent by terminals like: iTerm2, Kitty, WezTerm, xterm (with modifyOtherKeys)
SHIFT_ENTER_SEQUENCES = [
    '\x1b[13;2u',      # kitty protocol / CSI u encoding
    '\x1b[27;2;13~',   # xterm modifyOtherKeys mode 1
]

# prompt_toolkit styling
PROMPT_STYLE = Style.from_dict({
    'prompt': 'ansigreen bold',
    'continuation': 'ansigray',
})


def _create_key_bindings() -> KeyBindings:
    """
    Create custom key bindings for chat input.

    - Enter: Submit message
    - Alt+Enter: Insert newline (works on most terminals)
    - Escape, then Enter: Insert newline (works on all terminals)
    - Shift+Enter: Insert newline (requires terminal CSI u support)

    Returns:
        Configured KeyBindings instance
    """
    bindings = KeyBindings()

    @bindings.add(Keys.Enter)
    def handle_enter(event):
        """Submit on Enter."""
        event.current_buffer.validate_and_handle()

    # Alt+Enter - works on most terminals including iTerm2
    @bindings.add(Keys.Escape, Keys.ControlM)
    def handle_alt_enter(event):
        """Insert newline on Alt+Enter."""
        event.current_buffer.insert_text('\n')

    @bindings.add(Keys.Escape, Keys.ControlJ)
    def handle_alt_enter_j(event):
        """Insert newline on Alt+Enter (alternate)."""
        event.current_buffer.insert_text('\n')

    @bindings.add(Keys.Escape, Keys.Enter)
    def handle_escape_enter(event):
        """Insert newline on Escape+Enter (universal fallback)."""
        event.current_buffer.insert_text('\n')

    return bindings


def _register_shift_enter():
    """
    Register Shift+Enter escape sequences for modern terminals.

    Modern terminals (iTerm2, Kitty, WezTerm) with CSI u or modifyOtherKeys
    support send distinct escape sequences for Shift+Enter. We map these
    to insert a newline character directly into the buffer.

    This is registered at module load time.
    """
    # Map Shift+Enter sequences directly to newline character insertion
    # When prompt_toolkit sees these sequences, it will insert '\n' into buffer
    # (Keys.ControlJ would trigger Enter binding, so we use literal '\n')
    for seq in SHIFT_ENTER_SEQUENCES:
        vt100_parser.ANSI_SEQUENCES[seq] = '\n'

# Register Shift+Enter handling on module load
_register_shift_enter()


def _get_prompt_session() -> PromptSession:
    """
    Create a prompt session with history and auto-suggest.

    Returns:
        Configured PromptSession instance
    """
    # Ensure history directory exists
    history_dir = Path(".forge")
    history_dir.mkdir(parents=True, exist_ok=True)
    history_file = history_dir / "chat_history"

    return PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=True,
        multiline=True,
        style=PROMPT_STYLE,
        key_bindings=_create_key_bindings(),
    )


def _continuation_prompt(width: int, line_number: int, wrap_count: int) -> str:
    """Generate continuation prompt for multiline input."""
    if wrap_count > 0:
        return " " * 4  # Indent wrapped lines
    return "    "  # Simple indent for continuation lines


def _get_multiline_input(prompt: str = "You", session: Optional[PromptSession] = None) -> str:
    """
    Get multi-line input from user with full editing support.

    Uses prompt_toolkit for:
    - Full editing (backspace, delete, arrow keys)
    - Proper paste handling
    - Input history (Ctrl+R to search)
    - Auto-suggestions from history

    Submission:
    - Enter to submit
    - Escape then Enter for new line

    Args:
        prompt: Prompt label to display
        session: Optional existing PromptSession (for history persistence)

    Returns:
        User input (potentially multi-line)
    """
    if session is None:
        session = _get_prompt_session()

    try:
        # Use prompt_toolkit's async-capable prompt
        # patch_stdout prevents output from corrupting the prompt
        with patch_stdout():
            user_input = session.prompt(
                HTML(f'\n<ansigreen><b>{prompt}</b></ansigreen>: '),
                multiline=True,
                prompt_continuation=_continuation_prompt,
            )
        return user_input.strip()

    except EOFError:
        # Ctrl+D
        return ""
    except KeyboardInterrupt:
        raise


async def _get_multiline_input_async(
    prompt: str = "You",
    session: Optional[PromptSession] = None
) -> str:
    """
    Get multi-line input asynchronously (non-blocking).

    This allows the event loop to continue while waiting for input,
    enabling smoother streaming and background operations.

    Args:
        prompt: Prompt label to display
        session: Optional existing PromptSession

    Returns:
        User input (potentially multi-line)
    """
    if session is None:
        session = _get_prompt_session()

    try:
        with patch_stdout():
            user_input = await session.prompt_async(
                HTML(f'\n<ansigreen><b>{prompt}</b></ansigreen>: '),
                multiline=True,
                prompt_continuation=_continuation_prompt,
            )
        return user_input.strip()

    except EOFError:
        return ""
    except KeyboardInterrupt:
        raise


async def chat_session(
    api_key: str,
    project_id: Optional[str] = None,
    save_session: bool = True,
    analyze_cwd: bool = True,
    repo_context=None,
    model: str = None,
    guided: bool = True
) -> Dict[str, Any]:
    """
    Run interactive planning chat session.

    Uses prompt_toolkit for professional input handling:
    - Full editing support (backspace, delete, arrow keys)
    - Proper paste handling
    - Input history with Ctrl+R search
    - Non-blocking async operation
    - Guided startup with smart suggestions

    Args:
        api_key: Anthropic API key
        project_id: Optional existing project ID to continue
        save_session: Whether to save conversation history
        analyze_cwd: Whether to analyze current directory codebase
        repo_context: Optional RepositoryContext from pre-analyzed repository
        model: Model name to use (defaults to Opus 4.5)
        guided: Enable guided startup with suggestions (default True)

    Returns:
        Project summary dictionary

    Raises:
        PlanningError: If session fails
    """
    from forge.cli.guided import guided_startup

    try:
        # Determine model name
        model_name = model if model else "claude-opus-4-5-20251101"

        # Initialize planning agent with specified model
        agent = PlanningAgent(api_key, model=model_name)

        # Create persistent prompt session for input history
        prompt_session = _get_prompt_session()

        # Get repo path
        repo_path = Path.cwd()

        # Use provided repo_context if available, otherwise analyze cwd
        codebase_context = None
        codebase_context_str = None
        if repo_context:
            # Use the pre-analyzed repository context
            agent.repository_context = repo_context
            agent.codebase_context = repo_context.to_prompt_context()
            codebase_context_str = repo_context.to_prompt_context()
            console.print("[green]✓[/green] Using provided repository analysis\n")
        elif analyze_cwd and not project_id:
            codebase_context = _analyze_codebase()
            if codebase_context:
                console.print("\n[green]✓[/green] Analyzed existing codebase\n")
                codebase_context_str = codebase_context.get('detailed_analysis')

        # Provide codebase context to agent if available
        if codebase_context and not repo_context:
            agent.codebase_context = codebase_context['detailed_analysis']

        # Load existing conversation if resuming
        if project_id:
            session_file = Path(f".forge/sessions/planning-{project_id}.json")
            if session_file.exists():
                agent.load_conversation(str(session_file))
                console.print(f"\n[green]✓[/green] Resumed conversation for project: {project_id}\n")
            guided = False  # Skip guided startup when resuming

        # Guided startup: show suggestions and get initial task
        initial_task = None
        if guided and not project_id:
            initial_task = await guided_startup(
                api_key=api_key,
                model=model_name,
                repo_path=repo_path,
                repo_context=codebase_context_str
            )

            if initial_task is None:
                console.print("\n[yellow]Session cancelled.[/yellow]")
                return None
        else:
            # Print traditional welcome banner
            _print_welcome()

        # Process initial task from guided startup
        if initial_task:
            first_chunk = True
            response_text = ""

            # Start inline cursor animation
            animation_task = asyncio.create_task(
                _animate_thinking_cursor()
            )

            try:
                async for chunk in agent.chat(initial_task):
                    if first_chunk:
                        # Stop animation and clear it
                        animation_task.cancel()
                        try:
                            await animation_task
                        except asyncio.CancelledError:
                            pass
                        # Clear the animation line and print response header
                        sys.stdout.write("\r" + " " * 40 + "\r")
                        sys.stdout.flush()
                        console.print("[bold green]Forge[/bold green]: ", end="")
                        first_chunk = False
                    console.print(chunk, end="", markup=False)
                    response_text += chunk
            finally:
                if not animation_task.done():
                    animation_task.cancel()

            console.print()  # New line after response

            # Check if planning is complete and prompt next steps
            if _detect_planning_complete(response_text):
                next_cmd = _show_next_steps()
                if next_cmd:
                    # Execute the selected command
                    await _handle_slash_command(
                        next_cmd,
                        agent,
                        repo_path,
                        api_key,
                        model_name
                    )

        # Main chat loop
        while True:
            try:
                # Get user input with full editing support (async, non-blocking)
                user_input = await _get_multiline_input_async("You", prompt_session)

                # Handle empty input
                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ['done', 'finish', 'complete']:
                    console.print("\n[yellow]Finishing planning session...[/yellow]")
                    break

                if user_input.lower() in ['exit', 'quit', 'q']:
                    if _confirm_exit():
                        console.print("\n[yellow]Session cancelled.[/yellow]")
                        return None
                    continue

                if user_input.lower() == 'save':
                    _save_session(agent, project_id)
                    continue

                if user_input.lower() == 'help':
                    _print_help()
                    continue

                if user_input.lower() == 'clear':
                    console.clear()
                    _print_welcome()
                    continue

                # Handle slash commands for Forge actions
                if user_input.startswith('/'):
                    handled = await _handle_slash_command(
                        user_input,
                        agent,
                        repo_path,
                        api_key,
                        model_name
                    )
                    if handled:
                        continue

                # Stream agent response with inline thinking animation
                first_chunk = True
                response_text = ""

                # Start inline cursor animation
                animation_task = asyncio.create_task(
                    _animate_thinking_cursor()
                )

                try:
                    async for chunk in agent.chat(user_input):
                        if first_chunk:
                            # Stop animation and clear it
                            animation_task.cancel()
                            try:
                                await animation_task
                            except asyncio.CancelledError:
                                pass
                            # Clear the animation line and print response header
                            sys.stdout.write("\r" + " " * 40 + "\r")
                            sys.stdout.flush()
                            console.print("[bold green]Forge[/bold green]: ", end="")
                            first_chunk = False
                        console.print(chunk, end="", markup=False)
                        response_text += chunk
                finally:
                    if not animation_task.done():
                        animation_task.cancel()

                console.print()  # New line after response

                # Check if planning is complete and prompt next steps
                if _detect_planning_complete(response_text):
                    next_cmd = _show_next_steps()
                    if next_cmd:
                        # Execute the selected command
                        await _handle_slash_command(
                            next_cmd,
                            agent,
                            repo_path,
                            api_key,
                            model_name
                        )

            except KeyboardInterrupt:
                if _confirm_exit():
                    console.print("\n[yellow]Session interrupted.[/yellow]")
                    return None
                continue

            except PlanningError as e:
                console.print(f"\n[red]✗ Error:[/red] {e}")
                continue

        # Extract project summary
        console.print("\n[bold]Analyzing conversation...[/bold]")

        with console.status("[bold green]Extracting requirements..."):
            summary = agent.get_project_summary()

        # Display summary
        _display_summary(summary)

        # Save session if requested
        if save_session:
            _save_session(agent, project_id or summary.get("project_name", "unknown"))

        # Ask to create project
        if _confirm_create_project():
            project = _create_project_from_summary(summary)
            if project:
                summary["forge_project_id"] = project.id
                console.print(f"\n[green]✓[/green] Created project: [bold]{project.id}[/bold]")

        return summary

    except Exception as e:
        logger.error(f"Chat session failed: {e}")
        console.print(f"\n[red]✗ Session failed:[/red] {e}")
        raise


def _print_welcome():
    """Print welcome banner."""
    banner = """
[bold blue]⚒ Forge v1.0.0[/bold blue] - AI Development Orchestration

[dim]I'll help you plan your software project through conversation.[/dim]

[bold]Input:[/bold]
  • Type normally with full editing support (arrow keys, backspace)
  • [cyan]Enter[/cyan] to submit • [cyan]Alt+Enter[/cyan] or [cyan]Esc,Enter[/cyan] for new line
  • [cyan]Ctrl+R[/cyan] to search input history

[bold]Commands:[/bold]
  • Type your project ideas or answer my questions
  • [cyan]done[/cyan] - Finish planning and create project
  • [cyan]save[/cyan] - Save conversation progress
  • [cyan]help[/cyan] - Show this help
  • [cyan]clear[/cyan] - Clear screen
  • [cyan]exit[/cyan] - Cancel session

Let's start planning! What would you like to build?
"""
    console.print(Panel(banner, border_style="blue", padding=(1, 2)))


def _print_help():
    """Print help information."""
    # Input controls
    input_table = Table(title="Input Controls", border_style="cyan")
    input_table.add_column("Key", style="cyan")
    input_table.add_column("Action")

    input_table.add_row("Enter", "Submit your message")
    input_table.add_row("Alt+Enter", "New line (most terminals)")
    input_table.add_row("Esc, Enter", "New line (all terminals)")
    input_table.add_row("Ctrl+R", "Search input history")
    input_table.add_row("Arrow keys", "Navigate within text")
    input_table.add_row("Ctrl+C", "Cancel/interrupt")
    input_table.add_row("Ctrl+D", "Submit (alternative)")

    console.print("\n")
    console.print(input_table)

    # Commands
    help_table = Table(title="Available Commands", border_style="blue")
    help_table.add_column("Command", style="cyan")
    help_table.add_column("Description")

    help_table.add_row("done/finish", "Complete planning and extract requirements")
    help_table.add_row("save", "Save current conversation progress")
    help_table.add_row("help", "Show this help message")
    help_table.add_row("clear", "Clear the screen")
    help_table.add_row("exit/quit", "Cancel and exit session")

    console.print(help_table)
    console.print()


def _display_summary(summary: Dict[str, Any]):
    """Display formatted project summary."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold]Project Summary[/bold]",
        border_style="green"
    ))

    # Project name and description
    console.print(f"\n[bold]Project:[/bold] {summary.get('project_name', 'Unknown')}")
    console.print(f"[bold]Description:[/bold] {summary.get('description', 'N/A')}")

    # Requirements
    if summary.get("requirements"):
        console.print("\n[bold]Requirements:[/bold]")
        for req in summary["requirements"]:
            console.print(f"  • {req}")

    # Features
    if summary.get("features"):
        console.print("\n[bold]Features:[/bold]")
        for feature in summary["features"]:
            console.print(f"  • {feature}")

    # Tech stack
    if summary.get("tech_stack"):
        console.print("\n[bold]Technology Stack:[/bold]")
        console.print(f"  {', '.join(summary['tech_stack'])}")

    # Constraints
    if summary.get("constraints"):
        console.print("\n[bold]Constraints:[/bold]")
        for constraint in summary["constraints"]:
            console.print(f"  • {constraint}")

    # Success criteria
    if summary.get("success_criteria"):
        console.print("\n[bold]Success Criteria:[/bold]")
        for criterion in summary["success_criteria"]:
            console.print(f"  • {criterion}")

    # Deployment
    if summary.get("deployment"):
        console.print(f"\n[bold]Deployment:[/bold] {summary['deployment']}")

    # Target users
    if summary.get("target_users"):
        console.print(f"[bold]Target Users:[/bold] {summary['target_users']}")

    console.print()


def _save_session(agent: PlanningAgent, project_id: Optional[str]):
    """Save conversation session."""
    try:
        # Create sessions directory
        sessions_dir = Path(".forge/sessions")
        sessions_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        if project_id:
            filename = f"planning-{project_id}.json"
        else:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"planning-{timestamp}.json"

        filepath = sessions_dir / filename

        # Save conversation
        agent.save_conversation(str(filepath))

        console.print(f"\n[green]✓[/green] Conversation saved to: {filepath}")

    except Exception as e:
        console.print(f"\n[red]✗[/red] Failed to save session: {e}")


def _confirm_exit() -> bool:
    """Confirm user wants to exit."""
    response = Prompt.ask(
        "\n[yellow]Exit without finishing?[/yellow]",
        choices=["y", "n"],
        default="n"
    )
    return response.lower() == "y"


def _confirm_create_project() -> bool:
    """Confirm user wants to create project."""
    response = Prompt.ask(
        "\n[bold]Create Forge project from this plan?[/bold]",
        choices=["y", "n"],
        default="y"
    )
    return response.lower() == "y"


def _create_project_from_summary(summary: Dict[str, Any]):
    """Create Forge project from planning summary."""
    try:
        from forge.core.state_manager import StateManager
        import re

        # Generate project ID from name
        project_name = summary.get("project_name", "planned-project")
        project_slug = re.sub(r'[^\w\s-]', '', project_name.lower())
        project_slug = re.sub(r'[-\s]+', '-', project_slug)
        timestamp = datetime.now().strftime("%Y%m%d")
        project_id = f"{project_slug}-{timestamp}"

        # Create project in state manager
        state = StateManager()
        project = state.create_project(
            project_id=project_id,
            name=project_name,
            description=summary.get("description", "Project from planning session"),
            metadata={
                "planning_summary": summary,
                "created_from": "chat_session",
                "created_at": datetime.now().isoformat()
            }
        )

        # Create checkpoint with full planning data
        state.checkpoint(
            project_id=project_id,
            stage="planning",
            state={"summary": summary},
            description="Planning session completed"
        )

        state.close()
        return project

    except Exception as e:
        console.print(f"\n[red]✗[/red] Failed to create project: {e}")
        return None


def _analyze_codebase() -> Optional[Dict[str, Any]]:
    """
    Analyze the current directory's codebase.

    Returns:
        Dictionary with codebase analysis or None if not a code project
    """
    cwd = Path.cwd()

    # Check if this looks like a code project
    indicators = {
        'package.json': 'Node.js/JavaScript',
        'pyproject.toml': 'Python (Poetry)',
        'requirements.txt': 'Python (pip)',
        'Cargo.toml': 'Rust',
        'go.mod': 'Go',
        'pom.xml': 'Java (Maven)',
        'build.gradle': 'Java/Kotlin (Gradle)',
        'Gemfile': 'Ruby',
        'composer.json': 'PHP',
        '.csproj': 'C#/.NET',
    }

    detected_type = None
    for file, lang in indicators.items():
        if list(cwd.glob(f"**/{file}")):
            detected_type = lang
            break

    if not detected_type:
        return None

    analysis = {
        'project_type': detected_type,
        'directory': str(cwd.name),
        'files': []
    }

    # Count files by type
    file_counts = {}
    code_extensions = {
        '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
        '.jsx': 'React', '.tsx': 'React/TypeScript',
        '.rs': 'Rust', '.go': 'Go', '.java': 'Java',
        '.rb': 'Ruby', '.php': 'PHP', '.cs': 'C#',
        '.cpp': 'C++', '.c': 'C', '.h': 'C/C++ Header',
        '.vue': 'Vue', '.svelte': 'Svelte'
    }

    for ext, lang in code_extensions.items():
        count = len(list(cwd.rglob(f"*{ext}")))
        if count > 0:
            file_counts[lang] = file_counts.get(lang, 0) + count

    # Find README
    readme = None
    for readme_file in ['README.md', 'README.txt', 'README']:
        readme_path = cwd / readme_file
        if readme_path.exists():
            try:
                readme = readme_path.read_text()[:1000]  # First 1000 chars
                break
            except Exception:
                pass

    # Find main entry points
    entry_points = []
    entry_files = [
        'main.py', 'app.py', '__init__.py',
        'index.js', 'server.js', 'app.js',
        'main.go', 'main.rs', 'Main.java'
    ]
    for entry in entry_files:
        if (cwd / entry).exists() or list(cwd.rglob(entry)):
            entry_points.append(entry)

    # Check for common directories
    directories = {}
    common_dirs = ['src', 'lib', 'app', 'components', 'routes', 'api', 'tests', 'docs']
    for dir_name in common_dirs:
        dir_path = cwd / dir_name
        if dir_path.exists() and dir_path.is_dir():
            file_count = len(list(dir_path.rglob('*.*')))
            directories[dir_name] = file_count

    # Build summary
    summary_parts = [f"**Project**: {cwd.name}"]
    summary_parts.append(f"**Type**: {detected_type}")

    if file_counts:
        files_summary = ", ".join([f"{count} {lang} files" for lang, count in sorted(file_counts.items(), key=lambda x: -x[1])[:3]])
        summary_parts.append(f"**Files**: {files_summary}")

    if directories:
        dirs_summary = ", ".join([f"{name}/ ({count} files)" for name, count in directories.items()])
        summary_parts.append(f"**Structure**: {dirs_summary}")

    if entry_points:
        summary_parts.append(f"**Entry Points**: {', '.join(entry_points)}")

    analysis['summary'] = "\n".join(summary_parts)

    # Build detailed analysis
    detailed = f"""# Project: {cwd.name}
Type: {detected_type}
Location: {cwd}

## File Statistics
{chr(10).join([f"- {lang}: {count} files" for lang, count in sorted(file_counts.items(), key=lambda x: -x[1])])}

## Directory Structure
{chr(10).join([f"- {name}/: {count} files" for name, count in directories.items()])}

## Entry Points
{chr(10).join([f"- {ep}" for ep in entry_points]) if entry_points else "Not detected"}
"""

    if readme:
        detailed += f"\n## README (excerpt)\n{readme}\n"

    analysis['detailed_analysis'] = detailed
    analysis['file_counts'] = file_counts
    analysis['directories'] = directories
    analysis['entry_points'] = entry_points

    return analysis


def simple_chat(api_key: str, repo_context=None, model: str = None, guided: bool = True):
    """
    Simple synchronous chat wrapper for CLI.

    Args:
        api_key: Anthropic API key
        repo_context: Optional RepositoryContext from repository analysis
        model: Model name to use (defaults to Opus 4.5)
        guided: Enable guided startup with suggestions (default True)

    Returns:
        Project summary or None
    """
    return asyncio.run(chat_session(api_key, repo_context=repo_context, model=model, guided=guided))
