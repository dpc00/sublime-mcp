"""
Integration tests for the MCP SSE server (port 9502).

Prerequisites:
  - Sublime Text must be running with sublime_mcp.py loaded
  - At least one file must be open in ST

Run:
  cd C:\\Users\\donal\\projects\\sublime-mcp
  pytest tests/test_mcp_sse.py -v

The SSE transport works like this:
  1. GET /sse  →  SSE stream; first event is  event: endpoint / data: /messages?sessionId=<uuid>
  2. POST /messages?sessionId=<uuid>  →  202 {}  (response arrives via SSE)
"""

import json
import queue
import threading
import time

import httpx
import pytest

BASE = "http://127.0.0.1:9502"
TIMEOUT = 10.0


# ── MCPSession helper ─────────────────────────────────────────────────────────


class MCPSession:
    """Open one SSE session, send JSON-RPC messages, collect responses."""

    def __init__(self):
        self._q = queue.Queue()
        self._endpoint = None
        self._client = httpx.Client(timeout=TIMEOUT)
        self._msg_id = 0
        self._thread = None
        self._ready = threading.Event()

    def __enter__(self):
        self._thread = threading.Thread(target=self._stream, daemon=True)
        self._thread.start()
        assert self._ready.wait(timeout=8), "SSE endpoint event never arrived"
        return self

    def __exit__(self, *_):
        self._client.close()

    def _stream(self):
        """Read SSE events and put JSON-RPC responses on the queue."""
        with self._client.stream("GET", f"{BASE}/sse",
                                 headers={"Accept": "text/event-stream"}) as resp:
            buf = []
            for line in resp.iter_lines():
                if line.startswith("event:"):
                    buf.append(("event", line[6:].strip()))
                elif line.startswith("data:"):
                    buf.append(("data", line[5:].strip()))
                elif line == "" and buf:
                    # flush accumulated event
                    event_type = next((v for k, v in buf if k == "event"), "message")
                    data = next((v for k, v in buf if k == "data"), "")
                    buf = []
                    if event_type == "endpoint":
                        self._endpoint = data
                        self._ready.set()
                    elif data and not data.startswith(":"):
                        try:
                            self._q.put(json.loads(data))
                        except json.JSONDecodeError:
                            pass
                elif line.startswith(":"):
                    pass  # ping

    def call(self, method, params=None, timeout=8):
        """Send a request and return the response (blocks until reply arrives)."""
        self._msg_id += 1
        msg_id = self._msg_id
        body = {"jsonrpc": "2.0", "id": msg_id, "method": method}
        if params:
            body["params"] = params
        url = f"{BASE}{self._endpoint}"
        r = self._client.post(url, json=body)
        assert r.status_code == 202, f"Expected 202, got {r.status_code}"
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                msg = self._q.get(timeout=0.2)
                if msg.get("id") == msg_id:
                    return msg
                self._q.put(msg)  # not ours, put back
            except queue.Empty:
                pass
        raise TimeoutError(f"No response for {method} id={msg_id} within {timeout}s")

    def notify(self, method, params=None):
        """Send a notification (no response expected)."""
        body = {"jsonrpc": "2.0", "method": method}
        if params:
            body["params"] = params
        url = f"{BASE}{self._endpoint}"
        r = self._client.post(url, json=body)
        assert r.status_code == 202


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def require_sse_server():
    """Skip entire session if the SSE server is not running."""
    try:
        with httpx.stream("GET", f"{BASE}/sse",
                          headers={"Accept": "text/event-stream"},
                          timeout=3.0) as r:
            assert r.status_code == 200
    except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError):
        pytest.skip("SSE server not running on port 9502 — start Sublime Text first")


@pytest.fixture
def session():
    """Fresh MCPSession for each test."""
    with MCPSession() as s:
        # handshake
        r = s.call("initialize", {"protocolVersion": "2024-11-05",
                                   "clientInfo": {"name": "pytest", "version": "0"}})
        assert "result" in r
        s.notify("notifications/initialized")
        yield s


# ── connectivity ──────────────────────────────────────────────────────────────


