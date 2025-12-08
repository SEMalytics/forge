"""
CodeGen repository setup automation.

Handles automatic detection and setup of CodeGen repositories to ensure
they're properly configured before agent runs.
"""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from forge.utils.logger import logger
from forge.integrations.codegen_client import CodeGenClient, CodeGenError


class CodeGenRepositorySetup:
    """
    Manages CodeGen repository setup and validation.

    Ensures repositories are properly configured with setup commands
    before running agent tasks.
    """

    def __init__(self, client: CodeGenClient):
        """
        Initialize setup manager.

        Args:
            client: CodeGenClient instance
        """
        self.client = client

    async def ensure_repository_setup(
        self,
        repo_id: int,
        auto_setup: bool = True,
        setup_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ensure repository is properly set up for agent runs.

        Checks if repository has setup commands configured. If not, and
        auto_setup is enabled, triggers setup command generation.

        Args:
            repo_id: Repository ID to check
            auto_setup: Automatically generate setup commands if NOT_SETUP
            setup_prompt: Custom prompt for setup generation

        Returns:
            Repository status information

        Raises:
            CodeGenError: If setup fails or repository not found
        """
        logger.info(f"Checking setup status for repository {repo_id}...")

        # Get repository details
        try:
            repo = await self.client.get_repository(repo_id)
        except Exception as e:
            raise CodeGenError(f"Failed to get repository {repo_id}: {e}")

        setup_status = repo.get("setup_status", "UNKNOWN")
        repo_name = repo.get("full_name", f"repo-{repo_id}")

        logger.info(f"Repository: {repo_name}")
        logger.info(f"Setup status: {setup_status}")

        # Check if setup is needed
        if setup_status == "NOT_SETUP":
            if not auto_setup:
                raise CodeGenError(
                    f"Repository {repo_name} is not set up. "
                    f"Setup commands are required before running agents.\n"
                    f"Fix: Run setup manually at https://codegen.com/repos/{repo['name']}/setup-commands\n"
                    f"Or enable auto_setup=True"
                )

            logger.warning(f"Repository {repo_name} has NOT_SETUP status")
            logger.info("Automatically generating setup commands...")

            # Generate setup commands
            await self._generate_setup_commands(repo_id, repo_name, setup_prompt)

            # Wait for setup to complete
            await self._wait_for_setup_completion(repo_id, timeout=300)

            # Re-fetch repository to get updated status
            repo = await self.client.get_repository(repo_id)
            setup_status = repo.get("setup_status")

            logger.info(f"Updated setup status: {setup_status}")

        return repo

    async def _generate_setup_commands(
        self,
        repo_id: int,
        repo_name: str,
        custom_prompt: Optional[str] = None
    ):
        """
        Generate setup commands for a repository.

        Args:
            repo_id: Repository ID
            repo_name: Repository full name (for logging)
            custom_prompt: Optional custom instructions
        """
        logger.info(f"Generating setup commands for {repo_name}...")

        # Build prompt
        prompt = custom_prompt or self._build_default_setup_prompt(repo_name)

        try:
            result = await self.client.generate_setup_commands(
                repo_id=repo_id,
                prompt=prompt
            )

            agent_run_id = result.get("agent_run_id")
            logger.info(f"Setup generation started: agent_run_id={agent_run_id}")
            logger.info(f"Monitor at: https://codegen.com/agent/trace/{agent_run_id}")

            return agent_run_id

        except Exception as e:
            raise CodeGenError(f"Failed to generate setup commands: {e}")

    async def _wait_for_setup_completion(
        self,
        repo_id: int,
        timeout: int = 300,
        poll_interval: int = 10
    ):
        """
        Wait for repository setup to complete.

        Args:
            repo_id: Repository ID
            timeout: Maximum wait time (seconds)
            poll_interval: Time between status checks (seconds)

        Raises:
            CodeGenError: If setup times out or fails
        """
        logger.info(f"Waiting for setup to complete (timeout: {timeout}s)...")

        import time
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            if elapsed > timeout:
                raise CodeGenError(
                    f"Setup command generation timed out after {timeout}s. "
                    f"Check status at: https://codegen.com/repos"
                )

            # Check repository status
            try:
                repo = await self.client.get_repository(repo_id)
                status = repo.get("setup_status")

                if status != "NOT_SETUP":
                    logger.info(f"Setup completed! New status: {status}")
                    return

                logger.debug(f"Still setting up... ({int(elapsed)}s elapsed)")

            except Exception as e:
                logger.warning(f"Error checking status: {e}")

            await asyncio.sleep(poll_interval)

    def _build_default_setup_prompt(self, repo_name: str) -> str:
        """
        Build default setup command generation prompt.

        Args:
            repo_name: Repository full name

        Returns:
            Setup prompt string
        """
        # Detect language from repo name/metadata
        # For now, assume Python since that's our primary use case

        return (
            f"Generate setup commands for {repo_name}. "
            "This is a Python project. "
            "Install dependencies and prepare the development environment. "
            "Use poetry if pyproject.toml exists, otherwise use pip with requirements.txt. "
            "Setup should be non-interactive and idempotent."
        )

    async def validate_repository_ready(
        self,
        repo_id: int
    ) -> bool:
        """
        Validate that repository is ready for agent runs.

        Args:
            repo_id: Repository ID

        Returns:
            True if ready, False otherwise
        """
        try:
            repo = await self.client.get_repository(repo_id)
            status = repo.get("setup_status", "UNKNOWN")

            if status == "NOT_SETUP":
                return False

            logger.info(f"Repository {repo.get('full_name')} is ready (status: {status})")
            return True

        except Exception as e:
            logger.error(f"Failed to validate repository: {e}")
            return False


async def ensure_repository_setup(
    client: CodeGenClient,
    repo_id: int,
    auto_setup: bool = True,
    setup_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to ensure repository setup.

    Args:
        client: CodeGenClient instance
        repo_id: Repository ID
        auto_setup: Automatically generate setup if needed
        setup_prompt: Custom setup prompt

    Returns:
        Repository information

    Example:
        >>> client = CodeGenClient(api_token="...", org_id="123")
        >>> repo = await ensure_repository_setup(client, repo_id=456)
        >>> print(f"Ready: {repo['setup_status']}")
    """
    setup_manager = CodeGenRepositorySetup(client)
    return await setup_manager.ensure_repository_setup(
        repo_id=repo_id,
        auto_setup=auto_setup,
        setup_prompt=setup_prompt
    )
