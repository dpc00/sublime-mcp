# LSP MCP — standalone Sublime Text plugin
# Serves LSP (Language Server Protocol) tools over MCP SSE on port 9506.
# Refactored from lsp_mcp_tools.py (formerly an add-on to sublime-mcp).
# Includes all LSP ST commands (67 user-facing) + hand-written request wrappers (13).

import sublime
import sublime_plugin
import sys
import os
import json
import threading
import uuid as _uuid
import queue as _queue
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

_MCP_PORT = int(os.environ.get("LSP_MCP_PORT", 9506))


# ── MCP server boilerplate ────────────────────────────────────────────────────

_MCP_TOOLS = []
_mcp_tools_lock = threading.Lock()
_mcp_sessions = {}


def register_mcp_tools(tools):
    with _mcp_tools_lock:
        existing = {t[0] for t in _MCP_TOOLS}
        for entry in tools:
            name = entry[0]
            if name in existing:
                print("[lsp-mcp] register_mcp_tools: '{}' already registered - skipped".format(name))
                continue
            _MCP_TOOLS.append(entry)
            existing.add(name)


def unregister_mcp_tools(tools):
    names = {entry[0] for entry in tools}
    with _mcp_tools_lock:
        for i in range(len(_MCP_TOOLS) - 1, -1, -1):
            if _MCP_TOOLS[i][0] in names:
                _MCP_TOOLS.pop(i)


class _ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


class _MCPHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if urlparse(self.path).path == "/sse":
            self._handle_sse()
        else:
            self.send_error(404)

    def do_POST(self):
        if urlparse(self.path).path == "/messages":
            self._handle_message()
        else:
            self.send_error(404)

    def _handle_sse(self):
        session_id = str(_uuid.uuid4())
        q = _queue.Queue()
        _mcp_sessions[session_id] = q

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            endpoint = "/messages?sessionId=" + session_id
            self.wfile.write(("event: endpoint\ndata: " + endpoint + "\n\n").encode())
            self.wfile.flush()
            while True:
                try:
                    msg = q.get(timeout=30)
                except _queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    continue
                if msg is None:
                    break
                self.wfile.write(("data: " + json.dumps(msg) + "\n\n").encode())
                self.wfile.flush()
        except Exception:
            pass
        finally:
            _mcp_sessions.pop(session_id, None)

    def _handle_message(self):
        params = parse_qs(urlparse(self.path).query)
        session_id = params.get("sessionId", [None])[0]
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"{}")

        threading.Thread(target=_mcp_dispatch, args=(session_id, body), daemon=True).start()


def _mcp_send(session_id, msg):
    q = _mcp_sessions.get(session_id)
    if q:
        q.put(msg)


def _mcp_dispatch(session_id, msg):
    method = msg.get("method", "")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "lsp-mcp", "version": "1.0.0"},
            }
        elif method in ("notifications/initialized", "notifications/cancelled"):
            return
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            with _mcp_tools_lock:
                snapshot = list(_MCP_TOOLS)
            tools = []
            for name, desc, schema, _ in snapshot:
                input_schema = dict(schema) if schema else {}
                if "type" not in input_schema:
                    input_schema["type"] = "object"
                if "properties" not in input_schema:
                    input_schema["properties"] = {}
                tools.append({"name": name, "description": desc, "inputSchema": input_schema})
            result = {"tools": tools}
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}
            with _mcp_tools_lock:
                entry = next((t for t in _MCP_TOOLS if t[0] == tool_name), None)
            if entry is None:
                raise ValueError("Unknown tool: " + str(tool_name))
            data = entry[3](tool_args)
            if isinstance(data, list):
                result = {"content": data}
            else:
                result = {"content": [{"type": "text", "text": json.dumps(data)}]}
        else:
            raise ValueError("Unknown method: " + method)

        if msg_id is not None:
            _mcp_send(session_id, {"jsonrpc": "2.0", "id": msg_id, "result": result})
    except Exception as e:
        if msg_id is not None:
            _mcp_send(session_id, {"jsonrpc": "2.0", "id": msg_id,
                                   "error": {"code": -32603, "message": str(e)}})


# ── plugin lifecycle ──────────────────────────────────────────────────────────

_server = None


def _start_server():
    global _server
    if not _server:
        try:
            _server = _ThreadingHTTPServer(("127.0.0.1", _MCP_PORT), _MCPHandler)
            threading.Thread(target=_server.serve_forever, daemon=True).start()
        except OSError as e:
            print("[lsp-mcp] could not bind MCP SSE on port {}: {}".format(_MCP_PORT, e))
            _server = None
    print("[lsp-mcp] MCP SSE on 127.0.0.1:{}".format(_MCP_PORT))


def _stop_server():
    global _server
    if _server:
        _server.shutdown()
        _server = None
    for q in list(_mcp_sessions.values()):
        q.put(None)
    _mcp_sessions.clear()
    print("[lsp-mcp] stopped")


def plugin_loaded():
    register_mcp_tools(TOOLS)
    _start_server()
    print("[lsp-mcp] {} tools loaded".format(len(TOOLS)))


def plugin_unloaded():
    unregister_mcp_tools(TOOLS)
    _stop_server()


# ── LSP helper functions (from lsp_mcp_tools.py) ──────────────────────────────

def find_view_by_file_path(file_path):
    if not file_path:
        return None
    target_path = os.path.abspath(file_path).lower()
    for window in sublime.windows():
        for view in window.views():
            if view.file_name() and os.path.abspath(view.file_name()).lower() == target_path:
                return view
    return None

def get_or_open_view_for_file(file_path):
    view = find_view_by_file_path(file_path)
    if view:
        return view
    window = sublime.active_window() or (sublime.windows()[0] if sublime.windows() else None)
    if not window:
        return None
    return window.open_file(file_path, sublime.TRANSIENT)

def get_active_session_for_view(view, config_name=None):
    if not view:
        return None
    reg = sys.modules.get("LSP.plugin.core.registry")
    if not reg:
        return None
    wm = reg.windows.lookup(view.window() or sublime.active_window())
    if not wm:
        return None
    for session in wm.get_sessions():
        if config_name and session.config.name != config_name:
            continue
        if session.can_handle(view):
            return session
    sessions = wm.get_sessions()
    if sessions:
        return next((s for s in sessions if not config_name or s.config.name == config_name), None)
    return None

