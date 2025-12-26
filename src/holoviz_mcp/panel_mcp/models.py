"""Pydantic models for Panel component metadata collection.

This module defines the data models used to represent Panel UI component information,
including parameter details, component summaries, and search results.
"""

from __future__ import annotations

from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ParameterInfo(BaseModel):
    """
    Information about a Panel component parameter.

    This model captures parameter metadata including type, default value,
    documentation, and type-specific attributes like bounds or options.
    """

    model_config = ConfigDict(extra="allow")  # Allow additional fields we don't know about

    # Common attributes that most parameters have
    type: str = Field(description="The type of the parameter, e.g., 'Parameter', 'Number', 'Selector'.")
    default: Optional[Any] = Field(default=None, description="The default value for the parameter.")
    doc: Optional[str] = Field(default=None, description="Documentation string for the parameter.")
    # Optional attributes that may not be present
    allow_None: Optional[bool] = Field(default=None, description="Whether the parameter accepts None values.")
    constant: Optional[bool] = Field(default=None, description="Whether the parameter is constant (cannot be changed after initialization).")
    readonly: Optional[bool] = Field(default=None, description="Whether the parameter is read-only.")
    per_instance: Optional[bool] = Field(default=None, description="Whether the parameter is per-instance or shared across instances.")

    # Type-specific attributes (will be present only for relevant parameter types)
    objects: Optional[Any] = Field(default=None, description="Available options for Selector-type parameters.")
    bounds: Optional[Any] = Field(default=None, description="Value bounds for Number-type parameters.")
    regex: Optional[str] = Field(default=None, description="Regular expression pattern for String-type parameters.")


class ComponentSummary(BaseModel):
    """
    High-level information about a Panel UI component.

    This model provides a compact representation of a component without
    detailed parameter information or docstrings. Used for listings and
    quick overviews.
    """

    module_path: str = Field(description="Full module path of the component, e.g., 'panel.widgets.Button' or 'panel_material_ui.Button'.")
    name: str = Field(description="Name of the component, e.g., 'Button' or 'TextInput'.")
    package: str = Field(description="Package name of the component, e.g., 'panel' or 'panel_material_ui'.")
    description: str = Field(description="Short description of the component's purpose and functionality.")


class ComponentSummarySearchResult(ComponentSummary):
    """
    Component summary with search relevance scoring.

    Extends ComponentSummary with a relevance score for search results,
    allowing proper ranking and filtering of search matches.

    """

    relevance_score: int = Field(default=0, description="Relevance score for search results")

    @classmethod
    def from_component(cls, component: ComponentDetails, relevance_score: int) -> ComponentSummarySearchResult:
        """
        Create a search result from a component and relevance score.

        Parameters
        ----------
        component : ComponentDetails
            The component to create a search result from.
        relevance_score : int
            The relevance score (0-100) for this search result.

        Returns
        -------
        ComponentSummarySearchResult
            A search result summary of the component.
        """
        return cls(
            module_path=component.module_path, name=component.name, package=component.package, description=component.description, relevance_score=relevance_score
        )


class ComponentDetails(ComponentSummary):
    """
    Complete information about a Panel UI component.

    This model includes all available information about a component:
    summary information, initialization signature, full docstring,
    and detailed parameter specifications.

    """

    init_signature: str = Field(description="Signature of the component's __init__ method.")
    docstring: str = Field(description="Docstring of the component, providing detailed information about its usage.")
    parameters: dict[str, ParameterInfo] = Field(
        description="Dictionary of parameters for the component, where keys are parameter names and values are ParameterInfo objects."
    )

    def to_base(self) -> ComponentSummary:
        """
        Convert to a basic component summary.

        Strips away detailed information to create a lightweight
        summary suitable for listings and overviews.

        Returns
        -------
        ComponentSummary
            A summary version of this component.
        """
        return ComponentSummary(
            module_path=self.module_path,
            name=self.name,
            package=self.package,
            description=self.description,
        )
