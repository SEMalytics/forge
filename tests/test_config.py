"""
Tests for configuration system
"""

import pytest
from pathlib import Path
import yaml
from forge.core.config import ForgeConfig, GeneratorConfig, GitConfig


def test_default_config():
    """Test default configuration values"""
    config = ForgeConfig()

    assert config.generator.backend == "codegen_api"
    assert config.generator.timeout == 7200  # 2 hours for CodeGen agent runs
    assert config.git.author_name == "Forge AI"
    assert config.git.commit_format == "conventional"
    assert config.pattern_store_path == ".forge/patterns.db"
    assert config.state_db_path == ".forge/state.db"


def test_config_serialization():
    """Test configuration serialization"""
    config = ForgeConfig()

    # Convert to dict
    config_dict = config.model_dump()

    assert 'generator' in config_dict
    assert 'git' in config_dict
    assert config_dict['generator']['backend'] == "codegen_api"


def test_generator_config():
    """Test generator configuration"""
    gen_config = GeneratorConfig(
        backend="claude_code",
        api_key="test-key",
        timeout=600
    )

    assert gen_config.backend == "claude_code"
    assert gen_config.api_key == "test-key"
    assert gen_config.timeout == 600


def test_git_config():
    """Test git configuration"""
    git_config = GitConfig(
        author_name="Test User",
        author_email="test@example.com"
    )

    assert git_config.author_name == "Test User"
    assert git_config.author_email == "test@example.com"
    assert git_config.commit_format == "conventional"


def test_config_save_load(tmp_path):
    """Test configuration save and load"""
    config_path = tmp_path / "forge.yaml"

    # Create and save config
    config = ForgeConfig()
    config.generator.backend = "claude_code"
    config.save(config_path)

    assert config_path.exists()

    # Load config
    with open(config_path) as f:
        loaded_data = yaml.safe_load(f)

    assert loaded_data['generator']['backend'] == "claude_code"


def test_create_default_config(tmp_path):
    """Test creating default configuration file"""
    config_path = tmp_path / "forge.yaml"

    config = ForgeConfig.create_default(config_path)

    assert config_path.exists()
    assert isinstance(config, ForgeConfig)
