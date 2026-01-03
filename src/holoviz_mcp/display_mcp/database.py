"""Database models and operations for the display server.

This module handles SQLite database operations for storing and retrieving
visualization requests.
"""

import json
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


class DisplayRequest(BaseModel):
    """Model for a display request stored in the database."""

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


class DisplayDatabase:
    """SQLite database manager for display requests."""

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
                CREATE TABLE IF NOT EXISTS display_requests (
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON display_requests(created_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON display_requests(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_method ON display_requests(method)")

            # Create full-text search virtual table
            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS display_requests_fts
                USING fts5(name, description, code, content=display_requests)
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

    def create_request(self, request: DisplayRequest) -> DisplayRequest:
        """Create a new display request.

        Parameters
        ----------
        request : DisplayRequest
            Request to create

        Returns
        -------
        DisplayRequest
            Created request with ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO display_requests
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
                INSERT INTO display_requests_fts(rowid, name, description, code)
                VALUES ((SELECT rowid FROM display_requests WHERE id = ?), ?, ?, ?)
                """,
                (request.id, request.name, request.description, request.code),
            )

            conn.commit()

        return request

    def get_request(self, request_id: str) -> Optional[DisplayRequest]:
        """Get a display request by ID.

        Parameters
        ----------
        request_id : str
            Request ID

        Returns
        -------
        Optional[DisplayRequest]
            Request if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM display_requests WHERE id = ?", (request_id,))
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
        """Update a display request.

        Parameters
        ----------
        request_id : str
            Request ID
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
                f"UPDATE display_requests SET {', '.join(updates)} WHERE id = ?",
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
    ) -> list[DisplayRequest]:
        """List display requests with filters.

        Parameters
        ----------
        limit : int
            Maximum number of requests to return
        offset : int
            Number of requests to skip
        start : Optional[datetime]
            Filter requests after this time
        end : Optional[datetime]
            Filter requests before this time
        status : Optional[str]
            Filter by status
        method : Optional[str]
            Filter by method

        Returns
        -------
        list[DisplayRequest]
            List of requests
        """
        query = "SELECT * FROM display_requests WHERE 1=1"
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
        """Delete a display request.

        Parameters
        ----------
        request_id : str
            Request ID

        Returns
        -------
        bool
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Delete from FTS index
            cursor.execute(
                "DELETE FROM display_requests_fts WHERE rowid = (SELECT rowid FROM display_requests WHERE id = ?)",
                (request_id,),
            )

            # Delete from main table
            cursor.execute("DELETE FROM display_requests WHERE id = ?", (request_id,))
            conn.commit()

            return cursor.rowcount > 0

    def search_requests(self, query: str, limit: int = 100) -> list[DisplayRequest]:
        """Search requests using full-text search.

        Parameters
        ----------
        query : str
            Search query
        limit : int
            Maximum number of results

        Returns
        -------
        list[DisplayRequest]
            Matching requests
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.* FROM display_requests r
                JOIN display_requests_fts fts ON r.rowid = fts.rowid
                WHERE display_requests_fts MATCH ?
                ORDER BY r.created_at DESC
                LIMIT ?
                """,
                (query, limit),
            )
            rows = cursor.fetchall()

            return [self._row_to_request(dict(row)) for row in rows]

    @staticmethod
    def _row_to_request(row: dict) -> DisplayRequest:
        """Convert a database row to a DisplayRequest."""
        return DisplayRequest(
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
