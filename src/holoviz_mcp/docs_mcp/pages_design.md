# Pages Tool Design Document

## Overview

The `pages` tool is designed to search HoloViz documentation and return relevant pages based on a user query. This document outlines the architecture, implementation approach, and technical decisions for building this functionality.

## Current State Analysis

The current `pages` tool in `server.py` is a stub that needs:
1. A `Page` model definition
2. Data preparation pipeline

### Search Implementation Details
```python
import re
from pathlib import Path
from fastmcp import Context

class DocumentationIndexer:
    def search_pages(
        self,
        name: str | None = None,
        path: str | None = None,
        query: str | None = None,
        package: str | None = None,
        content: bool = True,
        max_results: int | None = 5,
    ) -> List[Page]:
        """Enhanced search with multiple filtering options and regex support."""

        # Build ChromaDB where clause for metadata filtering
        where_clause = {}
        if package:
            where_clause["package"] = package

        # Add filtering to where clause
        if path:
            where_clause["source_path"] = {"$regex": path}

        if name:
            # Exact filename matching, not regex
            where_clause["name"] = name

        # Perform search
        if query:
            # Vector similarity search
            results = self.collection.query(
                query_texts=[query],
                n_results=max_results,
                where=where_clause if where_clause else None
            )
        else:
            # Metadata-only search
            results = self.collection.get(
                where=where_clause if where_clause else None,
                limit=max_results
            )

        # Convert to Page objects
        pages = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]

                # Include full content if requested
                if content:
                    content_text = results['documents'][0][i] if results['documents'] else ""
                else:
                    # Just metadata - no content
                    content_text = None

                page = Page(
                    title=metadata.get('title', ''),
                    url=metadata.get('url', ''),
                    package=metadata.get('package', ''),
                    path=metadata.get('path', ''),
                    description=metadata.get('description', ''),
                    content_preview=content_text,
                    relevance_score=1.0 - results['distances'][0][i] if results.get('distances') else None
                )
                pages.append(page)

        return pages
```

### Notebook to Markdown Path Mapping
```python
def process_notebook_file(self, file_path: Path, package: str, folder_type: str) -> Optional[Dict]:
    """Process a notebook file and map it to documentation structure."""
    try:
        # Convert notebook to markdown
        markdown_content = self.convert_notebook_to_markdown(file_path)
        if not markdown_content:
            return None

        # Map notebook path to documentation path
        # examples/reference/widgets/Button.ipynb -> reference/widgets/Button.md
        relative_path = file_path.relative_to(self.repos_dir / package)

        if str(relative_path).startswith('examples/reference/'):
            # Transform examples/reference/widgets/Button.ipynb to reference/widgets/Button.md
            doc_path = str(relative_path).replace('examples/reference/', 'reference/')
            doc_path = doc_path.replace('.ipynb', '.md')
        else:
            # Keep original path but change extension
            doc_path = str(relative_path).replace('.ipynb', '.md')

        # Extract title and content
        title = file_path.stem.replace('_', ' ').title()
        # ... rest of processing

        return {
            'title': title,
            'url': self._generate_doc_url(package, Path(doc_path), folder_type),
            'package': package,
            'path': doc_path,  # This is the key - mapped path
            'description': description,
            'content': text_content,
            'folder_type': folder_type,
            'id': f"{package}_{doc_path}".replace('/', '_').replace('.', '_')
        }

    except Exception as e:
        logger.error(f"Failed to process notebook file {file_path}: {e}")
        return None
```

### Configuration Managementor documentation indexing
3. Vector search implementation
4. Integration with the FastMCP framework

## Architecture

### 1. Data Models (`src/holoviz_mcp/docs_mcp/models.py`)

```python
from pydantic import BaseModel, HttpUrl
from typing import Optional

class Page(BaseModel):
    """Represents a documentation page in the HoloViz ecosystem."""

    title: str
    url: HttpUrl
    package: str
    path: str
    description: Optional[str] = None
    content_preview: Optional[str] = None
    relevance_score: Optional[float] = None
```

### 2. Data Preparation Pipeline (`src/holoviz_mcp/docs_mcp/data.py`)

The data preparation will involve:

