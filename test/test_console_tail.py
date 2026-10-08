"""get_console honours `tail` in visible mode, and a capture that cannot get the focus changes nothing.

The line-cutting helpers are pure functions, so they are pulled out of the plugin source and run for
real (the plugin imports `sublime` and cannot be imported outside Sublime Text). The focus check lives
inside a closure that needs Sublime, so it is checked in the source: it must come before anything is
printed to the console, copied to the clipboard or switched.
"""
import re
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parent.parent / "sublime_mcp.py").read_text(encoding="utf-8")


def _load():
    match = re.search(r"(def _tail_lines.*?)\ndef _get_console\(", SOURCE, re.S)
    assert match, "tail helpers not found"
    namespace = {}
    exec(match.group(1), namespace)
    return namespace["_tail_lines"], namespace["_apply_visible_tail"]


tail_lines, apply_tail = _load()
TEXT = "".join("line {}\n".format(i) for i in range(1, 11))  # 10 lines


class TailLinesTest(unittest.TestCase):
    def test_keeps_the_last_lines_and_counts_all(self):
        text, total = tail_lines(TEXT, 3)
        self.assertEqual(text, "line 8\nline 9\nline 10\n")
        self.assertEqual(total, 10)

    def test_zero_or_negative_keeps_everything(self):
        self.assertEqual(tail_lines(TEXT, 0), (TEXT, 10))
        self.assertEqual(tail_lines(TEXT, -5), (TEXT, 10))

    def test_tail_larger_than_the_text_keeps_everything(self):
        self.assertEqual(tail_lines(TEXT, 50), (TEXT, 10))

    def test_text_without_a_final_newline(self):
        text, total = tail_lines("a\nb\nc", 2)
        self.assertEqual((text, total), ("b\nc", 3))

    def test_empty_text(self):
        self.assertEqual(tail_lines("", 5), ("", 0))


class ApplyVisibleTailTest(unittest.TestCase):
    def _visible(self):
        return {"text": TEXT, "length": len(TEXT), "source": "visible_windows", "complete": True}

    def test_cuts_and_reports(self):
        result = apply_tail(self._visible(), 2)
        self.assertEqual(result["text"], "line 9\nline 10\n")
        self.assertEqual(result["length"], len(result["text"]))
        self.assertEqual(result["lines_total"], 10)
        self.assertTrue(result["truncated"])
        self.assertTrue(result["complete"])

    def test_not_truncated_when_it_all_fits(self):
        result = apply_tail(self._visible(), 100)
        self.assertEqual(result["text"], TEXT)
        self.assertFalse(result["truncated"])

    def test_tail_zero_returns_the_original_untouched(self):
        visible = self._visible()
        self.assertIs(apply_tail(visible, 0), visible)

    def test_errors_pass_through(self):
        error = {"error": "not in front"}
        self.assertIs(apply_tail(error, 5), error)

    def test_input_is_not_modified(self):
        visible = self._visible()
        apply_tail(visible, 2)
        self.assertEqual(visible["text"], TEXT)


class FocusCheckTest(unittest.TestCase):
    def test_focus_is_checked_before_anything_is_changed(self):
        check = SOURCE.index("if not force_focus_requested and not own_window_has_focus():")
        start = SOURCE.index("sublime.set_timeout(do_show, 0)")
        self.assertLess(check, start, "the focus check must come before do_show is scheduled")
        # do_show is the only place that prints the marker and replaces the clipboard
        do_show = SOURCE.index("    def do_show():")
        marker_print = SOURCE.index("print(marker)", do_show)
        self.assertLess(do_show, marker_print)
        self.assertLess(marker_print, check, "the marker is printed inside do_show, which only runs after the check")

    def test_visible_results_go_through_the_tail(self):
        self.assertIn("return _apply_visible_tail(visible, tail_n)", SOURCE)

    def test_bad_tail_is_an_error_not_a_crash(self):
        self.assertIn('"tail must be an integer"', SOURCE)


if __name__ == "__main__":
    unittest.main()
