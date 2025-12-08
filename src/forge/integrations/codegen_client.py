"""
CodeGen API integration for Forge

Provides integration with CodeGen's agent-based code generation API.
"""

import httpx
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class CodeGenError(ForgeError):
    """Errors during CodeGen API interactions"""
    pass


class CodeGenClient:
    """
    Client for CodeGen API integration.

    Manages agent runs, status polling, and result retrieval.
    """

    BASE_URL = "https://api.codegen.com/v1"

    def __init__(
        self,
        api_token: str,
        org_id: Optional[str] = None,
        timeout: int = 300,
        poll_interval: int = 5
    ):
        """
        Initialize CodeGen client.

        Args:
            api_token: CodeGen API token
            org_id: Organization ID (optional - will be auto-fetched if not provided)
            timeout: Maximum time to wait for agent completion (seconds)
            poll_interval: Time between status checks (seconds)

        Raises:
            CodeGenError: If initialization fails
        """
        if not api_token:
            raise CodeGenError("CodeGen API token is required")

        self.api_token = api_token
        self.org_id = org_id  # May be None initially
        self.timeout = timeout
        self.poll_interval = poll_interval

        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        if org_id:
            logger.info(f"Initialized CodeGen client for org: {org_id}")
        else:
            logger.info("Initialized CodeGen client (org_id will be auto-fetched)")

    async def _ensure_org_id(self):
        """Ensure org_id is set, fetching it if necessary."""
        if self.org_id:
            return

        logger.info("Auto-fetching organization ID...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/user",
                    headers=self.headers
                )
                response.raise_for_status()
                user_info = response.json()

                # Extract org_id from user info
                # API may return it as 'organization_id', 'org_id', or in 'organizations' array
                self.org_id = (
                    user_info.get("organization_id") or
                    user_info.get("org_id") or
                    (user_info.get("organizations", [{}])[0].get("id") if user_info.get("organizations") else None)
                )

                if not self.org_id:
                    raise CodeGenError(
                        "Could not auto-fetch organization ID. Please provide it explicitly via "
                        "CODEGEN_ORG_ID environment variable or in forge.yaml config."
                    )

                logger.info(f"Auto-fetched organization ID: {self.org_id}")

        except httpx.HTTPStatusError as e:
            raise CodeGenError(f"Failed to fetch organization ID: {e.response.text}")
        except Exception as e:
            raise CodeGenError(f"Failed to fetch organization ID: {e}")

    async def create_agent_run(
        self,
        prompt: str,
        repository_id: Optional[int] = None,
        image_path: Optional[Path] = None
    ) -> str:
        """
        Create and start an agent run.

        Args:
            prompt: Task description for the agent
            repository_id: Optional repository ID (integer) to work in
            image_path: Optional image file to include

        Returns:
            Agent run ID

        Raises:
            CodeGenError: If agent creation fails
        """
        # Ensure org_id is available
        await self._ensure_org_id()

        logger.info("Creating CodeGen agent run...")
        logger.debug(f"Prompt: {prompt[:200]}...")

        endpoint = f"{self.BASE_URL}/organizations/{self.org_id}/agent/run"

        try:
            # Prepare request data
            payload = {"prompt": prompt}

            # Debug: Log repository_id value and type
            logger.info(f"create_agent_run called with repository_id={repository_id} (type: {type(repository_id).__name__})")

            if repository_id:
                # API uses "repo_id" not "repository_id"
                payload["repo_id"] = repository_id
                # CRITICAL: Must specify agent_type for repo_id to work!
                payload["agent_type"] = "codegen"
                logger.info(f"✓ Including repo_id in request: {repository_id} with agent_type=codegen")
            else:
                logger.warning(f"⚠ No repo_id provided (repository_id={repository_id}) - agent will run without repo context")

            logger.info(f"API payload: {payload}")

            # Handle image upload case vs JSON-only
            async with httpx.AsyncClient(timeout=30.0) as client:
                if image_path and image_path.exists():
                    # For multipart/form-data with files, use data= and files=
                    files = {"image": open(image_path, "rb")}
                    # Remove Content-Type header for multipart/form-data (httpx sets it automatically)
                    headers = {k: v for k, v in self.headers.items() if k.lower() != "content-type"}
                    response = await client.post(
                        endpoint,
                        headers=headers,
                        data=payload,
                        files=files
                    )
                    files["image"].close()
                else:
                    # For JSON payload without files, use json=
                    response = await client.post(
                        endpoint,
                        headers=self.headers,
                        json=payload
                    )

            response.raise_for_status()
            result = response.json()

            # Log full response for debugging
            logger.info(f"API Response Status: {response.status_code}")
            logger.info(f"API Response Body: {result}")

            agent_run_id = result.get("agent_run_id") or result.get("id")

            if not agent_run_id:
                raise CodeGenError(f"No agent_run_id in response: {result}")

            # Check if repository was actually set in the response
            response_repo_id = result.get("repository_id") or result.get("repo_id")
            if response_repo_id:
                logger.info(f"✓ Agent run {agent_run_id} created with repository ID: {response_repo_id}")
            else:
                logger.warning(f"⚠ Agent run {agent_run_id} created WITHOUT repository context (API may have rejected repo_id)")

            return agent_run_id

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating agent run: {e}")
            raise CodeGenError(f"Failed to create agent run: {e.response.text}")
        except Exception as e:
            logger.error(f"Error creating agent run: {e}")
            raise CodeGenError(f"Failed to create agent run: {e}")

    async def get_agent_run_status(self, agent_run_id: str) -> Dict[str, Any]:
        """
        Get current status of an agent run.

        Args:
            agent_run_id: ID of the agent run

        Returns:
            Status information including progress and results

        Raises:
            CodeGenError: If status retrieval fails
        """
        # Ensure org_id is available
        await self._ensure_org_id()

        endpoint = f"{self.BASE_URL}/organizations/{self.org_id}/agent/run/{agent_run_id}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, headers=self.headers)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting agent status: {e}")
            raise CodeGenError(f"Failed to get agent status: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            raise CodeGenError(f"Failed to get agent status: {e}")

    async def wait_for_completion(
        self,
        agent_run_id: str,
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Poll agent run until completion or timeout.

        Args:
            agent_run_id: ID of the agent run
            on_progress: Optional callback for progress updates

        Returns:
            Final status and results

        Raises:
            CodeGenError: If polling fails or times out
        """
        logger.info(f"Waiting for agent run {agent_run_id} to complete...")

        start_time = time.time()

        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > self.timeout:
                raise CodeGenError(
                    f"Agent run timed out after {self.timeout}s"
                )

            # Get current status
            status = await self.get_agent_run_status(agent_run_id)

            # Call progress callback if provided
            if on_progress:
                on_progress(status)

            # Check if complete
            # Note: Exact status field names may vary - adjust based on actual API
            current_status = status.get("status", "").lower()

            if current_status in ["complete", "completed", "success", "done"]:
                logger.info("Agent run completed successfully")
                return status

            if current_status in ["failed", "error", "failure"]:
                error_msg = status.get("error", "Unknown error")
                raise CodeGenError(f"Agent run failed: {error_msg}")

            # Wait before next poll
            await asyncio.sleep(self.poll_interval)

    async def resume_agent_run(
        self,
        agent_run_id: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Resume an existing agent run with additional instructions.

        Args:
            agent_run_id: ID of the agent run to resume
            prompt: Additional instructions

        Returns:
            Updated status

        Raises:
            CodeGenError: If resume fails
        """
        # Ensure org_id is available
        await self._ensure_org_id()

        logger.info(f"Resuming agent run {agent_run_id}...")

        endpoint = f"{self.BASE_URL}/organizations/{self.org_id}/agent/run/{agent_run_id}/resume"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint,
                    headers=self.headers,
                    json={"prompt": prompt}
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error resuming agent: {e}")
            raise CodeGenError(f"Failed to resume agent: {e.response.text}")
        except Exception as e:
            logger.error(f"Error resuming agent: {e}")
            raise CodeGenError(f"Failed to resume agent: {e}")

    async def list_repositories(self) -> List[Dict[str, Any]]:
        """
        List all repositories accessible to the organization.

        Returns:
            List of repository dictionaries with id, name, url, etc.

        Raises:
            CodeGenError: If listing fails
        """
        # Ensure org_id is available
        await self._ensure_org_id()

        # Correct endpoint is /repos (not /repositories)
        endpoint = f"{self.BASE_URL}/organizations/{self.org_id}/repos"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, headers=self.headers)
                response.raise_for_status()
                data = response.json()

                # API returns paginated response with 'items' key
                if isinstance(data, dict) and "items" in data:
                    return data["items"]
                elif isinstance(data, list):
                    return data
                else:
                    logger.warning(f"Unexpected response format: {data}")
                    return []

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error listing repositories: {e}")
            raise CodeGenError(f"Failed to list repositories: {e.response.text}")
        except Exception as e:
            logger.error(f"Error listing repositories: {e}")
            raise CodeGenError(f"Failed to list repositories: {e}")

    async def get_repository(self, repo_id: int) -> Dict[str, Any]:
        """
        Get repository details by ID.

        Args:
            repo_id: Repository ID

        Returns:
            Repository dictionary with id, name, url, etc.

        Raises:
            CodeGenError: If retrieval fails
        """
        # Ensure org_id is available
        await self._ensure_org_id()

        endpoint = f"{self.BASE_URL}/organizations/{self.org_id}/repositories/{repo_id}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, headers=self.headers)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting repository: {e}")
            raise CodeGenError(f"Failed to get repository: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting repository: {e}")
            raise CodeGenError(f"Failed to get repository: {e}")

    async def find_repository_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find repository by name (case-insensitive partial match).

        Searches both 'full_name' (e.g., 'internexio/SEMalytics-forge')
        and 'name' (e.g., 'SEMalytics-forge') fields.

        Args:
            name: Repository name, full name, or partial match

        Returns:
            Repository dict if found, None otherwise

        Raises:
            CodeGenError: If listing fails
        """
        repos = await self.list_repositories()
        name_lower = name.lower()

        # Priority 1: Exact match on full_name (e.g., "internexio/SEMalytics-forge")
        for repo in repos:
            if repo.get("full_name", "").lower() == name_lower:
                return repo

        # Priority 2: Exact match on name (e.g., "SEMalytics-forge")
        for repo in repos:
            if repo.get("name", "").lower() == name_lower:
                return repo

        # Priority 3: Partial match on full_name
        for repo in repos:
            if name_lower in repo.get("full_name", "").lower():
                return repo

        # Priority 4: Partial match on name
        for repo in repos:
            if name_lower in repo.get("name", "").lower():
                return repo

        return None

    async def get_agent_run_logs(
        self,
        agent_run_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve execution logs for an agent run.

        Args:
            agent_run_id: ID of the agent run
            skip: Number of logs to skip (pagination)
            limit: Maximum logs to retrieve (max 100)

        Returns:
            List of log entries with timestamps, messages, tool executions, etc.

        Raises:
            CodeGenError: If log retrieval fails
        """
        # Ensure org_id is available
        await self._ensure_org_id()

        endpoint = f"{self.BASE_URL}/organizations/{self.org_id}/agent/run/{agent_run_id}/logs"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    endpoint,
                    headers=self.headers,
                    params={"skip": skip, "limit": min(limit, 100)}
                )
                response.raise_for_status()
                data = response.json()

                # API may return list or dict with 'items'
                if isinstance(data, dict) and "items" in data:
                    return data["items"]
                elif isinstance(data, list):
                    return data
                else:
                    return []

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting agent logs: {e}")
            raise CodeGenError(f"Failed to get agent logs: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting agent logs: {e}")
            raise CodeGenError(f"Failed to get agent logs: {e}")

    async def generate_setup_commands(
        self,
        repo_id: int,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate setup commands for a repository.

        This creates initialization scripts that run when the repository's
        sandbox environment is configured. Setup commands are required for
        repositories to change from NOT_SETUP status.

        Args:
            repo_id: Repository ID
            prompt: Optional custom instructions for setup generation

        Returns:
            Response containing agent_run_id, status, and url

        Raises:
            CodeGenError: If generation fails
        """
        # Ensure org_id is available
        await self._ensure_org_id()

        logger.info(f"Generating setup commands for repository {repo_id}...")

        endpoint = f"{self.BASE_URL}/organizations/{self.org_id}/setup-commands/generate"

        payload = {
            "repo_id": repo_id,
            "trigger_source": "setup-commands"
        }

        if prompt:
            payload["prompt"] = prompt

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    endpoint,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                agent_run_id = result.get("agent_run_id")
                logger.info(f"Setup command generation started: agent_run_id={agent_run_id}")

                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error generating setup commands: {e}")
            raise CodeGenError(f"Failed to generate setup commands: {e.response.text}")
        except Exception as e:
            logger.error(f"Error generating setup commands: {e}")
            raise CodeGenError(f"Failed to generate setup commands: {e}")

    async def generate_code(
        self,
        prompt: str,
        repository_id: Optional[int] = None,
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        High-level method to generate code and wait for results.

        Args:
            prompt: Code generation task description
            repository_id: Repository ID (integer) - CRITICAL for targeting correct repo
            on_progress: Optional progress callback

        Returns:
            Generation results

        Raises:
            CodeGenError: If generation fails
        """
        # Create agent run
        agent_run_id = await self.create_agent_run(
            prompt=prompt,
            repository_id=repository_id
        )

        # Wait for completion
        result = await self.wait_for_completion(
            agent_run_id=agent_run_id,
            on_progress=on_progress
        )

        return result
