"""Stopping the servers releases their listening sockets.

A plugin reload runs _stop_servers; with shutdown() alone the old module kept the port open and the
new server's clients could connect to a socket nobody accepted from. The function is pulled out of the
plugin source and run against real HTTP servers on free ports (the plugin imports `sublime` and cannot
be imported outside Sublime Text).
"""
import re
import socket
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SOURCE = (Path(__file__).resolve().parent.parent / "sublime_mcp.py").read_text(encoding="utf-8")


def _load():
    match = re.search(r"(def _stop_servers\(\):.*?)\n\n\ndef plugin_loaded", SOURCE, re.S)
    assert match, "_stop_servers not found"
    namespace = {"_server": None, "_mcp_server": None, "_mcp_sessions": {}}
    exec(match.group(1), namespace)
    return namespace


def _serve():
    server = HTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class StopServersTest(unittest.TestCase):
    def test_both_listening_sockets_are_closed(self):
        ns = _load()
        # keep our own references: dropping the last one lets the garbage collector close the
        # socket, which would hide a missing server_close() (a handler thread can hold the real one)
        keep = [_serve(), _serve()]
        ns["_server"], ns["_mcp_server"] = keep
        ports = [s.server_address[1] for s in keep]
        ns["_stop_servers"]()
        self.assertIsNone(ns["_server"])
        self.assertIsNone(ns["_mcp_server"])
        for port in ports:
            with self.assertRaises(OSError):  # nothing listens any more: the connect is refused
                socket.create_connection(("127.0.0.1", port), timeout=2).close()

    def test_a_missing_server_is_fine(self):
        ns = _load()
        ns["_stop_servers"]()


if __name__ == "__main__":
    unittest.main()
