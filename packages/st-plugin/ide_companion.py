"""Gemini-compatible IDE Companion discovery and authenticated MCP transport.

This module deliberately does not import ``sublime`` so its path, lifecycle,
and HTTP authentication behavior can be unit tested outside Sublime Text.
"""

import hmac
import json
import os
import queue
import re
import secrets
import select
import socket
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse


MAX_RECENT_FILES = 10
MAX_SELECTED_TEXT_BYTES = 16 * 1024
MAX_REQUEST_BODY_BYTES = 64 * 1024 * 1024


def detect_line_ending(data):
    """Return the dominant newline sequence in UTF-8 file bytes."""
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n") - crlf
    cr = data.count(b"\r") - crlf
    if crlf >= lf and crlf >= cr and crlf:
        return "\r\n"
    if lf >= cr and lf:
        return "\n"
    if cr:
        return "\r"
    return os.linesep


def preserve_line_endings(text, line_ending):
    """Normalize proposed text to the source file's newline convention."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized if line_ending == "\n" else normalized.replace("\n", line_ending)

COMPANION_TOOLS = (
    {
        "name": "openDiff",
        "description": "Open a modifiable native diff review for a file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filePath": {"type": "string"},
                "newContent": {"type": "string"},
            },
            "required": ["filePath", "newContent"],
        },
    },
    {
        "name": "closeDiff",
        "description": "Close a diff review and return its final content.",
        "inputSchema": {
            "type": "object",
            "properties": {"filePath": {"type": "string"}},
            "required": ["filePath"],
        },
    },
)


def companion_dispatch(message, open_diff, close_diff):
    """Dispatch only the MCP surface published by the IDE Companion spec."""
    method = message.get("method", "")
    message_id = message.get("id")
    params = message.get("params") or {}
    try:
        if method == "initialize":
            requested = params.get("protocolVersion") or "2025-06-18"
            result = {
                "protocolVersion": requested,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "sublime-ide-companion", "version": "0.1.0"},
            }
        elif method in ("notifications/initialized", "notifications/cancelled"):
            return None
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": list(COMPANION_TOOLS)}
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments") or {}
            if tool_name == "openDiff":
                result = open_diff(arguments)
            elif tool_name == "closeDiff":
                result = close_diff(arguments)
            else:
                raise ValueError("Unknown tool: " + str(tool_name))
        else:
            raise ValueError("Unknown method: " + method)
        if message_id is None:
            return None
        return {"jsonrpc": "2.0", "id": message_id, "result": result}
    except Exception as error:
        if message_id is None:
            return None
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "error": {"code": -32603, "message": str(error)},
        }


def truncate_utf8(text, max_bytes=MAX_SELECTED_TEXT_BYTES):
    encoded = (text or "").encode("utf-8")
    if len(encoded) <= max_bytes:
        return text or ""
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def build_selection_changed_params(
    file_path,
    start_line,
    start_character,
    end_line,
    end_character,
    text,
    max_bytes=MAX_SELECTED_TEXT_BYTES,
):
    """Build the selection_changed notification params (capped like context)."""
    return {
        "selection": {
            "start": {"line": int(start_line), "character": int(start_character)},
            "end": {"line": int(end_line), "character": int(end_character)},
        },
        "text": truncate_utf8(text, max_bytes=max_bytes),
        "filePath": file_path,
    }


class IdeContextTracker:
    """Tracks file focus order and builds the published IdeContext shape."""

    def __init__(self, clock=None):
        self._clock = clock or time.time
        self._timestamps = {}

    @staticmethod
    def _key(path):
        return os.path.normcase(os.path.abspath(os.path.normpath(path)))

    def touch(self, path, timestamp=None):
        if path:
            self._timestamps[self._key(path)] = (
                int(self._clock() * 1000) if timestamp is None else int(timestamp)
            )

    def forget(self, path):
        if path:
            self._timestamps.pop(self._key(path), None)

    def snapshot(
        self,
        open_paths,
        active_path=None,
        cursor=None,
        selected_text=None,
        is_trusted=True,
    ):
        active_key = self._key(active_path) if active_path else None
        if active_path:
            self.touch(active_path)
        files = []
        seen = set()
        for path in open_paths:
            if not path or not os.path.isfile(path):
                continue
            absolute = os.path.abspath(os.path.normpath(path))
            key = self._key(absolute)
            if key in seen:
                continue
            seen.add(key)
            timestamp = self._timestamps.get(key)
            if timestamp is None:
                timestamp = int(self._clock() * 1000)
                self._timestamps[key] = timestamp
            item = {"path": absolute, "timestamp": timestamp}
            if key == active_key:
                item["isActive"] = True
                if cursor:
                    item["cursor"] = {
                        "line": int(cursor[0]),
                        "character": int(cursor[1]),
                    }
                if selected_text:
                    item["selectedText"] = truncate_utf8(selected_text)
            files.append(item)
        files.sort(key=lambda item: item["timestamp"], reverse=True)
        return {
            "workspaceState": {
                "openFiles": files[:MAX_RECENT_FILES],
                "isTrusted": bool(is_trusted),
            }
        }


def workspace_path_value(paths, path_separator=None):
    """Return unique absolute workspace roots in discovery-file form."""
    separator = os.pathsep if path_separator is None else path_separator
    normalized = []
    seen = set()
    for path in paths:
        if not path:
            continue
        value = os.path.abspath(os.path.normpath(path))
        key = os.path.normcase(value)
        if key not in seen:
            seen.add(key)
            normalized.append(value)
    return separator.join(normalized)


def gemini_discovery_directory(temp_directory=None):
    root = tempfile.gettempdir() if temp_directory is None else temp_directory
    return os.path.join(root, "gemini", "ide")


def gemini_discovery_filename(pid, port):
    return "gemini-ide-server-{}-{}.json".format(int(pid), int(port))


def create_gemini_discovery_file(
    pid,
    port,
    workspace_paths,
    auth_token,
    directory=None,
    ide_name="sublime",
    display_name="Sublime Text",
):
    """Atomically publish one record and remove stale records for this PID."""
    target_dir = directory or gemini_discovery_directory()
    os.makedirs(target_dir, exist_ok=True)
    stale_pattern = re.compile(
        r"^gemini-ide-server-{}-\d+\.json$".format(re.escape(str(int(pid))))
    )
    for name in os.listdir(target_dir):
        if stale_pattern.match(name):
            try:
                os.remove(os.path.join(target_dir, name))
            except FileNotFoundError:
                pass

    payload = {
        "port": int(port),
        "workspacePath": workspace_path_value(workspace_paths),
        "authToken": auth_token,
        "ideInfo": {"name": ide_name, "displayName": display_name},
    }
    target = os.path.join(target_dir, gemini_discovery_filename(pid, port))
    fd, temporary = tempfile.mkstemp(prefix=".gemini-ide-", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except Exception:
        try:
            os.remove(temporary)
        except FileNotFoundError:
            pass
        raise
    return target


def remove_discovery_file(path):
    if not path:
        return
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def qwen_discovery_directory(home_directory=None):
    home = os.path.expanduser("~") if home_directory is None else home_directory
    return os.path.join(home, ".qwen", "ide")


def create_qwen_discovery_file(
    port,
    workspace_paths,
    auth_token,
    parent_pid,
    directory=None,
    ide_name="Sublime Text",
    ide_id="sublime",
):
    """Atomically publish the current Qwen Code <PORT>.lock record."""
    target_dir = directory or qwen_discovery_directory()
    os.makedirs(target_dir, exist_ok=True)
    payload = {
        "port": int(port),
        "workspacePath": workspace_path_value(workspace_paths),
        "authToken": auth_token,
        "ppid": int(parent_pid),
        "ideName": ide_name,
        "ideInfo": {"name": ide_id, "displayName": ide_name},
    }
    target = os.path.join(target_dir, "{}.lock".format(int(port)))
    fd, temporary = tempfile.mkstemp(prefix=".qwen-ide-", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except Exception:
        try:
            os.remove(temporary)
        except FileNotFoundError:
            pass
        raise
    return target


def _authorized(header_value, expected_token):
    if not header_value or not expected_token:
        return False
    prefix = "Bearer "
    if not header_value.startswith(prefix):
        return False
    return hmac.compare_digest(header_value[len(prefix):], expected_token)


def _request_authorized(headers, expected_token):
    if _authorized(headers.get("Authorization"), expected_token):
        return True
    claude_token = headers.get("X-Claude-Code-Ide-Authorization")
    return bool(
        claude_token
        and expected_token
        and hmac.compare_digest(claude_token, expected_token)
    )


def _valid_origin(origin):
    """Allow absent Origin (non-browser clients) or a loopback Origin."""
    if not origin:
        return True
    parsed = urlparse(origin)
    return parsed.hostname in ("127.0.0.1", "localhost", "::1")


class _NotificationHub:
    def __init__(self):
        self._queues = set()
        self._lock = threading.Lock()

    def subscribe(self):
        stream = queue.Queue()
        with self._lock:
            self._queues.add(stream)
        return stream

    def unsubscribe(self, stream):
        with self._lock:
            self._queues.discard(stream)
            return len(self._queues)

    def publish(self, message):
        with self._lock:
            streams = list(self._queues)
        for stream in streams:
            stream.put(message)
        return len(streams)

    def close(self):
        with self._lock:
            streams = list(self._queues)
            self._queues.clear()
        for stream in streams:
            stream.put(None)


class _ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        import sys
        if isinstance(sys.exc_info()[1], (ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


def _handler_class(
    auth_token,
    dispatcher,
    legacy_dispatcher,
    notifications,
    on_subscribe,
    on_last_disconnect,
):
    class CompanionHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format, *args):
            pass

        def _reject_body_too_large(self, length):
            # HTTP/1.1 keep-alive requires the declared body to be fully
            # consumed (or the connection closed) before writing a response,
            # otherwise the next request on this connection gets misframed
            # as leftover body bytes from this one. Draining keeps the
            # connection reusable instead of racing a close against a
            # client still mid-write.
            remaining = length
            chunk = 1024 * 1024
            while remaining > 0:
                read = self.rfile.read(min(chunk, remaining))
                if not read:
                    self.close_connection = True
                    break
                remaining -= len(read)
            self._json(413, {"error": "request body too large"})

        def _json(self, status, body):
            payload = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header(
                "Access-Control-Allow-Headers",
                "Authorization, Content-Type, X-Claude-Code-Ide-Authorization",
            )
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/sse" and legacy_dispatcher:
                self._legacy_sse()
                return
            if path != "/mcp":
                self._json(404, {})
                return
            if not _valid_origin(self.headers.get("Origin")):
                self._json(403, {"error": "forbidden origin"})
                return
            if not _request_authorized(self.headers, auth_token):
                self._json(401, {"error": "unauthorized"})
                return
            stream = notifications.subscribe()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            if on_subscribe:
                on_subscribe()
            try:
                while True:
                    readable, _, _ = select.select([self.connection], [], [], 0)
                    if readable:
                        try:
                            if not self.connection.recv(1, socket.MSG_PEEK):
                                break
                        except (ConnectionResetError, ConnectionAbortedError, OSError):
                            break
                    try:
                        message = stream.get(timeout=1)
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                        continue
                    if message is None:
                        break
                    payload = json.dumps(message, separators=(",", ":"))
                    self.wfile.write(("event: message\ndata: " + payload + "\n\n").encode("utf-8"))
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            finally:
                remaining = notifications.unsubscribe(stream)
                if remaining == 0 and on_last_disconnect:
                    on_last_disconnect()

        def do_POST(self):
            path = urlparse(self.path).path
            if path == "/messages" and legacy_dispatcher:
                self._legacy_message()
                return
            if path != "/mcp":
                self._json(404, {})
                return
            if not _valid_origin(self.headers.get("Origin")):
                self._json(403, {"error": "forbidden origin"})
                return
            if not _request_authorized(self.headers, auth_token):
                self._json(401, {"error": "unauthorized"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > MAX_REQUEST_BODY_BYTES:
                    self._reject_body_too_large(length)
                    return
                message = json.loads(self.rfile.read(length)) if length else {}
                response = dispatcher(message)
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                self._json(400, {"error": str(error)})
                return
            if response is None:
                self.send_response(202)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self._json(200, response)

        def _legacy_sse(self):
            if not _valid_origin(self.headers.get("Origin")):
                self._json(403, {"error": "forbidden origin"})
                return
            session_id = str(uuid.uuid4())
            stream = notifications.subscribe()
            legacy_sessions[session_id] = stream
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            if on_subscribe:
                on_subscribe()
            try:
                endpoint = "/messages?sessionId=" + session_id
                self.wfile.write(("event: endpoint\ndata: " + endpoint + "\n\n").encode("utf-8"))
                self.wfile.flush()
                while True:
                    try:
                        message = stream.get(timeout=30)
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                        continue
                    if message is None:
                        break
                    payload = json.dumps(message, separators=(",", ":"))
                    self.wfile.write(("data: " + payload + "\n\n").encode("utf-8"))
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            finally:
                legacy_sessions.pop(session_id, None)
                remaining = notifications.unsubscribe(stream)
                if remaining == 0 and on_last_disconnect:
                    on_last_disconnect()

        def _legacy_message(self):
            if not _valid_origin(self.headers.get("Origin")):
                self._json(403, {"error": "forbidden origin"})
                return
            query = urlparse(self.path).query
            session_id = None
            for item in query.split("&"):
                key, separator, value = item.partition("=")
                if separator and key == "sessionId":
                    session_id = value
                    break
            stream = legacy_sessions.get(session_id)
            if stream is None:
                self._json(404, {"error": "unknown session"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > MAX_REQUEST_BODY_BYTES:
                    self._reject_body_too_large(length)
                    return
                message = json.loads(self.rfile.read(length)) if length else {}
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                self._json(400, {"error": str(error)})
                return
            self.send_response(202)
            self.send_header("Content-Length", "0")
            self.end_headers()

            def dispatch_and_push():
                response = legacy_dispatcher(message)
                if response is not None:
                    stream.put(response)

            threading.Thread(target=dispatch_and_push, daemon=True).start()

    legacy_sessions = {}
    return CompanionHandler


class IdeCompanionServer:
    """Authenticated loopback MCP server bound to a dynamic port."""

    def __init__(
        self,
        dispatcher,
        auth_token=None,
        legacy_dispatcher=None,
        on_subscribe=None,
        on_last_disconnect=None,
    ):
        self.dispatcher = dispatcher
        self.legacy_dispatcher = legacy_dispatcher
        self.auth_token = auth_token or secrets.token_urlsafe(32)
        self.on_subscribe = on_subscribe
        self.on_last_disconnect = on_last_disconnect
        self._notifications = _NotificationHub()
        self._server = None
        self._thread = None

    @property
    def port(self):
        return self._server.server_address[1] if self._server else None

    def start(self):
        if self._server:
            return self.port
        self._server = _ThreadingHTTPServer(
            ("127.0.0.1", 0),
            _handler_class(
                self.auth_token,
                self.dispatcher,
                self.legacy_dispatcher,
                self._notifications,
                self.on_subscribe,
                self.on_last_disconnect,
            ),
        )
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self.port

    def stop(self):
        server = self._server
        thread = self._thread
        self._server = None
        self._thread = None
        self._notifications.close()
        if server:
            server.shutdown()
            server.server_close()
        if thread and thread is not threading.current_thread():
            thread.join(timeout=2)

    def notify(self, method, params=None):
        message = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        return self._notifications.publish(message)
