"""A tool call with an argument the tool does not list gets a warning in its result.

The helpers are pure functions, so they are pulled out of the plugin source and run for real (the plugin
itself imports `sublime` and cannot be imported outside Sublime Text).
"""
import re
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parent.parent / "sublime_mcp.py").read_text(encoding="utf-8")


def _load_helpers():
    match = re.search(r"(def _unknown_arg_warning.*?)\n_BATCH_MAX_CALLS", SOURCE, re.S)
    assert match, "unknown-argument helpers not found"
    namespace = {}
    exec(match.group(1), namespace)
    return namespace["_unknown_arg_warning"], namespace["_with_arg_warning"]


warning_for, with_warning = _load_helpers()
DELETE_SCHEMA = {"type": "object", "properties": {"files": {"type": "array"}, "prompt": {"type": "boolean"}}}


class UnknownArgumentTest(unittest.TestCase):
    def test_wrong_name_is_reported_with_the_valid_names(self):
        text = warning_for(DELETE_SCHEMA, {"path": "x"})
        self.assertIn("path", text)
        self.assertIn("files, prompt", text)

    def test_known_arguments_give_no_warning(self):
        self.assertIsNone(warning_for(DELETE_SCHEMA, {"files": ["a"], "prompt": False}))

    def test_no_arguments_give_no_warning(self):
        self.assertIsNone(warning_for(DELETE_SCHEMA, {}))
        self.assertIsNone(warning_for(DELETE_SCHEMA, None))

    def test_schema_without_properties_is_left_alone(self):
        self.assertIsNone(warning_for({}, {"anything": 1}))
        self.assertIsNone(warning_for(None, {"anything": 1}))
        self.assertIsNone(warning_for({"type": "object", "properties": {}}, {"anything": 1}))

    def test_dict_result_gets_the_warning_and_keeps_its_content(self):
        result = with_warning({"ok": True}, DELETE_SCHEMA, {"path": "x"})
        self.assertEqual(result["ok"], True)
        self.assertIn("path", result["warning"])

    def test_original_result_is_not_changed(self):
        original = {"ok": True}
        with_warning(original, DELETE_SCHEMA, {"path": "x"})
        self.assertNotIn("warning", original)

    def test_list_result_is_returned_unchanged(self):
        content = [{"type": "text", "text": "hi"}]
        self.assertIs(with_warning(content, DELETE_SCHEMA, {"path": "x"}), content)

    def test_existing_warning_is_kept(self):
        result = with_warning({"ok": True, "warning": "mine"}, DELETE_SCHEMA, {"path": "x"})
        self.assertEqual(result["warning"], "mine")

    def test_both_call_paths_use_it(self):
        self.assertIn("_with_arg_warning(entry[3](tool_args), entry[2], tool_args)", SOURCE)  # tools/call
        self.assertIn("handler(tool_args), schemas_by_name.get(tool_name), tool_args", SOURCE)  # batch


if __name__ == "__main__":
    unittest.main()
