"""F3 — Claude _claude_open_diff used bare event.wait() with no timeout;
a forgotten review pinned a worker thread forever.

PROOF: F3 — 2026-08-17. FIXED: event.wait(timeout=_CLAUDE_DIFF_WAIT_TIMEOUT_SECONDS)
bounds the wait. On timeout the function returns the default DIFF_REJECTED
without mutating _ide_diffs / the review. Behavioral twin proves a short
timeout unblocks the waiter; source lock keeps production matching.
"""
import threading
import time
from pathlib import Path

from tests.proof.fakes.fake_diff_host import FakeDiffHost

BACKEND = Path(__file__).parents[2] / "packages" / "st-plugin" / "sublime_mcp.py"


def _function_source(text, signature, terminator):
    start = text.index(signature)
    end = text.index(terminator, start)
    return text[start:end]


def test_f03_open_diff_wait_is_bounded_in_source():
    text = BACKEND.read_text(encoding="utf-8")
    func = _function_source(text, "def _claude_open_diff(arguments):", "def _claude_close_tab(arguments):")
    assert "event.wait()" not in func
    assert "event.wait(timeout=_CLAUDE_DIFF_WAIT_TIMEOUT_SECONDS)" in func
    assert "_CLAUDE_DIFF_WAIT_TIMEOUT_SECONDS = 30 * 60" in text


def test_f03_timeout_path_does_not_mutate_shared_state_in_source():
    """After event.wait(...), production must only return claude_result —
    no pop/close on timeout, so an abandoned call can't disturb a live review."""
    text = BACKEND.read_text(encoding="utf-8")
    func = _function_source(text, "def _claude_open_diff(arguments):", "def _claude_close_tab(arguments):")
    after_wait = func.split("event.wait(timeout=_CLAUDE_DIFF_WAIT_TIMEOUT_SECONDS)", 1)[1]
    assert after_wait.strip().startswith('return {"content": state["claude_result"]}')


def test_f03_forgotten_review_unblocks_waiter_with_diff_rejected():
    """Behavioral: short timeout → waiter finishes with DIFF_REJECTED, no hang."""
    host = FakeDiffHost(wait_timeout_seconds=0.15)
    done = threading.Event()
    result_box = []

    def waiter():
        result_box.append(host.open_claude_diff("/tmp/a.py", tab_name="t1"))
        done.set()

    thread = threading.Thread(target=waiter)
    started = time.monotonic()
    thread.start()
    assert done.wait(2.0), "waiter must finish within timeout budget"
    elapsed = time.monotonic() - started
    thread.join(timeout=1)
    assert result_box[0]["content"] == [{"type": "text", "text": "DIFF_REJECTED"}]
    assert 0.10 <= elapsed < 1.0, "should wait ~timeout, not forever or instantly"
    # Timeout must not clear the registry (human may still be reviewing).
    assert "/tmp/a.py" in host.diffs


def test_f03_accept_unblocks_before_timeout_with_file_saved():
    host = FakeDiffHost(wait_timeout_seconds=5.0)
    done = threading.Event()
    result_box = []

    def waiter():
        result_box.append(host.open_claude_diff("/tmp/b.py", tab_name="t2"))
        done.set()

    thread = threading.Thread(target=waiter)
    thread.start()
    # Let the waiter register state.
    for _ in range(50):
        if "/tmp/b.py" in host.diffs:
            break
        time.sleep(0.01)
    host.accept("/tmp/b.py", final_content="new body")
    assert done.wait(2.0)
    thread.join(timeout=1)
    assert result_box[0]["content"][0]["text"] == "FILE_SAVED"
    assert result_box[0]["content"][1]["text"] == "new body"