def execute_lsp_request(method, params, file_path=None, config_name=None, timeout=5.0):
    reg = sys.modules.get("LSP.plugin.core.registry")
    if not reg:
        return {"error": "LSP package registry not loaded."}

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view:
        return {"error": "No active view found or resolved for the request."}

    session = get_active_session_for_view(view, config_name)
    if not session:
        return {"error": "No active LSP session found for the file: {}".format(view.file_name() or "Untitled")}

    proto = sys.modules.get("LSP.plugin.core.protocol")
    if not proto:
        return {"error": "LSP protocol module not loaded."}

    req = proto.Request(method, params)
    event = threading.Event()
    res_holder = []
    err_holder = []

    def on_result(res):
        res_holder.append(res)
        event.set()

    def on_error(err):
        err_holder.append(err)
        event.set()

    session.send_request_async(req, on_result, on_error)
    if event.wait(timeout):
        if res_holder:
            return {"result": res_holder[0]}
        else:
            return {"error": str(err_holder[0]) if err_holder else "Unknown error"}
    else:
        return {"error": "LSP request timed out after {} seconds.".format(timeout)}


# ── Hand-written LSP request wrappers (from lsp_mcp_tools.py) ──────────────────

def mcp_lsp_get_sessions(body):
    reg = sys.modules.get("LSP.plugin.core.registry")
    if not reg:
        return {"error": "LSP package registry not loaded."}
    result = []
    for window in sublime.windows():
        wm = reg.windows.lookup(window)
        if not wm:
            continue
        for session in wm.get_sessions():
            result.append({
                "window_id": window.id(),
                "name": session.config.name,
                "state": str(session.state),
                "project_path": wm.get_project_path()
            })
    return {"sessions": result}

def mcp_lsp_get_diagnostics(body):
    file_path = body.get("file_path")
    min_severity = body.get("min_severity", 4)

    reg = sys.modules.get("LSP.plugin.core.registry")
    if not reg:
        return {"error": "LSP package registry not loaded."}

    result = []
    for window in sublime.windows():
        wm = reg.windows.lookup(window)
        if not wm:
            continue

        for session in wm.get_sessions():
            diagnostics_storage = getattr(session, "diagnostics", None)
            if not diagnostics_storage:
                continue

            for uri, diags_dict in diagnostics_storage._diagnostics.items():
                local_path = uri
                if uri.startswith("file:///"):
                    local_path = uri[8:]
                    local_path = urllib.parse.unquote(local_path)
                    if sys.platform == "win32":
                        local_path = local_path.replace("/", "\\")

                if file_path and os.path.abspath(local_path).lower() != os.path.abspath(file_path).lower():
                    continue

                for identifier, diags in diags_dict.items():
                    for d in diags:
                        severity = d.get("severity", 1)
                        if severity > min_severity:
                            continue
                        result.append({
                            "window_id": window.id(),
                            "file_path": local_path,
                            "session": session.config.name,
                            "provider": str(identifier),
                            "severity": severity,
                            "message": d.get("message"),
                            "range": d.get("range"),
                            "code": d.get("code"),
                            "source": d.get("source", session.config.name)
                        })
    return {"diagnostics": result}

def mcp_lsp_get_symbols(body):
    file_path = body.get("file_path")
    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved to fetch symbols."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    res = execute_lsp_request("textDocument/documentSymbol", {"textDocument": {"uri": uri}}, file_path=view.file_name())
    if "error" in res:
        return res
    return {"symbols": res["result"]}

def mcp_lsp_hover(body):
    line = body["line"]
    column = body["column"]
    file_path = body.get("file_path")

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for hover."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": column}
    }
    res = execute_lsp_request("textDocument/hover", params, file_path=view.file_name())
    if "error" in res:
        return res
    return {"hover": res["result"]}

def mcp_lsp_goto_definition(body):
    line = body["line"]
    column = body["column"]
    file_path = body.get("file_path")

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for definition."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": column}
    }
    res = execute_lsp_request("textDocument/definition", params, file_path=view.file_name())
    if "error" in res:
        return res
    return {"definitions": res["result"]}

def mcp_lsp_find_references(body):
    line = body["line"]
    column = body["column"]
    file_path = body.get("file_path")

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for references."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": column},
        "context": {"includeDeclaration": True}
    }
    res = execute_lsp_request("textDocument/references", params, file_path=view.file_name(), timeout=10.0)
    if "error" in res:
        return res
    return {"references": res["result"]}

def mcp_lsp_format_document(body):
    file_path = body.get("file_path")
    if file_path:
        view = find_view_by_file_path(file_path)
        if not view:
            return {"error": "File is not open on screen. Cannot format a closed file via LSP."}
    else:
        window = sublime.active_window()
        view = window.active_view() if window else None

    if not view:
        return {"error": "No open file resolved to format."}

    view.run_command("lsp_format_document")
    return {"success": True, "message": "Triggered lsp_format_document command for view: {}".format(view.file_name())}

def mcp_lsp_search_workspace_symbols(body):
    query = body["query"]
    view = None
    for window in sublime.windows():
        if window.views():
            view = window.views()[0]
            break

    if not view:
        return {"error": "No open views to attach search symbol query to."}

    res = execute_lsp_request("workspace/symbol", {"query": query}, file_path=view.file_name())
    if "error" in res:
        return res
    return {"symbols": res["result"]}

def mcp_lsp_get_code_actions(body):
    file_path = body.get("file_path")
    start_line = body["start_line"]
    start_col = body.get("start_column", 0)
    end_line = body.get("end_line", start_line)
    end_col = body.get("end_column", 100)

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for code actions."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "range": {
            "start": {"line": start_line, "character": start_col},
            "end": {"line": end_line, "character": end_col}
        },
        "context": {"diagnostics": []}
    }
    res = execute_lsp_request("textDocument/codeAction", params, file_path=view.file_name())
    if "error" in res:
        return res
    return {"code_actions": res["result"]}

