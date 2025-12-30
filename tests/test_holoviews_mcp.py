import pytest

from holoviz_mcp.client import call_tool


@pytest.mark.asyncio
async def test_list_elements():
    """Test the list_elements tool with real data."""
    result = await call_tool("holoviews_list_elements", {})
    data = result.data
    assert isinstance(data, list)
    assert "Area" in data


@pytest.mark.asyncio
async def test_get_docstring():
    """Test the get_docstring tool with a known element."""
    result = await call_tool("holoviews_get_docstring", {"element": "Area"})
    text = result.content[0].text
    assert isinstance(text, str)
    assert "Area" in text
    assert "holoviews" in text
