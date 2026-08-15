"""OAuth discovery paths must fail closed and fast with JSON, not HTML.

mcp-remote (and Grok's HTTP MCP client) probe
/.well-known/oauth-authorization-server before initialize. A BaseHTTP
send_error(404) returns HTML; some clients then retry or start an OAuth
loop instead of treating the resource as no-auth. These servers are
loopback, no-auth MCP endpoints — discovery must return JSON 404 instantly.
"""

import importlib.util
import os

import pytest

_POLICY = os.path.join(
    os.path.dirname(__file__),
    "..",
    "packages",
    "st-plugin",
    "mcp_http_policy.py",
)


def _load_policy():
    spec = importlib.util.spec_from_file_location("mcp_http_policy", _POLICY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_policy_module_exists():
    assert os.path.isfile(_POLICY), (
        "packages/st-plugin/mcp_http_policy.py must exist so the handler "
        "can classify OAuth discovery paths without importing sublime"
    )


def test_known_discovery_paths_are_recognized():
    policy = _load_policy()
    for path in (
        "/.well-known/oauth-authorization-server",
        "/.well-known/oauth-protected-resource",
        "/.well-known/openid-configuration",
        "/.well-known/oauth-authorization-server/mcp",
        "/.well-known/oauth-protected-resource/mcp",
    ):
        assert policy.is_oauth_discovery_path(path), path


def test_real_mcp_paths_are_not_discovery():
    policy = _load_policy()
    for path in ("/sse", "/mcp", "/messages", "/", "/open_files"):
        assert not policy.is_oauth_discovery_path(path), path


def test_query_string_does_not_hide_discovery():
    policy = _load_policy()
    assert policy.is_oauth_discovery_path(
        "/.well-known/oauth-authorization-server?resource=http://127.0.0.1:9502/mcp"
    )


def test_discovery_response_is_json_404_not_html():
    """mcp-remote must see application/json, not send_error() HTML."""
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlparse

    import httpx

    policy = _load_policy()

    class H(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def do_GET(self):
            path = urlparse(self.path).path
            if policy.is_oauth_discovery_path(self.path):
                policy.send_no_authorization(self)
                return
            self.send_error(404)

    httpd = HTTPServer(("127.0.0.1", 0), H)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        r = httpx.get(
            f"http://127.0.0.1:{port}/.well-known/oauth-authorization-server",
            timeout=2.0,
        )
        assert r.status_code == 404
        assert r.headers.get("content-type", "").startswith("application/json")
        assert json.loads(r.text) == {}
        assert "<html" not in r.text.lower()
    finally:
        httpd.shutdown()


def test_mcp_handlers_route_discovery_through_policy():
    root = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "packages")
    )
    for rel in (
        os.path.join("st-plugin", "sublime_mcp.py"),
        os.path.join("debugger-mcp", "debugger_mcp.py"),
        os.path.join("lsp-mcp", "lsp_mcp.py"),
    ):
        text = open(os.path.join(root, rel), encoding="utf-8").read()
        assert "is_oauth_discovery_path" in text, rel
        assert "send_no_authorization" in text, rel


def test_sibling_packages_ship_the_same_policy():
    import filecmp

    root = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "packages")
    )
    a = os.path.join(root, "st-plugin", "mcp_http_policy.py")
    b = os.path.join(root, "debugger-mcp", "mcp_http_policy.py")
    c = os.path.join(root, "lsp-mcp", "mcp_http_policy.py")
    assert os.path.isfile(b) and os.path.isfile(c)
    assert filecmp.cmp(a, b, shallow=False)
    assert filecmp.cmp(a, c, shallow=False)
