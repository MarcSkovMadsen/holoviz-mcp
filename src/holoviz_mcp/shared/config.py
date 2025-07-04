"""Shared configuration for the holoviz_mcp package."""

import os
from typing import cast

from fastmcp.server.server import Transport

TRANSPORT: Transport = cast(Transport, os.getenv("HOLOVIZ_MCP_TRANSPORT", "stdio"))
