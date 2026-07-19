# Debugger MCP — standalone Sublime Text plugin
# Serves Debugger DAP tools over MCP SSE on port 9505.
# Refactored from debugger_mcp_tools.py (formerly an add-on to sublime-mcp).

import sublime
import sublime_plugin
import sys
import os
import json
import threading
import uuid as _uuid
import queue as _queue
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

_MCP_PORT = int(os.environ.get("DEBUGGER_MCP_PORT", 9505))


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
                print("[debugger-mcp] register_mcp_tools: '{}' already registered - skipped".format(name))
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
                "serverInfo": {"name": "debugger-mcp", "version": "1.0.0"},
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
            print("[debugger-mcp] could not bind MCP SSE on port {}: {}".format(_MCP_PORT, e))
            _server = None
    print("[debugger-mcp] MCP SSE on 127.0.0.1:{}".format(_MCP_PORT))


def _stop_server():
    global _server
    if _server:
        _server.shutdown()
        _server = None
    for q in list(_mcp_sessions.values()):
        q.put(None)
    _mcp_sessions.clear()
    print("[debugger-mcp] stopped")


def plugin_loaded():
    register_mcp_tools(TOOLS)
    _start_server()
    print("[debugger-mcp] {} tools loaded".format(len(TOOLS)))


def plugin_unloaded():
    unregister_mcp_tools(TOOLS)
    _stop_server()


# ── Debugger tool implementations (from debugger_mcp_tools.py) ────────────────

def get_debugger():
    db_mod = sys.modules.get("Debugger.modules.debugger")
    if not db_mod or not hasattr(db_mod, "Debugger"):
        return None
    for dbg in db_mod.Debugger.debuggers_for_window.values():
        if dbg.is_running():
            return dbg
    for dbg in db_mod.Debugger.debuggers_for_window.values():
        if dbg.is_open():
            return dbg
    return db_mod.Debugger.get(sublime.active_window(), create=False)

def mcp_debugger_get_state(body):
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}

    result = {
        "window_id": dbg.window.id() if hasattr(dbg, "window") else None,
        "is_open": dbg.is_open(),
        "is_running": dbg.is_running(),
        "is_paused": dbg.is_paused(),
        "sessions": []
    }

    for session in dbg.sessions:
        active_thread = None
        active_frame = None
        if session.selected_thread:
            active_thread = {
                "id": session.selected_thread.id,
                "name": session.selected_thread.name
            }
        if session.selected_frame:
            active_frame = {
                "id": session.selected_frame.id,
                "name": session.selected_frame.name,
                "file": session.selected_frame.source.path if session.selected_frame.source else None,
                "line": session.selected_frame.line
            }

        result["sessions"].append({
            "name": session.name,
            "state": str(session.state),
            "active_thread": active_thread,
            "active_frame": active_frame
        })

    return result

def mcp_debugger_get_breakpoints(body):
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}

    result = {"source_breakpoints": [], "function_breakpoints": []}
    if dbg.breakpoints:
        if dbg.breakpoints.source:
            for bp in dbg.breakpoints.source.breakpoints:
                result["source_breakpoints"].append({
                    "file": bp.file,
                    "line": bp.line,
                    "enabled": bp.enabled,
                    "condition": bp.condition,
                    "log_message": bp.log_message
                })
        if dbg.breakpoints.function:
            for bp in dbg.breakpoints.function.breakpoints:
                result["function_breakpoints"].append({
                    "name": bp.name,
                    "enabled": bp.enabled,
                    "condition": bp.dap.condition if hasattr(bp, "dap") else None
                })
    return result

def mcp_debugger_toggle_breakpoint(body):
    file_path = body["file_path"]
    line = body["line"]

    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}

    if dbg.breakpoints and dbg.breakpoints.source:
        dbg.breakpoints.source.toggle_file_line(file_path, line)
        return {"success": True, "message": "Toggled breakpoint on line {} in {}.".format(line, file_path)}
    return {"error": "Breakpoints manager not available."}

def mcp_debugger_clear_breakpoints(body):
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}

    if dbg.breakpoints:
        dbg.breakpoints.remove_all()
        return {"success": True, "message": "All breakpoints removed."}
    return {"error": "Breakpoints manager not available."}

def mcp_debugger_control(body):
    action = body["action"]
    config_name = body.get("configuration_name")

    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded or active."}

    core = sys.modules.get("Debugger.modules.core")
    if not core:
        return {"error": "Debugger core not loaded."}

    def _run_action():
        if action == "start":
            if config_name:
                configs = dbg.project.configurations
                target_config = next((c for c in configs if c.name == config_name), None)
                if target_config:
                    dbg.start(target_config)
                    return {"success": True, "message": "Debugger started with config '{}'.".format(config_name)}
                else:
                    return {"error": "Configuration '{}' not found in project configurations.".format(config_name)}
            else:
                dbg.open()
                return {"success": True, "message": "Debugger view opened."}
        elif action == "stop":
            dbg.stop()
            return {"success": True, "message": "Debugger stopped."}
        elif action == "pause":
            dbg.pause()
            return {"success": True, "message": "Debugger paused."}
        elif action == "resume":
            dbg.resume()
            return {"success": True, "message": "Debugger resumed."}
        elif action == "step_over":
            dbg.step_over()
            return {"success": True, "message": "Step over executed."}
        elif action == "step_in":
            dbg.step_in()
            return {"success": True, "message": "Step in executed."}
        elif action == "step_out":
            dbg.step_out()
            return {"success": True, "message": "Step out executed."}
        else:
            return {"error": "Unknown action: {}".format(action)}

    try:
        res = _run_action()
        return res
    except Exception as e:
        return {"error": str(e)}

