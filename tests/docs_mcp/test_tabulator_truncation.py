"""Tests for context-aware content truncation with Panel Tabulator reference guide.

This test suite validates that the context-aware truncation feature correctly
returns relevant sections of the Panel Tabulator reference guide when users
ask questions about Tabulator, testing with varying max_content_chars lengths
from 300 to 3000 characters.

The Panel Tabulator reference guide is a comprehensive document (~18,000 lines)
covering 70+ parameters, 40+ code examples, and 20+ major sections.
"""

import pytest

from holoviz_mcp.holoviz_mcp.data import DocumentationIndexer
from holoviz_mcp.holoviz_mcp.data import truncate_content

pytestmark = pytest.mark.integration


class TestTabulatorTruncation:
    """Test suite for Tabulator reference guide context-aware truncation."""

    @pytest.fixture
    async def tabulator_content(self, indexer):
        """Get full Tabulator reference guide content."""
        results = await indexer.search_get_reference_guide(component="Tabulator", project="panel", content=True)
        assert len(results) > 0, "Tabulator reference guide not found"
        return results[0].content or ""

    @pytest.fixture
    async def indexer(self):
        """Create and ensure indexed DocumentationIndexer instance."""
        indexer = DocumentationIndexer()
        await indexer.ensure_indexed()
        return indexer

    def verify_keywords(self, content: str, keywords: list[str], min_matches: int = 1) -> tuple[bool, list[str]]:
        """Verify that content contains minimum number of keywords.

        Returns
        -------
            Tuple of (passed, matched_keywords)
        """
        matched = [kw for kw in keywords if kw.lower() in content.lower()]
        return len(matched) >= min_matches, matched

    def verify_length_compliance(self, content: str, max_chars: int, tolerance: float = 0.1) -> bool:
        """Verify content length is within acceptable tolerance of max_chars."""
        return len(content) <= max_chars * (1 + tolerance)

    def log_test_result(
        self,
        test_name: str,
        query: str,
        max_chars: int,
        content: str,
        keywords: list[str],
        matched_keywords: list[str],
    ):
        """Log test result details for manual inspection."""
        print(f"\n{'=' * 80}")  # noqa: T201
        print(f"Test: {test_name}")  # noqa: T201
        print(f"Query: {query}")  # noqa: T201
        print(f"Max chars: {max_chars}")  # noqa: T201
        print(f"Actual length: {len(content)}")  # noqa: T201
        print(f"Keywords searched: {keywords}")  # noqa: T201
        print(f"Keywords matched: {matched_keywords}")  # noqa: T201
        print(f"Excerpt preview (first 400 chars):\n{'-' * 80}")  # noqa: T201
        print(content[:400])  # noqa: T201
        print(f"{'-' * 80}\n")  # noqa: T201

    @pytest.mark.asyncio
    async def test_tabulator_case_01_pagination_small(self, tabulator_content):
        """Test Case 1: Pagination with small truncation (300 chars).

        Tests that small excerpts can find and highlight pagination content
        in the middle of the document without just returning the header.
        """
        query = "pagination local remote page_size"
        max_content_chars = 300
        keywords = ["pagination", "page", "local", "remote"]

        # Apply truncation with query
        content = truncate_content(tabulator_content, max_content_chars, query=query)

        assert content is not None, "Truncated content should not be None"
        assert self.verify_length_compliance(content, max_content_chars), f"Content too long: {len(content)} > {max_content_chars * 1.1}"

        passed, matched = self.verify_keywords(content, keywords)
        assert passed, f"Content should contain at least one of: {keywords}. Found: {matched}"

        self.log_test_result("Pagination (small)", query, max_content_chars, content, keywords, matched)

    @pytest.mark.asyncio
    async def test_tabulator_case_02_editors_medium_small(self, tabulator_content):
        """Test Case 2: Dropdown editors with medium-small truncation (500 chars).

        Tests finding Editors/Editing section with SelectEditor examples.
        """
        query = "editors CheckboxEditor NumberEditor SelectEditor bokeh"
        max_content_chars = 500
        keywords = ["editor", "CheckboxEditor", "NumberEditor", "SelectEditor"]

        content = truncate_content(tabulator_content, max_content_chars, query=query)

        assert content is not None
        assert self.verify_length_compliance(content, max_content_chars), f"Content too long: {len(content)} > {max_content_chars * 1.1}"

        passed, matched = self.verify_keywords(content, keywords)
        assert passed, f"Content should contain at least one of: {keywords}. Found: {matched}"

        self.log_test_result("Editors (medium-small)", query, max_content_chars, content, keywords, matched)

    @pytest.mark.asyncio
    async def test_tabulator_case_03_formatters_medium(self, tabulator_content):
        """Test Case 3: Progress bar formatters with medium truncation (800 chars).

        Tests finding Formatters section with progress bar examples and code snippets.
        """
        query = "formatters CellFormatter NumberFormatter BooleanFormatter bokeh"
        max_content_chars = 800
        keywords = ["formatter", "CellFormatter", "NumberFormatter", "BooleanFormatter"]

        content = truncate_content(tabulator_content, max_content_chars, query=query)

        assert content is not None
        assert self.verify_length_compliance(content, max_content_chars), f"Content too long: {len(content)} > {max_content_chars * 1.1}"

        passed, matched = self.verify_keywords(content, keywords)
        assert passed, f"Content should contain at least one of: {keywords}. Found: {matched}"

        self.log_test_result("Formatters (medium)", query, max_content_chars, content, keywords, matched)

    @pytest.mark.asyncio
    async def test_tabulator_case_04_styling_medium_large(self, tabulator_content):
        """Test Case 4: Conditional styling with medium-large truncation (1000 chars).

        Tests finding Styling section with Pandas styling API integration examples.
        """
        query = "background_gradient text_gradient styling highlight gradients"
        max_content_chars = 1000
        keywords = ["style", "styling", "background", "gradient"]

        content = truncate_content(tabulator_content, max_content_chars, query=query)

        assert content is not None
        assert self.verify_length_compliance(content, max_content_chars), f"Content too long: {len(content)} > {max_content_chars * 1.1}"

        passed, matched = self.verify_keywords(content, keywords)
        assert passed, f"Content should contain at least one of: {keywords}. Found: {matched}"

        self.log_test_result("Styling (medium-large)", query, max_content_chars, content, keywords, matched)

    @pytest.mark.asyncio
    async def test_tabulator_case_05_selection_medium(self, tabulator_content):
        """Test Case 5: Checkbox selection with medium truncation (700 chars).

        Tests finding Selection/Click section with selectable checkbox modes.
        """
        query = "selectable checkbox toggle checkbox-single selection selected"
        max_content_chars = 700
        keywords = ["selectable", "checkbox", "toggle", "selection"]

        content = truncate_content(tabulator_content, max_content_chars, query=query)

        assert content is not None
        assert self.verify_length_compliance(content, max_content_chars), f"Content too long: {len(content)} > {max_content_chars * 1.1}"

        passed, matched = self.verify_keywords(content, keywords)
        assert passed, f"Content should contain at least one of: {keywords}. Found: {matched}"

        self.log_test_result("Selection (medium)", query, max_content_chars, content, keywords, matched)

    @pytest.mark.asyncio
    async def test_tabulator_case_06_frozen_columns_small_medium(self, tabulator_content):
        """Test Case 6: Frozen columns with small-medium truncation (600 chars).

        Tests finding Freezing Rows and Columns section with frozen_columns usage.
        """
        query = "frozen freeze column left right pinned fixed"
        max_content_chars = 600
        keywords = ["frozen", "freeze", "column", "left", "right"]

        content = truncate_content(tabulator_content, max_content_chars, query=query)

        assert content is not None
        assert self.verify_length_compliance(content, max_content_chars), f"Content too long: {len(content)} > {max_content_chars * 1.1}"

        passed, matched = self.verify_keywords(content, keywords)
        assert passed, f"Content should contain at least one of: {keywords}. Found: {matched}"

        self.log_test_result("Frozen columns (small-medium)", query, max_content_chars, content, keywords, matched)

    @pytest.mark.asyncio
    async def test_tabulator_case_07_filtering_large(self, tabulator_content):
        """Test Case 7: Dynamic filters with large truncation (1500 chars).

        Tests finding Filtering section with add_filter method and widget examples.
        """
        query = "filter add_filter widget RangeSlider MultiSelect filtering current_view"
        max_content_chars = 1500
        keywords = ["filter", "add_filter", "widget", "RangeSlider", "MultiSelect"]

        content = truncate_content(tabulator_content, max_content_chars, query=query)

        assert content is not None
        assert self.verify_length_compliance(content, max_content_chars), f"Content too long: {len(content)} > {max_content_chars * 1.1}"

        passed, matched = self.verify_keywords(content, keywords, min_matches=1)
        assert passed, f"Content should contain at least one of: {keywords}. Found: {matched}"

        self.log_test_result("Filtering (large)", query, max_content_chars, content, keywords, matched)

    @pytest.mark.asyncio
    async def test_tabulator_case_08_streaming_medium(self, tabulator_content):
        """Test Case 8: Data streaming with medium truncation (900 chars).

        Tests finding Streaming section with stream() method and follow parameter.
        """
        query = "stream follow rollover patch reset_index add_periodic_callback"
        max_content_chars = 900
        keywords = ["stream", "follow", "rollover", "patch"]

        content = truncate_content(tabulator_content, max_content_chars, query=query)

        assert content is not None
        assert self.verify_length_compliance(content, max_content_chars), f"Content too long: {len(content)} > {max_content_chars * 1.1}"

        passed, matched = self.verify_keywords(content, keywords)
        assert passed, f"Content should contain at least one of: {keywords}. Found: {matched}"

        self.log_test_result("Streaming (medium)", query, max_content_chars, content, keywords, matched)

    @pytest.mark.asyncio
    async def test_tabulator_case_09_hierarchical_large(self, tabulator_content):
        """Test Case 9: Hierarchical multi-index with large truncation (2000 chars).

        Tests finding Hierarchical Multi-Index section with aggregators configuration.
        """
        query = "hierarchical multi-index aggregator aggregation grouping nested"
        max_content_chars = 2000
        keywords = ["hierarchical", "multi-index", "aggregator", "aggregation"]

        content = truncate_content(tabulator_content, max_content_chars, query=query)

        assert content is not None
        assert self.verify_length_compliance(content, max_content_chars), f"Content too long: {len(content)} > {max_content_chars * 1.1}"

        passed, matched = self.verify_keywords(content, keywords)
        assert passed, f"Content should contain at least one of: {keywords}. Found: {matched}"

        self.log_test_result("Hierarchical (large)", query, max_content_chars, content, keywords, matched)

    @pytest.mark.asyncio
    async def test_tabulator_case_10_row_content_very_large(self, tabulator_content):
        """Test Case 10: Expandable row details with very large truncation (3000 chars).

        Tests finding Row Contents section with row_content function and embed_content.
        """
        query = "row_content expandable embed_content expanded details accordion"
        max_content_chars = 3000
        keywords = ["row_content", "expandable", "embed_content", "expanded", "details"]

        content = truncate_content(tabulator_content, max_content_chars, query=query)

        assert content is not None
        assert self.verify_length_compliance(content, max_content_chars), f"Content too long: {len(content)} > {max_content_chars * 1.1}"

        passed, matched = self.verify_keywords(content, keywords)
        assert passed, f"Content should contain at least one of: {keywords}. Found: {matched}"

        self.log_test_result("Row content (very large)", query, max_content_chars, content, keywords, matched)


