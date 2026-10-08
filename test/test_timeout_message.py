"""The main-thread timeout message names a real dialog, or says the thread is busy.

Before this, every timeout said a native dialog was blocking Sublime, which sent callers looking for
a dialog while a package was only loading or installing. The message logic is a pure function, so it
is pulled out of the plugin source and run for real (the plugin imports `sublime` and cannot be
imported outside Sublime Text).
"""
import re
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parent.parent / "sublime_mcp.py").read_text(encoding="utf-8")


def _load():
    match = re.search(r"(_BLOCKING_WINDOW_KINDS = .*?)\ndef _main_thread_timeout_message", SOURCE, re.S)
    assert match, "timeout message helpers not found"
    namespace = {}
    exec(match.group(1), namespace)
    return namespace["_timeout_message"]


message = _load()
LABEL = "sublime_mcp.py:2036"


def _w(kind, title):
    return {"kind": kind, "title": title, "class": "x"}


class TimeoutMessageTest(unittest.TestCase):
    def test_a_dialog_is_named(self):
        text = message(LABEL, [_w("editor_window", "a.txt - Sublime Text"), _w("dialog", "Delete File")])
        self.assertIn('"Delete File" (dialog)', text)
        self.assertIn("dismiss_native_window", text)
        self.assertNotIn("is busy", text)

    def test_a_menu_and_a_plain_window_count_as_blocking(self):
        self.assertIn("(menu)", message(LABEL, [{"kind": "menu", "class": "#32768"}]))
        self.assertIn('"Update" (window)', message(LABEL, [_w("window", "Update")]))

    def test_no_dialog_means_busy_and_says_what_it_was_running(self):
        text = message(LABEL, [_w("editor_window", "a.txt - Sublime Text")])
        self.assertIn("No native dialog or menu is open", text)
        self.assertIn("busy", text)
        self.assertIn(LABEL, text)
        self.assertNotIn("blocks Sublime's main thread", text)

    def test_other_window_kinds_are_not_blamed(self):
        text = message(LABEL, [_w("other", "tooltip"), _w("editor_window", "a.txt - Sublime Text")])
        self.assertIn("No native dialog or menu is open", text)

    def test_unknown_windows_give_a_hedged_message(self):
        text = message(LABEL, None)
        self.assertIn("may be blocking", text)
        self.assertIn("Windows only", text)

    def test_every_message_starts_with_the_same_words(self):
        for windows in (None, [], [_w("dialog", "x")]):
            self.assertTrue(message(LABEL, windows).startswith("main-thread timeout after 5s."))

    def test_the_timeout_uses_the_helper(self):
        self.assertIn("raise TimeoutError(_main_thread_timeout_message(label))", SOURCE)


if __name__ == "__main__":
    unittest.main()