class TestConnectivity:
    def test_sse_returns_200(self):
        with httpx.stream("GET", f"{BASE}/sse",
                          headers={"Accept": "text/event-stream"},
                          timeout=5.0) as r:
            assert r.status_code == 200

    def test_sse_content_type_is_event_stream(self):
        with httpx.stream("GET", f"{BASE}/sse",
                          headers={"Accept": "text/event-stream"},
                          timeout=5.0) as r:
            assert "text/event-stream" in r.headers.get("content-type", "")

    def test_sse_first_event_is_endpoint(self):
        with httpx.stream("GET", f"{BASE}/sse",
                          headers={"Accept": "text/event-stream"},
                          timeout=5.0) as r:
            lines = []
            for line in r.iter_lines():
                lines.append(line)
                if line == "" and lines:
                    break
            raw = "\n".join(lines)
            assert "event: endpoint" in raw

    def test_sse_endpoint_data_contains_messages(self):
        with httpx.stream("GET", f"{BASE}/sse",
                          headers={"Accept": "text/event-stream"},
                          timeout=5.0) as r:
            data_line = None
            for line in r.iter_lines():
                if line.startswith("data:"):
                    data_line = line[5:].strip()
                    break
        assert data_line is not None
        assert "/messages" in data_line
        assert "sessionId=" in data_line

    def test_sse_cors_header(self):
        with httpx.stream("GET", f"{BASE}/sse",
                          headers={"Accept": "text/event-stream"},
                          timeout=5.0) as r:
            assert r.headers.get("access-control-allow-origin") == "*"

    def test_options_preflight_204(self):
        r = httpx.options(f"{BASE}/sse", timeout=5.0)
        assert r.status_code == 204

    def test_options_cors_methods(self):
        r = httpx.options(f"{BASE}/sse", timeout=5.0)
        assert "GET" in r.headers.get("access-control-allow-methods", "")
        assert "POST" in r.headers.get("access-control-allow-methods", "")

    def test_unknown_get_path_returns_404(self):
        r = httpx.get(f"{BASE}/notapath", timeout=5.0)
        assert r.status_code == 404

    def test_unknown_post_path_returns_404(self):
        r = httpx.post(f"{BASE}/notapath", json={}, timeout=5.0)
        assert r.status_code == 404

    def test_messages_without_session_returns_202(self):
        r = httpx.post(f"{BASE}/messages?sessionId=fake-session",
                       json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
                       timeout=5.0)
        # server accepts the POST (202) even if session is unknown — response just never arrives
        assert r.status_code == 202


# ── initialize ────────────────────────────────────────────────────────────────


class TestInitialize:
    def test_returns_result(self, session):
        r = session.call("initialize", {"protocolVersion": "2024-11-05",
                                         "clientInfo": {"name": "t", "version": "0"}})
        assert "result" in r

    def test_protocol_version(self, session):
        r = session.call("initialize", {"protocolVersion": "2024-11-05",
                                         "clientInfo": {"name": "t", "version": "0"}})
        assert r["result"]["protocolVersion"] == "2024-11-05"

    def test_server_info_name(self, session):
        r = session.call("initialize", {"protocolVersion": "2024-11-05",
                                         "clientInfo": {"name": "t", "version": "0"}})
        assert r["result"]["serverInfo"]["name"] == "sublime-mcp"

    def test_server_info_has_version(self, session):
        r = session.call("initialize", {"protocolVersion": "2024-11-05",
                                         "clientInfo": {"name": "t", "version": "0"}})
        assert "version" in r["result"]["serverInfo"]

    def test_capabilities_has_tools(self, session):
        r = session.call("initialize", {"protocolVersion": "2024-11-05",
                                         "clientInfo": {"name": "t", "version": "0"}})
        assert "tools" in r["result"]["capabilities"]

    def test_response_id_matches(self, session):
        session._msg_id = 99
        r = session.call("initialize", {"protocolVersion": "2024-11-05",
                                         "clientInfo": {"name": "t", "version": "0"}})
        assert r["id"] == 100

    def test_jsonrpc_version_field(self, session):
        r = session.call("initialize", {"protocolVersion": "2024-11-05",
                                         "clientInfo": {"name": "t", "version": "0"}})
        assert r.get("jsonrpc") == "2.0"


# ── ping ──────────────────────────────────────────────────────────────────────


class TestPing:
    def test_ping_returns_empty_result(self, session):
        r = session.call("ping")
        assert r["result"] == {}

    def test_ping_no_error(self, session):
        r = session.call("ping")
        assert "error" not in r


# ── notifications ─────────────────────────────────────────────────────────────


class TestNotifications:
    def test_initialized_notification_accepted(self, session):
        # Should not raise (202 response, no SSE reply)
        session.notify("notifications/initialized")

    def test_cancelled_notification_accepted(self, session):
        session.notify("notifications/cancelled", {"requestId": 99})


# ── unknown method ────────────────────────────────────────────────────────────


class TestUnknownMethod:
    def test_unknown_method_returns_error(self, session):
        r = session.call("no_such_method")
        assert "error" in r

    def test_error_has_message(self, session):
        r = session.call("no_such_method")
        assert "message" in r["error"]

    def test_error_has_code(self, session):
        r = session.call("no_such_method")
        assert "code" in r["error"]


