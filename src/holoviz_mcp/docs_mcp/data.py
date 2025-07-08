"""Data handling for the HoloViz Documentation MCP server."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any
from typing import Optional

import chromadb
import git
import numpy as np
from fastmcp import Context
from nbconvert import MarkdownExporter
from nbformat import read as nbread
from pydantic import HttpUrl
from sentence_transformers import SentenceTransformer

from holoviz_mcp.config.loader import get_config
from holoviz_mcp.config.models import EnvironmentConfig
from holoviz_mcp.config.models import FolderConfig
from holoviz_mcp.config.models import GitRepository
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


def get_best_practices(package: str) -> str:
    """Get best practices for using a package with LLMs.

    This function searches for best practices resources in user and default directories,
    with user resources taking precedence over default ones.

    Args:
        package (str): The name of the package to get best practices for.
                      Both hyphenated (e.g., "panel-material-ui") and underscored
                      (e.g., "panel_material_ui") names are supported.

    Returns
    -------
        str: A string containing the best practices for the package in Markdown format.

    Raises
    ------
        FileNotFoundError: If no best practices file is found for the package.
    """
    env_config = EnvironmentConfig.from_environment()

    # Convert underscored names to hyphenated for file lookup
    package_filename = package.replace("_", "-")

    # Search in user directory first, then default directory
    search_paths = [
        env_config.best_practices_dir("user"),
        env_config.best_practices_dir("default"),
    ]

    for search_dir in search_paths:
        best_practices_file = search_dir / f"{package_filename}.md"
        if best_practices_file.exists():
            return best_practices_file.read_text(encoding="utf-8")

    # If not found, raise error with helpful message
    available_files = []
    for search_dir in search_paths:
        if search_dir.exists():
            available_files.extend([f.stem for f in search_dir.glob("*.md")])

    available_str = ", ".join(set(available_files)) if available_files else "None"
    raise FileNotFoundError(
        f"Best practices file for package '{package}' not found. " f"Available packages: {available_str}. " f"Searched in: {[str(p) for p in search_paths]}"
    )


def list_best_practices() -> list[str]:
    """List all available best practices packages.

    This function discovers available best practices from both user and default directories,
    with user resources taking precedence over default ones.

    Returns
    -------
        list[str]: A list of package names that have best practices available.
                   Names are returned in hyphenated format (e.g., "panel-material-ui").
    """
    env_config = EnvironmentConfig.from_environment()

    # Collect available packages from both directories
    available_packages = set()

    search_paths = [
        env_config.best_practices_dir("user"),
        env_config.best_practices_dir("default"),
    ]

    for search_dir in search_paths:
        if search_dir.exists():
            for md_file in search_dir.glob("*.md"):
                available_packages.add(md_file.stem)

    return sorted(list(available_packages))


def convert_path_to_url(path: Path, remove_first_part: bool = True) -> str:
    """Convert a relative file path to a URL path."""
    # Convert path to URL format
    parts = list(path.parts)

    # Only remove first part if requested (for legacy compatibility)
    if remove_first_part and parts:
        parts.pop(0)

    url = str(Path(*parts)) if parts else ""
    url = str(url).replace(".md", ".html").replace(".ipynb", ".html").replace(".rst", ".html")
    return url


def get_is_reference(relative_path: Path) -> bool:
    """Check if the path is a reference document (legacy function)."""
    return "reference" in relative_path.parts


class DocumentationIndexer:
    """Handles cloning, processing, and indexing of documentation."""

    def __init__(self, data_dir: Optional[Path] = None, repos_dir: Optional[Path] = None):
        """Initialize the DocumentationIndexer.

        Args:
            data_dir: Directory to store index data. Defaults to user config directory.
            repos_dir: Directory to store cloned repositories. Defaults to HOLOVIZ_MCP_REPOS_DIR.
        """
        # Use environment config for default paths
        env_config = EnvironmentConfig.from_environment()

        self.data_dir = data_dir or env_config.user_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Use configurable repos directory for repository downloads
        self.repos_dir = repos_dir or env_config.repos_dir
        self.repos_dir.mkdir(parents=True, exist_ok=True)

        # Use config logic to resolve vector DB path
        config = get_config()
        vector_db_path = config.server.get_vector_db_path(env_config.user_dir)
        vector_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Disable ChromaDB telemetry based on config
        if not config.server.anonymized_telemetry:
            os.environ["ANONYMIZED_TELEMETRY"] = "False"

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=str(vector_db_path))
        self.collection = self.chroma_client.get_or_create_collection("holoviz_docs")

        # Initialize embedding model with SSL certificate handling
        self.embedding_model = self._initialize_embedding_model()

        # Initialize notebook converter
        self.nb_exporter = MarkdownExporter()

        # Load documentation config from the centralized config system
        self.config = get_config().docs

    def _initialize_embedding_model(self) -> SentenceTransformer:
        """Initialize the SentenceTransformer with SSL certificate handling."""
        model_name = os.getenv("HOLOVIZ_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

        try:
            # Try to load the model normally first
            return SentenceTransformer(model_name)
        except Exception as e:
            if "SSL" in str(e) or "certificate" in str(e).lower():
                logger.warning(f"SSL certificate error encountered: {e}")
                logger.info("Attempting to configure SSL certificates...")

                # Try to set SSL certificate path using certifi
                try:
                    import certifi

                    cert_path = certifi.where()
                    # Set both environment variables for maximum compatibility
                    os.environ["SSL_CERT_FILE"] = cert_path
                    os.environ["REQUESTS_CA_BUNDLE"] = cert_path
                    logger.info(f"Set SSL_CERT_FILE and REQUESTS_CA_BUNDLE to: {cert_path}")

                    # Retry loading the model
                    return SentenceTransformer(model_name)
                except Exception as cert_error:
                    logger.error(f"Failed to configure SSL certificates: {cert_error}")
                    logger.warning("Please ensure your SSL certificates are properly configured.")
                    logger.warning("For Windows users, try setting REQUESTS_CA_BUNDLE environment variable.")
                    raise
            else:
                # Re-raise non-SSL related errors
                raise

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

    async def clone_or_update_repo(self, repo_name: str, repo_config: "GitRepository", ctx: Context | None = None) -> Optional[Path]:
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
                clone_kwargs: dict[str, Any] = {"depth": 1}  # Shallow clone for efficiency

                # Add branch, tag, or commit if specified
                if repo_config.branch:
                    clone_kwargs["branch"] = repo_config.branch
                elif repo_config.tag:
                    clone_kwargs["branch"] = repo_config.tag
                elif repo_config.commit:
                    # For specific commits, we need to clone and then checkout
                    git.Repo.clone_from(str(repo_config.url), repo_path, **clone_kwargs)
                    repo = git.Repo(repo_path)
                    repo.git.checkout(repo_config.commit)
                    return repo_path

                git.Repo.clone_from(str(repo_config.url), repo_path, **clone_kwargs)

            return repo_path
        except Exception as e:
            msg = f"Failed to clone/update {repo_name}: {e}"
            await log_warning(msg, ctx)  # Changed from log_exception to log_warning so it doesn't raise
            return None

    def _is_reference_document(self, file_path: Path, package: str, folder_name: str = "") -> bool:
        """Check if the document is a reference document using configurable patterns.

        Args:
            file_path: Full path to the file
            package: Package name
            folder_name: Name of the folder this file belongs to

        Returns
        -------
            bool: True if this is a reference document
        """
        repo_config = self.config.repositories[package]
        repo_path = self.repos_dir / package

        try:
            relative_path = file_path.relative_to(repo_path)

            # Check against configured reference patterns
            for pattern in repo_config.reference_patterns:
                if relative_path.match(pattern):
                    return True

            # Fallback to legacy check
            return get_is_reference(relative_path)
        except (ValueError, KeyError):
            # If we can't determine relative path or no patterns configured, use legacy
            return get_is_reference(file_path)

    def _generate_doc_id(self, package: str, path: Path) -> str:
        """Generate a unique document ID from package and path."""
        readable_path = str(path).replace("/", "___").replace(".", "_")
        readable_id = f"{package}___{readable_path}"

        return readable_id

    def _generate_doc_url(self, package: str, path: Path, folder_name: str = "") -> str:
        """Generate documentation URL for a file."""
        repo_config = self.config.repositories[package]
        base_url = str(repo_config.base_url).rstrip("/")

        # Get the URL path mapping for this folder
        folder_url_path = repo_config.get_folder_url_path(folder_name)

        # If there's a folder URL mapping, we need to adjust the path
        if folder_url_path and folder_name:
            # Remove the folder name from the beginning of the path
            path_str = str(path)

            # Check if path starts with the folder name
            if path_str.startswith(folder_name + "/"):
                # Remove the folder prefix and leading slash
                remaining_path = path_str[len(folder_name) + 1 :]
                adjusted_path = Path(remaining_path) if remaining_path else Path(".")
            elif path_str == folder_name:
                # The path is exactly the folder name
                adjusted_path = Path(".")
            else:
                # Fallback: try to remove folder parts from the beginning
                path_parts = list(path.parts)
                folder_parts = folder_name.split("/")
                for folder_part in folder_parts:
                    if path_parts and path_parts[0] == folder_part:
                        path_parts = path_parts[1:]
                adjusted_path = Path(*path_parts) if path_parts else Path(".")

            # Don't remove first part since we already adjusted the path
            doc_path = convert_path_to_url(adjusted_path, remove_first_part=False)
        else:
            # Convert file path to URL format normally (remove first part for legacy compatibility)
            doc_path = convert_path_to_url(path, remove_first_part=True)

        # Combine base URL, folder URL path, and document path
        if folder_url_path:
            full_url = f"{base_url}{folder_url_path}/{doc_path}"
        else:
            full_url = f"{base_url}/{doc_path}"

        return full_url.replace("//", "/").replace(":/", "://")  # Fix double slashes

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

    def process_file(self, file_path: Path, package: str, folder_name: str = "") -> Optional[dict[str, Any]]:
        """Process a file and extract metadata."""
        try:
            if file_path.suffix == ".md":
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            elif file_path.suffix == ".ipynb":
                content = self.convert_notebook_to_markdown(file_path)
            elif file_path.suffix in [".rst", ".txt"]:
                # Handle RST and TXT files as plain text - no conversion needed
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                # Skip files that aren't markdown, notebooks, RST, or TXT
                logger.debug(f"Skipping unsupported file type: {file_path}")
                return None

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

            # Check if this is a reference document using configurable patterns
            is_reference = self._is_reference_document(file_path, package, folder_name)

            return {
                "id": doc_id,
                "title": title,
                "url": self._generate_doc_url(package, relative_path, folder_name),
                "package": package,
                "path": str(relative_path),
                "path_stem": file_path.stem,
                "description": description,
                "content": content,
                "is_reference": is_reference,
            }
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            return None

    async def extract_docs_from_repo(self, repo_path: Path, package: str, ctx: Context | None = None) -> list[dict[str, Any]]:
        """Extract documentation files from a repository."""
        docs = []
        repo_config = self.config.repositories[package]

        # Use the new folder structure with URL path mapping
        if isinstance(repo_config.folders, dict):
            folders = repo_config.folders
        else:
            # Convert list to dict with default FolderConfig
            folders = {name: FolderConfig() for name in repo_config.folders}

        files: set = set()
        await log_info(f"Processing {package} documentation files in {','.join(folders.keys())}", ctx)

        for folder_name in folders.keys():
            docs_folder: Path = repo_path / folder_name
            if docs_folder.exists():
                # Use index patterns from config
                for pattern in self.config.index_patterns:
                    files.update(docs_folder.glob(pattern))

        for file in files:
            if file.exists() and not file.is_dir():
                # Determine which folder this file belongs to
                folder_name = ""
                for fname in folders.keys():
                    folder_path = repo_path / fname
                    try:
                        file.relative_to(folder_path)
                        folder_name = fname
                        break
                    except ValueError:
                        continue

                doc_data = self.process_file(file, package, folder_name)
                if doc_data:
                    docs.append(doc_data)

        # Count reference vs regular documents
        reference_count = sum(1 for doc in docs if doc["is_reference"])
        regular_count = len(docs) - reference_count

        await log_info(f"  📄 {package}: {len(docs)} total documents ({regular_count} regular, {reference_count} reference guides)", ctx)

        return docs

    async def create_embeddings(self, docs: list[dict[str, Any]], ctx=None) -> np.ndarray:
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
        try:
            embeddings = self.embedding_model.encode(texts)
            embeddings = np.asarray(embeddings, dtype="float32")
        except Exception as e:
            await log_warning(f"Embedding creation failed: {e}", ctx)
            raise

        await log_info(f"Created {len(embeddings)} embeddings", ctx)
        return embeddings

    async def index_documentation(self, ctx: Context | None = None):
        """Indexes all documentation."""
        await log_info("Starting documentation indexing...", ctx)
        await log_info(f"📁 Repositories directory: {self.repos_dir}", ctx)
        await log_info(f"💾 Vector database location: {self.data_dir / 'chroma'}", ctx)

        all_docs = []

        # Clone/update repositories and extract documentation
        for repo_name, repo_config in self.config.repositories.items():
            await log_info(f"Processing {repo_name}...", ctx)

            repo_path = await self.clone_or_update_repo(repo_name, repo_config)
            if repo_path:
                docs = await self.extract_docs_from_repo(repo_path, repo_name, ctx)
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

        # Show detailed summary table
        await self._log_summary_table(ctx)

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
        filters: list[dict[str, Any]] = []
        if package:
            filters.append({"package": str(package)})
        filters.append({"path_stem": str(component)})
        filters.append({"is_reference": True})
        where_clause: dict[str, Any] = {"$and": filters} if len(filters) > 1 else filters[0]

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
        where_clause = {"package": str(package)} if package else None

        try:
            # Perform vector similarity search
            results = self.collection.query(query_texts=[query], n_results=max_results, where=where_clause)  # type: ignore[arg-type]

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
        filters: list[dict[str, str]] = [{"package": str(package)}, {"path": str(path)}]
        where_clause: dict[str, Any] = {"$and": filters}

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

    async def _log_summary_table(self, ctx: Context | None = None):
        """Log a summary table showing document counts by repository."""
        try:
            # Get all documents from the collection
            results = self.collection.get()

            if not results["metadatas"]:
                await log_info("No documents found in index", ctx)
                return

            # Count documents by package and type
            package_stats: dict[str, dict[str, int]] = {}
            for metadata in results["metadatas"]:
                package = str(metadata.get("package", "unknown"))
                is_reference = metadata.get("is_reference", False)

                if package not in package_stats:
                    package_stats[package] = {"total": 0, "regular": 0, "reference": 0}

                package_stats[package]["total"] += 1
                if is_reference:
                    package_stats[package]["reference"] += 1
                else:
                    package_stats[package]["regular"] += 1

            # Log summary table
            await log_info("", ctx)
            await log_info("📊 Document Summary by Repository:", ctx)
            await log_info("=" * 60, ctx)
            await log_info(f"{'Repository':<20} {'Total':<8} {'Regular':<8} {'Reference':<10}", ctx)
            await log_info("-" * 60, ctx)

            total_docs = 0
            total_regular = 0
            total_reference = 0

            for package in sorted(package_stats.keys()):
                stats = package_stats[package]
                await log_info(f"{package:<20} {stats['total']:<8} {stats['regular']:<8} {stats['reference']:<10}", ctx)
                total_docs += stats["total"]
                total_regular += stats["regular"]
                total_reference += stats["reference"]

            await log_info("-" * 60, ctx)
            await log_info(f"{'TOTAL':<20} {total_docs:<8} {total_regular:<8} {total_reference:<10}", ctx)
            await log_info("=" * 60, ctx)

        except Exception as e:
            await log_warning(f"Failed to generate summary table: {e}", ctx)


def main():
    """Update the DocumentationIndexer."""
    # Configure logging for the CLI
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])

    logger.info("🚀 HoloViz MCP Documentation Indexer")
    logger.info("=" * 50)

    async def run_indexer():
        indexer = DocumentationIndexer()
        logger.info(f"📁 Repository directory: {indexer.repos_dir}")
        logger.info(f"💾 Vector database: {indexer.data_dir / 'chroma'}")
        logger.info(f"🔧 Configured repositories: {len(indexer.config.repositories)}")
        logger.info("")

        await indexer.index_documentation()

        # Final summary
        count = indexer.collection.count()
        logger.info("")
        logger.info("=" * 50)
        logger.info("✅ Indexing completed successfully!")
        logger.info(f"📊 Total documents in database: {count}")
        logger.info("=" * 50)

    asyncio.run(run_indexer())


if __name__ == "__main__":
    main()