#### HoloViz Packages to Index
- `panel` - Main Panel library
- `param` - Parameter handling
- `datashader` - Large data visualization
- `holoviews` - Declarative data visualization
- `geoviews` - Geographic visualization
- `hvplot` - High-level plotting interface
- `colorcet` - Color palettes
- `lumen` - Dashboard building
- `panel-material-ui` - Material UI components

#### Implementation Strategy

```python
import asyncio
import git
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from sentence_transformers import SentenceTransformer
import markdown
import yaml
from nbconvert import MarkdownExporter

class DocumentationIndexer:
    """Handles cloning, processing, and indexing of HoloViz documentation."""

    def __init__(self, data_dir: Path = Path("~/holoviz_mcp/data").expanduser()):
        self.data_dir = data_dir
        self.chroma_client = chromadb.PersistentClient(path=str(data_dir / "chroma"))
        self.collection = self.chroma_client.get_or_create_collection("holoviz_docs")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.nb_exporter = MarkdownExporter()
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """Load configuration from file specified by environment variable."""

    def clone_or_update_repos(self, ctx: Context = None):
        """Clone or update all HoloViz repositories with progress reporting."""

    def extract_docs_metadata(self, repo_path: Path, package: str) -> List[Dict]:
        """Extract documentation files and metadata from a repository."""

    def process_markdown_file(self, file_path: Path, package: str) -> Dict:
        """Process a single markdown file and extract relevant information."""

    def process_notebook_file(self, file_path: Path, package: str) -> Dict:
        """Process a single notebook file and convert to markdown."""

    def create_embeddings(self, docs: List[Dict], ctx: Context = None) -> List[List[float]]:
        """Create embeddings for documentation content with progress reporting."""

    def index_documentation(self, ctx: Context = None):
        """Main method to index all documentation with progress reporting."""

    def search_pages(
        self,
        name: str | None = None,
        path: str | None = None,
        query: str | None = None,
        package: str | None = None,
        content: bool = True,
        max_results: int | None = 5,
    ) -> List[Page]:
        """Search indexed documentation and return relevant pages.

        Args:
            name: Optional exact filename to filter by (e.g., "Audio.md", "Button.md")
            path: Optional path pattern (regex) to filter by (e.g., "reference/.*\.md$")
            query: Optional semantic search query
            package: Optional package name to filter by
            content: Whether to include full content in results (default: True)
            max_results: Maximum number of results to return

        Returns:
            List of Page objects matching the search criteria
        """
```

### 3. Documentation Processing Strategy

#### Git Repository Cloning
- Clone HoloViz repositories using GitPython
- Process both `docs/` and `examples/reference/` folders (configurable)
- Handle both markdown (.md) and notebook (.ipynb) files
- Support additional repositories via configuration file

#### Configuration File Support
- External configuration file for additional repositories
- Environment variable `HOLOVIZ_CONFIG_FILE` to specify config location
- Configurable folder names for documentation and reference guides
- Default folders: `docs/` and `examples/reference/`

#### Notebook Processing
- Use nbconvert to convert Jupyter notebooks to markdown
- Extract metadata and content from converted markdown
- Preserve code examples and outputs in searchable format
- Process notebooks in configurable reference folders
- **Important**: Reference notebooks in `examples/reference/**/*.ipynb` are indexed as `.md` files with paths like `reference/widgets/Button.md` to match the published documentation structure

#### Content Indexing
- Use ChromaDB for persistent vector storage
- Sentence transformers for embedding generation
- Direct markdown parsing without HTML conversion
- Metadata extraction including:
  - Package name
  - File path
  - Title (from frontmatter or headings)
  - Description (from frontmatter or first paragraph)
  - Content preview

### 4. Search Implementation

#### Enhanced Search Strategy
The search implementation now supports multiple search modes:

1. **Name-based Search**: Filter by exact filename matching (e.g., "Audio.md", "Button.md")
2. **Path-based Search**: Filter by file path using regex patterns (e.g., "reference/.*\.md$")
3. **Semantic Search**: Vector similarity search using queries
4. **Package Filtering**: Limit results to specific packages
5. **Content Control**: Option to include full content (default: True) vs. metadata only

#### Regex Pattern Support
The `path` parameter supports regex patterns for flexible path matching:

