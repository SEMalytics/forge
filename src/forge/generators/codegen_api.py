"""
CodeGen API backend for code generation

Implements code generation using the CodeGen API with parallel execution support.
Supports streaming output for real-time progress feedback.
"""

import httpx
import asyncio
import time
import re
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from forge.generators.base import (
    CodeGenerator,
    GenerationContext,
    GenerationResult,
    GeneratorError
)
from forge.utils.logger import logger

if TYPE_CHECKING:
    from forge.core.streaming import StreamEmitter


class CodeGenAPIGenerator(CodeGenerator):
    """
    Code generator using CodeGen API.

    Supports:
    - Parallel execution
    - Rate limiting with retries
    - KnowledgeForge pattern injection
    - File parsing from output
    """

    def __init__(
        self,
        api_key: str,
        org_id: Optional[str] = None,
        base_url: str = "https://api.codegen.com/v1",
        timeout: int = 300,
        max_retries: int = 3
    ):
        """
        Initialize CodeGen API generator.

        Args:
            api_key: CodeGen API key
            org_id: Optional organization ID
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        if not api_key:
            raise GeneratorError("API key is required")

        self.api_key = api_key
        self.org_id = org_id
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers=self._build_headers()
        )

        logger.info(f"Initialized CodeGen API generator (base_url={base_url})")

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for API requests"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if self.org_id:
            headers["X-Organization-ID"] = self.org_id

        return headers

    async def generate(self, context: GenerationContext) -> GenerationResult:
        """
        Generate code using CodeGen agent API.

        Args:
            context: Generation context

        Returns:
            GenerationResult with generated files

        Raises:
            GeneratorError: If generation fails
        """
        self.validate_context(context)

        start_time = time.time()

        try:
            # Build prompt with KF patterns
            prompt = self._build_prompt(context)

            logger.info(f"Generating code for task {context.task_id}")
            logger.debug(f"Prompt length: {len(prompt)} chars")

            # Use CodeGen agent run API
            from forge.integrations.codegen_client import CodeGenClient, CodeGenError

            codegen_client = CodeGenClient(
                api_token=self.api_key,
                org_id=self.org_id,
                timeout=self.timeout
            )

            # Determine repository ID
            repo_id = await self._get_repository_id(codegen_client, context)

            # Stop if no repository configured
            if repo_id is None:
                error_msg = "No CodeGen repository configured - cannot proceed"
                logger.error(error_msg)
                return GenerationResult(
                    success=False,
                    error=error_msg,
                    duration_seconds=time.time() - start_time,
                    metadata={"task_id": context.task_id}
                )

            # Create agent run and wait for completion
            result_data = await codegen_client.generate_code(
                prompt=prompt,
                repository_id=repo_id,
                on_progress=lambda status: logger.debug(f"CodeGen status: {status.get('status')}")
            )

            duration = time.time() - start_time

            # Extract files from CodeGen result
            # CodeGen may return files in different formats depending on the agent
            files = {}

            # Try to extract files from the result
            if isinstance(result_data, dict):
                # Check for files in common response fields
                if "files" in result_data:
                    for file_info in result_data["files"]:
                        path = file_info.get("path") or file_info.get("filepath")
                        content = file_info.get("content") or file_info.get("code")
                        if path and content:
                            files[path] = content

                # Check for output field
                if "output" in result_data and isinstance(result_data["output"], dict):
                    files.update(result_data["output"])

                # If no files found, try to parse from generated text
                if not files and "generated_text" in result_data:
                    files = self._parse_files(result_data["generated_text"])

            if not files:
                # Fallback: treat entire result as text and parse
                result_text = str(result_data)
                files = self._parse_files(result_text)

            if not files:
                logger.warning(f"No files generated from CodeGen response for task {context.task_id}")
                logger.debug(f"CodeGen result: {result_data}")

            result = GenerationResult(
                success=len(files) > 0,
                files=files,
                duration_seconds=duration,
                metadata={
                    "task_id": context.task_id,
                    "backend": "codegen_api",
                    "agent_run_id": result_data.get("id") or result_data.get("agent_run_id"),
                    "codegen_result": result_data
                }
            )

            logger.info(f"Generated {len(files)} files in {duration:.1f}s")
            return result

        except CodeGenError as e:
            duration = time.time() - start_time
            error_msg = f"CodeGen API error: {e}"
            logger.error(error_msg)

            return GenerationResult(
                success=False,
                error=error_msg,
                duration_seconds=duration,
                metadata={"task_id": context.task_id}
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Generation failed: {e}"
            logger.error(error_msg)

            return GenerationResult(
                success=False,
                error=error_msg,
                duration_seconds=duration,
                metadata={"task_id": context.task_id}
            )

    async def generate_streaming(
        self,
        context: GenerationContext,
        emitter: 'StreamEmitter'
    ) -> GenerationResult:
        """
        Generate code with streaming progress updates.

        Provides real-time feedback during CodeGen API generation.

        Args:
            context: Generation context
            emitter: StreamEmitter for progress events

        Returns:
            GenerationResult with generated files
        """
        self.validate_context(context)

        start_time = time.time()

        try:
            await emitter.started(f"Starting code generation for {context.task_id}")
            await emitter.stage("preparation", "Preparing generation context...")

            # Check for cancellation
            if emitter.is_cancelled:
                await emitter.cancelled()
                return GenerationResult(
                    success=False,
                    error="Cancelled",
                    duration_seconds=time.time() - start_time
                )

            # Build prompt
            await emitter.progress(0.1, "Building prompt with KF patterns...")
            prompt = self._build_prompt(context)

            await emitter.stage("connection", "Connecting to CodeGen API...")
            await emitter.progress(0.15)

            # Initialize CodeGen client
            from forge.integrations.codegen_client import CodeGenClient, CodeGenError

            codegen_client = CodeGenClient(
                api_token=self.api_key,
                org_id=self.org_id,
                timeout=self.timeout
            )

            # Get repository
            await emitter.progress(0.2, "Resolving repository...")
            repo_id = await self._get_repository_id(codegen_client, context)

            if emitter.is_cancelled:
                await emitter.cancelled()
                return GenerationResult(
                    success=False,
                    error="Cancelled",
                    duration_seconds=time.time() - start_time
                )

            if repo_id is None:
                error_msg = "No CodeGen repository configured"
                await emitter.failed(error_msg)
                return GenerationResult(
                    success=False,
                    error=error_msg,
                    duration_seconds=time.time() - start_time
                )

            # Start generation
            await emitter.stage("generation", "Generating code...")
            await emitter.progress(0.25)

            # Progress callback for CodeGen API
            last_progress = [0.25]

            async def progress_callback(status: Dict[str, Any]):
                """Update progress based on CodeGen status"""
                if emitter.is_cancelled:
                    return

                status_str = status.get("status", "unknown")
                await emitter.status(f"CodeGen: {status_str}")

                # Increment progress gradually
                current = last_progress[0]
                if current < 0.85:
                    last_progress[0] = min(current + 0.05, 0.85)
                    await emitter.progress(last_progress[0])

            # Run generation with progress updates
            result_data = await codegen_client.generate_code(
                prompt=prompt,
                repository_id=repo_id,
                on_progress=progress_callback
            )

            if emitter.is_cancelled:
                await emitter.cancelled()
                return GenerationResult(
                    success=False,
                    error="Cancelled",
                    duration_seconds=time.time() - start_time
                )

            # Parse results
            await emitter.stage("parsing", "Processing generated files...")
            await emitter.progress(0.9)

            duration = time.time() - start_time
            files = {}

            # Extract files from result
            if isinstance(result_data, dict):
                if "files" in result_data:
                    for file_info in result_data["files"]:
                        path = file_info.get("path") or file_info.get("filepath")
                        content = file_info.get("content") or file_info.get("code")
                        if path and content:
                            files[path] = content
                            await emitter.file_completed(path, len(content))

                if "output" in result_data and isinstance(result_data["output"], dict):
                    for path, content in result_data["output"].items():
                        files[path] = content
                        await emitter.file_completed(path, len(content))

                if not files and "generated_text" in result_data:
                    files = self._parse_files(result_data["generated_text"])
                    for path, content in files.items():
                        await emitter.file_completed(path, len(content))

            if not files:
                result_text = str(result_data)
                files = self._parse_files(result_text)
                for path, content in files.items():
                    await emitter.file_completed(path, len(content))

            result = GenerationResult(
                success=len(files) > 0,
                files=files,
                duration_seconds=duration,
                metadata={
                    "task_id": context.task_id,
                    "backend": "codegen_api",
                    "agent_run_id": result_data.get("id") or result_data.get("agent_run_id"),
                }
            )

            if result.success:
                await emitter.completed(
                    f"Generated {len(files)} files",
                    metadata={"files": list(files.keys()), "duration": duration}
                )
            else:
                await emitter.failed("No files generated")

            return result

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Generation failed: {e}"
            await emitter.failed(error_msg)

            return GenerationResult(
                success=False,
                error=error_msg,
                duration_seconds=duration,
                metadata={"task_id": context.task_id}
            )

    def supports_streaming(self) -> bool:
        """CodeGen API supports streaming progress updates"""
        return True

    async def _ensure_repository_setup(
        self,
        client: "CodeGenClient",
        repo_id: int,
        repo_info: Dict[str, Any]
    ):
        """
        Ensure repository is properly set up for agent runs.

        Checks if repository has setup commands configured. If NOT_SETUP,
        automatically triggers setup command generation.

        Args:
            client: CodeGen client instance
            repo_id: Repository ID
            repo_info: Repository information dict

        Raises:
            GeneratorError: If setup fails
        """
        setup_status = repo_info.get("setup_status", "UNKNOWN")
        repo_name = repo_info.get("full_name", f"repo-{repo_id}")

        if setup_status == "NOT_SETUP":
            logger.warning(f"Repository {repo_name} requires setup")
            logger.info("Automatically generating setup commands...")

            try:
                from forge.integrations.codegen_setup import ensure_repository_setup

                # Trigger setup with auto-setup enabled
                await ensure_repository_setup(
                    client=client,
                    repo_id=repo_id,
                    auto_setup=True
                )

                logger.info(f"Repository {repo_name} setup completed")

            except Exception as e:
                logger.error(f"Failed to setup repository: {e}")
                raise GeneratorError(
                    f"Repository {repo_name} is not set up and automatic setup failed.\n"
                    f"Please configure setup commands manually at:\n"
                    f"https://codegen.com/repos/{repo_info.get('name', '')}/setup-commands"
                )

    async def _get_repository_id(
        self,
        client: "CodeGenClient",
        context: GenerationContext
    ) -> Optional[int]:
        """
        Determine the CodeGen repository ID to use.

        Priority order:
        1. Detect git remote URL from current directory
        2. Find matching CodeGen repository by GitHub URL
        3. Prompt user to set up repository if not found
        4. Fall back to environment variable CODEGEN_REPO_ID (override)
        5. None (with warning)

        Args:
            client: CodeGen client instance
            context: Generation context

        Returns:
            Repository ID or None
        """
        import os
        from forge.utils.git_utils import get_github_repo_info, format_repo_identifier

        # Check for explicit override first
        repo_id_env = os.getenv("CODEGEN_REPO_ID")
        if repo_id_env:
            try:
                repo_id = int(repo_id_env)
                logger.info(f"Using repository ID from CODEGEN_REPO_ID override: {repo_id}")
                return repo_id
            except ValueError:
                logger.warning(f"Invalid CODEGEN_REPO_ID: {repo_id_env}")

        # Detect git remote
        github_info = get_github_repo_info()
        if not github_info:
            logger.warning("Not in a git repository or no GitHub remote found")
            logger.warning("CodeGen agents will run without repository context")
            return None

        owner, repo_name = github_info
        repo_identifier = format_repo_identifier(owner, repo_name)
        logger.info(f"Detected GitHub repository: {repo_identifier}")

        # Try to find matching CodeGen repository
        try:
            # Search by full identifier first
            repo = await client.find_repository_by_name(repo_identifier)
            if repo:
                repo_id = repo.get("id")
                logger.info(f"Found CodeGen repository '{repo.get('name')}' (ID: {repo_id})")

                # Check repository setup status
                await _ensure_repository_setup(client, repo_id, repo)

                return repo_id

            # Try just the repo name
            repo = await client.find_repository_by_name(repo_name)
            if repo:
                repo_id = repo.get("id")
                logger.info(f"Found CodeGen repository '{repo.get('name')}' (ID: {repo_id})")

                # Check repository setup status
                await _ensure_repository_setup(client, repo_id, repo)

                return repo_id

            # No matching repository found
            logger.error(f"Cannot auto-detect CodeGen repository for {repo_identifier}")
            logger.error("")
            logger.error("CodeGen API does not support repository listing.")
            logger.error("You must manually configure the repository ID.")
            logger.error("")
            logger.error("To fix this:")
            logger.error("")
            logger.error("1. Ensure GitHub App is installed:")
            logger.error(f"   Go to: https://github.com/apps/codegen-sh")
            logger.error(f"   Click 'Configure' next to {owner}")
            logger.error(f"   Select '{repo_identifier}' repository")
            logger.error("")
            logger.error("2. Find your repository ID:")
            logger.error(f"   Go to: https://codegen.com/repos")
            logger.error(f"   Find '{repo_identifier}' in the list")
            logger.error("   Note the repository ID (shown in URL or repo details)")
            logger.error("")
            logger.error("3. Set environment variable:")
            logger.error("   Add to ~/.zshrc:")
            logger.error("   export CODEGEN_REPO_ID=<your-repo-id>")
            logger.error("")
            logger.error("4. Reload and retry:")
            logger.error("   source ~/.zshrc")
            logger.error("   forge build -p <project-id>")
            logger.error("")

        except Exception as e:
            logger.error(f"Error checking CodeGen repositories: {e}")
            logger.error("")
            logger.error("Unable to auto-detect repository. Set CODEGEN_REPO_ID manually:")
            logger.error("1. Go to https://codegen.com/repos")
            logger.error(f"2. Find repository for: {repo_identifier}")
            logger.error("3. Set: export CODEGEN_REPO_ID=<repo-id>")
            logger.error("")

        # Don't continue without proper repository context
        logger.error("STOPPING: Cannot proceed without CodeGen repository configured")
        return None

    def _build_prompt(self, context: GenerationContext) -> str:
        """
        Build generation prompt with KF pattern injection.

        Args:
            context: Generation context

        Returns:
            Complete prompt string
        """
        prompt_parts = []

        # System context
        prompt_parts.append("You are an expert software engineer generating production-ready code.")
        prompt_parts.append("")

        # Project context
        prompt_parts.append("## Project Context")
        prompt_parts.append(context.project_context)
        prompt_parts.append("")

        # Tech stack
        if context.tech_stack:
            prompt_parts.append("## Technology Stack")
            prompt_parts.append(", ".join(context.tech_stack))
            prompt_parts.append("")

        # Dependencies
        if context.dependencies:
            prompt_parts.append("## Dependencies")
            prompt_parts.append("This task depends on:")
            for dep in context.dependencies:
                prompt_parts.append(f"- {dep}")
            prompt_parts.append("")

        # KnowledgeForge patterns
        if context.knowledgeforge_patterns:
            prompt_parts.append("## KnowledgeForge Patterns")
            prompt_parts.append("Apply these patterns:")
            for pattern in context.knowledgeforge_patterns:
                prompt_parts.append(f"- {pattern}")
            prompt_parts.append("")

        # File structure
        if context.file_structure:
            prompt_parts.append("## Existing File Structure")
            for filepath, content in context.file_structure.items():
                prompt_parts.append(f"### {filepath}")
                prompt_parts.append(f"```")
                prompt_parts.append(content[:500])  # First 500 chars
                prompt_parts.append("```")
            prompt_parts.append("")

        # Task specification
        prompt_parts.append("## Task Specification")
        prompt_parts.append(context.specification)
        prompt_parts.append("")

        # Output format
        prompt_parts.append("## Output Format")
        prompt_parts.append("Generate code files in the following format:")
        prompt_parts.append("")
        prompt_parts.append("### path/to/file.py")
        prompt_parts.append("```python")
        prompt_parts.append("# code here")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("Include all necessary files with complete implementations.")

        return "\n".join(prompt_parts)

    def _parse_files(self, generated_text: str) -> Dict[str, str]:
        """
        Parse files from generated text.

        Expects format:
        ### path/to/file.ext
        ```language
        code content
        ```

        Args:
            generated_text: Raw generated text

        Returns:
            Dictionary mapping file paths to content
        """
        files = {}

        # Pattern to match file blocks
        # ### filepath
        # ```language
        # content
        # ```
        pattern = r'###\s+(.+?)\n```(?:\w+)?\n(.*?)```'

        matches = re.finditer(pattern, generated_text, re.DOTALL)

        for match in matches:
            filepath = match.group(1).strip()
            content = match.group(2).strip()

            files[filepath] = content

        # Fallback: single code block
        if not files:
            code_block = re.search(r'```(?:\w+)?\n(.*?)```', generated_text, re.DOTALL)
            if code_block:
                # Try to infer filename from context
                content = code_block.group(1).strip()
                files["generated_code.py"] = content

        return files

    async def health_check(self) -> bool:
        """
        Check if CodeGen API is available.

        Returns:
            True if API is healthy
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/health",
                timeout=10.0
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def estimate_duration(self, context: GenerationContext) -> int:
        """
        Estimate generation duration.

        Based on:
        - Specification length
        - Number of dependencies
        - Number of KF patterns

        Args:
            context: Generation context

        Returns:
            Estimated duration in seconds
        """
        base_time = 30  # Base 30 seconds

        # Add time based on specification length
        spec_time = len(context.specification) // 1000 * 5  # 5s per 1000 chars

        # Add time for dependencies
        dep_time = len(context.dependencies) * 10  # 10s per dependency

        # Add time for patterns
        pattern_time = len(context.knowledgeforge_patterns) * 5  # 5s per pattern

        total = base_time + spec_time + dep_time + pattern_time

        return min(total, self.timeout)  # Cap at timeout

    def supports_parallel(self) -> bool:
        """CodeGen API supports parallel execution"""
        return True

    def max_context_tokens(self) -> int:
        """Maximum context window size"""
        return 8192  # Typical API limit

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    def __del__(self):
        """Cleanup on deletion"""
        # Don't try to close async client in __del__ as there may be no event loop
        # The client will be cleaned up by garbage collection
        pass
