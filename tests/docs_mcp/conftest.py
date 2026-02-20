"""Test fixtures for documentation MCP tests.

Configures a minimal 3-repo test index (panel, hvplot, panel-material-ui)
instead of the full production index, reducing test time from 5-15 minutes
to 1-3 minutes. Uses a fixed path (~/.holoviz-mcp-test/) for CI caching.
"""

import asyncio
import logging
import os
from pathlib import Path

import pytest

from holoviz_mcp.config.loader import ConfigLoader
from holoviz_mcp.config.models import HoloVizMCPConfig

logger = logging.getLogger(__name__)

# Fixed test directory (not tmp_path) so CI can cache the index across runs.
# Override with HOLOVIZ_MCP_TEST_DIR for custom locations or concurrent sessions.
TEST_DATA_DIR = Path(os.environ["HOLOVIZ_MCP_TEST_DIR"]) if "HOLOVIZ_MCP_TEST_DIR" in os.environ else Path.home() / ".holoviz-mcp-test"

# Only these projects are needed by test assertions
TEST_PROJECTS = ("panel", "hvplot", "panel-material-ui")


def _build_test_config():
    """Build a HoloVizMCPConfig with only 3 repos and test-specific paths."""
    # Load ONLY the package default config — skip user config entirely so
    # user-configured repos don't leak into the test index.
    env = HoloVizMCPConfig(user_dir=TEST_DATA_DIR / ".no_user_config")
    loader = ConfigLoader(config=env)
    default_config = loader.load_config()

    # Validate that all expected test repos exist in the default config
    missing = set(TEST_PROJECTS) - set(default_config.docs.repositories)
    if missing:
        raise RuntimeError(f"TEST_PROJECTS not found in default config: {missing}")
    test_repos = {name: default_config.docs.repositories[name] for name in TEST_PROJECTS}

    test_docs = default_config.docs.model_copy(update={"repositories": test_repos})
    test_server = default_config.server.model_copy(update={"vector_db_path": TEST_DATA_DIR / "vector_db" / "chroma"})

    return default_config.model_copy(
        update={
            "docs": test_docs,
            "server": test_server,
            "user_dir": TEST_DATA_DIR,
            "repos_dir": TEST_DATA_DIR / "repos",
        }
    )


@pytest.fixture(scope="package", autouse=True)
def docs_test_config():
    """Patch get_config() to use a minimal 3-repo test config for the session.

    This fixture:
    1. Builds a config with only panel, hvplot, panel-material-ui
    2. Redirects all data paths to ~/.holoviz-mcp-test/
    3. Resets the server's _indexer singleton so it picks up the test config
    4. Pre-builds the index if it doesn't exist (avoids a deadlock in
       ensure_indexed when called from within db_lock in search/list_projects)

    Since ~/.holoviz-mcp-test/ persists between runs, subsequent runs skip indexing.
    """
    import holoviz_mcp.config.loader as loader_module
    import holoviz_mcp.holoviz_mcp.server as server_module

    config = _build_test_config()

    # Pre-load the config into the loader (bypasses file loading and env overrides)
    test_loader = ConfigLoader()
    test_loader._loaded_config = config

    # Save originals
    original_loader = loader_module._config_loader
    original_indexer = server_module._indexer

    # Patch global config loader and reset indexer singleton
    loader_module._config_loader = test_loader
    server_module._indexer = None

    logger.info(
        "Docs test config: %d repos (%s), vector_db=%s",
        len(config.docs.repositories),
        ", ".join(config.docs.repositories.keys()),
        config.server.vector_db_path,
    )

    # Pre-build the index if it doesn't exist.  This MUST happen here (outside
    # any db_lock) because the MCP tools call ensure_indexed() from within
    # db_lock, and index_documentation() also acquires db_lock — causing a
    # deadlock when the index is empty.  By building here, ensure_indexed()
    # always finds is_indexed()==True and skips the build.
    indexer = server_module.get_indexer()
    if not indexer.is_indexed():
        logger.info("Building test index for %s ...", ", ".join(TEST_PROJECTS))
        asyncio.run(indexer.ensure_indexed())
        # Reset the db_lock so tests create a fresh one in their event loop
        indexer._db_lock = None

    yield config

    # Restore originals
    loader_module._config_loader = original_loader
    server_module._indexer = original_indexer
