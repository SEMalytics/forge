"""
Factory for creating code generators

Provides a unified interface for creating generator instances.
"""

from pathlib import Path
from typing import Optional

from forge.generators.base import CodeGenerator, GeneratorBackend, GeneratorError
from forge.generators.codegen_api import CodeGenAPIGenerator
from forge.generators.claude_code import ClaudeCodeGenerator
from forge.utils.logger import logger


class GeneratorFactory:
    """
    Factory for creating generator instances.

    Handles backend-specific configuration and validation.
    """

    @staticmethod
    def create(backend: GeneratorBackend, **kwargs) -> CodeGenerator:
        """
        Create generator instance based on backend.

        Args:
            backend: Generator backend to use
            **kwargs: Backend-specific configuration

        Returns:
            CodeGenerator instance

        Raises:
            GeneratorError: If backend is invalid or configuration is missing

        Examples:
            >>> # Create CodeGen API generator
            >>> gen = GeneratorFactory.create(
            ...     GeneratorBackend.CODEGEN_API,
            ...     api_key="your-key",
            ...     org_id=None  # Optional
            ... )

            >>> # Create Claude Code generator
            >>> gen = GeneratorFactory.create(
            ...     GeneratorBackend.CLAUDE_CODE,
            ...     workspace_dir=Path(".forge/workspaces")
            ... )
        """
        if backend == GeneratorBackend.CODEGEN_API:
            return GeneratorFactory._create_codegen_api(**kwargs)

        elif backend == GeneratorBackend.CLAUDE_CODE:
            return GeneratorFactory._create_claude_code(**kwargs)

        else:
            raise GeneratorError(f"Unknown backend: {backend}")

    @staticmethod
    def _create_codegen_api(**kwargs) -> CodeGenAPIGenerator:
        """
        Create CodeGen API generator.

        Required kwargs:
            - api_key: API key

        Optional kwargs:
            - org_id: Organization ID
            - base_url: API base URL
            - timeout: Request timeout
            - max_retries: Maximum retries
        """
        # Validate required parameters
        api_key = kwargs.get('api_key')
        if not api_key:
            raise GeneratorError("api_key is required for CodeGen API backend")

        # Create generator with optional parameters
        generator = CodeGenAPIGenerator(
            api_key=api_key,
            org_id=kwargs.get('org_id'),  # Optional
            base_url=kwargs.get('base_url', "https://api.codegen.ai/v1"),
            timeout=kwargs.get('timeout', 300),
            max_retries=kwargs.get('max_retries', 3)
        )

        logger.info("Created CodeGen API generator")
        return generator

    @staticmethod
    def _create_claude_code(**kwargs) -> ClaudeCodeGenerator:
        """
        Create Claude Code generator.

        Optional kwargs:
            - workspace_dir: Workspace directory
            - claude_binary: Path to claude binary
        """
        workspace_dir = kwargs.get('workspace_dir')
        if workspace_dir and not isinstance(workspace_dir, Path):
            workspace_dir = Path(workspace_dir)

        generator = ClaudeCodeGenerator(
            workspace_dir=workspace_dir,
            claude_binary=kwargs.get('claude_binary', 'claude')
        )

        logger.info("Created Claude Code generator")
        return generator

    @staticmethod
    def create_from_config(backend_name: str, config: dict) -> CodeGenerator:
        """
        Create generator from configuration dictionary.

        Args:
            backend_name: Backend name ("codegen_api" or "claude_code")
            config: Configuration dictionary

        Returns:
            CodeGenerator instance

        Raises:
            GeneratorError: If backend or configuration is invalid

        Examples:
            >>> config = {
            ...     "api_key": "your-key",
            ...     "org_id": None
            ... }
            >>> gen = GeneratorFactory.create_from_config("codegen_api", config)
        """
        try:
            backend = GeneratorBackend(backend_name)
        except ValueError:
            raise GeneratorError(f"Invalid backend name: {backend_name}")

        return GeneratorFactory.create(backend, **config)

    @staticmethod
    def get_available_backends() -> list[str]:
        """
        Get list of available backend names.

        Returns:
            List of backend names
        """
        return [backend.value for backend in GeneratorBackend]

    @staticmethod
    def detect_best_backend() -> Optional[GeneratorBackend]:
        """
        Detect the best available backend.

        Checks for:
        1. CodeGen API key in environment
        2. Claude Code CLI availability

        Returns:
            Best available backend or None
        """
        import os
        import shutil

        # Check for CodeGen API key
        if os.getenv('CODEGEN_API_KEY'):
            logger.info("Detected CodeGen API key, using CodeGen API backend")
            return GeneratorBackend.CODEGEN_API

        # Check for Claude Code CLI
        if shutil.which('claude'):
            logger.info("Detected Claude CLI, using Claude Code backend")
            return GeneratorBackend.CLAUDE_CODE

        logger.warning("No generator backend detected")
        return None
