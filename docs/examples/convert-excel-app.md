# Convert an Excel Spreadsheet

Upload an Excel spreadsheet and ask Claude Code to recreate it using Panel!

![Claude Logo](../assets/images/claude-logo.svg)

## Input

Download the file [stock_portfolio.xlsx](../assets/data/stock_portfolio.xlsx) and save it to your *current working directory*.

[![Excel Image](../assets/images/examples/convert-excel-app-image.png)](../assets/data/stock_portfolio.xlsx)

Ask Claude Code to create a plan:

```text
Please plan how to convert the attached Excel spreadsheet (stock_portfolio.xlsx) into an interactive Panel application.

Requirements:
- Create an editable Tabulator table widget for the stock data
  - Allow users to manually edit input cells (stock quantities, purchase prices)
- Create a separate Tabulator table widget for the portfolio totals
- Automatically recalculate dependent cells (total values, portfolio totals) when inputs change
- Match the visual formatting from the Excel sheet including:
  - Column alignment (left/right/center)
  - Number formatting (currency, decimals)
  - Cell styling (colors, fonts, borders)

Technical implementation:
- Ensure data validation for numeric inputs
- Preserve the Excel sheet's layout and structure
- Make the app responsive, professionally and user-friendly

Output should be a single Python file app.py and passing tests in test_app.py.
```

Ask Claude to implement the plan.

!!! Note "Installing the Dependencies"
    I had to help Claude install the dependencies and keep pandas<3

    ```bash
    pip install panel watchfiles pandas
    ```

## Result

The result is a solid foundation that can be further refined as needed.

![Panel Excel App](../assets/images/examples/convert-excel-app.gif)

<details><summary>Code</summary>

