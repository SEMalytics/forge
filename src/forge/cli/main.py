"""
Forge CLI using Click
"""

import click
from rich.console import Console
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
env_file = Path(__file__).parent.parent.parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

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

    # Check API credentials and connectivity
    console.print("\n🔌 Checking API connectivity...\n")

    import os
    import asyncio

    # Check CodeGen API
    codegen_key = os.getenv('CODEGEN_API_KEY')
    codegen_org = os.getenv('CODEGEN_ORG_ID')

    if codegen_key:
        print_success("CODEGEN_API_KEY is set")

        # Test CodeGen API connectivity
        try:
            from forge.integrations.codegen_client import CodeGenClient, CodeGenError

            async def test_codegen():
                try:
                    client = CodeGenClient(
                        api_token=codegen_key,
                        org_id=codegen_org,
                        timeout=10
                    )

                    # Try to fetch org ID (also tests API connectivity)
                    await client._ensure_org_id()

                    return True, f"Connected (org: {client.org_id})"
                except CodeGenError as e:
                    return False, str(e)
                except Exception as e:
                    return False, f"Connection failed: {e}"

            success, message = asyncio.run(test_codegen())

            if success:
                print_success(f"CodeGen API: {message}")
            else:
                print_error(f"CodeGen API: {message}")

        except Exception as e:
            print_warning(f"CodeGen API check failed: {e}")
    else:
        print_warning("CODEGEN_API_KEY not set")
        print_info("Set with: export CODEGEN_API_KEY=your-key")

    if codegen_org:
        print_success(f"CODEGEN_ORG_ID is set: {codegen_org}")
    else:
        print_info("CODEGEN_ORG_ID not set (will auto-fetch)")

    # Check Anthropic API (for planning)
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if anthropic_key:
        print_success("ANTHROPIC_API_KEY is set")
    else:
        print_warning("ANTHROPIC_API_KEY not set")
        print_info("Required for: forge chat")

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

            projects = state.list_projects()

            if not projects:
                console.print("\n[yellow]No projects found.[/yellow]")
                console.print("\nCreate a project with: [cyan]forge init <project-name>[/cyan]")
                console.print("Or start planning: [cyan]forge chat[/cyan]\n")
                state.close()
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
                created = project.created_at.strftime("%Y-%m-%d %H:%M:%S")
                table.add_row(project.id, project.name, project.stage, created)

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
@click.argument('repo_path', default='.', type=click.Path(exists=True))
@click.option('--force', '-f', is_flag=True, help="Force re-analysis (ignore cache)")
@click.option('--json', 'output_json', is_flag=True, help="Output as JSON")
@click.option('--verbose', '-v', is_flag=True, help="Show detailed analysis")
def analyze(repo_path, force, output_json, verbose):
    """Analyze repository structure and patterns

    Examines an existing codebase to understand:
    - Directory structure and naming conventions
    - Languages and file types
    - Dependencies and package manager
    - Testing setup and patterns
    - Code patterns and frameworks

    This analysis is used to inform code generation so that
    new code respects existing conventions.

    Example:
        forge analyze .
        forge analyze /path/to/project --verbose
        forge analyze . --json > analysis.json
    """
    from forge.layers.repository_analyzer import RepositoryAnalyzer, RepositoryAnalyzerError
    from rich.table import Table
    from rich.panel import Panel
    import json as json_module

    try:
        console.print("\n[bold blue]⚒ Forge Repository Analysis[/bold blue]\n")

        analyzer = RepositoryAnalyzer()
        repo = Path(repo_path).resolve()

        console.print(f"[dim]Analyzing: {repo}[/dim]")
        if force:
            console.print("[dim]Force re-analysis (ignoring cache)[/dim]")

        with console.status("[bold green]Analyzing repository...[/bold green]"):
            context = analyzer.analyze(repo, force=force)

        if output_json:
            # Output JSON for programmatic use
            console.print(json_module.dumps(context.to_dict(), indent=2))
            return

        # Display results
        console.print()
        console.print(Panel(
            f"[bold]{context.project_name}[/bold]\n\n"
            f"Primary Language: [cyan]{context.primary_language}[/cyan]\n"
            f"Files: {context.file_count} | Lines: {context.total_lines:,}",
            title="📁 Repository Overview",
            border_style="blue"
        ))

        # Languages table
        if context.languages:
            lang_table = Table(title="Languages", border_style="dim")
            lang_table.add_column("Language", style="cyan")
            lang_table.add_column("Files", justify="right")
            lang_table.add_column("Lines", justify="right")

            for lang, stats in sorted(
                context.languages.items(),
                key=lambda x: x[1].total_lines,
                reverse=True
            )[:8]:
                lang_table.add_row(lang, str(stats.count), f"{stats.total_lines:,}")

            console.print(lang_table)

        # Naming conventions
        nc = context.naming_conventions
        console.print(f"\n[bold]Naming Conventions:[/bold]")
        console.print(f"  Files: {nc.file_naming}")
        console.print(f"  Functions: {nc.function_naming}")
        console.print(f"  Classes: {nc.class_naming}")

        # Dependencies
        if context.dependency_info.package_manager:
            console.print(f"\n[bold]Dependencies:[/bold]")
            console.print(f"  Package Manager: {context.dependency_info.package_manager}")
            if context.dependency_info.python_version:
                console.print(f"  Python: {context.dependency_info.python_version}")
            if context.dependency_info.node_version:
                console.print(f"  Node: {context.dependency_info.node_version}")

            if verbose and context.dependency_info.dependencies:
                dep_count = len(context.dependency_info.dependencies)
                console.print(f"  Dependencies: {dep_count}")
                for name, version in list(context.dependency_info.dependencies.items())[:10]:
                    console.print(f"    - {name}: {version}")
                if dep_count > 10:
                    console.print(f"    ... and {dep_count - 10} more")

        # Testing
        if context.test_info.framework:
            console.print(f"\n[bold]Testing:[/bold]")
            console.print(f"  Framework: {context.test_info.framework}")
            console.print(f"  Directory: {context.test_info.test_directory or 'Not found'}")
            console.print(f"  Test Files: {context.test_info.test_count}")

        # Patterns
        if context.code_patterns:
            console.print(f"\n[bold]Detected Patterns:[/bold]")
            for pattern in context.code_patterns:
                console.print(f"  • {pattern}")

        # Key directories
        if verbose and context.key_directories:
            console.print(f"\n[bold]Key Directories:[/bold]")
            for d in context.key_directories:
                console.print(f"  📂 {d}/")

        # Config files
        if verbose and context.config_files:
            console.print(f"\n[bold]Config Files:[/bold]")
            for f in context.config_files[:10]:
                console.print(f"  📄 {f}")

        console.print()
        print_success("Analysis complete!")
        console.print(f"\n💡 Use this with planning: [cyan]forge chat --repo {repo_path}[/cyan]\n")

    except RepositoryAnalyzerError as e:
        print_error(f"Analysis failed: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        logger.exception("Analysis error")
        sys.exit(1)


@cli.command()
@click.option('--project-id', '-p', help="Resume existing project session")
@click.option('--repo', '-r', type=click.Path(exists=True), help="Analyze repository before planning")
def chat(project_id, repo):
    """Start interactive planning session

    For new projects:
        forge chat

    For existing codebases (analyzes repo first):
        forge chat --repo /path/to/project

    To resume a previous session:
        forge chat --project-id <id>
    """
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

    # Analyze repository if specified
    repo_context = None
    if repo:
        from forge.layers.repository_analyzer import RepositoryAnalyzer

        console.print("\n[bold blue]⚒ Analyzing Repository...[/bold blue]\n")

        try:
            analyzer = RepositoryAnalyzer()
            repo_path = Path(repo).resolve()

            with console.status("[bold green]Analyzing codebase...[/bold green]"):
                repo_context = analyzer.analyze(repo_path)

            console.print(f"[green]✓[/green] Analyzed: [bold]{repo_context.project_name}[/bold]")
            console.print(f"  Primary language: {repo_context.primary_language}")
            console.print(f"  Files: {repo_context.file_count} | Lines: {repo_context.total_lines:,}")

            if repo_context.code_patterns:
                console.print(f"  Patterns: {', '.join(repo_context.code_patterns[:3])}")

            console.print()

        except Exception as e:
            print_warning(f"Repository analysis failed: {e}")
            console.print("[dim]Continuing without repository context...[/dim]\n")

    try:
        # Start interactive chat session with optional repo context
        summary = simple_chat(api_key, repo_context=repo_context)

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
@click.argument('description', required=False)
@click.option('--tech-stack', '-t', multiple=True, help="Technologies to use (can specify multiple)")
@click.option('--project-id', '-p', help="Use existing project (loads planning summary)")
@click.option('--save', '-s', is_flag=True, help="Save plan to file")
@click.option('--visualize', '-v', is_flag=True, help="Show dependency graph visualization")
def decompose(description, tech_stack, project_id, save, visualize):
    """Generate project task plan from description or existing project"""
    from forge.knowledgeforge.pattern_store import PatternStore
    from forge.layers.decomposition import TaskDecomposer
    from forge.core.state_manager import StateManager
    from rich.table import Table
    from rich.panel import Panel
    import json

    try:
        console.print("\n[bold blue]⚒ Forge Task Decomposition[/bold blue]\n")

        # If project_id provided without description, load from planning summary
        if project_id and not description:
            state = StateManager()
            project = state.get_project(project_id)

            if not project:
                print_error(f"Project not found: {project_id}")
                sys.exit(1)

            # Extract description and tech stack from planning summary
            planning_summary = project.metadata.get('planning_summary', {})

            if not planning_summary:
                print_error(f"No planning summary found for project: {project_id}")
                print_info("Run 'forge chat' to create a planning session first")
                sys.exit(1)

            # Build comprehensive description from planning summary
            desc_parts = [planning_summary.get('description', '')]

            if planning_summary.get('requirements'):
                desc_parts.append("\nRequirements:")
                desc_parts.extend([f"- {req}" for req in planning_summary['requirements']])

            if planning_summary.get('features'):
                desc_parts.append("\nFeatures:")
                desc_parts.extend([f"- {feat}" for feat in planning_summary['features']])

            if planning_summary.get('constraints'):
                desc_parts.append("\nConstraints:")
                desc_parts.extend([f"- {const}" for const in planning_summary['constraints']])

            description = "\n".join(desc_parts)
            tech_stack = planning_summary.get('tech_stack', [])

            console.print(f"[green]✓[/green] Loaded planning summary for: [bold]{project.name}[/bold]")
            console.print(f"[dim]Tech stack: {', '.join(tech_stack)}[/dim]\n")

            state.close()

        elif not description:
            print_error("Description required (or use --project-id to load from existing project)")
            sys.exit(1)

        # Initialize decomposer
        console.print("[dim]Initializing task decomposer...[/dim]")
        store = PatternStore()
        decomposer = TaskDecomposer(pattern_store=store)

        # Perform decomposition
        console.print(f"[dim]Analyzing project...[/dim]")
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
@click.option('--resume/--no-resume', default=True, help="Resume from previous build (skip completed tasks)")
@click.option('--force', is_flag=True, help="Force re-run all tasks (ignore completed state)")
def build(project_id, backend, parallel, max_parallel, resume, force):
    """Build project from task plan

    By default, resumes from previous builds and skips completed tasks.
    Use --no-resume to start fresh, or --force to re-run everything.
    """
    import os
    import asyncio
    from forge.generators.factory import GeneratorFactory, GeneratorBackend
    from forge.layers.generation import GenerationOrchestrator
    from forge.layers.decomposition import TaskDecomposer
    from forge.core.state_manager import StateManager
    from forge.core.config import ForgeConfig

    try:
        console.print("\n[bold blue]⚒ Forge Build System[/bold blue]\n")

        # Load configuration
        config = ForgeConfig.load()

        # Load project
        state = StateManager()
        project = state.get_project(project_id)

        if not project:
            print_error(f"Project not found: {project_id}")
            sys.exit(1)

        console.print(f"[bold]Project:[/bold] {project.name}")
        console.print(f"[bold]Stage:[/bold] {project.stage}\n")

        # Get tasks for project
        task_states = state.get_project_tasks(project_id)

        if not task_states:
            print_warning("No tasks found. Run 'forge decompose' first.")
            sys.exit(1)

        # Convert TaskState objects to Task objects for generation
        from forge.integrations.compound_engineering import Task
        tasks = []
        for task_state in task_states:
            tasks.append(Task(
                id=task_state.id,
                title=task_state.title,
                description=task_state.title,  # TaskState doesn't have description
                dependencies=task_state.dependencies,
                priority=task_state.priority,
                kf_patterns=[]  # Will be enriched later
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
                org_id=os.getenv('CODEGEN_ORG_ID'),
                timeout=config.generator.timeout  # Pass timeout from config
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
                project_context=project_context,
                resume=resume and not force,  # Resume unless force is set
                force=force
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
@click.option('--project-id', '-p', required=True, help="Project ID to triage")
@click.option('--session', '-s', help="Resume existing triage session")
@click.option('--batch', '-b', is_flag=True, help="Use batch mode (show all at once)")
@click.option('--auto', '-a', is_flag=True, help="Auto-approve critical issues")
@click.option('--list', 'list_sessions', is_flag=True, help="List triage sessions for project")
def triage(project_id, session, batch, auto, list_sessions):
    """Interactive triage of test failures and issues

    Review findings one-by-one and decide which fixes to apply.
    Separates finding review from fix application.

    Example:
        forge triage -p my-project
        forge triage -p my-project --batch
        forge triage -p my-project --auto
        forge triage -p my-project --list
    """
    from forge.layers.triage import TriageWorkflow, TriageError
    from forge.layers.failure_analyzer import FailureAnalyzer
    from forge.core.state_manager import StateManager
    from rich.table import Table

    try:
        console.print("\n[bold blue]⚖ Forge Triage Workflow[/bold blue]\n")

        # Initialize workflow
        workflow = TriageWorkflow(console=console)

        # List sessions mode
        if list_sessions:
            sessions = workflow.list_sessions(project_id)

            if not sessions:
                console.print(f"[yellow]No triage sessions found for project: {project_id}[/yellow]")
                return

            table = Table(title=f"Triage Sessions for {project_id}", border_style="blue")
            table.add_column("Session ID", style="cyan")
            table.add_column("Created", style="dim")
            table.add_column("Total", justify="right")
            table.add_column("Approved", justify="right", style="green")
            table.add_column("Pending", justify="right", style="yellow")

            for sess in sessions:
                summary = sess.get('summary', {})
                table.add_row(
                    sess['session_id'],
                    sess['created_at'][:19],
                    str(summary.get('total', 0)),
                    str(summary.get('approved', 0)),
                    str(summary.get('pending', 0))
                )

            console.print(table)
            console.print(f"\n💡 Resume a session: [cyan]forge triage -p {project_id} -s <session-id>[/cyan]\n")
            return

        # Load project
        state = StateManager()
        project = state.get_project(project_id)

        if not project:
            print_error(f"Project not found: {project_id}")
            sys.exit(1)

        console.print(f"[bold]Project:[/bold] {project.name}")

        # Resume existing session or create new
        if session:
            console.print(f"[dim]Resuming session: {session}[/dim]\n")
            triage_session = workflow.load_session(session)

            if not triage_session:
                print_error(f"Session not found: {session}")
                sys.exit(1)

        else:
            # Analyze failures to get suggestions
            console.print("[dim]Analyzing project failures...[/dim]")

            # Load test results from project
            project_output_dir = Path(".forge/output") / project_id

            # Try to get failure suggestions from test results
            analyzer = FailureAnalyzer()

            # Check if there are test results to analyze
            test_results_file = Path(".forge") / "test_results" / f"{project_id}.json"

            if test_results_file.exists():
                import json as json_module
                test_data = json_module.loads(test_results_file.read_text())

                # Analyze failures
                with console.status("[bold green]Analyzing failures..."):
                    suggestions = analyzer.analyze_failures(test_data)

                if not suggestions:
                    console.print("[green]✓ No issues found to triage![/green]")
                    state.close()
                    return

                console.print(f"[dim]Found {len(suggestions)} issues to triage[/dim]\n")

                # Create new session
                triage_session = workflow.create_session(project_id, suggestions)

            else:
                # No test results - check for deferred items from previous sessions
                previous_sessions = workflow.list_sessions(project_id)

                if previous_sessions:
                    # Check for deferred items
                    console.print("[yellow]No new test results found.[/yellow]")
                    console.print(f"\nFound {len(previous_sessions)} previous session(s).")
                    console.print("Use [cyan]--list[/cyan] to see sessions or [cyan]--session[/cyan] to resume.")
                else:
                    console.print("[yellow]No test results found.[/yellow]")
                    console.print(f"\nRun tests first: [cyan]forge test -p {project_id}[/cyan]")

                state.close()
                return

        # Auto-triage if requested
        if auto:
            console.print("[dim]Running auto-triage for critical issues...[/dim]\n")
            triage_session = workflow.auto_triage(
                triage_session,
                approve_critical=True,
                approve_high=True,
                min_confidence=0.8
            )

            if triage_session.pending_count == 0:
                console.print("[green]✓ All findings auto-triaged![/green]")
                workflow._print_session_summary(triage_session)
                state.close()
                workflow.close()
                return

        # Run interactive triage
        triage_session = workflow.run_interactive_triage(
            session=triage_session,
            batch_mode=batch
        )

        # Get approved suggestions
        approved = workflow.get_approved_suggestions(triage_session)

        if approved:
            console.print(f"\n[bold]Ready to apply {len(approved)} fixes[/bold]")
            console.print(f"Run: [cyan]forge iterate -p {project_id}[/cyan] to apply fixes\n")
        else:
            console.print("\n[dim]No fixes approved in this session[/dim]\n")

        # Cleanup
        state.close()
        workflow.close()

    except TriageError as e:
        print_error(f"Triage failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Triage interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        print_error(f"Triage failed: {e}")
        logger.exception("Triage error")
        sys.exit(1)


@cli.group()
def worktree():
    """Manage git worktrees for parallel execution

    Worktrees allow running multiple tasks in parallel, each in
    its own isolated working directory with its own branch.

    Example:
        forge worktree create task-001 task-002
        forge worktree list
        forge worktree clean
    """
    pass


@worktree.command('create')
@click.argument('names', nargs=-1, required=True)
@click.option('--base', '-b', default='main', help="Base branch to create from")
@click.option('--force', '-f', is_flag=True, help="Force creation (remove existing)")
def worktree_create(names, base, force):
    """Create worktrees for parallel tasks

    Creates one or more worktrees, each with its own branch.
    Worktrees are created in a sibling directory to the repository.

    Example:
        forge worktree create task-001
        forge worktree create task-001 task-002 task-003
        forge worktree create my-feature --base develop
    """
    from forge.git.worktree import WorktreeManager, WorktreeError
    from rich.table import Table

    try:
        manager = WorktreeManager()

        created = []
        for name in names:
            try:
                wt = manager.create_worktree(
                    name=name,
                    base_branch=base,
                    force=force
                )
                created.append(wt)
                print_success(f"Created worktree: {wt.path}")
                console.print(f"  Branch: [cyan]{wt.branch}[/cyan]")
            except WorktreeError as e:
                print_error(f"Failed to create {name}: {e}")

        if len(created) > 1:
            console.print(f"\n[green]✓[/green] Created {len(created)} worktrees")

        # Show usage hint
        if created:
            console.print(f"\n[dim]Run commands in worktree:[/dim]")
            console.print(f"  cd {created[0].path}")
            console.print(f"  # ... make changes ...")
            console.print(f"  forge worktree merge {created[0].name}\n")

    except WorktreeError as e:
        print_error(f"Worktree creation failed: {e}")
        sys.exit(1)


@worktree.command('list')
@click.option('--all', '-a', 'show_all', is_flag=True, help="Show all worktrees (not just forge)")
@click.option('--json', 'output_json', is_flag=True, help="Output as JSON")
def worktree_list(show_all, output_json):
    """List worktrees

    Shows all forge-managed worktrees by default.
    Use --all to see all worktrees including the main repository.

    Example:
        forge worktree list
        forge worktree list --all
        forge worktree list --json
    """
    from forge.git.worktree import WorktreeManager, WorktreeError
    from rich.table import Table
    import json as json_module

    try:
        manager = WorktreeManager()
        worktrees = manager.list_worktrees()

        if not show_all:
            worktrees = [wt for wt in worktrees if wt.is_forge_worktree]

        if output_json:
            data = [wt.to_dict() for wt in worktrees]
            console.print(json_module.dumps(data, indent=2))
            return

        if not worktrees:
            console.print("\n[yellow]No worktrees found.[/yellow]")
            console.print("Create one with: [cyan]forge worktree create <name>[/cyan]\n")
            return

        console.print()
        table = Table(title="Git Worktrees", border_style="blue")
        table.add_column("Name", style="cyan")
        table.add_column("Branch", style="green")
        table.add_column("Path")
        table.add_column("Status", width=12)

        for wt in worktrees:
            status = ""
            if wt.is_locked:
                status = "[yellow]locked[/yellow]"
            elif wt.prunable:
                status = "[dim]prunable[/dim]"
            elif wt.is_detached:
                status = "[dim]detached[/dim]"
            else:
                status = "[green]active[/green]"

            table.add_row(
                wt.name,
                wt.branch or "(detached)",
                str(wt.path),
                status
            )

        console.print(table)
        console.print()

    except WorktreeError as e:
        print_error(f"Failed to list worktrees: {e}")
        sys.exit(1)


@worktree.command('remove')
@click.argument('names', nargs=-1, required=True)
@click.option('--force', '-f', is_flag=True, help="Force removal even if dirty")
@click.option('--delete-branch', '-d', is_flag=True, help="Also delete associated branch")
def worktree_remove(names, force, delete_branch):
    """Remove worktrees

    Removes one or more worktrees. Use --force to remove even if
    there are uncommitted changes.

    Example:
        forge worktree remove task-001
        forge worktree remove task-001 task-002 --force
        forge worktree remove task-001 --delete-branch
    """
    from forge.git.worktree import WorktreeManager, WorktreeError

    try:
        manager = WorktreeManager()

        for name in names:
            try:
                # Get branch before removing
                wt = manager.get_worktree(name)
                branch = wt.branch if wt else None

                manager.remove_worktree(name, force=force)
                print_success(f"Removed worktree: {name}")

                if delete_branch and branch:
                    manager._delete_branch(branch, force=True)
                    console.print(f"  [dim]Deleted branch: {branch}[/dim]")

            except WorktreeError as e:
                print_error(f"Failed to remove {name}: {e}")

    except WorktreeError as e:
        print_error(f"Worktree removal failed: {e}")
        sys.exit(1)


@worktree.command('clean')
@click.option('--all', '-a', 'clean_all', is_flag=True, help="Clean all forge worktrees (not just merged)")
@click.option('--delete-branches', '-d', is_flag=True, help="Also delete associated branches")
@click.option('--dry-run', '-n', is_flag=True, help="Show what would be removed")
def worktree_clean(clean_all, delete_branches, dry_run):
    """Clean up completed worktrees

    By default, removes only worktrees whose branches have been merged.
    Use --all to remove all forge worktrees.

    Example:
        forge worktree clean
        forge worktree clean --all
        forge worktree clean --delete-branches
        forge worktree clean --dry-run
    """
    from forge.git.worktree import WorktreeManager, WorktreeError

    try:
        manager = WorktreeManager()

        if dry_run:
            worktrees = manager.get_forge_worktrees()

            if not worktrees:
                console.print("\n[yellow]No forge worktrees to clean.[/yellow]\n")
                return

            console.print("\n[bold]Would remove:[/bold]")
            for wt in worktrees:
                if wt.path == manager.repo_path:
                    continue

                if clean_all or manager._is_branch_merged(wt.branch):
                    console.print(f"  • {wt.name} ({wt.branch})")

            console.print("\n[dim]Run without --dry-run to remove[/dim]\n")
            return

        removed = manager.clean_worktrees(
            completed_only=not clean_all,
            delete_branches=delete_branches
        )

        if removed > 0:
            print_success(f"Cleaned {removed} worktree(s)")
        else:
            console.print("\n[yellow]No worktrees to clean.[/yellow]\n")

    except WorktreeError as e:
        print_error(f"Worktree cleanup failed: {e}")
        sys.exit(1)


@worktree.command('merge')
@click.argument('name')
@click.option('--target', '-t', default='main', help="Target branch to merge into")
@click.option('--keep', '-k', is_flag=True, help="Keep worktree after merge")
def worktree_merge(name, target, keep):
    """Merge worktree branch into target

    Merges the worktree's branch into the target branch (default: main),
    then removes the worktree and branch.

    Example:
        forge worktree merge task-001
        forge worktree merge task-001 --target develop
        forge worktree merge task-001 --keep
    """
    from forge.git.worktree import WorktreeManager, WorktreeError

    try:
        manager = WorktreeManager()

        wt = manager.get_worktree(name)
        if not wt:
            print_error(f"Worktree not found: {name}")
            sys.exit(1)

        console.print(f"\n[bold]Merging {wt.branch} into {target}...[/bold]\n")

        success = manager.merge_worktree(
            name=name,
            target_branch=target,
            delete_after=not keep
        )

        if success:
            print_success(f"Merged {wt.branch} into {target}")
            if not keep:
                console.print(f"[dim]Cleaned up worktree and branch[/dim]")
        else:
            print_error("Merge failed - resolve conflicts manually")
            sys.exit(1)

    except WorktreeError as e:
        print_error(f"Merge failed: {e}")
        sys.exit(1)


@worktree.command('status')
@click.argument('name', required=False)
def worktree_status(name):
    """Show worktree status

    Shows status of a specific worktree or all forge worktrees.

    Example:
        forge worktree status
        forge worktree status task-001
    """
    from forge.git.worktree import WorktreeManager, WorktreeError
    from rich.panel import Panel

    try:
        manager = WorktreeManager()

        if name:
            wt = manager.get_worktree(name)
            if not wt:
                print_error(f"Worktree not found: {name}")
                sys.exit(1)

            # Show detailed status
            console.print()
            console.print(Panel(
                f"[bold]Path:[/bold] {wt.path}\n"
                f"[bold]Branch:[/bold] {wt.branch}\n"
                f"[bold]HEAD:[/bold] {wt.head[:8]}\n"
                f"[bold]Locked:[/bold] {wt.is_locked}\n"
                f"[bold]Prunable:[/bold] {wt.prunable}",
                title=f"[bold cyan]Worktree: {wt.name}[/bold cyan]",
                border_style="blue"
            ))

            # Show git status in worktree
            result = manager.run_in_worktree(name, ["git", "status", "--short"])
            if result.stdout.strip():
                console.print("\n[bold]Changes:[/bold]")
                console.print(result.stdout)
            else:
                console.print("\n[green]Working tree clean[/green]")

            console.print()

        else:
            # Show summary of all forge worktrees
            worktrees = manager.get_forge_worktrees()

            if not worktrees:
                console.print("\n[yellow]No forge worktrees found.[/yellow]\n")
                return

            console.print(f"\n[bold]Forge Worktrees: {len(worktrees)}[/bold]\n")

            for wt in worktrees:
                if wt.path == manager.repo_path:
                    continue

                status_icon = "🔒" if wt.is_locked else "📁"
                merged = manager._is_branch_merged(wt.branch)
                merge_status = "[green](merged)[/green]" if merged else ""

                console.print(f"  {status_icon} [cyan]{wt.name}[/cyan] → {wt.branch} {merge_status}")

            console.print()

    except WorktreeError as e:
        print_error(f"Failed to get status: {e}")
        sys.exit(1)


@cli.group()
def context():
    """Manage generation context for cascading information

    Context items carry information between generation stages,
    enabling coherent multi-stage code generation.

    Example:
        forge context show
        forge context add -t architecture -f design.md
        forge context stats
    """
    pass


@context.command('show')
@click.option('--source', '-s', help="Filter by source (e.g., project ID, task ID)")
@click.option('--type', '-t', 'context_type', help="Filter by context type")
@click.option('--tag', help="Filter by tag")
@click.option('--json', 'output_json', is_flag=True, help="Output as JSON")
@click.option('--limit', '-n', default=20, help="Maximum items to show")
def context_show(source, context_type, tag, output_json, limit):
    """Show context items

    Displays context items with optional filtering.

    Example:
        forge context show
        forge context show --source my-project
        forge context show --type architecture
        forge context show --json
    """
    from forge.core.context import ContextManager, ContextType
    import json as json_module

    try:
        manager = ContextManager()

        # Load from storage if it exists
        try:
            manager.load()
        except Exception:
            pass  # No existing context, that's fine

        # Get all items
        items = list(manager)

        # Filter by source
        if source:
            items = [i for i in items if i.source == source]

        # Filter by type
        if context_type:
            try:
                ct = ContextType(context_type)
                items = [i for i in items if i.context_type == ct]
            except ValueError:
                print_error(f"Unknown context type: {context_type}")
                console.print(f"Available types: {', '.join(t.value for t in ContextType)}")
                sys.exit(1)

        # Filter by tag
        if tag:
            items = [i for i in items if tag in i.tags]

        # Sort by created_at descending
        items.sort(key=lambda x: x.created_at, reverse=True)

        # Limit
        items = items[:limit]

        if output_json:
            data = [i.to_dict() for i in items]
            console.print(json_module.dumps(data, indent=2, default=str))
            return

        if not items:
            console.print("\n[yellow]No context items found.[/yellow]")
            console.print("Add context with: [cyan]forge context add -t <type> -f <file>[/cyan]\n")
            return

        # Display items
        from rich.table import Table

        console.print()
        table = Table(title="Context Items", border_style="blue")
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Type", style="green")
        table.add_column("Source")
        table.add_column("Tokens", justify="right")
        table.add_column("Active")
        table.add_column("Created", style="dim")

        for item in items:
            active = "[green]yes[/green]" if item.is_active else "[dim]no[/dim]"
            table.add_row(
                item.id[:12],
                item.context_type.value,
                item.source or "-",
                str(item.token_count or 0),
                active,
                item.created_at[:16]
            )

        console.print(table)
        console.print()

    except Exception as e:
        print_error(f"Failed to show context: {e}")
        sys.exit(1)


@context.command('add')
@click.option('--type', '-t', 'context_type', required=True, help="Context type")
@click.option('--file', '-f', 'file_path', type=click.Path(exists=True), help="File to read content from")
@click.option('--id', 'item_id', help="Custom ID for the context item")
@click.option('--source', '-s', help="Source identifier (e.g., project ID, task ID)")
@click.option('--tag', multiple=True, help="Tags for the item (can specify multiple)")
@click.option('--priority', type=int, default=0, help="Priority (higher = more important)")
@click.option('--stdin', is_flag=True, help="Read content from stdin")
def context_add(context_type, file_path, item_id, source, tag, priority, stdin):
    """Add context item

    Adds a new context item from a file or stdin.

    Example:
        forge context add -t architecture -f design.md
        forge context add -t specification -s my-project -f spec.md
        echo "API design..." | forge context add -t architecture --stdin
        forge context add -t user_input -f notes.txt --tag important --tag api
    """
    from forge.core.context import ContextManager, ContextType
    import hashlib

    try:
        # Validate context type
        try:
            ct = ContextType(context_type)
        except ValueError:
            print_error(f"Unknown context type: {context_type}")
            console.print(f"Available types: {', '.join(t.value for t in ContextType)}")
            sys.exit(1)

        # Get content
        if stdin:
            import sys as sys_module
            content = sys_module.stdin.read()
        elif file_path:
            content = Path(file_path).read_text()
        else:
            print_error("Provide --file or --stdin for content")
            sys.exit(1)

        if not content.strip():
            print_error("Content cannot be empty")
            sys.exit(1)

        # Generate ID if not provided
        if not item_id:
            hash_content = hashlib.md5(content.encode()).hexdigest()[:8]
            item_id = f"ctx-{context_type[:4]}-{hash_content}"

        # Add context
        manager = ContextManager()

        # Load existing context
        try:
            manager.load()
        except Exception:
            pass

        item = manager.add(
            id=item_id,
            content=content,
            context_type=ct,
            source=source,
            tags=list(tag),
            priority=priority
        )

        # Save context
        manager.save()

        print_success(f"Added context item: {item.id}")
        console.print(f"  Type: [cyan]{item.context_type.value}[/cyan]")
        console.print(f"  Tokens: [dim]{item.token_count}[/dim]")
        if source:
            console.print(f"  Source: [dim]{source}[/dim]")
        if tag:
            console.print(f"  Tags: [dim]{', '.join(tag)}[/dim]")
        console.print()

    except Exception as e:
        print_error(f"Failed to add context: {e}")
        sys.exit(1)


@context.command('remove')
@click.argument('ids', nargs=-1, required=True)
def context_remove(ids):
    """Remove context items

    Removes one or more context items by ID (or ID prefix).

    Example:
        forge context remove ctx-spec-abc123
        forge context remove ctx-spec ctx-arch
    """
    from forge.core.context import ContextManager

    try:
        manager = ContextManager()

        # Load existing context
        try:
            manager.load()
        except Exception:
            console.print("\n[yellow]No context found.[/yellow]\n")
            return

        removed = 0
        for item_id in ids:
            # Try to find by prefix
            matches = [k for k in manager._items.keys() if k.startswith(item_id)]

            if not matches:
                print_warning(f"Context item not found: {item_id}")
                continue

            for match in matches:
                if manager.remove(match):
                    print_success(f"Removed: {match}")
                    removed += 1

        if removed > 0:
            manager.save()
            console.print(f"\n[green]✓[/green] Removed {removed} item(s)\n")

    except Exception as e:
        print_error(f"Failed to remove context: {e}")
        sys.exit(1)


@context.command('clear')
@click.option('--source', '-s', help="Clear only items with this source")
@click.option('--type', '-t', 'context_type', help="Clear only items of type")
@click.option('--force', '-f', is_flag=True, help="Skip confirmation")
def context_clear(source, context_type, force):
    """Clear context items

    Clears all context items or filters by source/type.

    Example:
        forge context clear
        forge context clear --source my-project
        forge context clear --type test_result
        forge context clear --force
    """
    from forge.core.context import ContextManager, ContextType

    try:
        manager = ContextManager()

        # Load existing context
        try:
            manager.load()
        except Exception:
            console.print("\n[yellow]No context found.[/yellow]\n")
            return

        # Filter items
        items = list(manager)

        if source:
            items = [i for i in items if i.source == source]

        if context_type:
            try:
                ct = ContextType(context_type)
                items = [i for i in items if i.context_type == ct]
            except ValueError:
                print_error(f"Unknown context type: {context_type}")
                sys.exit(1)

        if not items:
            console.print("\n[yellow]No matching context items to clear.[/yellow]\n")
            return

        # Confirm unless force
        if not force:
            console.print(f"\n[yellow]Will clear {len(items)} context item(s)[/yellow]")
            if not click.confirm("Continue?"):
                console.print("[dim]Cancelled[/dim]")
                return

        # Clear
        if source or context_type:
            # Remove filtered items
            for item in items:
                manager.remove(item.id)
        else:
            # Clear all
            manager.clear()

        manager.save()
        print_success(f"Cleared {len(items)} context item(s)")

    except Exception as e:
        print_error(f"Failed to clear context: {e}")
        sys.exit(1)


@context.command('stats')
def context_stats():
    """Show context statistics

    Displays statistics about context usage including
    item counts, token usage, and type distribution.

    Example:
        forge context stats
    """
    from forge.core.context import ContextManager
    from rich.table import Table
    from rich.panel import Panel

    try:
        manager = ContextManager()

        # Load existing context
        try:
            manager.load()
        except Exception:
            pass

        if len(manager) == 0:
            console.print("\n[yellow]No context items.[/yellow]\n")
            return

        # Get stats using the manager's method
        stats = manager.get_stats()

        console.print()
        console.print(Panel(
            f"[bold]Total Items:[/bold] {stats['total_items']}\n"
            f"[bold]Active Items:[/bold] {stats['active_items']}\n"
            f"[bold]Total Tokens:[/bold] {stats['total_tokens']:,}\n"
            f"[bold]Max Tokens:[/bold] {stats['max_tokens']:,}",
            title="[bold cyan]Context Statistics[/bold cyan]",
            border_style="blue"
        ))

        # Type breakdown
        if stats['types']:
            table = Table(title="By Type", border_style="dim")
            table.add_column("Type", style="cyan")
            table.add_column("Count", justify="right")

            for ctx_type, count in sorted(stats['types'].items(), key=lambda x: -x[1]):
                table.add_row(ctx_type, str(count))

            console.print(table)

        console.print()

    except Exception as e:
        print_error(f"Failed to get stats: {e}")
        sys.exit(1)


@cli.group()
def cache():
    """Manage generation cache for incremental builds

    The cache stores generated code to avoid regenerating unchanged tasks.
    Use these commands to inspect, manage, and optimize the cache.

    Example:
        forge cache stats
        forge cache list
        forge cache clear
    """
    pass


@cache.command('stats')
def cache_stats():
    """Show cache statistics

    Displays cache usage statistics including hit rate, disk usage,
    and entry counts.

    Example:
        forge cache stats
    """
    from forge.core.cache import GenerationCache
    from rich.panel import Panel
    from rich.table import Table

    try:
        cache_instance = GenerationCache()
        stats = cache_instance.get_stats()

        console.print()
        console.print(Panel(
            f"[bold]Entries:[/bold] {stats['entries']} / {stats['max_entries']}\n"
            f"[bold]Hit Rate:[/bold] {stats['hit_rate']:.1%}\n"
            f"[bold]Hits:[/bold] {stats['hits']}  [bold]Misses:[/bold] {stats['misses']}\n"
            f"[bold]Disk Usage:[/bold] {stats['disk_usage_mb']:.2f} MB / {stats['max_size_mb']} MB\n"
            f"[bold]Evictions:[/bold] {stats['evictions']}  [bold]Invalidations:[/bold] {stats['invalidations']}",
            title="[bold cyan]Cache Statistics[/bold cyan]",
            border_style="blue"
        ))
        console.print()

    except Exception as e:
        print_error(f"Failed to get cache stats: {e}")
        sys.exit(1)


@cache.command('list')
@click.option('--task-id', '-t', help="Filter by task ID")
@click.option('--limit', '-n', default=20, help="Maximum entries to show")
@click.option('--json', 'output_json', is_flag=True, help="Output as JSON")
def cache_list(task_id, limit, output_json):
    """List cache entries

    Shows cached generation results with metadata.

    Example:
        forge cache list
        forge cache list --task-id my-task
        forge cache list --json
    """
    from forge.core.cache import GenerationCache
    from rich.table import Table
    import json as json_module

    try:
        cache_instance = GenerationCache()
        entries = cache_instance.list_entries(task_id=task_id, limit=limit)

        if output_json:
            data = [e.to_dict() for e in entries]
            console.print(json_module.dumps(data, indent=2, default=str))
            return

        if not entries:
            console.print("\n[yellow]No cache entries found.[/yellow]\n")
            return

        console.print()
        table = Table(title="Cache Entries", border_style="blue")
        table.add_column("Key", style="cyan", width=14)
        table.add_column("Task ID")
        table.add_column("Files", justify="right")
        table.add_column("Hits", justify="right")
        table.add_column("Age", style="dim")
        table.add_column("Status")

        for entry in entries:
            age_hours = entry.age_seconds / 3600
            if age_hours < 1:
                age_str = f"{entry.age_seconds / 60:.0f}m"
            elif age_hours < 24:
                age_str = f"{age_hours:.0f}h"
            else:
                age_str = f"{age_hours / 24:.0f}d"

            status = "[red]expired[/red]" if entry.is_expired else "[green]valid[/green]"

            table.add_row(
                entry.key[:14],
                entry.task_id[:20] if len(entry.task_id) > 20 else entry.task_id,
                str(len(entry.files)),
                str(entry.hit_count),
                age_str,
                status
            )

        console.print(table)
        console.print()

    except Exception as e:
        print_error(f"Failed to list cache: {e}")
        sys.exit(1)


@cache.command('show')
@click.argument('key')
def cache_show(key):
    """Show details of a cache entry

    Displays full details of a cached entry including files.

    Example:
        forge cache show my-task-abc123
    """
    from forge.core.cache import GenerationCache
    from rich.panel import Panel
    from rich.syntax import Syntax

    try:
        cache_instance = GenerationCache()

        # Find entry by key prefix
        entries = cache_instance.list_entries()
        entry = None
        for e in entries:
            if e.key.startswith(key):
                entry = e
                break

        if not entry:
            print_error(f"Cache entry not found: {key}")
            sys.exit(1)

        console.print()
        console.print(Panel(
            f"[bold]Key:[/bold] {entry.key}\n"
            f"[bold]Task ID:[/bold] {entry.task_id}\n"
            f"[bold]Content Hash:[/bold] {entry.content_hash}\n"
            f"[bold]Dependency Hash:[/bold] {entry.dependency_hash}\n"
            f"[bold]Files:[/bold] {len(entry.files)}\n"
            f"[bold]Hit Count:[/bold] {entry.hit_count}\n"
            f"[bold]Created:[/bold] {entry.created_at}\n"
            f"[bold]Accessed:[/bold] {entry.accessed_at}\n"
            f"[bold]TTL:[/bold] {entry.ttl_seconds}s\n"
            f"[bold]Expired:[/bold] {entry.is_expired}",
            title=f"[bold cyan]Cache Entry: {entry.key[:20]}...[/bold cyan]",
            border_style="blue"
        ))

        # Show files
        if entry.files:
            console.print("\n[bold]Cached Files:[/bold]")
            for filepath in sorted(entry.files.keys()):
                size = len(entry.files[filepath])
                console.print(f"  [cyan]{filepath}[/cyan] ({size} bytes)")

        console.print()

    except Exception as e:
        print_error(f"Failed to show cache entry: {e}")
        sys.exit(1)


@cache.command('invalidate')
@click.argument('key_or_task')
@click.option('--by-task', '-t', is_flag=True, help="Invalidate by task ID")
@click.option('--by-dependency', '-d', is_flag=True, help="Invalidate dependents of task")
def cache_invalidate(key_or_task, by_task, by_dependency):
    """Invalidate cache entries

    Removes specific cache entries or all entries for a task.

    Example:
        forge cache invalidate my-task-abc123
        forge cache invalidate --by-task my-task
        forge cache invalidate --by-dependency upstream-task
    """
    from forge.core.cache import GenerationCache

    try:
        cache_instance = GenerationCache()

        if by_dependency:
            count = cache_instance.invalidate_by_dependency(key_or_task)
            print_success(f"Invalidated {count} dependent entries")
        elif by_task:
            count = cache_instance.invalidate_by_task(key_or_task)
            print_success(f"Invalidated {count} entries for task {key_or_task}")
        else:
            # Try exact key or prefix match
            entries = cache_instance.list_entries()
            found = False
            for entry in entries:
                if entry.key.startswith(key_or_task):
                    cache_instance.invalidate(entry.key)
                    print_success(f"Invalidated: {entry.key}")
                    found = True
                    break

            if not found:
                print_warning(f"No cache entry found matching: {key_or_task}")

    except Exception as e:
        print_error(f"Failed to invalidate cache: {e}")
        sys.exit(1)


@cache.command('clear')
@click.option('--expired', is_flag=True, help="Only clear expired entries")
@click.option('--force', '-f', is_flag=True, help="Skip confirmation")
def cache_clear(expired, force):
    """Clear cache entries

    Clears all cache entries or just expired ones.

    Example:
        forge cache clear
        forge cache clear --expired
        forge cache clear --force
    """
    from forge.core.cache import GenerationCache

    try:
        cache_instance = GenerationCache()

        if expired:
            count = cache_instance.cleanup_expired()
            print_success(f"Cleared {count} expired entries")
        else:
            stats = cache_instance.get_stats()

            if not force and stats['entries'] > 0:
                console.print(f"\n[yellow]Will clear {stats['entries']} cache entries[/yellow]")
                console.print(f"[dim]Disk usage: {stats['disk_usage_mb']:.2f} MB[/dim]")
                if not click.confirm("Continue?"):
                    console.print("[dim]Cancelled[/dim]")
                    return

            count = cache_instance.clear()
            print_success(f"Cleared {count} cache entries")

    except Exception as e:
        print_error(f"Failed to clear cache: {e}")
        sys.exit(1)


@cache.command('warm')
@click.option('--project-id', '-p', required=True, help="Project to warm cache for")
def cache_warm(project_id):
    """Pre-warm cache for a project

    Analyzes project and pre-generates cache entries for unchanged tasks.

    Example:
        forge cache warm --project-id my-project
    """
    from forge.core.cache import GenerationCache, IncrementalBuildDetector
    from forge.core.state_manager import StateManager

    try:
        cache_instance = GenerationCache()
        state_manager = StateManager()
        detector = IncrementalBuildDetector(cache_instance)

        # Load project task plan
        try:
            task_plan = state_manager.load_task_plan(project_id)
        except Exception:
            print_error(f"No task plan found for project: {project_id}")
            sys.exit(1)

        # Build dependency graph
        dep_graph = {}
        for task in task_plan.tasks:
            task_id = task.id if hasattr(task, 'id') else task.get('id', '')
            deps = task.dependencies if hasattr(task, 'dependencies') else task.get('dependencies', [])
            dep_graph[task_id] = deps

        # Detect what needs rebuilding
        tasks_data = [
            {
                "id": t.id if hasattr(t, 'id') else t.get('id'),
                "specification": t.specification if hasattr(t, 'specification') else t.get('specification', ''),
                "project_context": "",
                "tech_stack": task_plan.tech_stack if hasattr(task_plan, 'tech_stack') else [],
                "dependencies": t.dependencies if hasattr(t, 'dependencies') else t.get('dependencies', [])
            }
            for t in task_plan.tasks
        ]

        changes = detector.detect_changes(tasks_data, dep_graph)

        cached = len(task_plan.tasks) - len(changes)
        console.print(f"\n[bold]Cache Status for {project_id}:[/bold]")
        console.print(f"  [green]Cached:[/green] {cached} tasks")
        console.print(f"  [yellow]Need rebuild:[/yellow] {len(changes)} tasks")

        if changes:
            console.print("\n[bold]Tasks requiring rebuild:[/bold]")
            for task_id, reason in changes.items():
                console.print(f"  [yellow]•[/yellow] {task_id}: {reason}")

        console.print()

    except Exception as e:
        print_error(f"Failed to warm cache: {e}")
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


# =============================================================================
# Resilience Commands
# =============================================================================

@cli.group()
def resilience():
    """Resilience and error recovery management."""
    pass


@resilience.command("circuits")
def resilience_circuits():
    """Show circuit breaker status."""
    from forge.core.resilience import circuit_registry
    from rich.table import Table

    circuits = circuit_registry.list_circuits()

    if not circuits:
        console.print("[yellow]No circuit breakers registered[/yellow]")
        return

    table = Table(title="Circuit Breaker Status")
    table.add_column("Name", style="cyan")
    table.add_column("State", style="bold")
    table.add_column("Total Calls")
    table.add_column("Successful")
    table.add_column("Failed")
    table.add_column("Rejected")

    for name, circuit in circuits.items():
        stats = circuit.stats
        state_color = {
            "closed": "green",
            "open": "red",
            "half_open": "yellow"
        }.get(circuit.state.value, "white")

        table.add_row(
            name,
            f"[{state_color}]{circuit.state.value.upper()}[/{state_color}]",
            str(stats.total_calls),
            str(stats.successful_calls),
            str(stats.failed_calls),
            str(stats.rejected_calls)
        )

    console.print(table)


@resilience.command("reset")
@click.argument("circuit_name", required=False)
@click.option("--all", "reset_all", is_flag=True, help="Reset all circuits")
def resilience_reset(circuit_name: str, reset_all: bool):
    """Reset circuit breaker(s) to closed state."""
    from forge.core.resilience import circuit_registry

    if reset_all:
        circuit_registry.reset_all()
        print_success("All circuit breakers reset to CLOSED")
    elif circuit_name:
        circuit = circuit_registry.get(circuit_name)
        if circuit:
            circuit.reset()
            print_success(f"Circuit '{circuit_name}' reset to CLOSED")
        else:
            print_error(f"Circuit '{circuit_name}' not found")
    else:
        print_error("Specify circuit name or use --all")


@resilience.command("checkpoints")
@click.argument("operation_id", required=False)
@click.option("--dir", "checkpoint_dir", type=click.Path(), help="Checkpoint directory")
def resilience_checkpoints(operation_id: str, checkpoint_dir: str):
    """List saved checkpoints."""
    from forge.core.resilience import CheckpointManager
    from rich.table import Table
    from datetime import datetime

    manager = CheckpointManager(
        checkpoint_dir=Path(checkpoint_dir) if checkpoint_dir else None
    )

    if operation_id:
        # List checkpoints for specific operation
        checkpoints = manager.list_checkpoints(operation_id)

        if not checkpoints:
            console.print(f"[yellow]No checkpoints found for '{operation_id}'[/yellow]")
            return

        table = Table(title=f"Checkpoints for {operation_id}")
        table.add_column("ID", style="cyan")
        table.add_column("Stage", style="bold")
        table.add_column("Created At")
        table.add_column("State Keys")

        for cp in checkpoints:
            created = datetime.fromisoformat(cp.created_at)
            table.add_row(
                cp.checkpoint_id[:20] + "...",
                cp.stage,
                created.strftime("%Y-%m-%d %H:%M:%S"),
                ", ".join(cp.state.keys())
            )

        console.print(table)

    else:
        # List all operations with checkpoints
        checkpoint_path = manager.checkpoint_dir
        if not checkpoint_path.exists():
            console.print("[yellow]No checkpoints found[/yellow]")
            return

        operations = [d.name for d in checkpoint_path.iterdir() if d.is_dir()]

        if not operations:
            console.print("[yellow]No operations with checkpoints[/yellow]")
            return

        table = Table(title="Operations with Checkpoints")
        table.add_column("Operation ID", style="cyan")
        table.add_column("Checkpoints")
        table.add_column("Latest Stage")

        for op_id in operations:
            checkpoints = manager.list_checkpoints(op_id)
            latest = checkpoints[0] if checkpoints else None
            table.add_row(
                op_id,
                str(len(checkpoints)),
                latest.stage if latest else "-"
            )

        console.print(table)


@resilience.command("restore")
@click.argument("operation_id")
@click.option("--stage", help="Specific stage to restore")
def resilience_restore(operation_id: str, stage: str):
    """Show checkpoint data for restoration."""
    from forge.core.resilience import CheckpointManager
    import json

    manager = CheckpointManager()

    if stage:
        checkpoint = manager.load_by_stage(operation_id, stage)
    else:
        checkpoint = manager.load_latest(operation_id)

    if not checkpoint:
        print_error(f"No checkpoint found for '{operation_id}'")
        return

    console.print(f"\n[bold cyan]Checkpoint: {checkpoint.checkpoint_id}[/bold cyan]")
    console.print(f"Operation: {checkpoint.operation_id}")
    console.print(f"Stage: {checkpoint.stage}")
    console.print(f"Created: {checkpoint.created_at}")

    console.print("\n[bold]State:[/bold]")
    console.print(json.dumps(checkpoint.state, indent=2))

    if checkpoint.metadata:
        console.print("\n[bold]Metadata:[/bold]")
        console.print(json.dumps(checkpoint.metadata, indent=2))


@resilience.command("clean")
@click.argument("operation_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def resilience_clean(operation_id: str, yes: bool):
    """Delete checkpoints for an operation."""
    from forge.core.resilience import CheckpointManager

    manager = CheckpointManager()
    checkpoints = manager.list_checkpoints(operation_id)

    if not checkpoints:
        print_warning(f"No checkpoints found for '{operation_id}'")
        return

    if not yes:
        if not click.confirm(f"Delete {len(checkpoints)} checkpoints for '{operation_id}'?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

    count = manager.delete_checkpoints(operation_id)
    print_success(f"Deleted {count} checkpoints")


@resilience.command("stats")
def resilience_stats():
    """Show resilience statistics."""
    from forge.core.resilience import circuit_registry, CheckpointManager
    from rich.panel import Panel

    # Circuit breaker stats
    circuits = circuit_registry.list_circuits()
    total_calls = sum(c.stats.total_calls for c in circuits.values())
    total_failures = sum(c.stats.failed_calls for c in circuits.values())
    total_rejected = sum(c.stats.rejected_calls for c in circuits.values())

    circuit_stats = f"""
[bold]Circuit Breakers:[/bold]
  Registered: {len(circuits)}
  Total Calls: {total_calls}
  Failed Calls: {total_failures}
  Rejected Calls: {total_rejected}
  Success Rate: {(total_calls - total_failures) / total_calls * 100:.1f}% (of allowed calls)
""" if total_calls > 0 else f"""
[bold]Circuit Breakers:[/bold]
  Registered: {len(circuits)}
  No calls recorded yet
"""

    # Checkpoint stats
    manager = CheckpointManager()
    checkpoint_path = manager.checkpoint_dir

    if checkpoint_path.exists():
        operations = [d for d in checkpoint_path.iterdir() if d.is_dir()]
        total_checkpoints = sum(
            len(list(op.glob("*.json"))) for op in operations
        )
        checkpoint_stats = f"""
[bold]Checkpoints:[/bold]
  Directory: {checkpoint_path}
  Operations: {len(operations)}
  Total Checkpoints: {total_checkpoints}
"""
    else:
        checkpoint_stats = """
[bold]Checkpoints:[/bold]
  No checkpoints stored
"""

    console.print(Panel(circuit_stats.strip() + "\n" + checkpoint_stats.strip(), title="Resilience Statistics"))


# =============================================================================
# Metrics Commands
# =============================================================================

@cli.group()
def metrics():
    """Metrics and telemetry management."""
    pass


@metrics.command("show")
@click.option("--format", "output_format", type=click.Choice(["table", "json", "prometheus"]), default="table")
def metrics_show(output_format: str):
    """Show current metrics."""
    from forge.core.metrics import metrics_collector, MetricsExporter
    from rich.table import Table

    if output_format == "json":
        exporter = MetricsExporter(metrics_collector)
        console.print(exporter.to_json())
        return

    if output_format == "prometheus":
        exporter = MetricsExporter(metrics_collector)
        console.print(exporter.to_prometheus())
        return

    # Table format
    all_metrics = metrics_collector.get_all_metrics()

    # Counters table
    if all_metrics["counters"]:
        counter_table = Table(title="Counters")
        counter_table.add_column("Name", style="cyan")
        counter_table.add_column("Labels")
        counter_table.add_column("Value", justify="right")

        for name, values in all_metrics["counters"].items():
            for labels, value in values.items():
                counter_table.add_row(name, labels or "-", f"{value:,.2f}")

        console.print(counter_table)
        console.print()

    # Gauges table
    if all_metrics["gauges"]:
        gauge_table = Table(title="Gauges")
        gauge_table.add_column("Name", style="cyan")
        gauge_table.add_column("Labels")
        gauge_table.add_column("Value", justify="right")

        for name, values in all_metrics["gauges"].items():
            for labels, value in values.items():
                gauge_table.add_row(name, labels or "-", f"{value:,.2f}")

        console.print(gauge_table)
        console.print()

    # Timers table
    if all_metrics["timers"]:
        timer_table = Table(title="Timers")
        timer_table.add_column("Name", style="cyan")
        timer_table.add_column("Count", justify="right")
        timer_table.add_column("Mean", justify="right")
        timer_table.add_column("P50", justify="right")
        timer_table.add_column("P90", justify="right")
        timer_table.add_column("P99", justify="right")

        for name, stats in all_metrics["timers"].items():
            timer_table.add_row(
                name,
                str(stats["count"]),
                f"{stats['mean']:.3f}s",
                f"{stats['p50']:.3f}s",
                f"{stats['p90']:.3f}s",
                f"{stats['p99']:.3f}s"
            )

        console.print(timer_table)

    if not any([all_metrics["counters"], all_metrics["gauges"], all_metrics["timers"]]):
        console.print("[yellow]No metrics recorded yet[/yellow]")


@metrics.command("cost")
@click.option("--hours", default=24, help="Hours of history to show")
def metrics_cost(hours: int):
    """Show API cost breakdown."""
    from forge.core.metrics import cost_tracker
    from rich.table import Table
    from rich.panel import Panel

    # Get totals
    total_usage = cost_tracker.get_total_usage()
    total_cost = cost_tracker.get_total_cost()

    summary = f"""
[bold]Total API Usage:[/bold]
  Input Tokens: {total_usage.input_tokens:,}
  Output Tokens: {total_usage.output_tokens:,}
  Cached Tokens: {total_usage.cached_tokens:,}
  Total Tokens: {total_usage.total_tokens:,}

[bold]Estimated Cost:[/bold] ${total_cost:.4f}
"""
    console.print(Panel(summary.strip(), title="API Cost Summary"))

    # By model breakdown
    by_model = cost_tracker.get_usage_by_model()
    if by_model:
        table = Table(title="Usage by Model")
        table.add_column("Model", style="cyan")
        table.add_column("Calls", justify="right")
        table.add_column("Input", justify="right")
        table.add_column("Output", justify="right")
        table.add_column("Cost", justify="right")

        for model, stats in by_model.items():
            table.add_row(
                model,
                str(stats["calls"]),
                f"{stats['input_tokens']:,}",
                f"{stats['output_tokens']:,}",
                f"${stats['total_cost']:.4f}"
            )

        console.print(table)
    else:
        console.print("[yellow]No API usage recorded[/yellow]")


@metrics.command("performance")
def metrics_performance():
    """Show performance metrics."""
    from forge.core.metrics import performance_tracker, metrics_collector
    from rich.table import Table

    # Active operations
    active = performance_tracker.get_active_operations()
    if active:
        table = Table(title="Active Operations")
        table.add_column("Operation", style="cyan")
        table.add_column("Started At")
        table.add_column("Duration")
        table.add_column("Labels")

        for op in active:
            duration = (datetime.now() - op.started_at).total_seconds()
            table.add_row(
                op.operation,
                op.started_at.strftime("%H:%M:%S"),
                f"{duration:.1f}s",
                str(op.labels) if op.labels else "-"
            )

        console.print(table)
        console.print()

    # Operation statistics
    all_metrics = metrics_collector.get_all_metrics()
    op_timers = {k: v for k, v in all_metrics["timers"].items() if "operation_duration" in k}

    if op_timers:
        table = Table(title="Operation Performance")
        table.add_column("Operation", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Total Time", justify="right")
        table.add_column("Avg Time", justify="right")
        table.add_column("P99", justify="right")

        for name, stats in op_timers.items():
            op_name = name.replace("operation_duration_", "").split(":")[0]
            table.add_row(
                op_name,
                str(stats["count"]),
                f"{stats['sum']:.1f}s",
                f"{stats['mean']:.2f}s",
                f"{stats['p99']:.2f}s"
            )

        console.print(table)
    else:
        console.print("[yellow]No performance data recorded[/yellow]")


@metrics.command("export")
@click.argument("output_path", type=click.Path())
@click.option("--format", "output_format", type=click.Choice(["json", "prometheus"]), default="json")
def metrics_export(output_path: str, output_format: str):
    """Export metrics to file."""
    from forge.core.metrics import metrics_collector, MetricsExporter

    exporter = MetricsExporter(metrics_collector)
    output = Path(output_path)

    exporter.save_to_file(output, output_format)
    print_success(f"Metrics exported to {output}")


@metrics.command("snapshot")
def metrics_snapshot():
    """Save metrics snapshot for historical analysis."""
    from forge.core.metrics import metrics_collector, MetricsAggregator

    aggregator = MetricsAggregator(metrics_collector)
    path = aggregator.save_snapshot()
    print_success(f"Snapshot saved to {path}")


@metrics.command("history")
@click.option("--limit", default=10, help="Number of snapshots to show")
def metrics_history(limit: int):
    """Show historical metrics snapshots."""
    from forge.core.metrics import metrics_collector, MetricsAggregator
    from rich.table import Table

    aggregator = MetricsAggregator(metrics_collector)
    snapshots = aggregator.load_snapshots(limit)

    if not snapshots:
        console.print("[yellow]No snapshots found[/yellow]")
        return

    table = Table(title="Metrics Snapshots")
    table.add_column("File", style="cyan")
    table.add_column("Time")
    table.add_column("Uptime")
    table.add_column("Counters")
    table.add_column("Gauges")

    for snap in snapshots:
        table.add_row(
            snap.get("_file", "-"),
            snap.get("snapshot_time", "-")[:19],
            f"{snap.get('uptime_seconds', 0):.0f}s",
            str(len(snap.get("counters", {}))),
            str(len(snap.get("gauges", {})))
        )

    console.print(table)


@metrics.command("reset")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def metrics_reset(yes: bool):
    """Reset all metrics."""
    from forge.core.metrics import metrics_collector, cost_tracker

    if not yes:
        if not click.confirm("Reset all metrics? This cannot be undone."):
            console.print("[yellow]Cancelled[/yellow]")
            return

    metrics_collector.reset()
    cost_tracker.reset()
    print_success("All metrics reset")


@metrics.command("record")
@click.argument("metric_name")
@click.argument("value", type=float)
@click.option("--type", "metric_type", type=click.Choice(["counter", "gauge"]), default="counter")
@click.option("--label", "-l", multiple=True, help="Label in key=value format")
def metrics_record(metric_name: str, value: float, metric_type: str, label: tuple):
    """Manually record a metric value."""
    from forge.core.metrics import metrics_collector

    labels = {}
    for l in label:
        if "=" in l:
            k, v = l.split("=", 1)
            labels[k] = v

    if metric_type == "counter":
        metrics_collector.increment(metric_name, value, labels or None)
    else:
        metrics_collector.set_gauge(metric_name, value, labels or None)

    print_success(f"Recorded {metric_type} '{metric_name}' = {value}")


# ============================================================================
# Review Commands
# ============================================================================


@cli.group()
def review():
    """Multi-agent code review system."""
    pass


@review.command("file")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--threshold", "-t", type=int, default=8, help="Approval threshold (default: 8)")
@click.option("--parallel/--sequential", default=True, help="Run reviews in parallel")
@click.option("--format", "output_format", type=click.Choice(["summary", "full", "json"]), default="summary")
def review_file(file_path: str, threshold: int, parallel: bool, output_format: str):
    """Review a single source file."""
    from forge.review import ReviewPanel
    import json

    path = Path(file_path)
    if not path.exists():
        print_error(f"File not found: {file_path}")
        return

    print_info(f"Reviewing {path.name} with {threshold}/12 approval threshold...")

    try:
        code = path.read_text()
        panel = ReviewPanel(approval_threshold=threshold, parallel=parallel)
        report = panel.review_code(code, file_path=str(path))

        if output_format == "json":
            console.print_json(json.dumps(report.to_dict(), indent=2))
        elif output_format == "full":
            console.print(report.format_summary())
            _print_all_findings(report)
        else:
            _print_review_summary(report)

    except Exception as e:
        print_error(f"Review failed: {e}")


@review.command("directory")
@click.argument("directory", type=click.Path(exists=True))
@click.option("--pattern", "-p", default="*.py", help="File pattern to match (default: *.py)")
@click.option("--threshold", "-t", type=int, default=8, help="Approval threshold")
@click.option("--format", "output_format", type=click.Choice(["summary", "full", "json"]), default="summary")
def review_directory(directory: str, pattern: str, threshold: int, output_format: str):
    """Review all matching files in a directory."""
    from forge.review import ReviewPanel
    import json

    dir_path = Path(directory)
    if not dir_path.is_dir():
        print_error(f"Not a directory: {directory}")
        return

    files = list(dir_path.rglob(pattern))
    if not files:
        print_warning(f"No files matching '{pattern}' found in {directory}")
        return

    print_info(f"Reviewing {len(files)} files matching '{pattern}'...")

    try:
        # Read all files
        file_contents = {}
        for f in files:
            try:
                file_contents[str(f)] = f.read_text()
            except Exception as e:
                print_warning(f"Skipping {f}: {e}")

        panel = ReviewPanel(approval_threshold=threshold)
        report = panel.review_files(file_contents)

        if output_format == "json":
            console.print_json(json.dumps(report.to_dict(), indent=2))
        elif output_format == "full":
            console.print(report.format_summary())
            _print_all_findings(report)
        else:
            _print_review_summary(report)

    except Exception as e:
        print_error(f"Review failed: {e}")


@review.command("code")
@click.option("--threshold", "-t", type=int, default=8, help="Approval threshold")
@click.option("--format", "output_format", type=click.Choice(["summary", "full", "json"]), default="summary")
def review_code_stdin(threshold: int, output_format: str):
    """Review code from stdin."""
    from forge.review import ReviewPanel
    import json

    print_info("Reading code from stdin (Ctrl+D to end)...")
    code = sys.stdin.read()

    if not code.strip():
        print_error("No code provided")
        return

    try:
        panel = ReviewPanel(approval_threshold=threshold)
        report = panel.review_code(code)

        if output_format == "json":
            console.print_json(json.dumps(report.to_dict(), indent=2))
        elif output_format == "full":
            console.print(report.format_summary())
            _print_all_findings(report)
        else:
            _print_review_summary(report)

    except Exception as e:
        print_error(f"Review failed: {e}")


@review.command("panel")
def review_panel_info():
    """Show information about the review panel."""
    from forge.review import ReviewPanel
    from rich.table import Table

    panel = ReviewPanel()

    table = Table(title="Review Panel - 12 Expert Agents")
    table.add_column("Agent", style="cyan")
    table.add_column("Expertise", style="green")

    for reviewer in panel.reviewers:
        table.add_row(reviewer.name, reviewer.expertise)

    console.print(table)
    console.print()
    console.print(f"[bold]Default threshold:[/bold] 8/12 approvals required")
    console.print("[bold]Blocking issues:[/bold] Critical and High severity findings")


def _print_review_summary(report):
    """Print a concise review summary."""
    from rich.table import Table
    from rich.panel import Panel

    decision = report.decision

    # Status banner
    if decision.approved:
        console.print(Panel(
            f"[bold green]✓ APPROVED[/bold green]\n"
            f"Votes: {decision.approval_count}/{decision.total_reviewers} approve",
            title="Review Decision",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold red]✗ REJECTED[/bold red]\n"
            f"Votes: {decision.approval_count}/{decision.total_reviewers} approve "
            f"(need {decision.threshold})",
            title="Review Decision",
            border_style="red"
        ))

    console.print()

    # Findings summary
    if report.all_findings:
        table = Table(title="Findings Summary")
        table.add_column("Severity", style="cyan")
        table.add_column("Count", justify="right")

        severity_colors = {
            "critical": "red bold",
            "high": "red",
            "medium": "yellow",
            "low": "blue",
            "info": "dim"
        }

        for severity, findings in report.findings_by_severity.items():
            color = severity_colors.get(severity, "white")
            table.add_row(f"[{color}]{severity.upper()}[/{color}]", str(len(findings)))

        console.print(table)

    # Show blocking issues
    if decision.blocking_findings:
        console.print()
        console.print("[bold red]Blocking Issues:[/bold red]")
        for finding in decision.blocking_findings[:5]:
            console.print(f"  • [{finding.severity.value}] {finding.message}")
        if len(decision.blocking_findings) > 5:
            console.print(f"  ... and {len(decision.blocking_findings) - 5} more")

    console.print()
    console.print(f"[dim]Review completed in {report.total_review_time_seconds:.2f}s[/dim]")


def _print_all_findings(report):
    """Print all findings grouped by file and category."""
    from rich.tree import Tree

    if not report.all_findings:
        console.print("[green]No findings to report[/green]")
        return

    console.print()
    console.print("[bold]All Findings:[/bold]")

    tree = Tree("[bold]Findings[/bold]")

    for category, findings in report.findings_by_category.items():
        category_branch = tree.add(f"[cyan]{category}[/cyan] ({len(findings)})")
        for finding in findings[:10]:  # Limit per category
            severity_colors = {
                "critical": "red bold",
                "high": "red",
                "medium": "yellow",
                "low": "blue",
                "info": "dim"
            }
            color = severity_colors.get(finding.severity.value, "white")
            msg = f"[{color}][{finding.severity.value}][/{color}] {finding.message}"
            if finding.file_path:
                msg += f" [dim]({Path(finding.file_path).name}"
                if finding.line_number:
                    msg += f":{finding.line_number}"
                msg += ")[/dim]"
            category_branch.add(msg)
        if len(findings) > 10:
            category_branch.add(f"[dim]... and {len(findings) - 10} more[/dim]")

    console.print(tree)


if __name__ == '__main__':
    main()
