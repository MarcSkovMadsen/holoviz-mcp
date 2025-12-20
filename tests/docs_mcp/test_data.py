from pathlib import Path

import pytest
from pydantic import AnyHttpUrl

from holoviz_mcp.config import GitRepository
from holoviz_mcp.holoviz_mcp.data import DocumentationIndexer
from holoviz_mcp.holoviz_mcp.data import convert_path_to_url


def is_reference_path(relative_path: Path) -> bool:
    """Check if the path is a reference document (simple fallback logic)."""
    return "reference" in relative_path.parts


EXAMPLES = [
    ("examples/reference/widgets/Button.ipynb", "reference/widgets/Button.html", True),
    ("doc/reference/tabular/area.ipynb", "reference/tabular/area.html", True),
    ("doc/tutorials/getting_started.ipynb", "tutorials/getting_started.html", False),
    ("doc/how_to/best_practices/dev_experience.md", "how_to/best_practices/dev_experience.html", False),
    ("doc/reference/xarray/bar.ipynb", "reference/xarray/bar.html", True),
]


@pytest.mark.parametrize(["relative_path", "expected_url", "expected_is_reference"], EXAMPLES)
def test_convert_path_to_url(relative_path, expected_url, expected_is_reference):
    url = convert_path_to_url(Path(relative_path))
    assert url == expected_url
    assert is_reference_path(Path(relative_path)) == expected_is_reference


def test_convert_path_to_url_plotly():
    url = convert_path_to_url(Path("/doc/python/3d-axes.md"), url_transform="plotly")
    assert url == "doc/python/3d-axes/"


def test_convert_index_path_to_url_plotly():
    url = convert_path_to_url(Path("docs/index.md"), url_transform="plotly")
    assert url == "/"


def test_convert_path_to_url_datashader():
    url = convert_path_to_url(Path("/examples/user_guide/10_Performance.ipynb"), url_transform="datashader")
    assert url == "examples/user_guide/Performance.html"


def test_convert_path_to_url_holoviz():
    url = convert_path_to_url(Path("examples/user_guide/10-Indexing_and_Selecting_Data.ipynb"), url_transform="datashader")
    assert url == "user_guide/Indexing_and_Selecting_Data.html"


# https://github.com/holoviz/panel/blob/main/examples/reference/layouts/Card.ipynb
panel_card = """
```python
import panel as pn
pn.extension()
```

The Card layout allows arranging multiple Panel objects in a collapsible, vertical container with a header bar. It has a list-like API with methods for interactively updating and modifying the layout, including append, extend, clear, insert, pop, remove and __setitem__ (for replacing the card's contents).

Card components are very helpful for laying out components in a grid in a complex dashboard to make clear visual separations between different sections. The ability to collapse them can also be very useful to save space on a page with a lot of components.

**Parameters:**

- collapsed (bool): Whether the Card is collapsed.
- collapsible (bool): Whether the Card can be expanded and collapsed.
- header (Viewable): A Panel component to display in the header bar of the Card.
- hide_header (bool): Whether to hide the Card header.
- objects (list): The list of objects to display in the Card, which will be formatted like a Column. Should not generally be modified directly except when replaced in its entirety.
- title (str): The title to display in the header bar if no explicit header is defined.
"""  # noqa: E501

# https://raw.githubusercontent.com/holoviz/panel/refs/heads/main/doc/how_to/editor/markdown.md
panel_markdown = """
# Write apps in Markdown

This guide addresses how to write Panel apps inside Markdown files.

---

Panel applications can be written as Python scripts (`.py`), notebooks (`.ipynb`) and also Markdown files (`.md`). This is particularly useful when writing applications that serve both as documentation and as an application, e.g. when writing a demo.

To begin simply create a Markdown file with the `.md` file extension, e.g. `app.md`. Once created give your app a title:

```markdown
# My App
```

Before adding any actual content add a code block with any imports your application needs. The code block should have one of two type declarations, either `python` or `{pyodide}`. The latter is useful if you also want to use [the Sphinx Pyodide integration](../wasm/sphinx). In this case we will simply declare a `python` code block that imports Panel and calls the extension with a specific template:

````markdown
```python
import panel as pn

pn.extension(template='fast')
```
````

Once we have initialized the extension any subsequent Markdown will be rendered as part of the application, e.g. we can put some description in our application. If you also want to render some Python code without having Panel interpret it as code, use `.py` as the language declaration:

````markdown
This application provides a minimal example demonstrating how to write an app in a Markdown file.

```.py
widget = pn.widgets.TextInput(value='world')

def hello_world(text):
    return f'Hello {text}!'

pn.Row(widget, pn.bind(hello_world, widget)).servable()
```
````
"""  # noqa: E501

