"""Tests for schema.json validation."""

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator

from holoviz_mcp.config.models import HoloVizMCPConfig


def get_schema_path() -> Path:
    """Get path to schema.json."""
    return Path(__file__).parent.parent.parent / "src" / "holoviz_mcp" / "config" / "schema.json"


def get_config_path() -> Path:
    """Get path to default config.yaml."""
    return Path(__file__).parent.parent.parent / "src" / "holoviz_mcp" / "config" / "config.yaml"


class TestSchemaValidation:
    """Test JSON schema validation."""

    def test_schema_is_valid_json(self):
        """Test that schema.json is valid JSON."""
        schema_path = get_schema_path()
        with open(schema_path) as f:
            schema = json.load(f)

        assert schema is not None
        assert "$schema" in schema
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"

    def test_schema_validates_config_yaml(self):
        """Test that schema.json validates the default config.yaml."""
        schema_path = get_schema_path()
        config_path = get_config_path()

        with open(schema_path) as f:
            schema = json.load(f)

        with open(config_path) as f:
            config = yaml.safe_load(f)

        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(config))

        if errors:
            error_messages = [f"Path: {'.'.join(str(p) for p in e.path)}, Error: {e.message}" for e in errors]
            pytest.fail("Schema validation failed:\n" + "\n".join(error_messages))

    def test_schema_includes_all_server_fields(self):
        """Test that schema includes all ServerConfig fields."""
        schema_path = get_schema_path()
        with open(schema_path) as f:
            schema = json.load(f)

        server_props = schema["properties"]["server"]["properties"]

        # Check all required ServerConfig fields are present
        required_fields = [
            "name",
            "version",
            "description",
            "log_level",
            "transport",
            "host",
            "port",
            "anonymized_telemetry",
            "jupyter_server_proxy_url",
            "vector_db_path",
        ]

        for field in required_fields:
            assert field in server_props, f"Field '{field}' missing from server schema"

    def test_schema_includes_git_repository_url_transform(self):
        """Test that schema includes url_transform field for GitRepository."""
        schema_path = get_schema_path()
        with open(schema_path) as f:
            schema = json.load(f)

        # Navigate to GitRepository properties
        repo_schema = schema["properties"]["docs"]["properties"]["repositories"]["patternProperties"]["^[a-zA-Z0-9_-]+$"]
        repo_props = repo_schema["properties"]

        assert "url_transform" in repo_props, "url_transform field missing from GitRepository schema"
        assert "enum" in repo_props["url_transform"], "url_transform should have enum values"
        assert repo_props["url_transform"]["enum"] == ["holoviz", "plotly", "datashader"]

    def test_schema_includes_base_url_as_required(self):
        """Test that schema marks base_url as required for GitRepository."""
        schema_path = get_schema_path()
        with open(schema_path) as f:
            schema = json.load(f)

        # Navigate to GitRepository properties
        repo_schema = schema["properties"]["docs"]["properties"]["repositories"]["patternProperties"]["^[a-zA-Z0-9_-]+$"]

        assert "required" in repo_schema, "GitRepository should have required fields"
        assert "base_url" in repo_schema["required"], "base_url should be required"

    def test_schema_includes_top_level_path_fields(self):
        """Test that schema includes user_dir, default_dir, and repos_dir fields."""
        schema_path = get_schema_path()
        with open(schema_path) as f:
            schema = json.load(f)

        props = schema["properties"]

        # Check all top-level path fields are present
        path_fields = ["user_dir", "default_dir", "repos_dir"]

        for field in path_fields:
            assert field in props, f"Field '{field}' missing from top-level schema"

    def test_pydantic_model_matches_schema(self):
        """Test that Pydantic model can be instantiated with default config."""
        config_path = get_config_path()

        with open(config_path) as f:
            config_dict = yaml.safe_load(f)

        # This should not raise any validation errors
        config = HoloVizMCPConfig(**config_dict)

        assert config is not None
        assert config.server.name == "holoviz-mcp"
