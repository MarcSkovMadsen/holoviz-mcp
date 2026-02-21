from pathlib import Path
from typing import Any

import chromadb
import pytest
from pydantic import AnyHttpUrl

from holoviz_mcp.config import GitRepository
from holoviz_mcp.holoviz_mcp.data import DocumentationIndexer
from holoviz_mcp.holoviz_mcp.data import chunk_document
from holoviz_mcp.holoviz_mcp.data import convert_path_to_url
from holoviz_mcp.holoviz_mcp.data import extract_keywords
from holoviz_mcp.holoviz_mcp.data import extract_relevant_excerpt
from holoviz_mcp.holoviz_mcp.data import find_keyword_matches
from holoviz_mcp.holoviz_mcp.data import truncate_content


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


# Tests for context-aware content truncation


def test_extract_keywords_basic():
    """Test basic keyword extraction."""
    keywords = extract_keywords("How to extract data from FUMO")
    assert "extract" in keywords
    assert "data" in keywords
    assert "fumo" in keywords
    # Stopwords should be removed
    assert "how" not in keywords
    assert "to" not in keywords
    assert "from" not in keywords


def test_extract_keywords_stopwords_only():
    """Test that stopword-only queries return empty list."""
    keywords = extract_keywords("the and or but in on at")
    assert keywords == []


def test_extract_keywords_short_words():
    """Test that short words (<=2 chars) are filtered out."""
    keywords = extract_keywords("a ab abc abcd")
    assert "a" not in keywords
    assert "ab" not in keywords
    assert "abc" in keywords
    assert "abcd" in keywords


def test_extract_keywords_case_insensitive():
    """Test that keywords are lowercased."""
    keywords = extract_keywords("Button COMPONENT Widget")
    assert "button" in keywords
    assert "component" in keywords
    assert "widget" in keywords


def test_find_keyword_matches_single_match():
    """Test finding a single keyword match."""
    content = "Python is great for data analysis."
    matches = find_keyword_matches(content, ["python"])
    assert len(matches) == 1
    assert matches[0] == (0, 6, "python")


def test_find_keyword_matches_multiple_same_keyword():
    """Test finding multiple instances of the same keyword."""
    content = "Python is great. Python is powerful. Python rocks!"
    matches = find_keyword_matches(content, ["python"])
    assert len(matches) == 3
    assert matches[0][0] == 0
    assert matches[1][0] == 17
    assert matches[2][0] == 37


def test_find_keyword_matches_multiple_keywords():
    """Test finding multiple different keywords."""
    content = "Learn Python for data analysis and visualization."
    matches = find_keyword_matches(content, ["python", "data", "visualization"])
    assert len(matches) == 3
    # Matches should be sorted by position
    assert matches[0][2] == "python"
    assert matches[1][2] == "data"
    assert matches[2][2] == "visualization"


def test_find_keyword_matches_case_insensitive():
    """Test that keyword matching is case-insensitive."""
    content = "Python is great. PYTHON is powerful."
    matches = find_keyword_matches(content, ["python"])
    assert len(matches) == 2


def test_find_keyword_matches_no_matches():
    """Test behavior when no matches are found."""
    content = "This is some text without the keyword."
    matches = find_keyword_matches(content, ["python"])
    assert matches == []


def test_extract_relevant_excerpt_with_match():
    """Test excerpt extraction with keyword match in middle of document."""
    content = "x" * 5000 + "IMPORTANT MATCH HERE" + "y" * 5000
    excerpt = extract_relevant_excerpt(content, "match", max_chars=1000)

    # Should contain the match
    assert "MATCH" in excerpt

    # Should have reasonable length (with some tolerance for separators)
    assert len(excerpt) <= 1100

    # Should have [...] indicators since we truncated
    assert "[...]" in excerpt


