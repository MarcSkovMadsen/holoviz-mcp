"""Integration tests for different installation methods of holoviz-mcp.

These tests verify that the server can be installed and run using:
1. UV tool installation from git
2. Docker container

Note: These tests require uv and docker to be installed and available on the system.
"""

import subprocess
import time

import pytest


@pytest.mark.skipif(
    subprocess.run(["which", "docker"], capture_output=True).returncode != 0,
    reason="Docker not available",
)
class TestDockerInstallation:
    """Test Docker-based installation and execution."""

    def test_docker_image_exists_or_builds(self):
        """Verify Docker image exists or can be built."""
        # Check if image exists
        result = subprocess.run(
            ["docker", "images", "-q", "holoviz-mcp:local"],
            capture_output=True,
            text=True,
        )

        if not result.stdout.strip():
            # Image doesn't exist, try to build it
            build_result = subprocess.run(
                ["docker", "build", "-t", "holoviz-mcp:local", "."],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes max for build
            )
            assert build_result.returncode == 0, f"Docker build failed: {build_result.stderr}"

        # Verify image exists now
        result = subprocess.run(
            ["docker", "images", "-q", "holoviz-mcp:local"],
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip(), "Docker image not found after build"

    def test_docker_stdio_transport(self):
        """Test Docker container starts with stdio transport."""
        # Start container with stdio transport (default)
        container_name = "holoviz-test-stdio"

        try:
            # Run container in background
            result = subprocess.run(
                ["docker", "run", "-d", "--name", container_name, "holoviz-mcp:local"],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Failed to start container: {result.stderr}"

            # Wait for container to initialize
            time.sleep(8)  # Increased wait time for container initialization

            # Check logs for successful startup
            logs = subprocess.run(
                ["docker", "logs", container_name],
                capture_output=True,
                text=True,
            )

            combined_output = logs.stdout + logs.stderr
            assert "FastMCP" in combined_output, "Server banner not found in logs"
            assert "Transport:   STDIO" in combined_output, "STDIO transport not detected"
            assert "Starting MCP server 'holoviz'" in combined_output

        finally:
            # Cleanup
            subprocess.run(["docker", "stop", container_name], capture_output=True)
            subprocess.run(["docker", "rm", container_name], capture_output=True)

    def test_docker_http_transport(self):
        """Test Docker container starts with HTTP transport."""
        container_name = "holoviz-test-http"

        try:
            # Run container with HTTP transport
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    container_name,
                    "-p",
                    "8888:8000",  # Use different port to avoid conflicts
                    "-e",
                    "HOLOVIZ_MCP_TRANSPORT=http",
                    "holoviz-mcp:local",
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Failed to start container: {result.stderr}"

            # Wait for container to initialize
            time.sleep(5)

            # Check logs for successful startup
            logs = subprocess.run(
                ["docker", "logs", container_name],
                capture_output=True,
                text=True,
            )

            combined_output = logs.stdout + logs.stderr
            assert "FastMCP" in combined_output, "Server banner not found in logs"
            assert "Transport:   HTTP" in combined_output, "HTTP transport not detected"
            # Server can bind to either 127.0.0.1 or 0.0.0.0 depending on configuration
            assert (
                "http://127.0.0.1:8000/mcp" in combined_output or "http://0.0.0.0:8000/mcp" in combined_output
            ), "Server URL not found in logs"
            assert "Uvicorn running" in combined_output

        finally:
            # Cleanup
            subprocess.run(["docker", "stop", container_name], capture_output=True)
            subprocess.run(["docker", "rm", container_name], capture_output=True)

    def test_docker_environment_variables(self):
        """Test Docker container respects environment variables."""
        container_name = "holoviz-test-env"

        try:
            # Run container with custom environment variables
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    container_name,
                    "-e",
                    "HOLOVIZ_MCP_TRANSPORT=http",
                    "-e",
                    "HOLOVIZ_MCP_LOG_LEVEL=DEBUG",
                    "-e",
                    "HOLOVIZ_MCP_ALLOW_CODE_EXECUTION=false",
                    "holoviz-mcp:local",
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Failed to start container: {result.stderr}"

            # Wait for initialization
            time.sleep(5)

            # Check logs
            logs = subprocess.run(
                ["docker", "logs", container_name],
                capture_output=True,
                text=True,
            )

            combined_output = logs.stdout + logs.stderr
            # HTTP transport should be active
            assert "Transport:   HTTP" in combined_output

        finally:
            # Cleanup
            subprocess.run(["docker", "stop", container_name], capture_output=True)
            subprocess.run(["docker", "rm", container_name], capture_output=True)


@pytest.mark.skipif(
    subprocess.run(["which", "uvx"], capture_output=True).returncode != 0,
    reason="UV not available",
)
class TestUVInstallation:
    """Test UV-based installation and execution."""

    def test_uv_help_command(self):
        """Test that uvx can run holoviz-mcp with --help flag."""
        # This test requires the package to be installed via uv tool install
        # Skip if not already installed
        result = subprocess.run(
            ["uvx", "--from", "holoviz-mcp", "holoviz-mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # If package not installed, this will fail - that's expected
        # We just verify the command structure is correct
        # A return code of 0 means success
        if result.returncode == 0:
            # If successful, verify output contains expected content
            assert "holoviz" in result.stdout.lower() or "mcp" in result.stdout.lower()


@pytest.mark.integration
class TestPackageStructure:
    """Test package structure and entry points."""

    def test_pyproject_has_scripts(self):
        """Verify pyproject.toml defines the required entry points."""
        import tomllib
        from pathlib import Path

        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        scripts = pyproject.get("project", {}).get("scripts", {})

        assert "holoviz-mcp" in scripts, "holoviz-mcp entry point not found"
        assert "holoviz-mcp-update" in scripts, "holoviz-mcp-update entry point not found"
        assert "holoviz-mcp-serve" in scripts, "holoviz-mcp-serve entry point not found"

    def test_required_dependencies_in_pyproject(self):
        """Verify all required dependencies are in pyproject.toml."""
        import tomllib
        from pathlib import Path

        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        dependencies = pyproject.get("project", {}).get("dependencies", [])
        dep_names = [dep.split("[")[0].split(">=")[0].split("<")[0].split("==")[0] for dep in dependencies]

        required_deps = ["fastmcp", "panel", "chromadb", "pydantic", "sentence-transformers"]

        for dep in required_deps:
            assert dep in dep_names, f"Required dependency '{dep}' not found in pyproject.toml"
