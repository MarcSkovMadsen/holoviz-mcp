"""Tests for configuration models."""

from pathlib import Path

import pytest
from pydantic import AnyHttpUrl
from pydantic import ValidationError
from pydantic import parse_obj_as

from holoviz_mcp.config.models import DocsConfig
from holoviz_mcp.config.models import FolderConfig
from holoviz_mcp.config.models import GitRepository
from holoviz_mcp.config.models import HoloVizMCPConfig
from holoviz_mcp.config.models import PromptConfig
from holoviz_mcp.config.models import ResourceConfig
from holoviz_mcp.config.models import ServerConfig


class TestGitRepository:
    """Test GitRepository model."""

    def test_valid_repository(self):
        """Test valid repository configuration."""
        repo = GitRepository(url=parse_obj_as(AnyHttpUrl, "https://github.com/test/repo.git"), base_url=parse_obj_as(AnyHttpUrl, "https://example.com/"))
        assert str(repo.url) == "https://github.com/test/repo.git"
        assert repo.branch is None
        assert repo.tag is None
        assert repo.commit is None
        assert repo.folders == {"doc": FolderConfig()}  # Default value converted to dict
        assert str(repo.base_url) == "https://example.com/"

    def test_repository_with_all_fields(self):
        """Test repository with all fields."""
        repo = GitRepository(
            url=parse_obj_as(AnyHttpUrl, "https://github.com/test/repo.git"),
            base_url=parse_obj_as(AnyHttpUrl, "https://test.example.com/"),
            branch="main",
            tag="v1.0.0",
            commit="abc123",
            folders=["doc", "examples"],
            reference_patterns=["examples/**/*.md"],
        )
        assert str(repo.url) == "https://github.com/test/repo.git"
        assert repo.branch == "main"
        assert repo.tag == "v1.0.0"
        assert repo.commit == "abc123"
        assert repo.folders == {"doc": FolderConfig(), "examples": FolderConfig()}
        assert str(repo.base_url) == "https://test.example.com/"

    def test_invalid_url(self):
        """Test invalid URL validation."""
        with pytest.raises(ValidationError, match="Input should be a valid URL"):
            GitRepository(url="invalid-url", base_url=parse_obj_as(AnyHttpUrl, "https://example.com/"))  # type: ignore

    def test_valid_url_schemes(self):
        """Test various valid URL schemes."""
        valid_urls = [
            "https://github.com/test/repo.git",
            "http://github.com/test/repo.git",
        ]

        for url in valid_urls:
            repo = GitRepository(url=url, base_url=parse_obj_as(AnyHttpUrl, "https://example.com/"))  # type: ignore
            assert str(repo.url) == url


class TestDocsConfig:
    """Test DocsConfig model."""

    def test_default_holoviz_config(self):
        """Test default docs configuration."""
        config = DocsConfig()
        assert config.repositories == {}
        assert config.index_patterns == ["**/*.md", "**/*.rst", "**/*.txt"]
        assert config.exclude_patterns == ["**/node_modules/**", "**/.git/**", "**/build/**"]
        assert config.max_file_size == 1024 * 1024
        assert config.update_interval == 86400

    def test_holoviz_config_with_repositories(self):
        """Test docs configuration with repositories."""
        config = DocsConfig(
            repositories={
                "test-repo": GitRepository(url="https://github.com/test/repo.git", base_url="https://example.com/", url_transform="plotly")  # type: ignore
            }
        )
        assert "test-repo" in config.repositories
        assert str(config.repositories["test-repo"].url) == "https://github.com/test/repo.git"
        assert str(config.repositories["test-repo"].url_transform) == "plotly"


class TestResourceConfig:
    """Test ResourceConfig model."""

    def test_default_resource_config(self):
        """Test default resource configuration."""
        config = ResourceConfig()
        assert config.search_paths == []

    def test_resource_config_with_values(self):
        """Test resource configuration with values."""
        config = ResourceConfig(search_paths=[Path("/custom/resources")])
        assert config.search_paths == [Path("/custom/resources")]


class TestPromptConfig:
    """Test PromptConfig model."""

    def test_default_prompt_config(self):
        """Test default prompt configuration."""
        config = PromptConfig()
        assert config.search_paths == []

    def test_prompt_config_with_values(self):
        """Test prompt configuration with values."""
        config = PromptConfig(search_paths=[Path("/custom/prompts")])
        assert config.search_paths == [Path("/custom/prompts")]


class TestServerConfig:
    """Test ServerConfig model."""

    def test_default_server_config(self):
        """Test default server configuration."""
        config = ServerConfig()
        assert config.name == "holoviz-mcp"
        assert config.version == "1.0.0"
        assert config.description == "Model Context Protocol server for HoloViz ecosystem"
        assert config.log_level == "INFO"

    def test_server_config_with_values(self):
        """Test server configuration with custom values."""
        config = ServerConfig(name="custom-server", version="2.0.0", description="Custom server", log_level="DEBUG")
        assert config.name == "custom-server"
        assert config.version == "2.0.0"
        assert config.description == "Custom server"
        assert config.log_level == "DEBUG"

    def test_invalid_log_level(self):
        """Test invalid log level validation."""
        with pytest.raises(ValidationError, match="Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'"):
            ServerConfig(log_level="INVALID")  # type: ignore

    def test_log_level_case_sensitive(self):
        """Test log level case sensitivity."""
        # Lowercase should fail
        with pytest.raises(ValidationError, match="Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'"):
            ServerConfig(log_level="debug")  # type: ignore

        # Uppercase should work
        config = ServerConfig(log_level="DEBUG")
        assert config.log_level == "DEBUG"


class TestHoloVizMCPConfig:
    """Test HoloVizMCPConfig model."""

    def test_default_config(self):
        """Test default configuration."""
        config = HoloVizMCPConfig()
        assert isinstance(config.server, ServerConfig)
        assert isinstance(config.docs, DocsConfig)
        assert isinstance(config.resources, ResourceConfig)
        assert isinstance(config.prompts, PromptConfig)

    def test_config_with_custom_values(self):
        """Test configuration with custom values."""
        config = HoloVizMCPConfig(
            server=ServerConfig(name="test-server"),
            docs=DocsConfig(max_file_size=512 * 1024),
            resources=ResourceConfig(search_paths=[Path("/custom")]),
            prompts=PromptConfig(search_paths=[Path("/prompts")]),
        )
        assert config.server.name == "test-server"
        assert config.docs.max_file_size == 512 * 1024
        assert config.resources.search_paths == [Path("/custom")]
        assert config.prompts.search_paths == [Path("/prompts")]

    def test_config_forbids_extra_fields(self):
        """Test that configuration forbids extra fields."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            # We need to construct this in a way that bypasses type checking
            config_dict = {"server": {"name": "test"}, "docs": {"repositories": {}}, "resources": {}, "prompts": {}, "extra_field": "not allowed"}
            HoloVizMCPConfig(**config_dict)

    def test_with_environment_variables(self, monkeypatch):
        """Test configuration with environment variables."""
        monkeypatch.setenv("HOLOVIZ_MCP_USER_DIR", "/test/dir")
        config = HoloVizMCPConfig()
        assert config.user_dir == Path("/test/dir")
        assert config.server.vector_db_path == Path("/test/dir") / "vector_db" / "chroma"
        assert config.repos_dir == Path("/test/dir") / "repos"
