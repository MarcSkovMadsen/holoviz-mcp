"""Shared configuration for the holoviz_mcp package."""

import os
from typing import cast

from fastmcp.server.server import Transport

TRANSPORT: Transport = cast(Transport, os.getenv("HOLOVIZ_MCP_TRANSPORT", "stdio"))
os.environ["ANONYMIZED_TELEMETRY"] = os.getenv("ANONYMIZED_TELEMETRY", "False")

JUPYTER_SERVER_PROXY_URL = os.getenv("JUPYTER_SERVER_PROXY_URL", "")
# For example "https://my-jupyterhub-domain/some-user-specific-prefix/proxy/"
