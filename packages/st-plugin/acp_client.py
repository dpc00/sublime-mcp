"""Small ACP client core using newline-delimited JSON-RPC over stdio.

The module deliberately has no Sublime Text imports so transport and lifecycle
behavior can be regression-tested with an in-memory agent.
"""

import json
import queue
import subprocess
import threading

# PROOF: F9 — 2026-08-17. Cap in-flight agent-request workers so a flood
# cannot spawn one thread per request. close() now shuts the reader and
# joins the read loop.
MAX_AGENT_REQUEST_THREADS = 8


class AcpError(RuntimeError):
    pass


class AcpConnection:
    def __init__(self, reader, writer, on_notification=None, on_request=None):
        self.reader = reader
        self.writer = writer
        self.on_notification = on_notification or (lambda _method, _params: None)
        self.on_request = on_request or self._unsupported_request
        self._next_id = 0
        self._pending = {}
        self._write_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._closed = threading.Event()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._agent_jobs = queue.Queue()
        self._agent_workers = []
        self.invalid_json_count = 0

    @staticmethod
    def _unsupported_request(method, _params):
        raise AcpError("Unsupported agent request: " + method)

    def start(self):
        for i in range(MAX_AGENT_REQUEST_THREADS):
            worker = threading.Thread(
                target=self._agent_worker,
                name="acp-agent-{}".format(i),
                daemon=True,
            )
            worker.start()
            self._agent_workers.append(worker)
        self._thread.start()
        return self

    def _agent_worker(self):
        while True:
            job = self._agent_jobs.get()
            if job is None:
                return
            try:
                self._respond_to_agent(*job)
            except Exception:
                pass

    def _send(self, message):
        payload = json.dumps(message, separators=(",", ":")) + "\n"
        with self._write_lock:
            self.writer.write(payload)
            self.writer.flush()

    def request(self, method, params=None, timeout=30.0):
        with self._state_lock:
            if self._closed.is_set():
                raise AcpError("ACP connection is closed")
            request_id = self._next_id
            self._next_id += 1
            pending = {"event": threading.Event(), "response": None}
            self._pending[request_id] = pending
        self._send({
            "jsonrpc": "2.0", "id": request_id, "method": method,
            "params": params or {},
        })
        if not pending["event"].wait(timeout):
            with self._state_lock:
                self._pending.pop(request_id, None)
            raise TimeoutError("ACP request timed out: " + method)
        response = pending["response"]
        if "error" in response:
            error = response["error"]
            raise AcpError(error.get("message", str(error)))
        return response.get("result")

    def notify(self, method, params=None):
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def _respond_to_agent(self, request_id, method, params):
        try:
            result = self.on_request(method, params)
            response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as error:
            response = {
                "jsonrpc": "2.0", "id": request_id,
                "error": {"code": -32603, "message": str(error)},
            }
        self._send(response)

    def _read_loop(self):
        try:
            while True:
                line = self.reader.readline()
                if not line:
                    break
                try:
                    message = json.loads(line)
                except (TypeError, json.JSONDecodeError):
                    self.invalid_json_count += 1
                    continue
                if "method" in message and "id" in message:
                    self._agent_jobs.put((
                        message["id"],
                        message["method"],
                        message.get("params") or {},
                    ))
                elif "method" in message:
                    self.on_notification(message["method"], message.get("params") or {})
                elif "id" in message:
                    with self._state_lock:
                        pending = self._pending.pop(message["id"], None)
                    if pending:
                        pending["response"] = message
                        pending["event"].set()
        finally:
            self._closed.set()
            with self._state_lock:
                pending_requests = list(self._pending.values())
                self._pending.clear()
            for pending in pending_requests:
                pending["response"] = {
                    "error": {"message": "ACP connection closed before response"}
                }
                pending["event"].set()

    def close(self):
        self._closed.set()
        try:
            self.writer.close()
        except Exception:
            pass
        try:
            closer = getattr(self.reader, "close", None)
            if closer:
                closer()
        except Exception:
            pass
        for _ in self._agent_workers:
            self._agent_jobs.put(None)
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)
        for worker in self._agent_workers:
            if worker.is_alive():
                worker.join(timeout=1.0)


class AcpProcessClient:
    def __init__(self, command, cwd, on_notification=None, on_request=None):
        self.command = list(command)
        self.cwd = cwd
        self.on_notification = on_notification
        self.on_request = on_request
        self.process = None
        self.connection = None
        self.stderr_lines = []

    def start(self):
        if self.process and self.process.poll() is None:
            return self
        self.process = subprocess.Popen(
            self.command,
            cwd=self.cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        self.connection = AcpConnection(
            self.process.stdout,
            self.process.stdin,
            on_notification=self.on_notification,
            on_request=self.on_request,
        ).start()
        threading.Thread(target=self._drain_stderr, daemon=True).start()
        return self

    def _drain_stderr(self):
        for line in self.process.stderr:
            self.stderr_lines.append(line.rstrip())
            if len(self.stderr_lines) > 200:
                del self.stderr_lines[:-200]

    def initialize(self, protocol_version=1):
        return self.connection.request("initialize", {
            "protocolVersion": protocol_version,
            "capabilities": {},
            "clientInfo": {
                "name": "sublime-mcp",
                "title": "Sublime Text ACP Client",
                "version": "0.1.0",
            },
        })

    def new_session(self, additional_directories=None, mcp_servers=None):
        return self.connection.request("session/new", {
            "cwd": self.cwd,
            "additionalDirectories": additional_directories or [],
            "mcpServers": mcp_servers or [],
        })

    def prompt(self, session_id, text, timeout=300.0):
        return self.connection.request("session/prompt", {
            "sessionId": session_id,
            "prompt": [{"type": "text", "text": text}],
        }, timeout=timeout)

    def set_config_option(self, session_id, config_id, value, value_type="id"):
        return self.connection.request("session/set_config_option", {
            "sessionId": session_id,
            "configId": config_id,
            "type": value_type,
            "value": value,
        })

    def cancel(self, session_id):
        self.connection.notify("session/cancel", {"sessionId": session_id})

    def stop(self, timeout=5.0):
        if not self.process:
            return
        if self.connection:
            self.connection.close()
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=timeout)