dot_plots = """
---
jupyter:
  jupytext:
    notebook_metadata_filter: all
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.2'
      jupytext_version: 1.4.2
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
  language_info:
    codemirror_mode:
      name: ipython
      version: 3
    file_extension: .py
    mimetype: text/x-python
    name: python
    nbconvert_exporter: python
    pygments_lexer: ipython3
    version: 3.7.7
  plotly:
    description: How to make dot plots in Python with Plotly.
    display_as: basic
    language: python
    layout: base
    name: Dot Plots
    order: 6
    page_type: u-guide
    permalink: python/dot-plots/
    thumbnail: thumbnail/dot-plot.jpg
---

#### Basic Dot Plot

Dot plots (also known as [Cleveland dot plots](<https://en.wikipedia.org/wiki/Dot_plot_(statistics)>)) are [scatter plots](https://plotly.com/python/line-and-scatter/) with one categorical axis and one continuous axis. They can be used to show changes between two (or more) points in time or between two (or more) conditions. Compared to a [bar chart](/python/bar-charts/), dot plots can be less cluttered and allow for an easier comparison between conditions.

For the same data, we show below how to create a dot plot using either `px.scatter` or `go.Scatter`.

[Plotly Express](/python/plotly-express/) is the easy-to-use, high-level interface to Plotly, which [operates on a variety of types of data](/python/px-arguments/) and produces [easy-to-style figures](/python/styling-plotly-express/).

```python
import plotly.express as px
df = px.data.medals_long()

fig = px.scatter(df, y="nation", x="count", color="medal", symbol="medal")
fig.update_traces(marker_size=10)
fig.show()
```

...

```python
# Use column names of df for the different parameters x, y, color, ...
```
"""  # noqa: E501


def test_extract_description_from_markdown():
    indexer = DocumentationIndexer()

    assert (
        indexer._extract_description_from_markdown(panel_card, max_length=100)
        == "The Card layout allows arranging multiple Panel objects in a collapsible, vertical container with a ..."
    )

    assert (
        indexer._extract_description_from_markdown(panel_markdown, max_length=100)
        == "This guide addresses how to write Panel apps inside Markdown files. Panel applications can be ..."
    )

    assert indexer._extract_description_from_markdown(dot_plots, max_length=100) == "Dot plots (also known as [Cleveland dot ..."


@pytest.mark.parametrize(
    "content,filename,expected",
    [
        (panel_card, "Card.ipynb", "Card"),
        (panel_markdown, "Markdown.ipynb", "Write apps in Markdown"),
        (dot_plots, "dot-plots.md", "Dot Plots"),
    ],
)
def test_extract_title_from_markdown(content, filename, expected):
    indexer = DocumentationIndexer()

    assert indexer._extract_title_from_markdown(content, filename) == expected


def test_to_title():
    path = "examples/tutorial/02_Plotting.ipynb"
    indexer = DocumentationIndexer
    assert indexer._to_title(path) == "Plotting"


def test_to_source_url_github():
    repo_config = GitRepository(url=AnyHttpUrl("https://github.com/holoviz/panel.git"), base_url=AnyHttpUrl("https://panel.holoviz.org/"))
    file_path = "examples/reference/widgets/Button.ipynb"
    actual = DocumentationIndexer._to_source_url(Path(file_path), repo_config)
    assert actual == "https://github.com/holoviz/panel/blob/main/examples/reference/widgets/Button.ipynb"


def test_to_source_url_azure_devops():
    repo_config = GitRepository(
        url=AnyHttpUrl("https://dev.azure.com/test-organisation/TestProject/_git/test-repository"), base_url=AnyHttpUrl("https://panel.holoviz.org/")
    )
    file_path = "examples/reference/widgets/Button.ipynb"
    actual = DocumentationIndexer._to_source_url(Path(file_path), repo_config)
    assert actual == "https://dev.azure.com/test-organisation/TestProject/_git/test-repository?path=/examples/reference/widgets/Button.ipynb&version=GBmain"


def test_to_source_url_github_raw():
    repo_config = GitRepository(url=AnyHttpUrl("https://github.com/holoviz/panel.git"), base_url=AnyHttpUrl("https://panel.holoviz.org/"))
    file_path = "examples/reference/widgets/Button.ipynb"
    actual = DocumentationIndexer._to_source_url(Path(file_path), repo_config, raw=True)
    assert actual == "https://raw.githubusercontent.com/holoviz/panel/refs/heads/main/examples/reference/widgets/Button.ipynb"


def test_to_source_url_azure_devops_raw():
    repo_config = GitRepository(
        url=AnyHttpUrl("https://dev.azure.com/test-organisation/TestProject/_git/test-repository"), base_url=AnyHttpUrl("https://panel.holoviz.org/")
    )
    file_path = "examples/reference/widgets/Button.ipynb"
    actual = DocumentationIndexer._to_source_url(Path(file_path), repo_config, raw=True)
    assert (
        actual
        == "https://dev.azure.com/test-organisation/TestProject/_apis/sourceProviders/TfsGit/filecontents?repository=test-repository&path=/examples/reference/widgets/Button.ipynb&commitOrBranch=main&api-version=7.0"
    )


# Azure Devops
#
# https://dev.azure.com/dongenergy-p/TradingAnalytics/_git/mt-docs?path=/docs/guides/daily_operation_short_version.md
# https://dev.azure.com/dongenergy-p/TradingAnalytics/_apis/sourceProviders/TfsGit/filecontents?repository=mt-docs&path=/docs/guides/daily_operation_short_version.md&commitOrBranch=main&api-version=7.0
# From: https://dongenergy-p@dev.azure.com/dongenergy-p/TradingAnalytics/_git/mt-docs and /docs/guides/daily_operation_short_version.md
# To: https://dev.azure.com/dongenergy-p/TradingAnalytics/_git/mt-docs?path=/docs/guides/daily_operation_short_version.md&version=GBmain