def test_extract_relevant_excerpt_multiple_matches():
    """Test excerpt extraction with multiple keyword matches."""
    content = "Start text. " + "x" * 1000 + " First MATCH here " + "y" * 1000 + " Second MATCH there " + "z" * 1000
    excerpt = extract_relevant_excerpt(content, "match", max_chars=2000)

    # Should contain both matches if they fit
    assert excerpt.count("MATCH") >= 1

    # Should have reasonable length
    assert len(excerpt) <= 2100


def test_extract_relevant_excerpt_no_match_fallback():
    """Test fallback to beginning when no matches found."""
    content = "Beginning text is important. " + "x" * 10000
    excerpt = extract_relevant_excerpt(content, "nomatch xyz123", max_chars=1000)

    # Should start with the beginning of the document
    assert excerpt.startswith("Beginning")

    # Should have truncation indicator
    assert "[... content truncated" in excerpt or "[...]" in excerpt


def test_extract_relevant_excerpt_empty_query():
    """Test behavior with empty query."""
    content = "Beginning text. " + "x" * 10000
    excerpt = extract_relevant_excerpt(content, "", max_chars=1000)

    # Should fall back to simple truncation
    assert excerpt.startswith("Beginning")
    assert len(excerpt) <= 1100


def test_extract_relevant_excerpt_short_content():
    """Test that short content is not truncated."""
    content = "This is a short document with a MATCH keyword."
    excerpt = extract_relevant_excerpt(content, "match", max_chars=1000)

    # Should return full content without truncation
    assert excerpt == content


def test_truncate_content_with_query():
    """Test truncate_content with query parameter."""
    content = "x" * 5000 + " IMPORTANT KEYWORD HERE " + "y" * 5000
    result = truncate_content(content, max_chars=1000, query="keyword")

    # Should use smart truncation
    assert result is not None
    assert "KEYWORD" in result
    assert len(result) <= 1100


def test_truncate_content_without_query():
    """Test truncate_content without query parameter (legacy behavior)."""
    content = "Beginning text. " + "x" * 10000 + " END KEYWORD HERE"
    result = truncate_content(content, max_chars=1000, query=None)

    # Should use simple truncation from beginning
    assert result is not None
    assert result.startswith("Beginning")
    assert "KEYWORD" not in result  # Keyword is at the end, so it won't be included
    assert "[... content truncated" in result


def test_truncate_content_no_truncation_needed():
    """Test that content under limit is not truncated."""
    content = "This is a short document."
    result = truncate_content(content, max_chars=1000, query="document")

    # Should return full content
    assert result == content


def test_truncate_content_none_handling():
    """Test that None values are handled correctly."""
    assert truncate_content(None, 1000, "query") is None
    assert truncate_content("content", None, "query") == "content"
    assert truncate_content(None, None, "query") is None


def test_extract_relevant_excerpt_word_boundaries():
    """Test that excerpts break at word boundaries."""
    content = "x" * 100 + " word boundary before MATCH and after word boundary " + "y" * 100
    excerpt = extract_relevant_excerpt(content, "match", max_chars=200, context_chars=50)

    # Should contain the match
    assert "MATCH" in excerpt

    # Should not start or end mid-word (unless at document boundaries)
    words = excerpt.split()
    # Check that words are complete (no fragments like "xxx...xxx")
    for word in words:
        if word != "[...]":
            assert len(word) < 50  # Words should be reasonable length, not fragments


def test_extract_relevant_excerpt_multiple_clusters():
    """Test excerpt extraction with distant matches."""
    # Create content with two matches far apart
    content = "First MATCH here " + "x" * 5000 + " Second MATCH there"
    excerpt = extract_relevant_excerpt(content, "match", max_chars=1500, context_chars=300)

    # Should contain at least one match
    assert "MATCH" in excerpt

    # If both matches fit, they should be separated by [...]
    if excerpt.count("MATCH") == 2:
        assert "\n\n[...]\n\n" in excerpt


def test_truncate_content_with_special_characters():
    """Test handling of special characters in query."""
    content = "Start text with special chars: foo-bar, baz_qux. More text here."
    result = truncate_content(content, max_chars=1000, query="foo-bar baz_qux")

    # Should handle special characters gracefully
    assert result is not None
    assert "foo-bar" in result or "baz_qux" in result or "Start text" in result


