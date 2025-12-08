"""
Forge CLI using Click
"""

import click
from rich.console import Console
from pathlib import Path
import sys

from forge.core.config import ForgeConfig
from forge.core.orchestrator import Orchestrator
from forge.cli.output import (
    print_banner,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_project_status,
    print_patterns,
    print_system_status,
    console
)
from forge.utils.logger import setup_logger

# Setup logger
logger = setup_logger()


@click.group()
@click.version_option(version="1.0.0")
@click.pass_context
def cli(ctx):
    """⚒ Forge - AI Development Orchestration System"""
    # Store orchestrator in context
    try:
        ctx.ensure_object(dict)
        config = ForgeConfig.load()
        ctx.obj['orchestrator'] = Orchestrator(config)
        ctx.obj['config'] = config
    except Exception as e:
        print_error(f"Failed to initialize Forge: {e}")
        sys.exit(1)


@cli.command()
def doctor():
    """Check system dependencies and configuration"""
    print_banner()
    console.print("\n🔍 Checking Forge installation...\n")

    # Check Python version
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    else:
        print_error(f"Python 3.11+ required (found {version.major}.{version.minor})")

    # Check dependencies
    deps = ['git', 'docker']
    for dep in deps:
        import shutil
        if shutil.which(dep):
            print_success(f"{dep} installed")
        else:
            print_warning(f"{dep} not found (optional)")

    # Check patterns directory
    # Try to find patterns directory relative to the repository root
    patterns_dir = Path(__file__).parent.parent.parent.parent / "patterns"
    if patterns_dir.exists():
        count = len(list(patterns_dir.glob("*.md")))
        if count > 0:
            print_success(f"Pattern library ({count} files)")
        else:
            print_warning(f"No .md files found in {patterns_dir}")
    else:
        print_error(f"Patterns directory not found at {patterns_dir}")
        print_info("Patterns should be in the repository at ./patterns/")

    # Check CE plugin (optional - Forge has built-in CE-style planning)
    # Look for plugin inside the forge directory
    repo_root = Path(__file__).parent.parent.parent.parent
    ce_dir = repo_root / "compound-engineering"

    if ce_dir.exists():
        plan_file = ce_dir / "plugins" / "compound-engineering" / "commands" / "workflows" / "plan.md"
        if plan_file.exists():
            print_success("Compound Engineering plugin (for Claude Code integration)")
        else:
            print_warning("compound-engineering/ exists but structure is incomplete")
    else:
        print_info("Using built-in CE-style planning (clone plugin for Claude Code integration)")

    # Check Forge directories
    forge_dir = Path(".forge")
    if forge_dir.exists():
        print_success(f"Forge data directory: {forge_dir}")
    else:
        print_info("Forge data directory will be created on first use")

    console.print("\n✨ Forge health check complete!\n")


@cli.command()
@click.argument('project_name')
@click.option('--description', '-d', default="", help="Project description")
@click.pass_context
def init(ctx, project_name, description):
    """Initialize a new Forge project"""
    orchestrator = ctx.obj['orchestrator']

    try:
        project = orchestrator.create_project(
            name=project_name,
            description=description
        )

        console.print()
        print_success(f"Initialized project: {project.name}")
        print_info(f"ID: {project.id}")
        print_info(f"Stage: {project.stage}")
        console.print()

    except Exception as e:
        print_error(f"Failed to initialize project: {e}")
        sys.exit(1)


@cli.command()
@click.argument('project_id', required=False)
@click.pass_context
def status(ctx, project_id):
    """Show project status or list all projects"""
    orchestrator = ctx.obj['orchestrator']

    try:
        # If no project_id provided, list all projects
        if not project_id:
            from forge.core.state_manager import StateManager
            state = StateManager()

            projects = state.execute(
                "SELECT id, name, stage, created_at FROM projects ORDER BY created_at DESC"
            ).fetchall()

            if not projects:
                console.print("\n[yellow]No projects found.[/yellow]")
                console.print("\nCreate a project with: [cyan]forge init <project-name>[/cyan]")
                console.print("Or start planning: [cyan]forge chat[/cyan]\n")
                return

            # Display projects table
            from rich.table import Table

            console.print()
            table = Table(title="Forge Projects", border_style="blue")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="bold")
            table.add_column("Stage", style="yellow")
            table.add_column("Created", style="dim")

            for project in projects:
                # Format created_at timestamp
                created = project[3] if project[3] else "Unknown"
                if len(created) > 19:  # Has full timestamp
                    created = created[:19].replace('T', ' ')

                table.add_row(project[0], project[1], project[2], created)

            console.print(table)
            console.print(f"\n💡 Tip: Use [cyan]forge status <project-id>[/cyan] for detailed status\n")
            state.close()
            return

        # Show specific project status
        project = orchestrator.get_project(project_id)

        if not project:
            print_error(f"Project not found: {project_id}")
            sys.exit(1)

        console.print()
        print_project_status({
            'id': project.id,
            'name': project.name,
            'stage': project.stage,
            'created_at': project.created_at
        })
        console.print()

    except Exception as e:
        print_error(f"Failed to get project status: {e}")
        sys.exit(1)


