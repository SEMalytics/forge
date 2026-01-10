"""
User-friendly error handling for Forge CLI.

Provides consistent error display with helpful hints and context.
"""

from typing import Optional, Dict
from rich.console import Console
from rich.panel import Panel


class ForgeErrorHandler:
    """Consistent error display for CLI with helpful hints."""

    # Common error patterns and their helpful hints
    ERROR_HINTS: Dict[str, str] = {
        "ANTHROPIC_API_KEY": "Set your API key: export ANTHROPIC_API_KEY=sk-...",
        "CODEGEN_API_KEY": "Set your API key: export CODEGEN_API_KEY=...",
        "Docker": "Start Docker Desktop or run: sudo systemctl start docker",
        "not found": "Run 'forge doctor' to check your setup",
        "timeout": "Try increasing timeout with --timeout flag",
        "rate limit": "Wait a moment and retry, or check your API quota",
        "connection": "Check your internet connection and try again",
        "permission": "Check file permissions or run with appropriate access",
        "No such file": "Verify the file path exists and is accessible",
        "ModuleNotFoundError": "Missing dependency. Try: pip install -e .",
        "ImportError": "Missing dependency. Try: pip install -e .",
        "Project not found": "Run 'forge status' to see available projects",
        "No planning data": "Run 'forge chat' first to create a planning session",
    }

    @classmethod
    def get_hint(cls, error_msg: str) -> Optional[str]:
        """Find a relevant hint for an error message.

        Args:
            error_msg: The error message to find a hint for

        Returns:
            A helpful hint string, or None if no hint applies
        """
        error_lower = error_msg.lower()
        for pattern, hint in cls.ERROR_HINTS.items():
            if pattern.lower() in error_lower:
                return hint
        return None

    @classmethod
    def display(cls, error: Exception, console: Optional[Console] = None, debug: bool = False):
        """Display error with helpful context.

        Args:
            error: The exception to display
            console: Rich console to use (creates new one if None)
            debug: If True, show full traceback
        """
        if console is None:
            console = Console()

        error_msg = str(error)
        error_type = type(error).__name__

        # Build error content
        content_lines = [f"[red]{error_msg}[/red]"]

        # Add hint if available
        hint = cls.get_hint(error_msg)
        if hint:
            content_lines.append("")
            content_lines.append(f"[yellow]💡 {hint}[/yellow]")

        # Show debug info if requested
        if debug:
            content_lines.append("")
            content_lines.append(f"[dim]Type: {error_type}[/dim]")

        content = "\n".join(content_lines)

        console.print(Panel(
            content,
            title="[bold red]Error[/bold red]",
            border_style="red",
        ))

        # Print full traceback in debug mode
        if debug:
            console.print_exception(show_locals=True)

    @classmethod
    def wrap_command(cls, func, console: Optional[Console] = None, debug: bool = False):
        """Decorator to wrap CLI commands with error handling.

        Usage:
            @ForgeErrorHandler.wrap_command
            def my_command():
                ...

        Args:
            func: The function to wrap
            console: Rich console to use
            debug: If True, show full tracebacks
        """
        import functools

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                if console:
                    console.print("\n[yellow]Operation cancelled by user[/yellow]")
                return 1
            except Exception as e:
                cls.display(e, console=console, debug=debug)
                return 1

        return wrapper