def mcp_lsp_rename_symbol(body):
    file_path = body.get("file_path")
    line = body["line"]
    column = body["column"]
    new_name = body["new_name"]

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for rename."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": column},
        "newName": new_name
    }
    res = execute_lsp_request("textDocument/rename", params, file_path=view.file_name())
    if "error" in res:
        return res
    return {"workspace_edit": res["result"]}

def mcp_lsp_get_implementation(body):
    line = body["line"]
    column = body["column"]
    file_path = body.get("file_path")

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for implementation."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": column}
    }
    res = execute_lsp_request("textDocument/implementation", params, file_path=view.file_name())
    if "error" in res:
        return res
    return {"implementations": res["result"]}

def mcp_lsp_get_type_definition(body):
    line = body["line"]
    column = body["column"]
    file_path = body.get("file_path")

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for type definition."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": column}
    }
    res = execute_lsp_request("textDocument/typeDefinition", params, file_path=view.file_name())
    if "error" in res:
        return res
    return {"type_definitions": res["result"]}

def mcp_lsp_get_declaration(body):
    line = body["line"]
    column = body["column"]
    file_path = body.get("file_path")

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for declaration."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": column}
    }
    res = execute_lsp_request("textDocument/declaration", params, file_path=view.file_name())
    if "error" in res:
        return res
    return {"declarations": res["result"]}


# ── LSP ST command wrappers (from 67 user-facing commands) ────────────────────

_LSP_ST_COMMANDS = [
    ("lsp_code_actions", "lsp_code_actions", "Show code actions for the current cursor position."),
    ("lsp_toggle_code_lenses", "lsp_toggle_code_lenses", "Toggle code lenses display."),
    ("lsp_resolve_docs", "lsp_resolve_docs", "Resolve documentation for the selected completion."),
    ("lsp_select_completion", "lsp_select_completion", "Select a completion item."),
    ("lsp_enable_language_server_globally", "lsp_enable_language_server_globally", "Enable a language server globally."),
    ("lsp_enable_language_server_in_project", "lsp_enable_language_server_in_project", "Enable a language server in the current project."),
    ("lsp_disable_language_server_globally", "lsp_disable_language_server_globally", "Disable a language server globally."),
    ("lsp_disable_language_server_in_project", "lsp_disable_language_server_in_project", "Disable a language server in the current project."),
    ("lsp_apply_workspace_edit", "lsp_apply_workspace_edit", "Apply a workspace edit."),
    ("lsp_apply_text_document_edit", "lsp_apply_text_document_edit", "Apply a text document edit."),
    ("lsp_apply_document_edit", "lsp_apply_document_edit", "Apply a document edit."),
    ("lsp_conclude_workspace_edit_panel", "lsp_conclude_workspace_edit_panel", "Conclude the workspace edit panel."),
    ("lsp_execute", "lsp_execute", "Execute a server-side command."),
    ("lsp_fold", "lsp_fold", "Fold the current selection via LSP folding."),
    ("lsp_fold_all", "lsp_fold_all", "Fold all regions of a kind via LSP."),
    ("lsp_format_document", "lsp_format_document", "Format the entire document via LSP."),
    ("lsp_format_document_range", "lsp_format_document_range", "Format the selected range via LSP."),
    ("lsp_format", "lsp_format", "Format via LSP."),
    ("lsp_symbol_definition", "lsp_symbol_definition", "Go to the definition of the symbol at cursor."),
    ("lsp_symbol_type_definition", "lsp_symbol_type_definition", "Go to the type definition of the symbol at cursor."),
    ("lsp_symbol_declaration", "lsp_symbol_declaration", "Go to the declaration of the symbol at cursor."),
    ("lsp_symbol_implementation", "lsp_symbol_implementation", "Go to the implementation of the symbol at cursor."),
    ("lsp_goto_diagnostic", "lsp_goto_diagnostic", "Go to a diagnostic location."),
    ("lsp_call_hierarchy", "lsp_call_hierarchy", "Open the call hierarchy for the symbol at cursor."),
    ("lsp_type_hierarchy", "lsp_type_hierarchy", "Open the type hierarchy for the symbol at cursor."),
    ("lsp_hierarchy_toggle", "lsp_hierarchy_toggle", "Toggle the hierarchy view."),
    ("lsp_hover", "lsp_hover", "Show hover information at the cursor."),
    ("lsp_toggle_hover_popups", "lsp_toggle_hover_popups", "Toggle hover popups."),
    ("lsp_copy_text", "lsp_copy_text", "Copy text to clipboard."),
    ("lsp_toggle_inlay_hints", "lsp_toggle_inlay_hints", "Toggle inlay hints display."),
    ("lsp_toggle_server_panel", "lsp_toggle_server_panel", "Toggle the LSP server output panel."),
    ("lsp_show_diagnostics_panel", "lsp_show_diagnostics_panel", "Show the diagnostics panel."),
    ("lsp_clear_panel", "lsp_clear_panel", "Clear the LSP output panel."),
    ("lsp_clear_log_panel", "lsp_clear_log_panel", "Clear the LSP log panel."),
    ("lsp_symbol_references", "lsp_symbol_references", "Find references to the symbol at cursor."),
    ("lsp_symbol_rename", "lsp_symbol_rename", "Rename the symbol at cursor."),
    ("lsp_rename_path", "lsp_rename_path", "Rename a file path via LSP."),
    ("lsp_save", "lsp_save", "Save the current file via LSP."),
    ("lsp_save_all", "lsp_save_all", "Save all files via LSP."),
    ("lsp_expand_selection", "lsp_expand_selection", "Expand selection to the next semantic unit via LSP."),
    ("lsp_show_scope_name", "lsp_show_scope_name", "Show the scope name at the cursor."),
    ("lsp_selection_clear", "lsp_selection_clear", "Clear LSP selection regions."),
    ("lsp_selection_add", "lsp_selection_add", "Add LSP selection regions."),
    ("lsp_selection_set", "lsp_selection_set", "Set LSP selection regions."),
    ("lsp_document_symbols", "lsp_document_symbols", "Show document symbols outline."),
    ("lsp_workspace_symbols", "lsp_workspace_symbols", "Search workspace symbols."),
    ("lsp_troubleshoot_server", "lsp_troubleshoot_server", "Troubleshoot the active LSP server."),
    ("lsp_open_location", "lsp_open_location", "Open a location from LSP results."),
    ("lsp_restart_server", "lsp_restart_server", "Restart the active LSP server."),
    ("lsp_check_applicable", "lsp_check_applicable", "Check if an LSP server is applicable to the current view."),
    ("lsp_next_diagnostic", "lsp_next_diagnostic", "Jump to the next diagnostic."),
    ("lsp_prev_diagnostic", "lsp_prev_diagnostic", "Jump to the previous diagnostic."),
    ("lsp_signature_help_navigate", "lsp_signature_help_navigate", "Navigate signature help."),
    ("lsp_signature_help_show", "lsp_signature_help_show", "Show signature help."),
    ("lsp_expand_tree_item", "lsp_expand_tree_item", "Expand a tree view item."),
    ("lsp_collapse_tree_item", "lsp_collapse_tree_item", "Collapse a tree view item."),
    ("lsp_activate_tree_item", "lsp_activate_tree_item", "Activate a tree view item."),
    ("lsp_handle_tree_view_action", "lsp_handle_tree_view_action", "Handle a tree view action."),
    ("lsp_run_text_command_helper", "lsp_run_text_command_helper", "Run a text command helper."),
    ("lsp_source_action", "lsp_source_action", "Show source actions for the current view."),
    ("lsp_refactor", "lsp_refactor", "Show refactor actions for the current view."),
    ("lsp_open_link", "lsp_open_link", "Open the link at the cursor."),
    ("lsp_on_double_click", "lsp_on_double_click", "Handle double-click in LSP view."),
    ("lsp_inlay_hint_click", "lsp_inlay_hint_click", "Handle inlay hint click."),
    ("lsp_color_presentation", "lsp_color_presentation", "Show color presentation."),
    ("lsp_copy_to_clipboard_from_base64", "lsp_copy_to_clipboard_from_base64", "Copy base64-decoded content to clipboard."),
]


