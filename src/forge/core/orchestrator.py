"""
Main orchestration coordinator for Forge
"""

from typing import Optional, Dict, Any
from pathlib import Path
from forge.core.config import ForgeConfig
from forge.core.state_manager import StateManager, ProjectState
from forge.knowledgeforge.pattern_store import PatternStore
from forge.knowledgeforge.search_engine import SearchEngine
from forge.utils.logger import logger


class Orchestrator:
    """Main coordinator for Forge development orchestration"""

    def __init__(self, config: Optional[ForgeConfig] = None):
        """
        Initialize orchestrator

        Args:
            config: Forge configuration (loads default if not provided)
        """
        self.config = config or ForgeConfig.load()

        # Initialize components
        logger.info("Initializing Forge orchestrator...")

        self.state_manager = StateManager(self.config.state_db_path)
        self.pattern_store = PatternStore(
            self.config.pattern_store_path,
            self.config.knowledgeforge.patterns_dir
        )
        self.search_engine = SearchEngine(
            self.pattern_store,
            cache_size=self.config.knowledgeforge.cache_size,
            default_method=self.config.knowledgeforge.search_method
        )

        logger.info("Orchestrator initialized")

    def create_project(
        self,
        name: str,
        description: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectState:
        """
        Create a new project

        Args:
            name: Project name
            description: Project description
            project_id: Optional project ID (generated if not provided)
            metadata: Optional metadata

        Returns:
            Created project state
        """
        # Generate project ID if not provided
        if not project_id:
            import re
            from datetime import datetime
            slug = re.sub(r'[^\w\s-]', '', name.lower())
            slug = re.sub(r'[-\s]+', '-', slug)
            timestamp = datetime.now().strftime("%Y%m%d")
            project_id = f"{slug}-{timestamp}"

        logger.info(f"Creating project: {name} ({project_id})")

        # Create project in state manager
        project = self.state_manager.create_project(
            project_id=project_id,
            name=name,
            description=description,
            metadata=metadata or {}
        )

        # Create initial checkpoint
        self.state_manager.checkpoint(
            project_id=project_id,
            stage='planning',
            state={'project': project.__dict__},
            description="Project created"
        )

        return project

    def get_project(self, project_id: str) -> Optional[ProjectState]:
        """
        Get project by ID

        Args:
            project_id: Project identifier

        Returns:
            Project state or None
        """
        return self.state_manager.get_project(project_id)

    def search_patterns(
        self,
        query: str,
        max_results: int = 10,
        method: Optional[str] = None
    ):
        """
        Search KnowledgeForge patterns

        Args:
            query: Search query
            max_results: Maximum results to return
            method: Search method (keyword, semantic, hybrid)

        Returns:
            List of matching patterns
        """
        return self.search_engine.search(query, max_results, method)

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status and statistics

        Returns:
            Dictionary with system status
        """
        pattern_count = self.pattern_store.get_pattern_count()
        cache_stats = self.search_engine.get_cache_stats()

        return {
            'pattern_count': pattern_count,
            'cache_stats': cache_stats,
            'config': {
                'backend': self.config.generator.backend,
                'search_method': self.config.knowledgeforge.search_method
            }
        }

    def close(self):
        """Cleanup resources"""
        self.state_manager.close()
        self.pattern_store.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
