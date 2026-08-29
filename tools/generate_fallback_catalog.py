"""Regenerate proxy fallback catalogs from the Sublime backend tool list."""

import ast
import json
import pprint
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "packages" / "st-plugin" / "sublime_mcp.py"
NODE_OUTPUT = ROOT / "packages" / "node-proxy" / "fallback-tools.json"
PYTHON_OUTPUT = ROOT / "packages" / "python-proxy" / "tool_catalog.py"
COMMENT = (
    "GENERATED FILE - do not edit. Produced by tools/generate_fallback_catalog.py "
    "from packages/st-plugin/sublime_mcp.py::_MCP_TOOLS. Regenerate after changing "
    "the backend tool catalog."
)


def load_tools():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_MCP_TOOLS" for target in node.targets)
    )
    tools = []
    for entry in assignment.value.elts:
        name, description, schema = (ast.literal_eval(value) for value in entry.elts[:3])
        input_schema = dict(schema or {})
        input_schema.setdefault("type", "object")
        input_schema.setdefault("properties", {})
        tools.append({"name": name, "description": description, "inputSchema": input_schema})
    return sorted(tools, key=lambda tool: tool["name"])


def main():
    tools = load_tools()
    node_text = json.dumps({"_comment": COMMENT, "tools": tools}, indent=2, ensure_ascii=True) + "\n"
    python_text = '"""{}"""\n\nTOOLS = {}\n'.format(
        COMMENT,
        pprint.pformat(tools, indent=4, width=100, sort_dicts=False),
    )
    NODE_OUTPUT.write_bytes(
        node_text.replace("\n", "\r\n").encode("utf-8")
    )
    PYTHON_OUTPUT.write_bytes(
        python_text.replace("\n", "\r\n").encode("utf-8")
    )
    print("generated {} tools".format(len(tools)))


if __name__ == "__main__":
    main()
