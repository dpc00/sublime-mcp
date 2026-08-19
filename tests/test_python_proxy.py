"""
Integration test for packages/python-proxy/mcp_server.py.

Unlike test_http_api.py (which hits the HTTP bridge on port 9500 directly)
and test_mcp_sse.py (which hits the MCP/SSE server on port 9502 directly),
this test exercises the actual python-proxy subprocess over MCP stdio —
the same code path a real MCP client (e.g. Claude Code configured with a
stdio server entry) would use. This is the only test that would have
caught the missing `_POST["/batch"]` route on the HTTP bridge: reading
mcp_server.py's source showed the tool was defined correctly, but only a
live call through the real transport surfaced the 404.

Prerequisites:
  - Sublime Text must be running with sublime_mcp.py loaded (HTTP bridge
    on port 9500)
  - At least one file must be open in ST

Run:
  cd C:\\Users\\donal\\projects\\sublime-mcp
  pytest tests/test_python_proxy.py -v
"""

import asyncio
from pathlib import Path

import httpx
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE = "http://127.0.0.1:9500"
PROXY_DIR = str(Path(__file__).resolve().parent.parent / "packages" / "python-proxy")


@pytest.fixture(scope="session", autouse=True)
def require_http_bridge():
    """Skip entire session if the HTTP bridge is not running."""
    try:
        r = httpx.get(f"{BASE}/active_file", timeout=3.0)
        assert r.status_code == 200
    except (httpx.ConnectError, httpx.ReadTimeout):
        pytest.skip("HTTP bridge not running on port 9500 — start Sublime Text first")


async def _run_session(coro):
    """Launch python-proxy as a subprocess, run coro(session), return its result."""
    params = StdioServerParameters(command="python", args=["mcp_server.py"], cwd=PROXY_DIR)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await coro(session)


class TestToolDiscovery:
    def test_batch_is_registered(self):
        async def go(session):
            tools = await session.list_tools()
            return [t.name for t in tools.tools]

        names = asyncio.run(_run_session(go))
        assert "batch" in names

    def test_get_help_is_registered(self):
        async def go(session):
            tools = await session.list_tools()
            return [t.name for t in tools.tools]

        names = asyncio.run(_run_session(go))
        assert "get_help" in names

    def test_full_backend_catalog_is_exposed(self):
        """F10 second surface: python-proxy used to expose 72 of 220 tools.

        It has no dynamic discovery, so a missing tool was permanently
        unreachable rather than merely dropped on a discovery miss. The
        generated catalog must reach the client intact over real MCP stdio.
        """
        import json

        catalog = json.loads(
            (
                Path(__file__).resolve().parent.parent
                / "packages"
                / "node-proxy"
                / "fallback-tools.json"
            ).read_text(encoding="utf-8")
        )
        expected = {tool["name"] for tool in catalog["tools"]}

        async def go(session):
            tools = await session.list_tools()
            return {t.name for t in tools.tools}

        names = asyncio.run(_run_session(go))
        assert expected - names == set(), "tools missing from python-proxy"
        assert names - expected == set(), "python-proxy advertises unknown tools"

    def test_generated_schemas_are_typed_not_passthrough(self):
        """Registration must replay each schema, not degrade to an opaque dict."""

        async def go(session):
            tools = await session.list_tools()
            return {t.name: t.inputSchema for t in tools.tools}

        schemas = asyncio.run(_run_session(go))

        open_file = schemas["open_file"]
        assert open_file["required"] == ["path"]
        assert open_file["properties"]["path"]["type"] == "string"
        assert open_file["properties"]["line"]["default"] == 0

        # Nested structure from the backend schema must survive.
        calls = schemas["batch"]["properties"]["calls"]
        assert calls["type"] == "array"
        assert calls["items"]["required"] == ["tool"]

        # A no-parameter tool must advertise no parameters.
        assert schemas["get_active_file"].get("properties") == {}


class TestGeneratedToolCalls:
    """The generated wrappers must actually reach the backend."""

    def test_newly_reachable_tool_works(self):
        """get_view_size was absent from the old hand-written 72."""

        async def go(session):
            return await session.call_tool("get_view_size", {})

        result = asyncio.run(_run_session(go))
        assert not result.isError
        import json

        assert "size" in json.loads(result.content[0].text)

    def test_optional_param_without_default_is_omitted_not_nulled(self):
        """Optional params carry a None sentinel; it must not be sent as null.

        The deterministic body-level assertion lives in
        tests/proof/test_f10_python_proxy_catalog.py against a fake bridge.
        This is the live smoke check that the same call reaches Sublime.
        """

        async def go(session):
            return await session.call_tool("get_setting", {"key": "tab_size"})

        result = asyncio.run(_run_session(go))
        assert not result.isError
        import json

        assert "value" in json.loads(result.content[0].text)

    def test_image_override_still_shapes_the_response(self):
        """get_sheet_content is a declared override, not a generated twin."""

        async def go(session):
            tools = await session.list_tools()
            return [t for t in tools.tools if t.name == "get_sheet_content"]

        matches = asyncio.run(_run_session(go))
        assert len(matches) == 1, "override must replace, not duplicate, the generated tool"
        assert matches[0].inputSchema["required"] == ["index"]


class TestBatchToolCall:
    def test_batch_returns_results_for_each_call(self):
        async def go(session):
            return await session.call_tool(
                "batch",
                {"calls": [{"tool": "get_line_count"}, {"tool": "get_selection"}]},
            )

        result = asyncio.run(_run_session(go))
        assert not result.isError
        import json

        data = json.loads(result.content[0].text)
        assert "results" in data
        assert len(data["results"]) == 2
        assert "line_count" in data["results"][0]
        assert "selections" in data["results"][1]

    def test_batch_partial_failure_does_not_abort(self):
        async def go(session):
            return await session.call_tool(
                "batch",
                {"calls": [{"tool": "get_line_count"}, {"tool": "no_such_tool_xyz"}]},
            )

        result = asyncio.run(_run_session(go))
        import json

        data = json.loads(result.content[0].text)
        assert len(data["results"]) == 2
        assert "line_count" in data["results"][0]
        assert "error" in data["results"][1]
