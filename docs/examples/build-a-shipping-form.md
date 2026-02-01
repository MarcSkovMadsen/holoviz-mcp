# Build a Shipping Form

Build a shipping address form with cascading country, state/province, and city selectors where each dropdown's options dynamically depend on the previous selection, with default country loaded from environment variables.

![Claude Logo](../assets/images/claude-logo.svg)

## Input

Ask Claude Code to create a Param-based shipping form:

```text
Plan how to create a ShippingForm param class with:
- country: selector with at least 3 countries (USA, Canada, Germany)
- state_province: selector whose options depend on the selected country
- city: selector whose options depend on the selected state/province
- street_address: string for the street address
- postal_code: string with format validation (different patterns per country)
- recipient_name: string with minimum 2 characters

Requirements:
- Load the default country from the DEFAULT_COUNTRY environment variable (fallback to "USA")
- When country changes, update state/province options and reset to first valid option
- When state/province changes, update city options and reset to first valid option
- Add postal code validation that varies by country (US: 5 digits, Canada: A1A 1A1 pattern, Germany: 5 digits)
- Include a method to get the full formatted address as a string
- Include a method to validate the complete form and return any errors
- Add proper docstrings and type hints
- Create a simple Panel UI form to fill in the shipping form, submit and display the formatted address
- Catch ValueError during validation and shown them to the user in the UI

Output should be a single Python file app.py. Add tests in test_app.py and make sure all tests pass.
```

!!! tip "Using the Param Skill"
    Claude Code has access to the HoloViz MCP server which includes a **param skill** with best practices for creating Parameterized classes. The skill guides Claude on:

    - Using `@param.depends(watch=True, on_init=True)` for cascading dependent selectors
    - Dynamically updating `param.Selector.objects` when parent selections change
    - Reading environment variables for default values at class definition time
    - Implementing custom parameter types with `_validate_value` for format validation

## Result

Claude leverages the `param` and `panel` skills to create a well-structured `ShippingForm` class with cascading selectors, country-specific validation, and environment-based defaults.

![Shipping Form](../assets/images/examples/shipping-form.gif)

Claude created comprehensive tests covering the validation scenarios:

![Claude Finished Message](../assets/images/examples/shipping-form-claude.png)

<details><summary>Code</summary>

