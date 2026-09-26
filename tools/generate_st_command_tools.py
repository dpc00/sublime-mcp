"""Generate typed MCP tools for Sublime Text's own commands.

Reads tools/st_commands_metadata.json (a snapshot of CommandsBrowser's Sublime
Text command metadata, MIT licensed, see the "_source" key) and writes two
generated blocks into sublime_mcp.py:

  * routes  - entries inside the `_POST = {...}` dict
  * tools   - entries inside the `_MCP_TOOLS = [...]` list

A command is skipped when a tool already exposes it: either a tool with the same
name exists, or a tool is routed to a hand-written `_vc/_wc/_ac("<command>")`
wrapper. Generated blocks are stripped before that check, so the script is
idempotent. Run `python tools/generate_fallback_catalog.py` afterwards so the
proxy fallback catalogs pick up the new tools.
"""

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sublime_mcp.py"
SNAPSHOT = ROOT / "tools" / "st_commands_metadata.json"

ROUTES_BEGIN = "    # BEGIN GENERATED ST COMMAND ROUTES (tools/generate_st_command_tools.py)"
ROUTES_END = "    # END GENERATED ST COMMAND ROUTES"
TOOLS_BEGIN = "    # BEGIN GENERATED ST COMMAND TOOLS (tools/generate_st_command_tools.py)"
TOOLS_END = "    # END GENERATED ST COMMAND TOOLS"

KIND = {
    "text": ("_vc", "TextCommand"),
    "window": ("_wc", "WindowCommand"),
    "find": ("_wc", "WindowCommand"),
    "application": ("_ac", "ApplicationCommand"),
}

BEHAVIOR = ROOT / "tools" / "st_commands_behavior.json"

def load_behavior():
    if not BEHAVIOR.exists():
        return {}
    return json.loads(BEHAVIOR.read_text(encoding="utf-8")).get("commands", {})


def _window_titles(rec):
    titles = []
    for w in (rec or {}).get("new_windows") or []:
        cls, _, title = w.partition(" | ")
        if cls == "#32768":
            titles.append("native menu")
        elif cls == "#32770":
            titles.append(title.strip() or "dialog")
        else:
            titles.append(title.strip() or "window")
    return titles


def observed_note(name, behavior):
    """One sentence stating what running the command was OBSERVED to do on a bare
    Sublime Text 4215 (tools/probe_st_commands.py). Empty when nothing notable."""
    rec = behavior.get(name)
    if not rec:
        return ""
    passes = [("", rec), ("when given arguments: ", rec.get("with_args"))]
    parts = []
    for prefix, r in passes:
        if not r:
            continue
        tags = set(r.get("tags") or [])
        found = []
        if "EXITS_APP" in tags:
            found.append("quits Sublime Text (which also stops this MCP server)")
        if "BLOCKS_MAIN_THREAD" in tags:
            t = ", ".join('"{}"'.format(x) for x in _window_titles(r)[:2]) or "a native window"
            found.append("opens a native OS window ({}) that blocks Sublime's main thread until a person "
                         "dismisses it".format(t))
        elif "NEW_OS_WINDOW" in tags and "NEW_ST_WINDOW" not in tags:
            t = ", ".join('"{}"'.format(x) for x in _window_titles(r)[:2])
            found.append("opens a separate window ({})".format(t))
        if "NEW_ST_WINDOW" in tags:
            found.append("opens a new Sublime Text window")
        if tags & {"OPENS_PANEL", "VISUAL_ONLY_OVERLAY_OR_POPUP"} and not tags & {"BLOCKS_MAIN_THREAD", "NEW_OS_WINDOW"}:
            found.append("shows an in-app panel, popup or overlay (dismiss with hide_overlay, hide_panel or hide_popup)")
        if "STARTS_EXTERNAL_APP" in tags:
            found.append("starts another program ({})".format(", ".join(r.get("new_processes") or ["see st_commands_behavior.json"])))
        if "CHANGES_FILES" in tags:
            found.append("writes files")
        if "CHANGES_SETTINGS_OR_SESSION" in tags:
            found.append("writes Sublime Text settings")
        if "CHANGES_CLIPBOARD" in tags:
            found.append("changes the clipboard")
        if found:
            parts.append(prefix + "; ".join(found))
    if not parts:
        return ""
    # de-duplicate an identical statement from both passes
    if len(parts) == 2 and parts[1].split(": ", 1)[1] == parts[0]:
        parts = parts[:1]
    return "Observed on Sublime Text 4215: " + " | ".join(parts) + "."


