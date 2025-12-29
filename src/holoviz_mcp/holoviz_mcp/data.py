"""Data handling for the HoloViz Documentation MCP server."""

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Any
from typing import Literal
from typing import Optional

import chromadb
import git
from chromadb.api.collection_configuration import CreateCollectionConfiguration
from fastmcp import Context
from nbconvert import MarkdownExporter
from nbformat import read as nbread
from pydantic import HttpUrl

from holoviz_mcp.config.loader import get_config
from holoviz_mcp.config.models import FolderConfig
from holoviz_mcp.config.models import GitRepository
from holoviz_mcp.holoviz_mcp.models import Document

logger = logging.getLogger(__name__)

# Todo: Describe DocumentApp
# Todo: Avoid overflow-x in SearchApp sidebar
# Todo: Add bokeh documentation to README extra config

_CROMA_CONFIGURATION = CreateCollectionConfiguration(
    hnsw={
        "space": "cosine",
        "ef_construction": 200,
        "ef_search": 200,
    }
)


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


def get_skill(name: str) -> str:
    """Get skill for using a project with LLMs.

    This function searches for skill resources in user and default directories,
    with user resources taking precedence over default ones.

    Args:
        name (str): The name of the skill to get.

    Returns
    -------
        str: A string containing the skill in Markdown format.

    Raises
    ------
        FileNotFoundError: If the specified skill is not found in either directory.
    """
    config = get_config()

    # Convert underscored names to hyphenated for file lookup
    skill_filename = name.replace("_", "-") + ".md"

    # Search in user directory first, then default directory
    search_paths = [
        config.skills_dir("user"),
        config.skills_dir("default"),
    ]

    for search_dir in search_paths:
        skills_file = search_dir / skill_filename
        if skills_file.exists():
            return skills_file.read_text(encoding="utf-8")

    # If not found, raise error with helpful message
    available_files = []
    for search_dir in search_paths:
        if search_dir.exists():
            available_files.extend([f.name for f in search_dir.glob("*.md")])

    available_str = ", ".join(set(available_files)) if available_files else "None"
    raise FileNotFoundError(f"Skill file {name} not found. " f"Available skills: {available_str}. " f"Searched in: {[str(p) for p in search_paths]}")


def list_skills() -> list[str]:
    """List all available skills.

    This function discovers available skills from both user and default directories,
    with user resources taking precedence over default ones.

    Returns
    -------
        list[str]: A list of the skills available.
            Names are returned in hyphenated format (e.g., "panel-material-ui").
    """
    config = get_config()

    # Collect available projects from both directories
    available_projects = set()

    search_paths = [
        config.skills_dir("user"),
        config.skills_dir("default"),
    ]

    for search_dir in search_paths:
        if search_dir.exists():
            for md_file in search_dir.glob("*.md"):
                available_projects.add(md_file.stem)

    return sorted(list(available_projects))


def remove_leading_number_sep_from_path(p: Path) -> Path:
    """Remove a leading number + underscore or hyphen from the last path component."""
    new_name = re.sub(r"^\d+[_-]", "", p.name)
    return p.with_name(new_name)


def convert_path_to_url(path: Path, remove_first_part: bool = True, url_transform: Literal["holoviz", "plotly", "datashader"] = "holoviz") -> str:
    """Convert a relative file path to a URL path.

    Converts file paths to web URLs by replacing file extensions with .html
    and optionally removing the first path component for legacy compatibility.

    Args:
        path: The file path to convert
        remove_first_part: Whether to remove the first path component (legacy compatibility)
        url_transform: How to transform the file path into a URL:

            - "holoviz": Replace file extension with .html (default)
            - "plotly": Replace file extension with / (e.g., filename.md -> filename/)
            - "datashader": Remove leading index and replace file extension with .html (e.g., 01_filename.md -> filename.html)

    Returns
    -------
        URL path with .html extension

    Examples
    --------
        >>> convert_path_to_url(Path("doc/getting_started.md"))
        "getting_started.html"
        >>> convert_path_to_url(Path("examples/reference/Button.ipynb"), False)
        "examples/reference/Button.html"
        >>> convert_path_to_url(Path("/doc/python/3d-axes.md"), False, "plotly")
        "/doc/python/3d-axes/"
        >>> convert_path_to_url(Path("/examples/user_guide/10_Performance.ipynb"), False, "datashader")
        "/examples/user_guide/Performance.html"
    """
    if url_transform in ["holoviz", "datashader"]:
        path = remove_leading_number_sep_from_path(path)

    # Convert path to URL format
    parts = list(path.parts)

    # Only remove first part if requested (for legacy compatibility)
    if remove_first_part and parts:
        parts.pop(0)

    # Reconstruct path and convert to string
    if parts:
        url_path = str(Path(*parts))
    else:
        url_path = ""

    # Replace file extensions with suffix
    if url_path:
        path_obj = Path(url_path)
        if url_transform == "plotly":
            url_path = str(path_obj.with_suffix(suffix="")) + "/"
            if url_path.endswith("index/"):
                url_path = url_path[: -len("index/")] + "/"
        else:
            url_path = str(path_obj.with_suffix(suffix=".html"))

    return url_path