```python
"""
Stock Portfolio Tracker - Panel Application

Interactive dashboard for tracking stock portfolio with automatic calculations.
"""

import pandas as pd
import panel as pn
from bokeh.models.widgets.tables import NumberFormatter

# Initialize Panel
pn.extension('tabulator')


# ============================================================================
# 1. DATA LOADING
# ============================================================================

def load_data():
    """Load stock data from Excel file or create initial DataFrame."""
    try:
        # Load the Excel file
        df = pd.read_excel('stock_portfolio.xlsx', header=0)

        # Keep only the first 5 rows (stock data)
        df = df.iloc[:5].copy()

        # Ensure all input columns are numeric
        numeric_cols = ['Shares Owned', 'Purchase Price', 'Current Price']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        # Initialize calculated columns if they don't exist or are NaN
        df['Total Cost'] = 0.0
        df['Current Value'] = 0.0
        df['Gain/Loss $'] = 0.0
        df['Gain/Loss %'] = 0.0

        # Ensure proper column order
        df = df[['Ticker', 'Company Name', 'Shares Owned', 'Purchase Price',
                 'Current Price', 'Total Cost', 'Current Value', 'Gain/Loss $', 'Gain/Loss %']]

        # IMPORTANT: Make all numeric columns writeable for Bokeh/Panel
        # Newer Pandas versions create read-only arrays by default
        # Note: StringArray doesn't have flags attribute, so skip string columns
        for col in df.columns:
            if df[col].dtype.kind in ['f', 'i']:  # float or integer types
                arr = df[col].values
                if hasattr(arr, 'flags'):
                    arr.flags.writeable = True

        # Calculate all derived values initially
        recalculate_all(df)

        return df

    except FileNotFoundError:
        # Create default data if file not found
        df = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'],
            'Company Name': ['Apple Inc.', 'Microsoft Corp.', 'Alphabet Inc.',
                            'Tesla Inc.', 'Amazon.com Inc.'],
            'Shares Owned': [50.0, 30.0, 25.0, 40.0, 15.0],
            'Purchase Price': [150.0, 300.0, 120.0, 200.0, 140.0],
            'Current Price': [175.0, 380.0, 145.0, 185.0, 160.0],
            'Total Cost': [0.0, 0.0, 0.0, 0.0, 0.0],
            'Current Value': [0.0, 0.0, 0.0, 0.0, 0.0],
            'Gain/Loss $': [0.0, 0.0, 0.0, 0.0, 0.0],
            'Gain/Loss %': [0.0, 0.0, 0.0, 0.0, 0.0],
        })

        # IMPORTANT: Make all numeric columns writeable for Bokeh/Panel
        for col in df.columns:
            if df[col].dtype.kind in ['f', 'i']:  # float or integer types
                arr = df[col].values
                if hasattr(arr, 'flags'):
                    arr.flags.writeable = True

        recalculate_all(df)
        return df


# ============================================================================
# 2. CALCULATION FUNCTIONS
# ============================================================================

def calculate_derived_values(df, row_idx):
    """
    Calculate derived values for a single row.

    Args:
        df: DataFrame containing stock data
        row_idx: Row index to calculate (0-based)

    Returns:
        Dictionary of patches for Tabulator: {'Column': [(row_idx, value)], ...}
    """
    # Get input values
    shares = df.at[row_idx, 'Shares Owned']
    purchase_price = df.at[row_idx, 'Purchase Price']
    current_price = df.at[row_idx, 'Current Price']

    # Handle NaN values
    shares = 0.0 if pd.isna(shares) else float(shares)
    purchase_price = 0.0 if pd.isna(purchase_price) else float(purchase_price)
    current_price = 0.0 if pd.isna(current_price) else float(current_price)

    # Calculate derived values
    total_cost = shares * purchase_price
    current_value = shares * current_price
    gain_loss_dollar = current_value - total_cost

    # Calculate percentage (handle division by zero)
    if total_cost != 0:
        gain_loss_pct = gain_loss_dollar / total_cost
    else:
        gain_loss_pct = 0.0

    # Update DataFrame
    df.at[row_idx, 'Total Cost'] = total_cost
    df.at[row_idx, 'Current Value'] = current_value
    df.at[row_idx, 'Gain/Loss $'] = gain_loss_dollar
    df.at[row_idx, 'Gain/Loss %'] = gain_loss_pct

    # Create patch dictionary for Tabulator
    patches = {
        'Total Cost': [(row_idx, total_cost)],
        'Current Value': [(row_idx, current_value)],
        'Gain/Loss $': [(row_idx, gain_loss_dollar)],
        'Gain/Loss %': [(row_idx, gain_loss_pct)],
    }

    return patches


def calculate_summaries(df):
    """
    Calculate portfolio summary totals.

    Args:
        df: DataFrame containing stock data

    Returns:
        DataFrame with summary metrics
    """
    # Calculate totals
    total_investment = df['Total Cost'].sum()
    current_portfolio_value = df['Current Value'].sum()
    total_gain_loss = current_portfolio_value - total_investment

    # Calculate total return percentage (handle division by zero)
    if total_investment != 0:
        total_return_pct = (total_gain_loss / total_investment) * 100
        total_return_str = f"{total_return_pct:.2f}%"
    else:
        total_return_str = "0.00%"

    # Create summary DataFrame
    summary_df = pd.DataFrame({
        'Metric': [
            'Total Investment',
            'Current Portfolio Value',
            'Total Gain/Loss $',
            'Total Return %'
        ],
        'Value': [
            total_investment,
            current_portfolio_value,
            total_gain_loss,
            total_return_str  # String for last row
        ]
    })

    return summary_df


def recalculate_all(df):
    """
    Recalculate all derived columns for the entire DataFrame.

    Args:
        df: DataFrame containing stock data (modified in place)
    """
    for idx in range(len(df)):
        # Get input values
        shares = df.at[idx, 'Shares Owned']
        purchase_price = df.at[idx, 'Purchase Price']
        current_price = df.at[idx, 'Current Price']

        # Handle NaN values
        shares = 0.0 if pd.isna(shares) else float(shares)
        purchase_price = 0.0 if pd.isna(purchase_price) else float(purchase_price)
        current_price = 0.0 if pd.isna(current_price) else float(current_price)

        # Calculate derived values
        total_cost = shares * purchase_price
        current_value = shares * current_price
        gain_loss_dollar = current_value - total_cost

        # Calculate percentage (handle division by zero)
        if total_cost != 0:
            gain_loss_pct = gain_loss_dollar / total_cost
        else:
            gain_loss_pct = 0.0

        # Update DataFrame
        df.at[idx, 'Total Cost'] = total_cost
        df.at[idx, 'Current Value'] = current_value
        df.at[idx, 'Gain/Loss $'] = gain_loss_dollar
        df.at[idx, 'Gain/Loss %'] = gain_loss_pct


def validate_input(value, column):
    """
    Validate user input for numeric columns.

    Args:
        value: Input value to validate
        column: Column name

    Returns:
        Tuple of (is_valid: bool, validated_value_or_error_msg)
    """
    # Text columns are always valid
    if column in ['Ticker', 'Company Name']:
        return True, value

    # Numeric columns need validation
    if column in ['Shares Owned', 'Purchase Price', 'Current Price']:
        try:
            val = float(value)
            if val < 0:
                return False, "Value cannot be negative"
            return True, val
        except (ValueError, TypeError):
            return False, "Must be a number"

    # Default: accept value as-is
    return True, value


# ============================================================================
# 3. CONFIGURE FORMATTERS AND ALIGNMENT
# ============================================================================

formatters = {
    'Purchase Price': NumberFormatter(format='$0,0.00'),
    'Current Price': NumberFormatter(format='$0,0.00'),
    'Total Cost': NumberFormatter(format='$0,0.00'),
    'Current Value': NumberFormatter(format='$0,0.00'),
    'Gain/Loss $': NumberFormatter(format='$0,0.00'),
    'Gain/Loss %': NumberFormatter(format='0.00%'),
}

text_align = {
    'Ticker': 'left',
    'Company Name': 'left',
    'Shares Owned': 'right',
    'Purchase Price': 'right',
    'Current Price': 'right',
    'Total Cost': 'right',
    'Current Value': 'right',
    'Gain/Loss $': 'right',
    'Gain/Loss %': 'right',
}

header_align = {col: 'center' for col in text_align.keys()}


# ============================================================================
# 4. CREATE WIDGETS
# ============================================================================

# Load data
df = load_data()

# Configuration for Tabulator columns
configuration = {
    'columns': [
        {'field': 'Ticker', 'editor': 'input'},
        {'field': 'Company Name', 'editor': 'input'},
        {'field': 'Shares Owned', 'editor': 'number', 'editorParams': {'min': 0}},
        {'field': 'Purchase Price', 'editor': 'number', 'editorParams': {'min': 0, 'step': 0.01}},
        {'field': 'Current Price', 'editor': 'number', 'editorParams': {'min': 0, 'step': 0.01}},
        {'field': 'Total Cost', 'editor': False},  # Not editable
        {'field': 'Current Value', 'editor': False},  # Not editable
        {'field': 'Gain/Loss $', 'editor': False},  # Not editable
        {'field': 'Gain/Loss %', 'editor': False},  # Not editable
    ]
}

# Create main Tabulator widget
main_table = pn.widgets.Tabulator(
    df,
    formatters=formatters,
    text_align=text_align,
    header_align=header_align,
    disabled=False,  # Enable editing
    configuration=configuration,
    frozen_columns=['Ticker'],  # Keep ticker visible when scrolling
    show_index=False,
    sizing_mode='stretch_width',
    height=250,
    layout='fit_columns',
    sortable=False,
)

# Create summary Tabulator widget
summary_df = calculate_summaries(df)

summary_table = pn.widgets.Tabulator(
    summary_df,
    formatters={
        'Value': NumberFormatter(format='$0,0.00')
    },
    text_align={
        'Metric': 'left',
        'Value': 'right'
    },
    header_align={
        'Metric': 'center',
        'Value': 'center'
    },
    disabled=True,  # Read-only
    show_index=False,
    sizing_mode='stretch_width',
    height=200,
    selectable=False,
    sortable=False,
)


# ============================================================================
# 5. DEFINE CALLBACK
# ============================================================================

def on_table_edit(event):
    """
    Handle cell edits in the main table.

    Triggered when user edits a cell. Validates input, recalculates derived
    values, and updates both tables.
    """
    # Extract event information
    column = event.column
    row_idx = event.row
    new_value = event.value

    # Validate input
    is_valid, validated_value = validate_input(new_value, column)
    if not is_valid:
        # Optionally show notification (requires pn.state.notifications)
        print(f"Invalid input: {validated_value}")
        # Revert to old value by not updating
        return

    # Update source DataFrame
    df.at[row_idx, column] = validated_value

    # Recalculate derived values for this row
    calculate_derived_values(df, row_idx)

    # Create a fresh copy of the DataFrame to avoid Bokeh read-only issues
    # This triggers a full table refresh instead of trying to patch
    main_table.value = df.copy()

    # Recalculate and update summary table
    new_summary = calculate_summaries(df)
    summary_table.value = new_summary


# Attach callback to main table
main_table.on_edit(on_table_edit)


# ============================================================================
# 6. APPLY CUSTOM CSS
# ============================================================================

custom_css = """
.tabulator .tabulator-header {
    background-color: #D3D3D3 !important;
    font-weight: bold;
    border: 1px solid black;
}
.tabulator .tabulator-header .tabulator-col {
    background-color: #D3D3D3 !important;
    border-right: 1px solid black;
}
.tabulator .tabulator-cell {
    border: 1px solid #ddd;
}
.tabulator .tabulator-row {
    border-bottom: 1px solid #ddd;
}
"""

main_table.stylesheets = [custom_css]
summary_table.stylesheets = [custom_css]


# ============================================================================
# 7. CREATE LAYOUT
# ============================================================================

app = pn.Column(
    pn.pane.Markdown("# Stock Portfolio Tracker", sizing_mode='stretch_width'),
    pn.pane.Markdown(
        "**Instructions:** Edit the Ticker, Company Name, Shares Owned, Purchase Price, "
        "or Current Price columns. Calculated fields will update automatically.",
        sizing_mode='stretch_width'
    ),
    main_table,
    pn.layout.Divider(),
    pn.pane.Markdown("### Portfolio Summary", sizing_mode='stretch_width'),
    summary_table,
    sizing_mode='stretch_width',
    max_width=1200,
    margin=(20, 20),
)

# Make the app servable
app.servable()
```

</details>

Claude is happy:

![Claude Complete Message](../assets/images/examples/convert-excel-app-claude-complete.png)
