"""
Rich formatted output for CLI

Provides consistent styling and visual elements for Forge CLI.
"""

from contextlib import contextmanager
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.status import Status
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich import box
from typing import Dict, List, Any, Generator


console = Console()


# ============================================================================
# ASCII Banners
# ============================================================================

FORGE_BANNER_LARGE = """[bold blue]
    ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
    ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
    █████╗  ██║   ██║██████╔╝██║  ███╗█████╗
    ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
    ██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
    ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
[/bold blue]
[dim]AI Development Orchestration • v1.0.0[/dim]
"""

FORGE_BANNER_MINIMAL = "[bold blue]⚒ FORGE[/bold blue] [dim]• AI Development Orchestration • v1.0.0[/dim]"


# ============================================================================
# Style Constants
# ============================================================================

class ForgeStyles:
    """Consistent color scheme for Forge CLI."""

    # Stage status
    RUNNING = "bold blue"
    SUCCESS = "bold green"
    FAILED = "bold red"
    WARNING = "bold yellow"
    SKIPPED = "dim"

    # UI elements
    HEADER = "bold blue"
    PROMPT = "yellow"
    INFO = "cyan"
    MUTED = "dim"

    # Stage icons
    ICONS = {
        "running": "▶",
        "success": "✓",
        "failed": "✗",
        "warning": "⚠",
        "skipped": "⊘",
        "waiting": "⏸",
        "pending": "○",
    }


# ============================================================================
# Banner Functions
# ============================================================================

def print_banner(large: bool = False):
    """Print Forge banner.

    Args:
        large: If True, print the full ASCII art banner. Otherwise print minimal.
    """
    if large:
        console.print(FORGE_BANNER_LARGE)
    else:
        banner = """
    ⚒ Forge - AI Development Orchestration System
    Transform natural language into production-ready code
    """
        console.print(Panel(banner, style="bold blue"))


def print_pipeline_banner():
    """Print the large ASCII banner for pipeline operations."""
    console.print(FORGE_BANNER_LARGE)


def print_success(message: str):
    """Print success message"""
    console.print(f"✓ {message}", style="bold green")


def print_error(message: str):
    """Print error message"""
    console.print(f"✗ {message}", style="bold red")


def print_warning(message: str):
    """Print warning message"""
    console.print(f"⚠ {message}", style="bold yellow")


def print_info(message: str):
    """Print info message"""
    console.print(f"• {message}", style="blue")


def print_project_status(project: Dict[str, Any]):
    """Print project status"""
    table = Table(title="Project Status")

    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("ID", project.get('id', 'N/A'))
    table.add_row("Name", project.get('name', 'N/A'))
    table.add_row("Stage", project.get('stage', 'N/A'))
    table.add_row("Created", str(project.get('created_at', 'N/A')))

    console.print(table)


def print_patterns(patterns: List[Dict[str, Any]]):
    """Print pattern search results"""
    if not patterns:
        print_warning("No patterns found")
        return

    table = Table(title=f"Found {len(patterns)} patterns")

    table.add_column("Filename", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Module", style="yellow")

    for pattern in patterns:
        table.add_row(
            pattern.get('filename', 'N/A'),
            pattern.get('title', 'N/A'),
            pattern.get('module', 'N/A')
        )

    console.print(table)


def print_system_status(status: Dict[str, Any]):
    """Print system status"""
    console.print("\n[bold]System Status[/bold]\n")

    print_info(f"Patterns indexed: {status.get('pattern_count', 0)}")

    cache_stats = status.get('cache_stats', {})
    if cache_stats:
        hit_rate = cache_stats.get('hit_rate', 0) * 100
        print_info(f"Cache: {cache_stats.get('size', 0)}/{cache_stats.get('maxsize', 0)} entries")
        print_info(f"Cache hit rate: {hit_rate:.1f}%")

    config = status.get('config', {})
    if config:
        print_info(f"Backend: {config.get('backend', 'N/A')}")
        print_info(f"Search method: {config.get('search_method', 'N/A')}")


def print_code(code: str, language: str = "python"):
    """Print syntax-highlighted code"""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def print_markdown(content: str):
    """Print markdown content"""
    md = Markdown(content)
    console.print(md)


def create_progress() -> Progress:
    """Create progress bar"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    )


def confirm(question: str, default: bool = True) -> bool:
    """Ask user for confirmation"""
    default_str = "Y/n" if default else "y/N"
    response = console.input(f"{question} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ('y', 'yes')


# ============================================================================
# Spinners and Progress
# ============================================================================

@contextmanager
def stage_spinner(message: str) -> Generator[Status, None, None]:
    """
    Context manager for stage spinners.

    Usage:
        with stage_spinner("Running tests..."):
            run_tests()

    Args:
        message: Message to display with spinner
    """
    with console.status(f"[bold blue]{message}[/bold blue]", spinner="dots") as status:
        yield status


def create_task_progress() -> Progress:
    """Create progress bar for task-based operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TextColumn("[dim]{task.completed}/{task.total}[/dim]"),
        console=console,
    )