def mcp_debugger_get_variables(body):
    ref = body.get("variables_reference")

    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}

    session = getattr(dbg, "session", None)
    if not session:
        return {"error": "No active debug session found."}

    core = sys.modules.get("Debugger.modules.core")
    if not core:
        return {"error": "Debugger core not loaded."}

    try:
        if ref is not None:
            coro = session.get_variables(ref)
            variables = core.run(coro)
        else:
            frame = session.selected_frame
            if not frame:
                return {"error": "Debugger is not currently paused on a stack frame."}

            core.run(session.refresh_scopes(frame))
            variables = session.variables

        result = []
        for var in variables:
            result.append({
                "name": var.name,
                "value": var.value,
                "variables_reference": var.variablesReference,
                "has_children": var.has_children,
                "evaluate_name": var.evaluateName
            })
        return {"variables": result}
    except Exception as e:
        return {"error": str(e)}

def mcp_debugger_evaluate(body):
    expression = body["expression"]

    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}

    session = getattr(dbg, "session", None)
    if not session:
        return {"error": "No active debug session found."}

    core = sys.modules.get("Debugger.modules.core")
    if not core:
        return {"error": "Debugger core not loaded."}

    try:
        coro = session.evaluate_expression(expression, context="repl")
        response = core.run(coro)
        return {
            "result": response.result,
            "variables_reference": response.variablesReference,
            "type": response.type
        }
    except Exception as e:
        return {"error": str(e)}

def mcp_debugger_get_callstack(body):
    thread_id = body.get("thread_id")

    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}

    session = getattr(dbg, "session", None)
    if not session:
        return {"error": "No active debug session found."}

    core = sys.modules.get("Debugger.modules.core")
    if not core:
        return {"error": "Debugger core not loaded."}

    try:
        result = {"threads": []}
        if thread_id is not None:
            coro = session.stack_trace(thread_id)
            frames = core.run(coro)
            result["threads"].append({
                "thread_id": thread_id,
                "frames": [{
                    "id": f.id,
                    "name": f.name,
                    "file": f.source.path if f.source else None,
                    "line": f.line,
                    "column": f.column
                } for f in frames]
            })
        else:
            if session.selected_thread:
                coro = session.stack_trace(session.selected_thread.id)
                frames = core.run(coro)
                result["threads"].append({
                    "thread_id": session.selected_thread.id,
                    "name": session.selected_thread.name,
                    "active": True,
                    "frames": [{
                        "id": f.id,
                        "name": f.name,
                        "file": f.source.path if f.source else None,
                        "line": f.line,
                        "column": f.column
                    } for f in frames]
                })
        return result
    except Exception as e:
        return {"error": str(e)}

def mcp_debugger_get_exception_info(body):
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}

    session = getattr(dbg, "session", None)
    if not session:
        return {"error": "No active debug session found."}

    core = sys.modules.get("Debugger.modules.core")
    if not core:
        return {"error": "Debugger core not loaded."}

    thread_id = body.get("thread_id")
    if thread_id is None:
        if session.selected_thread:
            thread_id = session.selected_thread.id
        else:
            return {"error": "No thread selected and no thread_id specified."}

    try:
        coro = session.exception_info(thread_id)
        info = core.run(coro)
        return {
            "exception_id": info.exceptionId,
            "description": info.description,
            "break_mode": info.breakMode,
            "details": {
                "message": info.details.message if info.details else None,
                "type_name": info.details.typeName if info.details else None,
                "stack_trace": info.details.stackTrace if info.details else None
            } if info.details else None
        }
    except Exception as e:
        return {"error": str(e)}

def mcp_debugger_add_watch_expression(body):
    expression = body["expression"]
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}

    if dbg.watch:
        dbg.watch.add(expression)
        return {"success": True, "message": "Added watch expression: '{}'.".format(expression)}
    return {"error": "Watch manager not available."}

def mcp_debugger_get_watch_expressions(body):
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}

    result = {"watch_expressions": []}
    if dbg.watch:
        for expr in dbg.watch.expressions:
            val = None
            if expr.evaluate_response:
                val = {
                    "value": expr.evaluate_response.value,
                    "has_children": expr.evaluate_response.has_children
                }
            result["watch_expressions"].append({
                "expression": expr.value,
                "message": expr.message,
                "evaluation": val
            })
    return result

def mcp_debugger_add_function_breakpoint(body):
    name = body["name"]
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}

    if dbg.breakpoints and dbg.breakpoints.function:
        dbg.breakpoints.function.add(name)
        return {"success": True, "message": "Added function breakpoint on '{}'.".format(name)}
    return {"error": "Breakpoints manager not available."}


# ── Additional DAP session-level tool implementations ──────────────────────────

def _run_coro(coro, timeout=5.0):
    core = sys.modules.get("Debugger.modules.core")
    if not core:
        return {"error": "Debugger core not loaded."}
    try:
        return core.run(coro)
    except Exception as e:
        return {"error": str(e)}


def _get_threads():
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session:
        return {"error": "No active debug session."}
    result = []
    for thread in session.threads:
        result.append({
            "id": thread.id,
            "name": thread.name,
            "state": str(thread.state) if hasattr(thread, "state") else None,
            "selected": session.selected_thread and session.selected_thread.id == thread.id,
        })
    return {"threads": result}


