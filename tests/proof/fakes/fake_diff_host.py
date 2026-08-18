"""Behavioral twin of the Claude/Gemini diff lifecycle in sublime_mcp.py.

Mirrors control flow only (no Sublime UI):
  _claude_open_diff, _claude_close_tab, Accept/Reject commands, on_close

Kept in lockstep with production via tests/proof/test_f03_* and test_f04_*
source-parity checks. When production changes ordering, update this twin.
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Optional


NotifyFn = Callable[[str, dict], None]


class FakeReview:
    """Stand-in for a Sublime review view + settings."""

    def __init__(self, file_path: str):
        self._settings = {"ide_companion_diff_path": file_path}
        self.closed = False
        self.valid = True

    def settings_get(self, key, default=None):
        return self._settings.get(key, default)

    def settings_erase(self, key):
        self._settings.pop(key, None)

    def is_valid(self):
        return self.valid and not self.closed

    def close(self):
        self.closed = True
        self.valid = False


class FakeDiffHost:
    """In-process diff registry + Claude wait semantics."""

    def __init__(
        self,
        notify: Optional[NotifyFn] = None,
        wait_timeout_seconds: float = 30 * 60,
    ):
        self._notify = notify or (lambda method, params: None)
        self.wait_timeout_seconds = wait_timeout_seconds
        self.diffs: Dict[str, dict] = {}

    def _key(self, file_path: str) -> str:
        return file_path

    def open_claude_diff(self, file_path: str, tab_name: Optional[str] = None) -> dict:
        """Mirror _claude_open_diff after the review is already open."""
        key = self._key(file_path)
        if key in self.diffs:
            return {"isError": True, "content": [{"type": "text", "text": "already open"}]}
        review = FakeReview(file_path)
        event = threading.Event()
        # Keep a local ref to the state dict — production does the same so
        # accept/reject/close can mutate claude_result even after popping the
        # map entry; re-getting from self.diffs after wait would lose the result.
        state = {
            "file_path": file_path,
            "review": review,
            "claude_event": event,
            "claude_result": [{"type": "text", "text": "DIFF_REJECTED"}],
            "claude_tab_name": tab_name,
        }
        self.diffs[key] = state
        # Bounded wait — production uses _CLAUDE_DIFF_WAIT_TIMEOUT_SECONDS.
        event.wait(timeout=self.wait_timeout_seconds)
        return {"content": state["claude_result"]}

    def close_tab(self, tab_name: str) -> dict:
        """Mirror _claude_close_tab: pop, set event, erase marker, then close."""
        for key, state in list(self.diffs.items()):
            if state.get("claude_tab_name") == tab_name:
                state["claude_result"] = [{"type": "text", "text": "TAB_CLOSED"}]
                review = state["review"]
                self.diffs.pop(key, None)
                if state.get("claude_event"):
                    state["claude_event"].set()
                if review and review.is_valid():
                    # Erase before close so on_close no-ops (no hub reject).
                    review.settings_erase("ide_companion_diff_path")
                    review.close()
                    # Simulate ST firing on_close after close().
                    self.on_close(review)
                return {"content": [{"type": "text", "text": "TAB_CLOSED"}]}
        return {"isError": True, "content": [{"type": "text", "text": "Tab not found"}]}

    def accept(self, file_path: str, final_content: str = "accepted-body") -> None:
        """Mirror AcceptIdeCompanionDiffCommand."""
        key = self._key(file_path)
        state = self.diffs.get(key)
        if not state:
            return
        review = state["review"]
        claude_owned = bool(state.get("claude_event"))
        if claude_owned:
            state["claude_result"] = [
                {"type": "text", "text": "FILE_SAVED"},
                {"type": "text", "text": final_content},
            ]
            state["claude_event"].set()
        self.diffs.pop(key, None)
        review.settings_erase("ide_companion_diff_path")
        review.close()
        self.on_close(review)
        # Hub accept is Gemini-protocol; Claude uses the tool result instead.
        if not claude_owned:
            self._notify(
                "ide/diffAccepted",
                {"filePath": file_path, "content": final_content},
            )

    def reject(self, file_path: str) -> None:
        """Mirror RejectIdeCompanionDiffCommand."""
        key = self._key(file_path)
        state = self.diffs.pop(key, None)
        if not state:
            return
        review = state["review"]
        claude_owned = bool(state.get("claude_event"))
        if claude_owned:
            state["claude_result"] = [{"type": "text", "text": "DIFF_REJECTED"}]
            state["claude_event"].set()
        review.settings_erase("ide_companion_diff_path")
        review.close()
        self.on_close(review)
        if not claude_owned:
            self._notify("ide/diffRejected", {"filePath": state["file_path"]})

    def user_close_review(self, file_path: str) -> None:
        """User closes the review tab without Accept/Reject/close_tab."""
        key = self._key(file_path)
        state = self.diffs.get(key)
        if not state:
            return
        review = state["review"]
        # Marker still present — on_close does full cleanup.
        review.close()
        self.on_close(review)

    def on_close(self, review: FakeReview) -> None:
        """Mirror IdeCompanionContextListener.on_close diff branch."""
        diff_path = review.settings_get("ide_companion_diff_path")
        if not diff_path:
            return
        key = self._key(diff_path)
        state = self.diffs.pop(key, None)
        if not state:
            return
        claude_owned = bool(state.get("claude_event"))
        if claude_owned:
            state["claude_event"].set()
        # Claude-owned reviews terminate via claude_result/event only.
        # Broadcasting Gemini-shaped ide/diffRejected would cross-talk to
        # every other companion subscriber on the shared hub.
        if not claude_owned:
            self._notify("ide/diffRejected", {"filePath": state["file_path"]})

    def open_gemini_diff(self, file_path: str) -> None:
        """Gemini openDiff: no claude_event."""
        key = self._key(file_path)
        self.diffs[key] = {
            "file_path": file_path,
            "review": FakeReview(file_path),
        }
