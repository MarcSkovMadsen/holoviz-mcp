"""Configuration models for HoloViz MCP server."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal
from typing import Optional
from typing import Union

from pydantic import AnyHttpUrl
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import PositiveInt
from pydantic import field_validator


def _holoviz_mcp_user_dir() -> Path:
    """Get the default user directory for HoloViz MCP."""
    return Path(os.environ.get("HOLOVIZ_MCP_USER_DIR", Path.home() / ".holoviz-mcp"))


def _holoviz_mcp_default_dir() -> Path:
    """Get the default configuration directory for HoloViz MCP."""
    return Path(os.environ.get("HOLOVIZ_MCP_DEFAULT_DIR", Path(__file__).parent.parent / "config"))


class FolderConfig(BaseModel):
    """Configuration for a folder within a repository."""

    url_path: str = Field(default="", description="URL path mapping for this folder (e.g., '' for root, '/reference' for reference docs)")


class GitRepository(BaseModel):
    """Configuration for a Git repository."""

    url: AnyHttpUrl = Field(..., description="Git repository URL")
    branch: Optional[str] = Field(default=None, description="Git branch to use")
    tag: Optional[str] = Field(default=None, description="Git tag to use (e.g., '1.7.2')")
    commit: Optional[str] = Field(default=None, description="Git commit hash to use")
    folders: Union[list[str], dict[str, FolderConfig]] = Field(
        default_factory=lambda: {"doc": FolderConfig()},
        description="Folders to index within the repository. Can be a list of folder names or a dict mapping folder names to FolderConfig objects",
    )
    base_url: AnyHttpUrl = Field(..., description="Base URL for documentation links")
    url_transform: Literal["holoviz", "plotly", "datashader"] = Field(
        default="holoviz",
        description="""How to transform file path into URL:

        - holoViz transform suffix to .html: filename.md -> filename.html
        - plotly transform suffix to /: filename.md -> filename/
        - datashader removes leading index and transform suffix to .html: 01_filename.md -> filename.html
        """,
    )
    reference_patterns: list[str] = Field(
        default_factory=lambda: ["examples/reference/**/*.md", "examples/reference/**/*.ipynb"], description="Glob patterns for reference documentation files"
    )

    @field_validator("tag")
    @classmethod
    def validate_tag(cls, v):
        """Validate git tag format, allowing both 'v1.2.3' and '1.2.3' formats."""
        if v is not None and v.startswith("v"):
            # Allow tags like 'v1.7.2' but also suggest plain version numbers
            pass
        return v

    @field_validator("folders")
    @classmethod
    def validate_folders(cls, v):
        """Validate and normalize folders configuration."""
        if isinstance(v, list):
            # Convert list to dict format for backward compatibility
            return {folder: FolderConfig() for folder in v}
        elif isinstance(v, dict):
            # Ensure all values are FolderConfig objects
            result = {}
            for folder, config in v.items():
                if isinstance(config, dict):
                    result[folder] = FolderConfig(**config)
                elif isinstance(config, FolderConfig):
                    result[folder] = config
                else:
                    raise ValueError(f"Invalid folder config for '{folder}': must be dict or FolderConfig")
            return result
        else:
            raise ValueError("folders must be a list or dict")

    def get_folder_names(self) -> list[str]:
        """Get list of folder names for backward compatibility."""
        if isinstance(self.folders, dict):
            return list(self.folders.keys())
        return self.folders

    def get_folder_url_path(self, folder_name: str) -> str:
        """Get URL path for a specific folder."""
        if isinstance(self.folders, dict):
            folder_config = self.folders.get(folder_name)
            if folder_config:
                return folder_config.url_path
        return ""


class DocsConfig(BaseModel):
    """Configuration for documentation repositories."""

    repositories: dict[str, GitRepository] = Field(default_factory=dict, description="Dictionary mapping package names to repository configurations")
    index_patterns: list[str] = Field(
        default_factory=lambda: ["**/*.md", "**/*.rst", "**/*.txt"], description="File patterns to include when indexing documentation"
    )
    exclude_patterns: list[str] = Field(
        default_factory=lambda: ["**/node_modules/**", "**/.git/**", "**/build/**"], description="File patterns to exclude when indexing documentation"
    )
    max_file_size: PositiveInt = Field(
        default=1024 * 1024,  # 1MB
        description="Maximum file size in bytes to index",
    )
    update_interval: PositiveInt = Field(
        default=86400,  # 24 hours
        description="How often to check for updates in seconds",
    )


class ResourceConfig(BaseModel):
    """Configuration for resources (agents, skills, etc.)."""

    search_paths: list[Path] = Field(default_factory=list, description="Additional paths to search for resources")


class PromptConfig(BaseModel):
    """Configuration for prompts."""

    search_paths: list[Path] = Field(default_factory=list, description="Additional paths to search for prompts")


class ServerConfig(BaseModel):
    """Configuration for the MCP server."""

    name: str = Field(default="holoviz-mcp", description="Server name")
    version: str = Field(default="1.0.0", description="Server version")
    description: str = Field(default="Model Context Protocol server for HoloViz ecosystem", description="Server description")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO", description="Logging level")
    transport: Literal["stdio", "http"] = Field(default="stdio", description="Transport protocol for MCP communication")
    host: str = Field(default="127.0.0.1", description="Host address to bind to when using HTTP transport (use 0.0.0.0 for Docker)")
    port: int = Field(default=8000, description="Port to bind to when using HTTP transport")
    anonymized_telemetry: bool = Field(default=False, description="Enable anonymized telemetry")
    jupyter_server_proxy_url: str = Field(default="", description="Jupyter server proxy URL for Panel app integration")
    vector_db_path: Path = Field(
        default_factory=lambda: (_holoviz_mcp_user_dir() / "vector_db" / "chroma").expanduser(), description="Path to the Chroma vector database."
    )


class HoloVizMCPConfig(BaseModel):
    """Main configuration for HoloViz MCP server."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    docs: DocsConfig = Field(default_factory=DocsConfig)
    resources: ResourceConfig = Field(default_factory=ResourceConfig)
    prompts: PromptConfig = Field(default_factory=PromptConfig)

    # Environment paths - merged from EnvironmentConfig with defaults
    user_dir: Path = Field(default_factory=_holoviz_mcp_user_dir, description="User configuration directory")
    default_dir: Path = Field(default_factory=_holoviz_mcp_default_dir, description="Default configuration directory")
    repos_dir: Path = Field(default_factory=lambda: _holoviz_mcp_user_dir() / "repos", description="Repository download directory")

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    def config_file_path(self, location: Literal["user", "default"] = "user") -> Path:
        """Get the path to the configuration file.

        Args:
            location: Whether to get user or default config file path
        """
        if location == "user":
            return self.user_dir / "config.yaml"
        else:
            return self.default_dir / "config.yaml"

    def resources_dir(self, location: Literal["user", "default"] = "user") -> Path:
        """Get the path to the resources directory.

        Args:
            location: Whether to get user or default resources directory
        """
        if location == "user":
            return self.user_dir / "resources"
        else:
            return self.default_dir / "resources"

    def agents_dir(self, location: Literal["user", "default"] = "user") -> Path:
        """Get the path to the agents directory.

        Args:
            location: Whether to get user or default agents directory
        """
        return self.resources_dir(location) / "agents"

    def skills_dir(self, location: Literal["user", "default"] = "user") -> Path:
        """Get the path to the skills directory.

        Args:
            location: Whether to get user or default skills directory
        """
        return self.resources_dir(location) / "skills"
