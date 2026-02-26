"""[HoloViz](https://holoviz.org/) Documentation MCP Server.

This server provides tools, resources and prompts for accessing documentation related to the HoloViz ecosystems
and any user-defined/internal documentation you have configured.

Use this server to search and access documentation for HoloViz libraries (Panel, hvPlot, etc.) and your custom projects.
"""

import atexit
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from typing import Optional

from fastmcp import Context
from fastmcp import FastMCP
from fastmcp.resources import FileResource
from fastmcp.utilities.types import Image
from mcp.types import ImageContent
from mcp.types import TextContent

from holoviz_mcp.config import logger
from holoviz_mcp.config.loader import get_config
from holoviz_mcp.core.docs import get_indexer
from holoviz_mcp.core.inspect import inspect_app as _inspect_app
from holoviz_mcp.core.skills import get_skill as _get_skill
from holoviz_mcp.core.skills import list_skills as _list_skills
from holoviz_mcp.display_mcp.client import DisplayClient
from holoviz_mcp.display_mcp.manager import PanelServerManager
from holoviz_mcp.holoviz_mcp.models import Document

# Global display manager instance (lazy-loaded, subprocess mode only)
_display_manager: Optional["PanelServerManager"] = None

# Global display client instance (lazy-loaded)
_display_client: Optional["DisplayClient"] = None


def _get_display_manager() -> Optional["PanelServerManager"]:
    """Get or create the Panel server manager (subprocess mode only)."""
    global _display_manager

    config = get_config()
    if not config.display.enabled or config.display.mode != "subprocess":
        return None

    if _display_manager is None:
        # Import here to avoid circular imports and only when needed
        from holoviz_mcp.display_mcp.manager import PanelServerManager

        # Create manager
        _display_manager = PanelServerManager(
            db_path=config.display.db_path,
            port=config.display.port,
            host=config.display.host,
            max_restarts=config.display.max_restarts,
        )

        # Start server
        if not _display_manager.start():
            logger.error("Failed to start Panel server for display tool")
            _display_manager = None
            return None

        # Register cleanup
        atexit.register(_cleanup_display_manager)

    return _display_manager


def _get_display_client() -> Optional["DisplayClient"]:
    """Get or create the Display Client."""
    global _display_client

    config = get_config()
    if not config.display.enabled:
        return None

    if _display_client is None:
        # Determine base URL based on mode
        if config.display.mode == "remote":
            if not config.display.server_url:
                logger.error("Remote mode enabled but server_url not configured")
                return None
            base_url = config.display.server_url
        else:  # subprocess mode
            manager = _get_display_manager()
            if not manager:
                return None
            base_url = manager.get_base_url()

        # Create client
        _display_client = DisplayClient(base_url=base_url)

        # Register cleanup
        atexit.register(_cleanup_display_client)

    return _display_client


def _cleanup_display_manager():
    """Cleanup Panel server on exit."""
    global _display_manager
    if _display_manager:
        logger.info("Cleaning up Panel server for display tool")
        _display_manager.stop()
        _display_manager = None


def _cleanup_display_client():
    """Cleanup Display Client on exit."""
    global _display_client
    if _display_client:
        logger.info("Cleaning up Display Client")
        _display_client.close()
        _display_client = None


