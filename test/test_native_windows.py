import importlib.util
import pathlib
import subprocess
import sys
import time
import unittest


MODULE_PATH = pathlib.Path(__file__).parents[1] / "lib" / "native_windows.py"
SPEC = importlib.util.spec_from_file_location("native_windows", MODULE_PATH)
NW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NW)


class PickButtonTest(unittest.TestCase):
    YES_NO = [{"id": 6, "text": "&Yes", "default": True}, {"id": 7, "text": "&No", "default": False}]
    OK_CANCEL = [{"id": 1, "text": "OK", "default": True}, {"id": 2, "text": "Cancel", "default": False}]

    def test_cancel_prefers_idcancel_then_label(self):
        self.assertEqual(NW.pick_button(self.OK_CANCEL, "cancel")["text"], "Cancel")
        self.assertEqual(NW.pick_button(self.YES_NO, "cancel")["text"], "&No")

    def test_ok_prefers_idok_then_label_then_default(self):
        self.assertEqual(NW.pick_button(self.OK_CANCEL, "ok")["id"], 1)
        self.assertEqual(NW.pick_button(self.YES_NO, "ok")["text"], "&Yes")
        odd = [{"id": 9, "text": "Proceed", "default": True}, {"id": 10, "text": "Stop", "default": False}]
        self.assertEqual(NW.pick_button(odd, "ok")["text"], "Proceed")
        self.assertIsNone(NW.pick_button(odd, "cancel"))

    def test_named_button_ignores_case_and_mnemonics(self):
        self.assertEqual(NW.pick_button(self.YES_NO, "button", "no")["id"], 7)
        self.assertEqual(NW.pick_button(self.YES_NO, "button", "&YES")["id"], 6)
        self.assertIsNone(NW.pick_button(self.YES_NO, "button", "Maybe"))

    def test_classify(self):
        self.assertEqual(NW.classify("#32770", "Open"), "dialog")
        self.assertEqual(NW.classify("#32768", ""), "menu")
        self.assertEqual(NW.classify("PX_WINDOW_CLASS", "a.txt - Sublime Text (UNREGISTERED)"), "editor_window")
        self.assertEqual(NW.classify("PX_WINDOW_CLASS", "Changelog"), "window")
        self.assertEqual(NW.classify("Other", "x"), "other")


@unittest.skipUnless(NW.SUPPORTED, "native window handling is Windows only")
class RealDialogTest(unittest.TestCase):
    """Open a real Windows message box in a child process and drive it."""

    def open_box(self, text, title, flags):
        code = (
            "import ctypes, sys\n"
            "sys.exit(ctypes.windll.user32.MessageBoxW(0, %r, %r, %d))\n" % (text, title, flags)
        )
        proc = subprocess.Popen([sys.executable, "-c", code])
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        deadline = time.time() + 15
        while time.time() < deadline:
            wins = [w for w in NW.list_windows(proc.pid) if w["kind"] == "dialog"]
            if wins:
                return proc, wins[0]
            time.sleep(0.1)
        self.fail("the message box did not appear")

    def test_lists_dialog_with_buttons_and_message(self):
        proc, win = self.open_box("Really delete a.txt?", "Delete File", 4)  # MB_YESNO
        self.assertEqual(win["title"], "Delete File")
        self.assertEqual([b["text"] for b in win["buttons"]], ["Yes", "No"])
        self.assertIn("Really delete a.txt?", win["messages"])
        NW.dismiss(proc.pid, action="cancel")
        self.assertEqual(proc.wait(timeout=10), 7)  # IDNO

    def test_cancel_picks_no_and_ok_picks_yes(self):
        proc, _ = self.open_box("q", "t", 4)  # MB_YESNO
        result = NW.dismiss(proc.pid, action="cancel")
        self.assertTrue(result["ok"] and result["closed"], result)
        self.assertEqual(proc.wait(timeout=10), 7)
        proc2, _ = self.open_box("q", "t", 4)
        NW.dismiss(proc2.pid, action="ok")
        self.assertEqual(proc2.wait(timeout=10), 6)  # IDYES

    def test_named_button_and_close(self):
        proc, _ = self.open_box("q", "t", 1)  # MB_OKCANCEL
        result = NW.dismiss(proc.pid, action="button", button_text="OK")
        self.assertTrue(result["closed"], result)
        self.assertEqual(proc.wait(timeout=10), 1)  # IDOK
        proc2, _ = self.open_box("q", "t", 1)
        NW.dismiss(proc2.pid, action="close")
        self.assertEqual(proc2.wait(timeout=10), 2)  # IDCANCEL

    def test_reports_instead_of_raising(self):
        proc, win = self.open_box("q", "t", 4)
        bad = NW.dismiss(proc.pid, action="button", button_text="Maybe")
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["buttons"], ["Yes", "No"])
        self.assertFalse(NW.dismiss(proc.pid, hwnd=1, action="cancel")["ok"])
        self.assertFalse(NW.dismiss(proc.pid, action="explode")["ok"])
        NW.dismiss(proc.pid, action="cancel")
        proc.wait(timeout=10)

    def test_no_dialog_and_other_process_are_refused(self):
        me = NW.dismiss(1, action="cancel")  # pid 1 has no windows of ours
        self.assertFalse(me["ok"])
        proc, win = self.open_box("q", "t", 0)
        # a window of another process cannot be dismissed through our own pid
        import os
        self.assertFalse(NW.dismiss(os.getpid(), hwnd=win["hwnd"], action="close")["ok"])
        NW.dismiss(proc.pid, action="close")
        proc.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