class DocumentationIndexer:
    """Handles cloning, processing, and indexing of documentation."""

    def __init__(self, *, data_dir: Optional[Path] = None, repos_dir: Optional[Path] = None, vector_dir: Optional[Path] = None):
        """Initialize the DocumentationIndexer.

        Args:
            data_dir: Directory to store index data. Defaults to user config directory.
            repos_dir: Directory to store cloned repositories. Defaults to HOLOVIZ_MCP_REPOS_DIR.
            vector_dir: Directory to store vector database. Defaults to config.vector_dir
        """
        # Use unified config for default paths
        config = self._holoviz_mcp_config = get_config()

        self.data_dir = data_dir or config.user_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Use configurable repos directory for repository downloads
        self.repos_dir = repos_dir or config.repos_dir
        self.repos_dir.mkdir(parents=True, exist_ok=True)

        # Use configurable directory for vector database path
        vector_db_path = vector_dir or config.server.vector_db_path
        vector_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Disable ChromaDB telemetry based on config
        if not config.server.anonymized_telemetry:
            os.environ["ANONYMIZED_TELEMETRY"] = "False"

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=str(vector_db_path))
        self.collection = self.chroma_client.get_or_create_collection("holoviz_docs", configuration=_CROMA_CONFIGURATION)

        # Initialize notebook converter
        self.nb_exporter = MarkdownExporter()

        # Load documentation config from the centralized config system
        self.config = get_config().docs

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

    def _is_reference_document(self, file_path: Path, project: str, folder_name: str = "") -> bool:
        """Check if the document is a reference document using configurable patterns.

        Args:
            file_path: Full path to the file
            project: Project name
            folder_name: Name of the folder this file belongs to

        Returns
        -------
            bool: True if this is a reference document
        """
        repo_config = self.config.repositories[project]
        repo_path = self.repos_dir / project

        try:
            relative_path = file_path.relative_to(repo_path)

            # Check against configured reference patterns
            for pattern in repo_config.reference_patterns:
                if relative_path.match(pattern):
                    return True

            # Fallback to simple "reference" in path check
            return "reference" in relative_path.parts
        except (ValueError, KeyError):
            # If we can't determine relative path or no patterns configured, use simple fallback
            return "reference" in file_path.parts

    def _generate_doc_id(self, project: str, path: Path) -> str:
        """Generate a unique document ID from project and path."""
        readable_path = str(path).replace("/", "___").replace(".", "_")
        readable_id = f"{project}___{readable_path}"

        return readable_id

    def _generate_doc_url(self, project: str, path: Path, folder_name: str = "") -> str:
        """Generate documentation URL for a file.

        This method creates the final URL where the documentation can be accessed online.
        It handles folder URL mapping to ensure proper URL structure for different documentation layouts.

        Args:
            project: Name of the project/repository (e.g., "panel", "hvplot")
            path: Relative path to the file within the repository
            folder_name: Name of the folder containing the file (e.g., "examples/reference", "doc")
                       Used for URL path mapping when folders have custom URL structures

        Returns
        -------
            Complete URL to the documentation file

        Examples
        --------
            For Panel reference guides:
            - Input: project="panel", path="examples/reference/widgets/Button.ipynb", folder_name="examples/reference"
            - Output: "https://panel.holoviz.org/reference/widgets/Button.html"

            For regular documentation:
            - Input: project="panel", path="doc/getting_started.md", folder_name="doc"
            - Output: "https://panel.holoviz.org/getting_started.html"
        """
        repo_config = self.config.repositories[project]
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
            doc_path = convert_path_to_url(adjusted_path, remove_first_part=False, url_transform=repo_config.url_transform)
        else:
            # Convert file path to URL format normally (remove first part for legacy compatibility)
            doc_path = convert_path_to_url(path, remove_first_part=True, url_transform=repo_config.url_transform)

        # Combine base URL, folder URL path, and document path
        if folder_url_path:
            full_url = f"{base_url}{folder_url_path}/{doc_path}"
        else:
            full_url = f"{base_url}/{doc_path}"

        return full_url.replace("//", "/").replace(":/", "://")  # Fix double slashes

    @staticmethod
    def _to_title(fallback_filename: str = "") -> str:
        """Extract title from a filename or return a default title."""
        title = Path(fallback_filename).stem
        if "_" in title and title.split("_")[0].isdigit():
            title = title.split("_", 1)[-1]
        title = title.replace("_", " ").replace("-", " ").title()
        return title

    @classmethod
    def _extract_title_from_markdown(cls, content: str, fallback_filename: str = "") -> str:
        """Extract title from markdown content, with filename fallback."""
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("# "):
                # Return just the title text without the "# " prefix
                return line[2:].strip()
            if line.startswith("##"):
                break

        if fallback_filename:
            return cls._to_title(fallback_filename)

        return "No Title"

    @staticmethod
    def _extract_description_from_markdown(content: str, max_length=200) -> str:
        """Extract description from markdown content."""
        content = content.strip()

        # Plotly documents start with --- ... --- section. Skip the section
        if content.startswith("---"):
            content = content.split("---", 2)[-1].strip()

        lines = content.split("\n")
        clean_lines = []
        in_code_block = False

        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block or line.startswith(("#", "    ", "\t", "---", "___")):
                continue

            clean_lines.append(line)

        # Join lines and clean up
        clean_content = "\n".join(clean_lines).strip()

        # Remove extra whitespace and limit length
        clean_content = " ".join(clean_content.split())

        if len(clean_content) > max_length:
            clean_content = clean_content[:max_length].rsplit(" ", 1)[0]
        if not clean_content.endswith("."):
            clean_content += " ..."

        return clean_content

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

    @staticmethod
    def _to_source_url(file_path: Path, repo_config: GitRepository, raw: bool = False) -> str:
        """Generate source URL for a file based on repository configuration."""
        url = str(repo_config.url)
        branch = repo_config.branch or "main"
        if url.startswith("https://github.com") and url.endswith(".git"):
            url = url.replace("https://github.com/", "").replace(".git", "")
            project, repository = url.split("/")
            if raw:
                return f"https://raw.githubusercontent.com/{project}/{repository}/refs/heads/{branch}/{file_path}"

            return f"https://github.com/{project}/{repository}/blob/{branch}/{file_path}"
        if "dev.azure.com" in url:
            organisation = url.split("/")[3].split("@")[0]
            project = url.split("/")[-3]
            repo_name = url.split("/")[-1]
            if raw:
                return f"https://dev.azure.com/{organisation}/{project}/_apis/sourceProviders/TfsGit/filecontents?repository={repo_name}&path=/{file_path}&commitOrBranch={branch}&api-version=7.0"

            return f"https://dev.azure.com/{organisation}/{project}/_git/{repo_name}?path=/{file_path}&version=GB{branch}"

        raise ValueError(f"Unsupported repository URL format: {url}. Please provide a valid GitHub or Azure DevOps URL.")

    def process_file(self, file_path: Path, project: str, repo_config: GitRepository, folder_name: str = "") -> Optional[dict[str, Any]]:
        """Process a file and extract metadata."""
        try:
            if file_path.suffix == ".ipynb":
                content = self.convert_notebook_to_markdown(file_path)
            elif file_path.suffix in [".md", ".rst", ".txt"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                logger.debug(f"Skipping unsupported file type: {file_path}")
                return None

            title = self._extract_title_from_markdown(content, file_path.name)
            if not title:
                title = file_path.stem.replace("_", " ").title()

            description = self._extract_description_from_markdown(content)

            repo_path = self.repos_dir / project
            relative_path = file_path.relative_to(repo_path)

            doc_id = self._generate_doc_id(project, relative_path)

            is_reference = self._is_reference_document(file_path, project, folder_name)

            source_url = self._to_source_url(relative_path, repo_config)

            return {
                "id": doc_id,
                "title": title,
                "url": self._generate_doc_url(project, relative_path, folder_name),
                "project": project,
                "source_path": str(relative_path),
                "source_path_stem": file_path.stem,
                "source_url": source_url,
                "description": description,
                "content": content,
                "is_reference": is_reference,
            }
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            return None

    async def extract_docs_from_repo(self, repo_path: Path, project: str, ctx: Context | None = None) -> list[dict[str, Any]]:
        """Extract documentation files from a repository."""
        docs = []
        repo_config = self.config.repositories[project]

        # Use the new folder structure with URL path mapping
        if isinstance(repo_config.folders, dict):
            folders = repo_config.folders
        else:
            # Convert list to dict with default FolderConfig
            folders = {name: FolderConfig() for name in repo_config.folders}

        files: set = set()
        await log_info(f"Processing {project} documentation files in {','.join(folders.keys())}", ctx)

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

                doc_data = self.process_file(file, project, repo_config, folder_name)
                if doc_data:
                    docs.append(doc_data)

        # Count reference vs regular documents
        reference_count = sum(1 for doc in docs if doc["is_reference"])
        regular_count = len(docs) - reference_count

        await log_info(f"  📄 {project}: {len(docs)} total documents ({regular_count} regular, {reference_count} reference guides)", ctx)
        return docs

    async def index_documentation(self, ctx: Context | None = None):
        """Indexes all documentation."""
        await log_info("Starting documentation indexing...", ctx)

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
                self.collection = self.chroma_client.get_or_create_collection("holoviz_docs", configuration=_CROMA_CONFIGURATION)
            except Exception as e2:
                await log_exception(f"Failed to recreate collection: {e2}", ctx)
                raise

        # Add documents to ChromaDB
        await log_info(f"Adding {len(all_docs)} documents to index...", ctx)

        self.collection.add(
            documents=[doc["content"] for doc in all_docs],
            metadatas=[
                {
                    "title": doc["title"],
                    "url": doc["url"],
                    "project": doc["project"],
                    "source_path": doc["source_path"],
                    "source_path_stem": doc["source_path_stem"],
                    "source_url": doc["source_url"],
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
                    {
                        "id": doc_id,
                        "first_doc": seen_ids[doc_id],
                        "duplicate_doc": {"project": doc["project"], "source_path": doc["source_path"], "title": doc["title"]},
                    }
                )

                await log_warning(f"DUPLICATE ID FOUND: {doc_id}", ctx)
                await log_warning(f"  First document: {seen_ids[doc_id]['project']}/{seen_ids[doc_id]['path']} - {seen_ids[doc_id]['title']}", ctx)
                await log_warning(f"  Duplicate document: {doc['project']}/{doc['path']} - {doc['title']}", ctx)
            else:
                seen_ids[doc_id] = {"project": doc["project"], "source_path": doc["source_path"], "title": doc["title"]}

        if duplicates:
            error_msg = f"Found {len(duplicates)} duplicate document IDs"
            await log_exception(error_msg, ctx)

            # Log all duplicates for debugging
            for dup in duplicates:
                await log_exception(
                    f"Duplicate ID '{dup['id']}': {dup['first_doc']['project']}/{dup['first_doc']['path']} vs {dup['duplicate_doc']['project']}/{dup['duplicate_doc']['path']}",  # noqa: D401, E501
                    ctx,
                )

            raise ValueError(f"Document ID collision detected. {len(duplicates)} duplicate IDs found. Check logs for details.")

    async def search_get_reference_guide(self, component: str, project: Optional[str] = None, content: bool = True, ctx: Context | None = None) -> list[Document]:
        """Search for reference guides for a specific component."""
        await self.ensure_indexed()

        # Build search strategies
        filters: list[dict[str, Any]] = []
        if project:
            filters.append({"project": str(project)})
        filters.append({"source_path_stem": str(component)})
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

                    document = Document(
                        title=str(metadata["title"]),
                        url=HttpUrl(url_value),
                        project=str(metadata["project"]),
                        source_path=str(metadata["source_path"]),
                        source_url=HttpUrl(str(metadata.get("source_url", ""))),
                        description=str(metadata["description"]),
                        is_reference=bool(metadata["is_reference"]),
                        content=content_text,
                        relevance_score=relevance_score,
                    )

                    if project and document.project != project:
                        await log_exception(f"Project mismatch for component '{component}': expected '{project}', got '{document.project}'", ctx)
                    elif metadata["source_path_stem"] != component:
                        await log_exception(f"Path stem mismatch for component '{component}': expected '{component}', got '{metadata['source_path_stem']}'", ctx)
                    else:
                        all_results.append(document)
        return all_results

    async def search(self, query: str, project: Optional[str] = None, content: bool = True, max_results: int = 5, ctx: Context | None = None) -> list[Document]:
        """Search the documentation using semantic similarity."""
        await self.ensure_indexed(ctx=ctx)

        # Build where clause for filtering
        where_clause = {"project": str(project)} if project else None

        try:
            # Perform vector similarity search
            results = self.collection.query(query_texts=[query], n_results=max_results, where=where_clause)  # type: ignore[arg-type]

            documents = []
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
                                relevance_score = (2.0 - float(results["distances"][0][i])) / 2.0
                            except (ValueError, TypeError):
                                relevance_score = None

                        document = Document(
                            title=str(metadata["title"]),
                            url=HttpUrl(url_value),
                            project=str(metadata["project"]),
                            source_path=str(metadata["source_path"]),
                            source_url=HttpUrl(str(metadata.get("source_url", ""))),
                            description=str(metadata["description"]),
                            is_reference=bool(metadata["is_reference"]),
                            content=content_text,
                            relevance_score=relevance_score,
                        )
                        documents.append(document)
            return documents
        except Exception as e:
            raise e

    async def get_document(self, path: str, project: str, ctx: Context | None = None) -> Document:
        """Get a specific document."""
        await self.ensure_indexed(ctx=ctx)

        # Build where clause for filtering
        filters: list[dict[str, str]] = [{"project": str(project)}, {"source_path": str(path)}]
        where_clause: dict[str, Any] = {"$and": filters}

        # Perform vector similarity search
        results = self.collection.query(query_texts=[""], n_results=3, where=where_clause)

        documents = []
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

                    document = Document(
                        title=str(metadata["title"]),
                        url=HttpUrl(url_value),
                        project=str(metadata["project"]),
                        source_path=str(metadata["source_path"]),
                        source_url=HttpUrl(str(metadata.get("source_url", ""))),
                        description=str(metadata["description"]),
                        is_reference=bool(metadata["is_reference"]),
                        content=content_text,
                        relevance_score=relevance_score,
                    )
                    documents.append(document)

        if len(documents) > 1:
            raise ValueError(f"Multiple documents found for path '{path}' in project '{project}'. Please ensure unique paths.")
        elif len(documents) == 0:
            raise ValueError(f"No document found for path '{path}' in project '{project}'.")
        return documents[0]

    async def list_projects(self) -> list[str]:
        """List all available projects with documentation in the index.

        Returns
        -------
        list[str]: A list of project names that have documentation available.
                   Names are returned in hyphenated format (e.g., "panel-material-ui").
        """
        await self.ensure_indexed()

        try:
            # Get all documents from the collection to extract unique project names
            results = self.collection.get()

            if not results["metadatas"]:
                return []

            # Extract unique project names
            projects = set()
            for metadata in results["metadatas"]:
                project = metadata.get("project")
                if project:
                    # Convert underscored names to hyphenated format for consistency
                    project_name = str(project).replace("_", "-")
                    projects.add(project_name)

            # Return sorted list
            return sorted(projects)

        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []

    async def _log_summary_table(self, ctx: Context | None = None):
        """Log a summary table showing document counts by repository."""
        try:
            # Get all documents from the collection
            results = self.collection.get()

            if not results["metadatas"]:
                await log_info("No documents found in index", ctx)
                return

            # Count documents by project and type
            project_stats: dict[str, dict[str, int]] = {}
            for metadata in results["metadatas"]:
                project = str(metadata.get("project", "unknown"))
                is_reference = metadata.get("is_reference", False)

                if project not in project_stats:
                    project_stats[project] = {"total": 0, "regular": 0, "reference": 0}

                project_stats[project]["total"] += 1
                if is_reference:
                    project_stats[project]["reference"] += 1
                else:
                    project_stats[project]["regular"] += 1

            # Log summary table
            await log_info("", ctx)
            await log_info("📊 Document Summary by Repository:", ctx)
            await log_info("=" * 60, ctx)
            await log_info(f"{'Repository':<20} {'Total':<8} {'Regular':<8} {'Reference':<10}", ctx)
            await log_info("-" * 60, ctx)

            total_docs = 0
            total_regular = 0
            total_reference = 0

            for project in sorted(project_stats.keys()):
                stats = project_stats[project]
                await log_info(f"{project:<20} {stats['total']:<8} {stats['regular']:<8} {stats['reference']:<10}", ctx)
                total_docs += stats["total"]
                total_regular += stats["regular"]
                total_reference += stats["reference"]

            await log_info("-" * 60, ctx)
            await log_info(f"{'TOTAL':<20} {total_docs:<8} {total_regular:<8} {total_reference:<10}", ctx)
            await log_info("=" * 60, ctx)

        except Exception as e:
            await log_warning(f"Failed to generate summary table: {e}", ctx)

    def run(self):
        """Update the DocumentationIndexer."""
        # Configure logging for the CLI
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])

        logger.info("🚀 HoloViz MCP Documentation Indexer")
        logger.info("=" * 50)

        async def run_indexer(indexer=self):
            logger.info(f"📦 Default config: {indexer._holoviz_mcp_config.config_file_path(location='default')}")
            logger.info(f"🏠 User config: {indexer._holoviz_mcp_config.config_file_path(location='user')}")
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


def main():
    """Run the documentation indexer."""
    DocumentationIndexer().run()


if __name__ == "__main__":
    main()