- `reference/.*\.md$` - All markdown files in reference folder and subfolders
- `reference/panes/.*\.md$` - All markdown files in reference/panes folder
- `.*/Audio.*` - All files containing "Audio" anywhere in the tree
- `docs/how_to/.*` - All files in docs/how_to folder and subfolders

#### Search Process
1. Apply exact filename filtering if `name` parameter provided
2. Apply path filtering using regex patterns if `path` parameter provided
3. Apply package filtering if `package` parameter provided
4. If `query` provided, perform vector similarity search
5. Combine and rank results by relevance
6. Return top N results as Page objects
7. Include full content if `content` is True (default), otherwise metadata only

### 5. Integration Points

#### Configuration (`src/holoviz_mcp/shared/config.py`)
```python
# Add documentation-specific configuration
DATA_DIR = Path(os.getenv("HOLOVIZ_DATA_DIR", "~/holoviz_mcp/data")).expanduser()
CONFIG_FILE = os.getenv("HOLOVIZ_CONFIG_FILE", "")
DOCS_UPDATE_INTERVAL = int(os.getenv("HOLOVIZ_DOCS_UPDATE_INTERVAL", "86400"))  # 24 hours
```

#### Configuration File Format
```yaml
# holoviz_config.yaml
repositories:
  # Core HoloViz packages (built-in)
  panel:
    url: "https://github.com/holoviz/panel.git"
    docs_folder: "docs"
    reference_folder: "examples/reference"

  # Additional user-defined repositories
  my_custom_panel_extension:
    url: "https://github.com/user/my-panel-extension.git"
    docs_folder: "documentation"
    reference_folder: "examples"

  another_project:
    url: "https://github.com/org/another-project.git"
    docs_folder: "docs"
    reference_folder: "reference"

# Default folder configuration
default_docs_folder: "docs"
default_reference_folder: "examples/reference"
```

## Index Update Strategy

### **First Time Initialization**
The documentation index will be created **automatically on first use** of either the `get_reference_guide` or `pages` tools:

```python
# In both tools, there will be logic like:
if not indexer.is_indexed():
    logger.info("Documentation index not found. Creating initial index...")
    indexer.index_documentation()
```

**Benefits of lazy initialization:**
- **No upfront setup required** - the index is created when first needed
- **Better UX** - users can start using tools immediately without waiting for setup
- **Resource efficiency** - only creates index when actually needed
- **Simpler deployment** - no background processes or startup delays

### **Subsequent Updates**
After the initial creation, the index will be updated **only when manually triggered** using the `update_index` tool:

```python
# Manual updates only
update_index()  # User must explicitly call this
```

**Benefits of manual updates:**
- **Predictable behavior** - index content doesn't change unexpectedly
- **Resource control** - users control when expensive re-indexing happens
- **Reliability** - no background processes that could fail silently
- **Explicit control** - users decide when to refresh documentation

### **Implementation Details**

```python
class DocumentationIndexer:
    def is_indexed(self) -> bool:
        """Check if documentation index exists and is valid."""
        try:
            # Check if ChromaDB collection exists and has documents
            collection = self.chroma_client.get_collection("holoviz_docs")
            count = collection.count()
            return count > 0
        except Exception:
            return False

    def ensure_indexed(self, ctx: Context = None):
        """Ensure documentation is indexed, creating if necessary."""
        if not self.is_indexed():
            await self.log_info("Documentation index not found. Creating initial index...")
            self.index_documentation(ctx)
```

### **Recommended Usage Pattern**

```python
# Day 1: First use (automatic index creation)
get_reference_guide("Button", "panel")  # Index created automatically during first call

# Day 7: Manual refresh to get latest documentation
update_index()  # User explicitly updates when needed

# Day 14: Another manual refresh
update_index()  # User controls update frequency
```

### **Alternative Strategies (Future Enhancements)**

The following could be added in future versions but are not currently implemented:

1. **Time-based updates**: Check for updates every 24 hours (via `DOCS_UPDATE_INTERVAL`)
2. **Webhook updates**: Update when GitHub repositories change
3. **Startup checks**: Check for stale index on server startup
4. **Background updates**: Periodic updates without blocking user requests

This strategy balances **ease of use** (automatic first-time setup) with **control** (manual updates when needed), making it suitable for an MCP server where users want predictable, on-demand documentation access.
