"""Tests for display database module."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from holoviz_mcp.display_mcp.database import DisplayDatabase
from holoviz_mcp.display_mcp.database import DisplayRequest


class TestDisplayDatabase:
    """Tests for DisplayDatabase."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        
        db = DisplayDatabase(db_path)
        yield db
        
        # Cleanup
        db_path.unlink(missing_ok=True)

    def test_create_request(self, temp_db):
        """Test creating a display request."""
        request = DisplayRequest(
            code="print('hello')",
            name="Test",
            description="Test description",
            method="jupyter",
        )
        
        created = temp_db.create_request(request)
        
        assert created.id == request.id
        assert created.code == "print('hello')"
        assert created.name == "Test"
        assert created.status == "pending"

    def test_get_request(self, temp_db):
        """Test retrieving a request."""
        request = DisplayRequest(
            code="x = 1",
            name="Simple",
            method="jupyter",
        )
        
        temp_db.create_request(request)
        retrieved = temp_db.get_request(request.id)
        
        assert retrieved is not None
        assert retrieved.id == request.id
        assert retrieved.code == "x = 1"

    def test_get_nonexistent_request(self, temp_db):
        """Test getting a request that doesn't exist."""
        result = temp_db.get_request("nonexistent")
        assert result is None

    def test_update_request(self, temp_db):
        """Test updating a request."""
        request = DisplayRequest(
            code="y = 2",
            method="jupyter",
        )
        
        temp_db.create_request(request)
        
        # Update status
        updated = temp_db.update_request(
            request.id,
            status="success",
            execution_time=1.5,
        )
        
        assert updated is True
        
        # Retrieve and verify
        retrieved = temp_db.get_request(request.id)
        assert retrieved.status == "success"
        assert retrieved.execution_time == 1.5

    def test_list_requests(self, temp_db):
        """Test listing requests."""
        # Create multiple requests
        for i in range(5):
            request = DisplayRequest(
                code=f"x = {i}",
                name=f"Test {i}",
                method="jupyter",
            )
            temp_db.create_request(request)
        
        # List all
        requests = temp_db.list_requests()
        assert len(requests) == 5
        
        # List with limit
        requests = temp_db.list_requests(limit=3)
        assert len(requests) == 3

    def test_delete_request(self, temp_db):
        """Test deleting a request."""
        request = DisplayRequest(
            code="z = 3",
            method="jupyter",
        )
        
        temp_db.create_request(request)
        
        # Delete
        deleted = temp_db.delete_request(request.id)
        assert deleted is True
        
        # Verify deleted
        retrieved = temp_db.get_request(request.id)
        assert retrieved is None

    def test_search_requests(self, temp_db):
        """Test full-text search."""
        # Create requests with different content
        requests = [
            DisplayRequest(code="import pandas", name="Pandas Test", method="jupyter"),
            DisplayRequest(code="import numpy", name="NumPy Test", method="jupyter"),
            DisplayRequest(code="import matplotlib", name="Plotting", method="jupyter"),
        ]
        
        for req in requests:
            temp_db.create_request(req)
        
        # Search for pandas
        results = temp_db.search_requests("pandas")
        assert len(results) >= 1
        assert any("pandas" in r.code.lower() or "pandas" in r.name.lower() for r in results)
