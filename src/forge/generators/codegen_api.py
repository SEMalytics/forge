"""
CodeGen API backend for code generation

Implements code generation using the CodeGen API with parallel execution support.
"""

import httpx
import asyncio
import time
import re
from typing import Dict, List, Optional, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from forge.generators.base import (
    CodeGenerator,
    GenerationContext,
    GenerationResult,
    GeneratorError
)
from forge.utils.logger import logger


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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def generate(self, context: GenerationContext) -> GenerationResult:
        """
        Generate code using CodeGen API.

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

            # Make API request
            response = await self.client.post(
                f"{self.base_url}/generate",
                json={
                    "prompt": prompt,
                    "max_tokens": 4000,
                    "temperature": 0.2,
                    "stop": ["```\n\n", "---END---"]
                }
            )

            response.raise_for_status()
            data = response.json()

            # Parse generated code
            generated_text = data.get("completion", data.get("text", ""))
            files = self._parse_files(generated_text)

            duration = time.time() - start_time

            if not files:
                raise GeneratorError("No files generated from API response")

            result = GenerationResult(
                success=True,
                files=files,
                duration_seconds=duration,
                tokens_used=data.get("usage", {}).get("total_tokens"),
                metadata={
                    "task_id": context.task_id,
                    "model": data.get("model"),
                    "backend": "codegen_api"
                }
            )

            logger.info(f"Generated {len(files)} files in {duration:.1f}s")
            return result

        except httpx.HTTPError as e:
            duration = time.time() - start_time
            error_msg = f"API request failed: {e}"
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
        try:
            asyncio.create_task(self.close())
        except:
            pass
