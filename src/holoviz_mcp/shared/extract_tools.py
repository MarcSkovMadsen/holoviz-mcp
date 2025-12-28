#!/usr/bin/env python3
"""Extract tools from the MCP server for documentation."""

import asyncio
import logging

from holoviz_mcp.server import mcp
from holoviz_mcp.server import setup_composed_server

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def extract_tools():
    """Extract available tools from the HoloViz MCP server and return as structured data."""
    await setup_composed_server()
    tools_dict = await mcp.get_tools()

    # Group tools by category
    holoviz_tools = []
    panel_tools = []
    utility_tools = []

    for tool_name, tool_info in tools_dict.items():
        tool_data = {"name": tool_name, "description": getattr(tool_info, "description", "No description available"), "parameters": []}

        # Get input schema
        input_schema = getattr(tool_info, "inputSchema", None)
        if input_schema and hasattr(input_schema, "get") and "properties" in input_schema:
            for param_name, param_info in input_schema["properties"].items():
                required = param_name in input_schema.get("required", [])
                param_type = param_info.get("type", "unknown")
                desc = param_info.get("description", "No description")
                tool_data["parameters"].append({"name": param_name, "type": param_type, "required": required, "description": desc})

        # Categorize tools
        if any(x in tool_name for x in ["docs", "get_skill", "get_reference_guide", "get_document", "update_docs"]) or (
            tool_name == "search" and "component" not in str(tool_info)
        ):
            holoviz_tools.append(tool_data)
        elif any(x in tool_name for x in ["component", "packages"]) or "search" in tool_name:
            panel_tools.append(tool_data)
        else:
            utility_tools.append(tool_data)

    return {"panel_tools": panel_tools, "holoviz_tools": holoviz_tools, "utility_tools": utility_tools}


async def main():
    """Extract and print available tools from the HoloViz MCP server."""
    tools_data = await extract_tools()
    logger.info("## 🛠️ Available Tools")
    logger.info("")

    def print_tools(tools_list, category_name):
        if not tools_list:
            return
        logger.info("<details>")
        logger.info(f"<summary><b>{category_name}</b></summary>")
        logger.info("")
        for tool_data in tools_list:
            logger.info(f"- **{tool_data['name']}**: {tool_data['description']}")
            logger.info("")
        logger.info("</details>")
        logger.info("")

    print_tools(tools_data["panel_tools"], "Panel Components")
    print_tools(tools_data["holoviz_tools"], "Documentation")
    print_tools(tools_data["utility_tools"], "Utilities")


if __name__ == "__main__":
    asyncio.run(main())
