import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = {"get_help", "batch", "get_active_file", "project_search",
           "str_replace_based_edit_tool", "save_file", "discover_tools"}


def catalog_names():
    tree = ast.parse((ROOT / "sublime_mcp.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_MCP_TOOLS" for t in node.targets):
            return [e.elts[0].value for e in node.value.elts]
    raise AssertionError("_MCP_TOOLS not found")


class ToolTreeTest(unittest.TestCase):
    def test_every_hidden_tool_is_in_exactly_one_leaf(self):
        tree = json.loads((ROOT / "tool_tree.json").read_text(encoding="utf-8"))
        placed = [n for cat in tree.values() for leaf in cat["children"].values() for n in leaf["tools"]]
        self.assertEqual(len(placed), len(set(placed)), "a tool is listed twice")
        self.assertEqual(set(placed), set(catalog_names()) - DEFAULT)

    def test_every_node_has_a_description(self):
        tree = json.loads((ROOT / "tool_tree.json").read_text(encoding="utf-8"))
        for cat in tree.values():
            self.assertTrue(cat["description"])
            for leaf in cat["children"].values():
                self.assertTrue(leaf["description"])
                self.assertTrue(leaf["tools"])


if __name__ == "__main__":
    unittest.main()
