"""Pydantic models for MaterialComponent metadata collection."""

from __future__ import annotations

from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ParameterInfo(BaseModel):
    """Model for parameter attribute information."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields we don't know about

    # Common attributes that most parameters have
    type: str
    default: Optional[Any] = None
    doc: Optional[str] = None
    allow_None: Optional[bool] = None
    constant: Optional[bool] = None
    readonly: Optional[bool] = None
    per_instance: Optional[bool] = None

    # Type-specific attributes (will be present only for relevant parameter types)
    objects: Optional[Any] = None  # For Selector parameters
    bounds: Optional[Any] = None  # For Number parameters
    regex: Optional[str] = None  # For String parameters


class ComponentBase(BaseModel):
    """Base model for component summary information."""

    module_path: str = Field(description="Full module path of the component, e.g., 'panel.widgets.Button' or 'panel_material_ui.Button'.")
    name: str = Field(description="Name of the component, e.g., 'Button' or 'TextInput'.")
    package: str = Field(description="Package name of the component, e.g., 'panel' or 'panel_material_ui'.")
    description: str = Field(description="Short description of the component's purpose and functionality.")


class ComponentBaseSearchResult(ComponentBase):
    """Component Search Result."""

    relevance_score: int = Field(default=0, description="Relevance score for search results")

    @classmethod
    def from_component(cls, component: Component, relevance_score: int) -> ComponentBaseSearchResult:
        """
        Create a ComponentBaseSearchResult from a Component and a relevance score.

        Args:
            component (Component): The Component to convert.
            relevance_score (int): The relevance score for search results.

        Returns
        -------
            ComponentBaseSearchResult: A search result summary of the component.
        """
        return cls(
            module_path=component.module_path, name=component.name, package=component.package, description=component.description, relevance_score=relevance_score
        )


class Component(ComponentBase):
    """Model for full info of MaterialComponent information."""

    init_signature: str = Field(description="Signature of the component's __init__ method.")
    docstring: str = Field(description="Docstring of the component, providing detailed information about its usage.")
    parameters: dict[str, ParameterInfo] = Field(
        description="Dictionary of parameters for the component, where keys are parameter names and values are ParameterInfo objects."
    )

    def to_base(self) -> ComponentBase:
        """
        Convert this ComponentInfo to a ComponentSummary.

        Returns
        -------
            ComponentSummary: A summary of the component.
        """
        return ComponentBase(
            module_path=self.module_path,
            name=self.name,
            package=self.package,
            description=self.description,
        )
