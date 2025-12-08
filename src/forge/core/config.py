"""
Layered configuration system supporting:
- Global config: ~/.forge/config.yaml
- Project config: ./forge.yaml
- Environment variables
- Validation with Pydantic
"""

from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import os
import re
from pydantic import BaseModel, Field
from forge.utils.errors import ConfigurationError


class GeneratorConfig(BaseModel):
    """Code generator configuration"""
    backend: str = "codegen_api"  # or "claude_code"
    api_key: Optional[str] = None
    org_id: Optional[str] = None
    timeout: int = 300
    base_url: Optional[str] = None


class GitConfig(BaseModel):
    """Git configuration"""
    author_name: str = "Forge AI"
    author_email: str = "forge@ai.dev"
    commit_format: str = "conventional"


class KnowledgeForgeConfig(BaseModel):
    """KnowledgeForge pattern configuration"""
    patterns_dir: str = "patterns"
    embedding_model: str = "all-MiniLM-L6-v2"
    cache_size: int = 128
    search_method: str = "hybrid"  # keyword, semantic, or hybrid


class TestingConfig(BaseModel):
    """Testing configuration"""
    use_docker: bool = True
    timeout: int = 600
    min_coverage: float = 80.0


class ForgeConfig(BaseModel):
    """Complete Forge configuration"""
    generator: GeneratorConfig = Field(default_factory=GeneratorConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    knowledgeforge: KnowledgeForgeConfig = Field(default_factory=KnowledgeForgeConfig)
    testing: TestingConfig = Field(default_factory=TestingConfig)

    # Database paths
    pattern_store_path: str = ".forge/patterns.db"
    state_db_path: str = ".forge/state.db"

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = ".forge/forge.log"

    @classmethod
    def load(cls, project_dir: Optional[Path] = None) -> "ForgeConfig":
        """
        Load config with layering: global < project < env vars

        Args:
            project_dir: Project directory (defaults to current directory)

        Returns:
            Loaded configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        config_data = {}

        # Load global config
        global_config = Path.home() / ".forge" / "config.yaml"
        if global_config.exists():
            try:
                with open(global_config) as f:
                    global_data = yaml.safe_load(f) or {}
                    config_data.update(global_data)
            except Exception as e:
                raise ConfigurationError(f"Failed to load global config: {e}")

        # Load project config (overrides global)
        if project_dir is None:
            project_dir = Path.cwd()

        project_config = project_dir / "forge.yaml"
        if project_config.exists():
            try:
                with open(project_config) as f:
                    project_data = yaml.safe_load(f) or {}
                    config_data.update(project_data)
            except Exception as e:
                raise ConfigurationError(f"Failed to load project config: {e}")

        # Apply environment variables (highest priority)
        config_data = cls._apply_env_vars(config_data)

        try:
            return cls(**config_data)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}")

    @staticmethod
    def _apply_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace ${VAR} with environment variable values

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with environment variables substituted
        """
        def replace_env_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.lastindex >= 2 else ""
            return os.getenv(var_name, default_value if default_value else match.group(0))

        config_str = yaml.dump(config)
        # Support ${VAR} and ${VAR:default}
        config_str = re.sub(r'\$\{(\w+)(?::([^}]*))?\}', replace_env_var, config_str)
        return yaml.safe_load(config_str)

    def save(self, path: Optional[Path] = None):
        """
        Save configuration to file

        Args:
            path: Path to save to (defaults to ./forge.yaml)
        """
        if path is None:
            path = Path.cwd() / "forge.yaml"

        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dictionary and save
        with open(path, 'w') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)

    @classmethod
    def create_default(cls, path: Optional[Path] = None) -> "ForgeConfig":
        """
        Create default configuration file

        Args:
            path: Path to save to (defaults to ./forge.yaml)

        Returns:
            Default configuration instance
        """
        config = cls()
        config.save(path)
        return config
