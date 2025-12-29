"""Test fixtures for configuration tests."""

import os
import tempfile
from pathlib import Path
from typing import Any
from typing import Generator

import pytest
import yaml

from holoviz_mcp.config import ConfigLoader
from holoviz_mcp.config import HoloVizMCPConfig


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary configuration directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_repos_dir() -> Generator[Path, None, None]:
    """Create a temporary repositories directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_config(temp_config_dir: Path, temp_repos_dir: Path) -> HoloVizMCPConfig:
    """Create test configuration with temporary directories."""
    return HoloVizMCPConfig(user_dir=temp_config_dir / "user", default_dir=temp_config_dir / "default", repos_dir=temp_repos_dir)


@pytest.fixture
def env_config(test_config: HoloVizMCPConfig):
    """Create test environment configuration for backward compatibility."""
    # Return test_config directly since HoloVizMCPConfig now has all the same methods
    return test_config


@pytest.fixture
def config_loader(test_config: HoloVizMCPConfig) -> ConfigLoader:
    """Create test configuration loader."""
    return ConfigLoader(test_config)


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Sample configuration for testing."""
    return {
        "server": {
            "name": "test-server",
            "log_level": "DEBUG",
        },
        "docs": {
            "repositories": {"test-repo": {"url": "https://github.com/test/repo.git", "branch": "main", "folders": ["docs", "examples"]}},
            "max_file_size": 512 * 1024,
        },
        "resources": {"search_paths": ["/custom/resources"]},
    }


@pytest.fixture
def sample_repo_structure(temp_repos_dir: Path) -> Path:
    """Create a sample repository structure for testing."""
    repo_dir = temp_repos_dir / "test-repo"
    repo_dir.mkdir(parents=True)

    # Create some sample documentation files
    docs_dir = repo_dir / "docs"
    docs_dir.mkdir()

    (docs_dir / "README.md").write_text("# Test Documentation\n\nThis is a test.")
    (docs_dir / "guide.md").write_text("# User Guide\n\nHow to use this.")

    # Create a subdirectory
    api_dir = docs_dir / "api"
    api_dir.mkdir()
    (api_dir / "reference.md").write_text("# API Reference\n\nAPI documentation.")

    return repo_dir


@pytest.fixture
def sample_resources_dir(temp_config_dir: Path) -> Path:
    """Create a sample resources directory structure."""
    resources_dir = temp_config_dir / "user" / "resources"
    resources_dir.mkdir(parents=True)

    # Create skill directory
    skills_dir = resources_dir / "skills"
    skills_dir.mkdir()

    # Create sample skill files
    (skills_dir / "panel.md").write_text("# Panel skill\n\nUse Panel wisely.")
    (skills_dir / "panel-material-ui.md").write_text("# Panel Material UI skill\n\nUse Material UI components.")

    return resources_dir


@pytest.fixture
def user_config_file(test_config: HoloVizMCPConfig, sample_config: dict[str, Any]) -> Path:
    """Create a user configuration file."""
    config_file = test_config.config_file_path()
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, "w") as f:
        yaml.dump(sample_config, f)

    return config_file


@pytest.fixture
def default_config_file(test_config: HoloVizMCPConfig) -> Path:
    """Create a default configuration file."""
    config_file = test_config.default_dir / "config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    default_config = {
        "server": {"name": "default-server", "version": "1.0.0"},
        "docs": {"repositories": {"default-repo": {"url": "https://github.com/default/repo.git"}}},
    }

    with open(config_file, "w") as f:
        yaml.dump(default_config, f)

    return config_file


@pytest.fixture
def clean_environment():
    """Clean environment variables before and after test."""
    env_vars = [
        "HOLOVIZ_MCP_USER_DIR",
        "HOLOVIZ_MCP_DEFAULT_DIR",
        "HOLOVIZ_MCP_REPOS_DIR",
        "HOLOVIZ_MCP_LOG_LEVEL",
        "HOLOVIZ_MCP_SERVER_NAME",
    ]

    # Save original values
    original_values = {}
    for var in env_vars:
        original_values[var] = os.environ.get(var)

    # Clear environment variables
    for var in env_vars:
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]
