"""Panel server subprocess management.

This module manages the Panel server as a subprocess, including
startup, health checks, and shutdown.
"""

import os
import signal
import socket
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
        host: str = "localhost",
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

    def _is_port_in_use(self) -> bool:
        """Check if the configured port is already in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self.host, self.port))
                return False
            except OSError:
                return True

    def _try_recover_stale_server(self) -> bool:
        """Try to recover from a stale server occupying the port.

        If the port is in use, checks whether the existing server is healthy.
        If healthy, adopts it. If unhealthy (zombie), finds and kills the
        stale process.

        Returns
        -------
        bool
            True if a healthy server is available on the port, False otherwise.
        """
        # First check if the existing server responds to health checks
        try:
            response = requests.get(f"http://{self.host}:{self.port}/api/health", timeout=3)
            if response.status_code == 200:
                logger.info(f"Found healthy display server already running on port {self.port}")
                return True
        except requests.RequestException:
            pass

        # Port is occupied but server is unresponsive (zombie) — try to find and kill it
        logger.warning(f"Port {self.port} is occupied by an unresponsive process, attempting cleanup")
        stale_pid = self._find_pid_on_port()
        if stale_pid:
            logger.info(f"Killing stale display server process (PID {stale_pid})")
            try:
                os.kill(stale_pid, signal.SIGTERM)
                # Give it a moment to release the port
                for _ in range(10):
                    time.sleep(0.5)
                    if not self._is_port_in_use():
                        logger.info(f"Stale process (PID {stale_pid}) cleaned up successfully")
                        return False
                # Still alive, force kill
                os.kill(stale_pid, signal.SIGKILL)
                time.sleep(1)
            except ProcessLookupError:
                pass  # Already dead
            except PermissionError:
                logger.error(f"No permission to kill stale process (PID {stale_pid})")
                return False

        if self._is_port_in_use():
            logger.error(f"Cannot free port {self.port} — another process is using it")
            return False

        return False

    def _find_pid_on_port(self) -> int | None:
        """Find the PID of a process listening on the configured port.

        Parses /proc/net/tcp on Linux to find the process.
        """
        port_hex = f"{self.port:04X}"
        try:
            with open("/proc/net/tcp") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) > 9 and parts[3] == "0A":  # LISTEN state
                        local = parts[1]
                        if local.split(":")[1].upper() == port_hex:
                            inode = int(parts[9])
                            return self._inode_to_pid(inode)
        except (FileNotFoundError, PermissionError):
            pass
        return None

    def _inode_to_pid(self, target_inode: int) -> int | None:
        """Find the PID that owns a given socket inode."""
        if target_inode == 0:
            return None
        try:
            for entry in os.listdir("/proc"):
                if not entry.isdigit():
                    continue
                fd_dir = f"/proc/{entry}/fd"
                try:
                    for fd in os.listdir(fd_dir):
                        try:
                            link = os.readlink(f"{fd_dir}/{fd}")
                            if f"socket:[{target_inode}]" in link:
                                return int(entry)
                        except (OSError, ValueError):
                            continue
                except PermissionError:
                    continue
        except (FileNotFoundError, PermissionError):
            pass
        return None

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

        # Check if port is already in use (stale process from previous session)
        if self._is_port_in_use():
            if self._try_recover_stale_server():
                # A healthy server is already running, adopt it
                return True
            # Stale server was cleaned up or port was freed, continue with startup
            if self._is_port_in_use():
                logger.error(f"Port {self.port} is still in use, cannot start display server")
                return False

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
            # Try to connect to health endpoint
            try:
                response = requests.get(f"{base_url}/api/health", timeout=2)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass  # The panel server has not started yet

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
    logger.info("Press Enter to stop the Panel server...")
    input()

    display_manager.stop()
