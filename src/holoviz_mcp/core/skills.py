"""Skills core functions.

Pure Python functions for accessing skill/best-practice documents.
No MCP framework required. No heavy dependencies (chromadb, etc.).

Usage::

    from holoviz_mcp.core.skills import list_skills, get_skill

    names = list_skills()
    content = get_skill("panel")
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def list_skills() -> list[dict[str, str]]:
    """List all available skills with their descriptions.

    Returns
    -------
    list[dict[str, str]]
        Sorted list of dicts with 'name' and 'description' keys.
        Names are in hyphenated format (e.g., 'panel', 'hvplot', 'panel-material-ui').
    """
    from holoviz_mcp.config.loader import get_config

    config = get_config()

    # Map name -> description (user dir overrides default)
    skills: dict[str, str] = {}
    search_paths = [
        config.skills_dir("default"),
        config.skills_dir("user"),
    ]

    for search_dir in search_paths:
        if search_dir.exists():
            for md_file in search_dir.glob("*.md"):
                name = md_file.stem
                description = _extract_description(md_file)
                skills[name] = description

    return [{"name": name, "description": skills[name]} for name in sorted(skills)]


def _extract_description(path: Path) -> str:
    """Extract the description field from a skill file's YAML frontmatter.

    Parameters
    ----------
    path : Path
        Path to the skill markdown file.

    Returns
    -------
    str
        The description, or empty string if not found.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""

    # Simple YAML frontmatter parser — avoids importing yaml
    if not text.startswith("---"):
        return ""
    end = text.find("---", 3)
    if end == -1:
        return ""
    frontmatter = text[3:end]
    for line in frontmatter.splitlines():
        stripped = line.strip()
        if stripped.startswith("description:"):
            return stripped[len("description:") :].strip().strip("\"'")
    return ""


def get_skill(name: str) -> str:
    """Get skill content by name.

    Parameters
    ----------
    name : str
        The skill name (e.g., 'panel', 'hvplot', 'panel-material-ui').

    Returns
    -------
    str
        The skill content in Markdown format.

    Raises
    ------
    FileNotFoundError
        If the skill is not found.
    """
    from holoviz_mcp.config.loader import get_config

    config = get_config()

    # Convert underscored names to hyphenated for file lookup
    skill_filename = name.replace("_", "-") + ".md"

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
    raise FileNotFoundError(f"Skill file {name} not found. Available skills: {available_str}. Searched in: {[str(p) for p in search_paths]}")
