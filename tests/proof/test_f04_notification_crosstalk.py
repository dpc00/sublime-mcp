"""F4 — Shared companion hub + on_close used to always publish
ide/diffRejected, so Claude close/accept paths could bleed Gemini-shaped
reject notifications to every other subscriber.

PROOF: F4 — 2026-08-17.
- close_tab: erase marker before close (already fixed) — no hub reject.
- accept/reject/user-close for Claude-owned: must not hub-notify (Gemini
  protocol is for Gemini-owned diffs only). Behavioral twin + real hub
  subscriber prove the sequences; source locks keep production matching.
"""
import json
import threading
import time
from pathlib import Path

import httpx
import importlib.util

from tests.proof.fakes.fake_diff_host import FakeDiffHost

BACKEND = Path(__file__).parents[2] / "packages" / "st-plugin" / "sublime_mcp.py"
COMPANION = Path(__file__).parents[2] / "packages" / "st-plugin" / "ide_companion.py"


def load_companion():
    spec = importlib.util.spec_from_file_location("ide_companion", COMPANION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _function_source(text, signature, terminator):
    start = text.index(signature)
    end = text.index(terminator, start)
    return text[start:end]


def _collect_notifications(port, token, ready_event, bucket, stop_event):
    try:
        with httpx.stream(
            "GET",
            "http://127.0.0.1:{}/mcp".format(port),
            headers={"Authorization": "Bearer {}".format(token), "Accept": "text/event-stream"},
            timeout=httpx.Timeout(5.0, read=2.0),
        ) as response:
            assert response.status_code == 200
            ready_event.set()
            for line in response.iter_lines():
                if stop_event.is_set():
                    return
                if line.startswith("data: "):
                    bucket.append(json.loads(line[6:]))
    except (httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError):
        # Server stop / test teardown — expected.
        return


def test_f04_close_tab_erases_marker_before_close_in_source():
    text = BACKEND.read_text(encoding="utf-8")
    func = _function_source(
        text, "def _claude_close_tab(arguments):", "def _claude_ide_dispatch(message):"
    )
    erase_index = func.index('review.settings().erase("ide_companion_diff_path")')
    close_index = func.index("review.close()")
    assert erase_index < close_index


def test_f04_close_tab_sets_event_and_pops_itself_in_source():
    text = BACKEND.read_text(encoding="utf-8")
    func = _function_source(
        text, "def _claude_close_tab(arguments):", "def _claude_ide_dispatch(message):"
    )
    assert "_ide_diffs.pop(key, None)" in func
    assert 'state.get("claude_event")' in func
    assert 'state["claude_event"].set()' in func


def test_f04_on_close_skips_hub_notify_for_claude_owned_in_source():
    """Production on_close must not broadcast ide/diffRejected when the
    review is Claude-owned (has claude_event)."""
    text = BACKEND.read_text(encoding="utf-8")
    # Grab on_close body inside IdeCompanionContextListener
    start = text.index("def on_close(self, view):")
    end = text.index("class AcceptIdeCompanionDiffCommand", start)
    body = text[start:end]
    assert "ide/diffRejected" in body
    # Must gate the notify on not being Claude-owned.
    assert "claude_event" in body
    assert "claude_owned" in body or "not state.get(\"claude_event\")" in body or "if not" in body
    # Stronger: twin's contract — notify only when not claude-owned.
    assert "if state and state.get(\"claude_event\")" in body or "claude_owned" in body


def test_f04_claude_close_tab_does_not_notify_gemini_subscriber():
    module = load_companion()
    notifications = []
    server = module.IdeCompanionServer(lambda message: None, auth_token="token")
    port = server.start()
    ready = threading.Event()
    stop = threading.Event()

    def hub_notify(method, params):
        server.notify(method, params)

    host = FakeDiffHost(notify=hub_notify, wait_timeout_seconds=5.0)
    listener = threading.Thread(
        target=_collect_notifications,
        args=(port, "token", ready, notifications, stop),
        daemon=True,
    )
    listener.start()
    try:
        assert ready.wait(2)
        # Give the hub a moment after on_subscribe.
        time.sleep(0.05)

        done = threading.Event()
        result_box = []

        def waiter():
            result_box.append(host.open_claude_diff("/repo/x.py", tab_name="review-1"))
            done.set()

        threading.Thread(target=waiter, daemon=True).start()
        for _ in range(50):
            if "/repo/x.py" in host.diffs:
                break
            time.sleep(0.01)

        host.close_tab("review-1")
        assert done.wait(2)
        assert result_box[0]["content"][0]["text"] == "TAB_CLOSED"
        # Brief window for any stray SSE.
        time.sleep(0.2)
        rejects = [
            n for n in notifications
            if n.get("method") == "ide/diffRejected"
        ]
        assert rejects == [], "Claude close_tab must not bleed ide/diffRejected: {}".format(rejects)
    finally:
        stop.set()
        server.stop()
        listener.join(timeout=2)


def test_f04_claude_user_close_does_not_notify_gemini_subscriber():
    module = load_companion()
    notifications = []
    server = module.IdeCompanionServer(lambda message: None, auth_token="token")
    port = server.start()
    ready = threading.Event()
    stop = threading.Event()

    def hub_notify(method, params):
        server.notify(method, params)

    host = FakeDiffHost(notify=hub_notify, wait_timeout_seconds=5.0)
    listener = threading.Thread(
        target=_collect_notifications,
        args=(port, "token", ready, notifications, stop),
        daemon=True,
    )
    listener.start()
    try:
        assert ready.wait(2)
        time.sleep(0.05)

        done = threading.Event()
        result_box = []

        def waiter():
            result_box.append(host.open_claude_diff("/repo/y.py", tab_name="review-2"))
            done.set()

        threading.Thread(target=waiter, daemon=True).start()
        for _ in range(50):
            if "/repo/y.py" in host.diffs:
                break
            time.sleep(0.01)

        host.user_close_review("/repo/y.py")
        assert done.wait(2)
        assert result_box[0]["content"][0]["text"] == "DIFF_REJECTED"
        time.sleep(0.2)
        rejects = [n for n in notifications if n.get("method") == "ide/diffRejected"]
        assert rejects == [], "Claude user-close must not bleed ide/diffRejected: {}".format(rejects)
    finally:
        stop.set()
        server.stop()
        listener.join(timeout=2)


def test_f04_gemini_user_close_still_notifies_reject():
    """Control: Gemini-owned review close must still publish ide/diffRejected."""
    module = load_companion()
    notifications = []
    server = module.IdeCompanionServer(lambda message: None, auth_token="token")
    port = server.start()
    ready = threading.Event()
    stop = threading.Event()

    def hub_notify(method, params):
        server.notify(method, params)

    host = FakeDiffHost(notify=hub_notify)
    listener = threading.Thread(
        target=_collect_notifications,
        args=(port, "token", ready, notifications, stop),
        daemon=True,
    )
    listener.start()
    try:
        assert ready.wait(2)
        time.sleep(0.05)
        host.open_gemini_diff("/repo/g.py")
        host.user_close_review("/repo/g.py")
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if any(n.get("method") == "ide/diffRejected" for n in notifications):
                break
            time.sleep(0.05)
        rejects = [n for n in notifications if n.get("method") == "ide/diffRejected"]
        assert len(rejects) == 1
        assert rejects[0]["params"]["filePath"] == "/repo/g.py"
    finally:
        stop.set()
        server.stop()
        listener.join(timeout=2)


def test_f04_claude_accept_no_reject_and_no_gemini_accept_bleed():
    notifications = []
    host = FakeDiffHost(notify=lambda m, p: notifications.append((m, p)), wait_timeout_seconds=5.0)
    done = threading.Event()
    result_box = []

    def waiter():
        result_box.append(host.open_claude_diff("/repo/a.py", tab_name="t"))
        done.set()

    threading.Thread(target=waiter, daemon=True).start()
    for _ in range(50):
        if "/repo/a.py" in host.diffs:
            break
        time.sleep(0.01)
    host.accept("/repo/a.py", final_content="ok")
    assert done.wait(2)
    assert result_box[0]["content"][0]["text"] == "FILE_SAVED"
    assert notifications == []
