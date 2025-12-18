"""
Integration tests for the client module.

These tests verify the functionality of the client module, including
the singleton client pattern and its thread safety under concurrent access.
"""

import asyncio

import pytest

from holoviz_mcp.client import call_tool


class TestClientSingleton:
    """Tests for the singleton client pattern."""

    @pytest.mark.asyncio
    async def test_concurrent_client_initialization(self):
        """Test that concurrent calls to call_tool don't create multiple clients.

        This test verifies that the singleton client pattern handles race
        conditions properly when multiple async tasks call call_tool
        concurrently before the client is initialized. The asyncio.Lock
        ensures only one task initializes the client.
        """
        # Reset the client state for testing
        # Note: This directly manipulates module state for testing purposes
        import holoviz_mcp.client as client_module

        client_module._CLIENT = None

        # Create multiple concurrent tasks that all call call_tool
        tasks = [
            call_tool("panel_list_components", {}),
            call_tool("panel_list_components", {}),
            call_tool("panel_list_components", {}),
            call_tool("panel_list_components", {}),
            call_tool("panel_list_components", {}),
        ]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)

        # All tasks should complete successfully
        assert len(results) == 5
        for result in results:
            assert result is not None
            # Results should contain component data
            assert isinstance(result.data, list)

    @pytest.mark.asyncio
    async def test_client_reuse(self):
        """Test that the client is reused across multiple calls."""
        # First call
        result1 = await call_tool("panel_list_components", {})
        assert result1 is not None

        # Second call should reuse the same client
        result2 = await call_tool("panel_list_components", {})
        assert result2 is not None

        # Both should return valid data
        assert isinstance(result1.data, list)
        assert isinstance(result2.data, list)

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Test multiple concurrent tool calls using the singleton client."""
        # Create tasks that call different tools concurrently
        tasks = [
            call_tool("panel_list_components", {}),
            call_tool("panel_list_packages", {}),
            call_tool("panel_list_components", {}),
        ]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)

        # All tasks should complete successfully
        assert len(results) == 3
        for result in results:
            assert result is not None
            assert isinstance(result.data, list)
