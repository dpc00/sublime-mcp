"""Loopback MCP servers are no-auth. Answer OAuth discovery instantly.

Clients such as mcp-remote and Grok's HTTP MCP transport probe
/.well-known/oauth-* before initialize. Returning HTML via
BaseHTTPRequestHandler.send_error(404) makes some of them retry or
enter an OAuth loop. JSON 404 means "no authorization server" per the
MCP OAuth spec and lets the client proceed (or fail fast) without a hang.

This module must not import sublime — ST loads every .py in the package.
"""


def is_oauth_discovery_path(path):
    if not path:
        return False
    path = path.split("?", 1)[0]
    return path.startswith("/.well-known/")


def send_no_authorization(handler):
    body = b"{}"
    handler.send_response(404)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)
