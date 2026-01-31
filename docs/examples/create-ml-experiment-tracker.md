# Create an ML Experiment Tracker

Build a machine learning experiment configuration tracker using Param's declarative parameter system with validation, constraints, and change history tracking.

![Claude Logo](../assets/images/claude-logo.svg)

## Input

Ask Claude Code to create a Param-based ML experiment tracker:

```text
Create an MLExperiment param class with:
- model_name: string parameter
- learning_rate: number constrained to range 0.0001-1.0
- batch_size: integer that must be a power of 2 only (8, 16, 32, 64, etc.)
- epochs: positive integer
- early_stopping: boolean flag
- patience: integer that should only be validated when early_stopping is True

Requirements:
- Track all parameter changes in a history list with timestamps
- Add a method to get the current configuration as a dictionary
- Add a method to reset to default values
- Include proper docstrings and type hints
- Create a simple Panel UI to edit the experiment parameters and view history

Output should be a single Python file app.py. Add tests in test.py and make sure all tests pass.
```

!!! tip "Using the Param Skill"
    Claude Code has access to the HoloViz MCP server which includes a **param skill** with best practices for creating Parameterized classes. The skill guides Claude on:

    - Using appropriate parameter types (`param.String`, `param.Number`, `param.Integer`, etc.)
    - Implementing custom validation with bounds and constraints
    - Setting up parameter dependencies with `@param.depends`
    - Tracking parameter changes with watchers

## Result

Claude leverages the `param` and `panel` skills to create a well-structured `MLExperiment` class with proper validation, conditional logic, and change tracking.

![ML Experiment Tracker](../assets/images/examples/ml-experiment-tracker.png)

Claude even created 25 successful tests:

![Claude Finished Message](../assets/images/examples/ml-experiment-tracker-claude.png)

<details><summary>Code</summary>