@cli.command()
@click.argument('query')
@click.option('--max-results', '-n', default=10, help="Maximum results to return")
@click.option('--method', '-m', type=click.Choice(['keyword', 'semantic', 'hybrid']),
              default='hybrid', help="Search method")
@click.pass_context
def search(ctx, query, max_results, method):
    """Search KnowledgeForge patterns"""
    orchestrator = ctx.obj['orchestrator']

    try:
        results = orchestrator.search_patterns(query, max_results, method)

        console.print()
        print_patterns(results)
        console.print()

    except Exception as e:
        print_error(f"Search failed: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def info(ctx):
    """Show system information and statistics"""
    orchestrator = ctx.obj['orchestrator']

    try:
        status = orchestrator.get_system_status()

        console.print()
        print_system_status(status)
        console.print()

    except Exception as e:
        print_error(f"Failed to get system info: {e}")
        sys.exit(1)


@cli.command()
@click.option('--global-config', '-g', is_flag=True, help="Create global config")
def config(global_config):
    """Create default configuration file"""
    try:
        if global_config:
            config_path = Path.home() / ".forge" / "config.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            config_path = Path.cwd() / "forge.yaml"

        ForgeConfig.create_default(config_path)

        console.print()
        print_success(f"Created configuration file: {config_path}")
        console.print()

    except Exception as e:
        print_error(f"Failed to create config: {e}")
        sys.exit(1)


@cli.command()
@click.option('--project-id', '-p', help="Resume existing project session")
def chat(project_id):
    """Start interactive planning session"""
    import os
    from forge.cli.interactive import simple_chat

    # Get API key from environment
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print_error("ANTHROPIC_API_KEY environment variable not set")
        console.print("\n[yellow]Set your API key:[/yellow]")
        console.print("  export ANTHROPIC_API_KEY='your-key-here'")
        console.print("\nOr add to your shell profile (~/.zshrc or ~/.bashrc)")
        sys.exit(1)

    try:
        # Start interactive chat session
        summary = simple_chat(api_key)

        if summary:
            console.print("\n[green]✓[/green] Planning session completed successfully!")
        else:
            console.print("\n[yellow]Session cancelled[/yellow]")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Session interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        print_error(f"Chat session failed: {e}")
        logger.exception("Chat session error")
        sys.exit(1)


@cli.command()
@click.argument('description')
@click.option('--tech-stack', '-t', multiple=True, help="Technologies to use (can specify multiple)")
@click.option('--project-id', '-p', help="Save decomposition to project")
@click.option('--save', '-s', is_flag=True, help="Save plan to file")
@click.option('--visualize', '-v', is_flag=True, help="Show dependency graph visualization")
def decompose(description, tech_stack, project_id, save, visualize):
    """Generate project task plan from description"""
    from forge.knowledgeforge.pattern_store import PatternStore
    from forge.layers.decomposition import TaskDecomposer
    from rich.table import Table
    from rich.panel import Panel

    try:
        console.print("\n[bold blue]⚒ Forge Task Decomposition[/bold blue]\n")

        # Initialize decomposer
        console.print("[dim]Initializing task decomposer...[/dim]")
        store = PatternStore()
        decomposer = TaskDecomposer(pattern_store=store)

        # Perform decomposition
        console.print(f"[dim]Analyzing: {description}[/dim]")
        tech_list = list(tech_stack) if tech_stack else None

        with console.status("[bold green]Decomposing project..."):
            tasks = decomposer.decompose(
                project_description=description,
                tech_stack=tech_list,
                project_id=project_id
            )

        # Display summary
        summary = decomposer.get_task_summary(tasks)

        console.print(Panel(
            f"[bold]Generated {summary['total_tasks']} tasks[/bold]\n"
            f"Patterns: {summary['total_patterns']} | "
            f"Avg Dependencies: {summary['avg_dependencies']:.1f} | "
            f"Max Depth: {summary['max_dependency_depth']}",
            title="Summary",
            border_style="green"
        ))

        # Display tasks in table
        table = Table(title="\nProject Tasks", border_style="blue")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="bold")
        table.add_column("Priority", justify="center")
        table.add_column("Complexity", justify="center")
        table.add_column("Dependencies", style="yellow")
        table.add_column("KF Patterns", style="green")

        for task in tasks:
            deps = ", ".join(task.dependencies) if task.dependencies else "-"
            patterns = ", ".join(task.kf_patterns[:2]) if task.kf_patterns else "-"
            if len(task.kf_patterns) > 2:
                patterns += f" (+{len(task.kf_patterns) - 2})"

            # Color code complexity
            complexity_color = {
                "low": "[green]low[/green]",
                "medium": "[yellow]medium[/yellow]",
                "high": "[red]high[/red]"
            }.get(task.estimated_complexity, task.estimated_complexity)

            table.add_row(
                task.id,
                task.title[:50],
                str(task.priority),
                complexity_color,
                deps[:30],
                patterns[:40]
            )

        console.print(table)

        # Show detailed task information
        console.print("\n[bold]Task Details:[/bold]\n")
        for task in tasks:
            console.print(f"[cyan]{task.id}[/cyan]: {task.title}")
            console.print(f"  [dim]{task.description}[/dim]")

            if task.dependencies:
                console.print(f"  [yellow]Dependencies:[/yellow] {', '.join(task.dependencies)}")

            if task.acceptance_criteria:
                console.print(f"  [green]Acceptance Criteria:[/green]")
                for criterion in task.acceptance_criteria[:3]:
                    console.print(f"    • {criterion}")

            if task.kf_patterns:
                console.print(f"  [blue]KF Patterns:[/blue] {', '.join(task.kf_patterns)}")

            if task.tags:
                console.print(f"  [magenta]Tags:[/magenta] {', '.join(task.tags)}")

            console.print()

        # Show dependency visualization if requested
        if visualize:
            console.print("\n[bold]Dependency Graph:[/bold]\n")
            graph = decomposer.visualize_dependency_graph(tasks)
            console.print(Panel(graph, border_style="cyan"))

        # Save to file if requested
        if save:
            import json
            from datetime import datetime

            # Generate filename
            slug = description.lower()[:30].replace(" ", "-")
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"plan-{slug}-{timestamp}.json"

            # Save plan
            plan_data = {
                "description": description,
                "tech_stack": tech_list,
                "generated_at": datetime.now().isoformat(),
                "tasks": [task.to_dict() for task in tasks],
                "summary": summary
            }

            Path(filename).write_text(json.dumps(plan_data, indent=2))
            console.print(f"\n[green]✓[/green] Plan saved to: [bold]{filename}[/bold]")

        # Show project info if saved
        if project_id:
            console.print(f"\n[green]✓[/green] Decomposition saved to project: [bold]{project_id}[/bold]")

        console.print()

        # Cleanup
        decomposer.close()

    except Exception as e:
        print_error(f"Task decomposition failed: {e}")
        logger.exception("Decomposition error")
        sys.exit(1)


