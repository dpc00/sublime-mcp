"""The main-thread stack printed to the console on a dispatch timeout is limited to the innermost frames.

A package import can be 40 frames deep; printing all of them put 5 KB into the console on every
timeout and filled every later get_console read. The function is pulled out of the plugin source and
run for real against this test's own main thread.
"""
import re
import sys
import threading
import traceback
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parent.parent / "sublime_mcp.py").read_text(encoding="utf-8")


def _load():
    match = re.search(r"(def _main_thread_stack\(.*?)\n\n\n_in_flight_dispatch", SOURCE, re.S)
    assert match, "_main_thread_stack not found"
    namespace = {"sys": sys, "threading": threading, "traceback": traceback}
    exec(match.group(1), namespace)
    return namespace["_main_thread_stack"]


stack = _load()


def _frames(text):
    return len(re.findall(r"^  File ", text, re.M))  # a frame line starts like this; source lines are indented more


def _deeper(n):
    return stack(None) if n == 0 else _deeper(n - 1)


class MainThreadStackTest(unittest.TestCase):
    def setUp(self):
        if threading.current_thread() is not threading.main_thread():
            self.skipTest("needs to run on the main thread")

    def test_unlimited_gives_every_frame(self):
        self.assertGreater(_frames(_deeper(10)), 10)

    def test_a_limit_keeps_only_the_innermost_frames(self):
        self.assertGreater(_frames(stack()), 3)
        self.assertEqual(_frames(stack(3)), 3)
        self.assertEqual(_frames(stack(1)), 1)

    def test_the_timeout_print_uses_a_limit(self):
        self.assertIn("_main_thread_stack(4)", SOURCE)


if __name__ == "__main__":
    unittest.main()
