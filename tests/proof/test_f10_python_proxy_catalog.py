"""F10 (python-proxy) — generated catalog vs backend _MCP_TOOLS.

PROOF: F10 second surface — 2026-08-19. `node-proxy`'s fallback drift was
fixed first; `python-proxy` had the same dual-maintenance defect in a worse
form. It has no dynamic `/mcp_tools` discovery at all, so its 72
hand-written tools were the *entire* surface a Python-side agent ever saw:
148 of the backend's 220 tools were permanently unreachable, not merely
dropped on a discovery miss.

FIXED. `tools/generate_fallback_catalog.py` now also emits
`packages/python-proxy/tool_catalog.py`, and `mcp_server.py` builds typed
FastMCP tools from it. These tests lock the result:

  * the committed catalog is not stale (shared `--check` covers both
    proxies);
  * the catalog equals the backend exactly;
  * `mcp_server.py` carries no hand-written tool list — only the declared
    response-shaping overrides;
  * an override cannot silently shadow or duplicate a generated tool.

Live MCP-stdio behavior is covered by `tests/test_python_proxy.py`, which
needs a running Sublime; these tests are static and always run.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
BACKEND = ROOT / "packages" / "st-plugin" / "sublime_mcp.py"
PROXY = ROOT / "packages" / "python-proxy" / "mcp_server.py"
CATALOG = ROOT / "packages" / "python-proxy" / "tool_catalog.py"
GENERATOR = ROOT / "tools" / "generate_fallback_catalog.py"


def _backend_names():
    """Parse tool names out of _MCP_TOOLS in the plugin source."""
    text = BACKEND.read_text(encoding="utf-8")
    start = text.index("_MCP_TOOLS = [")
    end = text.index("\n_mcp_tools_lock", start)
    chunk = text[start:end]
    return {part.split('"', 1)[0] for part in re.split(r'\n    \("', chunk)[1:]}


def _catalog_tools():
    namespace = {}
    exec(compile(CATALOG.read_text(encoding="utf-8"), str(CATALOG), "exec"), namespace)
    return namespace["TOOLS"]


def test_committed_python_catalog_is_not_stale():
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "tool_catalog.py is stale. Run:\n"
        "    python tools/generate_fallback_catalog.py\n\n" + result.stdout + result.stderr
    )


def test_catalog_matches_the_backend_exactly():
    backend = _backend_names()
    catalog = {tool["name"] for tool in _catalog_tools()}
    assert catalog - backend == set(), "catalog advertises tools the backend lacks"
    assert backend - catalog == set(), (
        "F10 regression: {} backend tools unreachable through python-proxy".format(
            len(backend - catalog)
        )
    )


def test_every_catalog_entry_is_usable():
    """A name alone is not a tool; description and schema must survive."""
    for tool in _catalog_tools():
        assert tool.get("description"), "{} has no description".format(tool["name"])
        schema = tool.get("inputSchema")
        assert isinstance(schema, dict), "{} has no inputSchema".format(tool["name"])
        assert schema.get("type") == "object", "{} schema is not an object".format(tool["name"])
        assert isinstance(schema.get("properties"), dict)


def test_proxy_has_no_hand_maintained_tool_list():
    """The original defect was a second hand-written catalog. Keep it gone."""
    text = PROXY.read_text(encoding="utf-8")
    assert "from tool_catalog import TOOLS" in text, "proxy must build from the generated catalog"

    declared = re.findall(r'@mcp\.tool\(name="([a-z0-9_]+)"\)', text)
    bare = re.findall(r"@mcp\.tool\(\)", text)
    assert bare == [], (
        "hand-written @mcp.tool() definitions reintroduced: use the generated "
        "catalog, or add an explicit named override"
    )

    override_block = re.search(r"_OVERRIDDEN = \((.*?)\)", text, re.S)
    assert override_block, "overrides must be declared in _OVERRIDDEN"
    overridden = re.findall(r'"([a-z0-9_]+)"', override_block.group(1))
    assert sorted(declared) == sorted(overridden), (
        "every hand-written tool must be listed in _OVERRIDDEN so it replaces "
        "its generated twin instead of colliding: declared={} overridden={}".format(
            sorted(declared), sorted(overridden)
        )
    )


def test_overrides_correspond_to_real_backend_tools():
    """An override for a nonexistent tool would add a ghost."""
    text = PROXY.read_text(encoding="utf-8")
    override_block = re.search(r"_OVERRIDDEN = \((.*?)\)", text, re.S)
    overridden = set(re.findall(r'"([a-z0-9_]+)"', override_block.group(1)))
    assert overridden <= _backend_names(), (
        "override names not present in the backend catalog: {}".format(
            sorted(overridden - _backend_names())
        )
    )


def test_generated_catalog_is_packaged():
    """A generated module that is not shipped installs a broken server.

    mcp_server imports tool_catalog at startup, so leaving it out of
    py-modules would make `pip install .` produce an ImportError rather
    than a proxy. Checked against the declaration, not a full build, so
    this stays fast and offline.
    """
    pyproject = (PROXY.parent / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"py-modules\s*=\s*\[(.*?)\]", pyproject, re.S)
    assert match, "py-modules declaration missing"
    modules = set(re.findall(r'"([A-Za-z0-9_]+)"', match.group(1)))
    assert {"mcp_server", "tool_catalog"} <= modules, (
        "tool_catalog must ship with the package; py-modules={}".format(sorted(modules))
    )


def test_optional_params_are_omitted_rather_than_sent_as_null():
    """The generated wrappers give optional params a None sentinel.

    Those must be dropped from the request body. Sending an explicit null
    would hand the backend a value where it expects the key to be absent,
    which is a different request from the one the agent made. Driven
    through a real MCP stdio subprocess against a fake bridge, so it needs
    no Sublime and records the exact bytes the proxy sends.
    """
    import asyncio
    import json
    import os
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    seen = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002 - stdlib signature
            pass

        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            seen.append((self.path, self.rfile.read(length).decode() if length else ""))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]

    async def drive():
        env = dict(os.environ)
        env["SUBLIME_MCP_BASE"] = "http://127.0.0.1:{}".format(port)
        params = StdioServerParameters(
            command=sys.executable,
            args=["mcp_server.py"],
            cwd=str(PROXY.parent),
            env=env,
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # `scope` has a backend default; nothing else is declared.
                await session.call_tool("get_setting", {"key": "tab_size"})
                # `args` is an optional object with no backend default.
                await session.call_tool("run_command", {"command": "noop"})

    try:
        asyncio.run(drive())
    finally:
        server.shutdown()

    bodies = {path: json.loads(body) for path, body in seen}

    assert bodies["/get_setting"] == {"key": "tab_size", "scope": "view"}, (
        "declared defaults must be sent; got {}".format(bodies["/get_setting"])
    )
    assert bodies["/run_command"] == {"command": "noop", "scope": "window"}, (
        "optional param with no default must be omitted, not sent as null; got {}".format(
            bodies["/run_command"]
        )
    )
    assert "args" not in bodies["/run_command"]
