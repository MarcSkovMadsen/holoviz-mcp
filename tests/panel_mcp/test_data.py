import pytest

from holoviz_mcp.panel_mcp.data import to_proxy_url

TEST_CASES = [
    # Basic cases
    ("http://localhost:5007", "https://some-path/proxy/5007/"),
    ("http://localhost:5007/", "https://some-path/proxy/5007/"),
    ("http://localhost:5007/some/path", "https://some-path/proxy/5007/some/path"),
    ("http://localhost:5007/some/path?query=1", "https://some-path/proxy/5007/some/path?query=1"),
    ("https://example.com", "https://example.com"),  # Should not change
    # IP address
    ("http://127.0.0.1:5007", "https://some-path/proxy/5007/"),
    ("http://127.0.0.1:5007/", "https://some-path/proxy/5007/"),
    ("http://127.0.0.1:5007/path", "https://some-path/proxy/5007/path"),
    # Different port numbers
    ("http://localhost:8080", "https://some-path/proxy/8080/"),
    ("http://localhost:3000/app", "https://some-path/proxy/3000/app"),
    ("http://localhost:8888/lab", "https://some-path/proxy/8888/lab"),
    # Complex paths and query strings
    ("http://localhost:5007/very/long/path/to/resource", "https://some-path/proxy/5007/very/long/path/to/resource"),
    ("http://localhost:5007/path?query=1&another=2", "https://some-path/proxy/5007/path?query=1&another=2"),
    ("http://localhost:5007/path?complex=hello%20world&encoded=%3D%26", "https://some-path/proxy/5007/path?complex=hello%20world&encoded=%3D%26"),
    # URLs with fragments
    ("http://localhost:5007/page#section", "https://some-path/proxy/5007/page#section"),
    ("http://localhost:5007/path?query=1#fragment", "https://some-path/proxy/5007/path?query=1#fragment"),
    # Non-localhost URLs that should not change
    ("http://example.com:5007/path", "http://example.com:5007/path"),
    ("https://localhost:5007/path", "https://localhost:5007/path"),  # HTTPS localhost
    ("http://other-host:5007/path", "http://other-host:5007/path"),
    # Edge cases with special characters
    ("http://localhost:5007/path with spaces", "https://some-path/proxy/5007/path with spaces"),
    ("http://localhost:5007/path/with/unicode/café", "https://some-path/proxy/5007/path/with/unicode/café"),
]


@pytest.mark.parametrize("test_input, expected_output", TEST_CASES)
def test_to_proxy_url(test_input, expected_output):
    """Test the to_proxy_url function with various inputs."""
    jupyter_server_proxy_url = "https://some-path/proxy/"
    result = to_proxy_url(test_input, jupyter_server_proxy_url)
    assert result == expected_output, f"Expected {expected_output}, but got {result}"