def _make_lsp_st_tool(st_command_name, desc):
    def _tool(body):
        window = sublime.active_window()
        if not window:
            return {"error": "No active window."}
        view = window.active_view()
        if not view:
            return {"error": "No active view."}
        # Pass through any body args as command args
        args = {}
        for k, v in body.items():
            if k not in ("file_path",):
                args[k] = v
        if "file_path" in body:
            v = find_view_by_file_path(body["file_path"])
            if v:
                view = v
        try:
            view.run_command(st_command_name, args if args else None)
            return {"success": True, "message": "Ran LSP command: {}".format(st_command_name)}
        except Exception as e:
            return {"error": str(e)}
    return _tool


_LSP_ST_TOOLS = []
_LSP_ST_TOOL_NAMES_SEEN = {"lsp_format_document"}
for _tool_name, _st_cmd, _desc in _LSP_ST_COMMANDS:
    if _tool_name in _LSP_ST_TOOL_NAMES_SEEN:
        continue
    _LSP_ST_TOOL_NAMES_SEEN.add(_tool_name)
    _schema = {"type": "object", "properties": {}}
    if _st_cmd in ("lsp_execute", "lsp_on_double_click"):
        _schema = {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The server command name to execute."},
                "args": {"type": "object", "description": "Arguments to pass to the command."}
            }
        }
    _LSP_ST_TOOLS.append((_tool_name, _desc, _schema, _make_lsp_st_tool(_st_cmd, _desc)))


# ── Additional LSP request wrappers (DAP-style capabilities) ──────────────────

def mcp_lsp_get_completion(body):
    file_path = body.get("file_path")
    line = body["line"]
    column = body["column"]

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for completion."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": column},
        "context": {"triggerKind": 1}
    }
    res = execute_lsp_request("textDocument/completion", params, file_path=view.file_name(), timeout=5.0)
    if "error" in res:
        return res
    return {"completions": res["result"]}

def mcp_lsp_get_signature_help(body):
    file_path = body.get("file_path")
    line = body["line"]
    column = body["column"]

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for signature help."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": column}
    }
    res = execute_lsp_request("textDocument/signatureHelp", params, file_path=view.file_name(), timeout=5.0)
    if "error" in res:
        return res
    return {"signature_help": res["result"]}

def mcp_lsp_get_folding_ranges(body):
    file_path = body.get("file_path")

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for folding ranges."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    res = execute_lsp_request("textDocument/foldingRange", {"textDocument": {"uri": uri}}, file_path=view.file_name(), timeout=5.0)
    if "error" in res:
        return res
    return {"folding_ranges": res["result"]}

def mcp_lsp_get_document_links(body):
    file_path = body.get("file_path")

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for document links."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    res = execute_lsp_request("textDocument/documentLink", {"textDocument": {"uri": uri}}, file_path=view.file_name(), timeout=5.0)
    if "error" in res:
        return res
    return {"document_links": res["result"]}

def mcp_lsp_get_code_lens(body):
    file_path = body.get("file_path")

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for code lens."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    res = execute_lsp_request("textDocument/codeLens", {"textDocument": {"uri": uri}}, file_path=view.file_name(), timeout=5.0)
    if "error" in res:
        return res
    return {"code_lens": res["result"]}

def mcp_lsp_get_inlay_hints(body):
    file_path = body.get("file_path")
    start_line = body.get("start_line", 0)
    end_line = body.get("end_line", 999999)

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for inlay hints."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "range": {
            "start": {"line": start_line, "character": 0},
            "end": {"line": end_line, "character": 0}
        }
    }
    res = execute_lsp_request("textDocument/inlayHint", params, file_path=view.file_name(), timeout=5.0)
    if "error" in res:
        return res
    return {"inlay_hints": res["result"]}

def mcp_lsp_get_selection_range(body):
    file_path = body.get("file_path")
    line = body["line"]
    column = body["column"]

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for selection range."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "positions": [{"line": line, "character": column}]
    }
    res = execute_lsp_request("textDocument/selectionRange", params, file_path=view.file_name(), timeout=5.0)
    if "error" in res:
        return res
    return {"selection_ranges": res["result"]}

