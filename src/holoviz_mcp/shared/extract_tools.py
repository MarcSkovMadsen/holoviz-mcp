#!/usr/bin/env python3
"""Extract tools from the MCP server for documentation."""

import asyncio
import logging

from holoviz_mcp.server import mcp
from holoviz_mcp.server import setup_composed_server

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def main():
    """Extract and print available tools from the HoloViz MCP server."""
    await setup_composed_server()
    tools_dict = await mcp.get_tools()
    logger.info("## 🛠️ Available Tools")
    logger.info("")

    # Group tools by category
    docs_tools = []
    panel_tools = []
    utility_tools = []

    for tool_name, tool_info in tools_dict.items():
        if any(x in tool_name for x in ["docs", "get_best_practices", "get_reference_guide", "get_page", "update_docs"]) or (
            tool_name == "search" and "component" not in str(tool_info)
        ):
            docs_tools.append((tool_name, tool_info))
        elif any(x in tool_name for x in ["component", "packages"]) or "search" in tool_name:
            panel_tools.append((tool_name, tool_info))
        else:
            utility_tools.append((tool_name, tool_info))

    def print_tools(tools_list, category_name):
        if not tools_list:
            return
        logger.info("<details>")
        logger.info(f"<summary><b>{category_name}</b></summary>")
        logger.info("")
        for tool_name, tool_info in tools_list:
            logger.info(f"- **{tool_name}**")
            # Get description from tool_info
            description = getattr(tool_info, "description", "No description available")
            logger.info(f"  - Description: {description}")

            # Get input schema
            input_schema = getattr(tool_info, "inputSchema", None)
            if input_schema and hasattr(input_schema, "get") and "properties" in input_schema:
                logger.info("  - Parameters:")
                for param_name, param_info in input_schema["properties"].items():
                    required = param_name in input_schema.get("required", [])
                    param_type = param_info.get("type", "unknown")
                    desc = param_info.get("description", "No description")
                    req_str = "" if required else ", optional"
                    logger.info(f"    - `{param_name}` ({param_type}{req_str}): {desc}")
            else:
                logger.info("  - Parameters: None")
            logger.info("")
        logger.info("</details>")
        logger.info("")

    print_tools(panel_tools, "Panel Components")
    print_tools(docs_tools, "Documentation")
    print_tools(utility_tools, "Utilities")


if __name__ == "__main__":
    asyncio.run(main())
