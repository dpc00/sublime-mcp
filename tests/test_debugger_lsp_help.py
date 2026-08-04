"""
Integration test for debugger-mcp's and lsp-mcp's get_help tools.

Unlike test_mcp_sse.py (which hand-rolls SSE parsing against sublime-mcp
on port 9502), this uses the real MCP SDK SSE client (mcp.client.sse) —
the same client machinery a real MCP client uses when configured with
type: sse, closer to what actually connects to these servers in practice.

Covers a gap found by direct testing: debugger-mcp (9505) and lsp-mcp
(9506) shipped ~100+ tools each with no get_help/AGENT_GUIDE.md at all,
unlike sublime-mcp. debugger_get_help / lsp_get_help were added, wired
through each file's existing TOOLS list so both the SSE tool table and the
HTTP bridge route table stay in sync automatically (see
test_python_proxy.py / test_batch.mjs for the bug class this avoids).

Note: the SDK's sse_client occasionally raises a transient httpx.ReadError
on the first connection attempt against this particular server
implementation (observed manually, not yet root-caused) — retry once
before treating a connection failure as real.

Prerequisites:
  - Sublime Text must be running with debugger_mcp.py and lsp_mcp.py loaded

Run:
  cd C:\\Users\\donal\\projects\\sublime-mcp
  pytest tests/test_debugger_lsp_help.py -v
"""

import asyncio
import json

import httpx
import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client

SERVERS = [
    ("debugger-mcp", "http://127.0.0.1:9505/sse", "debugger_get_help", "http://127.0.0.1:9515"),
    ("lsp-mcp", "http://127.0.0.1:9506/sse", "lsp_get_help", "http://127.0.0.1:9516"),
]


def _require_running(http_base):
    try:
        r = httpx.get(f"{http_base}/mcp_tools", timeout=3.0)
        assert r.status_code == 200
    except (httpx.ConnectError, httpx.ReadTimeout):
        pytest.skip(f"{http_base} not running — start Sublime Text first")


async def _list_and_call_help(sse_url, help_tool_name, retries=2):
    last_exc = None
    for attempt in range(retries):
        try:
            async with sse_client(sse_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    names = [t.name for t in tools.tools]

                    result = await session.call_tool(help_tool_name, {})
                    data = json.loads(result.content[0].text)
                    return names, data
        except Exception as e:  # transient httpx.ReadError on first connect, seen manually
            last_exc = e
            await asyncio.sleep(0.5)
    raise last_exc


class TestDebuggerMcpHelp:
    def test_help_tool_registered_and_returns_content(self):
        label, sse_url, help_tool, http_base = SERVERS[0]
        _require_running(http_base)
        names, data = asyncio.run(_list_and_call_help(sse_url, help_tool))
        assert help_tool in names
        assert data.get("ok") is True
        assert len(data.get("content", "")) > 500


class TestLspMcpHelp:
    def test_help_tool_registered_and_returns_content(self):
        label, sse_url, help_tool, http_base = SERVERS[1]
        _require_running(http_base)
        names, data = asyncio.run(_list_and_call_help(sse_url, help_tool))
        assert help_tool in names
        assert data.get("ok") is True
        assert len(data.get("content", "")) > 500
