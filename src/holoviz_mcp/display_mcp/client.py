"""HTTP client for Display Server REST API.

This module provides a client for interacting with the Panel Display Server
via its REST API. The client can be used with either a locally-managed subprocess
or a remote server instance.
"""

import requests  # type: ignore[import-untyped]

from holoviz_mcp.config import logger


class DisplayClient:
    """HTTP client for Display Server REST API.

    This client handles all HTTP communication with the Panel Display Server,
    including health checks and snippet creation. It uses a persistent session
    for connection pooling.
    """

    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize the Display Client.

        Parameters
        ----------
        base_url : str
            Base URL of the Display Server (e.g., "http://localhost:5005")
        timeout : int
            Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def is_healthy(self) -> bool:
        """Check if Display Server is healthy.

        Returns
        -------
        bool
            True if server responds to health check, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def create_snippet(self, code: str, name: str = "", description: str = "", method: str = "jupyter") -> dict:
        """Create a visualization snippet on the Display Server.

        Sends Python code to the server for execution and rendering.

        Parameters
        ----------
        code : str
            Python code to execute
        name : str, optional
            Name for the visualization
        description : str, optional
            Description of the visualization
        method : str, optional
            Execution method ("jupyter" or "panel")

        Returns
        -------
        dict
            Server response containing either:
            - Success: {"url": str, "id": str, ...}
            - Error: {"error": str, "message": str, "traceback": str}

        Raises
        ------
        RuntimeError
            If HTTP request fails
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/snippet",
                json={
                    "code": code,
                    "name": name,
                    "description": description,
                    "method": method,
                },
                timeout=self.timeout,
            )

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.exception(f"Error creating visualization: {e}")
            raise RuntimeError(f"Failed to create visualization: {e}") from e

    def close(self) -> None:
        """Close the HTTP session and cleanup resources."""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
