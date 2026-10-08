"""get_quick_panel, pick_quick_panel and click_menu_item, run against a fake `sublime`.

The plugin imports `sublime` and cannot be imported outside Sublime Text, so the functions are pulled
out of the plugin source (as in test_timeout_message.py) and run for real with a small fake.
"""
import json
import re
import types
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parent.parent / "sublime_mcp.py").read_text(encoding="utf-8")


def _between(start, end):
    match = re.search(r"(%s.*?)\n%s" % (re.escape(start), re.escape(end)), SOURCE, re.S)
    assert match, "not found: " + start
    return match.group(1)


class FakeWindow:
    shown = []  # what the real show_quick_panel would have received

    def __init__(self):
        self.commands = []

    def id(self):
        return 1

    def show_quick_panel(self, items, on_select, flags=0, selected_index=-1, on_highlight=None, placeholder=None):
        FakeWindow.shown.append((items, on_select))

    def extract_variables(self):
        return {"packages": "C:/Pk"}

    def run_command(self, cmd, args=None):
        self.commands.append((cmd, args))
        if cmd == "hide_overlay" and FakeWindow.shown:
            FakeWindow.shown[-1][1](-1)  # Sublime reports a cancel when the panel is hidden


PRISTINE_SHOW = FakeWindow.show_quick_panel


def _build(menus):
    window = FakeWindow()
    FakeWindow.show_quick_panel = PRISTINE_SHOW  # earlier tests wrap or replace it
    FakeWindow.shown = []
    sub = types.SimpleNamespace(
        Window=FakeWindow,
        active_window=lambda: window,
        find_resources=lambda pattern: sorted(menus),
        load_resource=lambda r: menus[r],
        decode_value=json.loads,
        expand_variables=lambda a, v: {k: s.replace("${packages}", v["packages"]) if isinstance(s, str) else s
                                       for k, s in a.items()},
        set_timeout=lambda fn, ms: fn(),
        run_command=lambda c, a=None: window.commands.append(("app:" + c, a)),
    )
    plugin = types.SimpleNamespace(
        application_command_classes=[], window_command_classes=[], text_command_classes=[])
    ns = {"sublime": sub, "sublime_plugin": plugin, "_on_main": lambda fn: fn(),
          "_command_name_from_class": lambda c: c.name}
    exec(_between("_QUICK_PANELS = {}", "def _find_in_file("), ns)
    exec(_between("def _walk_menu_items(", "def _active_output_panel_view("), ns)
    exec(_between("def _collect_menu_entries(", "def _get_active_panel("), ns)
    ns["_install_quick_panel_recorder"]()
    return ns, window, plugin


MENU = json.dumps([
    {"caption": "Tools", "children": [
        {"caption": "Command Palette...", "command": "show_overlay", "args": {"overlay": "command_palette"}},
        {"caption": "Build", "command": "build"}]},
    {"caption": "View", "children": [
        {"caption": "Side Bar", "children": [{"caption": "Build", "command": "toggle_side_bar"}]}]},
])