def _get_loaded_sources():
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session:
        return {"error": "No active debug session."}
    sources = getattr(session, "loaded_sources", [])
    return {"sources": [{"path": getattr(s, "path", None), "name": getattr(s, "name", None)} for s in sources]}


def _get_modules():
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session:
        return {"error": "No active debug session."}
    modules = getattr(session, "modules", [])
    return {"modules": [{"id": getattr(m, "id", None), "name": getattr(m, "name", None), "path": getattr(m, "path", None), "version": getattr(m, "version", None)} for m in modules]}


def _get_completions(body):
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session:
        return {"error": "No active debug session."}
    text = body["text"]
    line = body.get("line")
    column = body.get("column", 0)
    frame = session.selected_frame
    if not frame:
        return {"error": "No selected frame."}
    try:
        completions = _run_coro(session.completions(text, frame, line or frame.line, column))
        if isinstance(completions, dict) and "error" in completions:
            return completions
        return {"completions": completions if isinstance(completions, list) else []}
    except Exception as e:
        return {"error": str(e)}


def _step_back():
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}
    try:
        dbg.step_back()
        return {"success": True, "message": "Step back executed."}
    except Exception as e:
        return {"error": str(e)}


def _reverse_continue():
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}
    try:
        dbg.reverse_continue()
        return {"success": True, "message": "Reverse continue executed."}
    except Exception as e:
        return {"error": str(e)}


def _restart():
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session:
        return {"error": "No active debug session."}
    try:
        _run_coro(session.restart())
        return {"success": True, "message": "Session restarted."}
    except Exception as e:
        return {"error": str(e)}


def _disconnect():
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session:
        return {"error": "No active debug session."}
    try:
        _run_coro(session.disconnect())
        return {"success": True, "message": "Disconnected from adapter."}
    except Exception as e:
        return {"error": str(e)}


def _terminate():
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session:
        return {"error": "No active debug session."}
    try:
        _run_coro(session.terminate())
        return {"success": True, "message": "Session terminated."}
    except Exception as e:
        return {"error": str(e)}


# ── Additional DAP session method implementations ─────────────────────────────

def _session_call(method_name, body):
    """Generic dispatcher for session.* methods."""
    dbg = get_debugger()
    if not dbg:
        return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session:
        return {"error": "No active debug session."}
    method = getattr(session, method_name, None)
    if method is None:
        return {"error": "Session has no method '{}'.".format(method_name)}
    thread_id = body.get("thread_id") or (session.selected_thread.id if session.selected_thread else None)
    granularity = body.get("granularity", "line")
    try:
        coro = method(thread_id, granularity) if thread_id is not None else method()
        result = _run_coro(coro)
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}


def _step_over_session(body):
    return _session_call("step_over", body)

def _step_in_session(body):
    return _session_call("step_in", body)

def _step_out_session(body):
    return _session_call("step_out", body)