# Create the lifespan context manager
@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Lifespan context manager for HoloViz MCP server.

    The display server is NOT started here. It is lazy-started on first
    use of the ``show`` tool via ``_get_display_manager()``.  Eagerly
    starting it caused failures for demo apps and Client() usage that
    never call ``show``.
    """
    try:
        yield None
    except Exception as e:
        logger.error(f"Error during app lifespan: {e}")
        raise


# The HoloViz MCP server instance
mcp: FastMCP = FastMCP(
    name="documentation",
    instructions="""
    [HoloViz](https://holoviz.org/) Documentation MCP Server.

    This server provides tools, resources and prompts for accessing documentation related to the HoloViz ecosystems
    and any user-defined/internal documentation you have configured.

    Use this server to search and access documentation for HoloViz libraries (Panel, hvPlot, etc.) and your custom projects.
    """,
)


@mcp.tool(name="skill_get")
def get_skill(name: str) -> str:
    """Get the specified skill for usage with LLMs.

    Use list_skills tool to see available skills.

    Args:
        name (str): The name of the skill to get. For example, "panel", "panel-material-ui",
        "panel-holoviews", "panel-custom-components" etc.


    Returns
    -------
        str: A string containing the skill in Markdown format.

    Examples
    --------
    >>> get_skill("holoviews")  # Best practices for using HoloViews
    >>> get_skill("hvplot")  # Best practices for using hvPlot
    >>> get_skill("panel-material-ui")  # Best practices for using Panel Material UI
    >>> get_skill("panel")  # Best practices for using Panel
    """
    return _get_skill(name)


@mcp.tool(name="skill_list")
def list_skills() -> list[dict[str, str]]:
    """List all available skills with descriptions (~8 skills).

    Use skill_get to retrieve the full content of a specific skill.

    Returns
    -------
        list[dict[str, str]]: Skills with 'name' and 'description' keys.
            Names are in hyphenated format (e.g., "panel-material-ui", "panel-custom-components").
    """
    return _list_skills()


@mcp.tool(name="ref_get")
async def get_reference_guide(
    component: str,
    project: str | None = None,
    content: bool = True,
    ctx: Context | None = None,
) -> list[Document]:
    """Find reference guides for specific components in HoloViz or user-defined projects.

    Use this when you know the exact component name and want its reference guide directly.
    For fuzzy or semantic search, use the search tool instead.

    Reference guides are a subset of all documents that focus on specific UI components
    or plot types, such as:

    - `panel`: "Button", "TextInput", ...
    - `hvplot`: "bar", "scatter", ...
    - `my-custom-project`: custom components from your organization

    Args:
        component (str): Name of the component (e.g., "Button", "TextInput", "bar", "scatter")
        project (str, optional): Project name. Defaults to None (searches all projects).
            Options: "panel", "panel-material-ui", "hvplot", "param", "holoviews"
        content (bool, optional): Whether to include full content. Defaults to True.
            Set to False to only return metadata for faster responses.

    Returns
    -------
        list[Document]: A list of reference guides for the component with full content.

    Examples
    --------
    >>> get_reference_guide("Button")  # Find Button component guide across all projects
    >>> get_reference_guide("Button", "panel")  # Find Panel Button component guide specifically
    >>> get_reference_guide("TextInput", "panel-material-ui")  # Find Material UI TextInput guide
    >>> get_reference_guide("bar", "hvplot")  # Find hvplot bar chart reference
    >>> get_reference_guide("scatter", "hvplot")  # Find hvplot scatter plot reference
    >>> get_reference_guide("Audio", content=False)  # Don't include Markdown content for faster response
    """
    indexer = get_indexer()
    return await indexer.search_get_reference_guide(component, project, content, ctx=ctx)


@mcp.tool(name="project_list")
async def list_projects() -> list[str]:
    """List all HoloViz and user-defined projects with indexed documentation (~20 projects).

    This includes both built-in HoloViz projects (panel, hvplot, etc.) and any custom/internal
    documentation projects you have configured.

    Returns
    -------
        list[str]: A list of project names that have documentation available.
                   Names are returned in hyphenated format (e.g., "panel-material-ui", "my-custom-project").
    """
    indexer = get_indexer()
    return await indexer.list_projects()


@mcp.tool(name="doc_get")
async def get_document(path: str, project: str, ctx: Context) -> Document:
    """Retrieve a specific document by path and project.

    Use this tool to look up a specific document within a project.

    Args:
        path: The relative path to the source document (e.g., "index.md", "how_to/customize.md")
        project: the name of the project (e.g., "panel", "panel-material-ui", "hvplot", "my-custom-project")

    Returns
    -------
        The markdown content of the specified document.
    """
    indexer = get_indexer()
    return await indexer.get_document(path, project, ctx=ctx)


@mcp.tool()
async def search(
    query: str,
    project: str | None = None,
    content: str | bool = "truncated",
    max_results: int = 2,
    max_content_chars: int | None = 10000,
    ctx: Context | None = None,
) -> list[Document]:
    """Search the HoloViz and any user defined project documentation using semantic similarity.

    IMPORTANT: This is a general purpose search tool. Not just for searching the HoloViz documentation.

    DO use this tool to search the HoloViz project documentation
    DO use this tool to search any additional user-defined project documentation.
    DO use the project_list tool to list the available projects.

    BEST PRACTICES:
    - For initial exploration, use content=False to get an overview of available documents
    - Use content="chunk" for quick snippets, content="full" for complete documents
    - Adjust max_content_chars if you need more or less content per result
    - Set max_content_chars=None to get untruncated content (use with caution for large docs)

    QUERY OPTIMIZATION:
    The search uses context-aware truncation that centers returned content on query keywords.
    To get the most relevant excerpts:

    - Use SPECIFIC terms: "CheckboxEditor SelectEditor" > "editor dropdown"
    - Use UNIQUE identifiers: "background_gradient text_gradient" > "styling colors"
    - Avoid COMMON terms that appear everywhere: "pandas", "import", "data", "widget"
    - Include CLASS/FUNCTION names: "add_filter RangeSlider" > "filtering with widgets"
    - Use MULTIPLE specific terms: Helps the algorithm find the right section
    - Target FEATURE-SPECIFIC vocabulary: Terms unique to the feature you're looking for

    Example: Instead of "how to add pagination to a table", use "pagination page_size local remote"
    This ensures the truncated content focuses on the pagination section, not generic table info.

    Args:
        query (str): Search query using natural language or specific keywords.
            Natural language works for finding documents, but specific terms work better
            for content truncation. See QUERY OPTIMIZATION above.

            Good examples: "Button onClick on_click callback event", "hvPlot bar chart kind options"
            Okay examples: "how to style Material UI components", "interactive plotting with widgets"
        project (str, optional): Optional project filter. Defaults to None.
            Examples: "panel", "hvplot", "my-custom-project""
        content (str | bool, optional): Controls what content is returned. Defaults to "truncated".
            - "truncated": Full document content, smart-truncated around query keywords (default)
            - "chunk": Only the best-matching chunk from the document
            - "full": Full document content with no truncation (can be very large)
            - False: No content, metadata only (fastest)
            For backward compat, True maps to "truncated".
        max_results (int, optional): Maximum number of results to return. Defaults to 2.
            Increase if you need more options, but be mindful of response size.
        max_content_chars (int | None, optional): Maximum characters of content per result.
            Defaults to 10000. Set to None for untruncated content (may cause token limit errors).
            Content is truncated at word boundaries with an ellipsis indicator.

    Returns
    -------
        list[Document]: A list of relevant documents ordered by relevance.

    Examples
    --------
    >>> search("Button onClick on_click callback event", "panel-material-ui")  # Optimized: specific class and methods
    >>> search("hvPlot bar chart kind colormap", "hvplot")  # Optimized: feature-specific terms
    >>> search("FlexBox GridBox layout responsive sizing", "panel")  # Optimized: specific layout classes
    >>> search("Tabulator pagination page_size local remote", "panel", max_results=3)  # Optimized with more results
    >>> search("Param Parameter depends watch", content=False)  # Quick metadata search with specific terms
    >>> search("stream follow rollover patch", max_content_chars=5000)  # Streaming-specific methods
    >>> search("custom database connector SQL query", "my-custom-project")  # User project with specific terms
    >>> search("Tabulator formatters", content="full")  # Full document content, no truncation
    >>> search("Button widget", content="chunk")  # Only the best-matching chunk
    """
    indexer = get_indexer()
    return await indexer.search(query, project, content, max_results, max_content_chars, ctx=ctx)


# @mcp.tool(enabled=False)
async def update_index(ctx: Context) -> str:
    """Update the documentation index by re-cloning repositories and re-indexing content.

    DO use this tool periodically (weekly) to ensure the documentation index is up-to-date
    with the latest changes in the HoloViz ecosystem.

    Warning: This operation can take a long time (up to 5 minutes) depending on the number of
    repositories and their size!

    Returns
    -------
        str: Status message indicating the result of the update operation.

    Examples
    --------
    >>> update_index()  # Updates all documentation repositories and rebuilds index
    """
    try:
        indexer = get_indexer()

        # Use True as ctx to enable print statements for user feedback
        await indexer.index_documentation(ctx=ctx)

        return "Documentation index updated successfully."
    except Exception as e:
        logger.error(f"Failed to update documentation index: {e}")
        error_msg = f"Failed to update documentation index: {str(e)}"
        return error_msg


@mcp.tool(name="show")
async def display(
    code: str,
    name: str = "",
    description: str = "",
    method: Literal["jupyter", "panel"] = "jupyter",
    ctx: Context | None = None,
) -> str:
    """Display Python code visualization in a browser.

    This tool executes Python code and renders it in a Panel web interface,
    returning a URL where you can view the output. The code is validated
    before execution and any errors are reported immediately.

    Use this tool to when ever the user asks to show, display, visualize data, plots, dashboards, and other Python objects.

    Parameters
    ----------
    code : str
        The Python code to execute. For "jupyter" method, the last line is displayed.
        For "panel" method, objects marked .servable() are displayed.
    name : str, optional
        A name for the visualization (displayed in admin/feed views)
    description : str, optional
        A short description of the visualization
    method : {"jupyter", "panel"}, default "jupyter"
        Execution mode:
        - "jupyter": Execute code and display the last expression's result. The last expression must be dedented fully.
            DO use this for standard data visualizations like plots, dataframes, etc. that do not import and use Panel directly.
        - "panel": Execute code and and display Panel objects marked .servable()
            DO use this for code that imports and uses Panel to create dashboards, apps, and complex layouts.

    Returns
    -------
    str
        URL to view the rendered visualization (e.g., http://localhost:5005/view?id=abc123)

    Raises
    ------
    RuntimeError
        If the display server is not enabled or not running
    ValueError
        If code execution fails (syntax error, runtime error)

    Examples
    --------
    Simple visualization with jupyter method:
    >>> code = '''
    ... import pandas as pd
    ... df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
    ... df
    ... '''
    >>> url = await display(code, name="Sample DataFrame")

    Panel app with servable:
    >>> code = '''
    ... import panel as pn
    ... pn.extension()
    ... pn.pane.Markdown("# Hello World").servable()
    ... '''
    >>> url = await display(code, method="panel")
    """
    config = get_config()

    if not config.display.enabled:
        return "Error: Display server is not enabled. Set display.enabled=true in config."

    # Get client
    client = _get_display_client()
    if not client:
        return "Error: Failed to initialize display client. Check logs for details."

    # Check health with mode-aware logic
    if not client.is_healthy():
        if config.display.mode == "subprocess":
            # Try to restart in subprocess mode
            if ctx:
                await ctx.info("Display server is not healthy, attempting restart...")

            manager = _get_display_manager()
            if manager and manager.restart():
                # Recreate client with new base URL
                global _display_client
                if _display_client:
                    _display_client.close()
                _display_client = DisplayClient(base_url=manager.get_base_url())
                client = _display_client
            else:
                return "Error: Display server is not healthy and failed to restart."
        else:
            # Fail fast in remote mode
            return "Error: Display server is not healthy. Check remote server status."

    # Send request to Panel server
    try:
        response = client.create_snippet(
            code=code,
            name=name,
            description=description,
            method=method,
        )
        url = response.get("url", "")

        # Check for errors in response
        if error_message := response.get("error_message", None):
            return f"""
Visualization created with errors. View here {url}

{error_message}
"""

        return f"Visualization created successfully!\n\nView here {url}"

    except Exception as e:
        logger.exception(f"Error creating visualization: {e}")

        if ctx:
            await ctx.error(f"Failed to create visualization: {e}")

        return f"Error: Failed to create visualization: {str(e)}"


@mcp.tool()
async def inspect(
    url: str = "http://localhost:5006/",
    width: int = 1920,
    height: int = 1200,
    full_page: bool = False,
    delay: int = 2,
    save_screenshot: bool | str = False,
    screenshot: bool = True,
    console_logs: bool = True,
    log_level: str | None = None,
) -> list[TextContent | ImageContent]:
    """
    Inspect a running web app by capturing a screenshot and/or browser console logs.

    Web apps (especially custom components) often have JavaScript errors that are
    invisible to users and LLMs. This tool captures both a visual screenshot and the
    browser console output in a single call, making it easy to diagnose rendering
    issues, JS errors, and runtime warnings.

    Arguments
    ----------
    url : str, default="http://localhost:5006/"
        The URL of the page to inspect.
    width : int, default=1920
        The width of the browser viewport.
    height : int, default=1200
        The height of the browser viewport.
    full_page : bool, default=False
        Whether to capture the full scrollable page.
    delay : int, default=2
        Seconds to wait after page load before capturing, to allow dynamic content to render.
    save_screenshot : bool | str, default=False
        Whether and where to save the screenshot to disk:
        - True: Save to default screenshots directory (~/.holoviz-mcp/screenshots/) with auto-generated filename
        - False: Don't save screenshot to disk (only return to AI)
        - str: Save to specified absolute path (raises ValueError if path is not absolute)
    screenshot : bool, default=True
        Whether to capture a screenshot of the page.
    console_logs : bool, default=True
        Whether to capture browser console log messages.
    log_level : str | None, default=None
        Filter console logs by level. If None, all levels are captured.
        Common levels: 'log', 'info', 'warning', 'error', 'debug'.
    """
    config = get_config()
    screenshots_dir = config.server.screenshots_dir if save_screenshot is True else None

    core_result = await _inspect_app(
        url=url,
        width=width,
        height=height,
        full_page=full_page,
        delay=delay,
        save_screenshot=save_screenshot,
        screenshot=screenshot,
        console_logs=console_logs,
        log_level=log_level,
        screenshots_dir=screenshots_dir,
    )

    # Convert core InspectResult to MCP content types
    result: list[TextContent | ImageContent] = []

    if core_result.screenshot is not None:
        image = Image(data=core_result.screenshot, format="png")
        result.append(image.to_image_content())

    if console_logs:
        logs_json = json.dumps([entry.model_dump() for entry in core_result.console_logs], indent=2)
        result.append(TextContent(type="text", text=logs_json))

    return result


def _add_agent_resources():
    """Add agent resources from the config/resources/agents directory."""
    config = get_config()
    files = config.agents_dir("default").rglob("*.agent.md")
    for file_path in files:
        path = Path(file_path)
        name = path.name.replace(".agent.md", "").replace("-", "_")  # filename without suffix
        resource = FileResource(
            uri=f"resources://agents/{path.name}",
            path=path.absolute(),  # Path to the actual file
            name=name + "_agent",
            description=f"{name} Agent",
            mime_type="text/markdown",
            tags=["holoviz", "agent"],
        )
        mcp.add_resource(resource)


def _add_skills_resources():
    """Add skill resources from the config/resources/skills directory."""
    config = get_config()
    files = config.skills_dir("default").rglob("*.md")
    for file_path in files:
        path = Path(file_path)
        name = path.stem.replace("-", "_")  # filename without suffix
        resource = FileResource(
            uri=f"resources://skills/{path.name}",
            path=path.absolute(),  # Path to the actual file
            name=name,
            description=f"Best practices for {name}",
            mime_type="text/markdown",
            tags=["holoviz", "skills"],
        )
        mcp.add_resource(resource)


_add_agent_resources()
_add_skills_resources()

if __name__ == "__main__":
    config = get_config()
    mcp.run(transport=config.server.transport)
