"""Tests for display database module."""

import tempfile
from pathlib import Path

import pytest

from holoviz_mcp.display_mcp.database import Snippet
from holoviz_mcp.display_mcp.database import SnippetDatabase


class TestSnippetDatabase:
    """Tests for SnippetDatabase."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        db = SnippetDatabase(db_path)
        yield db

        # Cleanup
        db_path.unlink(missing_ok=True)

    def test_create_snippet(self, temp_db):
        """Test creating a display snippet."""
        snippet = Snippet(
            app="print('hello')",
            name="Test",
            description="Test description",
            method="jupyter",
        )

        created = temp_db.create_snippet(snippet)

        assert created.id == snippet.id
        assert created.app == "print('hello')"
        assert created.name == "Test"
        assert created.status == "pending"

    def test_get_snippet(self, temp_db):
        """Test retrieving a snippet."""
        snippet = Snippet(
            app="x = 1",
            name="Simple",
            method="jupyter",
        )

        temp_db.create_snippet(snippet)
        retrieved = temp_db.get_snippet(snippet.id)

        assert retrieved is not None
        assert retrieved.id == snippet.id
        assert retrieved.app == "x = 1"

    def test_get_nonexistent_snippet(self, temp_db):
        """Test getting a snippet that doesn't exist."""
        result = temp_db.get_snippet("nonexistent")
        assert result is None

    def test_update_snippet(self, temp_db):
        """Test updating a snippet."""
        snippet = Snippet(
            app="y = 2",
            method="jupyter",
        )

        temp_db.create_snippet(snippet)

        # Update status
        updated = temp_db.update_snippet(
            snippet.id,
            status="success",
            execution_time=1.5,
        )

        assert updated is True

        # Retrieve and verify
        retrieved = temp_db.get_snippet(snippet.id)
        assert retrieved.status == "success"
        assert retrieved.execution_time == 1.5

    def test_list_snippets(self, temp_db):
        """Test listing snippets."""
        # Create multiple snippets
        for i in range(5):
            snippet = Snippet(
                app=f"x = {i}",
                name=f"Test {i}",
                method="jupyter",
            )
            temp_db.create_snippet(snippet)

        # List all
        snippets = temp_db.list_snippets()
        assert len(snippets) == 5

        # List with limit
        snippets = temp_db.list_snippets(limit=3)
        assert len(snippets) == 3

    def test_delete_snippet(self, temp_db):
        """Test deleting a snippet."""
        snippet = Snippet(
            app="z = 3",
            method="jupyter",
        )

        temp_db.create_snippet(snippet)

        # Delete
        deleted = temp_db.delete_snippet(snippet.id)
        assert deleted is True

        # Verify deleted
        retrieved = temp_db.get_snippet(snippet.id)
        assert retrieved is None

    def test_search_snippets(self, temp_db):
        """Test full-text search."""
        # Create snippets with different content
        snippets = [
            Snippet(app="import pandas", name="Pandas Test", method="jupyter"),
            Snippet(app="import numpy", name="NumPy Test", method="jupyter"),
            Snippet(app="import matplotlib", name="Plotting", method="jupyter"),
        ]

        for snippet in snippets:
            temp_db.create_snippet(snippet)

        # Search for pandas
        results = temp_db.search_snippets("pandas")
        assert len(results) >= 1
        assert any("pandas" in r.app.lower() or "pandas" in r.name.lower() for r in results)