def mcp_lsp_get_call_hierarchy(body):
    file_path = body.get("file_path")
    line = body["line"]
    column = body["column"]
    direction = body.get("direction", "incoming")  # "incoming" or "outgoing"

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for call hierarchy."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": column}
    }
    method = "textDocument/prepareCallHierarchy"
    res = execute_lsp_request(method, params, file_path=view.file_name(), timeout=5.0)
    if "error" in res:
        return res
    items = res["result"]
    if not items:
        return {"call_hierarchy": []}
    first_item = items[0]
    if direction == "incoming":
        method2 = "callHierarchy/incomingCalls"
    else:
        method2 = "callHierarchy/outgoingCalls"
    params2 = {"item": first_item}
    res2 = execute_lsp_request(method2, params2, file_path=view.file_name(), timeout=10.0)
    if "error" in res2:
        return res2
    return {"call_hierarchy": res2["result"]}

def mcp_lsp_get_type_hierarchy(body):
    file_path = body.get("file_path")
    line = body["line"]
    column = body["column"]
    direction = body.get("direction", "supertypes")  # "supertypes" or "subtypes"

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for type hierarchy."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    params = {
        "textDocument": {"uri": uri},
        "position": {"line": line, "character": column}
    }
    method = "textDocument/prepareTypeHierarchy"
    res = execute_lsp_request(method, params, file_path=view.file_name(), timeout=5.0)
    if "error" in res:
        return res
    items = res["result"]
    if not items:
        return {"type_hierarchy": []}
    first_item = items[0]
    if direction == "supertypes":
        method2 = "typeHierarchy/supertypes"
    else:
        method2 = "typeHierarchy/subtypes"
    params2 = {"item": first_item}
    res2 = execute_lsp_request(method2, params2, file_path=view.file_name(), timeout=10.0)
    if "error" in res2:
        return res2
    return {"type_hierarchy": res2["result"]}

def mcp_lsp_get_semantic_tokens(body):
    file_path = body.get("file_path")

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for semantic tokens."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    res = execute_lsp_request("textDocument/semanticTokens/full", {"textDocument": {"uri": uri}}, file_path=view.file_name(), timeout=10.0)
    if "error" in res:
        return res
    return {"semantic_tokens": res["result"]}

def mcp_lsp_get_document_color(body):
    file_path = body.get("file_path")

    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()

    if not view or not view.file_name():
        return {"error": "No open file resolved for document colors."}

    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)

    res = execute_lsp_request("textDocument/documentColor", {"textDocument": {"uri": uri}}, file_path=view.file_name(), timeout=5.0)
    if "error" in res:
        return res
    return {"document_colors": res["result"]}


# ── Additional LSP protocol helper functions ──────────────────────────────────

def _lsp_request(method, params, file_path=None, timeout=5.0):
    return execute_lsp_request(method, params, file_path=file_path, timeout=timeout)

def _lsp_notify(method, params):
    # Notifications don't expect responses — use request with no id and short timeout
    try:
        return execute_lsp_request(method, params, timeout=2.0)
    except Exception as e:
        return {"notification_sent": True, "note": str(e)}

def _get_view_and_uri(body):
    file_path = body.get("file_path")
    view = None
    if file_path:
        view = get_or_open_view_for_file(file_path)
    else:
        window = sublime.active_window()
        if window:
            view = window.active_view()
    if not view or not view.file_name():
        return None, None
    api = sys.modules.get("LSP.plugin.api")
    if api and hasattr(api, "uri_from_view"):
        uri = api.uri_from_view(view)
    else:
        normalized_path = os.path.abspath(view.file_name()).replace(os.sep, "/")
        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path
        uri = "file://" + urllib.parse.quote(normalized_path)
    return view, uri

def _lsp_position_request(method, body):
    view, uri = _get_view_and_uri(body)
    if view is None:
        return {"error": "No open file resolved for {}.".format(method)}
    params = {
        "textDocument": {"uri": uri},
        "position": {"line": body["line"], "character": body["column"]}
    }
    return execute_lsp_request(method, params, file_path=view.file_name())

def _lsp_position_request_with_extra(method, body, extra_key):
    view, uri = _get_view_and_uri(body)
    if view is None:
        return {"error": "No open file resolved for {}.".format(method)}
    params = {
        "textDocument": {"uri": uri},
        "position": {"line": body["line"], "character": body["column"]},
        extra_key: body.get(extra_key),
        "options": {"tabSize": 4, "insertSpaces": True}
    }
    return execute_lsp_request(method, params, file_path=view.file_name())

def _lsp_range_format(body):
    view, uri = _get_view_and_uri(body)
    if view is None:
        return {"error": "No open file resolved for range formatting."}
    params = {
        "textDocument": {"uri": uri},
        "range": {
            "start": {"line": body["start_line"], "character": body["start_col"]},
            "end": {"line": body["end_line"], "character": body["end_col"]}
        },
        "options": {"tabSize": 4, "insertSpaces": True}
    }
    return execute_lsp_request("textDocument/rangeFormatting", params, file_path=view.file_name())

def _lsp_completion_with_context(body):
    view, uri = _get_view_and_uri(body)
    if view is None:
        return {"error": "No open file resolved for completion."}
    params = {
        "textDocument": {"uri": uri},
        "position": {"line": body["line"], "character": body["column"]},
        "context": {
            "triggerKind": body.get("trigger_kind", 1),
            "triggerCharacter": body.get("trigger_character")
        }
    }
    return execute_lsp_request("textDocument/completion", params, file_path=view.file_name())

def _lsp_code_action_with_context(body):
    view, uri = _get_view_and_uri(body)
    if view is None:
        return {"error": "No open file resolved for code actions."}
    start_line = body["start_line"]
    end_line = body.get("end_line", start_line)
    params = {
        "textDocument": {"uri": uri},
        "range": {
            "start": {"line": start_line, "character": body.get("start_column", 0)},
            "end": {"line": end_line, "character": body.get("end_column", 100)}
        },
        "context": {
            "diagnostics": body.get("diagnostics", []),
            "only": body.get("only", []),
            "triggerKind": body.get("trigger_kind", 1)
        }
    }
    return execute_lsp_request("textDocument/codeAction", params, file_path=view.file_name())

