"""
Interactive chat interface with Rich formatting

Provides beautiful terminal-based conversational interface for
project planning with the Forge Planning Agent.
"""

from typing import Dict, Any, Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from pathlib import Path
import asyncio
import sys
from datetime import datetime

from forge.layers.planning import PlanningAgent, PlanningError
from forge.core.state_manager import StateManager
from forge.utils.logger import logger


console = Console()


def _get_multiline_input(prompt: str = "You") -> str:
    """
    Get multi-line input from user.

    Supports:
    - Regular Enter to submit
    - Ctrl+D (Unix) or Ctrl+Z (Windows) on empty line to submit
    - Type content normally, use empty line + Ctrl+D to finish

    Args:
        prompt: Prompt to display

    Returns:
        User input (potentially multi-line)
    """
    console.print(f"\n[bold cyan]{prompt}[/bold cyan] (Enter twice or Ctrl+D to submit):")

    lines = []
    empty_line_count = 0

    try:
        while True:
            try:
                line = input()

                # If user enters empty line twice in a row, submit
                if not line.strip():
                    empty_line_count += 1
                    if empty_line_count >= 2:
                        # Remove the last empty line we just added
                        if lines and not lines[-1].strip():
                            lines.pop()
                        break
                    lines.append(line)
                else:
                    empty_line_count = 0
                    lines.append(line)

            except EOFError:
                # Ctrl+D (Unix) or Ctrl+Z (Windows)
                break

    except KeyboardInterrupt:
        raise

    return "\n".join(lines).strip()


async def chat_session(
    api_key: str,
    project_id: Optional[str] = None,
    save_session: bool = True,
    analyze_cwd: bool = True,
    repo_context=None
) -> Dict[str, Any]:
    """
    Run interactive planning chat session.

    Args:
        api_key: Anthropic API key
        project_id: Optional existing project ID to continue
        save_session: Whether to save conversation history
        analyze_cwd: Whether to analyze current directory codebase
        repo_context: Optional RepositoryContext from pre-analyzed repository

    Returns:
        Project summary dictionary

    Raises:
        PlanningError: If session fails
    """
    try:
        # Initialize planning agent
        agent = PlanningAgent(api_key)

        # Use provided repo_context if available, otherwise analyze cwd
        codebase_context = None
        if repo_context:
            # Use the pre-analyzed repository context
            agent.repository_context = repo_context
            agent.codebase_context = repo_context.to_prompt_context()
            console.print("[green]✓[/green] Using provided repository analysis\n")
        elif analyze_cwd and not project_id:
            codebase_context = _analyze_codebase()
            if codebase_context:
                console.print("\n[green]✓[/green] Analyzed existing codebase\n")
                console.print(Panel(
                    codebase_context["summary"],
                    title="[bold]Codebase Analysis[/bold]",
                    border_style="blue"
                ))

        # Print welcome banner
        _print_welcome()

        # Provide codebase context to agent if available (from old-style analysis)
        if codebase_context and not repo_context:
            # Add codebase context to agent's system prompt/context
            # The agent will have this context for the entire conversation
            agent.codebase_context = codebase_context['detailed_analysis']

        # Load existing conversation if resuming
        if project_id:
            session_file = Path(f".forge/sessions/planning-{project_id}.json")
            if session_file.exists():
                agent.load_conversation(str(session_file))
                console.print(f"\n[green]✓[/green] Resumed conversation for project: {project_id}\n")

        # Main chat loop
        while True:
            try:
                # Get user input (supports multi-line)
                user_input = _get_multiline_input("You")

                # Handle special commands
                if user_input.lower() in ['done', 'finish', 'complete']:
                    console.print("\n[yellow]Finishing planning session...[/yellow]")
                    break

                if user_input.lower() in ['exit', 'quit']:
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

                # Stream agent response
                console.print("\n[bold green]Forge[/bold green]: ", end="")

                response_text = ""
                async for chunk in agent.chat(user_input):
                    console.print(chunk, end="", markup=False)
                    response_text += chunk

                console.print()  # New line after response

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
  • Press Enter for new lines in your message
  • Press Enter twice (empty line) or Ctrl+D to submit

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
    help_table = Table(title="Available Commands", border_style="blue")
    help_table.add_column("Command", style="cyan")
    help_table.add_column("Description")

    help_table.add_row("done/finish", "Complete planning and extract requirements")
    help_table.add_row("save", "Save current conversation progress")
    help_table.add_row("help", "Show this help message")
    help_table.add_row("clear", "Clear the screen")
    help_table.add_row("exit/quit", "Cancel and exit session")

    console.print("\n")
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
            except:
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


def simple_chat(api_key: str, repo_context=None):
    """
    Simple synchronous chat wrapper for CLI.

    Args:
        api_key: Anthropic API key
        repo_context: Optional RepositoryContext from repository analysis

    Returns:
        Project summary or None
    """
    return asyncio.run(chat_session(api_key, repo_context=repo_context))