# ── tools/list ────────────────────────────────────────────────────────────────


class TestToolsList:
    def test_returns_tools_key(self, session):
        r = session.call("tools/list")
        assert "tools" in r["result"]

    def test_tools_is_list(self, session):
        r = session.call("tools/list")
        assert isinstance(r["result"]["tools"], list)

    def test_tools_not_empty(self, session):
        r = session.call("tools/list")
        assert len(r["result"]["tools"]) > 0

    def test_each_tool_has_name(self, session):
        r = session.call("tools/list")
        for t in r["result"]["tools"]:
            assert "name" in t

    def test_each_tool_has_description(self, session):
        r = session.call("tools/list")
        for t in r["result"]["tools"]:
            assert "description" in t

    def test_each_tool_has_input_schema(self, session):
        r = session.call("tools/list")
        for t in r["result"]["tools"]:
            assert "inputSchema" in t

    def test_input_schema_has_type_object(self, session):
        r = session.call("tools/list")
        for t in r["result"]["tools"]:
            assert t["inputSchema"].get("type") == "object"

    def test_contains_get_active_file(self, session):
        r = session.call("tools/list")
        names = [t["name"] for t in r["result"]["tools"]]
        assert "get_active_file" in names

    def test_contains_str_replace_based_edit_tool(self, session):
        r = session.call("tools/list")
        names = [t["name"] for t in r["result"]["tools"]]
        assert "str_replace_based_edit_tool" in names

    def test_contains_eval_python(self, session):
        r = session.call("tools/list")
        names = [t["name"] for t in r["result"]["tools"]]
        assert "eval_python" in names

    def test_tool_count_matches_expected(self, session):
        r = session.call("tools/list")
        # Should be at least 40 tools
        assert len(r["result"]["tools"]) >= 40


# ── tools/call — read-only tools ─────────────────────────────────────────────