@cli.command()
@click.option('--project-id', '-p', required=True, help="Project ID to build")
@click.option('--backend', '-b', type=click.Choice(['codegen_api', 'claude_code']), help="Generator backend")
@click.option('--parallel/--sequential', default=True, help="Enable parallel execution")
@click.option('--max-parallel', default=3, help="Maximum parallel tasks")
def build(project_id, backend, parallel, max_parallel):
    """Build project from task plan"""
    import os
    import asyncio
    from forge.generators.factory import GeneratorFactory, GeneratorBackend
    from forge.layers.generation import GenerationOrchestrator
    from forge.layers.decomposition import TaskDecomposer
    from forge.core.state_manager import StateManager

    try:
        console.print("\n[bold blue]⚒ Forge Build System[/bold blue]\n")

        # Load project
        state = StateManager()
        project = state.get_project(project_id)

        if not project:
            print_error(f"Project not found: {project_id}")
            sys.exit(1)

        console.print(f"[bold]Project:[/bold] {project.name}")
        console.print(f"[bold]Stage:[/bold] {project.stage}\n")

        # Get tasks for project
        # First check if tasks exist in state
        tasks_data = state.execute(
            "SELECT * FROM tasks WHERE project_id = ?",
            (project_id,)
        ).fetchall()

        if not tasks_data:
            print_warning("No tasks found. Run 'forge decompose' first.")
            sys.exit(1)

        # Convert to Task objects
        from forge.integrations.compound_engineering import Task
        tasks = []
        for row in tasks_data:
            metadata = eval(row[6]) if row[6] else {}
            tasks.append(Task(
                id=row[1],
                title=row[2],
                description=row[3],
                dependencies=eval(row[4]) if row[4] else [],
                priority=1,
                kf_patterns=metadata.get('kf_patterns', [])
            ))

        console.print(f"Found {len(tasks)} tasks to build\n")

        # Auto-detect or use specified backend
        if backend:
            backend_enum = GeneratorBackend(backend)
        else:
            backend_enum = GeneratorFactory.detect_best_backend()
            if not backend_enum:
                print_error("No generator backend available")
                console.print("\nSet CODEGEN_API_KEY or install Claude CLI")
                sys.exit(1)

        console.print(f"[bold]Backend:[/bold] {backend_enum.value}\n")

        # Create generator
        if backend_enum == GeneratorBackend.CODEGEN_API:
            api_key = os.getenv('CODEGEN_API_KEY')
            if not api_key:
                print_error("CODEGEN_API_KEY environment variable not set")
                sys.exit(1)

            generator = GeneratorFactory.create(
                backend_enum,
                api_key=api_key,
                org_id=os.getenv('CODEGEN_ORG_ID')
            )
        else:
            generator = GeneratorFactory.create(backend_enum)

        # Create orchestrator
        max_par = max_parallel if parallel else 1
        orchestrator = GenerationOrchestrator(
            generator=generator,
            state_manager=state,
            console=console,
            max_parallel=max_par
        )

        # Get project context
        project_context = project.description or "Software project"

        # Execute generation
        console.print("[bold]Starting code generation...[/bold]\n")

        async def run_generation():
            return await orchestrator.generate_project(
                project_id=project_id,
                tasks=tasks,
                project_context=project_context
            )

        results = asyncio.run(run_generation())

        # Check success
        success_count = sum(1 for r in results.values() if r.success)

        if success_count == len(results):
            console.print("[green]✓[/green] All tasks completed successfully!")
        elif success_count > 0:
            console.print(f"[yellow]⚠[/yellow] {success_count}/{len(results)} tasks completed")
        else:
            console.print("[red]✗[/red] All tasks failed")
            sys.exit(1)

        # Cleanup
        orchestrator.close()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Build interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        print_error(f"Build failed: {e}")
        logger.exception("Build error")
        sys.exit(1)


