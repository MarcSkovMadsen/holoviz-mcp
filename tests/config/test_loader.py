"""Tests for configuration loader."""

import os
from pathlib import Path

import pytest
import yaml

from holoviz_mcp.config.loader import ConfigLoader
from holoviz_mcp.config.loader import ConfigurationError
from holoviz_mcp.config.models import HoloVizMCPConfig


class TestConfigLoader:
    """Test ConfigLoader class."""

    def test_default_config_loading(self, config_loader: ConfigLoader):
        """Test loading default configuration."""
        config = config_loader.load_config()
        assert isinstance(config, HoloVizMCPConfig)
        assert config.server.name == "holoviz-mcp"
        assert config.server.log_level == "INFO"
        # Default repos are now empty unless provided by YAML
        assert isinstance(config.docs.repositories, dict)

    def test_user_config_override(self, config_loader: ConfigLoader, user_config_file: Path):
        """Test user configuration overrides."""
        # Patch user config file to include base_url for test-repo
        import yaml

        with open(user_config_file, "r") as f:
            user_config = yaml.safe_load(f)
        if "docs" in user_config and "repositories" in user_config["docs"]:
            for repo in user_config["docs"]["repositories"].values():
                if "base_url" not in repo:
                    repo["base_url"] = "https://example.com/"
        with open(user_config_file, "w") as f:
            yaml.safe_dump(user_config, f)
        config = config_loader.load_config()
        assert config.server.name == "test-server"
        assert config.server.log_level == "DEBUG"
        assert "test-repo" in config.docs.repositories
        assert config.docs.max_file_size == 512 * 1024
        assert config.resources.search_paths == [Path("/custom/resources")]

    def test_default_and_user_config_merge(self, config_loader: ConfigLoader, default_config_file: Path, user_config_file: Path):
        """Test merging default and user configurations."""
        import yaml

        for config_file in [default_config_file, user_config_file]:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
            if "docs" in config and "repositories" in config["docs"]:
                for repo in config["docs"]["repositories"].values():
                    if "base_url" not in repo:
                        repo["base_url"] = "https://example.com/"
            with open(config_file, "w") as f:
                yaml.safe_dump(config, f)
        config = config_loader.load_config()
        assert config.server.name == "test-server"
        assert config.server.log_level == "DEBUG"
        assert "default-repo" in config.docs.repositories
        assert "test-repo" in config.docs.repositories
        # No longer expect default repos like 'panel' unless present in YAML

    def test_environment_variable_overrides(self, config_loader: ConfigLoader, clean_environment):
        """Test environment variable overrides."""
        os.environ["HOLOVIZ_MCP_LOG_LEVEL"] = "ERROR"
        os.environ["HOLOVIZ_MCP_SERVER_NAME"] = "env-server"

        config = config_loader.load_config()

        assert config.server.log_level == "ERROR"
        assert config.server.name == "env-server"

    def test_invalid_yaml_file(self, config_loader: ConfigLoader, test_config: HoloVizMCPConfig):
        """Test handling of invalid YAML file."""
        config_file = test_config.config_file_path()
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Write invalid YAML
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(ConfigurationError, match="Invalid YAML"):
            config_loader.load_config()

    def test_non_dict_yaml_file(self, config_loader: ConfigLoader, test_config: HoloVizMCPConfig):
        """Test handling of non-dictionary YAML file."""
        config_file = test_config.config_file_path()
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Write non-dictionary YAML
        with open(config_file, "w") as f:
            f.write("- item1\n- item2\n")

        with pytest.raises(ConfigurationError, match="must contain a YAML dictionary"):
            config_loader.load_config()

    def test_invalid_configuration_validation(self, config_loader: ConfigLoader, test_config: HoloVizMCPConfig):
        """Test validation of invalid configuration."""
        config_file = test_config.config_file_path()
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Write configuration with invalid values
        invalid_config = {"server": {"log_level": "INVALID_LEVEL"}}

        with open(config_file, "w") as f:
            yaml.dump(invalid_config, f)

        with pytest.raises(ConfigurationError, match="Invalid configuration"):
            config_loader.load_config()

    def test_config_caching(self, config_loader: ConfigLoader):
        """Test configuration caching."""
        config1 = config_loader.load_config()
        config2 = config_loader.load_config()

        # Should return the same instance
        assert config1 is config2

    def test_config_reload(self, config_loader: ConfigLoader, test_config: HoloVizMCPConfig):
        """Test configuration reloading."""
        # Load initial config
        config1 = config_loader.load_config()
        assert config1.server.name == "holoviz-mcp"

        # Create user config
        config_file = test_config.config_file_path()
        config_file.parent.mkdir(parents=True, exist_ok=True)

        user_config = {"server": {"name": "reloaded-server"}}

        with open(config_file, "w") as f:
            yaml.dump(user_config, f)

        # Reload config
        config2 = config_loader.reload_config()

        assert config2.server.name == "reloaded-server"
        assert config1 is not config2

    def test_directory_paths(self, config_loader: ConfigLoader, test_config: HoloVizMCPConfig):
        """Test directory path methods."""
        assert config_loader.get_repos_dir() == test_config.repos_dir
        assert config_loader.get_resources_dir() == test_config.resources_dir()
        assert config_loader.get_agents_dir() == test_config.agents_dir()
        assert config_loader.get_skills_dir() == test_config.skills_dir()

    def test_create_user_config_template(self, config_loader: ConfigLoader, test_config: HoloVizMCPConfig):
        """Test creating user configuration template (now default user config)."""
        config_file = test_config.config_file_path()

        # File should not exist initially
        assert not config_file.exists()

        # Create template
        config_loader.create_default_user_config()

        # File should now exist
        assert config_file.exists()

        # Should contain valid YAML
        with open(config_file, "r") as f:
            content = yaml.safe_load(f)

        assert "server" in content
        assert "docs" in content
        assert "resources" in content

    def test_create_user_config_template_no_overwrite(self, config_loader: ConfigLoader, test_config: HoloVizMCPConfig):
        """Test that default user config creation doesn't overwrite existing file."""
        config_file = test_config.config_file_path()
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Create existing config
        original_content = {"existing": "content"}
        with open(config_file, "w") as f:
            yaml.dump(original_content, f)

        # Try to create template
        config_loader.create_default_user_config()

        # Original content should be preserved
        with open(config_file, "r") as f:
            content = yaml.safe_load(f)

        assert content == original_content

    @pytest.mark.skip(reason="No longer have Python-side default repos; only YAML-driven.")
    def test_default_repos_configuration(self, config_loader: ConfigLoader):
        pass

    def test_config_merge_deep(self, config_loader: ConfigLoader):
        """Test deep merging of configuration dictionaries."""
        base = {
            "server": {"name": "base-server", "version": "1.0.0"},
            "docs": {"repositories": {"repo1": {"url": "https://repo1.com", "base_url": "https://repo1.com/"}}},
        }

        override = {"server": {"name": "override-server"}, "docs": {"repositories": {"repo2": {"url": "https://repo2.com", "base_url": "https://repo2.com/"}}}}

        merged = config_loader._merge_configs(base, override)

        # Server name should be overridden
        assert merged["server"]["name"] == "override-server"
        # Server version should be preserved
        assert merged["server"]["version"] == "1.0.0"
        # Both repositories should be present
        assert "repo1" in merged["docs"]["repositories"]
        assert "repo2" in merged["docs"]["repositories"]


class TestConfigLoaderGlobalFunctions:
    """Test global configuration functions."""

    def test_get_config_loader_singleton(self):
        """Test that get_config_loader returns singleton."""
        from holoviz_mcp.config.loader import get_config_loader

        loader1 = get_config_loader()
        loader2 = get_config_loader()

        assert loader1 is loader2

    def test_get_config_function(self):
        """Test get_config function."""
        from holoviz_mcp.config.loader import get_config

        config = get_config()
        assert isinstance(config, HoloVizMCPConfig)

    def test_reload_config_function(self):
        """Test reload_config function."""
        from holoviz_mcp.config.loader import reload_config

        config = reload_config()
        assert isinstance(config, HoloVizMCPConfig)
