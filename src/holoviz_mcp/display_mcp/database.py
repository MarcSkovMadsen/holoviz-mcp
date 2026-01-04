"""Database models and operations for the display server.

This module handles SQLite database operations for storing and retrieving
visualization requests.
"""

import ast
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator
from typing import Literal
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class Snippet(BaseModel):
    """Model for a code snippet stored in the database.

    Represents a code snippet submitted to the Display System for visualization.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str = Field(..., description="Python code to execute")
    name: str = Field(default="", description="User-provided name")
    description: str = Field(default="", description="User-provided description")
    method: Literal["jupyter", "panel"] = Field(..., description="Execution method")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["pending", "success", "error"] = Field(default="pending")
    error_message: Optional[str] = Field(default=None, description="Error details if status='error'")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")
    packages: list[str] = Field(default_factory=list, description="Inferred required packages")
    extensions: list[str] = Field(default_factory=list, description="Inferred Panel extensions")


class SnippetDatabase:
    """SQLite database manager for code snippets.

    Manages storage and retrieval of Snippet records (code snippets)
    submitted to the Display System.
    """

    def __init__(self, db_path: Path):
        """Initialize the database.

        Parameters
        ----------
        db_path : Path
            Path to the SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create main table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS snippets (
                    id TEXT PRIMARY KEY,
                    code TEXT NOT NULL,
                    name TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    method TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    execution_time REAL,
                    packages TEXT,
                    extensions TEXT
                )
                """
            )

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON snippets(created_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON snippets(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_method ON snippets(method)")

            # Create full-text search virtual table
            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS snippets_fts
                USING fts5(name, description, code, content=snippets)
                """
            )

            conn.commit()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def create_request(self, request: Snippet) -> Snippet:
        """Create a new snippet record.

        Parameters
        ----------
        request : Snippet
            Snippet record to create

        Returns
        -------
        Snippet
            Created snippet record with ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO snippets
                (id, code, name, description, method, created_at, updated_at, status,
                 error_message, execution_time, packages, extensions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.id,
                    request.code,
                    request.name,
                    request.description,
                    request.method,
                    request.created_at.isoformat(),
                    request.updated_at.isoformat(),
                    request.status,
                    request.error_message,
                    request.execution_time,
                    json.dumps(request.packages),
                    json.dumps(request.extensions),
                ),
            )

            # Update FTS index
            cursor.execute(
                """
                INSERT INTO snippets_fts(rowid, name, description, code)
                VALUES ((SELECT rowid FROM snippets WHERE id = ?), ?, ?, ?)
                """,
                (request.id, request.name, request.description, request.code),
            )

            conn.commit()

        return request

    def get_request(self, request_id: str) -> Optional[Snippet]:
        """Get a snippet record by ID.

        Parameters
        ----------
        request_id : str
            Snippet ID

        Returns
        -------
        Optional[Snippet]
            Snippet record if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM snippets WHERE id = ?", (request_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_request(dict(row))
            return None

    def update_request(
        self,
        request_id: str,
        status: Optional[str] = None,
        error_message: Optional[str] = None,
        execution_time: Optional[float] = None,
        packages: Optional[list[str]] = None,
        extensions: Optional[list[str]] = None,
    ) -> bool:
        """Update a snippet record.

        Parameters
        ----------
        request_id : str
            Snippet ID
        status : Optional[str]
            New status
        error_message : Optional[str]
            Error message
        execution_time : Optional[float]
            Execution time
        packages : Optional[list[str]]
            Required packages
        extensions : Optional[list[str]]
            Required extensions

        Returns
        -------
        bool
            True if updated, False if not found
        """
        updates = []
        params = []

        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        if execution_time is not None:
            updates.append("execution_time = ?")
            params.append(str(execution_time))

        if packages is not None:
            updates.append("packages = ?")
            params.append(json.dumps(packages))

        if extensions is not None:
            updates.append("extensions = ?")
            params.append(json.dumps(extensions))

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())

        params.append(request_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE snippets SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_requests(
        self,
        limit: int = 100,
        offset: int = 0,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        status: Optional[str] = None,
        method: Optional[str] = None,
    ) -> list[Snippet]:
        """List snippet records with filters.

        Parameters
        ----------
        limit : int
            Maximum number of snippets to return
        offset : int
            Number of snippets to skip
        start : Optional[datetime]
            Filter snippets created after this time
        end : Optional[datetime]
            Filter snippets created before this time
        status : Optional[str]
            Filter by status
        method : Optional[str]
            Filter by method

        Returns
        -------
        list[Snippet]
            List of snippet records
        """
        query = "SELECT * FROM snippets WHERE 1=1"
        params = []

        if start:
            query += " AND created_at >= ?"
            params.append(start.isoformat())

        if end:
            query += " AND created_at <= ?"
            params.append(end.isoformat())

        if status:
            query += " AND status = ?"
            params.append(status)

        if method:
            query += " AND method = ?"
            params.append(method)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([str(limit), str(offset)])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_request(dict(row)) for row in rows]

    def delete_request(self, request_id: str) -> bool:
        """Delete a snippet record.

        Parameters
        ----------
        request_id : str
            Snippet ID

        Returns
        -------
        bool
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Delete from FTS index
            cursor.execute(
                "DELETE FROM snippets_fts WHERE rowid = (SELECT rowid FROM snippets WHERE id = ?)",
                (request_id,),
            )

            # Delete from main table
            cursor.execute("DELETE FROM snippets WHERE id = ?", (request_id,))
            conn.commit()

            return cursor.rowcount > 0

    def search_requests(self, query: str, limit: int = 100) -> list[Snippet]:
        """Search snippet records using full-text search.

        Parameters
        ----------
        query : str
            Search query
        limit : int
            Maximum number of results

        Returns
        -------
        list[Snippet]
            Matching snippet records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.* FROM snippets r
                JOIN snippets_fts fts ON r.rowid = fts.rowid
                WHERE snippets_fts MATCH ?
                ORDER BY r.created_at DESC
                LIMIT ?
                """,
                (query, limit),
            )
            rows = cursor.fetchall()

            return [self._row_to_request(dict(row)) for row in rows]

    def create_visualization(
        self,
        code: str,
        name: str = "",
        description: str = "",
        method: Literal["jupyter", "panel"] = "jupyter",
    ) -> dict[str, str]:
        """Create a visualization request.

        This is the core business logic for creating visualizations,
        shared by both the HTTP API endpoint and the UI form.

        Parameters
        ----------
        code : str
            Python code to execute
        name : str, optional
            Display name for the visualization
        description : str, optional
            Description of the visualization
        method : str, optional
            Execution method: "jupyter" or "panel"

        Returns
        -------
        dict[str, str]
            Dictionary with 'id', 'url', and 'created_at' keys

        Raises
        ------
        ValueError
            If code is empty or contains unsupported operations
        SyntaxError
            If code has syntax errors
        Exception
            If database operation or other errors occur
        """
        # Import here to avoid circular dependency
        from holoviz_mcp.display_mcp.utils import find_extensions
        from holoviz_mcp.display_mcp.utils import find_requirements
        from holoviz_mcp.display_mcp.utils import get_url

        # Validate code is not empty
        if not code:
            raise ValueError("Code is required")
        if ".show(" in code:
            raise ValueError("`.show()` calls are not supported in this environment")

        # Validate syntax
        ast.parse(code)  # Raises SyntaxError if invalid

        # Infer requirements and extensions
        packages = find_requirements(code)
        extensions = find_extensions(code) if method == "jupyter" else []

        # Create request in database with "pending" status
        request_obj = Snippet(
            code=code,
            name=name,
            description=description,
            method=method,
            packages=packages,
            extensions=extensions,
            status="pending",
        )

        self.create_request(request_obj)

        # Generate URL
        url = get_url(id=request_obj.id)

        # Return result
        return {
            "id": request_obj.id,
            "url": url,
            "created_at": request_obj.created_at.isoformat(),
        }

    @staticmethod
    def _row_to_request(row: dict) -> Snippet:
        """Convert a database row to a Snippet."""
        return Snippet(
            id=row["id"],
            code=row["code"],
            name=row["name"] or "",
            description=row["description"] or "",
            method=row["method"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            status=row["status"],
            error_message=row["error_message"],
            execution_time=row["execution_time"],
            packages=json.loads(row["packages"]) if row["packages"] else [],
            extensions=json.loads(row["extensions"]) if row["extensions"] else [],
        )


# Global database instance cache
_db_instance: Optional[SnippetDatabase] = None


def get_db(db_path: Optional[Path] = None) -> SnippetDatabase:
    """Get or create the SnippetDatabase instance.

    This function implements lazy initialization with a global cache.
    The database instance is created once and reused across the application.

    Parameters
    ----------
    db_path : Optional[Path]
        Path to database file. If None, uses default from environment/config.
        Only used on first call; subsequent calls ignore this parameter.

    Returns
    -------
    SnippetDatabase
        Shared database instance
    """
    global _db_instance

    if _db_instance is None:
        if db_path is None:
            # Try environment variable first
            env_path = os.getenv("DISPLAY_DB_PATH", "")

            if env_path:
                db_path = Path(env_path)
            else:
                # Fall back to default location
                db_path = Path.home() / ".holoviz-mcp" / "snippets" / "snippets.db"

        _db_instance = SnippetDatabase(db_path)

    return _db_instance


def reset_db() -> None:
    """Reset the database instance.

    This is primarily for testing purposes to ensure a clean state.
    """
    global _db_instance
    _db_instance = None