@cli.command()
@click.option('--project-id', '-p', required=True, help="Project ID to test")
@click.option('--coverage', default=80.0, help="Minimum coverage percentage")
@click.option('--security/--no-security', default=True, help="Run security scan")
@click.option('--performance/--no-performance', default=False, help="Run performance tests")
@click.option('--docker/--no-docker', default=True, help="Use Docker isolation")
def test(project_id, coverage, security, performance, docker):
    """Run comprehensive tests for project"""
    import asyncio
    from forge.core.state_manager import StateManager
    from forge.layers.testing import TestingOrchestrator, TestingConfig

    try:
        console.print("\n[bold blue]⚒ Forge Testing System[/bold blue]\n")

        # Load project
        state = StateManager()
        project = state.get_project(project_id)

        if not project:
            print_error(f"Project not found: {project_id}")
            sys.exit(1)

        console.print(f"[bold]Project:[/bold] {project.name}")
        console.print(f"[bold]Stage:[/bold] {project.stage}\n")

        # Get generated code files from build artifacts
        # In a real scenario, load from file system or state
        code_files = {}

        # Load code files from project output directory
        project_output_dir = Path(".forge") / "output" / project_id
        if project_output_dir.exists():
            for file_path in project_output_dir.rglob("*.py"):
                try:
                    relative_path = file_path.relative_to(project_output_dir)
                    code_files[str(relative_path)] = file_path.read_text()
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")

        if not code_files:
            print_warning("No code files found. Generate code first with 'forge build'.")
            console.print("\nRun: forge build -p <project-id>")
            sys.exit(1)

        console.print(f"Found {len(code_files)} code files to test\n")

        # Create testing configuration
        config = TestingConfig(
            run_unit_tests=True,
            run_integration_tests=True,
            run_security_scan=security,
            run_performance_tests=performance,
            generate_tests=True,
            use_docker=docker,
            min_coverage=coverage,
            security_required=security
        )

        # Create orchestrator
        orchestrator = TestingOrchestrator(
            config=config,
            console=console
        )

        # Get tech stack from project
        tech_stack = []
        if hasattr(project, 'metadata'):
            tech_stack = project.metadata.get('tech_stack', [])

        # Run tests
        console.print("[bold]Starting comprehensive testing...[/bold]\n")

        async def run_tests():
            return await orchestrator.test_project(
                project_id=project_id,
                code_files=code_files,
                tech_stack=tech_stack,
                project_context=project.description or ""
            )

        report = asyncio.run(run_tests())

        # Exit with appropriate code
        if report.all_passed and report.security_passed and report.performance_passed:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Testing interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        print_error(f"Testing failed: {e}")
        logger.exception("Testing error")
        sys.exit(1)


