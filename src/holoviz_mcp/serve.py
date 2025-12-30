#!/usr/bin/env python3
"""Serve Panel apps with configurable arguments."""

import logging
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

THUMBNAILS_DIR = Path(__file__).parent / "thumbnails"


def main(port: int = 5006, address: str = "0.0.0.0", allow_websocket_origin="*", num_procs: int = 1) -> None:
    """Serve all Panel apps in the apps directory."""
    apps_dir = Path(__file__).parent / "apps"
    app_files = [str(f) for f in apps_dir.glob("*.py") if f.name != "__init__.py"]
    if not app_files:
        logger.warning("No Panel apps found in apps directory")
        return

    # Use python -m panel to ensure we use the same Python environment
    cmd = [
        sys.executable,
        "-m",
        "panel",
        "serve",
        *app_files,
        "--static-dirs",
        f"thumbnails={THUMBNAILS_DIR}",
        "--port",
        str(port),
        "--address",
        address,
        "--allow-websocket-origin",
        allow_websocket_origin,
        "--num-procs",
        str(num_procs),
    ]
    logger.info(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("Server stopped")


if __name__ == "__main__":
    main()
