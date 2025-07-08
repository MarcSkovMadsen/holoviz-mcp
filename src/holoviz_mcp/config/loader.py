"""Configuration loader for HoloViz MCP server."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any
from typing import Optional

import yaml
from pydantic import ValidationError

from .models import EnvironmentConfig
from .models import HoloVizMCPConfig

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration cannot be loaded or is invalid."""


class ConfigLoader:
    """Loads and manages HoloViz MCP configuration."""

    def __init__(self, env_config: Optional[EnvironmentConfig] = None):
        """Initialize configuration loader.

        Args:
            env_config: Environment configuration. If None, loads from environment.
        """
        self.env_config = env_config or EnvironmentConfig.from_environment()
        self._config: Optional[HoloVizMCPConfig] = None

    def load_config(self) -> HoloVizMCPConfig:
        """Load configuration from files and environment.

        Returns
        -------
            Loaded configuration.

        Raises
        ------
            ConfigurationError: If configuration cannot be loaded or is invalid.
        """
        if self._config is not None:
            return self._config

        # Start with default configuration
        config_dict = self._get_default_config()

        # Load from default config file if it exists
        default_config_file = self.env_config.default_dir / "config.yaml"
        if default_config_file.exists():
            try:
                default_config = self._load_yaml_file(default_config_file)
                config_dict = self._merge_configs(config_dict, default_config)
                logger.info(f"Loaded default configuration from {default_config_file}")
            except Exception as e:
                logger.warning(f"Failed to load default config from {default_config_file}: {e}")

        # Load from user config file if it exists
        user_config_file = self.env_config.config_file_path()
        if user_config_file.exists():
            user_config = self._load_yaml_file(user_config_file)
            config_dict = self._merge_configs(config_dict, user_config)
            logger.info(f"Loaded user configuration from {user_config_file}")

        # Apply environment variable overrides
        config_dict = self._apply_env_overrides(config_dict)

        # Validate and create configuration
        try:
            self._config = HoloVizMCPConfig(**config_dict)
        except ValidationError as e:
            raise ConfigurationError(f"Invalid configuration: {e}") from e

        return self._config

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration dictionary."""
        return {
            "server": {
                "name": "holoviz-mcp",
                "version": "1.0.0",
                "description": "Model Context Protocol server for HoloViz ecosystem",
                "log_level": "INFO",
                "security": {"allow_code_execution": False},
            },
            "docs": {
                "repositories": {},  # No more Python-side defaults!
                "index_patterns": ["**/*.md", "**/*.rst", "**/*.txt"],
                "exclude_patterns": ["**/node_modules/**", "**/.git/**", "**/build/**"],
                "max_file_size": 1024 * 1024,  # 1MB
                "update_interval": 86400,  # 24 hours
            },
            "resources": {"search_paths": []},
            "prompts": {"search_paths": []},
        }

    def _load_yaml_file(self, file_path: Path) -> dict[str, Any]:
        """Load YAML file safely.

        Args:
            file_path: Path to YAML file.

        Returns
        -------
            Parsed YAML content.

        Raises
        ------
            ConfigurationError: If file cannot be loaded or parsed.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                if content is None:
                    return {}
                if not isinstance(content, dict):
                    raise ConfigurationError(f"Configuration file must contain a YAML dictionary: {file_path}")
                return content
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {file_path}: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load {file_path}: {e}") from e

    def _merge_configs(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Merge two configuration dictionaries recursively.

        Args:
            base: Base configuration.
            override: Override configuration.

        Returns
        -------
            Merged configuration.
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _apply_env_overrides(self, config: dict[str, Any]) -> dict[str, Any]:
        """Apply environment variable overrides to configuration.

        Args:
            config: Configuration dictionary.

        Returns
        -------
            Configuration with environment overrides applied.
        """
        # Log level override
        if "HOLOVIZ_MCP_LOG_LEVEL" in os.environ:
            config.setdefault("server", {})["log_level"] = os.environ["HOLOVIZ_MCP_LOG_LEVEL"]

        # Server name override
        if "HOLOVIZ_MCP_SERVER_NAME" in os.environ:
            config.setdefault("server", {})["name"] = os.environ["HOLOVIZ_MCP_SERVER_NAME"]

        # Transport override
        if "HOLOVIZ_MCP_TRANSPORT" in os.environ:
            config.setdefault("server", {})["transport"] = os.environ["HOLOVIZ_MCP_TRANSPORT"]

        # Telemetry override
        if "ANONYMIZED_TELEMETRY" in os.environ:
            config.setdefault("server", {})["anonymized_telemetry"] = os.environ["ANONYMIZED_TELEMETRY"].lower() in ("true", "1", "yes", "on")

        # Jupyter proxy URL override
        if "JUPYTER_SERVER_PROXY_URL" in os.environ:
            config.setdefault("server", {})["jupyter_server_proxy_url"] = os.environ["JUPYTER_SERVER_PROXY_URL"]

        # Security configuration override
        if "HOLOVIZ_MCP_ALLOW_CODE_EXECUTION" in os.environ:
            config.setdefault("server", {}).setdefault("security", {})["allow_code_execution"] = os.environ["HOLOVIZ_MCP_ALLOW_CODE_EXECUTION"].lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

        return config

    def get_repos_dir(self) -> Path:
        """Get the repository download directory."""
        return self.env_config.repos_dir

    def get_resources_dir(self) -> Path:
        """Get the resources directory."""
        return self.env_config.resources_dir()

    def get_prompts_dir(self) -> Path:
        """Get the prompts directory."""
        return self.env_config.prompts_dir()

    def get_best_practices_dir(self) -> Path:
        """Get the best practices directory."""
        return self.env_config.best_practices_dir()

    def create_default_user_config(self) -> None:
        """Create a default user configuration file."""
        config_file = self.env_config.config_file_path()

        # Create directories if they don't exist
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Don't overwrite existing config
        if config_file.exists():
            logger.info(f"Configuration file already exists: {config_file}")
            return

        # Create default configuration
        template = {
            "server": {"name": "holoviz-mcp", "log_level": "INFO", "security": {"allow_code_execution": False}},
            "docs": {
                "repositories": {
                    "example-repo": {
                        "url": "https://github.com/example/repo.git",
                        "branch": "main",
                        "folders": {"doc": {"url_path": ""}},
                        "base_url": "https://example.readthedocs.io",
                        "reference_patterns": ["doc/reference/**/*.md", "examples/reference/**/*.ipynb"],
                    }
                }
            },
            "resources": {"search_paths": []},
            "prompts": {"search_paths": []},
        }

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(template, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created default user configuration file: {config_file}")

    def reload_config(self) -> HoloVizMCPConfig:
        """Reload configuration from files.

        Returns
        -------
            Reloaded configuration.
        """
        self._config = None
        return self.load_config()


# Global configuration loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def get_config() -> HoloVizMCPConfig:
    """Get the current configuration."""
    return get_config_loader().load_config()


def reload_config() -> HoloVizMCPConfig:
    """Reload configuration from files."""
    return get_config_loader().reload_config()