```python
"""ShippingForm - A Param class with cascading selectors and Panel UI form."""

import os
import re

import param
import panel as pn

pn.extension()

# Location data for cascading selectors
LOCATIONS = {
    "USA": {
        "California": ["Los Angeles", "San Francisco", "San Diego"],
        "New York": ["New York City", "Buffalo", "Albany"],
        "Texas": ["Houston", "Austin", "Dallas"],
    },
    "Canada": {
        "Ontario": ["Toronto", "Ottawa", "Hamilton"],
        "Quebec": ["Montreal", "Quebec City", "Laval"],
        "British Columbia": ["Vancouver", "Victoria", "Burnaby"],
    },
    "Germany": {
        "Bavaria": ["Munich", "Nuremberg", "Augsburg"],
        "Berlin": ["Berlin"],
        "Hamburg": ["Hamburg"],
    },
}

# Postal code validation patterns
POSTAL_PATTERNS = {
    "USA": r"^\d{5}$",
    "Canada": r"^[A-Za-z]\d[A-Za-z] \d[A-Za-z]\d$",
    "Germany": r"^\d{5}$",
}

# Default country from environment variable
DEFAULT_COUNTRY = os.environ.get("DEFAULT_COUNTRY", "USA")
if DEFAULT_COUNTRY not in LOCATIONS:
    DEFAULT_COUNTRY = "USA"


class MinLengthString(param.String):
    """A String parameter with minimum length validation."""

    __slots__ = ["min_length"]

    def __init__(self, min_length=0, **params):
        self.min_length = min_length
        super().__init__(**params)

    def _validate_value(self, val, allow_None):
        super()._validate_value(val, allow_None)
        if val and len(val) < self.min_length:
            raise ValueError(
                f"Parameter {self.name!r} must be at least {self.min_length} characters."
            )


class ShippingForm(param.Parameterized):
    """A shipping form with cascading location selectors and validation."""

    country = param.Selector(
        default=DEFAULT_COUNTRY,
        objects=list(LOCATIONS.keys()),
        doc="Shipping country",
    )

    state_province = param.Selector(
        default=None,
        objects=[],
        doc="State or province",
    )

    city = param.Selector(
        default=None,
        objects=[],
        doc="City",
    )

    street_address = param.String(
        default="",
        doc="Street address",
    )

    postal_code = param.String(
        default="",
        doc="Postal/ZIP code",
    )

    recipient_name = MinLengthString(
        default="",
        min_length=2,
        doc="Recipient name (minimum 2 characters)",
    )

    @param.depends("country", watch=True, on_init=True)
    def _update_states(self):
        """Update state/province options when country changes."""
        states = list(LOCATIONS[self.country].keys())
        self.param.state_province.objects = states
        if self.state_province not in states:
            self.state_province = states[0]

    @param.depends("state_province", watch=True, on_init=True)
    def _update_cities(self):
        """Update city options when state/province changes."""
        if self.state_province is None:
            return
        cities = LOCATIONS[self.country][self.state_province]
        self.param.city.objects = cities
        if self.city not in cities:
            self.city = cities[0]

    def validate_postal_code(self):
        """Validate postal code against country-specific pattern.

        Raises:
            ValueError: If postal code doesn't match the expected pattern.
        """
        if not self.postal_code:
            raise ValueError("Postal code is required.")

        pattern = POSTAL_PATTERNS.get(self.country)
        if pattern and not re.match(pattern, self.postal_code):
            if self.country == "USA":
                raise ValueError("USA postal code must be 5 digits (e.g., 12345).")
            elif self.country == "Canada":
                raise ValueError(
                    "Canada postal code must be in format A1A 1A1 (e.g., K1A 0B1)."
                )
            elif self.country == "Germany":
                raise ValueError("Germany postal code must be 5 digits (e.g., 10115).")
            else:
                raise ValueError("Invalid postal code format.")

    def validate(self):
        """Validate all form fields.

        Returns:
            list[str]: List of validation error messages. Empty if valid.
        """
        errors = []

        if not self.recipient_name:
            errors.append("Recipient name is required.")
        elif len(self.recipient_name) < 2:
            errors.append("Recipient name must be at least 2 characters.")

        if not self.street_address:
            errors.append("Street address is required.")

        try:
            self.validate_postal_code()
        except ValueError as e:
            errors.append(str(e))

        return errors

    def formatted_address(self):
        """Return a formatted multi-line address string.

        Returns:
            str: Formatted address.
        """
        lines = [
            self.recipient_name,
            self.street_address,
            f"{self.city}, {self.state_province} {self.postal_code}",
            self.country,
        ]
        return "\n".join(lines)


def create_shipping_form():
    """Create a Panel UI for the shipping form.

    Returns:
        pn.Column: Panel column containing the form UI.
    """
    form = ShippingForm()

    # Create widgets from parameters
    country_widget = pn.widgets.Select.from_param(form.param.country, name="Country")
    state_widget = pn.widgets.Select.from_param(
        form.param.state_province, name="State/Province"
    )
    city_widget = pn.widgets.Select.from_param(form.param.city, name="City")
    street_widget = pn.widgets.TextInput.from_param(
        form.param.street_address, name="Street Address", placeholder="123 Main St"
    )
    postal_widget = pn.widgets.TextInput.from_param(
        form.param.postal_code, name="Postal Code", placeholder="12345"
    )
    name_widget = pn.widgets.TextInput.from_param(
        form.param.recipient_name, name="Recipient Name", placeholder="John Doe"
    )

    # Error display
    error_pane = pn.pane.Alert(visible=False, alert_type="danger")

    # Address display
    address_pane = pn.pane.Markdown("")

    # Submit button
    submit_btn = pn.widgets.Button(name="Submit", button_type="primary")

    def on_submit(event):
        errors = form.validate()
        if errors:
            error_pane.object = "\n".join(errors)
            error_pane.visible = True
            address_pane.object = ""
        else:
            error_pane.visible = False
            address_pane.object = (
                f"**Formatted Address:**\n```\n{form.formatted_address()}\n```"
            )

    submit_btn.on_click(on_submit)

    return pn.Column(
        pn.pane.Markdown("# Shipping Form"),
        pn.pane.Markdown("Please fill in your shipping details:"),
        name_widget,
        street_widget,
        country_widget,
        state_widget,
        city_widget,
        postal_widget,
        submit_btn,
        error_pane,
        address_pane,
        width=400,
    )


# Create the app for Panel serve
app = create_shipping_form()
app.servable()
```

</details>

Key features demonstrated:

- **Cascading Selectors**: Country -> State/Province -> City with `@param.depends(watch=True, on_init=True)`
- **Dynamic Options**: Updates `param.Selector.objects` when parent selection changes
- **Environment Defaults**: Reads `DEFAULT_COUNTRY` from environment variables at class definition
- **Custom Validation**: Country-specific postal code patterns (US: 5 digits, Canada: A1A 1A1, Germany: 5 digits)
- **Custom Parameter Types**: `MinLengthString` for recipient name validation
- **Form Methods**: `get_formatted_address()` and `validate()` for complete form handling
- **Panel Integration**: Reactive UI with automatic placeholder updates
