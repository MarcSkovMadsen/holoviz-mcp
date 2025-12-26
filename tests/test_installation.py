"""Integration tests for different installation methods of holoviz-mcp.

These tests verify that the server can be installed and run using:
1. UV tool installation from git
2. Docker container

Note: These tests require uv and docker to be installed and available on the system.
"""

import os
import shutil
import subprocess
import time

import pytest


def is_docker_available():
    """Check if Docker is available and the daemon is running."""
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


@pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker not available or daemon not running",
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

            # Wait for container to initialize (with retry)
            max_wait = 10
            interval = 0.5
            elapsed = 0.0
            status = None
            while elapsed < max_wait:
                status = subprocess.run(
                    ["docker", "ps", "-a", "-f", f"name={container_name}", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True,
                )
                container_status = status.stdout.strip()
                # Accept if container is present and in a known state (Up, Exited, or Created)
                if container_status and container_status.startswith(("Up", "Exited", "Created")):
                    break
                time.sleep(interval)
                elapsed += interval

            # Check container status (may have exited for stdio, which is ok)
            assert status is not None and status.stdout.strip(), f"Container {container_name} not found or not ready after {max_wait} seconds"

            # Wait for logs to appear with retry logic (logs may take time due to buffering)
            max_log_wait = 15  # Maximum 15 seconds to wait for logs
            log_check_interval = 1
            log_elapsed = 0
            combined_output = ""

            while log_elapsed < max_log_wait:
                time.sleep(log_check_interval)
                log_elapsed += log_check_interval

                logs = subprocess.run(
                    ["docker", "logs", container_name],
                    capture_output=True,
                    text=True,
                )
                combined_output = logs.stdout + logs.stderr

                # Check if we have the expected log content
                if "Starting MCP server 'holoviz'" in combined_output:
                    break

            # Add diagnostic info if logs are still incomplete after waiting
            if not combined_output.strip() or "Starting MCP server 'holoviz'" not in combined_output:
                # Get additional diagnostic info
                inspect = subprocess.run(
                    ["docker", "inspect", container_name],
                    capture_output=True,
                    text=True,
                )
                ps_output = subprocess.run(
                    ["docker", "ps", "-a", "-f", f"name={container_name}"],
                    capture_output=True,
                    text=True,
                )
                diagnostic_msg = (
                    f"Logs incomplete after {log_elapsed}s. Container status: {status.stdout}\n"
                    f"Docker ps output:\n{ps_output.stdout}\n"
                    f"Actual logs ({len(combined_output)} chars):\n{combined_output[:1000]}\n"
                    f"Container inspect (last 500 chars):\n{inspect.stdout[-500:]}"
                )
                pytest.fail(diagnostic_msg)

            assert "FastMCP" in combined_output, f"Server banner not found in logs. Output: {combined_output[:500]}"
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

            # Wait for container to initialize (with retry)
            max_wait = 10
            interval = 0.5
            elapsed = 0.0
            while elapsed < max_wait:
                status_check = subprocess.run(
                    ["docker", "ps", "-f", f"name={container_name}", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True,
                )
                if status_check.stdout.strip():
                    break
                time.sleep(interval)
                elapsed += interval

            # Check if container is still running
            status = subprocess.run(
                ["docker", "ps", "-f", f"name={container_name}", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
            )
            assert status.stdout.strip(), f"Container {container_name} is not running"

            # Wait for logs to appear with retry logic (HTTP server takes time to start)
            max_log_wait = 20  # HTTP needs more time than STDIO
            log_check_interval = 1
            log_elapsed = 0
            combined_output = ""

            while log_elapsed < max_log_wait:
                time.sleep(log_check_interval)
                log_elapsed += log_check_interval

                logs = subprocess.run(
                    ["docker", "logs", container_name],
                    capture_output=True,
                    text=True,
                )
                combined_output = logs.stdout + logs.stderr

                # Check if we have the expected log content
                if "Uvicorn running" in combined_output:
                    break

            # Verify logs contain expected content
            if not combined_output.strip():
                pytest.fail(f"No logs found after {log_elapsed}s. Container status: {status.stdout}")

            assert "FastMCP" in combined_output, f"Server banner not found in logs. Output: {combined_output[:500]}"
            assert "Transport:   HTTP" in combined_output, "HTTP transport not detected"
            # Server can bind to either 127.0.0.1 or 0.0.0.0 depending on configuration
            assert "http://127.0.0.1:8000/mcp" in combined_output or "http://0.0.0.0:8000/mcp" in combined_output, "Server URL not found in logs"
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
                    "holoviz-mcp:local",
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Failed to start container: {result.stderr}"

            # Wait for initialization
            time.sleep(10)

            # Check if container is still running
            status = subprocess.run(
                ["docker", "ps", "-f", f"name={container_name}", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
            )
            assert status.stdout.strip(), f"Container {container_name} is not running"

            # Check logs
            logs = subprocess.run(
                ["docker", "logs", container_name],
                capture_output=True,
                text=True,
            )

            combined_output = logs.stdout + logs.stderr
            assert combined_output.strip(), f"No logs found. Container status: {status.stdout}"
            # HTTP transport should be active
            assert "Transport:   HTTP" in combined_output, f"HTTP transport not detected. Logs: {combined_output[:500]}"

        finally:
            # Cleanup
            subprocess.run(["docker", "stop", container_name], capture_output=True)
            subprocess.run(["docker", "rm", container_name], capture_output=True)


@pytest.mark.skipif(
    shutil.which("uvx") is None,
    reason="UV not available",
)
class TestUVInstallation:
    """Test UV-based installation and execution."""

    def test_uv_help_command(self):
        """Test that uvx can run holoviz-mcp with --help flag."""
        # This test requires the package to be installed via uv tool install
        # Skip if not already installed
        env = os.environ.copy()
        env["HOLOVIZ_MCP_PORT"] = "7653"  # Avoid port conflicts

        result = subprocess.run(
            ["uvx", "holoviz-mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,  # Avoid port conflicts
        )

        # If package not installed, this will fail - that's expected
        # We just verify the command structure is correct
        # A return code of 0 means success
        if result.returncode == 0:
            # If successful, verify output contains expected content
            std = (result.stdout + result.stderr).lower()
            assert "holoviz" in std or "mcp" in std
        else:
            raise RuntimeError(f"uvx command failed unexpectedly:\n\n{result.stderr}")


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

        # After CLI refactoring, we only have one entry point
        assert "holoviz-mcp" in scripts, "holoviz-mcp entry point not found"
        assert scripts["holoviz-mcp"] == "holoviz_mcp.cli:cli_main", "holoviz-mcp entry point has incorrect target"

    def test_required_dependencies_in_pyproject(self):
        """Verify all required dependencies are in pyproject.toml."""
        import tomllib
        from pathlib import Path

        from packaging.requirements import Requirement

        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        dependencies = pyproject.get("project", {}).get("dependencies", [])
        dep_names = []
        for dep in dependencies:
            try:
                req = Requirement(dep)
                dep_names.append(req.name)
            except Exception:
                # Fallback for unparsable dependencies
                dep_names.append(dep.split("[")[0].split(">=")[0].split("==")[0].strip())

        required_deps = ["fastmcp", "panel", "chromadb", "pydantic", "typer"]

        for dep in required_deps:
            assert dep in dep_names, f"Required dependency '{dep}' not found in pyproject.toml"
