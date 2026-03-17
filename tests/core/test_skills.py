"""Tests for holoviz_mcp.core.skills — Skills core functions."""

from pathlib import Path

import pytest

from holoviz_mcp.core.skills import get_skill
from holoviz_mcp.core.skills import get_skill_file
from holoviz_mcp.core.skills import list_skill_files
from holoviz_mcp.core.skills import list_skills


class TestListSkills:
    def test_returns_list(self):
        result = list_skills()
        assert isinstance(result, list)

    def test_contains_known_skills(self):
        result = list_skills()
        names = [s["name"] for s in result]
        assert "panel" in names
        assert "hvplot" in names

    def test_contains_routing_skill(self):
        result = list_skills()
        names = [s["name"] for s in result]
        assert "developing-with-holoviz-tools" in names

    def test_returns_dicts_with_name_and_description(self):
        result = list_skills()
        for entry in result:
            assert isinstance(entry, dict)
            assert "name" in entry
            assert "description" in entry
            assert isinstance(entry["name"], str)
            assert isinstance(entry["description"], str)


class TestGetSkill:
    def test_returns_string(self):
        result = get_skill("panel")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_panel_skill_content(self):
        result = get_skill("panel")
        assert "panel" in result.lower() or "Panel" in result

    def test_hvplot_skill_content(self):
        result = get_skill("hvplot")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_nonexistent_skill_raises(self):
        with pytest.raises(FileNotFoundError):
            get_skill("nonexistent-skill-xyz-12345")

    def test_routing_skill_content(self):
        result = get_skill("developing-with-holoviz-tools")
        assert isinstance(result, str)
        assert "developing-with-holoviz-tools" in result.lower() or "HoloViz" in result


@pytest.fixture()
def skill_with_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Create a temporary skill directory with supporting files."""
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "test-skill"
    skill_dir.mkdir(parents=True)

    (skill_dir / "SKILL.md").write_text("---\ndescription: Test skill\n---\n# Test Skill\n")
    refs_dir = skill_dir / "references"
    refs_dir.mkdir()
    (refs_dir / "example.md").write_text("# Example reference\n")
    (refs_dir / "data.txt").write_text("some data")

    monkeypatch.setattr(
        "holoviz_mcp.core.skills._skills_search_paths",
        lambda: [skills_dir],
    )
    return skills_dir


class TestListSkillFiles:
    def test_routing_skill_has_no_supporting_files_dir(self):
        result = list_skill_files("developing-with-holoviz-tools")
        assert result == []

    def test_returns_list(self, skill_with_files: Path):
        result = list_skill_files("test-skill")
        assert isinstance(result, list)

    def test_excludes_skill_md(self, skill_with_files: Path):
        result = list_skill_files("test-skill")
        paths = [f["path"] for f in result]
        assert "SKILL.md" not in paths

    def test_includes_supporting_files(self, skill_with_files: Path):
        result = list_skill_files("test-skill")
        paths = [f["path"] for f in result]
        assert "references/example.md" in paths
        assert "references/data.txt" in paths

    def test_returns_size(self, skill_with_files: Path):
        result = list_skill_files("test-skill")
        for f in result:
            assert "size" in f
            assert isinstance(f["size"], int)
            assert f["size"] > 0

    def test_empty_for_skill_without_supporting_files(self, skill_with_files: Path):
        # Create a skill with only SKILL.md
        bare_dir = skill_with_files / "bare-skill"
        bare_dir.mkdir()
        (bare_dir / "SKILL.md").write_text("# Bare\n")

        result = list_skill_files("bare-skill")
        assert result == []

    def test_nonexistent_skill_raises(self, skill_with_files: Path):
        with pytest.raises(FileNotFoundError):
            list_skill_files("nonexistent-skill-xyz-12345")


class TestGetSkillFile:
    def test_reads_content(self, skill_with_files: Path):
        content = get_skill_file("test-skill", "references/example.md")
        assert content == "# Example reference\n"

    def test_nonexistent_skill_raises(self, skill_with_files: Path):
        with pytest.raises(FileNotFoundError):
            get_skill_file("nonexistent-skill-xyz-12345", "any.md")

    def test_nonexistent_file_raises(self, skill_with_files: Path):
        with pytest.raises(FileNotFoundError):
            get_skill_file("test-skill", "no-such-file.md")

    def test_path_traversal_parent(self, skill_with_files: Path):
        with pytest.raises(ValueError, match="Path traversal"):
            get_skill_file("test-skill", "../../etc/passwd")

    def test_path_traversal_sibling_skill(self, skill_with_files: Path):
        # Create a sibling skill to attempt traversal to
        sibling = skill_with_files / "other-skill"
        sibling.mkdir()
        (sibling / "SKILL.md").write_text("# Other\n")

        with pytest.raises(ValueError, match="Path traversal"):
            get_skill_file("test-skill", "../other-skill/SKILL.md")


@pytest.fixture()
def context_dir_skill(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture that mirrors the built-in developing-with-holoviz-tools layout.

    Structure::

        context/
            SKILL.md         <- routing skill named "context"
            skills/
                sub-skill/
                    SKILL.md
    """
    context_dir = tmp_path / "context"
    (context_dir).mkdir()
    (context_dir / "SKILL.md").write_text("---\nname: context\ndescription: Routing skill\n---\n# Routing\n")
    sub_dir = context_dir / "skills" / "sub-skill"
    sub_dir.mkdir(parents=True)
    (sub_dir / "SKILL.md").write_text("---\nname: sub-skill\ndescription: A sub-skill\n---\n# Sub-skill\n")

    monkeypatch.setattr(
        "holoviz_mcp.core.skills._skills_search_paths",
        lambda: [context_dir],
    )
    return context_dir


class TestContextDirectoryLayout:
    """Verify the two-level developing-with-holoviz-tools layout is correctly scanned."""

    def test_routing_skill_is_found(self, context_dir_skill: Path):
        names = [s["name"] for s in list_skills()]
        assert "context" in names

    def test_sub_skill_is_found(self, context_dir_skill: Path):
        names = [s["name"] for s in list_skills()]
        assert "sub-skill" in names

    def test_routing_skill_content(self, context_dir_skill: Path):
        content = get_skill("context")
        assert "Routing" in content

    def test_sub_skill_content(self, context_dir_skill: Path):
        content = get_skill("sub-skill")
        assert "Sub-skill" in content