# ============================================================================
# Pipeline Visualization
# ============================================================================

def print_pipeline_header(project_id: str, policy: str, stages: List[str]):
    """Print pipeline header with project info."""
    stages_str = " → ".join(stages)

    content = f"""[bold]Project:[/bold] {project_id}
[bold]Policy:[/bold]  {policy}
[bold]Stages:[/bold]  {stages_str}"""

    console.print(Panel(
        content,
        border_style="blue",
        box=box.ROUNDED,
    ))
    console.print()


def print_stage_start(stage: str):
    """Print stage start indicator."""
    icon = ForgeStyles.ICONS["running"]
    console.print(f"[{ForgeStyles.RUNNING}]{icon} {stage.upper()}[/{ForgeStyles.RUNNING}]")


def print_stage_success(stage: str, message: str = "", duration: float = 0):
    """Print stage success indicator."""
    icon = ForgeStyles.ICONS["success"]
    duration_str = f" [dim]({duration:.1f}s)[/dim]" if duration > 0 else ""
    msg_str = f" {message}" if message else ""
    console.print(f"  [{ForgeStyles.SUCCESS}]{icon}{msg_str}{duration_str}[/{ForgeStyles.SUCCESS}]")


def print_stage_failed(stage: str, message: str = ""):
    """Print stage failure indicator."""
    icon = ForgeStyles.ICONS["failed"]
    msg_str = f" {message}" if message else ""
    console.print(f"  [{ForgeStyles.FAILED}]{icon}{msg_str}[/{ForgeStyles.FAILED}]")


def print_checkpoint_prompt(stage: str, message: str, options: List[str]) -> str:
    """Print checkpoint prompt and get user decision.

    Args:
        stage: Current stage name
        message: Prompt message
        options: List of valid options

    Returns:
        User's choice
    """
    icon = ForgeStyles.ICONS["waiting"]
    console.print(f"\n[{ForgeStyles.WARNING}]{icon} Checkpoint: {stage}[/{ForgeStyles.WARNING}]")
    console.print(f"  {message}")
    options_str = " | ".join(options)
    console.print(f"  [dim]Options: {options_str}[/dim]")

    while True:
        choice = console.input("  [yellow]Decision:[/yellow] ").strip().lower()
        if choice in [o.lower() for o in options] or choice.startswith("override:"):
            return choice
        console.print(f"  [red]Invalid choice. Options: {options_str}[/red]")


def print_pipeline_summary(results: List[Dict[str, Any]], total_duration: float, succeeded: bool):
    """Print pipeline summary panel.

    Args:
        results: List of stage results with keys: stage, success, duration_seconds
        total_duration: Total pipeline duration
        succeeded: Whether pipeline succeeded overall
    """
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("Stage", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Duration", justify="right")

    for r in results:
        icon = ForgeStyles.ICONS["success"] if r.get("success") else ForgeStyles.ICONS["failed"]
        color = "green" if r.get("success") else "red"
        duration = r.get("duration_seconds", 0)
        table.add_row(
            r.get("stage", "unknown").upper(),
            f"[{color}]{icon}[/{color}]",
            f"{duration:.1f}s"
        )

    stages_run = len(results)
    stages_passed = sum(1 for r in results if r.get("success"))

    if succeeded:
        result_line = f"[green]{stages_passed}/{stages_run} passed[/green]"
        border_style = "green"
    else:
        failed_stage = next((r.get("stage", "unknown") for r in results if not r.get("success")), "unknown")
        result_line = f"[red]Failed at {failed_stage}[/red]"
        border_style = "red"

    content = Group(
        table,
        "",
        f"[bold]Total:[/bold] {total_duration:.1f}s across {stages_run} stages",
        f"[bold]Result:[/bold] {result_line}",
    )

    console.print(Panel(
        content,
        title="[bold]Pipeline Summary[/bold]",
        border_style=border_style,
    ))
