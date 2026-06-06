"""
Simple tests for the documentation MCP server.

Tests just the docs server functionality without the composed server.
"""

import json
from unittest.mock import patch

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

import holoviz_mcp.holoviz_mcp.server as docs_server
from holoviz_mcp.holoviz_mcp.server import mcp


@pytest.mark.asyncio
async def test_skills_resource():
    """Test the skills resource."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("skill_get", {"name": "panel"})
        assert result.data


@pytest.mark.asyncio
async def test_show_pyodide_payload():
    """show_pyodide returns a JSON text payload for app rendering."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool(
            "show_pyodide",
            {
                "code": "import panel as pn\npn.extension()\npn.pane.Markdown('hello').servable()",
                "name": "Pyodide test",
                "description": "Contract smoke test",
            },
        )

    assert isinstance(result.data, str)
    assert '"tool": "show_pyodide"' in result.data
    assert '"runtime": "panel-live-pyodide"' in result.data


@pytest.mark.asyncio
async def test_show_pyodide_requires_code():
    """show_pyodide returns a clear error when code is blank."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("show_pyodide", {"code": "   "})

    assert isinstance(result.data, str)
    assert "Code is required for show_pyodide" in result.data


@pytest.mark.asyncio
async def test_show_display_disabled_returns_legacy_error(monkeypatch: pytest.MonkeyPatch):
    """show preserves existing fallback error string when display is disabled."""

    class _DisplayConfig:
        enabled = False

    class _Config:
        display = _DisplayConfig()

    monkeypatch.setattr(docs_server, "get_config", lambda: _Config())

    client = Client(mcp)
    async with client:
        result = await client.call_tool("show", {"code": "1 + 1"})

    assert isinstance(result.data, str)
    assert result.data == "Error: Display server is not enabled. Set display.enabled=true in config."


@pytest.mark.asyncio
async def test_show_pyodide_does_not_use_display_client(monkeypatch: pytest.MonkeyPatch):
    """show_pyodide is runtime-isolated from display client/server path."""

    def _should_not_be_called():
        raise AssertionError("show_pyodide should not request display client")

    monkeypatch.setattr(docs_server, "_get_display_client", _should_not_be_called)

    client = Client(mcp)
    async with client:
        result = await client.call_tool("show_pyodide", {"code": "print('hello')"})

    assert isinstance(result.data, str)
    assert '"runtime": "panel-live-pyodide"' in result.data


@pytest.mark.asyncio
async def test_show_rewrites_localhost_url_for_codespaces(monkeypatch: pytest.MonkeyPatch):
    """show should rewrite localhost URLs to Codespaces forwarding URL when available."""

    class _DisplayConfig:
        enabled = True
        mode = "subprocess"

    class _ServerConfig:
        jupyter_server_proxy_url = ""

    class _Config:
        display = _DisplayConfig()
        server = _ServerConfig()

    class _FakeClient:
        def is_healthy(self):
            return True

        def create_snippet(self, code: str, name: str, description: str, method: str):
            return {"url": "http://localhost:5005/view?id=abc123"}

    monkeypatch.setattr(docs_server, "get_config", lambda: _Config())
    monkeypatch.setattr(docs_server, "_get_display_client", lambda: _FakeClient())

    with patch.dict(
        "os.environ",
        {
            "CODESPACE_NAME": "literate-chainsaw-54wjwvrrxv4c4p5q",
            "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN": "app.github.dev",
        },
        clear=False,
    ):
        result = await docs_server.display(code="1 + 1")

    assert "https://literate-chainsaw-54wjwvrrxv4c4p5q-5005.app.github.dev/view?id=abc123" in result


@pytest.mark.asyncio
async def test_show_returns_json_payload_for_mcp_app(monkeypatch: pytest.MonkeyPatch):
    """show returns a structured JSON payload consumable by the MCP App template."""

    class _DisplayConfig:
        enabled = True
        mode = "subprocess"

    class _ServerConfig:
        jupyter_server_proxy_url = ""

    class _Config:
        display = _DisplayConfig()
        server = _ServerConfig()

    class _FakeClient:
        def is_healthy(self):
            return True

        def create_snippet(self, code: str, name: str, description: str, method: str):
            return {"url": "http://localhost:5005/view?id=abc123"}

    monkeypatch.setattr(docs_server, "get_config", lambda: _Config())
    monkeypatch.setattr(docs_server, "_get_display_client", lambda: _FakeClient())

    raw_result = await docs_server.display(code="1 + 1", name="Demo", description="Plot", method="jupyter")
    payload = json.loads(raw_result)

    assert payload["tool"] == "show"
    assert payload["status"] == "success"
    assert payload["name"] == "Demo"
    assert payload["description"] == "Plot"
    assert payload["method"] == "jupyter"
    assert payload["url"].startswith("http")
    assert payload["url"].endswith("/view?id=abc123")


@pytest.mark.integration
@pytest.mark.skip(reason="this test is very slow")
@pytest.mark.asyncio
async def test_update_index():
    """Test the update_index tool."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("update_index")
        assert result.data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_projects():
    """Test that all projects are listed correctly."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("project_list")

    assert len(result.data) > 0
    assert "panel" in result.data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_semantic_search():
    """Test the search tool."""
    client = Client(mcp)
    async with client:
        # Test basic semantic search across all projects
        result = await client.call_tool("search", {"query": "dashboard layout best practices"})
        assert result.data
        assert isinstance(result.data, list)
        # Should return up to 5 results by default
        assert len(result.data) <= 5

        # Verify each result is a proper Document
        for document in result.data:
            assert hasattr(document, "title")
            assert hasattr(document, "url")
            assert hasattr(document, "project")
            assert hasattr(document, "source_path")
            assert hasattr(document, "source_url")
            # Should include content by default
            assert hasattr(document, "content")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_by_project():
    """Test the search tool with project filtering."""
    client = Client(mcp)
    async with client:
        # Test search with specific project filter
        result = await client.call_tool("search", {"query": "interactive plotting with widgets", "project": "hvplot"})
        assert result.data
        assert isinstance(result.data, list)

        # All results should be from hvplot project
        for document in result.data:
            assert document.project == "hvplot"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_with_custom_max_results():
    """Test the search tool with custom max_results parameter."""
    client = Client(mcp)
    async with client:
        # Test search with limited results
        result = await client.call_tool("search", {"query": "custom widgets", "project": "panel", "max_results": 3})
        assert result.data
        assert isinstance(result.data, list)
        # Should return at most 3 results
        assert len(result.data) <= 3

        # All results should be from panel project
        for document in result.data:
            assert document.project == "panel"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_without_content():
    """Test the search tool with content=False for metadata only."""
    client = Client(mcp)
    async with client:
        # Test search without content for faster response
        result = await client.call_tool("search", {"query": "parameter handling", "content": False})
        assert result.data
        assert isinstance(result.data, list)

        # Verify each result has metadata but no content
        for document in result.data:
            assert hasattr(document, "title")
            assert hasattr(document, "url")
            assert hasattr(document, "project")
            assert hasattr(document, "source_path")
            assert hasattr(document, "source_url")
            # Should not include content when content=False
            assert document.content is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_material_ui_specific():
    """Test the search tool with Material UI specific query."""
    client = Client(mcp)
    async with client:
        # Test search for Material UI styling
        result = await client.call_tool("search", {"query": "How to style Material UI components?", "project": "panel-material-ui"})
        assert result.data
        assert isinstance(result.data, list)

        # Results should be from panel-material-ui project
        for document in result.data:
            assert document.project == "panel-material-ui"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_empty_query():
    """Test the search tool with edge cases."""
    client = Client(mcp)
    async with client:
        # Test with empty query
        result = await client.call_tool("search", {"query": ""})
        # Should handle gracefully and return empty or minimal results
        assert isinstance(result.data, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_invalid_project():
    """Test the search tool with invalid project name."""
    client = Client(mcp)
    async with client:
        # Test with non-existent project
        result = await client.call_tool("search", {"query": "test query", "project": "nonexistent_project"})
        # Should handle gracefully and return empty results
        assert isinstance(result.data, list)
        assert len(result.data) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_with_project_filter():
    """Test the search tool with project filtering."""
    client = Client(mcp)
    async with client:
        # Test search with specific project filter
        result = await client.call_tool("doc_get", {"path": "doc/index.md", "project": "hvplot"})
        assert result.data
        assert result.data.title == "hvPlot"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_document_returns_full_content_after_chunking():
    """get_document() reconstructs full content from chunks."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("doc_get", {"path": "doc/index.md", "project": "hvplot"})
        assert result.data
        # Content should be non-empty and substantial (reconstructed from all chunks)
        assert result.data.content is not None
        assert len(result.data.content) > 100
        # Should contain content that appears in the full document
        assert "hvPlot" in result.data.content or "hvplot" in result.data.content.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_returns_unique_source_paths():
    """search() deduplicates by source_path — no two results share the same path."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("search", {"query": "widgets buttons interactive", "project": "panel", "max_results": 5})
        assert result.data
        assert isinstance(result.data, list)

        # All source_paths should be unique
        paths = [doc.source_path for doc in result.data]
        assert len(paths) == len(set(paths)), f"Duplicate source_paths found: {paths}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reference_guide_content_complete_after_chunking():
    """Reference guide returns complete merged content from all chunks."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("ref_get", {"component": "Button", "project": "panel"})
        assert result.data
        assert isinstance(result.data, list)
        assert len(result.data) == 1

        doc = result.data[0]
        assert doc.content is not None
        # Content should be substantial (merged from chunks, not just first chunk)
        assert len(doc.content) > 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_content_mode_chunk():
    """MCP tool with content='chunk' returns chunk-sized content."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("search", {"query": "Button widget", "project": "panel", "content": "chunk", "max_results": 1})
        assert result.data
        assert isinstance(result.data, list)
        assert len(result.data) >= 1

        doc = result.data[0]
        assert doc.content is not None

        # Chunk content should be no larger than full document content
        full_result = await client.call_tool("doc_get", {"path": doc.source_path, "project": doc.project})
        assert full_result.data
        assert len(doc.content) <= len(full_result.data.content)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_content_mode_full():
    """MCP tool with content='full' returns content matching get_document()."""
    client = Client(mcp)
    async with client:
        # Get search result with full content
        search_result = await client.call_tool("search", {"query": "Button widget", "project": "panel", "content": "full", "max_results": 1})
        assert search_result.data
        search_doc = search_result.data[0]

        # Get the same document via get_document
        full_doc = await client.call_tool("doc_get", {"path": search_doc.source_path, "project": search_doc.project})
        assert full_doc.data

        # Content should match
        assert search_doc.content == full_doc.data.content


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_content_mode_truncated_default():
    """Default content mode returns truncated full content."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("search", {"query": "dashboard layout", "max_results": 1})
        assert result.data
        doc = result.data[0]
        assert doc.content is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_keyword_prefilter_camelcase_integration():
    """Technical CamelCase terms find Tabulator reference via keyword pre-filter."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("search", {"query": "CheckboxEditor SelectEditor", "project": "panel", "content": False})
        assert result.data
        assert isinstance(result.data, list)
        titles = [doc.title for doc in result.data]
        assert any("Tabulator" in t for t in titles), f"Expected Tabulator in results, got: {titles}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_documents():
    """Test listing documents for a project."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("doc_list", {"project": "panel"})
        assert result.data
        docs = result.data
        assert isinstance(docs, list)
        assert len(docs) > 0

        # Each entry should be a DocumentSummary with the expected attributes
        for d in docs:
            assert hasattr(d, "source_path")
            assert hasattr(d, "title")
            assert hasattr(d, "is_reference")

        # Results should be sorted by source_path
        paths = [d.source_path for d in docs]
        assert paths == sorted(paths)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_documents_invalid_project():
    """Test listing documents for a nonexistent project raises error."""
    client = Client(mcp)
    async with client:
        with pytest.raises(ToolError, match="No documents found"):
            await client.call_tool("doc_list", {"project": "nonexistent_project_xyz"})


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_keyword_prefilter_mixed_integration():
    """Mixed technical terms (snake_case + CamelCase) find Tabulator reference."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("search", {"query": "add_filter RangeSlider Tabulator", "project": "panel", "content": False})
        assert result.data
        assert isinstance(result.data, list)
        titles = [doc.title for doc in result.data]
        assert any("Tabulator" in t for t in titles), f"Expected Tabulator in results, got: {titles}"