@pytest.mark.asyncio
async def test_tabulator_integration_all_cases():
    """Integration test running all test cases sequentially with summary report."""
    indexer = DocumentationIndexer()
    await indexer.ensure_indexed()

    # Get full Tabulator content once
    results = await indexer.search_get_reference_guide(component="Tabulator", project="panel", content=True)
    assert len(results) > 0, "Tabulator reference guide not found"
    tabulator_content = results[0].content or ""

    test_cases = [
        ("pagination local remote page_size", 300, ["pagination", "page", "local", "remote"]),
        ("editors CheckboxEditor NumberEditor SelectEditor bokeh", 500, ["editor", "CheckboxEditor", "NumberEditor"]),
        ("formatters CellFormatter NumberFormatter BooleanFormatter bokeh", 800, ["formatter", "CellFormatter", "NumberFormatter"]),
        ("background_gradient text_gradient styling highlight gradients", 1000, ["style", "styling", "background", "gradient"]),
        ("selectable checkbox toggle checkbox-single selection selected", 700, ["selectable", "checkbox", "toggle"]),
        ("frozen freeze column left right pinned fixed", 600, ["frozen", "freeze", "column"]),
        ("filter add_filter widget RangeSlider MultiSelect filtering", 1500, ["filter", "add_filter", "widget"]),
        ("stream follow rollover patch reset_index add_periodic_callback", 900, ["stream", "follow", "rollover"]),
        ("hierarchical multi-index aggregator aggregation grouping", 2000, ["hierarchical", "multi-index", "aggregator"]),
        ("row_content expandable embed_content expanded details", 3000, ["row_content", "expandable", "embed_content"]),
    ]

    print("\n" + "=" * 100)  # noqa: T201
    print("TABULATOR TRUNCATION INTEGRATION TEST")  # noqa: T201
    print("=" * 100)  # noqa: T201
    print(f"Full Tabulator doc length: {len(tabulator_content)} characters")  # noqa: T201

    passed_tests = 0
    failed_tests = 0

    for i, (query, max_chars, keywords) in enumerate(test_cases, 1):
        print(f"\nTest Case {i}/10:")  # noqa: T201
        print(f"Query: {query}")  # noqa: T201
        print(f"Max chars: {max_chars}")  # noqa: T201

        try:
            content = truncate_content(tabulator_content, max_chars, query=query)

            if not content:
                print("❌ FAIL: No content returned")  # noqa: T201
                failed_tests += 1
                continue

            actual_length = len(content)

            # Check length compliance
            max_allowed = int(max_chars * 1.1)
            length_ok = actual_length <= max_allowed

            # Check keyword presence
            matched_keywords = [kw for kw in keywords if kw.lower() in content.lower()]
            keywords_ok = len(matched_keywords) > 0

            # Overall pass/fail
            test_passed = length_ok and keywords_ok

            if test_passed:
                print("✅ PASS")  # noqa: T201
                passed_tests += 1
            else:
                print("❌ FAIL")  # noqa: T201
                failed_tests += 1

            print(f"  Length: {actual_length}/{max_chars} {'✅' if length_ok else '❌'}")  # noqa: T201
            print(f"  Keywords matched: {matched_keywords} {'✅' if keywords_ok else '❌'}")  # noqa: T201
            print("  Preview (first 200 chars):")  # noqa: T201
            print(f"  {'-' * 80}")  # noqa: T201
            print(f"  {content[:200]}")  # noqa: T201
            print(f"  {'-' * 80}")  # noqa: T201

        except Exception as e:
            print(f"❌ FAIL: Exception - {e}")  # noqa: T201
            failed_tests += 1

    print("\n" + "=" * 100)  # noqa: T201
    print(f"INTEGRATION TEST COMPLETE: {passed_tests}/10 passed, {failed_tests}/10 failed")  # noqa: T201
    print("=" * 100 + "\n")  # noqa: T201

    # Assert overall success
    assert failed_tests == 0, f"{failed_tests} test case(s) failed"
