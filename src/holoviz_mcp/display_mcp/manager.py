"""Panel server subprocess management.

This module manages the Panel server as a subprocess, including
startup, health checks, and shutdown.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests  # type: ignore[import-untyped]

from holoviz_mcp.config import logger
from holoviz_mcp.config.loader import get_config


class PanelServerManager:
    """Manages the Panel server subprocess."""

    def __init__(
        self,
        db_path: Path,
        port: int = 5005,
        host: str = "127.0.0.1",
        max_restarts: int = 3,
    ):
        """Initialize the Panel server manager.

        Parameters
        ----------
        db_path : Path
            Path to SQLite database
        port : int
            Port for Panel server
        host : str
            Host address for Panel server
        max_restarts : int
            Maximum number of restart attempts
        """
        self.db_path = db_path
        self.port = port
        self.host = host
        self.max_restarts = max_restarts
        self.process: Optional[subprocess.Popen] = None
        self.restart_count = 0

    def start(self) -> bool:
        """Start the Panel server subprocess.

        Returns
        -------
        bool
            True if started successfully, False otherwise
        """
        if self.process and self.process.poll() is None:
            logger.info("Panel server is already running")
            return True

        try:
            # Get path to app.py
            app_path = Path(__file__).parent / "app.py"

            # Set up environment
            env = os.environ.copy()
            env["DISPLAY_DB_PATH"] = str(self.db_path)
            env["PANEL_SERVER_PORT"] = str(self.port)
            env["PANEL_SERVER_HOST"] = self.host

            logger.info(f"Using database at: {env['DISPLAY_DB_PATH']}")

            # Start subprocess
            logger.info(f"Starting Panel server on {self.host}:{self.port}")
            self.process = subprocess.Popen(
                [sys.executable, str(app_path)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for server to be ready
            if self._wait_for_health():
                logger.info("Panel server started successfully")
                self.restart_count = 0
                return True
            else:
                logger.error("Panel server failed to start (health check failed)")
                self.stop()
                return False

        except Exception as e:
            logger.exception(f"Error starting Panel server: {e}")
            return False

    def _wait_for_health(self, timeout: int = 30, interval: float = 1.0) -> bool:
        """Wait for Panel server to be healthy.

        Parameters
        ----------
        timeout : int
            Maximum time to wait in seconds
        interval : float
            Time between checks in seconds

        Returns
        -------
        bool
            True if server is healthy, False if timeout
        """
        start_time = time.time()
        base_url = f"http://{self.host}:{self.port}"

        while time.time() - start_time < timeout:
            try:
                # Try to connect to health endpoint
                response = requests.get(f"{base_url}/api/health", timeout=2)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass

            # Check if process died
            if self.process and self.process.poll() is not None:
                logger.error("Panel server process died during startup")
                return False

            time.sleep(interval)

        return False

    def is_healthy(self) -> bool:
        """Check if Panel server is healthy.

        Returns
        -------
        bool
            True if server is healthy, False otherwise
        """
        if not self.process or self.process.poll() is not None:
            return False

        try:
            base_url = f"http://{self.host}:{self.port}"
            response = requests.get(f"{base_url}/api/health", timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def stop(self, timeout: int = 5) -> None:
        """Stop the Panel server subprocess.

        Parameters
        ----------
        timeout : int
            Maximum time to wait for graceful shutdown
        """
        if not self.process:
            return

        try:
            logger.info("Stopping Panel server")
            self.process.terminate()

            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=timeout)
                logger.info("Panel server stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning("Panel server did not stop gracefully, killing")
                self.process.kill()
                self.process.wait()

        except Exception as e:
            logger.exception(f"Error stopping Panel server: {e}")
        finally:
            self.process = None

    def restart(self) -> bool:
        """Restart the Panel server.

        Returns
        -------
        bool
            True if restarted successfully, False otherwise
        """
        if self.restart_count >= self.max_restarts:
            logger.error(f"Maximum restart attempts ({self.max_restarts}) reached")
            return False

        self.restart_count += 1
        logger.info(f"Restarting Panel server (attempt {self.restart_count}/{self.max_restarts})")
        self.stop()
        return self.start()

    def get_base_url(self) -> str:
        """Get the base URL for the Panel server.

        Returns
        -------
        str
            Base URL
        """
        return f"http://{self.host}:{self.port}"


if __name__ == "__main__":
    config = get_config()
    display_manager = PanelServerManager(
        db_path=config.display.db_path,
        port=config.display.port,
        host=config.display.host,
        max_restarts=config.display.max_restarts,
    )

    # Start server
    if not display_manager.start():
        logger.error("Failed to start Panel server for display tool")

    # wait for keypress to exit
    try:
        logger.info("Press Enter to stop the Panel server...")
        input()
    except KeyboardInterrupt:
        pass

    display_manager.stop()