class QuickPanelTest(unittest.TestCase):
    def setUp(self):
        self.ns, self.window, _ = _build({})
        self.picked = []

    def _open(self, items):
        self.window.show_quick_panel(items, self.picked.append)

    def test_items_are_recorded_in_all_three_shapes(self):
        class Item:
            trigger, details, annotation = "t", "d", "a"
        self._open(["a", ["b", "second"], Item()])
        got = self.ns["_get_quick_panel"]({})
        self.assertEqual(got["items"], ["a", ["b", "second"], {"trigger": "t", "details": "d", "annotation": "a"}])

    def test_no_panel_gives_an_error(self):
        self.assertIn("error", self.ns["_get_quick_panel"]({}))
        self.assertIn("error", self.ns["_pick_quick_panel"]({"index": 0}))

    def test_pick_by_index_calls_back_once_with_that_index(self):
        self._open(["a", "b"])
        self.assertTrue(self.ns["_pick_quick_panel"]({"index": 1})["ok"])
        self.assertEqual(self.picked, [1])  # no stray -1 from the hide
        self.assertIn("error", self.ns["_get_quick_panel"]({}))

    def test_pick_by_text_needs_exactly_one_match(self):
        self._open(["apple", "apricot", "berry"])
        self.assertIn("error", self.ns["_pick_quick_panel"]({"text": "ap"}))
        self.assertEqual(self.picked, [])
        self.assertTrue(self.ns["_pick_quick_panel"]({"text": "BERRY"})["ok"])
        self.assertEqual(self.picked, [2])

    def test_an_exact_text_beats_longer_items_that_contain_it(self):
        self._open(["Remove Package", "Remove", "Remove Library"])
        self.assertEqual(self.ns["_pick_quick_panel"]({"text": "remove"})["picked"], 1)
        self.assertEqual(self.picked, [1])

    def test_a_callback_that_raises_is_reported_not_called_ok(self):
        def boom(i):
            raise ValueError("package bug")
        self.window.show_quick_panel(["a"], boom)
        got = self.ns["_pick_quick_panel"]({"index": 0})
        self.assertNotIn("ok", got)
        self.assertIn("ValueError: package bug", got["error"])

    def test_cancel_delivers_one_minus_one(self):
        self._open(["a"])
        self.assertEqual(self.ns["_pick_quick_panel"]({"index": -1})["picked"], -1)
        self.assertEqual(self.picked, [-1])

    def test_bad_index_changes_nothing(self):
        self._open(["a"])
        self.assertIn("error", self.ns["_pick_quick_panel"]({"index": 5}))
        self.assertEqual(self.picked, [])
        self.assertIn("items", self.ns["_get_quick_panel"]({}))

    def test_the_user_closing_the_panel_clears_the_record(self):
        self._open(["a"])
        FakeWindow.shown[-1][1](-1)
        self.assertEqual(self.picked, [-1])
        self.assertIn("error", self.ns["_get_quick_panel"]({}))

    def test_a_generator_of_items_still_reaches_sublime_whole(self):
        self.window.show_quick_panel((x for x in "ab"), self.picked.append)
        self.assertEqual(FakeWindow.shown[-1][0], ["a", "b"])
        self.assertEqual(self.ns["_get_quick_panel"]({})["items"], ["a", "b"])

    def test_a_recording_failure_never_breaks_the_package(self):
        class Bad:
            trigger = property(lambda self: 1 / 0)
        self.window.show_quick_panel([Bad()], self.picked.append)
        self.assertEqual(len(FakeWindow.shown[-1][0]), 1)
        FakeWindow.shown[-1][1](0)
        self.assertEqual(self.picked, [0])

    def test_a_panel_that_fails_to_open_leaves_no_record(self):
        def boom(self, items, on_select, *a, **k):
            raise RuntimeError("bad flags")
        self.ns["_remove_quick_panel_recorder"]()
        FakeWindow.show_quick_panel = boom
        self.ns["_install_quick_panel_recorder"]()
        with self.assertRaises(RuntimeError):
            self.window.show_quick_panel(["a"], self.picked.append)
        self.assertIn("error", self.ns["_get_quick_panel"]({}))

    def test_removal_leaves_a_wrapper_someone_else_added_later(self):
        mine = FakeWindow.show_quick_panel
        theirs = lambda self, items, on_select, *a, **k: None
        FakeWindow.show_quick_panel = theirs
        self.ns["_remove_quick_panel_recorder"]()
        self.assertIs(FakeWindow.show_quick_panel, theirs)
        FakeWindow.show_quick_panel = mine
        self.ns["_remove_quick_panel_recorder"]()
        self.assertFalse(hasattr(FakeWindow.show_quick_panel, "_sublime_mcp_orig"))

    def test_index_and_text_together_or_a_boolean_index_are_refused(self):
        self._open(["a", "b"])
        self.assertIn("error", self.ns["_pick_quick_panel"]({"index": 0, "text": "b"}))
        self.assertIn("error", self.ns["_pick_quick_panel"]({"index": True}))
        self.assertEqual(self.picked, [])

    def test_wrapping_twice_does_not_stack(self):
        self.ns["_install_quick_panel_recorder"]()
        self._open(["a"])
        FakeWindow.shown[-1][1](0)
        self.assertEqual(self.picked, [0])


