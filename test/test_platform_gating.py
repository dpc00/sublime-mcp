"""Windows-only tools must be gated off on other platforms.

Source-level checks (the plugin imports `sublime`, so it cannot be imported outside Sublime Text):
every tool named in _WINDOWS_ONLY_TOOLS is a real tool, its route is in _WINDOWS_ONLY_ROUTES, and the
gate is applied on every call path and in every place that lists tools.
"""
import re
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parent.parent / "sublime_mcp.py").read_text(encoding="utf-8")


def _frozenset_of(name):
    match = re.search(name + r" = frozenset\(\{(.*?)\}\)", SOURCE, re.S)
    assert match, name + " not found"
    return set(re.findall(r'"([^"]+)"', match.group(1)))


class PlatformGatingTest(unittest.TestCase):
    def test_windows_only_tools_are_real_tools(self):
        tools = _frozenset_of("_WINDOWS_ONLY_TOOLS")
        self.assertEqual(tools, {"get_console_full", "get_console_win", "list_native_windows", "dismiss_native_window"})
        for name in tools:
            self.assertIn('("' + name + '",', SOURCE, name + " is not a registered tool")

    def test_routes_match_the_tools(self):
        routes = _frozenset_of("_WINDOWS_ONLY_ROUTES")
        self.assertEqual(routes, {"/console_full", "/console_win", "/list_native_windows", "/dismiss_native_window"})
        for route in routes:
            self.assertRegex(SOURCE, r'\["' + route + r'"\] =|"' + route + r'":')

    def test_gate_is_only_active_off_windows(self):
        self.assertIn('_WINDOWS_ONLY_TOOLS if sys.platform != "win32" else frozenset()', SOURCE)
        self.assertIn('_WINDOWS_ONLY_ROUTES if sys.platform != "win32" else frozenset()', SOURCE)

    def test_gate_survives_a_settings_reload(self):
        self.assertIn("| _PLATFORM_UNAVAILABLE_TOOLS", SOURCE)

    def test_all_call_paths_are_gated(self):
        self.assertEqual(SOURCE.count("_PLATFORM_UNAVAILABLE_ROUTES:"), 2)  # do_GET and do_POST
        self.assertIn("tool_name in _DISABLED_TOOLS", SOURCE)  # tools/call, batch, POST routes

    def test_listing_and_discovery_hide_gated_tools(self):
        self.assertGreaterEqual(SOURCE.count("if tool[0] not in _DISABLED_TOOLS]"), 3)


if __name__ == "__main__":
    unittest.main()