```python
# pyright: reportAssignmentType=false
"""
ML Experiment Configuration with Parameter Tracking.

A Param-based class for managing machine learning experiment configurations
with validation, history tracking, and a Panel UI for interactive editing.
"""

from datetime import datetime
from typing import Any

import panel as pn
import param

pn.extension(throttled=True)


# Custom Parameter Types
class PowerOfTwoInteger(param.Integer):
    """Integer parameter that must be a power of 2 (8, 16, 32, 64, etc.)."""

    def __init__(self, default: int = 32, **params):
        super().__init__(default=default, **params)

    def _validate_value(self, val: int | None, allow_None: bool) -> None:
        super()._validate_value(val, allow_None)
        if val is not None and val > 0:
            # Check if val is a power of 2: val & (val - 1) == 0
            if not (val & (val - 1) == 0):
                raise ValueError(f"Parameter {self.name!r} must be a power of 2 (e.g., 8, 16, 32, 64), not {val!r}.")


class MLExperiment(param.Parameterized):
    """
    Machine Learning Experiment Configuration.

    A parameterized class for managing ML experiment settings with automatic
    validation, change tracking, and serialization support.

    Attributes
    ----------
    model_name : str
        Name of the model architecture (e.g., 'ResNet50', 'BERT').
    learning_rate : float
        Learning rate for optimization, constrained to [0.0001, 1.0].
    batch_size : int
        Training batch size, must be a power of 2 (8, 16, 32, 64, etc.).
    epochs : int
        Number of training epochs, must be positive.
    early_stopping : bool
        Whether to enable early stopping during training.
    patience : int
        Number of epochs to wait before early stopping (only validated when early_stopping=True).
    history : list
        List of parameter change records with timestamps.

    Examples
    --------
    >>> exp = MLExperiment(model_name="ResNet50", learning_rate=0.001)
    >>> exp.batch_size = 64
    >>> print(exp.get_config())
    {'model_name': 'ResNet50', 'learning_rate': 0.001, 'batch_size': 64, ...}
    """

    model_name: str = param.String(
        default="ResNet50",
        doc="Name of the model architecture (e.g., 'ResNet50', 'BERT').",
    )

    learning_rate: float = param.Number(
        default=0.001,
        bounds=(0.0001, 1.0),
        step=0.0001,
        doc="Learning rate for optimization, constrained to [0.0001, 1.0].",
    )

    batch_size: int = PowerOfTwoInteger(
        default=32,
        bounds=(1, 1024),
        doc="Training batch size, must be a power of 2 (8, 16, 32, 64, etc.).",
    )

    epochs: int = param.Integer(
        default=10,
        bounds=(1, None),
        doc="Number of training epochs, must be positive.",
    )

    early_stopping: bool = param.Boolean(
        default=False,
        doc="Whether to enable early stopping during training.",
    )

    patience: int = param.Integer(
        default=5,
        bounds=(1, None),
        doc="Number of epochs to wait before early stopping (validated only when early_stopping=True).",
    )

    history: list = param.List(
        default=[],
        item_type=dict,
        doc="List of parameter change records with timestamps.",
    )

    # Store default values for reset functionality
    _defaults: dict = param.Dict(default={}, precedence=-1)

    def __init__(self, **params):
        # Capture defaults before initialization
        defaults = {
            "model_name": params.get("model_name", "ResNet50"),
            "learning_rate": params.get("learning_rate", 0.001),
            "batch_size": params.get("batch_size", 32),
            "epochs": params.get("epochs", 10),
            "early_stopping": params.get("early_stopping", False),
            "patience": params.get("patience", 5),
        }
        super().__init__(**params)
        self._defaults = defaults

    @param.depends("early_stopping", "patience", watch=True, on_init=True)
    def _validate_patience(self) -> None:
        """Validate patience only when early_stopping is enabled."""
        if self.early_stopping and self.patience < 1:
            raise ValueError(f"Parameter 'patience' must be at least 1 when early_stopping is enabled, not {self.patience!r}.")

    @param.depends(
        "model_name",
        "learning_rate",
        "batch_size",
        "epochs",
        "early_stopping",
        "patience",
        watch=True,
    )
    def _track_changes(self) -> None:
        """Track all parameter changes with timestamps."""
        # Get current values
        current_config = self.get_config()

        # Create history entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "config": current_config.copy(),
        }

        # Append to history (create new list to trigger reactivity)
        self.history = self.history + [entry]

    def get_config(self) -> dict[str, Any]:
        """
        Get the current experiment configuration as a dictionary.

        Returns
        -------
        dict[str, Any]
            Dictionary containing all experiment parameters.

        Examples
        --------
        >>> exp = MLExperiment(model_name="BERT", epochs=20)
        >>> config = exp.get_config()
        >>> print(config['model_name'])
        'BERT'
        """
        return {
            "model_name": self.model_name,
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "epochs": self.epochs,
            "early_stopping": self.early_stopping,
            "patience": self.patience,
        }

    def reset(self) -> None:
        """
        Reset all parameters to their default values.

        This resets the experiment configuration to the values it had
        when the instance was created. History is preserved.

        Examples
        --------
        >>> exp = MLExperiment(model_name="ResNet50")
        >>> exp.learning_rate = 0.1
        >>> exp.reset()
        >>> print(exp.learning_rate)
        0.001
        """
        self.param.update(**self._defaults)


class MLExperimentUI(pn.viewable.Viewer):
    """
    Panel UI for editing ML Experiment parameters and viewing history.

    Provides an interactive interface for modifying experiment settings
    and reviewing the change history.

    Parameters
    ----------
    experiment : MLExperiment, optional
        The experiment instance to edit. If not provided, creates a new one.
    """

    experiment: MLExperiment = param.ClassSelector(
        class_=MLExperiment,
        default=None,
        doc="The MLExperiment instance to edit.",
    )

    def __init__(self, experiment: MLExperiment | None = None, **params):
        if experiment is None:
            experiment = MLExperiment()
        super().__init__(experiment=experiment, **params)

        with pn.config.set(sizing_mode="stretch_width"):
            # Create widgets from parameters
            self._model_name_input = pn.widgets.TextInput.from_param(
                self.experiment.param.model_name,
                name="Model Name",
            )

            self._learning_rate_input = pn.widgets.FloatSlider.from_param(
                self.experiment.param.learning_rate,
                name="Learning Rate",
                format="0.0000",
            )

            # Batch size as select for power of 2 values
            self._batch_size_input = pn.widgets.Select.from_param(
                self.experiment.param.batch_size,
                name="Batch Size",
                options=[8, 16, 32, 64, 128, 256, 512, 1024],
            )

            self._epochs_input = pn.widgets.IntSlider.from_param(
                self.experiment.param.epochs,
                name="Epochs",
                start=1,
                end=100,
            )

            self._early_stopping_input = pn.widgets.Checkbox.from_param(
                self.experiment.param.early_stopping,
                name="Early Stopping",
            )

            self._patience_input = pn.widgets.IntSlider.from_param(
                self.experiment.param.patience,
                name="Patience",
                start=1,
                end=50,
            )

            # Reset button
            self._reset_button = pn.widgets.Button(
                name="Reset to Defaults",
                button_type="warning",
            )
            self._reset_button.on_click(self._on_reset_click)

            # Collect inputs
            self._inputs = pn.Column(
                "## Configuration",
                self._model_name_input,
                self._learning_rate_input,
                self._batch_size_input,
                self._epochs_input,
                self._early_stopping_input,
                self._patience_input,
                pn.layout.Divider(),
                self._reset_button,
                max_width=350,
            )

            # Output panes - created once with reactive content
            self._config_pane = pn.pane.JSON(
                self._current_config,
                name="Current Config",
                depth=2,
                sizing_mode="stretch_width",
            )

            self._history_pane = pn.pane.Markdown(
                self._history_display,
                sizing_mode="stretch_width",
            )

            # Collect outputs
            self._outputs = pn.Column(
                "## Current Configuration",
                self._config_pane,
                pn.layout.Divider(),
                "## Change History",
                self._history_pane,
            )

            # Combined layout
            self._panel = pn.Row(
                self._inputs,
                self._outputs,
                sizing_mode="stretch_width",
            )

    def _on_reset_click(self, _event: Any) -> None:
        """Handle reset button click."""
        self.experiment.reset()

    @param.depends(
        "experiment.model_name",
        "experiment.learning_rate",
        "experiment.batch_size",
        "experiment.epochs",
        "experiment.early_stopping",
        "experiment.patience",
    )
    def _current_config(self) -> dict[str, Any]:
        """Return current configuration for JSON pane."""
        return self.experiment.get_config()

    @param.depends("experiment.history")
    def _history_display(self) -> str:
        """Return formatted history for markdown pane."""
        if not self.experiment.history:
            return "*No changes recorded yet.*"

        lines = []
        for i, entry in enumerate(reversed(self.experiment.history[-10:]), 1):
            timestamp = entry["timestamp"]
            config = entry["config"]
            lines.append(f"### Change {len(self.experiment.history) - i + 1}")
            lines.append(f"**Time:** {timestamp}")
            lines.append(f"- Model: `{config['model_name']}`")
            lines.append(f"- LR: `{config['learning_rate']}`")
            lines.append(f"- Batch: `{config['batch_size']}`")
            lines.append(f"- Epochs: `{config['epochs']}`")
            lines.append(f"- Early Stop: `{config['early_stopping']}` (patience: `{config['patience']}`)")
            lines.append("")

        if len(self.experiment.history) > 10:
            lines.insert(0, f"*Showing last 10 of {len(self.experiment.history)} changes.*\n")

        return "\n".join(lines)

    def __panel__(self) -> pn.Row:
        """Return the panel layout for notebook display."""
        return self._panel

    @classmethod
    def create_app(cls, experiment: MLExperiment | None = None) -> pn.template.FastListTemplate:
        """
        Create a servable Panel application.

        Parameters
        ----------
        experiment : MLExperiment, optional
            The experiment instance to edit.

        Returns
        -------
        pn.template.FastListTemplate
            A Panel template ready to be served.
        """
        instance = cls(experiment=experiment)
        template = pn.template.FastListTemplate(
            title="ML Experiment Configuration",
            sidebar=[
                pn.pane.Markdown(
                    "### ML Experiment Tracker\n\nConfigure your machine learning experiment parameters. All changes are automatically tracked with timestamps."
                ),
                instance._inputs,
            ],
            main=[instance._outputs],
            main_layout=None,
        )
        return template


# Serve the app
if pn.state.served:
    MLExperimentUI.create_app().servable()
```

</details>

Key features demonstrated:

- **Parameter Types**: Uses `param.String`, `param.Number`, `param.Integer`, and `param.Boolean`
- **Validation**: Learning rate bounded to 0.0001-1.0, batch size restricted to powers of 2
- **Conditional Logic**: Patience parameter disabled when early_stopping is False
- **Change Tracking**: Automatic history with timestamps via param watchers
- **Panel Integration**: Direct widget binding with `from_param()` for reactive UI
