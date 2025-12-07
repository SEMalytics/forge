"""
Rich formatted output for CLI
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.syntax import Syntax
from rich.markdown import Markdown
from typing import Dict, List, Any


console = Console()


def print_banner():
    """Print Forge banner"""
    banner = """
    ⚒ Forge - AI Development Orchestration System
    Transform natural language into production-ready code
    """
    console.print(Panel(banner, style="bold blue"))


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
