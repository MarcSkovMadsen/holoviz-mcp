"""Skills core functions.

Pure Python functions for accessing skill/best-practice documents.
No MCP framework required. No heavy dependencies (chromadb, etc.).

Skills are stored in the Agent Skills standard format::

    skills/<name>/SKILL.md

Three sources are scanned with precedence (most specific wins):

1. **Project-level** — ``./skills/`` in cwd
2. **User-level** — ``~/.holoviz-mcp/skills/``
3. **Built-in** — Skills embedded in the package

Usage::

    from holoviz_mcp.core.skills import list_skills, get_skill

    names = list_skills()
    content = get_skill("panel")
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _skills_search_paths() -> list[Path]:
    """Return ordered skill directories (highest precedence first).

    Returns
    -------
    list[Path]
        [project, user, builtin] — first match wins for get_skill.
    """
    from holoviz_mcp.config.loader import get_config

    config = get_config()
    return [
        config.skills_dir("project"),
        config.skills_dir("user"),
        config.skills_dir("builtin"),
    ]


def _find_skill_file(skill_dir: Path, name: str) -> Path | None:
    """Locate the SKILL.md file for a given skill name within a directory.

    Supports both the new directory format (``<name>/SKILL.md``) and the
    legacy flat format (``<name>.md``) for backward compatibility.

    Parameters
    ----------
    skill_dir : Path
        Root skills directory to search.
    name : str
        Skill name (hyphenated, e.g. 'panel-material-ui').

    Returns
    -------
    Path | None
        Path to the skill file, or None if not found.
    """
    # New format: <name>/SKILL.md
    candidate = skill_dir / name / "SKILL.md"
    if candidate.exists():
        return candidate

    # Legacy flat format: <name>.md
    candidate = skill_dir / f"{name}.md"
    if candidate.exists():
        return candidate

    return None


def _scan_skills_in_dir(skill_dir: Path) -> dict[str, Path]:
    """Scan a directory for skills.

    Parameters
    ----------
    skill_dir : Path
        Root skills directory to scan.

    Returns
    -------
    dict[str, Path]
        Mapping from skill name to its SKILL.md path.
    """
    skills: dict[str, Path] = {}
    if not skill_dir.exists():
        return skills

    # New format: subdirectories with SKILL.md
    for sub in sorted(skill_dir.iterdir()):
        if sub.is_dir():
            skill_file = sub / "SKILL.md"
            if skill_file.exists():
                skills[sub.name] = skill_file

    # Legacy flat format: *.md files
    for md_file in sorted(skill_dir.glob("*.md")):
        name = md_file.stem
        if name not in skills:  # Don't override directory-format skills
            skills[name] = md_file

    return skills


def list_skills() -> list[dict[str, str]]:
    """List all available skills with their descriptions.

    Returns
    -------
    list[dict[str, str]]
        Sorted list of dicts with 'name' and 'description' keys.
        Names are in hyphenated format (e.g., 'panel', 'hvplot', 'panel-material-ui').
    """
    # Collect skills from all sources; earlier sources have higher precedence
    merged: dict[str, str] = {}

    # Iterate in reverse so higher-precedence sources overwrite lower ones
    for search_dir in reversed(_skills_search_paths()):
        for name, path in _scan_skills_in_dir(search_dir).items():
            merged[name] = _extract_description(path)

    return [{"name": name, "description": merged[name]} for name in sorted(merged)]


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
    # Convert underscored names to hyphenated for file lookup
    name = name.replace("_", "-")

    # Search in precedence order (project > user > builtin)
    for search_dir in _skills_search_paths():
        skill_file = _find_skill_file(search_dir, name)
        if skill_file is not None:
            return skill_file.read_text(encoding="utf-8")

    # If not found, raise error with helpful message
    available: set[str] = set()
    for search_dir in _skills_search_paths():
        available.update(_scan_skills_in_dir(search_dir).keys())

    available_str = ", ".join(sorted(available)) if available else "None"
    searched = [str(p) for p in _skills_search_paths()]
    raise FileNotFoundError(f"Skill file {name} not found. Available skills: {available_str}. Searched in: {searched}")


def _find_skill_dir(name: str) -> Path:
    """Locate the skill directory for a given skill name.

    Only supports the directory format (``<name>/SKILL.md``), not the
    legacy flat ``.md`` format — flat files have no supporting files.

    Parameters
    ----------
    name : str
        Skill name (hyphenated, e.g. 'panel-material-ui').

    Returns
    -------
    Path
        Path to the skill directory.

    Raises
    ------
    FileNotFoundError
        If no directory-format skill with the given name is found.
    """
    name = name.replace("_", "-")

    for search_dir in _skills_search_paths():
        candidate = search_dir / name
        if candidate.is_dir() and (candidate / "SKILL.md").exists():
            return candidate

    available: set[str] = set()
    for search_dir in _skills_search_paths():
        if search_dir.exists():
            for sub in search_dir.iterdir():
                if sub.is_dir() and (sub / "SKILL.md").exists():
                    available.add(sub.name)

    available_str = ", ".join(sorted(available)) if available else "None"
    raise FileNotFoundError(f"Skill directory '{name}' not found. Available skills: {available_str}")


def list_skill_files(name: str) -> list[dict[str, str | int]]:
    """List supporting files in a skill directory (excludes SKILL.md).

    Parameters
    ----------
    name : str
        Skill name (e.g. 'panel-custom-components').

    Returns
    -------
    list[dict[str, str | int]]
        List of dicts with 'path' (relative to skill dir) and 'size' (bytes).

    Raises
    ------
    FileNotFoundError
        If the skill directory is not found.
    """
    skill_dir = _find_skill_dir(name)
    files: list[dict[str, str | int]] = []
    for f in sorted(skill_dir.rglob("*")):
        if f.is_file() and f.name != "SKILL.md":
            rel = str(f.relative_to(skill_dir))
            files.append({"path": rel, "size": f.stat().st_size})
    return files


def get_skill_file(name: str, path: str) -> str:
    """Read a supporting file from a skill directory.

    Parameters
    ----------
    name : str
        Skill name (e.g. 'panel-custom-components').
    path : str
        Relative path within the skill directory (e.g. 'references/example.md').

    Returns
    -------
    str
        The file content as text.

    Raises
    ------
    FileNotFoundError
        If the skill or file is not found.
    ValueError
        If the path attempts directory traversal outside the skill directory.
    """
    skill_dir = _find_skill_dir(name)
    target = (skill_dir / path).resolve()

    # Path traversal protection
    if not str(target).startswith(str(skill_dir.resolve())):
        raise ValueError(f"Path traversal detected: '{path}' escapes skill directory")

    if not target.is_file():
        raise FileNotFoundError(f"File '{path}' not found in skill '{name}'")

    return target.read_text(encoding="utf-8")