def _pause_session(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    tid = body.get("thread_id")
    try:
        _run_coro(session.pause(tid))
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _resume_session(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    tid = body.get("thread_id")
    try:
        _run_coro(session.resume(tid))
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _stop_session(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        _run_coro(session.stop())
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _expand_thread(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    tid = body.get("thread_id")
    thread = session.get_thread(tid) if tid is not None else None
    if not thread: return {"error": "Thread not found."}
    try:
        _run_coro(thread.expand())
        return {"success": True, "frames": [{"id": f.id, "name": f.name, "line": f.line} for f in (thread.frames or [])]}
    except Exception as e:
        return {"error": str(e)}

def _get_thread_by_id(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    tid = body.get("thread_id")
    thread = session.get_thread(tid) if tid is not None else None
    if not thread: return {"error": "Thread not found."}
    return {"id": thread.id, "name": thread.name, "state": str(thread.state) if hasattr(thread, "state") else None}

def _refresh_threads():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        _run_coro(session.refresh_threads())
        return {"success": True, "threads": [{"id": t.id, "name": t.name} for t in session.threads]}
    except Exception as e:
        return {"error": str(e)}

def _refresh_scopes(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    fid = body.get("frame_id")
    frame = None
    if fid is not None and session.selected_thread:
        for f in (session.selected_thread.frames or []):
            if f.id == fid: frame = f; break
    if not frame: frame = session.selected_frame
    if not frame: return {"error": "No frame found."}
    try:
        _run_coro(session.refresh_scopes(frame))
        return {"success": True, "scopes": [{"name": getattr(s, "name", ""), "variables_reference": getattr(s, "variablesReference", 0)} for s in (session.scopes or [])]}
    except Exception as e:
        return {"error": str(e)}

def _set_variable(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.set_variable(body["variables_reference"], body["name"], body["value"]))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _set_breakpoints_for_file(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        bps = body.get("breakpoints", [])
        result = _run_coro(session.set_breakpoints_for_file(body["file_path"], bps))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _set_function_breakpoints(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.set_function_breakpoints(body["names"]))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _set_data_breakpoints(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.set_data_breakpoints(body.get("breakpoints", [])))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _data_breakpoint_info(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.data_breakpoint_info(body["variables_reference"], body.get("name")))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _set_exception_filters(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.set_exception_breakpoint_filters(body.get("filters", [])))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _get_source(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.get_source(body.get("source_path"), body.get("source_reference")))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _disassemble(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.disassemble(body["memory_reference"], body.get("instruction_count", 10)))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _read_memory(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.read_memory(body["memory_reference"], body["count"]))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _session_name():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    return {"name": session.name}

def _session_state():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    return {"state": str(session.state)}

def _session_is_paused():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    return {"is_paused": session.is_paused()}

def _session_is_running():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    return {"is_running": session.is_running()}

def _session_is_stoppable():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    return {"is_stoppable": session.is_stoppable()}

def _select_thread(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    tid = body.get("thread_id")
    thread = session.get_thread(tid) if tid is not None else None
    if not thread: return {"error": "Thread not found."}
    fid = body.get("frame_id")
    frame = None
    if fid is not None:
        for f in (thread.frames or []):
            if f.id == fid: frame = f; break
    try:
        session.select(thread, frame, True)
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _add_breakpoints(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.add_breakpoints(body.get("source_breakpoints", []), body.get("function_breakpoints", [])))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _remove_session(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    name = body.get("session_name")
    for s in dbg.sessions:
        if s.name == name:
            dbg.remove_session(s)
            return {"success": True}
    return {"error": "Session not found."}

def _set_current_session(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    name = body.get("session_name")
    for s in dbg.sessions:
        if s.name == name:
            dbg.set_current_session(s)
            return {"success": True}
    return {"error": "Session not found."}

def _get_current_session():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    s = dbg.current_session
    return {"name": s.name if s else None}

def _set_configuration(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    name = body.get("configuration_name")
    for c in dbg.project.configurations:
        if c.name == name:
            dbg.set_configuration(c)
            return {"success": True}
    return {"error": "Configuration not found."}

def _run_to_line(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    try:
        dbg.run_to_current_line()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _toggle_column_breakpoint(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    try:
        dbg.toggle_column_breakpoint()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _clear_all_breakpoints():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    try:
        dbg.clear_all_breakpoints()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _refresh_phantoms():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    try:
        dbg.refresh_phantoms()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _save_data():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    try:
        dbg.save_data()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _show_disassembly(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    try:
        dbg.show_disassembly(toggle=body.get("toggle", True))
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _run_task(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.run_task(body.get("task_name")))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _get_output_panels():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    panels = []
    for p in (getattr(dbg, "output_panels", []) or []):
        panels.append({"name": getattr(p, "name", str(p))})
    return {"panels": panels}

def _dispose_terminals(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    try:
        dbg.dispose_terminals(unused_only=body.get("unused_only", False))
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _get_stepping_granularity():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    return {"granularity": str(dbg.stepping_granularity)}

def _send_custom_request(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.request(body["method"], body.get("arguments", {})))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _get_children(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.children(body["reference"]))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}

def _has_children(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    return {"has_children": session.has_children()}

def _first_non_subtle_frame(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    frames = body.get("frames", [])
    f = session.first_non_subtle_frame(frames)
    return {"frame": {"id": f.id, "name": f.name, "line": f.line} if f else None}

def _launch(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    name = body.get("configuration_name")
    no_debug = body.get("no_debug", False)
    for c in dbg.project.configurations:
        if c.name == name:
            try:
                dbg.start(no_debug, c)
                return {"success": True}
            except Exception as e:
                return {"error": str(e)}
    return {"error": "Configuration not found."}

def _run_pre_debug_task():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        _run_coro(session.run_pre_debug_task())
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _run_post_debug_task():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        _run_coro(session.run_post_debug_task())
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

def _evaluate_expression(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    try:
        result = _run_coro(session.evaluate_expression(body["expression"], context=body.get("context", "repl")))
        return {"success": True, "result": result}
    except Exception as e:
        return {"error": str(e)}


def _get_scopes():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    session = getattr(dbg, "session", None)
    if not session: return {"error": "No active debug session."}
    scopes = []
    for s in (getattr(session, "scopes", []) or []):
        scopes.append({
            "name": getattr(s, "name", ""),
            "variables_reference": getattr(s, "variablesReference", 0),
            "expensive": getattr(s, "expensive", False),
        })
    return {"scopes": scopes}


def _get_all_sessions():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    sessions = []
    for s in dbg.sessions:
        sessions.append({"name": s.name, "state": str(s.state)})
    return {"sessions": sessions}


def _get_configurations():
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    configs = []
    for c in dbg.project.configurations:
        configs.append({"name": c.name, "type": getattr(c, "type", None), "request": getattr(c, "request", None)})
    return {"configurations": configs}


def _get_adapters():
    core = sys.modules.get("Debugger.modules.core")
    if not core: return {"error": "Debugger core not loaded."}
    try:
        from .Debugger.modules.adapters import AdaptersRegistry  # noqa
        adapters = []
        for name in AdaptersRegistry.registered:
            adapters.append({"name": name})
        return {"adapters": adapters}
    except Exception:
        return {"adapters": [], "note": "Could not enumerate adapters."}


def _get_storage_path():
    core = sys.modules.get("Debugger.modules.core")
    if not core: return {"error": "Debugger core not loaded."}
    try:
        return {"path": core.debugger_storage_path(ensure_exists=False)}
    except Exception as e:
        return {"error": str(e)}


def _get_console_output(body):
    dbg = get_debugger()
    if not dbg: return {"error": "Debugger package not loaded."}
    console = getattr(dbg, "console", None)
    if not console: return {"error": "No console available."}
    tail = body.get("tail", 100)
    try:
        buf = getattr(console, "buffer", None) or ""
        lines = buf.split("\n") if isinstance(buf, str) else []
        return {"output": "\n".join(lines[-tail:]) if tail else buf}
    except Exception as e:
        return {"error": str(e)}


# ── Debugger ST command wrappers (from commands.py) ────────────────────────────

_DEBUGGER_ST_COMMANDS = [
    ("open", "Open the debugger UI."),
    ("quit", "Close/quit the debugger."),
    ("settings", "Open debugger settings."),
    ("browse_storage", "Open debugger package storage directory."),
    ("install_adapters", "Install debugger adapters."),
    ("change_configuration", "Add or select a debug configuration."),
    ("add_configuration", "Add a new debug configuration."),
    ("edit_configurations", "Edit debug configuration files."),
    ("example_projects", "Show example debugger projects."),
    ("start", "Start debugging. Optional 'configuration_name' in body."),
    ("open_and_start", "Open debugger UI and start debugging."),
    ("start_no_debug", "Start without debugging."),
    ("stop", "Stop the active debug session."),
    ("continue", "Continue execution (resume from pause)."),
    ("pause", "Pause execution."),
    ("step_over", "Step over the next line."),
    ("step_in", "Step into the next function call."),
    ("step_out", "Step out of the current function."),
    ("reverse_continue", "Reverse continue (if reversable)."),
    ("step_back", "Step backwards (if reversable)."),
    ("input_command", "Input a debugger command."),
    ("run_task", "Run a debugger task."),
    ("run_last_task", "Run the last debugger task."),
    ("add_function_breakpoint", "Add a function breakpoint."),
    ("clear_breakpoints", "Clear all breakpoints."),
    ("clear_console", "Clear the debugger console."),
    ("show_protocol", "Show the DAP protocol log."),
    ("add_watch_expression", "Add a watch expression."),
    ("save_data", "Force save debugger data."),
    ("toggle_disassembly", "Toggle disassembly view."),
    ("toggle_breakpoint", "Toggle breakpoint at cursor."),
    ("toggle_column_breakpoint", "Toggle column breakpoint at cursor."),
    ("run_to_current_line", "Run to the selected line."),
    ("generate_commands", "Regenerate commands/settings/schema (development)."),
]


def _make_debugger_st_tool(key, desc):
    def _tool(body):
        window = sublime.active_window()
        if not window:
            return {"error": "No active window."}
        args = {}
        if "configuration_name" in body:
            args["configuration_name"] = body["configuration_name"]
        window.run_command("debugger", {"action": key, **args})
        return {"success": True, "message": "Ran debugger command: {}".format(key)}
    return _tool


_DEBUGGER_ST_TOOLS = []
_ST_TOOL_NAMES_SEEN = set()
# Pre-seed with hand-written tool names so ST commands don't duplicate them
_HANDWRITTEN_TOOL_NAMES = {
    "debugger_add_function_breakpoint", "debugger_clear_breakpoints",
    "debugger_toggle_breakpoint", "debugger_add_watch_expression",
    "debugger_step_back", "debugger_reverse_continue",
    "debugger_step_over", "debugger_run_task", "debugger_toggle_column_breakpoint",
}
_ST_TOOL_NAMES_SEEN.update(_HANDWRITTEN_TOOL_NAMES)
for _key, _desc in _DEBUGGER_ST_COMMANDS:
    _tool_name = "debugger_" + _key
    if _tool_name in _ST_TOOL_NAMES_SEEN:
        continue
    _ST_TOOL_NAMES_SEEN.add(_tool_name)
    _schema = {}
    if _key == "start":
        _schema = {
            "type": "object",
            "properties": {
                "configuration_name": {"type": "string", "description": "Optional: Launch configuration name."}
            }
        }
    _DEBUGGER_ST_TOOLS.append((_tool_name, _desc, _schema, _make_debugger_st_tool(_key, _desc)))


TOOLS = [
    *_DEBUGGER_ST_TOOLS,

    ("debugger_get_state",
     "Query the active debugger status (open, running, paused) and active session thread/frame information across all windows.",
     {},
     mcp_debugger_get_state),

    ("debugger_get_breakpoints",
     "Get a list of all registered source/function breakpoints and exception filters.",
     {},
     mcp_debugger_get_breakpoints),

    ("debugger_toggle_breakpoint",
     "Toggle (add/remove) a breakpoint at a specific line in a file.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "The absolute path of the file."},
             "line": {"type": "integer", "description": "The 1-based line number."}
         },
         "required": ["file_path", "line"]
     },
     mcp_debugger_toggle_breakpoint),

    ("debugger_clear_breakpoints",
     "Remove all registered breakpoints in the workspace.",
     {},
     mcp_debugger_clear_breakpoints),

    ("debugger_control",
     "Control the active debugger session (actions: start, stop, pause, resume, step_over, step_in, step_out) focus-independently.",
     {
         "type": "object",
         "properties": {
             "action": {
                 "type": "string",
                 "enum": ["start", "stop", "pause", "resume", "step_over", "step_in", "step_out"],
                 "description": "The debugging control action to execute."
             },
             "configuration_name": {
                 "type": "string",
                 "description": "Optional: Launch configuration name (used only with action='start')."
             }
         },
         "required": ["action"]
     },
     mcp_debugger_control),

    ("debugger_get_variables",
     "Retrieve variables and their values from the paused stack frame focus-independently.",
     {
         "type": "object",
         "properties": {
             "variables_reference": {
                 "type": "integer",
                 "description": "Optional: Reference ID of a variable to fetch child fields of."
             }
         }
     },
     mcp_debugger_get_variables),

    ("debugger_evaluate",
     "Evaluate an expression in the current context of the paused debug session focus-independently.",
     {
         "type": "object",
         "properties": {
             "expression": {
                 "type": "string",
                 "description": "The expression/code statement to evaluate."
             }
         },
         "required": ["expression"]
     },
     mcp_debugger_evaluate),

    ("debugger_get_callstack",
     "Get the full chronological callstack/stack trace of active or specific threads focus-independently.",
     {
         "type": "object",
         "properties": {
             "thread_id": {"type": "integer", "description": "Optional: The thread ID. If omitted, returns trace of active selected thread."}
         }
     },
     mcp_debugger_get_callstack),

    ("debugger_get_exception_info",
     "Query rich diagnosis and message details of any active exceptions/crashes focus-independently.",
     {
         "type": "object",
         "properties": {
             "thread_id": {"type": "integer", "description": "Optional: The thread ID. If omitted, uses active selected thread."}
         }
     },
     mcp_debugger_get_exception_info),

    ("debugger_add_watch_expression",
     "Add an expression to watch live values dynamically during debug pauses focus-independently.",
     {
         "type": "object",
         "properties": {
             "expression": {"type": "string", "description": "The string code expression to watch."}
         },
         "required": ["expression"]
     },
     mcp_debugger_add_watch_expression),

    ("debugger_get_watch_expressions",
     "Get a list of all active watched expressions and their live evaluated results.",
     {},
     mcp_debugger_get_watch_expressions),

    ("debugger_add_function_breakpoint",
     "Set a breakpoint on a function name (breaks execution whenever that function is entered) focus-independently.",
     {
         "type": "object",
         "properties": {
             "name": {"type": "string", "description": "The name of the target function."}
         },
         "required": ["name"]
     },
     mcp_debugger_add_function_breakpoint),

    # ── DAP session-level tools (beyond the hand-written wrappers) ──────────────

    ("debugger_get_threads",
     "Get all threads in the active debug session with their state and selected frame.",
     {},
     lambda body: _get_threads()),

    ("debugger_get_loaded_sources",
     "Get all loaded source files in the active debug session.",
     {},
     lambda body: _get_loaded_sources()),

    ("debugger_get_modules",
     "Get all loaded modules in the active debug session.",
     {},
     lambda body: _get_modules()),

    ("debugger_get_completions",
     "Get completions for an expression at a specific position in the paused frame.",
     {
         "type": "object",
         "properties": {
             "text": {"type": "string", "description": "The text to complete."},
             "line": {"type": "integer", "description": "Optional: line number (defaults to selected frame line)."},
             "column": {"type": "integer", "description": "Optional: column number (defaults to 0)."}
         },
         "required": ["text"]
     },
     lambda body: _get_completions(body)),

    ("debugger_step_back",
     "Step backwards one instruction (if the adapter supports reverse debugging).",
     {},
     lambda body: _step_back()),

    ("debugger_reverse_continue",
     "Continue execution in reverse (if the adapter supports reverse debugging).",
     {},
     lambda body: _reverse_continue()),

    ("debugger_restart",
     "Restart the current debug session.",
     {},
     lambda body: _restart()),

    ("debugger_disconnect",
     "Disconnect from the debug adapter (does not terminate).",
     {},
     lambda body: _disconnect()),

    ("debugger_terminate",
     "Terminate the debug session and the adapter.",
     {},
     lambda body: _terminate()),

    # ── Additional DAP session methods (~50 more to reach 100+) ────────────────

    ("debugger_step",
     "Generic step with granularity (break, instruction, line).",
     {
         "type": "object",
         "properties": {
             "thread_id": {"type": "integer", "description": "Thread ID to step."},
             "granularity": {"type": "string", "enum": ["break", "instruction", "line"], "description": "Step granularity."}
         },
         "required": ["thread_id"]
     },
     lambda body: _session_call("step", body)),

    ("debugger_step_over",
     "Step over (next) in a specific thread.",
     {
         "type": "object",
         "properties": {"thread_id": {"type": "integer", "description": "Thread ID. Defaults to selected thread."}}
     },
     lambda body: _step_over_session(body)),

    ("debugger_step_in_session",
     "Step into in a specific thread.",
     {
         "type": "object",
         "properties": {"thread_id": {"type": "integer", "description": "Thread ID. Defaults to selected thread."}}
     },
     lambda body: _step_in_session(body)),

    ("debugger_step_out_session",
     "Step out in a specific thread.",
     {
         "type": "object",
         "properties": {"thread_id": {"type": "integer", "description": "Thread ID. Defaults to selected thread."}}
     },
     lambda body: _step_out_session(body)),

    ("debugger_pause_session",
     "Pause a specific thread.",
     {
         "type": "object",
         "properties": {"thread_id": {"type": "integer", "description": "Thread ID. Defaults to all."}}
     },
     lambda body: _pause_session(body)),

    ("debugger_resume_session",
     "Continue (resume) a specific thread.",
     {
         "type": "object",
         "properties": {"thread_id": {"type": "integer", "description": "Thread ID. Defaults to all."}}
     },
     lambda body: _resume_session(body)),

    ("debugger_stop_session",
     "Stop a specific session by thread.",
     {
         "type": "object",
         "properties": {"thread_id": {"type": "integer", "description": "Thread ID."}}
     },
     lambda body: _stop_session(body)),

    ("debugger_expand_thread",
     "Expand a thread to load its frames (if not loaded).",
     {
         "type": "object",
         "properties": {"thread_id": {"type": "integer", "description": "Thread ID."}},
         "required": ["thread_id"]
     },
     lambda body: _expand_thread(body)),

    ("debugger_get_thread",
     "Get a specific thread by ID.",
     {
         "type": "object",
         "properties": {"thread_id": {"type": "integer", "description": "Thread ID."}},
         "required": ["thread_id"]
     },
     lambda body: _get_thread_by_id(body)),

    ("debugger_refresh_threads",
     "Refresh the thread list from the adapter.",
     {},
     lambda body: _refresh_threads()),

    ("debugger_refresh_scopes",
     "Refresh variable scopes for a frame.",
     {
         "type": "object",
         "properties": {"frame_id": {"type": "integer", "description": "Frame ID."}},
         "required": ["frame_id"]
     },
     lambda body: _refresh_scopes(body)),

    ("debugger_set_variable",
     "Set the value of a variable.",
     {
         "type": "object",
         "properties": {
             "variables_reference": {"type": "integer", "description": "Variables container reference."},
             "name": {"type": "string", "description": "Variable name."},
             "value": {"type": "string", "description": "New value."}
         },
         "required": ["variables_reference", "name", "value"]
     },
     lambda body: _set_variable(body)),

    ("debugger_set_breakpoints_for_file",
     "Set breakpoints for a file (replaces existing).",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Absolute file path."},
             "breakpoints": {"type": "array", "description": "List of {line, condition, hit_condition, log_message}."}
         },
         "required": ["file_path", "breakpoints"]
     },
     lambda body: _set_breakpoints_for_file(body)),

    ("debugger_set_function_breakpoints",
     "Set function breakpoints (replaces existing).",
     {
         "type": "object",
         "properties": {
             "names": {"type": "array", "items": {"type": "string"}, "description": "Function names."}
         },
         "required": ["names"]
     },
     lambda body: _set_function_breakpoints(body)),

    ("debugger_set_data_breakpoints",
     "Set data breakpoints (watch on variable writes/reads).",
     {
         "type": "object",
         "properties": {
             "breakpoints": {"type": "array", "description": "List of {data_id, access_type}."}
         }
     },
     lambda body: _set_data_breakpoints(body)),

    ("debugger_data_breakpoint_info",
     "Get info about a data breakpoint for a variable.",
     {
         "type": "object",
         "properties": {
             "variables_reference": {"type": "integer", "description": "Variable container reference."},
             "name": {"type": "string", "description": "Variable name."}
         },
         "required": ["variables_reference"]
     },
     lambda body: _data_breakpoint_info(body)),

    ("debugger_set_exception_breakpoint_filters",
     "Set exception filters (caught/uncaught).",
     {
         "type": "object",
         "properties": {
             "filters": {"type": "array", "items": {"type": "string"}, "description": "Filter IDs."}
         }
     },
     lambda body: _set_exception_filters(body)),

    ("debugger_get_source",
     "Get source content for a frame.",
     {
         "type": "object",
         "properties": {
             "source_path": {"type": "string", "description": "Source path."},
             "source_reference": {"type": "integer", "description": "Source reference for dynamic sources."}
         }
     },
     lambda body: _get_source(body)),

    ("debugger_disassemble",
     "Disassemble memory at an address.",
     {
         "type": "object",
         "properties": {
             "memory_reference": {"type": "string", "description": "Memory address."},
             "instruction_count": {"type": "integer", "description": "Number of instructions."}
         },
         "required": ["memory_reference"]
     },
     lambda body: _disassemble(body)),

    ("debugger_read_memory",
     "Read memory at an address.",
     {
         "type": "object",
         "properties": {
             "memory_reference": {"type": "string", "description": "Memory address."},
             "count": {"type": "integer", "description": "Number of bytes to read."}
         },
         "required": ["memory_reference", "count"]
     },
     lambda body: _read_memory(body)),

    ("debugger_get_session_name",
     "Get the name of the active session.",
     {},
     lambda body: _session_name()),

    ("debugger_get_session_state",
     "Get the state of the active session (running, paused, stopped).",
     {},
     lambda body: _session_state()),

    ("debugger_is_paused",
     "Check if the active session is paused.",
     {},
     lambda body: _session_is_paused()),

    ("debugger_is_running",
     "Check if the active session is running.",
     {},
     lambda body: _session_is_running()),

    ("debugger_is_stoppable",
     "Check if the active session can be stopped.",
     {},
     lambda body: _session_is_stoppable()),

    ("debugger_select_thread",
     "Select a thread and optionally a frame.",
     {
         "type": "object",
         "properties": {
             "thread_id": {"type": "integer", "description": "Thread ID."},
             "frame_id": {"type": "integer", "description": "Optional frame ID."}
         },
         "required": ["thread_id"]
     },
     lambda body: _select_thread(body)),

    ("debugger_add_breakpoints",
     "Add breakpoints to the existing set (not replace).",
     {
         "type": "object",
         "properties": {
             "source_breakpoints": {"type": "array", "description": "List of {file, line, condition}."},
             "function_breakpoints": {"type": "array", "items": {"type": "string"}, "description": "Function names."}
         }
     },
     lambda body: _add_breakpoints(body)),

    ("debugger_remove_session",
     "Remove a session from the debugger.",
     {
         "type": "object",
         "properties": {"session_name": {"type": "string", "description": "Session name."}}
     },
     lambda body: _remove_session(body)),

    ("debugger_set_current_session",
     "Set the current/active session.",
     {
         "type": "object",
         "properties": {"session_name": {"type": "string", "description": "Session name."}},
         "required": ["session_name"]
     },
     lambda body: _set_current_session(body)),

    ("debugger_get_current_session",
     "Get the name of the current session.",
     {},
     lambda body: _get_current_session()),

    ("debugger_set_configuration",
     "Set the active debug configuration by name.",
     {
         "type": "object",
         "properties": {"configuration_name": {"type": "string", "description": "Configuration name."}},
         "required": ["configuration_name"]
     },
     lambda body: _set_configuration(body)),

    ("debugger_run_to_line",
     "Run to a specific line in a file.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Absolute file path."},
             "line": {"type": "integer", "description": "Line number."}
         },
         "required": ["file_path", "line"]
     },
     lambda body: _run_to_line(body)),

    ("debugger_toggle_column_breakpoint",
     "Toggle a column breakpoint at a specific line/column in a file.",
     {
         "type": "object",
         "properties": {
             "file_path": {"type": "string", "description": "Absolute file path."},
             "line": {"type": "integer", "description": "Line number."},
             "column": {"type": "integer", "description": "Column number (optional)."}
         },
         "required": ["file_path", "line"]
     },
     lambda body: _toggle_column_breakpoint(body)),

    ("debugger_clear_all_breakpoints",
     "Clear all breakpoints (all types).",
     {},
     lambda body: _clear_all_breakpoints()),

    ("debugger_refresh_phantoms",
     "Refresh all debugger UI phantoms.",
     {},
     lambda body: _refresh_phantoms()),

    ("debugger_save_session_data",
     "Force-save debugger session data.",
     {},
     lambda body: _save_data()),

    ("debugger_get_disassembly",
     "Get disassembly for the current frame (toggle on/off).",
     {
         "type": "object",
         "properties": {"toggle": {"type": "boolean", "description": "Toggle disassembly view."}}
     },
     lambda body: _show_disassembly(body)),

    ("debugger_run_task",
     "Run a named task.",
     {
         "type": "object",
         "properties": {"task_name": {"type": "string", "description": "Task name."}},
         "required": ["task_name"]
     },
     lambda body: _run_task(body)),

    ("debugger_get_output_panels",
     "List all debugger output panels.",
     {},
     lambda body: _get_output_panels()),

    ("debugger_dispose_terminals",
     "Dispose all external terminals.",
     {
         "type": "object",
         "properties": {"unused_only": {"type": "boolean", "description": "Only dispose unused terminals."}}
     },
     lambda body: _dispose_terminals(body)),

    ("debugger_get_stepping_granularity",
     "Get the current stepping granularity setting.",
     {},
     lambda body: _get_stepping_granularity()),

    ("debugger_send_custom_request",
     "Send a custom DAP request to the adapter.",
     {
         "type": "object",
         "properties": {
             "method": {"type": "string", "description": "DAP method name."},
             "arguments": {"type": "object", "description": "Request arguments."}
         },
         "required": ["method"]
     },
     lambda body: _send_custom_request(body)),

    ("debugger_get_children",
     "Get child frames/variables of a thread/variable.",
     {
         "type": "object",
         "properties": {"reference": {"type": "integer", "description": "Reference ID."}},
         "required": ["reference"]
     },
     lambda body: _get_children(body)),

    ("debugger_has_children",
     "Check if a thread/variable has children.",
     {
         "type": "object",
         "properties": {"reference": {"type": "integer", "description": "Reference ID."}},
         "required": ["reference"]
     },
     lambda body: _has_children(body)),

    ("debugger_first_non_subtle_frame",
     "Get the first non-subtle frame of a thread (skip library frames).",
     {
         "type": "object",
         "properties": {"frames": {"type": "array", "description": "List of frame objects."}}
     },
     lambda body: _first_non_subtle_frame(body)),

    ("debugger_launch",
     "Launch a new debug session with a configuration.",
     {
         "type": "object",
         "properties": {
             "configuration_name": {"type": "string", "description": "Configuration name."},
             "no_debug": {"type": "boolean", "description": "Run without debugging."}
         },
         "required": ["configuration_name"]
     },
     lambda body: _launch(body)),

    ("debugger_run_pre_debug_task",
     "Run the pre-debug task for the current configuration.",
     {},
     lambda body: _run_pre_debug_task()),

    ("debugger_run_post_debug_task",
     "Run the post-debug task for the current configuration.",
     {},
     lambda body: _run_post_debug_task()),

    ("debugger_evaluate_expression",
     "Evaluate an expression with explicit context (repl, hover, watch).",
     {
         "type": "object",
         "properties": {
             "expression": {"type": "string", "description": "Expression to evaluate."},
             "context": {"type": "string", "enum": ["repl", "hover", "watch"], "description": "Evaluation context."}
         },
         "required": ["expression"]
     },
     lambda body: _evaluate_expression(body)),

    ("debugger_get_scopes",
     "Get variable scopes for the currently selected frame.",
     {},
     lambda body: _get_scopes()),

    ("debugger_get_all_sessions",
     "List all debug sessions (name + state) attached to the debugger.",
     {},
     lambda body: _get_all_sessions()),

    ("debugger_get_configurations",
     "List all available debug configurations for the current project.",
     {},
     lambda body: _get_configurations()),

    ("debugger_get_adapters",
     "List installed debug adapters.",
     {},
     lambda body: _get_adapters()),

    ("debugger_get_storage_path",
     "Get the debugger package storage path.",
     {},
     lambda body: _get_storage_path()),

    ("debugger_get_console_output",
     "Get recent debugger console output.",
     {
         "type": "object",
         "properties": {"tail": {"type": "integer", "description": "Number of recent lines. Defaults to 100."}}
     },
     lambda body: _get_console_output(body)),
]