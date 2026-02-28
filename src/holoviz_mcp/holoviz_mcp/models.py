"""Data models for the HoloViz Documentation MCP server."""

from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl


class DocumentSummary(BaseModel):
    """Summary of a document (used by doc_list)."""

    source_path: str = Field(..., description="The path to the document within the project.")
    title: str = Field(..., description="The title of the document.")
    is_reference: bool = Field(..., description="Indicates if the document is a reference guide.")


class Document(BaseModel):
    """Represents a document."""

    title: str = Field(..., description="The title of the document.")
    url: HttpUrl = Field(..., description="The URL of the rendered, target document.")
    project: str = Field(..., description="The project to which the document belongs.")
    source_path: str = Field(..., description="The path to the document within the project.")
    source_url: HttpUrl = Field(..., description="The URL to the source document.")
    is_reference: bool = Field(..., description="Indicates if the document is a reference guide.")
    description: Optional[str] = Field(default=None, description="A brief description of the document.")
    content: Optional[str] = Field(default=None, description="The content of the documentation, if available. In Markdown format if possible.")
    relevance_score: Optional[float] = Field(default=None, description="Relevance score of the document, where 1 is the highest score indicating an exact match.")

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override to exclude None values by default, saving tokens."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)
