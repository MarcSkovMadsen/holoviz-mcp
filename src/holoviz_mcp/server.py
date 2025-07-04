"""HoloViz MCP Server.

This MCP server provides comprehensive tools, resources and prompts for working with the HoloViz ecosystem,
including Panel and hvPlot following best practices.

The server is composed of multiple sub-servers that provide various functionalities:

- Documentation: Search and access HoloViz documentation as context
- Panel Material UI: Tools, resources and prompts for using Panel Material UI
- Panel: Tools, resources and prompts for using Panel Material UI
"""

import asyncio
import logging
import sys

from fastmcp import FastMCP

from holoviz_mcp.docs_mcp.server import mcp as docs_mcp
from holoviz_mcp.panel_mcp.server import mcp as panel_mcp
from holoviz_mcp.shared import config

mcp: FastMCP = FastMCP(
    name="holoviz",
    instructions="""
    [HoloViz](https://holoviz.org/) MCP Server

    This MCP server provides comprehensive tools, resources and prompts for working with the HoloViz ecosystem,
    including [Panel](https://panel.holoviz.org/) and [hvPlot](https://hvplot.holoviz.org/) following best practices.

    The server is composed of multiple sub-servers that provide various functionalities:

    - Documentation: Search and access HoloViz documentation as context
    - Panel Material UI: Tools, resources and prompts for using Panel Material UI
    - Panel: Tools, resources and prompts for using Panel Material UI
    """,
)


async def setup_composed_server() -> None:
    """Set up the composed server by importing all sub-servers with prefixes.

    This uses static composition (import_server), which copies components
    from sub-servers into the main server with appropriate prefixes.
    """
    await mcp.import_server(docs_mcp, prefix="docs")
    await mcp.import_server(panel_mcp, prefix="panel")


def main() -> None:
    """Set up and run the composed MCP server."""
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

    async def setup_and_run() -> None:
        await setup_composed_server()
        await mcp.run_async(transport=config.TRANSPORT)

    asyncio.run(setup_and_run())


if __name__ == "__main__":
    # Run the composed MCP server
    main()
