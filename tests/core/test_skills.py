"""Tests for holoviz_mcp.core.skills — Skills core functions."""

import pytest

from holoviz_mcp.core.skills import get_skill
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
