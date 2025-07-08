"""Test fixtures for configuration tests."""

import os
import tempfile
from pathlib import Path
from typing import Any
from typing import Generator

import pytest
import yaml

from holoviz_mcp.config import ConfigLoader
from holoviz_mcp.config import EnvironmentConfig


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
def env_config(temp_config_dir: Path, temp_repos_dir: Path) -> EnvironmentConfig:
    """Create test environment configuration."""
    return EnvironmentConfig(user_dir=temp_config_dir / "user", default_dir=temp_config_dir / "default", repos_dir=temp_repos_dir)


@pytest.fixture
def config_loader(env_config: EnvironmentConfig) -> ConfigLoader:
    """Create test configuration loader."""
    return ConfigLoader(env_config)


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Sample configuration for testing."""
    return {
        "server": {"name": "test-server", "log_level": "DEBUG", "security": {"allow_code_execution": True}},
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

    # Create best practices directory
    best_practices_dir = resources_dir / "best-practices"
    best_practices_dir.mkdir()

    # Create sample best practices files
    (best_practices_dir / "panel.md").write_text("# Panel Best Practices\n\nUse Panel wisely.")
    (best_practices_dir / "panel-material-ui.md").write_text("# Panel Material UI Best Practices\n\nUse Material UI components.")

    return resources_dir


@pytest.fixture
def user_config_file(env_config: EnvironmentConfig, sample_config: dict[str, Any]) -> Path:
    """Create a user configuration file."""
    config_file = env_config.config_file_path()
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, "w") as f:
        yaml.dump(sample_config, f)

    return config_file


@pytest.fixture
def default_config_file(env_config: EnvironmentConfig) -> Path:
    """Create a default configuration file."""
    config_file = env_config.default_dir / "config.yaml"
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
        "HOLOVIZ_MCP_ALLOW_CODE_EXECUTION",
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
