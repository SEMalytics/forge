"""
Master Controller - Pipeline orchestration for Forge

Chains existing layers with checkpoint control:
- PLANNING: Requirements gathering via PlanningAgent
- DECOMPOSITION: Task breakdown via TaskDecomposer
- GENERATION: Code generation via GenerationOrchestrator
- TESTING: Test execution via TestingOrchestrator
- REVIEW: Fix-test loop via ReviewLayer
- DEPLOYMENT: Deploy via deployment layer
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Callable, Any, Dict, cast
from datetime import datetime
from pathlib import Path
import time
import asyncio
import os

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from forge.core.config import ForgeConfig
from forge.core.state_manager import StateManager
from forge.utils.logger import logger


class Stage(Enum):
    """Pipeline stages in execution order."""
    PLANNING = "planning"
    DECOMPOSITION = "decomposition"
    GENERATION = "generation"
    TESTING = "testing"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    COMPLETE = "complete"


class CheckpointPolicy(Enum):
    """When to pause for human input."""
    NONE = "none"                    # Full auto, fail fast on errors
    PER_STAGE = "per_stage"          # Pause before each stage
    ON_FAILURE = "on_failure"        # Pause only when stage fails
    BEFORE_DEPLOY = "before_deploy"  # Auto until deployment


class DecisionType(Enum):
    """Type of human decision requested."""
    APPROVE = "approve"    # Simple proceed/abort
    CHOICE = "choice"      # Pick from options
    OVERRIDE = "override"  # Free-form instruction


@dataclass
class Checkpoint:
    """Represents a pause point requiring human input."""
    stage: Stage
    decision_type: DecisionType
    prompt: str
    choices: Optional[List[str]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StageResult:
    """Result of executing a single stage."""
    stage: Stage
    success: bool
    duration_seconds: float
    output: Any = None  # Stage-specific: TaskPlan, GeneratedCode, TestReport, etc.
    error: Optional[str] = None


@dataclass
class PipelineRun:
    """State of a pipeline execution."""
    project_id: str
    policy: CheckpointPolicy
    current_stage: Stage
    results: List[StageResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    aborted: bool = False

    @property
    def succeeded(self) -> bool:
        """True if pipeline completed with all stages successful."""
        return (
            self.current_stage == Stage.COMPLETE
            and not self.aborted
            and all(r.success for r in self.results)
        )

    @property
    def total_duration(self) -> float:
        """Total pipeline duration in seconds."""
        return sum(r.duration_seconds for r in self.results)


class MasterController:
    """
    Orchestrates full build pipeline with human checkpoints.

    Usage:
        controller = MasterController(config)
        run = controller.run(
            project_id="my-api",
            policy=CheckpointPolicy.ON_FAILURE,
        )

        if run.succeeded:
            print("Pipeline complete!")
        else:
            print(f"Failed at {run.current_stage}")
    """

    STAGE_ORDER = [
        Stage.PLANNING,
        Stage.DECOMPOSITION,
        Stage.GENERATION,
        Stage.TESTING,
        Stage.REVIEW,
        Stage.DEPLOYMENT,
    ]

    def __init__(
        self,
        config: Optional[ForgeConfig] = None,
        state_manager: Optional[StateManager] = None,
        console: Optional[Console] = None,
    ):
        """
        Initialize master controller.

        Args:
            config: Forge configuration (loads default if not provided)
            state_manager: State manager (creates new if not provided)
            console: Rich console for output
        """
        self.config = config or ForgeConfig.load()
        self.state = state_manager or StateManager()
        self.console = console or Console()
        self._layers: Dict[str, Any] = {}

        logger.info("MasterController initialized")

    def run(
        self,
        project_id: str,
        policy: CheckpointPolicy = CheckpointPolicy.ON_FAILURE,
        start_stage: Stage = Stage.PLANNING,
        end_stage: Stage = Stage.DEPLOYMENT,
        on_checkpoint: Optional[Callable[[Checkpoint], str]] = None,
        skip_stages: Optional[List[Stage]] = None,
    ) -> PipelineRun:
        """
        Run pipeline from start_stage to end_stage.

        Args:
            project_id: Project to build
            policy: When to pause for human input
            start_stage: First stage to execute
            end_stage: Last stage to execute
            on_checkpoint: Custom handler for checkpoints (uses interactive prompt if None)
            skip_stages: Stages to skip entirely

        Returns:
            PipelineRun with results from all executed stages
        """
        skip_stages = skip_stages or []
        pipeline = PipelineRun(
            project_id=project_id,
            policy=policy,
            current_stage=start_stage,
        )

        self._print_header(project_id, policy, start_stage, end_stage)

        stages = self._stages_between(start_stage, end_stage)

        for stage in stages:
            if stage in skip_stages:
                self._print_skip(stage)
                continue

            pipeline.current_stage = stage

            # Pre-stage checkpoint for PER_STAGE policy
            if policy == CheckpointPolicy.PER_STAGE:
                decision = self._checkpoint_before_stage(stage, on_checkpoint)
                if decision == "abort":
                    pipeline.aborted = True
                    break
                if decision == "skip":
                    self._print_skip(stage)
                    continue

            # Execute stage
            self._print_stage_start(stage)
            result = self._run_stage(stage, project_id, pipeline)
            pipeline.results.append(result)
            self._print_stage_result(result)

            # Handle failure
            if not result.success:
                decision = self._handle_failure(stage, result, policy, on_checkpoint)

                if decision == "abort":
                    pipeline.aborted = True
                    break
                elif decision == "retry":
                    self._print_stage_start(stage, retry=True)
                    result = self._run_stage(stage, project_id, pipeline)
                    pipeline.results.append(result)
                    self._print_stage_result(result)
                    if not result.success:
                        pipeline.aborted = True
                        break
                elif decision == "skip":
                    continue
                elif decision.startswith("override:"):
                    override_instruction = decision[9:].strip()
                    self._print_stage_start(stage, override=True)
                    result = self._run_stage(stage, project_id, pipeline, override=override_instruction)
                    pipeline.results.append(result)
                    self._print_stage_result(result)
                    if not result.success:
                        pipeline.aborted = True
                        break
                else:
                    # Unknown decision or NONE policy: fail fast
                    pipeline.aborted = True
                    break

            # Before deploy checkpoint
            if (
                stage == Stage.TESTING
                and policy == CheckpointPolicy.BEFORE_DEPLOY
                and result.success
                and Stage.DEPLOYMENT in stages
            ):
                decision = self._checkpoint_before_deploy(result, on_checkpoint)
                if decision == "abort":
                    pipeline.aborted = True
                    break

        if not pipeline.aborted:
            pipeline.current_stage = Stage.COMPLETE

        pipeline.completed_at = datetime.now()
        self._print_summary(pipeline)

        return pipeline

    def _run_stage(
        self,
        stage: Stage,
        project_id: str,
        pipeline: PipelineRun,
        override: Optional[str] = None,
    ) -> StageResult:
        """Execute a single stage with timing."""
        start = time.time()

        try:
            output = self._execute_stage(stage, project_id, pipeline, override)
            return StageResult(
                stage=stage,
                success=True,
                duration_seconds=time.time() - start,
                output=output,
            )
        except Exception as e:
            logger.exception(f"Stage {stage.value} failed")
            return StageResult(
                stage=stage,
                success=False,
                duration_seconds=time.time() - start,
                output=None,
                error=str(e),
            )

    def _execute_stage(
        self,
        stage: Stage,
        project_id: str,
        pipeline: PipelineRun,
        override: Optional[str] = None,
    ) -> Any:
        """
        Dispatch to appropriate layer.

        Each stage uses output from previous stages via pipeline.results.
        Override instruction is passed to layer for behavior modification.
        """
        if stage == Stage.PLANNING:
            return self._execute_planning(project_id, override)

        elif stage == Stage.DECOMPOSITION:
            return self._execute_decomposition(project_id, pipeline, override)

        elif stage == Stage.GENERATION:
            return self._execute_generation(project_id, pipeline, override)

        elif stage == Stage.TESTING:
            return self._execute_testing(project_id, pipeline)

        elif stage == Stage.REVIEW:
            return self._execute_review(project_id, pipeline, override)

        elif stage == Stage.DEPLOYMENT:
            return self._execute_deployment(project_id, pipeline, override)

        raise ValueError(f"Unknown stage: {stage}")

    def _execute_planning(
        self,
        project_id: str,
        override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute planning stage."""
        # Check if project already has planning data
        project = self.state.get_project(project_id)

        if project and project.metadata.get('planning_summary'):
            self.console.print("  [dim]Using existing planning summary[/dim]")
            return cast(Dict[str, Any], project.metadata['planning_summary'])

        # For now, require existing planning data or manual chat session
        # Full automation would use PlanningAgent with predefined prompts
        raise ValueError(
            f"No planning data found for project {project_id}. "
            "Run 'forge chat' first to create a planning session."
        )

    def _execute_decomposition(
        self,
        project_id: str,
        pipeline: PipelineRun,
        override: Optional[str] = None,
    ) -> List[Any]:
        """Execute decomposition stage."""
        from forge.knowledgeforge.pattern_store import PatternStore
        from forge.layers.decomposition import TaskDecomposer

        # Get planning output
        planning_output = self._get_stage_output(pipeline, Stage.PLANNING)

        # Build description from planning summary
        description = planning_output.get('description', '')
        if planning_output.get('requirements'):
            description += "\n\nRequirements:\n" + "\n".join(
                f"- {r}" for r in planning_output['requirements']
            )
        if planning_output.get('features'):
            description += "\n\nFeatures:\n" + "\n".join(
                f"- {f}" for f in planning_output['features']
            )

        if override:
            description += f"\n\nAdditional instruction: {override}"

        tech_stack = planning_output.get('tech_stack', [])

        # Initialize decomposer
        store = PatternStore()
        decomposer = TaskDecomposer(pattern_store=store)

        try:
            tasks = decomposer.decompose(
                project_description=description,
                tech_stack=tech_stack,
                project_id=project_id
            )

            self.console.print(f"  [dim]Generated {len(tasks)} tasks[/dim]")
            return tasks
        finally:
            decomposer.close()

    def _execute_generation(
        self,
        project_id: str,
        pipeline: PipelineRun,
        override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute generation stage."""
        from forge.generators.factory import GeneratorFactory, GeneratorBackend
        from forge.layers.generation import GenerationOrchestrator

        # Get tasks from decomposition
        tasks = self._get_stage_output(pipeline, Stage.DECOMPOSITION)

        # Get project for context
        project = self.state.get_project(project_id)
        project_context = project.description if project else ""

        if override:
            project_context += f"\n\nAdditional instruction: {override}"

        # Auto-detect backend
        backend = GeneratorFactory.detect_best_backend()
        if not backend:
            raise ValueError("No generator backend available. Set CODEGEN_API_KEY.")

        self.console.print(f"  [dim]Using backend: {backend.value}[/dim]")

        # Create generator
        if backend == GeneratorBackend.CODEGEN_API:
            api_key = os.getenv('CODEGEN_API_KEY')
            generator = GeneratorFactory.create(
                backend,
                api_key=api_key,
                org_id=os.getenv('CODEGEN_ORG_ID'),
                timeout=self.config.generator.timeout
            )
        else:
            generator = GeneratorFactory.create(backend)

        # Create orchestrator
        orchestrator = GenerationOrchestrator(
            generator=generator,
            state_manager=self.state,
            console=self.console,
            max_parallel=3
        )

        try:
            # Run generation
            async def run_gen():
                return await orchestrator.generate_project(
                    project_id=project_id,
                    tasks=tasks,
                    project_context=project_context,
                    resume=True,
                    force=False
                )

            results = asyncio.run(run_gen())

            success_count = sum(1 for r in results.values() if r.success)
            self.console.print(f"  [dim]{success_count}/{len(results)} tasks completed[/dim]")

            return cast(Dict[str, Any], results)
        finally:
            orchestrator.close()

    def _execute_testing(
        self,
        project_id: str,
        pipeline: PipelineRun,
    ) -> Any:
        """Execute testing stage."""
        from forge.layers.testing import TestingOrchestrator, TestingConfig

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
            raise ValueError(
                f"No code files found in {project_output_dir}. "
                "Generation stage may have failed."
            )

        self.console.print(f"  [dim]Testing {len(code_files)} files[/dim]")

        # Get project for tech stack
        project = self.state.get_project(project_id)
        tech_stack = []
        if project and project.metadata:
            tech_stack = project.metadata.get('tech_stack', [])

        # Create testing config
        config = TestingConfig(
            run_unit_tests=True,
            run_integration_tests=True,
            run_security_scan=True,
            run_performance_tests=False,
            generate_tests=True,
            use_docker=True,
            min_coverage=80.0,
            security_required=True
        )

        orchestrator = TestingOrchestrator(
            config=config,
            console=self.console
        )

        try:
            async def run_tests():
                return await orchestrator.test_project(
                    project_id=project_id,
                    code_files=code_files,
                    tech_stack=tech_stack,
                    project_context=project.description if project else ""
                )

            return asyncio.run(run_tests())
        finally:
            orchestrator.close()

    def _execute_review(
        self,
        project_id: str,
        pipeline: PipelineRun,
        override: Optional[str] = None,
    ) -> Any:
        """Execute review stage (iterative fix loop)."""
        from forge.layers.review import ReviewLayer
        from forge.layers.testing import TestingConfig

        # Get test report from testing stage
        test_report = self._get_stage_output(pipeline, Stage.TESTING)

        # If all tests passed, skip review
        if hasattr(test_report, 'all_passed') and test_report.all_passed:
            if hasattr(test_report, 'security_passed') and test_report.security_passed:
                self.console.print("  [dim]All tests passed, skipping review[/dim]")
                return test_report

        # Load code files
        project_output_dir = Path(".forge") / "output" / project_id
        code_files = {}

        if project_output_dir.exists():
            for file_path in project_output_dir.rglob("*.py"):
                try:
                    relative_path = file_path.relative_to(project_output_dir)
                    code_files[str(relative_path)] = file_path.read_text()
                except Exception:
                    pass

        # Get project info
        project = self.state.get_project(project_id)
        tech_stack = []
        if project and project.metadata:
            tech_stack = project.metadata.get('tech_stack', [])

        project_context = project.description if project else ""
        if override:
            project_context += f"\n\nReview instruction: {override}"

        # Create review layer
        review = ReviewLayer(
            testing_config=TestingConfig(
                run_unit_tests=True,
                run_integration_tests=True,
                run_security_scan=True,
                run_performance_tests=False,
            ),
            console=self.console,
            state_manager=self.state
        )

        try:
            async def run_review():
                return await review.iterate_until_passing(
                    project_id=project_id,
                    code_files=code_files,
                    tech_stack=tech_stack,
                    project_context=project_context,
                    max_iterations=5,
                    output_dir=project_output_dir
                )

            return asyncio.run(run_review())
        finally:
            review.close()

    def _execute_deployment(
        self,
        project_id: str,
        pipeline: PipelineRun,
        override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute deployment stage."""
        from forge.layers.deployment import DeploymentGenerator, DeploymentConfig, Platform

        # Get project
        project = self.state.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        # Determine platform from override or default
        platform_str = "docker"  # Default
        if override:
            # Parse platform from override like "deploy to flyio"
            override_lower = override.lower()
            for p in ["flyio", "vercel", "aws", "docker", "k8s"]:
                if p in override_lower:
                    platform_str = p
                    break

        # Map platform string to enum
        platform_map = {
            "flyio": Platform.FLYIO,
            "vercel": Platform.VERCEL,
            "aws": Platform.AWS_LAMBDA,
            "docker": Platform.DOCKER,
            "k8s": Platform.KUBERNETES,
        }
        platform = platform_map.get(platform_str, Platform.DOCKER)

        self.console.print(f"  [dim]Deploying to: {platform_str}[/dim]")

        # Determine project output directory
        project_output_dir = Path(".forge") / "output" / project_id
        project_output_dir.mkdir(parents=True, exist_ok=True)

        # Determine runtime from tech_stack
        tech_stack = project.metadata.get('tech_stack', []) if project.metadata else []
        runtime = "python"  # Default
        for tech in tech_stack:
            tech_lower = tech.lower()
            if "node" in tech_lower or "javascript" in tech_lower or "typescript" in tech_lower:
                runtime = "node"
                break
            elif "go" in tech_lower or "golang" in tech_lower:
                runtime = "go"
                break
            elif "rust" in tech_lower:
                runtime = "rust"
                break

        # Create deployment config
        deploy_config = DeploymentConfig(
            platform=platform,
            project_name=project.name,
            runtime=runtime,
            entry_point="main.py" if runtime == "python" else "index.js",
            environment_vars={},
        )

        # Initialize generator with project path
        generator = DeploymentGenerator(project_output_dir)

        # Generate deployment configs
        generated_files = generator.generate_configs(
            config=deploy_config,
            output_dir=project_output_dir / f"deploy-{platform_str}"
        )

        self.console.print(f"  [dim]Generated {len(generated_files)} deployment files[/dim]")

        return {
            "platform": platform_str,
            "generated_files": [str(f) for f in generated_files],
            "path": str(project_output_dir / f"deploy-{platform_str}")
        }

    def _get_stage_output(self, pipeline: PipelineRun, stage: Stage) -> Any:
        """Get output from a completed stage."""
        for result in reversed(pipeline.results):
            if result.stage == stage and result.success:
                return result.output
        raise ValueError(f"No successful {stage.value} result found in pipeline")

    def _stages_between(self, start: Stage, end: Stage) -> List[Stage]:
        """Get stages from start to end inclusive."""
        start_idx = self.STAGE_ORDER.index(start)
        end_idx = self.STAGE_ORDER.index(end)
        return self.STAGE_ORDER[start_idx:end_idx + 1]

    # ─────────────────────────────────────────────────────────────────
    # Checkpoint Handling
    # ─────────────────────────────────────────────────────────────────

    def _checkpoint_before_stage(
        self,
        stage: Stage,
        handler: Optional[Callable[[Checkpoint], str]],
    ) -> str:
        """Create checkpoint before stage execution."""
        checkpoint = Checkpoint(
            stage=stage,
            decision_type=DecisionType.CHOICE,
            prompt=f"Ready to execute {stage.value} stage",
            choices=["proceed", "skip", "abort"],
        )
        return self._get_decision(checkpoint, handler)

    def _checkpoint_before_deploy(
        self,
        test_result: StageResult,
        handler: Optional[Callable[[Checkpoint], str]],
    ) -> str:
        """Create checkpoint before deployment."""
        checkpoint = Checkpoint(
            stage=Stage.DEPLOYMENT,
            decision_type=DecisionType.APPROVE,
            prompt="All tests passed. Proceed with deployment?",
            choices=["proceed", "abort"],
            context={"test_report": test_result.output},
        )
        return self._get_decision(checkpoint, handler)

    def _handle_failure(
        self,
        stage: Stage,
        result: StageResult,
        policy: CheckpointPolicy,
        handler: Optional[Callable[[Checkpoint], str]],
    ) -> str:
        """Handle stage failure based on policy."""
        if policy == CheckpointPolicy.NONE:
            return "abort"

        checkpoint = Checkpoint(
            stage=stage,
            decision_type=DecisionType.CHOICE,
            prompt=f"Stage {stage.value} failed: {result.error}",
            choices=["retry", "skip", "abort", "override"],
            context={"error": result.error, "output": result.output},
        )
        return self._get_decision(checkpoint, handler)

    def _get_decision(
        self,
        checkpoint: Checkpoint,
        handler: Optional[Callable[[Checkpoint], str]],
    ) -> str:
        """Get decision from handler or interactive prompt."""
        if handler:
            return handler(checkpoint)
        return self._interactive_prompt(checkpoint)

    def _interactive_prompt(self, checkpoint: Checkpoint) -> str:
        """Rich interactive prompt for checkpoint decisions."""
        self.console.print()
        self.console.print(Panel(
            checkpoint.prompt,
            title=f"[yellow]Checkpoint: {checkpoint.stage.value}[/yellow]",
            border_style="yellow",
        ))

        if checkpoint.choices:
            choices_display = " | ".join(f"[cyan]{c}[/cyan]" for c in checkpoint.choices)
            self.console.print(f"  Options: {choices_display}")

        if checkpoint.decision_type == DecisionType.OVERRIDE or "override" in (checkpoint.choices or []):
            self.console.print("  [dim]For override, type: override:<instruction>[/dim]")

        while True:
            response = Prompt.ask("  Decision").strip().lower()

            # Handle override format
            if response.startswith("override:"):
                return response

            # Validate against choices
            if checkpoint.choices:
                if response in checkpoint.choices:
                    return response
                self.console.print(f"  [red]Invalid choice. Pick from: {', '.join(checkpoint.choices)}[/red]")
            else:
                return response

    # ─────────────────────────────────────────────────────────────────
    # Output Formatting
    # ─────────────────────────────────────────────────────────────────

    def _print_header(
        self,
        project_id: str,
        policy: CheckpointPolicy,
        start: Stage,
        end: Stage,
    ) -> None:
        """Print pipeline header with ASCII banner."""
        from forge.cli.output import (
            print_pipeline_banner,
            print_pipeline_header,
        )

        # Print large ASCII banner
        print_pipeline_banner()

        # Print pipeline info box
        stages = self._stages_between(start, end)
        stage_names = [s.value for s in stages]
        print_pipeline_header(project_id, policy.value, stage_names)

    def _print_stage_start(self, stage: Stage, retry: bool = False, override: bool = False) -> None:
        """Print stage start message."""
        from forge.cli.output import print_stage_start

        suffix = ""
        if retry:
            suffix = " [yellow](retry)[/yellow]"
        elif override:
            suffix = " [cyan](with override)[/cyan]"

        print_stage_start(stage.value)
        if suffix:
            self.console.print(f"  {suffix}")

    def _print_stage_result(self, result: StageResult) -> None:
        """Print stage result."""
        from forge.cli.output import print_stage_success, print_stage_failed

        if result.success:
            print_stage_success(result.stage.value, "Completed", result.duration_seconds)
        else:
            print_stage_failed(result.stage.value, str(result.error) if result.error else "Failed")
            self.console.print(f"  [dim]Duration: {result.duration_seconds:.1f}s[/dim]")

    def _print_skip(self, stage: Stage) -> None:
        """Print stage skip message."""
        from forge.cli.output import ForgeStyles
        icon = ForgeStyles.ICONS["skipped"]
        self.console.print(f"\n[{ForgeStyles.SKIPPED}]{icon} {stage.value.upper()} (skipped)[/{ForgeStyles.SKIPPED}]")

    def _print_summary(self, pipeline: PipelineRun) -> None:
        """Print pipeline summary using enhanced output."""
        from forge.cli.output import print_pipeline_summary

        # Convert results to dict format for output function
        results = [
            {
                "stage": r.stage.value,
                "success": r.success,
                "duration_seconds": r.duration_seconds,
            }
            for r in pipeline.results
        ]

        print_pipeline_summary(
            results=results,
            total_duration=pipeline.total_duration,
            succeeded=pipeline.succeeded,
        )

    def close(self):
        """Cleanup resources."""
        for layer in self._layers.values():
            if hasattr(layer, 'close'):
                layer.close()
        self._layers.clear()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