# --- ChromaDB health check and backup tests ---


def test_init_health_check_recovers_from_corrupt_db(tmp_path):
    """ChromaDB init recovers from a corrupt database by wiping and reinitializing."""
    from chromadb.api.shared_system_client import SharedSystemClient

    vector_dir = tmp_path / "chroma"
    vector_dir.mkdir()

    # Write a corrupt chroma.sqlite3 to trigger an init failure
    (vector_dir / "chroma.sqlite3").write_text("THIS IS NOT A VALID SQLITE FILE")

    # Clear cached ChromaDB state from other tests to avoid stale references
    SharedSystemClient.clear_system_cache()

    indexer = DocumentationIndexer(data_dir=tmp_path, repos_dir=tmp_path / "repos", vector_dir=vector_dir)

    # Should have recovered: collection exists and is empty
    assert indexer.collection.count() == 0


def test_init_health_check_reraises_keyboard_interrupt(tmp_path):
    """KeyboardInterrupt during ChromaDB init is not swallowed."""
    from unittest.mock import patch

    vector_dir = tmp_path / "chroma"
    vector_dir.mkdir()

    with patch("chromadb.PersistentClient", side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            DocumentationIndexer(data_dir=tmp_path, repos_dir=tmp_path / "repos", vector_dir=vector_dir)


def test_is_indexed_catches_base_exception(tmp_path):
    """is_indexed() returns False when collection.count() raises a BaseException subclass."""
    from unittest.mock import PropertyMock
    from unittest.mock import patch

    indexer = DocumentationIndexer(data_dir=tmp_path, repos_dir=tmp_path / "repos", vector_dir=tmp_path / "chroma")

    # Simulate a PanicException (BaseException subclass) from ChromaDB's Rust backend
    class FakePanicException(BaseException):
        pass

    with patch.object(type(indexer.collection), "count", new_callable=PropertyMock) as mock_count:
        mock_count.return_value = FakePanicException("rust panic")
        # Replace count as a regular method that raises
        indexer.collection.count = lambda: (_ for _ in ()).throw(FakePanicException("rust panic"))  # type: ignore[assignment]
        assert indexer.is_indexed() is False


def test_backup_path_property(tmp_path):
    """_backup_path returns the correct sibling path with .bak suffix."""
    indexer = DocumentationIndexer(data_dir=tmp_path, repos_dir=tmp_path / "repos", vector_dir=tmp_path / "chroma")
    assert indexer._backup_path == tmp_path / "chroma.bak"


@pytest.mark.asyncio
async def test_restore_from_backup_on_write_failure(tmp_path):
    """On write failure, _restore_from_backup recovers original data."""
    import shutil

    from chromadb.api.shared_system_client import SharedSystemClient

    vector_dir = tmp_path / "chroma"
    SharedSystemClient.clear_system_cache()
    indexer = DocumentationIndexer(data_dir=tmp_path, repos_dir=tmp_path / "repos", vector_dir=vector_dir)

    # Seed the collection with one document
    indexer.collection.add(documents=["hello world"], metadatas=[{"project": "test"}], ids=["doc1"])
    assert indexer.collection.count() == 1

    # Force-flush by recreating the client so all WAL data is checkpointed
    del indexer.chroma_client
    SharedSystemClient.clear_system_cache()
    client = chromadb.PersistentClient(path=str(vector_dir))
    assert client.get_or_create_collection("holoviz_docs").count() == 1
    del client
    SharedSystemClient.clear_system_cache()

    # Create a backup (simulating what index_documentation does)
    backup_path = indexer._backup_path
    shutil.copytree(vector_dir, backup_path, dirs_exist_ok=True)

    # Recreate indexer to get fresh client after backup
    indexer = DocumentationIndexer(data_dir=tmp_path, repos_dir=tmp_path / "repos", vector_dir=vector_dir)

    # Now corrupt the live database by clearing and adding a bad doc
    indexer.collection.delete(ids=["doc1"])
    indexer.collection.add(documents=["corrupted"], metadatas=[{"project": "bad"}], ids=["bad1"])
    assert indexer.collection.count() == 1

    # Restore from backup
    await indexer._restore_from_backup()

    # After restore, should have the original document back
    assert indexer.collection.count() == 1
    result = indexer.collection.get(ids=["doc1"])
    assert result["ids"] == ["doc1"]
    assert result["documents"] == ["hello world"]


# --- chunk_document tests ---


def _make_doc(**overrides: Any) -> dict[str, Any]:
    """Create a minimal document dict for testing chunk_document()."""
    doc: dict[str, Any] = {
        "id": "test___doc_md",
        "title": "Test Doc",
        "url": "https://example.com/doc.html",
        "project": "test-project",
        "source_path": "doc/test.md",
        "source_path_stem": "test",
        "source_url": "https://github.com/org/repo/blob/main/doc/test.md",
        "description": "A test document.",
        "is_reference": False,
        "content": "Hello world",
    }
    doc.update(overrides)
    return doc


def test_chunk_document_no_headers():
    """Document without headers -> single chunk with chunk_index=0."""
    doc = _make_doc(content="No headers here, just plain text that is long enough to survive filtering.")
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["parent_id"] == doc["id"]
    assert "No headers here" in chunks[0]["content"]


def test_chunk_document_single_h1():
    """Document with one H1 -> preamble + 1 section (2 chunks)."""
    preamble = "This is the preamble with enough text to pass the minimum character threshold for chunking. Adding more text to exceed 100 characters."
    section = "This is section one content with enough text to pass the minimum character threshold. Adding more text to exceed 100 characters."
    content = f"{preamble}\n# Section One\n{section}"
    doc = _make_doc(content=content)
    chunks = chunk_document(doc)
    assert len(chunks) == 2
    assert "preamble" in chunks[0]["content"]
    assert "# Section One" in chunks[1]["content"]


def test_chunk_document_multiple_h2():
    """Multiple H2 headers -> correct number of chunks."""
    filler = " Extra filler text to ensure each section is well over the one hundred character minimum threshold."
    content = (
        f"Preamble text that is definitely long enough to pass the minimum character threshold for this test.{filler}\n"
        f"## Section A\nContent A with enough text to pass the minimum character threshold for chunking.{filler}\n"
        f"## Section B\nContent B with enough text to pass the minimum character threshold for chunking.{filler}\n"
        f"## Section C\nContent C with enough text to pass the minimum character threshold for chunking.{filler}"
    )
    doc = _make_doc(content=content)
    chunks = chunk_document(doc)
    assert len(chunks) == 4  # preamble + 3 sections
    assert "## Section A" in chunks[1]["content"]
    assert "## Section B" in chunks[2]["content"]
    assert "## Section C" in chunks[3]["content"]


def test_chunk_document_metadata_preserved():
    """All parent metadata (url, project, etc.) copied to each chunk."""
    filler = " Extra filler text to ensure each section is over the minimum threshold."
    content = (
        f"Preamble text long enough to survive the minimum character threshold easily.{filler}"
        f"\n# Section\nSection content long enough to survive the minimum character threshold easily.{filler}"
    )
    doc = _make_doc(content=content)
    chunks = chunk_document(doc)
    assert len(chunks) == 2

    for chunk in chunks:
        assert chunk["title"] == doc["title"]
        assert chunk["url"] == doc["url"]
        assert chunk["project"] == doc["project"]
        assert chunk["source_path"] == doc["source_path"]
        assert chunk["source_path_stem"] == doc["source_path_stem"]
        assert chunk["source_url"] == doc["source_url"]
        assert chunk["description"] == doc["description"]
        assert chunk["is_reference"] == doc["is_reference"]


def test_chunk_document_ids():
    """Chunk IDs follow {parent_id}___chunk_{N} pattern."""
    filler = " Extra filler text to ensure each section is over the minimum threshold."
    content = (
        f"Preamble with enough text for minimum character threshold easily cleared.{filler}"
        f"\n# Section\nSection with enough text for minimum character threshold easily cleared.{filler}"
    )
    doc = _make_doc(content=content)
    chunks = chunk_document(doc)
    for idx, chunk in enumerate(chunks):
        assert chunk["id"] == f"{doc['id']}___chunk_{idx}"


def test_chunk_document_parent_id():
    """parent_id field set correctly on every chunk."""
    filler = " Extra filler text to ensure each section is over the minimum threshold."
    content = (
        f"Long enough preamble text for the minimum character threshold requirement.{filler}"
        f"\n## H2\nLong enough section text for the minimum character threshold requirement.{filler}"
    )
    doc = _make_doc(content=content)
    chunks = chunk_document(doc)
    for chunk in chunks:
        assert chunk["parent_id"] == doc["id"]


def test_chunk_document_skips_tiny_chunks():
    """Chunks under min_chunk_chars are skipped."""
    content = (
        "Preamble text that is definitely long enough to survive filtering at any threshold."
        "\n# A\nTiny\n# B\nThis section has enough content to survive the minimum character threshold."
    )
    doc = _make_doc(content=content)
    chunks = chunk_document(doc, min_chunk_chars=50)
    # "# A\nTiny" should be skipped (only ~10 chars)
    for chunk in chunks:
        assert len(chunk["content"].strip()) >= 50


def test_chunk_document_empty_content():
    """Empty content -> single chunk."""
    doc = _make_doc(content="")
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    # Title prefix is prepended even for empty content
    assert chunks[0]["content"] == "Test Doc\n\n"
    assert chunks[0]["raw_content"] == ""


def test_chunk_document_h3_no_split():
    """H3/H4 headers do NOT cause splitting."""
    content = "Preamble long enough text to pass any threshold we need for this test to work properly.\n### H3 Header\nH3 content\n#### H4 Header\nH4 content"
    doc = _make_doc(content=content)
    chunks = chunk_document(doc)
    # H3/H4 should not split, so only 1 chunk
    assert len(chunks) == 1
    assert "### H3 Header" in chunks[0]["content"]
    assert "#### H4 Header" in chunks[0]["content"]


def test_chunk_document_code_block_comments_not_split():
    """Python comments and decorative lines inside code blocks do NOT cause splitting."""
    content = (
        "# Real Header\n\n"
        "Some intro text that is long enough to exceed the minimum character threshold for chunking.\n\n"
        "```python\n"
        "# This is a Python comment that should NOT split\n"
        "x = 1\n"
        "# ========================================\n"
        "# Another decorative divider in code\n"
        "y = 2\n"
        "```\n\n"
        "## Second Header\n\n"
        "More content here that is long enough to exceed the minimum character threshold for chunking."
    )
    doc = _make_doc(content=content)
    chunks = chunk_document(doc)
    # Should only split at the two real markdown headers, not at Python comments
    assert len(chunks) == 2
    assert "# Real Header" in chunks[0]["content"]
    assert "# This is a Python comment" in chunks[0]["content"]
    assert "# ========" in chunks[0]["content"]
    assert "## Second Header" in chunks[1]["content"]


# --- Search content mode tests ---

# Multi-section document for content mode testing
MULTI_SECTION_CONTENT = (
    "This is the preamble of the test document. It contains general information about the document. "
    "This text should be long enough to exceed the minimum chunk character threshold of one hundred characters. "
    "Adding more text to make sure this preamble section is substantial enough for proper chunking.\n"
    "## Section Alpha\n"
    "This is the first section about alpha topics. It discusses alpha-related features and functionality. "
    "The alpha section contains information about configuration, setup, and basic usage patterns. "
    "This text should be long enough to exceed the minimum chunk character threshold of one hundred characters.\n"
    "## Section Beta\n"
    "This is the second section about beta features. Beta features include advanced formatting options. "
    "The beta section covers formatters, editors, and other display customization possibilities. "
    "This text should be long enough to exceed the minimum chunk character threshold of one hundred characters.\n"
    "## Section Gamma\n"
    "This is the third section covering gamma capabilities. Gamma includes pagination and data loading. "
    "The gamma section explains page_size, local vs remote pagination, and streaming data updates. "
    "This text should be long enough to exceed the minimum chunk character threshold of one hundred characters."
)


@pytest.fixture
def populated_indexer(tmp_path):
    """Create an indexer with a multi-chunk test document for content mode testing."""
    from chromadb.api.shared_system_client import SharedSystemClient

    SharedSystemClient.clear_system_cache()

    indexer = DocumentationIndexer(
        data_dir=tmp_path,
        repos_dir=tmp_path / "repos",
        vector_dir=tmp_path / "chroma",
    )

    doc = _make_doc(content=MULTI_SECTION_CONTENT, title="Test Document")
    chunks = chunk_document(doc)
    assert len(chunks) >= 3, f"Expected at least 3 chunks, got {len(chunks)}"

    indexer.collection.add(
        documents=[c["content"] for c in chunks],
        metadatas=[
            {
                "title": c["title"],
                "url": c["url"],
                "project": c["project"],
                "source_path": c["source_path"],
                "source_path_stem": c["source_path_stem"],
                "source_url": c["source_url"],
                "description": c["description"],
                "is_reference": c["is_reference"],
                "chunk_index": c["chunk_index"],
                "parent_id": c["parent_id"],
            }
            for c in chunks
        ],
        ids=[c["id"] for c in chunks],
    )

    return indexer


@pytest.mark.asyncio
async def test_search_content_chunk_returns_single_chunk(populated_indexer):
    """content='chunk' returns only the best-matching chunk, not the full document."""
    results = await populated_indexer.search("alpha", content="chunk", max_results=1)
    assert len(results) == 1
    doc = results[0]
    assert doc.content is not None
    # Should contain the alpha section
    assert "alpha" in doc.content.lower()
    # Should NOT contain the full document (just a single chunk)
    full_doc = await populated_indexer.get_document(doc.source_path, doc.project)
    assert len(doc.content) < len(full_doc.content)


@pytest.mark.asyncio
async def test_search_content_truncated_returns_full_doc_truncated(populated_indexer):
    """content='truncated' returns truncated full document content."""
    results = await populated_indexer.search("alpha", content="truncated", max_results=1, max_content_chars=300)
    assert len(results) == 1
    doc = results[0]
    assert doc.content is not None
    # Should be truncated — the full doc is much longer than 300 chars
    full_doc = await populated_indexer.get_document(doc.source_path, doc.project)
    assert len(doc.content) < len(full_doc.content)


@pytest.mark.asyncio
async def test_search_content_full_returns_complete_document(populated_indexer):
    """content='full' returns the complete untruncated document."""
    results = await populated_indexer.search("alpha", content="full", max_results=1)
    assert len(results) == 1
    doc = results[0]
    assert doc.content is not None
    # Should contain ALL sections
    assert "alpha" in doc.content.lower()
    assert "beta" in doc.content.lower()
    assert "gamma" in doc.content.lower()
    # Should match get_document() output
    full_doc = await populated_indexer.get_document(doc.source_path, doc.project)
    assert doc.content == full_doc.content


@pytest.mark.asyncio
async def test_search_content_false_returns_no_content(populated_indexer):
    """content=False returns None for content."""
    results = await populated_indexer.search("alpha", content=False, max_results=1)
    assert len(results) == 1
    assert results[0].content is None


@pytest.mark.asyncio
async def test_search_content_true_backward_compat(populated_indexer):
    """content=True behaves like 'truncated' (backward compatibility)."""
    results_true = await populated_indexer.search("alpha", content=True, max_results=1)
    results_truncated = await populated_indexer.search("alpha", content="truncated", max_results=1)
    assert len(results_true) == 1
    assert len(results_truncated) == 1
    # Both should have content
    assert results_true[0].content is not None
    assert results_truncated[0].content is not None
    # Content should be the same
    assert results_true[0].content == results_truncated[0].content
