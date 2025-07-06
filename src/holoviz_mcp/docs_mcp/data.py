"""Data handling for the HoloViz Documentation MCP server."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any
from typing import Optional
from urllib.parse import urljoin

import chromadb
import git
import yaml
from fastmcp import Context
from nbconvert import MarkdownExporter
from nbformat import read as nbread
from pydantic import HttpUrl
from sentence_transformers import SentenceTransformer

from holoviz_mcp.docs_mcp.models import Page

logger = logging.getLogger(__name__)


async def log_info(message: str, ctx: Context | None = None):
    """Log an info message to the context or logger."""
    if ctx:
        await ctx.info(message)
    else:
        logger.info(message)


async def log_warning(message: str, ctx: Context | None = None):
    """Log a warning message to the context or logger."""
    if ctx:
        await ctx.warning(message)
    else:
        logger.warning(message)


async def log_exception(message: str, ctx: Context | None = None):
    """Log an error message to the context or logger."""
    if ctx:
        await ctx.error(message)
    else:
        logger.error(message)
        raise Exception(message)


def convert_path_to_url(path: Path) -> str:
    """Convert a relative file path to a URL path."""
    # Convert path to URL format

    parts = list(path.parts)
    parts.pop(0)
    url = str(Path(*parts))
    url = str(url).replace(".md", ".html").replace(".ipynb", ".html")
    return url


def get_is_reference(relative_path: Path) -> bool:
    """Check if the path is a reference document."""
    return "reference" in relative_path.parts


class DocumentationIndexer:
    """Handles cloning, processing, and indexing of HoloViz documentation."""

    # Default HoloViz repositories and their configuration
    DEFAULT_REPOS = {
        "panel": {"url": "https://github.com/holoviz/panel.git", "doc_folders": ["doc", "examples/reference"], "base_url": "https://panel.holoviz.org"},
        "param": {"url": "https://github.com/holoviz/param.git", "doc_folders": ["doc"], "base_url": "https://param.holoviz.org"},
        "hvplot": {"url": "https://github.com/holoviz/hvplot.git", "doc_folders": ["doc"], "base_url": "https://hvplot.holoviz.org"},
        "holoviews": {"url": "https://github.com/holoviz/holoviews.git", "doc_folders": ["doc", "examples/reference"], "base_url": "https://holoviews.org"},
        "datashader": {"url": "https://github.com/holoviz/datashader.git", "doc_folders": ["doc"], "base_url": "https://datashader.org"},
        "geoviews": {"url": "https://github.com/holoviz/geoviews.git", "doc_folders": ["doc"], "base_url": "https://geoviews.org"},
        "colorcet": {"url": "https://github.com/holoviz/colorcet.git", "doc_folders": ["doc"], "base_url": "https://colorcet.holoviz.org"},
        "lumen": {"url": "https://github.com/holoviz/lumen.git", "doc_folders": ["doc"], "base_url": "https://lumen.holoviz.org"},
        "panel_material_ui": {
            "url": "https://github.com/panel-extensions/panel-material-ui",
            "doc_folders": ["doc", "examples/reference"],
            "base_url": "https://panel-material-ui.holoviz.org/",
        },
    }

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the DocumentationIndexer.

        Args:
            data_dir: Directory to store cloned repositories and index data.
                     Defaults to ~/holoviz_mcp/data
        """
        self.data_dir = data_dir or Path("~/.holoviz_mcp/data").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.repos_dir = self.data_dir / "repos"
        self.repos_dir.mkdir(exist_ok=True)

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=str(self.data_dir / "chroma"))
        self.collection = self.chroma_client.get_or_create_collection("holoviz_docs")

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(os.getenv("HOLOVIZ_EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

        # Initialize notebook converter
        self.nb_exporter = MarkdownExporter()

        # Load configuration
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from environment or file."""
        config = {"repositories": self.DEFAULT_REPOS.copy()}

        # Load additional configuration from file if specified
        config_file = os.getenv("HOLOVIZ_CONFIG_FILE", "")
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, "r") as f:
                    user_config = yaml.safe_load(f)
                    if "repositories" in user_config:
                        config["repositories"].update(user_config["repositories"])
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")

        return config

    def is_indexed(self) -> bool:
        """Check if documentation index exists and is valid."""
        try:
            count = self.collection.count()
            return count > 0
        except Exception:
            return False

    async def ensure_indexed(self, ctx: Context | None = None):
        """Ensure documentation is indexed, creating if necessary."""
        if not self.is_indexed():
            await log_info("Documentation index not found. Creating initial index...", ctx)
            await self.index_documentation()

    async def clone_or_update_repo(self, repo_name: str, repo_config: dict[str, str], ctx: Context | None = None) -> Optional[Path]:
        """Clone or update a single repository."""
        repo_path = self.repos_dir / repo_name

        try:
            if repo_path.exists():
                # Update existing repository
                await log_info(f"Updating {repo_name} repository at {repo_path}...", ctx)
                repo = git.Repo(repo_path)
                repo.remotes.origin.pull()
            else:
                # Clone new repository
                await log_info(f"Cloning {repo_name} repository to {repo_path}...", ctx)
                git.Repo.clone_from(
                    repo_config["url"],
                    repo_path,
                    depth=1,  # Shallow clone for efficiency
                )

            return repo_path
        except Exception as e:
            msg = f"Failed to clone/update {repo_name}: {e}"
            await log_exception(msg, ctx)
            return None

    def _generate_doc_id(self, package: str, path: Path) -> str:
        """Generate a unique document ID from package and path."""
        readable_path = str(path).replace("/", "___").replace(".", "_")
        readable_id = f"{package}___{readable_path}"

        return readable_id

    def _generate_doc_url(self, package: str, path: Path) -> str:
        """Generate documentation URL for a file."""
        base_url = self.config["repositories"][package].get("base_url", "")
        if not base_url:
            return f"https://{package}.holoviz.org"

        doc_path = convert_path_to_url(path)

        return urljoin(base_url + "/", doc_path)

    def _extract_title_from_markdown(self, content: str, fallback_filename: str = "") -> str:
        """Extract title from markdown content, with filename fallback."""
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("# "):
                # Return just the title text without the "# " prefix
                return line[2:].strip()

        # If no title found and fallback filename provided, use filename
        if fallback_filename:
            # Extract filename without extension and clean it up
            title = Path(fallback_filename).stem
            # Replace underscores with spaces and title case
            title = title.replace("_", " ").title()
            return title

        return ""

    def _extract_description_from_markdown(self, content: str) -> str:
        """Extract description from markdown content."""
        # Remove title and get first paragraph
        lines = content.split("\n")
        description_lines = []
        found_title = False

        for line in lines:
            line = line.strip()
            if line.startswith("# "):
                found_title = True
                continue
            if found_title and line:
                if line.startswith(("#", "```", "---")):
                    break
                description_lines.append(line)
                if len(" ".join(description_lines)) > 200:
                    break

        return " ".join(description_lines)[:200] + "..." if description_lines else ""

    def convert_notebook_to_markdown(self, notebook_path: Path) -> str:
        """Convert a Jupyter notebook to markdown."""
        try:
            with open(notebook_path, "r", encoding="utf-8") as f:
                notebook = nbread(f, as_version=4)

            (body, resources) = self.nb_exporter.from_notebook_node(notebook)
            return body
        except Exception as e:
            logger.error(f"Failed to convert notebook {notebook_path}: {e}")
            return str(e)

    def process_file(self, file_path: Path, package: str) -> Optional[dict[str, Any]]:
        """Process a file and extract metadata."""
        try:
            if file_path.suffix == ".md":
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = self.convert_notebook_to_markdown(file_path)

            # Extract title and description
            title = self._extract_title_from_markdown(content, file_path.name)
            if not title:
                # Additional fallback to filename
                title = file_path.stem.replace("_", " ").title()

            description = self._extract_description_from_markdown(content)

            # Generate relative path for documentation
            repo_path = self.repos_dir / package
            relative_path = file_path.relative_to(repo_path)

            # Create document ID that includes path for disambiguation
            doc_id = self._generate_doc_id(package, relative_path)

            return {
                "id": doc_id,
                "title": title,
                "url": self._generate_doc_url(package, relative_path),
                "package": package,
                "path": str(relative_path),
                "path_stem": file_path.stem,
                "description": description,
                "content": content,
                "is_reference": get_is_reference(file_path),
            }
        except Exception as e:
            logger.error(f"Failed to process markdown file {file_path}: {e}")
            return None

    async def extract_docs_from_repo(self, repo_path: Path, package: str, ctx: Context | None = None) -> list[dict[str, Any]]:
        """Extract documentation files from a repository."""
        docs = []
        repo_config = self.config["repositories"][package]
        folders = repo_config["doc_folders"]
        files: set = set()
        await log_info(f"Processing {package} documentation files in {",".join(folders)}", ctx)
        for folder in folders:
            docs_folder: Path = repo_path / folder
            files = files.union(docs_folder.rglob("*.md"))
            files = files.union(docs_folder.rglob("*.ipynb"))

        for file in files:
            if file.exists() and not file.is_dir():
                doc_data = self.process_file(file, package)
                if doc_data:
                    docs.append(doc_data)

        return docs

    async def create_embeddings(self, docs: list[dict[str, Any]], ctx=None) -> list[list[float]]:
        """Create embeddings for documentation content."""
        await log_info(f"Creating embeddings for {len(docs)} documents...", ctx)

        # Prepare text for embedding (title + description + content preview)
        texts = []
        for doc in docs:
            text_parts = [doc["title"]]
            if doc["description"]:
                text_parts.append(doc["description"])

            if doc["content"]:
                text_parts.append(doc["content"])

            texts.append(" ".join(text_parts))

        # Create embeddings
        embeddings = self.embedding_model.encode(texts).tolist()

        await log_info(f"Created {len(embeddings)} embeddings", ctx)

        return embeddings

    async def index_documentation(self, ctx: Context | None = None):
        """Indexes all documentation."""
        await log_info("Starting documentation indexing...", ctx)
        await log_info(f"📁 Repositories directory: {self.repos_dir}", ctx)
        await log_info(f"💾 Vector database location: {self.data_dir / 'chroma'}", ctx)

        all_docs = []

        # Clone/update repositories and extract documentation
        for repo_name, repo_config in self.config["repositories"].items():
            await log_info(f"Processing {repo_name}...", ctx)

            repo_path = await self.clone_or_update_repo(repo_name, repo_config)
            if repo_path:
                docs = await self.extract_docs_from_repo(repo_path, repo_name)
                all_docs.extend(docs)

        if not all_docs:
            await log_warning("No documentation found to index", ctx)
            return

        # Validate for duplicate IDs and log details
        await self._validate_unique_ids(all_docs)

        # Create embeddings
        embeddings = await self.create_embeddings(all_docs, ctx)

        # Clear existing collection
        await log_info("Clearing existing index...", ctx)

        # Only delete if collection has data
        try:
            count = self.collection.count()
            if count > 0:
                # Delete all documents by getting all IDs first
                results = self.collection.get()
                if results["ids"]:
                    self.collection.delete(ids=results["ids"])
        except Exception as e:
            logger.warning(f"Failed to clear existing collection: {e}")
            # If clearing fails, recreate the collection
            try:
                self.chroma_client.delete_collection("holoviz_docs")
                self.collection = self.chroma_client.get_or_create_collection("holoviz_docs")
            except Exception as e2:
                await log_exception(f"Failed to recreate collection: {e2}", ctx)
                raise

        # Add documents to ChromaDB
        await log_info(f"Adding {len(all_docs)} documents to index...", ctx)

        self.collection.add(
            embeddings=embeddings,
            documents=[doc["content"] for doc in all_docs],
            metadatas=[
                {
                    "title": doc["title"],
                    "url": doc["url"],
                    "package": doc["package"],
                    "path": doc["path"],
                    "path_stem": doc["path_stem"],
                    "description": doc["description"],
                    "is_reference": doc["is_reference"],
                }
                for doc in all_docs
            ],
            ids=[doc["id"] for doc in all_docs],
        )

        await log_info(f"✅ Successfully indexed {len(all_docs)} documents", ctx)
        await log_info(f"📊 Vector database stored at: {self.data_dir / 'chroma'}", ctx)
        await log_info(f"🔍 Index contains {self.collection.count()} total documents", ctx)

    async def _validate_unique_ids(self, all_docs: list[dict[str, Any]], ctx: Context | None = None) -> None:
        """Validate that all document IDs are unique and log duplicates."""
        seen_ids: dict = {}
        duplicates = []

        for doc in all_docs:
            doc_id = doc["id"]
            if doc_id in seen_ids:
                duplicates.append(
                    {"id": doc_id, "first_doc": seen_ids[doc_id], "duplicate_doc": {"package": doc["package"], "path": doc["path"], "title": doc["title"]}}
                )

                await log_warning(f"DUPLICATE ID FOUND: {doc_id}", ctx)
                await log_warning(f"  First document: {seen_ids[doc_id]['package']}/{seen_ids[doc_id]['path']} - {seen_ids[doc_id]['title']}", ctx)
                await log_warning(f"  Duplicate document: {doc['package']}/{doc['path']} - {doc['title']}", ctx)
            else:
                seen_ids[doc_id] = {"package": doc["package"], "path": doc["path"], "title": doc["title"]}

        if duplicates:
            error_msg = f"Found {len(duplicates)} duplicate document IDs"
            await log_exception(error_msg, ctx)

            # Log all duplicates for debugging
            for dup in duplicates:
                await log_exception(
                    f"Duplicate ID '{dup['id']}': {dup['first_doc']['package']}/{dup['first_doc']['path']} vs {dup['duplicate_doc']['package']}/{dup['duplicate_doc']['path']}",  # noqa: D401, E501
                    ctx,
                )

            raise ValueError(f"Document ID collision detected. {len(duplicates)} duplicate IDs found. Check logs for details.")

    async def search_get_reference_guide(self, component: str, package: Optional[str] = None, content: bool = True, ctx: Context | None = None) -> list[Page]:
        """Search for reference guides for a specific component."""
        await self.ensure_indexed()

        # Build search strategies
        where_clause = {}
        if package:
            where_clause = {"$and": [{"package": package}, {"path_stem": component}, {"is_reference": True}]}
        else:
            where_clause = {"$and": [{"path_stem": component}, {"is_reference": True}]}

        all_results = []

        filename_results = self.collection.query(query_texts=[component], n_results=1000, where=where_clause)
        if filename_results["ids"] and filename_results["ids"][0]:
            for i, _ in enumerate(filename_results["ids"][0]):
                if filename_results["metadatas"] and filename_results["metadatas"][0]:
                    metadata = filename_results["metadatas"][0][i]
                    # Include content if requested
                    content_text = filename_results["documents"][0][i] if (content and filename_results["documents"]) else None

                    # Safe URL construction
                    url_value = metadata.get("url", "https://example.com")
                    if not url_value or url_value == "None" or not isinstance(url_value, str):
                        url_value = "https://example.com"

                    # Give exact filename matches a high relevance score
                    relevance_score = 1.0  # Highest priority for exact filename matches

                    page = Page(
                        title=str(metadata["title"]),
                        url=HttpUrl(url_value),
                        package=str(metadata["package"]),
                        path=str(metadata["path"]),
                        description=str(metadata["description"]),
                        is_reference=bool(metadata["is_reference"]),
                        content=content_text,
                        relevance_score=relevance_score,
                    )

                    if package and page.package != package:
                        await log_exception(f"Package mismatch for component '{component}': expected '{package}', got '{page.package}'", ctx)
                    elif metadata["path_stem"] != component:
                        await log_exception(f"Path stem mismatch for component '{component}': expected '{component}', got '{metadata['path_stem']}'", ctx)
                    else:
                        all_results.append(page)
        return all_results

    async def search_pages(self, query: str, package: Optional[str] = None, content: bool = True, max_results: int = 5, ctx: Context | None = None) -> list[Page]:
        """Search documentation pages using semantic similarity."""
        await self.ensure_indexed(ctx=ctx)

        # Build where clause for filtering
        where_clause = {}
        if package:
            where_clause["package"] = package

        try:
            # Perform vector similarity search
            results = self.collection.query(query_texts=[query], n_results=max_results, where=where_clause if where_clause else None)

            pages = []
            if results["ids"] and results["ids"][0]:
                for i, _ in enumerate(results["ids"][0]):
                    if results["metadatas"] and results["metadatas"][0]:
                        metadata = results["metadatas"][0][i]

                        # Include content if requested
                        content_text = results["documents"][0][i] if (content and results["documents"]) else None

                        # Safe URL construction
                        url_value = metadata.get("url", "https://example.com")
                        if not url_value or url_value == "None" or not isinstance(url_value, str):
                            url_value = "https://example.com"

                        # Safe relevance score calculation
                        relevance_score = None
                        if (
                            results.get("distances")
                            and isinstance(results["distances"], list)
                            and len(results["distances"]) > 0
                            and isinstance(results["distances"][0], list)
                            and len(results["distances"][0]) > i
                        ):
                            try:
                                relevance_score = 1.0 - float(results["distances"][0][i])
                            except (ValueError, TypeError):
                                relevance_score = None

                        page = Page(
                            title=str(metadata["title"]),
                            url=HttpUrl(url_value),
                            package=str(metadata["package"]),
                            path=str(metadata["path"]),
                            description=str(metadata["description"]),
                            is_reference=bool(metadata["is_reference"]),
                            content=content_text,
                            relevance_score=relevance_score,
                        )
                        pages.append(page)

            return pages
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []

    async def get_page(self, path: str, package: str, ctx: Context | None = None) -> Page:
        """Search documentation pages using semantic similarity."""
        await self.ensure_indexed(ctx=ctx)

        # Build where clause for filtering
        where_clause = {
            "$and": [
                {"package": package},
                {"path": path},
            ]
        }

        # Perform vector similarity search
        results = self.collection.query(query_texts=[""], n_results=3, where=where_clause)

        pages = []
        if results["ids"] and results["ids"][0]:
            for i, _ in enumerate(results["ids"][0]):
                if results["metadatas"] and results["metadatas"][0]:
                    metadata = results["metadatas"][0][i]

                    # Include content if requested
                    content_text = results["documents"][0][i] if results["documents"] else None

                    # Safe URL construction
                    url_value = metadata.get("url", "https://example.com")
                    if not url_value or url_value == "None" or not isinstance(url_value, str):
                        url_value = "https://example.com"

                    # Safe relevance score calculation
                    relevance_score = None
                    if (
                        results.get("distances")
                        and isinstance(results["distances"], list)
                        and len(results["distances"]) > 0
                        and isinstance(results["distances"][0], list)
                        and len(results["distances"][0]) > i
                    ):
                        try:
                            relevance_score = 1.0 - float(results["distances"][0][i])
                        except (ValueError, TypeError):
                            relevance_score = None

                    page = Page(
                        title=str(metadata["title"]),
                        url=HttpUrl(url_value),
                        package=str(metadata["package"]),
                        path=str(metadata["path"]),
                        description=str(metadata["description"]),
                        is_reference=bool(metadata["is_reference"]),
                        content=content_text,
                        relevance_score=relevance_score,
                    )
                    pages.append(page)

        if len(pages) > 1:
            raise ValueError(f"Multiple pages found for path '{path}' in package '{package}'. Please ensure unique paths.")
        elif len(pages) == 0:
            raise ValueError(f"No page found for path '{path}' in package '{package}'.")
        return pages[0]


def main():
    """Update the DocumentationIndexer."""

    async def run_indexer():
        indexer = DocumentationIndexer()
        await indexer.index_documentation()

    asyncio.run(run_indexer())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()
