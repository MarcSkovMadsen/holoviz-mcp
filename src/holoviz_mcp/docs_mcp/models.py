"""Data models for the HoloViz Documentation MCP server."""

from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl


class Page(BaseModel):
    """Represents a documentation page in the HoloViz ecosystem."""

    title: str = Field(..., description="The title of the documentation page.")
    url: HttpUrl = Field(..., description="The URL of the documentation page.")
    project: str = Field(..., description="The project to which the documentation page belongs.")
    path: str = Field(..., description="The path to the documentation page within the project.")
    is_reference: bool = Field(..., description="Indicates if the page is a reference guide page.")
    description: Optional[str] = Field(default=None, description="A brief description of the documentation page.")
    content: Optional[str] = Field(default=None, description="The Markdown content of the documentation page, if available.")
    relevance_score: Optional[float] = Field(default=None, description="Relevance score of the page, where 100 is the highest score indicating an exact match.")