@cli.command()
@click.option('--project-id', '-p', required=True, help="Project ID to iterate on")
@click.option('--max-iterations', default=5, help="Maximum iteration attempts")
def iterate(project_id, max_iterations):
    """Iterate on project until tests pass"""
    import asyncio
    from forge.core.state_manager import StateManager
    from forge.layers.review import ReviewLayer
    from forge.layers.testing import TestingConfig

    try:
        console.print("\n[bold blue]⚒ Forge Iterative Refinement[/bold blue]\n")

        # Load project
        state = StateManager()
        project = state.get_project(project_id)

        if not project:
            print_error(f"Project not found: {project_id}")
            sys.exit(1)

        console.print(f"[bold]Project:[/bold] {project.name}")
        console.print(f"[bold]Max Iterations:[/bold] {max_iterations}\n")

        # Load code files from project output directory
        project_output_dir = Path(".forge") / "output" / project_id
        code_files = {}

        if project_output_dir.exists():
            for file_path in project_output_dir.rglob("*.py"):
                try:
                    relative_path = file_path.relative_to(project_output_dir)
                    code_files[str(relative_path)] = file_path.read_text()
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")

        if not code_files:
            print_warning("No code files found. Generate code first with 'forge build'.")
            console.print("\nRun: forge build -p <project-id>")
            sys.exit(1)

        console.print(f"Found {len(code_files)} code files\n")

        # Create review layer
        review = ReviewLayer(
            testing_config=TestingConfig(
                run_unit_tests=True,
                run_integration_tests=True,
                run_security_scan=True,
                run_performance_tests=False,
                generate_tests=True,
                use_docker=True,
                min_coverage=80.0,
                security_required=True
            ),
            console=console,
            state_manager=state
        )

        # Get tech stack from project
        tech_stack = []
        if hasattr(project, 'metadata'):
            tech_stack = project.metadata.get('tech_stack', [])

        # Run iteration
        console.print("[bold]Starting iterative refinement...[/bold]\n")

        async def run_iteration():
            return await review.iterate_until_passing(
                project_id=project_id,
                code_files=code_files,
                tech_stack=tech_stack,
                project_context=project.description or "",
                max_iterations=max_iterations,
                output_dir=project_output_dir
            )

        summary = asyncio.run(run_iteration())

        # Display final summary
        console.print("\n[bold]Final Summary:[/bold]\n")

        from rich.table import Table
        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value")

        table.add_row("Total Iterations", str(summary.total_iterations))
        table.add_row("Final Status", summary.final_status.upper())
        table.add_row("Success", "✓ Yes" if summary.success else "✗ No")
        table.add_row("Total Duration", f"{summary.total_duration_seconds:.1f}s")

        console.print(table)
        console.print()

        # Show learning stats
        if summary.learning_database_updated:
            stats = review.get_learning_statistics()
            console.print(f"[dim]Learning Database Updated:[/dim]")
            console.print(f"  [dim]Total Sessions: {stats['total_sessions']}[/dim]")
            console.print(f"  [dim]Success Rate: {stats['success_rate']:.1%}[/dim]")
            console.print(f"  [dim]Patterns Learned: {stats['total_patterns']}[/dim]")
            console.print()

        # Iteration breakdown
        if summary.iterations:
            console.print("[bold]Iteration Breakdown:[/bold]")
            for iteration in summary.iterations:
                status = "✓" if iteration.tests_failed == 0 else "✗"
                console.print(
                    f"  {status} Iteration {iteration.iteration_number}: "
                    f"{iteration.tests_passed} passed, "
                    f"{iteration.tests_failed} failed, "
                    f"{iteration.fixes_successful} fixes applied"
                )
            console.print()

        # Exit with appropriate code
        if summary.success:
            console.print("[bold green]✓ All tests passing![/bold green]")
            sys.exit(0)
        else:
            console.print("[bold yellow]⚠ Tests still failing after {summary.total_iterations} iterations[/bold yellow]")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Iteration interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        print_error(f"Iteration failed: {e}")
        logger.exception("Iteration error")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


