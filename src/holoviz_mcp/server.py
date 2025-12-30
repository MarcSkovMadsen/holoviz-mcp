"""HoloViz MCP Server.

This MCP server provides comprehensive tools, resources and prompts for working with the HoloViz ecosystem,
including Panel and hvPlot following best practices.

The server is composed of multiple sub-servers that provide various functionalities:

- Documentation: Search and access HoloViz documentation as context
- hvPlot: Tools, resources and prompts for using hvPlot to develop quick, interactive plots in Python
- Panel: Tools, resources and prompts for using Panel Material UI
"""

import asyncio
import logging
import os

from fastmcp import FastMCP

from holoviz_mcp.config.loader import get_config
from holoviz_mcp.holoviews_mcp.server import mcp as holoviews_mcp
from holoviz_mcp.holoviz_mcp.server import mcp as holoviz_mcp
from holoviz_mcp.hvplot_mcp.server import mcp as hvplot_mcp
from holoviz_mcp.panel_mcp.server import mcp as panel_mcp

logger = logging.getLogger(__name__)

mcp: FastMCP = FastMCP(
    name="holoviz",
    instructions="""
    This MCP server provides comprehensive tools, resources and prompts for exploring data, creating data visualizations,
    data tools, dashboards and data apps using the HoloViz ecosystem.

    Use this MCP server to get help, resources, and prompts for working with the HoloViz ecosystem effectively.

    HoloViz provides a set of core Python packages that make visualization easier, more accurate, and more powerful:

    - [Colorcet](https://colorcet.holoviz.org): for perceptually uniform colormaps.
    - [Datashader](https://datashader.org): for rendering even the largest datasets.
    - [GeoViews](https://geoviews.org): to extend HoloViews for geographic data.
    - [HoloViews](https://holoviews.org): to create advanced, interactive and high quality data visualizations.
    - [hvPlot](https://hvplot.holoviz.org): to quickly generate interactive plots from your data.
    - [Lumen](https://lumen.holoviz.org): to build data-driven dashboards from a simple YAML specification that's well suited to modern AI tools like LLMs.
    - [Panel](https://panel.holoviz.org): for making data tools, dashboards and data apps using the Holoviz and wider PyData ecosystems.
    - [Param](https://param.holoviz.org): to create declarative user-configurable objects.
    """,
)


async def setup_composed_server() -> None:
    """Set up the composed server by importing all sub-servers with prefixes.

    This uses static composition (import_server), which copies components
    from sub-servers into the main server with appropriate prefixes.
    """
    await mcp.import_server(holoviz_mcp, prefix="holoviz")
    await mcp.import_server(hvplot_mcp, prefix="hvplot")
    await mcp.import_server(panel_mcp, prefix="panel")
    await mcp.import_server(holoviews_mcp, prefix="holoviews")


def main() -> None:
    """Set up and run the composed MCP server."""
    pid = f"Process ID: {os.getpid()}"
    print(pid)  # noqa: T201

    async def setup_and_run() -> None:
        await setup_composed_server()
        config = get_config()

        # Pass host and port for HTTP transport
        if config.server.transport == "http":
            await mcp.run_async(
                transport=config.server.transport,
                host=config.server.host,
                port=config.server.port,
            )
        else:
            await mcp.run_async(transport=config.server.transport)

    asyncio.run(setup_and_run())


if __name__ == "__main__":
    # Run the composed MCP server
    main()
