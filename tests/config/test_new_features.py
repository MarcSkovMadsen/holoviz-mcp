"""Tests for new configuration features."""

import pytest
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as

from holoviz_mcp.config.loader import ConfigLoader
from holoviz_mcp.config.models import FolderConfig
from holoviz_mcp.config.models import GitRepository


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