@cli.command()
@click.option('--project-id', '-p', required=True, help="Project ID")
@click.option('--platform', type=click.Choice(['flyio', 'vercel', 'aws', 'docker', 'k8s']), required=True, help="Deployment platform")
@click.option('--runtime', default='python', help="Runtime (python, node, go)")
@click.option('--port', default=8080, type=int, help="Application port")
@click.option('--region', help="Deployment region")
@click.option('--create-pr', is_flag=True, help="Create PR with deployment configs")
def deploy(project_id, platform, runtime, port, region, create_pr):
    """Deploy project to platform"""
    from forge.layers.deployment import DeploymentGenerator, DeploymentConfig, Platform
    from forge.git.repository import ForgeRepository
    from forge.git.commits import CommitStrategy, CommitType, ConventionalCommit
    from forge.integrations.github_client import GitHubClient
    from pathlib import Path

    console.print(f"\n[bold cyan]Deploying {project_id} to {platform}[/bold cyan]\n")

    try:
        # Load project path
        project_path = Path(".forge/output") / project_id

        if not project_path.exists():
            print_error(f"Project not found: {project_id}")
            sys.exit(1)

        # Detect entry point
        if runtime == "python":
            entry_point = "app.py"
            start_command = f"python {entry_point}"
        elif runtime == "node":
            entry_point = "index.js"
            start_command = "node index.js"
        elif runtime == "go":
            entry_point = "main.go"
            start_command = "./main"
        else:
            entry_point = "main"
            start_command = None

        # Create deployment config
        platform_enum = Platform(platform)

        config = DeploymentConfig(
            platform=platform_enum,
            project_name=project_id,
            runtime=runtime,
            entry_point=entry_point,
            environment_vars={
                "PORT": str(port),
                "NODE_ENV": "production"
            },
            start_command=start_command,
            port=port,
            region=region
        )

        # Generate configs
        generator = DeploymentGenerator(project_path)
        generated_files = generator.generate_configs(config)

        console.print("[bold green]✓[/bold green] Generated deployment files:")
        for file_path in generated_files:
            console.print(f"  • {file_path.relative_to(project_path)}")

        # Create PR if requested
        if create_pr:
            try:
                repo = ForgeRepository(project_path)

                # Create feature branch
                branch_name = repo.create_feature_branch(f"deploy-{platform}")

                # Add files
                file_paths = [str(f.relative_to(project_path)) for f in generated_files]
                repo.add_files(file_paths)

                # Create commit
                commit = ConventionalCommit(
                    type=CommitType.BUILD,
                    description=f"add {platform} deployment configuration",
                    scope="deploy",
                    body=f"Generated deployment configs for {platform}:\n" + "\n".join(f"- {f}" for f in file_paths)
                )

                repo.commit(commit.format())

                # Push branch
                repo.push(set_upstream=True)

                # Create PR
                github_info = repo.parse_github_repo()
                if github_info:
                    owner, repo_name = github_info
                    github = GitHubClient(f"{owner}/{repo_name}")

                    pr = github.create_pr_with_checklist(
                        title=f"feat(deploy): add {platform} deployment",
                        description=f"Adds {platform} deployment configuration for {project_id}",
                        head=branch_name,
                        base="main",
                        checklist_items=[
                            f"Review {platform} configuration",
                            "Test deployment locally",
                            "Verify environment variables",
                            "Check resource limits"
                        ],
                        labels=["deployment", platform]
                    )

                    console.print(f"\n[bold green]✓[/bold green] Created PR: {pr.html_url}")
                else:
                    console.print("\n[yellow]⚠[/yellow] Could not parse GitHub repo, skipping PR creation")

            except Exception as e:
                console.print(f"\n[yellow]⚠[/yellow] Could not create PR: {e}")

        # Show next steps
        console.print(f"\n[bold]Next Steps:[/bold]")

        if platform == "flyio":
            console.print("  1. Install flyctl: curl -L https://fly.io/install.sh | sh")
            console.print(f"  2. Create app: fly apps create {project_id}")
            console.print("  3. Deploy: fly deploy")
        elif platform == "vercel":
            console.print("  1. Install Vercel CLI: npm i -g vercel")
            console.print("  2. Deploy: vercel")
        elif platform == "aws":
            console.print("  1. Install AWS SAM CLI")
            console.print("  2. Build: sam build")
            console.print("  3. Deploy: sam deploy --guided")
        elif platform == "docker":
            console.print("  1. Build: docker-compose build")
            console.print("  2. Run: docker-compose up")
        elif platform == "k8s":
            console.print("  1. Build image: docker build -t {project_id}:latest .")
            console.print("  2. Apply manifests: kubectl apply -f k8s/")

    except Exception as e:
        print_error(f"Deployment failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--project-id', '-p', required=True, help="Project ID")
@click.option('--title', help="PR title (auto-generated if not provided)")
@click.option('--base', default='main', help="Base branch")
@click.option('--draft', is_flag=True, help="Create as draft PR")
@click.option('--reviewers', help="Comma-separated list of reviewers")
@click.option('--labels', help="Comma-separated list of labels")
def pr(project_id, title, base, draft, reviewers, labels):
    """Create pull request for project"""
    from forge.git.repository import ForgeRepository
    from forge.git.commits import CommitStrategy, ConventionalCommit
    from forge.integrations.github_client import GitHubClient
    from pathlib import Path

    console.print(f"\n[bold cyan]Creating PR for {project_id}[/bold cyan]\n")

    try:
        project_path = Path(".forge/output") / project_id

        if not project_path.exists():
            # Try current directory
            project_path = Path(".")

        repo = ForgeRepository(project_path)

        # Get current status
        status = repo.get_status()

        console.print(f"[bold]Current branch:[/bold] {status.branch}")
        console.print(f"[bold]Staged files:[/bold] {len(status.staged_files)}")
        console.print(f"[bold]Unstaged files:[/bold] {len(status.unstaged_files)}")

        # Check if on forge branch
        if not status.branch.startswith("forge/"):
            console.print("\n[yellow]⚠[/yellow] Not on a forge/* branch. Create one first:")
            console.print(f"  forge checkout -b forge/{project_id}")
            sys.exit(1)

        # Create commit if there are changes
        if status.unstaged_files or status.untracked_files:
            console.print("\n[yellow]→[/yellow] Adding and committing changes...")

            # Add all files
            all_files = status.unstaged_files + status.untracked_files
            repo.add_files(all_files)

            # Generate commit message
            commit = CommitStrategy.from_changes(all_files)
            repo.commit(commit.format())

            console.print(f"[bold green]✓[/bold green] Created commit: {commit.description}")

        # Push branch
        console.print("\n[yellow]→[/yellow] Pushing branch...")
        repo.push(set_upstream=True)
        console.print("[bold green]✓[/bold green] Pushed to remote")

        # Get GitHub repo info
        github_info = repo.parse_github_repo()
        if not github_info:
            print_error("Could not parse GitHub repository from remote URL")
            sys.exit(1)

        owner, repo_name = github_info
        github = GitHubClient(f"{owner}/{repo_name}")

        # Auto-generate title if not provided
        if not title:
            # Get commit history
            commits = repo.get_commit_history(count=10)

            if commits:
                # Parse first commit to get type and description
                parsed = ConventionalCommit.parse(commits[0].message)
                if parsed:
                    title = f"{parsed.type.value}: {parsed.description}"
                else:
                    title = commits[0].message.split("\n")[0]
            else:
                title = f"feat: {project_id}"

        # Build PR description
        commits = repo.get_commit_history(count=10, branch=status.branch)

        description_parts = [
            f"## Changes for {project_id}",
            "",
            "### Commits"
        ]

        for commit in commits[:5]:
            commit_msg = commit.message.split("\n")[0]
            description_parts.append(f"- {commit_msg} ({commit.sha[:7]})")

        if len(commits) > 5:
            description_parts.append(f"- ... and {len(commits) - 5} more commits")

        description_parts.extend([
            "",
            "### Files Changed",
            f"- {sum(c.files_changed for c in commits)} files changed"
        ])

        description = "\n".join(description_parts)

        # Parse reviewers and labels
        reviewer_list = reviewers.split(",") if reviewers else None
        label_list = labels.split(",") if labels else ["forge"]

        # Create PR
        console.print("\n[yellow]→[/yellow] Creating pull request...")

        pr = github.create_pr_with_checklist(
            title=title,
            description=description,
            head=status.branch,
            base=base,
            checklist_items=[
                "Code follows project conventions",
                "Tests pass",
                "Documentation updated if needed",
                "No breaking changes (or documented)"
            ],
            labels=label_list,
            reviewers=reviewer_list
        )

        console.print(f"\n[bold green]✓[/bold green] Created PR #{pr.number}")
        console.print(f"\n[bold]PR URL:[/bold] {pr.html_url}")

        # Show summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  • Title: {pr.title}")
        console.print(f"  • Branch: {pr.head} → {pr.base}")
        console.print(f"  • State: {pr.state}")
        if label_list:
            console.print(f"  • Labels: {', '.join(label_list)}")
        if reviewer_list:
            console.print(f"  • Reviewers: {', '.join(reviewer_list)}")

    except Exception as e:
        print_error(f"PR creation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def examples():
    """List available example projects"""
    examples_list = [
        {
            "name": "simple-api",
            "description": "RESTful API with FastAPI and PostgreSQL",
            "complexity": "Simple",
            "time": "1 hour",
            "stack": ["Python", "FastAPI", "PostgreSQL", "SQLAlchemy"]
        },
        {
            "name": "ml-pipeline",
            "description": "ML pipeline with Prophet for time series",
            "complexity": "Medium",
            "time": "2-3 hours",
            "stack": ["Python", "Prophet", "FastAPI", "Pandas"]
        },
        {
            "name": "full-stack-app",
            "description": "Full stack with React and FastAPI",
            "complexity": "Complex",
            "time": "4-6 hours",
            "stack": ["React", "FastAPI", "PostgreSQL", "JWT"]
        }
    ]

    console.print("\n[bold cyan]Forge Example Projects[/bold cyan]\n")

    for example in examples_list:
        console.print(f"[bold]{example['name']}[/bold]")
        console.print(f"  {example['description']}")
        console.print(f"  Complexity: {example['complexity']} | Time: {example['time']}")
        console.print(f"  Stack: {', '.join(example['stack'])}")
        console.print()

    console.print("[bold]Build an example:[/bold]")
    console.print("  forge example <name>")
    console.print()


@cli.command()
@click.argument('name')
def example(name):
    """Build example project"""
    console.print(f"\n[bold cyan]Building example: {name}[/bold cyan]\n")

    examples = {
        "simple-api": {
            "description": "Build a RESTful API for task management",
            "tech_stack": ["python", "fastapi", "postgresql"],
            "features": [
                "CRUD operations for tasks",
                "SQLAlchemy ORM models",
                "Pydantic validation",
                "Basic authentication",
                "Pytest tests"
            ]
        },
        "ml-pipeline": {
            "description": "Build an ML pipeline for sales forecasting",
            "tech_stack": ["python", "prophet", "pandas"],
            "features": [
                "CSV data ingestion",
                "Feature engineering",
                "Prophet time series model",
                "Prediction API endpoint",
                "Model evaluation tests"
            ]
        },
        "full-stack-app": {
            "description": "Build a full-stack todo application",
            "tech_stack": ["react", "fastapi", "postgresql"],
            "features": [
                "React frontend with hooks",
                "FastAPI backend",
                "JWT authentication",
                "PostgreSQL database",
                "Deployment configs"
            ]
        }
    }

    if name not in examples:
        print_error(f"Example not found: {name}")
        console.print("\nAvailable examples:")
        for example_name in examples.keys():
            console.print(f"  • {example_name}")
        sys.exit(1)

    example_config = examples[name]

    console.print(f"[bold]Description:[/bold] {example_config['description']}")
    console.print(f"[bold]Tech Stack:[/bold] {', '.join(example_config['tech_stack'])}\n")

    console.print("[bold]Features:[/bold]")
    for feature in example_config['features']:
        console.print(f"  • {feature}")
    console.print()

    # Build example
    try:
        from forge.core.orchestrator import ForgeOrchestrator

        orchestrator = ForgeOrchestrator()

        project_id = f"example-{name}"

        console.print("[yellow]→[/yellow] Decomposing tasks...")

        # Use CLI decompose command internally
        import subprocess
        result = subprocess.run(
            ["forge", "decompose", example_config['description']],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print_error("Task decomposition failed")
            sys.exit(1)

        console.print("[bold green]✓[/bold green] Task plan generated")
        console.print()

        console.print("[bold]Next steps:[/bold]")
        console.print(f"  1. Build project: forge build --project {project_id}")
        console.print(f"  2. Run tests: forge test --project {project_id}")
        console.print(f"  3. Deploy: forge deploy --project {project_id} --platform docker")

    except Exception as e:
        print_error(f"Example build failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument('concept')
def explain(concept):
    """Explain Forge concepts"""
    from forge.knowledgeforge.pattern_store import PatternStore

    console.print(f"\n[bold cyan]Explaining: {concept}[/bold cyan]\n")

    try:
        # Search patterns for explanation
        pattern_store = PatternStore()
        patterns = pattern_store.search_patterns(concept, top_k=3)

        if not patterns:
            console.print(f"[yellow]No documentation found for '{concept}'[/yellow]\n")
            console.print("Try searching for:")
            console.print("  • task decomposition")
            console.print("  • code generation")
            console.print("  • testing")
            console.print("  • git workflows")
            console.print("  • deployment")
            return

        console.print(f"[bold]Found {len(patterns)} relevant pattern(s):[/bold]\n")

        for i, pattern in enumerate(patterns, 1):
            console.print(f"[bold]{i}. {pattern.get('title', 'Unknown')}[/bold]")
            console.print(f"   Category: {pattern.get('module', 'General')}")

            # Show excerpt
            content = pattern.get('content', '')
            lines = content.split('\n')
            excerpt = '\n'.join(lines[:10])

            console.print(f"\n{excerpt}\n")

            if len(lines) > 10:
                console.print("   [dim](... see pattern file for full content)[/dim]\n")

    except Exception as e:
        print_error(f"Explanation failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--project-id', '-p', help="Show stats for specific project")
def stats(project_id):
    """Show project statistics"""
    from forge.core.state_manager import StateManager
    from forge.layers.review import ReviewLayer

    console.print("\n[bold cyan]Forge Statistics[/bold cyan]\n")

    try:
        state_manager = StateManager()

        if project_id:
            # Project-specific stats
            console.print(f"[bold]Project: {project_id}[/bold]\n")

            # Load project data
            try:
                task_plan = state_manager.load_task_plan(project_id)
                console.print(f"Tasks: {len(task_plan.tasks)}")
                console.print(f"Complexity: {task_plan.complexity.value}")
                console.print(f"Total estimated time: {task_plan.total_estimated_time} minutes")
            except:
                console.print("[yellow]No task plan found[/yellow]")

            try:
                test_results = state_manager.load_test_results(project_id)
                console.print(f"\nTest Results:")
                console.print(f"  Passed: {test_results.passed_tests}")
                console.print(f"  Failed: {test_results.failed_tests}")
                console.print(f"  Coverage: {test_results.coverage}%")
            except:
                console.print("\n[yellow]No test results found[/yellow]")

        else:
            # Global stats
            projects = state_manager.list_projects()
            console.print(f"[bold]Total Projects:[/bold] {len(projects)}\n")

            # Learning stats
            review_layer = ReviewLayer()
            learning_stats = review_layer.get_learning_statistics()

            console.print("[bold]Learning Database:[/bold]")
            console.print(f"  Total sessions: {learning_stats.get('total_sessions', 0)}")
            console.print(f"  Successful sessions: {learning_stats.get('successful_sessions', 0)}")
            console.print(f"  Success rate: {learning_stats.get('success_rate', 0):.1%}")
            console.print(f"  Total patterns: {learning_stats.get('total_patterns', 0)}")
            if 'avg_iterations_to_success' in learning_stats:
                console.print(f"  Avg iterations: {learning_stats['avg_iterations_to_success']:.1f}")

    except Exception as e:
        print_error(f"Stats failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
