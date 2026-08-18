"""Minimal ThreadingHTTPServer stand-in for the Sublime HTTP backend.

Used by proxy proof tests (F5) so a controlled delay can be injected
without a live Sublime instance.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FakeBridge:
    """Loopback backend: sleep ``delay_s`` then return 200 JSON.

    ``completed`` is set after the delay, even if the client has already
    given up — that is the F5 signal that Sublime was still working.
    """

    def __init__(self, delay_s=0.0, payload=None):
        self.delay_s = delay_s
        self.payload = payload if payload is not None else {"results": [{"ok": True}]}
        self.completed = threading.Event()
        self.requests = []
        self._httpd = None
        self._thread = None

    @property
    def base_url(self):
        return "http://127.0.0.1:{}".format(self.port)

    @property
    def port(self):
        return self._httpd.server_address[1]

    def start(self):
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def _read_body(self):
                length = int(self.headers.get("Content-Length") or 0)
                return self.rfile.read(length) if length else b""

            def _handle(self):
                import time

                body = self._read_body()
                bridge.requests.append((self.command, self.path.split("?", 1)[0], body))
                if bridge.delay_s:
                    time.sleep(bridge.delay_s)
                bridge.completed.set()
                payload = json.dumps(bridge.payload).encode("utf-8")
                try:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                    pass

            def do_GET(self):
                self._handle()

            def do_POST(self):
                self._handle()

            def log_message(self, format, *args):
                return

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self.port

    def stop(self):
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