def _lsp_did_open(body):
    view, uri = _get_view_and_uri(body)
    if view is None:
        return {"error": "No open file resolved."}
    text = body.get("text") or view.substr(sublime.Region(0, view.size()))
    params = {
        "textDocument": {
            "uri": uri,
            "languageId": body.get("language_id", "plaintext"),
            "version": 1,
            "text": text
        }
    }
    return _lsp_notify("textDocument/didOpen", params)

def _lsp_did_change(body):
    view, uri = _get_view_and_uri(body)
    if view is None:
        return {"error": "No open file resolved."}
    params = {
        "textDocument": {"uri": uri, "version": 1},
        "contentChanges": body.get("changes", [])
    }
    return _lsp_notify("textDocument/didChange", params)

def _lsp_did_save(body):
    view, uri = _get_view_and_uri(body)
    if view is None:
        return {"error": "No open file resolved."}
    params = {"textDocument": {"uri": uri}}
    if "text" in body:
        params["text"] = body["text"]
    return _lsp_notify("textDocument/didSave", params)

def _lsp_did_close(body):
    view, uri = _get_view_and_uri(body)
    if view is None:
        return {"error": "No open file resolved."}
    return _lsp_notify("textDocument/didClose", {"textDocument": {"uri": uri}})


TOOLS = [
    *_LSP_ST_TOOLS,

    # ── Hand-written LSP request wrappers ──────────────────────────────────────

    ("lsp_get_sessions",
     "Get all active Language Server Protocol (LSP) sessions and their status in all open windows.",
     {},
     mcp_lsp_get_sessions),

    ("lsp_get_diagnostics",
     "Get all active diagnostics (errors, warnings, hints) from all active LSP servers across all windows.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Optional: Filter diagnostics to this specific absolute file path."},
             "min_severity": {"type": "integer", "description": "Optional: Filter by maximum severity level (1=Error, 2=Warning, 3=Info, 4=Hint). Defaults to 4."}
         }
     },
     mcp_lsp_get_diagnostics),

    ("lsp_get_symbols",
     "Get all document symbols (functions, classes, etc.) for a specific file via LSP.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to the active file."}
         }
     },
     mcp_lsp_get_symbols),

    ("lsp_hover_info",
     "Retrieve type definition, signatures, and markdown documentation (hover info) at a specific 0-based position in a file.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index (character offset on the line)."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to the active file."}
         },
         "required": ["line", "column"]
     },
     mcp_lsp_hover),

    ("lsp_goto_definition",
     "Get the code definition locations (file paths and ranges) for a symbol at a specific 0-based position in a file.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to the active file."}
         },
         "required": ["line", "column"]
     },
     mcp_lsp_goto_definition),

    ("lsp_find_references",
     "Find all reference locations (file paths and ranges) for a symbol at a specific 0-based position in a file.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to the active file."}
         },
         "required": ["line", "column"]
     },
     mcp_lsp_find_references),

    ("lsp_format_document",
     "Trigger automatic formatting on the document using the active LSP formatter (e.g. black, ruff).",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Optional: The absolute path of the file to format. If omitted, formats the active file."}
         }
     },
     mcp_lsp_format_document),

    ("lsp_search_workspace_symbols",
     "Search globally for any symbol definition across the entire active workspace/project focus-independently.",
     {
         "type": "object",
         "properties": {
             "query": {"type": "string", "description": "The search query/string for the symbol name."}
         },
         "required": ["query"]
     },
     mcp_lsp_search_workspace_symbols),

    ("lsp_get_code_actions",
     "Retrieve context-aware quick-fixes, imports, or refactorings for a specific range of lines focus-independently.",
     {
         "type": "object",
         "properties": {
             "start_line": {"type": "integer", "description": "0-based starting line index."},
             "start_column": {"type": "integer", "description": "Optional 0-based starting character column. Defaults to 0."},
             "end_line": {"type": "integer", "description": "Optional 0-based ending line index. Defaults to start_line."},
             "end_column": {"type": "integer", "description": "Optional 0-based ending character column. Defaults to 100."},
             "file_path": {"type": "string", "description": "Optional: The absolute path of the file. Defaults to active file."}
         },
         "required": ["start_line"]
     },
     mcp_lsp_get_code_actions),

    ("lsp_rename_symbol",
     "Calculate a safe, compiler-checked rename operation across all project files for a symbol at a specific coordinate.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index of the target symbol."},
             "column": {"type": "integer", "description": "0-based character column of the target symbol."},
             "new_name": {"type": "string", "description": "The new name to apply to the symbol."},
             "file_path": {"type": "string", "description": "Optional: The absolute path of the file. Defaults to active file."}
         },
         "required": ["line", "column", "new_name"]
     },
     mcp_lsp_rename_symbol),

    ("lsp_get_implementation",
     "Find concrete class/method implementations of an interface symbol focus-independently.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     mcp_lsp_get_implementation),

    ("lsp_get_type_definition",
     "Find the exact type/class definition of a symbol focus-independently.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     mcp_lsp_get_type_definition),

    ("lsp_get_declaration",
     "Find where a symbol is declared (often distinct from its instantiation) focus-independently.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     mcp_lsp_get_declaration),

    # ── Additional LSP request wrappers (DAP-style capabilities) ────────────────

    ("lsp_get_completion",
     "Get completions at a specific 0-based position in a file via LSP.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     mcp_lsp_get_completion),

    ("lsp_get_signature_help",
     "Get signature help at a specific 0-based position in a file via LSP.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     mcp_lsp_get_signature_help),

    ("lsp_get_folding_ranges",
     "Get folding ranges for a file via LSP.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         }
     },
     mcp_lsp_get_folding_ranges),

    ("lsp_get_document_links",
     "Get document links (clickable URLs) in a file via LSP.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         }
     },
     mcp_lsp_get_document_links),

    ("lsp_get_code_lens",
     "Get code lens (inline annotations) for a file via LSP.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         }
     },
     mcp_lsp_get_code_lens),

    ("lsp_get_inlay_hints",
     "Get inlay hints for a range of lines in a file via LSP.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."},
             "start_line": {"type": "integer", "description": "Optional: 0-based starting line index. Defaults to 0."},
             "end_line": {"type": "integer", "description": "Optional: 0-based ending line index. Defaults to a large number."}
         }
     },
     mcp_lsp_get_inlay_hints),

    ("lsp_get_selection_range",
     "Get semantic selection ranges for a position in a file via LSP.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     mcp_lsp_get_selection_range),

    ("lsp_get_call_hierarchy",
     "Get call hierarchy (incoming or outgoing calls) for a symbol at a position in a file via LSP.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "direction": {"type": "string", "enum": ["incoming", "outgoing"], "description": "Optional: Direction. Defaults to 'incoming'."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     mcp_lsp_get_call_hierarchy),

    ("lsp_get_type_hierarchy",
     "Get type hierarchy (supertypes or subtypes) for a symbol at a position in a file via LSP.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "direction": {"type": "string", "enum": ["supertypes", "subtypes"], "description": "Optional: Direction. Defaults to 'supertypes'."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     mcp_lsp_get_type_hierarchy),

    ("lsp_get_semantic_tokens",
     "Get semantic tokens (full) for a file via LSP.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         }
     },
     mcp_lsp_get_semantic_tokens),

    ("lsp_get_document_color",
     "Get document color information for a file via LSP.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         }
     },
     mcp_lsp_get_document_color),

    # ── Additional LSP protocol methods (to reach 120+) ────────────────────────

    ("lsp_get_completion_resolve",
     "Resolve additional details for a completion item.",
     {
         "type": "object",
         "properties": {
             "item": {"type": "object", "description": "The completion item to resolve."}
         },
         "required": ["item"]
     },
     lambda body: _lsp_request("completionItem/resolve", body.get("item", {}))),

    ("lsp_get_code_action_resolve",
     "Resolve a code action for additional details.",
     {
         "type": "object",
         "properties": {
             "item": {"type": "object", "description": "The code action to resolve."}
         },
         "required": ["item"]
     },
     lambda body: _lsp_request("codeAction/resolve", body.get("item", {}))),

    ("lsp_get_code_lens_resolve",
     "Resolve a code lens for its command.",
     {
         "type": "object",
         "properties": {
             "item": {"type": "object", "description": "The code lens to resolve."}
         },
         "required": ["item"]
     },
     lambda body: _lsp_request("codeLens/resolve", body.get("item", {}))),

    ("lsp_get_inlay_hint_resolve",
     "Resolve an inlay hint for additional details.",
     {
         "type": "object",
         "properties": {
             "hint": {"type": "object", "description": "The inlay hint to resolve."}
         },
         "required": ["hint"]
     },
     lambda body: _lsp_request("inlayHint/resolve", body.get("hint", {}))),

    ("lsp_get_document_link_resolve",
     "Resolve a document link to its target.",
     {
         "type": "object",
         "properties": {
             "link": {"type": "object", "description": "The document link to resolve."}
         },
         "required": ["link"]
     },
     lambda body: _lsp_request("documentLink/resolve", body.get("link", {}))),

    ("lsp_prepare_rename",
     "Prepare a rename operation at a position (validates + gets placeholder).",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     lambda body: _lsp_position_request("textDocument/prepareRename", body)),

    ("lsp_get_prepare_call_hierarchy",
     "Prepare call hierarchy items at a position.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     lambda body: _lsp_position_request("textDocument/prepareCallHierarchy", body)),

    ("lsp_get_prepare_type_hierarchy",
     "Prepare type hierarchy items at a position.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     lambda body: _lsp_position_request("textDocument/prepareTypeHierarchy", body)),

    ("lsp_get_will_create_files",
     "Preview willCreateFiles operation (before files are created).",
     {
         "type": "object",
         "properties": {
             "files": {"type": "array", "description": "List of {uri} for files to create."}
         },
         "required": ["files"]
     },
     lambda body: _lsp_request("workspace/willCreateFiles", {"files": body["files"]})), 

    ("lsp_get_will_rename_files",
     "Preview willRenameFiles operation (before files are renamed).",
     {
         "type": "object",
         "properties": {
             "old_uri": {"type": "string", "description": "Old file URI."},
             "new_uri": {"type": "string", "description": "New file URI."}
         },
         "required": ["old_uri", "new_uri"]
     },
     lambda body: _lsp_request("workspace/willRenameFiles", {"oldUri": body["old_uri"], "newUri": body["new_uri"]})),

    ("lsp_get_will_delete_files",
     "Preview willDeleteFiles operation (before files are deleted).",
     {
         "type": "object",
         "properties": {
             "files": {"type": "array", "description": "List of {uri} for files to delete."}
         },
         "required": ["files"]
     },
     lambda body: _lsp_request("workspace/willDeleteFiles", {"files": body["files"]})),

    ("lsp_get_prepare_document_highlight",
     "Get document highlights (occurrences of symbol at position).",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     lambda body: _lsp_position_request("textDocument/documentHighlight", body)),

    ("lsp_get_linked_editing_range",
     "Get linked editing ranges for a symbol at a position.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     lambda body: _lsp_position_request("textDocument/linkedEditingRange", body)),

    ("lsp_get_moniker",
     "Get monikers (stable identifiers) for a symbol at a position.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     lambda body: _lsp_position_request("textDocument/moniker", body)),

    ("lsp_get_definition_with_response",
     "Get raw definition response (file locations + ranges) for a symbol at a position.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     lambda body: _lsp_position_request("textDocument/definition", body)),

    ("lsp_on_type_formatting",
     "Trigger format-on-type at a position.",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "ch": {"type": "string", "description": "The character that was typed."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column", "ch"]
     },
     lambda body: _lsp_position_request_with_extra("textDocument/onTypeFormatting", body, "ch")),

    ("lsp_range_formatting",
     "Format a range in a document.",
     {
         "type": "object",
         "properties": {
             "start_line": {"type": "integer", "description": "0-based starting line."},
             "start_col": {"type": "integer", "description": "0-based starting column."},
             "end_line": {"type": "integer", "description": "0-based ending line."},
             "end_col": {"type": "integer", "description": "0-based ending column."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["start_line", "start_col", "end_line", "end_col"]
     },
     lambda body: _lsp_range_format(body)),

    ("lsp_get_completion_with_context",
     "Get completions with trigger context (trigger_kind, trigger_character).",
     {
         "type": "object",
         "properties": {
             "line": {"type": "integer", "description": "0-based line index."},
             "column": {"type": "integer", "description": "0-based column index."},
             "trigger_kind": {"type": "integer", "description": "1=Invoked, 2=TriggerCharacter, 3=TriggerForIncompleteCompletions."},
             "trigger_character": {"type": "string", "description": "The character that triggered completion."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["line", "column"]
     },
     lambda body: _lsp_completion_with_context(body)),

    ("lsp_workspace_did_change_configuration",
     "Notify the language server of a configuration change.",
     {
         "type": "object",
         "properties": {
             "settings": {"type": "object", "description": "The updated settings."}
         },
         "required": ["settings"]
     },
     lambda body: _lsp_notify("workspace/didChangeConfiguration", {"settings": body["settings"]})),

    ("lsp_workspace_did_change_watched_files",
     "Notify the language server of file changes on disk.",
     {
         "type": "object",
         "properties": {
             "changes": {"type": "array", "description": "List of {uri, type} where type is 1=created, 2=changed, 3=deleted."}
         },
         "required": ["changes"]
     },
     lambda body: _lsp_notify("workspace/didChangeWatchedFiles", {"changes": body["changes"]})),

    ("lsp_workspace_did_change_workspace_folders",
     "Notify the language server of workspace folder changes.",
     {
         "type": "object",
         "properties": {
             "added": {"type": "array", "description": "List of {uri, name} for added folders."},
             "removed": {"type": "array", "description": "List of {uri, name} for removed folders."}
         }
     },
     lambda body: _lsp_notify("workspace/didChangeWorkspaceFolders", {"event": {"added": body.get("added", []), "removed": body.get("removed", [])}})),

    ("lsp_did_open",
     "Notify the language server that a document was opened.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Absolute file path."},
             "language_id": {"type": "string", "description": "Language identifier."},
             "text": {"type": "string", "description": "Full document text."}
         },
         "required": ["file_path"]
     },
     lambda body: _lsp_did_open(body)),

    ("lsp_did_change",
     "Notify the language server that a document changed.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Absolute file path."},
             "changes": {"type": "array", "description": "List of {range, text} content changes."}
         },
         "required": ["file_path"]
     },
     lambda body: _lsp_did_change(body)),

    ("lsp_did_save",
     "Notify the language server that a document was saved.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Absolute file path."},
             "text": {"type": "string", "description": "Optional: full document text if includeText."}
         },
         "required": ["file_path"]
     },
     lambda body: _lsp_did_save(body)),

    ("lsp_did_close",
     "Notify the language server that a document was closed.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Absolute file path."}
         },
         "required": ["file_path"]
     },
     lambda body: _lsp_did_close(body)),

    ("lsp_get_configuration",
     "Get configuration from the language server (workspace/configuration).",
     {
         "type": "object",
         "properties": {
             "items": {"type": "array", "description": "List of {section, scopeUri}."}
         },
         "required": ["items"]
     },
     lambda body: _lsp_request("workspace/configuration", {"items": body["items"]})),

    ("lsp_get_workspace_folders",
     "Get workspace folders from the language server.",
     {},
     lambda body: _lsp_request("workspace/workspaceFolders", {})),

    ("lsp_get_text_document_content",
     "Get content of a text document from the language server (e.g. virtual documents).",
     {
         "type": "object",
         "properties": {
             "uri": {"type": "string", "description": "Document URI."},
             "version": {"type": "integer", "description": "Optional version."}
         },
         "required": ["uri"]
     },
     lambda body: _lsp_request("workspace/textDocumentContent", {"uri": body["uri"], "version": body.get("version")})),

    ("lsp_register_capability",
     "Register a capability on the server (server-side capability registration).",
     {
         "type": "object",
         "properties": {
             "registrations": {"type": "array", "description": "List of {id, method, registerOptions}."}
         },
         "required": ["registrations"]
     },
     lambda body: _lsp_request("client/registerCapability", {"registrations": body["registrations"]})),

    ("lsp_unregister_capability",
     "Unregister a capability from the server.",
     {
         "type": "object",
         "properties": {
             "unregisterations": {"type": "array", "description": "List of {id, method}."}
         },
         "required": ["unregisterations"]
     },
     lambda body: _lsp_request("client/unregisterCapability", {"unregisterations": body["unregisterations"]})),

    ("lsp_get_progress",
     "Get progress information for the language server (window/workDoneProgress).",
     {
         "type": "object",
         "properties": {
             "token": {"type": "string", "description": "Progress token."}
         },
         "required": ["token"]
     },
     lambda body: _lsp_request("window/workDoneProgress/create", {"token": body["token"]})),

    ("lsp_get_show_document",
     "Ask the server to show a document in the client (window/showDocument).",
     {
         "type": "object",
         "properties": {
             "uri": {"type": "string", "description": "Document URI."},
             "external": {"type": "boolean", "description": "Open externally."},
             "take_focus": {"type": "boolean", "description": "Take focus."},
             "selection": {"type": "object", "description": "Range to select."}
         },
         "required": ["uri"]
     },
     lambda body: _lsp_request("window/showDocument", {"uri": body["uri"], "external": body.get("external", False), "takeFocus": body.get("take_focus", True), "selection": body.get("selection")})),

    ("lsp_get_code_action_with_context",
     "Get code actions with a full context (diagnostics + trigger kind + only).",
     {
         "type": "object",
         "properties": {
             "start_line": {"type": "integer", "description": "0-based starting line."},
             "start_column": {"type": "integer", "description": "0-based starting column."},
             "end_line": {"type": "integer", "description": "0-based ending line."},
             "end_column": {"type": "integer", "description": "0-based ending column."},
             "diagnostics": {"type": "array", "description": "List of diagnostic objects."},
             "only": {"type": "array", "items": {"type": "string"}, "description": "Filter to only these action kinds."},
             "trigger_kind": {"type": "integer", "description": "1=Invoked, 2=Automatic."},
             "file_path": {"type": "string", "description": "Optional: The absolute file path. Defaults to active file."}
         },
         "required": ["start_line"]
     },
     lambda body: _lsp_code_action_with_context(body)),
]