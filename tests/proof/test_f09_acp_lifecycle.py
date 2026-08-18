"""F9 — ACP client lifecycle gaps.

PROOF: F9 — 2026-08-17. A 40-request flood started 40 handler threads;
close() left the reader thread blocked on readline(). FIXED: a daemon
worker pool of MAX_AGENT_REQUEST_THREADS (8) and close() now closes the
reader and joins the read loop. Invalid JSON is still skipped so a later
valid request is answered (session survives) — that sub-claim is
skip-and-continue, not a session-killer; locked by the peer + queue tests.
"""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from tests.test_acp_client import QueueReader, RecordingWriter, load_module

PEER = Path(__file__).parent / "fakes" / "fake_acp_peer.py"
FLOOD = 40
AGENT_REQUEST_CAP = 8


def test_f09_concurrent_agent_requests_are_capped():
    """Regression lock: at most AGENT_REQUEST_CAP on_request handlers run
    at once. On unfixed code a flood starts ~one thread per request."""
    module = load_module()
    reader, writer = QueueReader(), RecordingWriter()
    gate = threading.Event()
    active = [0]
    max_active = [0]
    lock = threading.Lock()

    def on_request(_method, _params):
        with lock:
            active[0] += 1
            if active[0] > max_active[0]:
                max_active[0] = active[0]
        gate.wait(timeout=2)
        with lock:
            active[0] -= 1
        return {"ok": True}

    connection = module.AcpConnection(reader, writer, on_request=on_request).start()
    try:
        for i in range(FLOOD):
            reader.send({
                "jsonrpc": "2.0", "id": i, "method": "session/ping", "params": {},
            })
        deadline = time.time() + 1.0
        while time.time() < deadline and max_active[0] < FLOOD:
            time.sleep(0.02)
        gate.set()
        # Drain the replies so workers are not left mid-request.
        for _ in range(FLOOD):
            writer.messages.get(timeout=2)
        assert max_active[0] >= 1
        assert max_active[0] <= AGENT_REQUEST_CAP, (
            "F9 PROVED: {} concurrent agent-request handlers from a {}-request "
            "flood (cap {})".format(max_active[0], FLOOD, AGENT_REQUEST_CAP)
        )
    finally:
        reader.close()
        connection.close()


def test_f09_close_joins_reader_thread():
    """close() must unblock and join the reader. Unfixed code only closes
    the writer, so the reader stays blocked on readline()."""
    module = load_module()
    reader, writer = QueueReader(), RecordingWriter()
    connection = module.AcpConnection(reader, writer).start()
    assert connection._thread.is_alive()
    connection.close()
    still_alive = connection._thread.is_alive()
    if still_alive:
        pytest.fail(
            "F9 PROVED: close() left the reader thread alive (no join / "
            "reader shutdown)"
        )


def test_f09_invalid_json_is_skipped_and_session_continues():
    """Bad NDJSON must not kill the session. A valid agent request after
    a garbage line still gets a response. That is skip-and-continue, not
    a silent session death — the residual is lack of visibility."""
    module = load_module()
    reader, writer = QueueReader(), RecordingWriter()
    seen = []
    connection = module.AcpConnection(
        reader, writer,
        on_request=lambda method, params: seen.append((method, params)) or {"ok": True},
    ).start()
    try:
        reader.lines.put("this is not json\n")
        reader.send({
            "jsonrpc": "2.0", "id": 7, "method": "session/request_permission",
            "params": {"options": [{"optionId": "allow-once"}]},
        })
        response = writer.messages.get(timeout=2)
        assert response["id"] == 7
        assert response["result"] == {"ok": True}
        assert seen == [("session/request_permission", {"options": [{"optionId": "allow-once"}]})]
    finally:
        reader.close()
        connection.close()


def test_f09_fake_peer_invalid_json_then_request_still_answered():
    """Same skip-and-continue claim over a real stdio peer process."""
    module = load_module()
    seen = []
    previous_mode = os.environ.get("ACP_PEER_MODE")
    os.environ["ACP_PEER_MODE"] = "bad_then_request"
    client = module.AcpProcessClient(
        [sys.executable, "-u", str(PEER)],
        cwd=str(PEER.parent),
        on_request=lambda method, params: seen.append((method, params)) or {
            "outcome": {"outcome": "selected", "optionId": "allow-once"}
        },
    )
    client.start()
    try:
        deadline = time.time() + 3
        while time.time() < deadline and not seen:
            time.sleep(0.05)
        assert seen == [(
            "session/request_permission",
            {"options": [{"optionId": "allow-once"}]},
        )], "valid agent request after a garbage line must still be dispatched"
    finally:
        if previous_mode is None:
            os.environ.pop("ACP_PEER_MODE", None)
        else:
            os.environ["ACP_PEER_MODE"] = previous_mode
        client.stop()


def test_f09_eof_still_unblocks_pending_request():
    """Existing strength — keep as a regression guard."""
    module = load_module()
    reader, writer = QueueReader(), RecordingWriter()
    connection = module.AcpConnection(reader, writer).start()
    errors = []

    def call():
        try:
            connection.request("session/new", {}, timeout=2)
        except Exception as exc:
            errors.append(exc)

    thread = threading.Thread(target=call)
    thread.start()
    writer.messages.get(timeout=1)
    reader.close()
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert errors
    assert "closed" in str(errors[0]).lower()
    connection.close()