class TestToolCallGetActiveFile:
    def test_returns_content(self, session):
        r = session.call("tools/call", {"name": "get_active_file", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "content" in data

    def test_returns_line_and_col(self, session):
        r = session.call("tools/call", {"name": "get_active_file", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "line" in data
        assert "col" in data

    def test_returns_is_dirty(self, session):
        r = session.call("tools/call", {"name": "get_active_file", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "is_dirty" in data

    def test_returns_syntax(self, session):
        r = session.call("tools/call", {"name": "get_active_file", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "syntax" in data

    def test_content_type(self, session):
        r = session.call("tools/call", {"name": "get_active_file", "arguments": {}})
        assert r["result"]["content"][0]["type"] == "text"


class TestToolCallGetOpenFiles:
    def test_returns_files_list(self, session):
        r = session.call("tools/call", {"name": "get_open_files", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "files" in data
        assert isinstance(data["files"], list)

    def test_each_file_has_name(self, session):
        r = session.call("tools/call", {"name": "get_open_files", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        for f in data["files"]:
            assert "name" in f


class TestToolCallGetSheets:
    def test_returns_sheets_list(self, session):
        r = session.call("tools/call", {"name": "get_sheets", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "sheets" in data
        assert isinstance(data["sheets"], list)

    def test_each_sheet_has_index(self, session):
        r = session.call("tools/call", {"name": "get_sheets", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        for s in data["sheets"]:
            assert "index" in s


class TestToolCallGetSelection:
    def test_returns_selections(self, session):
        r = session.call("tools/call", {"name": "get_selection", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "selections" in data
        assert isinstance(data["selections"], list)


class TestToolCallGetProjectFolders:
    def test_returns_folders(self, session):
        r = session.call("tools/call", {"name": "get_project_folders", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "folders" in data


class TestToolCallGetVariables:
    def test_returns_variables(self, session):
        r = session.call("tools/call", {"name": "get_variables", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "platform" in data or "variables" in data or isinstance(data, dict)


class TestToolCallGetEncoding:
    def test_returns_encoding(self, session):
        r = session.call("tools/call", {"name": "get_encoding", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "encoding" in data
        assert isinstance(data["encoding"], str)


class TestToolCallGetLineCount:
    def test_returns_count(self, session):
        r = session.call("tools/call", {"name": "get_line_count", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "line_count" in data
        assert isinstance(data["line_count"], int)
        assert data["line_count"] >= 1


class TestToolCallGetLayout:
    def test_returns_layout(self, session):
        r = session.call("tools/call", {"name": "get_layout", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "layout" in data or "groups" in data or isinstance(data, dict)


class TestToolCallGetSyntaxes:
    def test_returns_syntaxes(self, session):
        r = session.call("tools/call", {"name": "get_syntaxes", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "syntaxes" in data
        assert isinstance(data["syntaxes"], list)
        assert len(data["syntaxes"]) > 0


class TestToolCallGetScopeAtCursor:
    def test_returns_scope(self, session):
        r = session.call("tools/call", {"name": "get_scope_at_cursor", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "scope" in data


class TestToolCallGetWordAtCursor:
    def test_returns_word(self, session):
        r = session.call("tools/call", {"name": "get_word_at_cursor", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "word" in data


class TestToolCallGetCursorContext:
    def test_default_returns_context(self, session):
        r = session.call("tools/call", {"name": "get_cursor_context", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "context" in data

    def test_with_lines_param(self, session):
        r = session.call("tools/call", {"name": "get_cursor_context", "arguments": {"lines": 3}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "context" in data


class TestToolCallGetConsoleLog:
    def test_returns_entries(self, session):
        r = session.call("tools/call", {"name": "get_console_log", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "entries" in data or "log" in data or isinstance(data, dict)

    def test_tail_param(self, session):
        r = session.call("tools/call", {"name": "get_console_log", "arguments": {"tail": 5}})
        assert "result" in r
        assert "error" not in r


class TestToolCallGetViewContent:
    def test_active_view(self, session):
        r = session.call("tools/call", {"name": "get_view_content", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert "content" in data

    def test_content_is_string(self, session):
        r = session.call("tools/call", {"name": "get_view_content", "arguments": {}})
        data = json.loads(r["result"]["content"][0]["text"])
        assert isinstance(data["content"], str)


class TestToolCallFindInFile:
    def test_basic_search(self, session):
        r = session.call("tools/call", {
            "name": "find_in_file",
            "arguments": {"pattern": "def ", "regex": False}
        })
        assert "result" in r
        assert "error" not in r

    def test_returns_results_list(self, session):
        r = session.call("tools/call", {
            "name": "find_in_file",
            "arguments": {"pattern": "def "}
        })
        data = json.loads(r["result"]["content"][0]["text"])
        assert "results" in data or isinstance(data, dict)


class TestToolCallSetStatus:
    def test_set_status_ok(self, session):
        r = session.call("tools/call", {
            "name": "set_status",
            "arguments": {"value": "pytest-sse-test", "key": "pytest_sse"}
        })
        assert "result" in r
        assert "error" not in r


class TestToolCallEvalPython:
    def test_returns_output(self, session):
        r = session.call("tools/call", {
            "name": "eval_python",
            "arguments": {"code": "print('hello-sse')"}
        })
        data = json.loads(r["result"]["content"][0]["text"])
        assert "output" in data
        assert "hello-sse" in data["output"]


# ── tools/call — unknown tool ─────────────────────────────────────────────────


class TestToolCallErrors:
    def test_unknown_tool_returns_error(self, session):
        r = session.call("tools/call", {"name": "no_such_tool", "arguments": {}})
        assert "error" in r

    def test_error_message_mentions_tool(self, session):
        r = session.call("tools/call", {"name": "no_such_tool", "arguments": {}})
        assert "no_such_tool" in r["error"]["message"]

    def test_missing_required_arg_returns_error(self, session):
        # get_sheet_content requires `index`
        r = session.call("tools/call", {"name": "get_sheet_content", "arguments": {}})
        # Either an error or a graceful response — just must not hang
        assert "result" in r or "error" in r


# ── multiple sessions ─────────────────────────────────────────────────────────


class TestMultipleSessions:
    def test_two_independent_sessions(self):
        with MCPSession() as s1, MCPSession() as s2:
            r1 = s1.call("initialize", {"protocolVersion": "2024-11-05",
                                         "clientInfo": {"name": "s1", "version": "0"}})
            r2 = s2.call("initialize", {"protocolVersion": "2024-11-05",
                                         "clientInfo": {"name": "s2", "version": "0"}})
            assert r1["result"]["protocolVersion"] == "2024-11-05"
            assert r2["result"]["protocolVersion"] == "2024-11-05"

    def test_responses_are_not_mixed_between_sessions(self):
        with MCPSession() as s1, MCPSession() as s2:
            s1.call("initialize", {"protocolVersion": "2024-11-05",
                                    "clientInfo": {"name": "s1", "version": "0"}})
            s2.call("initialize", {"protocolVersion": "2024-11-05",
                                    "clientInfo": {"name": "s2", "version": "0"}})
            r1 = s1.call("ping")
            r2 = s2.call("ping")
            assert r1["result"] == {}
            assert r2["result"] == {}