class ClickMenuItemTest(unittest.TestCase):
    def setUp(self):
        self.ns, self.window, self.plugin = _build({"Packages/Default/Main.sublime-menu": MENU})

    def test_full_path_runs_the_command_with_its_args(self):
        got = self.ns["_click_menu_item"]({"path": "Tools > Command Palette..."})
        self.assertEqual(got["command"], "show_overlay")
        self.assertEqual(self.window.commands, [("show_overlay", {"overlay": "command_palette"})])
        self.assertEqual(got["scope"], "window")

    def test_matching_ignores_case_and_spaces_around_the_arrow(self):
        self.assertTrue(self.ns["_click_menu_item"]({"path": "tools>command palette..."})["ok"])

    def test_an_ambiguous_end_of_path_lists_the_candidates_and_runs_nothing(self):
        got = self.ns["_click_menu_item"]({"path": "Build"})
        self.assertEqual(len(got["matches"]), 2)
        self.assertEqual(self.window.commands, [])

    def test_a_longer_path_disambiguates(self):
        self.assertEqual(self.ns["_click_menu_item"]({"path": "Side Bar > Build"})["command"], "toggle_side_bar")

    def test_a_submenu_or_missing_item_is_an_error(self):
        self.assertIn("error", self.ns["_click_menu_item"]({"path": "Tools"}))
        self.assertIn("error", self.ns["_click_menu_item"]({"path": "Tools > Nope"}))
        self.assertIn("error", self.ns["_click_menu_item"]({"path": ""}))
        self.assertEqual(self.window.commands, [])

    def test_scope_comes_from_the_plugin_command_classes(self):
        self.plugin.application_command_classes.append(types.SimpleNamespace(name="build"))
        got = self.ns["_click_menu_item"]({"path": "Tools > Build"})
        self.assertEqual(got["scope"], "application")
        self.assertEqual(self.window.commands, [("app:build", {})])

    def test_a_text_command_needs_an_active_view(self):
        self.plugin.text_command_classes.append(types.SimpleNamespace(name="build"))
        self.window.active_view = lambda: None
        self.assertIn("error", self.ns["_click_menu_item"]({"path": "Tools > Build"}))

    def test_the_real_ellipsis_and_mnemonics_match_the_ascii_path(self):
        menu = json.dumps([{"caption": "&Tools", "children": [
            {"caption": "Command Palette…", "command": "show_overlay"}]}])
        ns, window, _ = _build({"m.sublime-menu": menu})
        self.assertEqual(ns["_click_menu_item"]({"path": "Tools > Command Palette..."})["command"], "show_overlay")
        self.assertEqual(ns["_click_menu_item"]({"path": "Tools > Command Palette…"})["command"], "show_overlay")

    def test_items_without_a_caption_match_by_command_name(self):
        # the shapes seen in Packages/Default/Main.sublime-menu on build 4215
        menu = json.dumps([
            {"caption": "Selection", "children": [{"command": "select_all"}]},
            {"caption": "View", "children": [{"caption": "Side Bar", "id": "side_bar", "children": [
                {"command": "toggle_side_bar"}, {"command": "toggle_show_open_files"}]}]}])
        ns, window, _ = _build({"m.sublime-menu": menu})
        for path in ("Selection > Select All", "Selection > select_all", "select all"):
            self.assertEqual(ns["_click_menu_item"]({"path": path})["command"], "select_all")
        self.assertEqual(ns["_click_menu_item"]({"path": "Side Bar > toggle_side_bar"})["command"], "toggle_side_bar")
        got = ns["_click_menu_item"]({"path": "Side Bar"})  # a submenu: nothing to run
        self.assertIn("error", got)
        self.assertIn("by command name", got["error"])

    def test_the_same_uncaptioned_command_in_two_menus_is_told_apart_in_the_error(self):
        menu = json.dumps([
            {"caption": "Selection", "children": [{"command": "select_all"}]},
            {"caption": "Edit", "children": [{"command": "select_all"}]}])
        ns, window, _ = _build({"m.sublime-menu": menu})
        got = ns["_click_menu_item"]({"path": "select all"})
        self.assertEqual(sorted(m["path"] for m in got["matches"]), ["Edit", "Selection"])
        self.assertEqual(window.commands, [])
        self.assertTrue(ns["_click_menu_item"]({"path": "Edit > select all"})["ok"])

    def test_the_same_item_in_two_menu_files_is_not_ambiguous(self):
        menu = json.dumps([{"caption": "Selection", "children": [{"command": "select_all"}]}])
        ns, window, _ = _build({"a.sublime-menu": menu, "b.sublime-menu": menu})
        self.assertTrue(ns["_click_menu_item"]({"path": "Selection > select_all"})["ok"])
        self.assertEqual(len(window.commands), 1)

    def test_variables_in_menu_args_are_expanded(self):
        menu = json.dumps([{"caption": "Preferences", "children": [
            {"caption": "Settings", "command": "open_file", "args": {"file": "${packages}/User/x"}}]}])
        ns, window, _ = _build({"m.sublime-menu": menu})
        ns["_click_menu_item"]({"path": "Preferences > Settings"})
        self.assertEqual(window.commands, [("open_file", {"file": "C:/Pk/User/x"})])

    def test_a_guessed_scope_is_flagged_and_a_known_one_is_not(self):
        got = self.ns["_click_menu_item"]({"path": "Tools > Build"})
        self.assertIn("guess", got["note"])
        self.plugin.window_command_classes.append(types.SimpleNamespace(name="build"))
        self.assertNotIn("note", self.ns["_click_menu_item"]({"path": "Tools > Build"}))
        self.assertNotIn("note", self.ns["_click_menu_item"]({"path": "Tools > Build", "scope": "window"}))

    def test_a_bad_scope_is_refused(self):
        self.assertIn("error", self.ns["_click_menu_item"]({"path": "Tools > Build", "scope": "bogus"}))
        self.assertEqual(self.window.commands, [])

    def test_get_menu_items_still_reports_unreadable_resources(self):
        ns, window, _ = _build({"a.sublime-menu": "{not json", "b.sublime-menu": MENU})
        entries = ns["_collect_menu_entries"]("", "", "", True)
        self.assertTrue(any("error" in e for e in entries))
        self.assertFalse(any("error" in e for e in ns["_collect_menu_entries"]()))

    def test_unreadable_menu_resources_are_skipped(self):
        ns, window, _ = _build({"a.sublime-menu": "{not json", "b.sublime-menu": MENU})
        self.assertTrue(ns["_click_menu_item"]({"path": "Tools > Command Palette..."})["ok"])


if __name__ == "__main__":
    unittest.main()
