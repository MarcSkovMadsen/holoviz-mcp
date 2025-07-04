"""Holds fixtures and configuration for the test suite."""

import pytest
from panel.config import panel_extension
from panel.io.reload import _local_modules
from panel.io.reload import _modules
from panel.io.reload import _watched_files
from panel.io.state import state
from panel.theme import Design

optional_markers = {
    "ui": {
        "help": "Runs UI related tests",
        "marker-descr": "UI test marker",
        "skip-reason": "Test only runs with the --ui option.",
    },
}


def pytest_addoption(parser):
    """Add extra command line options."""
    for marker, info in optional_markers.items():
        parser.addoption(f"--{marker}", action="store_true", default=False, help=info["help"])
    parser.addoption("--repeat", action="store", help="Number of times to repeat each test")


def pytest_configure(config):
    """Add extra markers."""
    for marker, info in optional_markers.items():
        config.addinivalue_line("markers", "{}: {}".format(marker, info["marker-descr"]))

    config.addinivalue_line("markers", "internet: mark test as requiring an internet connection")


@pytest.fixture(autouse=True)
def module_cleanup():
    """Cleanup Panel extensions after each test."""
    from bokeh.core.has_props import _default_resolver
    from panel.reactive import ReactiveMetaBase

    to_reset = list(panel_extension._imports.values())
    _default_resolver._known_models = {
        name: model for name, model in _default_resolver._known_models.items() if not any(model.__module__.startswith(tr) for tr in to_reset)
    }
    ReactiveMetaBase._loaded_extensions = set()


@pytest.fixture(autouse=True)
def server_cleanup():
    """Clean up server state after each test."""
    try:
        yield
    finally:
        state.reset()
        _watched_files.clear()
        _modules.clear()
        _local_modules.clear()


@pytest.fixture(autouse=True)
def cache_cleanup():
    """Clean up cache."""
    state.clear_caches()
    Design._resolve_modifiers.cache_clear()
    Design._cache.clear()
