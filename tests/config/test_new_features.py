"""Tests for new configuration features."""

import os

import pytest
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as

from holoviz_mcp.config.loader import ConfigLoader
from holoviz_mcp.config.models import FolderConfig
from holoviz_mcp.config.models import GitRepository
from holoviz_mcp.config.models import SecurityConfig
from holoviz_mcp.config.models import ServerConfig


class TestGitRepositoryNew:
    """Test new GitRepository features."""

    def test_multiple_folders(self):
        """Test repository with multiple folders."""
        repo = GitRepository(
            url=parse_obj_as(AnyHttpUrl, "https://github.com/test/repo.git"),
            base_url=parse_obj_as(AnyHttpUrl, "https://example.com/"),
            folders=["doc", "examples/reference", "tutorials"],
        )
        assert repo.folders == {"doc": FolderConfig(), "examples/reference": FolderConfig(), "tutorials": FolderConfig()}

    def test_base_url(self):
        """Test repository with base URL."""
        repo = GitRepository(url=parse_obj_as(AnyHttpUrl, "https://github.com/test/repo.git"), base_url=parse_obj_as(AnyHttpUrl, "https://test.readthedocs.io"))
        assert str(repo.base_url) == "https://test.readthedocs.io/"

    def test_version_tag(self):
        """Test repository with version tag."""
        repo = GitRepository(
            url=parse_obj_as(AnyHttpUrl, "https://github.com/holoviz/panel.git"), base_url=parse_obj_as(AnyHttpUrl, "https://panel.holoviz.org/"), tag="1.7.2"
        )
        assert repo.tag == "1.7.2"

    def test_v_prefixed_tag(self):
        """Test repository with v-prefixed tag."""
        repo = GitRepository(
            url=parse_obj_as(AnyHttpUrl, "https://github.com/holoviz/panel.git"), base_url=parse_obj_as(AnyHttpUrl, "https://panel.holoviz.org/"), tag="v1.7.2"
        )
        assert repo.tag == "v1.7.2"

    def test_default_folders(self):
        """Test default folders configuration."""
        repo = GitRepository(url=parse_obj_as(AnyHttpUrl, "https://github.com/test/repo.git"), base_url=parse_obj_as(AnyHttpUrl, "https://example.com/"))
        assert repo.folders == {"doc": FolderConfig()}


class TestSecurityConfig:
    """Test SecurityConfig model."""

    def test_default_security_config(self):
        """Test default security configuration."""
        config = SecurityConfig()
        assert config.allow_code_execution is False

    def test_custom_security_config(self):
        """Test custom security configuration."""
        config = SecurityConfig(allow_code_execution=True)
        assert config.allow_code_execution is True


class TestServerConfigWithSecurity:
    """Test ServerConfig with security configuration."""

    def test_server_with_security(self):
        """Test server configuration with security settings."""
        security = SecurityConfig(allow_code_execution=True)
        config = ServerConfig(security=security)

        assert config.security.allow_code_execution is True

    def test_default_server_security(self):
        """Test default server security configuration."""
        config = ServerConfig()
        assert config.security.allow_code_execution is False


class TestEnvironmentVariableOverrides:
    """Test new environment variable overrides."""

    def test_code_execution_env_var(self, config_loader: ConfigLoader, clean_environment):
        """Test code execution environment variable override."""
        os.environ["HOLOVIZ_MCP_ALLOW_CODE_EXECUTION"] = "true"

        config = config_loader.load_config()
        assert config.server.security.allow_code_execution is True

    def test_code_execution_env_var_false(self, config_loader: ConfigLoader, clean_environment):
        """Test code execution environment variable set to false."""
        os.environ["HOLOVIZ_MCP_ALLOW_CODE_EXECUTION"] = "false"

        config = config_loader.load_config()
        assert config.server.security.allow_code_execution is False

    def test_code_execution_env_var_various_values(self, config_loader: ConfigLoader, clean_environment):
        """Test various values for code execution environment variable."""
        true_values = ["true", "1", "yes", "on", "TRUE", "Yes", "ON"]
        false_values = ["false", "0", "no", "off", "FALSE", "No", "OFF"]

        for value in true_values:
            os.environ["HOLOVIZ_MCP_ALLOW_CODE_EXECUTION"] = value
            # Clear cached config
            config_loader.clear_cache()
            config = config_loader.load_config()
            assert config.server.security.allow_code_execution is True, f"Failed for value: {value}"

        for value in false_values:
            os.environ["HOLOVIZ_MCP_ALLOW_CODE_EXECUTION"] = value
            # Clear cached config
            config_loader.clear_cache()
            config = config_loader.load_config()
            assert config.server.security.allow_code_execution is False, f"Failed for value: {value}"


class TestRepositoryConfiguration:
    """Test repository configuration with new features."""

    @pytest.mark.skip(reason="No longer have Python-side default repos; only YAML-driven.")
    def test_default_repos_have_folders(self, config_loader: ConfigLoader):
        pass

    @pytest.mark.skip(reason="No longer have Python-side default repos; only YAML-driven.")
    def test_default_repos_have_base_urls(self, config_loader: ConfigLoader):
        pass


class TestConfigurationValidation:
    """Test configuration validation with new features."""

    def test_empty_folders_list(self):
        """Test repository with empty folders list."""
        repo = GitRepository(url=parse_obj_as(AnyHttpUrl, "https://github.com/test/repo.git"), base_url=parse_obj_as(AnyHttpUrl, "https://example.com/"), folders=[])
        assert repo.folders == {}