def strip_blocks(text):
    for begin, end in ((ROUTES_BEGIN, ROUTES_END), (TOOLS_BEGIN, TOOLS_END)):
        pattern = re.compile(
            r"^" + re.escape(begin) + r"\n.*?^" + re.escape(end) + r"\n",
            re.S | re.M,
        )
        text = pattern.sub("", text)
    return text


def existing_coverage(text):
    """Return (tool_names, covered_commands) from source without generated blocks."""
    tree = ast.parse(text)
    tool_names = set()
    used_routes = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "_MCP_TOOLS" for t in node.targets
        ):
            for elt in node.value.elts:
                tool_names.add(elt.elts[0].value)
                handler = elt.elts[3]
                if (
                    isinstance(handler, ast.Call)
                    and getattr(handler.func, "id", "") == "_p"
                    and handler.args
                    and isinstance(handler.args[0], ast.Constant)
                ):
                    used_routes.add(handler.args[0].value)
    wired = {}
    for m in re.finditer(r'"(/[A-Za-z0-9_]+)":\s*_(?:vc|wc|ac)\("([^"]+)"\)', text):
        wired[m.group(1)] = m.group(2)
    covered = set(tool_names)
    for route in used_routes:
        if route in wired:
            covered.add(wired[route])
    return tool_names, covered


def json_schema_type(type_string):
    t = (type_string or "").strip().rstrip(".").lower()
    if "|" in t:
        return None
    if t in ("string", "str"):
        return "string"
    if t in ("boolean", "bool"):
        return "boolean"
    if t == "int":
        return "integer"
    if t == "float":
        return "number"
    if t.startswith("list["):
        return "array"
    if t in ("object", "dict") or t.startswith("dict["):
        return "object"
    return None


def build_schema(args):
    props = {}
    for arg in args or []:
        name = arg.get("name")
        if not name:
            continue
        prop = {}
        t = json_schema_type(arg.get("type"))
        if t:
            prop["type"] = t
        doc = arg.get("doc_string")
        if doc:
            prop["description"] = " ".join(doc.split())
        props[name] = prop
    return {"type": "object", "properties": props}


def build_description(name, meta, behavior):
    _, kind_name = KIND[meta["command_type"]]
    doc = " ".join((meta.get("doc_string") or "").split())
    if not doc:
        doc = "Runs the Sublime Text '{}' command.".format(name)
    if doc[-1] not in ".!?":
        doc += "."
    doc += " ({})".format(kind_name)
    note = observed_note(name, behavior)
    if note:
        doc += " " + note
    return doc


def main():
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    commands = snapshot["commands"]
    behavior = load_behavior()
    text = strip_blocks(SOURCE.read_text(encoding="utf-8"))
    tool_names, covered = existing_coverage(text)

    route_lines = [ROUTES_BEGIN]
    tool_lines = [TOOLS_BEGIN]
    generated = []
    for name in sorted(commands):
        meta = commands[name]
        if name in covered or name in tool_names or meta.get("command_type") not in KIND:
            continue
        helper, _ = KIND[meta["command_type"]]
        route_lines.append('    "/{0}": {1}("{0}"),'.format(name, helper))
        schema = json.dumps(build_schema(meta.get("args")), ensure_ascii=True)
        tool_lines.append(
            '    ({name},\n     {desc},\n     {schema},\n     _p("/{raw}")),'.format(
                name=json.dumps(name),
                desc=json.dumps(build_description(name, meta, behavior), ensure_ascii=True),
                schema=schema,
                raw=name,
            )
        )
        generated.append(name)
    route_lines.append(ROUTES_END)
    tool_lines.append(TOOLS_END)

    lines = text.split("\n")

    def closing_index(start_pattern, close_pattern):
        start = next(i for i, l in enumerate(lines) if re.match(start_pattern, l))
        return next(j for j in range(start + 1, len(lines)) if re.match(close_pattern, lines[j]))

    # Insert tools first (later in the file) so the earlier index stays valid.
    tools_close = closing_index(r"^_MCP_TOOLS = \[", r"^\]")
    lines[tools_close:tools_close] = tool_lines
    routes_close = closing_index(r"^_POST = \{", r"^\}")
    lines[routes_close:routes_close] = route_lines

    SOURCE.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("generated {} typed tools for Sublime Text commands".format(len(generated)))
    return generated


if __name__ == "__main__":
    main()
