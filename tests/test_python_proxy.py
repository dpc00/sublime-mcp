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

import httpx
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE = "http://127.0.0.1:9500"
PROXY_DIR = r"C:\Users\donal\projects\sublime-mcp\packages\python-proxy"


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
