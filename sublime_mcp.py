"""sublime_mcp.py — HTTP bridge that exposes the Sublime Text API to Claude.

Architecture
------------
An external MCP server (the Node.js/Python process that Claude talks to) cannot
call Sublime's Python API directly because ST's API is only available inside
ST's embedded Python interpreter.  This plugin solves that by starting a
lightweight HTTP server on 127.0.0.1:9500 inside ST.  The MCP server sends
HTTP requests; this plugin handles them on ST's main thread and returns JSON.

Thread model
------------
The HTTP server runs on a daemon thread (one request at a time, no thread pool).
ST's Python API is NOT thread-safe — every call must be on the main thread.
_on_main(fn) is the bridge:
  1. Wraps fn() in a closure that captures exceptions and signals a threading.Event.
  2. Schedules the closure on the main thread via sublime.set_timeout(..., 0).
  3. Blocks the HTTP thread on done.wait(5.0) until the main thread runs it.
This gives the HTTP thread a synchronous result while keeping all ST API calls
on the correct thread.

Routing
-------
GET  /endpoint  → handler(params)   where params = parse_qs(query_string)
POST /endpoint  → handler(body)     where body = json.loads(request_body)

The _GET and _POST dicts map URL paths to handler functions.  Every handler
returns a plain dict that is serialised to JSON and sent back.

Console capture
---------------
_install_console_capture() monkey-patches sublime_api.log_message and
sys.stdout.write so that all print() calls and ST console output are captured
into _console_buf.  The /console_log endpoint exposes the tail of that buffer.
This lets Claude read the ST console without the user having to open it.

Phantom inspection
------------------
_get_view_phantoms walks sys.modules looking for any module that has a
_phantom_sets dict (the standard pattern used by plugins including this one
and pybackup_ui.py).  It then extracts the HTML content of each phantom and
strips tags to produce readable plain text.

str_replace_based_edit
----------------------
_edit_file implements the same four-command interface as the Claude Code
str_replace_based_edit_tool so the external MCP server can delegate file
edits directly into open ST views with gutter highlighting:
  view       → return numbered file content
  str_replace→ find unique old_str, replace with new_str, highlight in green
  insert     → insert text after a given line, highlight in blue
  create     → create a new file with initial content

Install: copy this file to Packages/User/ (or symlink it there).
Port: 9500 (Windows) / 9501 (Mac/Linux) — override with SUBLIME_MCP_PORT env var
"""

import contextlib
import html
import io
import json
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlparse

import sublime
import sublime_plugin

_PORT = int(os.environ.get("SUBLIME_MCP_PORT", 9500 if sys.platform == "win32" else 9501))


# ── main-thread dispatch ──────────────────────────────────────────────────────


def _on_main(fn):
    """Run fn() on ST's main thread and return its result (or re-raise its exception).

    ST's Python API is not thread-safe; this is the only correct way to call
    it from the HTTP handler thread.  Uses a threading.Event as a one-shot
    barrier: the HTTP thread blocks on done.wait() while the main thread
    executes fn() via sublime.set_timeout(..., 0).  Times out after 5 s so
    a deadlock doesn't hang the HTTP thread forever.
    """
    result = [None]
    exc = [None]
    done = threading.Event()

    def _run():
        try:
            result[0] = fn()
        except Exception as e:
            exc[0] = e
        finally:
            done.set()

    sublime.set_timeout(_run, 0)
    done.wait(5.0)
    if exc[0]:
        raise exc[0]
    return result[0]


def _active_view():
    return sublime.active_window().active_view()


def _command_name_from_class(cls):
    """Convert a Command class name to ST's snake_case command string.

    ST strips the 'Command' suffix and lowercases the CamelCase remainder.
    Example: OpenClaudeTerminusHereCommand -> 'open_claude_terminus_here'
    """
    name = cls.__name__
    if name.endswith("Command"):
        name = name[:-7]
    parts = re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|\d+", name)
    return "_".join(part.lower() for part in parts if part)


def _package_name_from_resource(resource_path):
    parts = resource_path.split("/", 2)
    if len(parts) >= 2 and parts[0] == "Packages":
        return parts[1]
    return None


def _walk_menu_items(items, resource, path, caption_filter, command_filter, out):
    for item in items or []:
        if not isinstance(item, dict):
            continue
        caption = item.get("caption", "")
        command = item.get("command", "")
        next_path = path + ([caption] if caption else [])
        matches = True
        if caption_filter and caption_filter not in caption.lower():
            matches = False
        if command_filter and command_filter not in command.lower():
            matches = False
        if matches and (caption or command):
            out.append(
                {
                    "caption": caption,
                    "command": command,
                    "args": item.get("args", {}),
                    "resource": resource,
                    "path": next_path,
                    "id": item.get("id"),
                    "mnemonic": item.get("mnemonic"),
                    "checkbox": item.get("checkbox"),
                }
            )
        children = item.get("children")
        if isinstance(children, list):
            _walk_menu_items(
                children, resource, next_path, caption_filter, command_filter, out
            )


def _active_output_panel_view(window):
    panel_name = window.active_panel()
    if not panel_name or not panel_name.startswith("output."):
        return None, None
    short_name = panel_name.split(".", 1)[1]
    return short_name, window.find_output_panel(short_name)


def _find_view_by_name(window, name):
    views = window.views()
    if name:
        match = next(
            (v for v in views if name.lower() in (v.name() or "").lower()), None
        )
        if not match:
            return None, [v.name() for v in views]
        return match, None
    return window.active_view(), None


def _clean_phantom_text(text):
    """Strip HTML from phantom content and return readable plain text.

    Phantoms store their content as raw HTML including inline CSS.  This
    function removes <style> and <script> blocks entirely, converts block
    elements (div, p, a closing tags, br) to newlines, strips remaining tags,
    unescapes HTML entities, and collapses blank lines.
    """
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(
        r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL
    )
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</a>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(div|p|h\d|li|tr)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line.strip()).strip()


# ── console log capture ───────────────────────────────────────────────────────

_console_buf = []
_console_patched = False


def _install_console_capture():
    """Monkey-patch ST's console and stdout to capture messages into _console_buf.

    Called once (guarded by _console_patched).  Wraps two entry points:
      1. sublime_api.log_message — the C-level function behind ST's console;
         every ST internal log and print() that goes through sublime_api passes here.
      2. sys.stdout.write — captures print() output from plugin code that
         hasn't gone through sublime_api (tagged with '[stdout]' prefix).

    The buffer is a plain list; callers slice the tail with _console_buf[-n:].
    """
    global _console_patched
    if _console_patched:
        return
    import sublime_api as _sapi

    _orig_log = _sapi.log_message

    def _capture_log(msg):
        _console_buf.append(msg)
        _orig_log(msg)

    _sapi.log_message = _capture_log

    orig_write = sys.stdout.write

    def _capture_write(s):
        _console_buf.append(f"[stdout]{s}")
        return orig_write(s)

    sys.stdout.write = _capture_write
    sys.stdout._capture_patched = True
    _console_patched = True


# ── GET handlers ──────────────────────────────────────────────────────────────


def _get_active_file(params):
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        sel = v.sel()
        pt = sel[0].begin() if sel else 0
        row, col = v.rowcol(pt)
        syn = v.syntax()
        return {
            "path": v.file_name(),
            "name": v.name(),
            "content": v.substr(sublime.Region(0, v.size())),
            "line": row + 1,
            "col": col + 1,
            "is_dirty": v.is_dirty(),
            "syntax": syn.name if syn else None,
        }

    return _on_main(fn)


def _get_selection(params):
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        out = []
        for r in v.sel():
            ar, ac = v.rowcol(r.begin())
            br, bc = v.rowcol(r.end())
            out.append(
                {
                    "text": v.substr(r),
                    "begin_line": ar + 1,
                    "begin_col": ac + 1,
                    "end_line": br + 1,
                    "end_col": bc + 1,
                }
            )
        return {"selections": out}

    return _on_main(fn)


def _get_cursor_context(params):
    n = int(params.get("lines", ["10"])[0])

    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        sel = v.sel()
        pt = sel[0].begin() if sel else 0
        row, col = v.rowcol(pt)
        start_row = max(0, row - n)
        end_row = row + n
        start_pt = v.text_point(start_row, 0)
        end_line = v.text_point(min(end_row, v.rowcol(v.size())[0]), 0)
        end_pt = v.full_line(end_line).end()
        text = v.substr(sublime.Region(start_pt, end_pt))
        lines = text.split("\n")
        numbered = "\n".join(f"{start_row + i + 1:4}: {l}" for i, l in enumerate(lines))
        return {
            "path": v.file_name(),
            "cursor_line": row + 1,
            "cursor_col": col + 1,
            "start_line": start_row + 1,
            "context": numbered,
        }

    return _on_main(fn)


def _get_open_files(params):
    def fn():
        import os

        w = sublime.active_window()

        def _name(v):
            n = v.name()
            if n:
                return n
            fp = v.file_name()
            return os.path.basename(fp) if fp else ""

        return {
            "files": [
                {"path": v.file_name(), "name": _name(v), "is_dirty": v.is_dirty()}
                for v in w.views()
            ]
        }

    return _on_main(fn)


def _get_sheets(params):
    def fn():
        w = sublime.active_window()
        out = []
        for i, s in enumerate(w.sheets()):
            kind = type(s).__name__
            path = None
            try:
                path = s.file_name()
            except Exception:
                pass
            v = s.view()
            out.append(
                {
                    "index": i,
                    "id": s.id(),
                    "type": kind,
                    "path": path,
                    "name": v.name() if v else None,
                    "is_dirty": v.is_dirty() if v else False,
                }
            )
        return {"sheets": out}

    return _on_main(fn)


def _get_sheet_content(params):
    index = int(params.get("index", [0])[0])

    def fn():
        w = sublime.active_window()
        sheets = w.sheets()
        if index >= len(sheets):
            return {"error": f"index {index} out of range (have {len(sheets)} sheets)"}
        s = sheets[index]
        kind = type(s).__name__
        path = None
        try:
            path = s.file_name()
        except Exception:
            pass
        if kind == "ImageSheet":
            return {
                "index": index,
                "type": kind,
                "path": path,
                "content": None,
                "note": "image — use path to read the file directly",
            }
        v = s.view()
        if not v:
            return {"error": f"sheet {index} has no text view"}
        return {
            "index": index,
            "type": kind,
            "path": path,
            "name": v.name(),
            "content": v.substr(sublime.Region(0, v.size())),
        }

    return _on_main(fn)


def _get_project_folders(params):
    def fn():
        return {"folders": sublime.active_window().folders()}

    return _on_main(fn)


def _get_file_content(params):
    path = params.get("path", [None])[0]
    if not path:
        return {"error": "path required"}

    def fn():
        v = sublime.active_window().find_open_file(path)
        if not v:
            return {"error": f"not open: {path}"}
        return {"path": path, "content": v.substr(sublime.Region(0, v.size()))}

    return _on_main(fn)


def _resolve_view(w, name, index):
    views = w.views()
    if name:
        match = next((v for v in views if name.lower() in v.name().lower()), None)
        if not match:
            names = [v.name() for v in views]
            return None, {"error": f"no view matching {name!r}", "open_views": names}
        return match, None
    if index >= 0:
        if index >= len(views):
            return None, {
                "error": f"index {index} out of range (have {len(views)} views)"
            }
        return views[index], None
    return w.active_view(), None


def _get_view_content(params):
    name = params.get("name", [None])[0] or ""
    index = int(params.get("index", [-1])[0])

    def fn():
        w = sublime.active_window()
        v, err = _resolve_view(w, name, index)
        if err:
            return err
        if not v:
            return {"error": "no view found"}
        return {
            "name": v.name(),
            "path": v.file_name(),
            "content": v.substr(sublime.Region(0, v.size())),
        }

    return _on_main(fn)


def _send_to_view(body):
    name = body.get("name", "")
    index = int(body.get("index", -1))
    text = body.get("text", "")
    if not text:
        return {"error": "text required"}

    def fn():
        w = sublime.active_window()
        v, err = _resolve_view(w, name, index)
        if err:
            return err
        if not v:
            return {"error": "no view found"}
        import sys

        Terminal = sys.modules.get("Terminus.terminus.terminal", None)
        Terminal = Terminal.Terminal if Terminal else None
        if Terminal and Terminal.from_id(v.id()):
            v.run_command("terminus_paste_text", {"text": text, "bracketed": False})
        else:
            w.focus_view(v)
            w.run_command("terminus_send_string", {"string": text})
        tag = v.settings().get("terminus_view.tag")
        return {"ok": True, "name": v.name(), "tag": tag}

    return _on_main(fn)


def _get_output_panel(params):
    name = params.get("name", [""])[0]

    def fn():
        w = sublime.active_window()
        panel_name = name
        if panel_name:
            v = w.find_output_panel(panel_name)
        else:
            panel_name, v = _active_output_panel_view(w)
            if not panel_name:
                return {"error": "no active output panel"}
        if not v:
            return {"error": f"panel not found: {panel_name}"}
        return {"name": panel_name, "content": v.substr(sublime.Region(0, v.size()))}

    return _on_main(fn)


def _get_console_log(params):
    _install_console_capture()
    tail = int(params.get("tail", ["200"])[0])
    entries = _console_buf[-tail:] if tail > 0 else list(_console_buf)
    return {"entries": entries, "total": len(_console_buf)}


def _get_console_full(params):
    """Return the entire captured ST console buffer (no tail limit)."""
    _install_console_capture()
    return {"entries": list(_console_buf), "total": len(_console_buf)}


def _get_symbols(params):
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        out = []
        for region, name in v.symbols():
            row, col = v.rowcol(region.begin())
            out.append({"name": name, "line": row + 1, "col": col + 1})
        return {"path": v.file_name(), "symbols": out}

    return _on_main(fn)


def _lookup_symbol(params):
    sym = params.get("symbol", [None])[0]
    if not sym:
        return {"error": "symbol required"}

    def fn():
        locs = sublime.active_window().lookup_symbol_in_open_files(sym)
        return {
            "locations": [
                {
                    "path": l.path,
                    "name": l.display_name,
                    "line": l.row + 1,
                    "col": l.col + 1,
                }
                for l in locs
            ]
        }

    return _on_main(fn)


def _get_project_data(params):
    def fn():
        return {"project_data": sublime.active_window().project_data()}

    return _on_main(fn)


def _get_variables(params):
    def fn():
        return sublime.active_window().extract_variables()

    return _on_main(fn)


def _get_bookmarks(params):
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        out = []
        for r in v.get_regions("bookmarks"):
            row, col = v.rowcol(r.begin())
            out.append({"line": row + 1, "col": col + 1})
        return {"path": v.file_name(), "bookmarks": out}

    return _on_main(fn)


def _get_line_count(params):
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        return {"path": v.file_name(), "line_count": v.rowcol(v.size())[0] + 1}

    return _on_main(fn)


def _get_syntaxes(params):
    def fn():
        return {
            "syntaxes": [
                {"name": s.name, "path": s.path} for s in sublime.list_syntaxes()
            ]
        }

    return _on_main(fn)


def _get_command_palette(params):
    package_filter = params.get("package", [""])[0].strip().lower()
    command_filter = params.get("command", [""])[0].strip().lower()
    caption_filter = params.get("caption", [""])[0].strip().lower()

    def fn():
        entries = []
        for resource in sorted(sublime.find_resources("*.sublime-commands")):
            package = _package_name_from_resource(resource) or ""
            if package_filter and package_filter not in package.lower():
                continue
            try:
                data = sublime.decode_value(sublime.load_resource(resource))
            except Exception as e:
                entries.append(
                    {
                        "resource": resource,
                        "package": package,
                        "error": str(e),
                    }
                )
                continue
            if not isinstance(data, list):
                continue
            for item in data:
                if not isinstance(item, dict):
                    continue
                command = item.get("command", "")
                caption = item.get("caption", "")
                if command_filter and command_filter not in command.lower():
                    continue
                if caption_filter and caption_filter not in caption.lower():
                    continue
                entries.append(
                    {
                        "caption": caption,
                        "command": command,
                        "args": item.get("args", {}),
                        "resource": resource,
                        "package": package,
                    }
                )
        return {"entries": entries, "count": len(entries)}

    return _on_main(fn)


def _get_commands(params):
    package_filter = params.get("package", [""])[0].strip().lower()
    command_filter = params.get("command", [""])[0].strip().lower()
    include_palette = (
        params.get("include_palette", ["true"])[0].strip().lower() != "false"
    )

    def fn():
        commands = {}
        for scope, classes in (
            ("application", getattr(sublime_plugin, "application_command_classes", [])),
            ("window", getattr(sublime_plugin, "window_command_classes", [])),
            ("text", getattr(sublime_plugin, "text_command_classes", [])),
        ):
            for cls in classes:
                command = _command_name_from_class(cls)
                module = getattr(cls, "__module__", "")
                package = module.split(".", 1)[0] if module else ""
                if package_filter and package_filter not in package.lower():
                    continue
                if command_filter and command_filter not in command.lower():
                    continue
                entry = commands.setdefault(
                    command,
                    {
                        "command": command,
                        "scopes": [],
                        "class_names": [],
                        "modules": [],
                        "packages": [],
                        "palette_entries": [],
                    },
                )
                if scope not in entry["scopes"]:
                    entry["scopes"].append(scope)
                if cls.__name__ not in entry["class_names"]:
                    entry["class_names"].append(cls.__name__)
                if module and module not in entry["modules"]:
                    entry["modules"].append(module)
                if package and package not in entry["packages"]:
                    entry["packages"].append(package)
        if include_palette:
            for resource in sorted(sublime.find_resources("*.sublime-commands")):
                package = _package_name_from_resource(resource) or ""
                if package_filter and package_filter not in package.lower():
                    continue
                try:
                    data = sublime.decode_value(sublime.load_resource(resource))
                except Exception:
                    continue
                if not isinstance(data, list):
                    continue
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    command = item.get("command", "")
                    caption = item.get("caption", "")
                    if not command:
                        continue
                    if command_filter and command_filter not in command.lower():
                        continue
                    entry = commands.setdefault(
                        command,
                        {
                            "command": command,
                            "scopes": [],
                            "class_names": [],
                            "modules": [],
                            "packages": [],
                            "palette_entries": [],
                        },
                    )
                    if package and package not in entry["packages"]:
                        entry["packages"].append(package)
                    entry["palette_entries"].append(
                        {
                            "caption": caption,
                            "args": item.get("args", {}),
                            "resource": resource,
                            "package": package,
                        }
                    )
        return {
            "commands": [commands[name] for name in sorted(commands)],
            "count": len(commands),
        }

    return _on_main(fn)


def _get_menu_items(params):
    menu_filter = params.get("menu", [""])[0].strip().lower()
    caption_filter = params.get("caption", [""])[0].strip().lower()
    command_filter = params.get("command", [""])[0].strip().lower()

    def fn():
        entries = []
        resources = sorted(sublime.find_resources("*.sublime-menu"))
        for resource in resources:
            filename = resource.rsplit("/", 1)[-1].lower()
            if menu_filter and menu_filter not in filename:
                continue
            try:
                data = sublime.decode_value(sublime.load_resource(resource))
            except Exception as e:
                entries.append({"resource": resource, "error": str(e)})
                continue
            if isinstance(data, list):
                _walk_menu_items(
                    data, resource, [], caption_filter, command_filter, entries
                )
        return {"entries": entries, "count": len(entries)}

    return _on_main(fn)


def _get_active_panel(params):
    def fn():
        w = sublime.active_window()
        panel_name = w.active_panel()
        out = {"active_panel": panel_name}
        if panel_name and panel_name.startswith("output."):
            short_name, v = _active_output_panel_view(w)
            out["name"] = short_name
            out["content"] = v.substr(sublime.Region(0, v.size())) if v else None
        else:
            out["name"] = None
            out["content"] = None
        return out

    return _on_main(fn)


def _get_scope_at_cursor(params):
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        sel = v.sel()
        pt = sel[0].begin() if sel else 0
        return {"scope": v.scope_name(pt).strip()}

    return _on_main(fn)


def _get_encoding(params):
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        return {"path": v.file_name(), "encoding": v.encoding()}

    return _on_main(fn)


def _get_word_at_cursor(params):
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        sel = v.sel()
        pt = sel[0].begin() if sel else 0
        word_region = v.word(pt)
        row, col = v.rowcol(pt)
        return {
            "word": v.substr(word_region),
            "line": row + 1,
            "col": col + 1,
        }

    return _on_main(fn)


def _get_layout(params):
    def fn():
        w = sublime.active_window()
        layout = w.layout()
        views_by_group = {}
        for g in range(w.num_groups()):
            views_by_group[g] = [
                {"path": v.file_name(), "name": v.name()} for v in w.views_in_group(g)
            ]
        return {
            "layout": layout,
            "num_groups": w.num_groups(),
            "views_by_group": views_by_group,
        }

    return _on_main(fn)


def _get_view_size(params):
    name = params.get("name", [None])[0]

    def fn():
        w = sublime.active_window()
        views = w.views()
        if name:
            match = next((v for v in views if name.lower() in v.name().lower()), None)
            if not match:
                return {
                    "error": f"no view matching {name!r}",
                    "open_views": [v.name() for v in views],
                }
            v = match
        else:
            v = w.active_view()
        if not v:
            return {"error": "no view found"}
        return {"name": v.name(), "path": v.file_name(), "size": v.size()}

    return _on_main(fn)


def _get_view_chars(params):
    name = params.get("name", [None])[0]
    begin = int(params.get("begin", [0])[0])
    end_p = params.get("end", [None])[0]

    def fn():
        w = sublime.active_window()
        views = w.views()
        if name:
            match = next((v for v in views if name.lower() in v.name().lower()), None)
            if not match:
                return {
                    "error": f"no view matching {name!r}",
                    "open_views": [v.name() for v in views],
                }
            v = match
        else:
            v = w.active_view()
        if not v:
            return {"error": "no view found"}
        size = v.size()
        end_c = int(end_p) if end_p is not None else size
        begin_c = max(0, begin)
        end_c = min(size, end_c)
        return {
            "name": v.name(),
            "path": v.file_name(),
            "size": size,
            "begin": begin_c,
            "end": end_c,
            "content": v.substr(sublime.Region(begin_c, end_c)),
        }

    return _on_main(fn)


def _get_view_phantoms(params):
    """Return all phantoms attached to a view, with HTML stripped to plain text.

    ST doesn't expose a public API to enumerate phantom sets; instead we walk
    sys.modules looking for any loaded plugin module that has a _phantom_sets
    attribute (a dict mapping view ID -> PhantomSet).  The optional 'key' param
    filters by the PhantomSet's key string.

    Each phantom entry includes both the raw HTML 'content' and a 'text' field
    with tags stripped, for easier reading.
    """
    name = params.get("name", [None])[0]
    key = params.get("key", [""])[0].strip()

    def fn():
        w = sublime.active_window()
        v, open_views = _find_view_by_name(w, name)
        if not v:
            return {"error": f"no view matching {name!r}", "open_views": open_views}
        phantoms = []
        for mod in list(sys.modules.values()):
            ps_map = getattr(mod, "_phantom_sets", None)
            if not isinstance(ps_map, dict):
                continue
            phantom_set = ps_map.get(v.id())
            if not phantom_set:
                continue
            phantom_key = getattr(phantom_set, "key", "")
            if key and phantom_key != key:
                continue
            for item in getattr(phantom_set, "phantoms", []):
                region = getattr(item, "region", sublime.Region(-1, -1))
                content = getattr(item, "content", "")
                layout = getattr(item, "layout", None)
                layout_name = (
                    getattr(layout, "name", None) if layout is not None else None
                )
                phantoms.append(
                    {
                        "module": getattr(mod, "__name__", None),
                        "key": phantom_key,
                        "region": [region.a, region.b],
                        "layout": layout_name or str(layout),
                        "content": content,
                        "text": _clean_phantom_text(content),
                    }
                )
        return {
            "name": v.name(),
            "path": v.file_name(),
            "phantoms": phantoms,
            "count": len(phantoms),
        }

    return _on_main(fn)


# ── POST handlers ─────────────────────────────────────────────────────────────


def _set_project_data(body):
    data = body.get("data")
    if data is None:
        return {"error": "data required"}

    def fn():
        sublime.active_window().set_project_data(data)
        return {"ok": True}

    return _on_main(fn)


def _open_file(body):
    path = body.get("path")
    if not path:
        return {"error": "path required"}
    line = body.get("line", 0)
    col = body.get("col", 0)

    def fn():
        w = sublime.active_window()
        flags = sublime.ENCODED_POSITION if (line or col) else sublime.NewFileFlags.NONE
        fname = f"{path}:{line}:{col}" if (line or col) else path
        w.open_file(fname, flags)
        return {"ok": True}

    return _on_main(fn)


def _goto_line(body):
    line = body.get("line")
    col = body.get("col", 1)
    if line is None:
        return {"error": "line required"}

    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        pt = v.text_point(line - 1, col - 1)
        v.sel().clear()
        v.sel().add(sublime.Region(pt))
        v.show_at_center(pt)
        return {"ok": True}

    return _on_main(fn)


def _show_panel(body):
    name = body.get("name", "exec")

    def fn():
        sublime.active_window().run_command("show_panel", {"panel": f"output.{name}"})
        return {"ok": True}

    return _on_main(fn)


def _replace_selection(body):
    text = body.get("text", "")

    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        v.run_command("insert", {"characters": text})
        return {"ok": True}

    return _on_main(fn)


def _replace_lines(body):
    begin = body.get("begin")
    end = body.get("end")
    text = body.get("text", "")
    path = body.get("path")
    index = int(body.get("index", -1))
    if begin is None or end is None:
        return {"error": "begin and end required"}

    def fn():
        w = sublime.active_window()
        if path:
            v = w.find_open_file(path)
            if not v:
                return {"error": f"not open: {path}"}
        elif index >= 0:
            v, err = _resolve_view(w, "", index)
            if err:
                return err
        else:
            v = _active_view()
        if not v:
            return {"error": "no active view"}
        start_pt = v.text_point(begin - 1, 0)
        end_pt = v.full_line(v.text_point(end - 1, 0)).end()
        v.run_command(
            "mcp_replace_region",
            {
                "begin": start_pt,
                "end": end_pt,
                "text": text,
            },
        )
        return {"ok": True}

    return _on_main(fn)


def _run_command(body):
    cmd = body.get("command")
    args = body.get("args") or {}
    scope = body.get("scope", "window")
    if not cmd:
        return {"error": "command required"}

    def fn():
        w = sublime.active_window()
        if scope == "view":
            v = w.active_view()
            if v:
                v.run_command(cmd, args)
        else:
            w.run_command(cmd, args)
        return {"ok": True}

    return _on_main(fn)


def _run_build(body):
    def fn():
        sublime.active_window().run_command("exec", body or {})
        return {"ok": True}

    return _on_main(fn)


def _set_status(body):
    key = body.get("key", "sublime_mcp")
    value = body.get("value", "")

    def fn():
        v = _active_view()
        if v:
            v.set_status(key, value)
        return {"ok": True}

    return _on_main(fn)


def _save_file(body):
    path = body.get("path")

    def fn():
        w = sublime.active_window()
        if path:
            v = w.find_open_file(path)
            if not v:
                return {"error": f"not open: {path}"}
        else:
            v = _active_view()
        if not v:
            return {"error": "no active view"}
        v.run_command("save")
        return {"ok": True}

    return _on_main(fn)


def _save_all(body):
    def fn():
        sublime.active_window().run_command("save_all")
        return {"ok": True}

    return _on_main(fn)


def _close_file(body):
    path = body.get("path")

    def fn():
        w = sublime.active_window()
        if path:
            v = w.find_open_file(path)
            if not v:
                return {"error": f"not open: {path}"}
        else:
            v = w.active_view()
        if not v:
            return {"error": "no active view"}
        v.close()
        return {"ok": True}

    return _on_main(fn)


def _find_in_files(body):
    """Search files in project folders for a pattern and return match locations.

    Runs entirely on the HTTP thread — no ST API needed for raw file I/O, so
    we don't need _on_main().  Skips common build/cache dirs (.git, node_modules,
    etc.) and binary-large files (> max_file_bytes, default 1 MB).  Returns
    early with truncated=True if max_results or max_files limits are hit.

    Body params:
      pattern          search string or regex
      folders          list of absolute paths (defaults to project folders)
      case_sensitive   bool (default False)
      regex            bool — treat pattern as regex (default False = literal)
      max_results      int (default 200)
      max_files        int (default 500)
      max_file_bytes   int (default 1048576)
    """
    pattern = body.get("pattern", "")
    folders = body.get("folders") or []
    case = body.get("case_sensitive", False)
    use_re = body.get("regex", False)
    max_hits = int(body.get("max_results", 200))
    max_files = int(body.get("max_files", 500))
    max_file_bytes = int(body.get("max_file_bytes", 1048576))  # 1 MB
    if not pattern:
        return {"error": "pattern required"}
    if not folders:
        folders = _on_main(lambda: sublime.active_window().folders())
    SKIP = {".git", "__pycache__", "node_modules", ".venv", ".mypy_cache"}
    flags = 0 if case else re.IGNORECASE
    try:
        rx = re.compile(pattern if use_re else re.escape(pattern), flags)
    except re.error as e:
        return {"error": f"bad pattern: {e}"}
    results = []
    files_scanned = 0
    files_skipped_size = 0
    for folder in folders:
        for dirpath, dirnames, filenames in os.walk(folder):
            dirnames[:] = [d for d in dirnames if d not in SKIP]
            for fname in filenames:
                if files_scanned >= max_files:
                    return {
                        "error": f"file limit reached: {max_files} files scanned across {folders}. "
                        f"Narrow folders or increase max_files.",
                        "results": results,
                        "files_scanned": files_scanned,
                        "files_skipped_size": files_skipped_size,
                        "truncated": True,
                    }
                fpath = os.path.join(dirpath, fname)
                try:
                    if os.path.getsize(fpath) > max_file_bytes:
                        files_skipped_size += 1
                        continue
                    text = open(fpath, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                files_scanned += 1
                for m in rx.finditer(text):
                    line_no = text[: m.start()].count("\n") + 1
                    results.append({"path": fpath, "line": line_no, "match": m.group()})
                    if len(results) >= max_hits:
                        return {
                            "results": results,
                            "files_scanned": files_scanned,
                            "files_skipped_size": files_skipped_size,
                            "truncated": True,
                        }
    return {
        "results": results,
        "files_scanned": files_scanned,
        "files_skipped_size": files_skipped_size,
        "truncated": False,
    }


def _find_in_file(body):
    pattern = body.get("pattern", "")
    case = body.get("case_sensitive", False)
    use_re = body.get("regex", False)
    if not pattern:
        return {"error": "pattern required"}

    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        flags = 0
        if not case:
            flags |= sublime.IGNORECASE
        if not use_re:
            flags |= sublime.LITERAL
        out = []
        for r in v.find_all(pattern, flags):
            row, col = v.rowcol(r.begin())
            out.append({"line": row + 1, "col": col + 1, "text": v.substr(r)})
        return {"path": v.file_name(), "matches": out}

    return _on_main(fn)


def _set_syntax(body):
    name = body.get("name", "")
    if not name:
        return {"error": "name required"}

    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        syns = sublime.list_syntaxes()
        match = next((s for s in syns if s.name.lower() == name.lower()), None)
        if not match:
            match = next((s for s in syns if name.lower() in s.name.lower()), None)
        if not match:
            return {"error": f"syntax not found: {name}"}
        v.assign_syntax(match.path)
        return {"ok": True, "syntax": match.name}

    return _on_main(fn)


def _toggle_comment(body):
    block = bool(body.get("block", False))

    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        v.run_command("toggle_comment", {"block": block})
        return {"ok": True}

    return _on_main(fn)


def _toggle_sidebar(body):
    def fn():
        sublime.active_window().run_command("toggle_side_bar")
        return {"ok": True}

    return _on_main(fn)


def _select_lines(body):
    begin = body.get("begin")
    end = body.get("end")
    if begin is None:
        return {"error": "begin required"}
    if end is None:
        end = begin

    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        start_pt = v.text_point(begin - 1, 0)
        end_pt = v.full_line(v.text_point(end - 1, 0)).end()
        v.sel().clear()
        v.sel().add(sublime.Region(start_pt, end_pt))
        v.show_at_center(start_pt)
        return {"ok": True}

    return _on_main(fn)


def _sort_lines(body):
    case = bool(body.get("case_sensitive", False))

    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        v.run_command("sort_lines", {"case_sensitive": case})
        return {"ok": True}

    return _on_main(fn)


def _eval_python(body):
    code = body.get("code", "")
    if not code:
        return {"error": "code required"}
    buf = io.StringIO()

    def fn():
        env = {
            "sublime": sublime,
            "window": sublime.active_window(),
            "view": sublime.active_window().active_view(),
            "print": lambda *a, **kw: print(*a, **kw, file=buf),
        }
        exec(code, env)  # noqa: S102
        return buf.getvalue()

    try:
        output = _on_main(fn)
        return {"ok": True, "output": output}
    except Exception as e:
        return {"ok": False, "error": str(e), "output": buf.getvalue()}


def _eval_python_latest(body):
    """Run code via the system Python interpreter (python) outside ST's embedded sandbox."""
    import os
    import subprocess
    import tempfile
    import shutil

    code = body.get("code", "")
    if not code:
        return {"error": "code required"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        fname = f.name
    try:
        _python = shutil.which("python3") or shutil.which("python") or "python"
        r = subprocess.run([_python, fname], capture_output=True, text=True, timeout=30)
        return {"ok": True, "stdout": r.stdout, "stderr": r.stderr, "returncode": r.returncode}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout after 30s"}
    except FileNotFoundError:
        return {"ok": False, "error": "python not found on PATH"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        os.unlink(fname)


def _fold_lines(body):
    begin = body.get("begin")
    end = body.get("end")
    if begin is None or end is None:
        return {"error": "begin and end required"}

    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        start_pt = v.text_point(begin - 1, 0)
        end_pt = v.full_line(v.text_point(end - 1, 0)).end()
        v.fold(sublime.Region(start_pt, end_pt))
        return {"ok": True}

    return _on_main(fn)


def _set_encoding(body):
    encoding = body.get("encoding", "")
    if not encoding:
        return {"error": "encoding required"}

    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        v.set_encoding(encoding)
        return {"ok": True}

    return _on_main(fn)


def _revert_file(body):
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        v.run_command("revert")
        return {"ok": True}

    return _on_main(fn)


def _undo(body):
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        v.run_command("undo")
        return {"ok": True}

    return _on_main(fn)


def _redo(body):
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        v.run_command("redo")
        return {"ok": True}

    return _on_main(fn)


def _duplicate_line(body):
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        v.run_command("duplicate_line")
        return {"ok": True}

    return _on_main(fn)


def _insert_snippet(body):
    contents = body.get("contents", "")
    if not contents:
        return {"error": "contents required"}

    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        v.run_command("insert_snippet", {"contents": contents})
        return {"ok": True}

    return _on_main(fn)


def _get_setting(body):
    key = body.get("key", "")
    if not key:
        return {"error": "key required"}
    scope = body.get("scope", "view")

    def fn():
        w = sublime.active_window()
        if scope == "view":
            v = w.active_view()
            if not v:
                return {"error": "no active view"}
            return {"key": key, "value": v.settings().get(key), "scope": "view"}
        else:
            return {"key": key, "value": w.settings().get(key), "scope": "window"}

    return _on_main(fn)


def _set_setting(body):
    key = body.get("key", "")
    value = body.get("value")
    scope = body.get("scope", "view")
    if not key:
        return {"error": "key required"}
    if value is None:
        return {"error": "value required"}

    def fn():
        w = sublime.active_window()
        if scope == "view":
            v = w.active_view()
            if not v:
                return {"error": "no active view"}
            v.settings().set(key, value)
        else:
            w.settings().set(key, value)
        return {"ok": True}

    return _on_main(fn)


def _focus_group(body):
    group = body.get("group")
    if group is None:
        return {"error": "group required"}

    def fn():
        w = sublime.active_window()
        if group >= w.num_groups():
            return {"error": f"group {group} out of range (have {w.num_groups()})"}
        w.focus_group(group)
        return {"ok": True}

    return _on_main(fn)


def _set_layout(body):
    layout = body.get("layout")
    if not layout:
        return {"error": "layout required"}

    def fn():
        sublime.active_window().run_command("set_layout", layout)
        return {"ok": True}

    return _on_main(fn)


# ── str_replace_based_edit ────────────────────────────────────────────────────

_EDIT_HIGHLIGHT_MS = 30000  # how long green underline stays visible


def _ensure_view(path):
    """Open *path* in ST if not already open, then wait for the async load to complete.

    ST's window.open_file() returns immediately with a loading view; the file
    content is not available until view.is_loading() returns False.  We poll
    from the HTTP thread (50 × 100 ms = 5 s max) so the ST main thread stays
    free to process the load callback.  Each _on_main call is brief.

    Returns (view, None) on success or (None, {"error": ...}) on failure.
    """
    import time

    def _open():
        w = sublime.active_window()
        v = w.find_open_file(path)
        if v:
            return v, None
        if not os.path.isfile(path):
            return None, {"error": f"file not found: {path}"}
        return w.open_file(path), None

    v, err = _on_main(_open)
    if err:
        return None, err

    # Poll until loaded (each _on_main is brief; main thread free between sleeps)
    for _ in range(50):
        if not _on_main(lambda: v.is_loading()):
            return v, None
        time.sleep(0.1)

    return None, {"error": f"timeout waiting for file to load: {path}"}


def _edit_file(body):
    command = body.get("command", "").strip()
    path = body.get("path", "").strip()

    if command == "create":
        file_text = body.get("file_text", "")
        if not path:
            return {"error": "path required"}

        def create_fn():
            w = sublime.active_window()
            if os.path.exists(path):
                return {"error": f"file already exists: {path}"}
            v = w.new_file()
            v.retarget(path)
            syn = sublime.find_syntax_for_file(path)
            if syn:
                v.assign_syntax(syn)
            v.run_command("mcp_create_file", {"file_text": file_text})
            return {"ok": True, "path": path}

        return _on_main(create_fn)

    # view / str_replace / insert all need an open view
    if not path:
        return {"error": "path required"}

    v, err = _ensure_view(path)
    if err:
        return err

    if command == "view":
        view_range = body.get("view_range")

        def view_fn():
            content = v.substr(sublime.Region(0, v.size()))
            lines = content.split("\n")
            total = len(lines)
            if view_range and len(view_range) >= 2:
                start = max(1, int(view_range[0]))
                end = min(total, int(view_range[1]) if view_range[1] != -1 else total)
                if start > end:
                    return {"error": "invalid view_range"}
                slice_lines = lines[start - 1 : end]
                numbered = "\n".join(
                    f"{start + i}: {l}" for i, l in enumerate(slice_lines)
                )
                return {
                    "content": numbered,
                    "total_lines": total,
                    "start_line": start,
                    "end_line": end,
                }
            else:
                numbered = "\n".join(f"{i + 1}: {l}" for i, l in enumerate(lines))
                return {"content": numbered, "total_lines": total}

        return _on_main(view_fn)

    if command == "str_replace":
        old_str = body.get("old_str", "")
        new_str = body.get("new_str", "")
        if not old_str:
            return {"error": "old_str required"}
        # Normalize line endings to match ST's internal \n representation
        old_str = old_str.replace("\r\n", "\n").replace("\r", "\n")
        new_str = new_str.replace("\r\n", "\n").replace("\r", "\n")

        def str_replace_fn():
            regions = v.find_all(old_str, sublime.LITERAL)
            if len(regions) == 0:
                return {
                    "error": "No match found for old_str. Check whitespace and indentation."
                }
            if len(regions) > 1:
                lns = [v.rowcol(r.begin())[0] + 1 for r in regions]
                return {
                    "error": f"Found {len(regions)} matches at lines {lns}. "
                    f"Add more surrounding context to old_str to make it unique."
                }
            region = regions[0]
            row, _ = v.rowcol(region.begin())
            # Save current state as reference so gutter shows the diff
            original = v.substr(sublime.Region(0, v.size()))
            v.set_reference_document(original)
            v.run_command(
                "mcp_str_replace",
                {
                    "begin": region.begin(),
                    "end": region.end(),
                    "new_str": new_str,
                },
            )
            return {"ok": True, "line": row + 1}

        return _on_main(str_replace_fn)

    if command == "insert":
        insert_line = body.get("insert_line")
        insert_text = body.get("insert_text", "")
        if insert_line is None:
            return {"error": "insert_line required"}
        insert_line = int(insert_line)

        def insert_fn():
            total_lines = v.rowcol(v.size())[0] + 1
            if insert_line == 0:
                pt = 0
            else:
                clamped = min(insert_line, total_lines)
                line_region = v.full_line(v.text_point(clamped - 1, 0))
                pt = line_region.end()
            # Normalize line endings
            text = insert_text.replace("\r\n", "\n").replace("\r", "\n")
            if not text.endswith("\n"):
                text += "\n"
            original = v.substr(sublime.Region(0, v.size()))
            v.set_reference_document(original)
            v.run_command(
                "mcp_insert_text",
                {
                    "insert_pt": pt,
                    "insert_text": text,
                },
            )
            row, _ = v.rowcol(pt)
            return {
                "ok": True,
                "after_line": insert_line,
                "inserted_at_pt": pt,
                "visible_line": row + 1,
            }

        return _on_main(insert_fn)

    return {
        "error": f"unknown command: {command!r}. Use: str_replace, insert, create, view"
    }


# ── routing ───────────────────────────────────────────────────────────────────

_GET = {
    "/active_file": _get_active_file,
    "/selection": _get_selection,
    "/cursor_context": _get_cursor_context,
    "/open_files": _get_open_files,
    "/sheets": _get_sheets,
    "/sheet_content": _get_sheet_content,
    "/project_folders": _get_project_folders,
    "/file_content": _get_file_content,
    "/view_content": _get_view_content,
    "/view_size": _get_view_size,
    "/view_chars": _get_view_chars,
    "/view_phantoms": _get_view_phantoms,
    "/output_panel": _get_output_panel,
    "/console_log": _get_console_log,
    "/console_full": _get_console_full,
    "/symbols": _get_symbols,
    "/lookup_symbol": _lookup_symbol,
    "/project_data": _get_project_data,
    "/variables": _get_variables,
    "/bookmarks": _get_bookmarks,
    "/line_count": _get_line_count,
    "/syntaxes": _get_syntaxes,
    "/command_palette": _get_command_palette,
    "/commands": _get_commands,
    "/menu_items": _get_menu_items,
    "/active_panel": _get_active_panel,
    "/scope_at_cursor": _get_scope_at_cursor,
    "/encoding": _get_encoding,
    "/word_at_cursor": _get_word_at_cursor,
    "/layout": _get_layout,
}

_POST = {
    "/set_project_data": _set_project_data,
    "/open_file": _open_file,
    "/goto_line": _goto_line,
    "/show_panel": _show_panel,
    "/replace_selection": _replace_selection,
    "/replace_lines": _replace_lines,
    "/run_command": _run_command,
    "/run_build": _run_build,
    "/set_status": _set_status,
    "/save_file": _save_file,
    "/save_all": _save_all,
    "/close_file": _close_file,
    "/find_in_files": _find_in_files,
    "/find_in_file": _find_in_file,
    "/set_syntax": _set_syntax,
    "/toggle_comment": _toggle_comment,
    "/toggle_sidebar": _toggle_sidebar,
    "/select_lines": _select_lines,
    "/sort_lines": _sort_lines,
    "/eval_python": _eval_python,
    "/eval_python_latest": _eval_python_latest,
    "/fold_lines": _fold_lines,
    "/set_encoding": _set_encoding,
    "/revert_file": _revert_file,
    "/undo": _undo,
    "/redo": _redo,
    "/duplicate_line": _duplicate_line,
    "/insert_snippet": _insert_snippet,
    "/get_setting": _get_setting,
    "/set_setting": _set_setting,
    "/focus_group": _focus_group,
    "/set_layout": _set_layout,
    "/send_to_view": _send_to_view,
    "/edit_file": _edit_file,
}


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress request log

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        handler = _GET.get(parsed.path)
        if handler:
            try:
                self._json(handler(params))
            except Exception as e:
                self._json({"error": str(e)}, 500)
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        handler = _POST.get(parsed.path)
        if handler:
            try:
                self._json(handler(body))
            except Exception as e:
                self._json({"error": str(e)}, 500)
        else:
            self._json({"error": "not found"}, 404)


# ── MCP SSE server (Python 3.8, no external dependencies) ────────────────────
#
# Implements the MCP 2024-11-05 SSE transport so agents can connect directly
# to Sublime Text without running index.js / npx.
#
# Claude Code config:
#   { "type": "sse", "url": "http://127.0.0.1:9502/sse" }   (Windows)
#   { "type": "sse", "url": "http://127.0.0.1:9503/sse" }   (Mac/Linux)
# or set SUBLIME_MCP_MCP_PORT to override.

import queue as _queue
import uuid as _uuid

_MCP_PORT = int(os.environ.get("SUBLIME_MCP_MCP_PORT", 9502 if sys.platform == "win32" else 9503))
_mcp_sessions = {}  # session_id -> queue.Queue


def _to_get_params(args):
    """Convert MCP args dict to parse_qs list-of-strings format for GET handlers."""
    return {k: [str(v)] for k, v in args.items() if v is not None}


def _mcp_add_folder(args):
    path = args.get("path")
    if not path:
        return {"error": "path required"}
    data = _get_project_data({}).get("project_data") or {}
    folders = data.get("folders") or []
    if any(f.get("path") == path for f in folders):
        return {"ok": True, "note": "already present"}
    folders.append({"path": path})
    data["folders"] = folders
    return _set_project_data({"data": data})


def _mcp_remove_folder(args):
    path = args.get("path")
    if not path:
        return {"error": "path required"}
    data = _get_project_data({}).get("project_data") or {}
    folders = data.get("folders") or []
    new_folders = [f for f in folders if f.get("path") != path]
    if len(new_folders) == len(folders):
        return {"ok": False, "note": "folder not found"}
    data["folders"] = new_folders
    return _set_project_data({"data": data})


def _g(endpoint):
    """Wrap a GET handler for use as an MCP tool handler."""
    def handler(args):
        return _GET[endpoint](_to_get_params(args))
    return handler


def _p(endpoint):
    """Wrap a POST handler for use as an MCP tool handler."""
    def handler(args):
        return _POST[endpoint](args)
    return handler


# (name, description, inputSchema, handler)
_MCP_TOOLS = [
    # ── no-parameter GET tools ────────────────────────────────────────────────
    ("get_active_file",
     "Return the active file's path, full content, cursor line/col, dirty flag, and syntax name.",
     {}, _g("/active_file")),
    ("get_selection",
     "Return the current selection(s): text and begin/end line+col for each.",
     {}, _g("/selection")),
    ("get_open_files",
     "List all files open in the current window (path, name, is_dirty).",
     {}, _g("/open_files")),
    ("get_sheets",
     "List ALL sheets (tabs) in the current window by index, including images and untitled buffers.\n"
     "Returns index, type (TextSheet/ImageSheet), path, name, is_dirty for each.\n"
     "Use index with get_sheet_content to read a specific tab.",
     {}, _g("/sheets")),
    ("get_project_folders", "Return the project's root folder paths.", {}, _g("/project_folders")),
    ("get_symbols", "Return all symbols (functions, classes, etc.) in the active file with line numbers.", {}, _g("/symbols")),
    ("get_project_data", "Return the raw .sublime-project JSON data for the current project.", {}, _g("/project_data")),
    ("get_variables", "Return Sublime Text's build variables: $file, $project_path, $platform, etc.", {}, _g("/variables")),
    ("get_active_panel", "Return the active panel id and, if it is an output panel, its content.", {}, _g("/active_panel")),
    ("get_syntaxes", "List all syntax definitions available in Sublime Text (name + path).", {}, _g("/syntaxes")),
    ("get_encoding", "Return the character encoding of the active file.", {}, _g("/encoding")),
    ("get_scope_at_cursor", "Return the full syntax scope string at the cursor position.", {}, _g("/scope_at_cursor")),
    ("get_word_at_cursor", "Return the word under the cursor and its line/col.", {}, _g("/word_at_cursor")),
    ("get_bookmarks", "Return all bookmarked positions in the active file.", {}, _g("/bookmarks")),
    ("get_line_count", "Return the total number of lines in the active file.", {}, _g("/line_count")),
    ("get_layout", "Return the current window layout (groups, cells) and which files are in each group.", {}, _g("/layout")),
    # ── no-parameter POST tools ───────────────────────────────────────────────
    ("save_all", "Save all open files.", {}, _p("/save_all")),
    ("revert_file", "Revert the active file to its last saved state, discarding unsaved changes.", {}, _p("/revert_file")),
    ("undo", "Undo the last edit in the active file.", {}, _p("/undo")),
    ("redo", "Redo the last undone edit in the active file.", {}, _p("/redo")),
    ("duplicate_line", "Duplicate the current line(s) in the active file.", {}, _p("/duplicate_line")),
    ("toggle_sidebar", "Show or hide the Sublime Text sidebar.", {}, _p("/toggle_sidebar")),
    # ── parameterized GET tools ───────────────────────────────────────────────
    ("get_cursor_context",
     "Return `lines` lines above and below the cursor with 1-based line numbers prepended.",
     {"type": "object", "properties": {"lines": {"type": "integer", "default": 10}}},
     _g("/cursor_context")),
    ("get_sheet_content",
     "Return the content of any tab by its sheet index (from get_sheets).\n"
     "Works for text tabs including untitled buffers and Terminus tabs.\n"
     "For image tabs returns the file path only.",
     {"type": "object", "properties": {"index": {"type": "integer"}}, "required": ["index"]},
     _g("/sheet_content")),
    ("get_file_content",
     "Return the full content of an already-open file by its path.",
     {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
     _g("/file_content")),
    ("get_view_content",
     "Return the full content of any open tab by name (partial match, case-insensitive).\n"
     "Works for Terminus tabs and other nameless views that have no file path.\n"
     "Use index (0-based, from get_open_files) to target a tab by position instead of name.\n"
     "Omit both to read the active view.",
     {"type": "object", "properties": {
         "name": {"type": "string", "default": ""},
         "index": {"type": "integer", "default": -1},
     }},
     _g("/view_content")),
    ("get_view_size",
     "Return the total character count of any open tab by name (partial match, case-insensitive).\n"
     "Use before get_view_chars to compute offsets. Omit name for the active view.",
     {"type": "object", "properties": {"name": {"type": "string", "default": ""}}},
     _g("/view_size")),
    ("get_view_chars",
     "Return text at character offsets begin..end (0-based, end exclusive) from any open tab.\n"
     "Clamps to buffer bounds automatically. Omit name for the active view.",
     {"type": "object", "properties": {
         "begin": {"type": "integer"},
         "end": {"type": "integer"},
         "name": {"type": "string", "default": ""},
     }, "required": ["begin", "end"]},
     _g("/view_chars")),
    ("get_view_phantoms",
     "Return phantom HTML and extracted text from a view by name.\n"
     "If key is omitted, returns phantoms for all keys.",
     {"type": "object", "properties": {
         "name": {"type": "string", "default": ""},
         "key": {"type": "string", "default": ""},
     }},
     _g("/view_phantoms")),
    ("get_output_panel",
     "Return the text content of an output panel.\n"
     "If name is omitted, read the active output panel. Use name='exec' for build output.",
     {"type": "object", "properties": {"name": {"type": "string", "default": ""}}},
     _g("/output_panel")),
    ("lookup_symbol",
     "Find where a symbol is defined across all open files.",
     {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]},
     _g("/lookup_symbol")),
    ("get_command_palette",
     "List Command Palette entries from installed *.sublime-commands resources.\n"
     "Optional filters: package, command id, or caption substring.",
     {"type": "object", "properties": {
         "package": {"type": "string", "default": ""},
         "command": {"type": "string", "default": ""},
         "caption": {"type": "string", "default": ""},
     }},
     _g("/command_palette")),
    ("get_commands",
     "List runnable Sublime command ids from loaded command classes, optionally enriched\n"
     "with matching Command Palette entries from installed packages.",
     {"type": "object", "properties": {
         "package": {"type": "string", "default": ""},
         "command": {"type": "string", "default": ""},
         "include_palette": {"type": "boolean", "default": True},
     }},
     _g("/commands")),
    ("get_menu_items",
     "List installed menu items from *.sublime-menu resources.\n"
     "Optional filters: menu filename, caption substring, or command id substring.",
     {"type": "object", "properties": {
         "menu": {"type": "string", "default": ""},
         "caption": {"type": "string", "default": ""},
         "command": {"type": "string", "default": ""},
     }},
     _g("/menu_items")),
    ("get_console_log",
     "Return recent Sublime Text console output (plugin log messages and stdout).\n"
     "tail=N limits to the last N entries. tail=0 returns all captured entries.",
     {"type": "object", "properties": {"tail": {"type": "integer", "default": 100}}},
     _g("/console_log")),
    ("get_console_full",
     "Return the entire captured ST console buffer with no tail limit.\n"
     "Includes startup messages, plugin load events, and all errors since ST started.",
     {},
     _g("/console_full")),
    # ── parameterized POST tools ──────────────────────────────────────────────
    ("add_folder",
     "Add a folder to the current project.",
     {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
     _mcp_add_folder),
    ("remove_folder",
     "Remove a folder from the current project by path.",
     {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
     _mcp_remove_folder),
    ("send_to_view",
     "Send a string to any open tab by name (partial match, case-insensitive).\n"
     "For Terminus tabs this types the text into the terminal as if the user typed it.\n"
     "Include a trailing newline (\\n) to execute a command.\n"
     "Use index (0-based, from get_open_files) to target a tab by position instead of name.\n"
     "Omit both name and index to target the active view.",
     {"type": "object", "properties": {
         "text": {"type": "string"},
         "name": {"type": "string", "default": ""},
         "index": {"type": "integer", "default": -1},
     }, "required": ["text"]},
     _p("/send_to_view")),
    ("open_file",
     "Open a file in Sublime Text, optionally jumping to a specific line and column.",
     {"type": "object", "properties": {
         "path": {"type": "string"},
         "line": {"type": "integer", "default": 0},
         "col": {"type": "integer", "default": 0},
     }, "required": ["path"]},
     _p("/open_file")),
    ("goto_line",
     "Move the cursor to a line (and optional column) in the active file.",
     {"type": "object", "properties": {
         "line": {"type": "integer"},
         "col": {"type": "integer", "default": 1},
     }, "required": ["line"]},
     _p("/goto_line")),
    ("show_panel",
     "Bring an output panel to the front. Use name='exec' for the build panel.",
     {"type": "object", "properties": {"name": {"type": "string", "default": "exec"}}},
     _p("/show_panel")),
    ("replace_selection",
     "Replace the current selection(s) with text.",
     {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
     _p("/replace_selection")),
    ("replace_lines",
     "Replace lines begin through end (inclusive, 1-based) in the active file with text.\n"
     "Pass path to target a specific open file regardless of which tab is focused.\n"
     "Use index (0-based, from get_open_files) to target a nameless tab by position.",
     {"type": "object", "properties": {
         "begin": {"type": "integer"},
         "end": {"type": "integer"},
         "text": {"type": "string"},
         "path": {"type": "string", "default": ""},
         "index": {"type": "integer", "default": -1},
     }, "required": ["begin", "end", "text"]},
     _p("/replace_lines")),
    ("run_command",
     "Run any Sublime Text command. scope='window' (default) or 'view'.",
     {"type": "object", "properties": {
         "command": {"type": "string"},
         "args": {"type": "object"},
         "scope": {"type": "string", "default": "window"},
     }, "required": ["command"]},
     _p("/run_command")),
    ("run_build",
     "Trigger the current build system, or pass cmd/shell_cmd to run a specific command.",
     {"type": "object", "properties": {
         "cmd": {"type": "array", "items": {"type": "string"}},
         "shell_cmd": {"type": "string"},
         "working_dir": {"type": "string", "default": ""},
     }},
     _p("/run_build")),
    ("set_status",
     "Write a message to Sublime Text's status bar.",
     {"type": "object", "properties": {
         "value": {"type": "string"},
         "key": {"type": "string", "default": "sublime_mcp"},
     }, "required": ["value"]},
     _p("/set_status")),
    ("save_file",
     "Save a file. Pass path to save a specific open file; omit path to save the active file.",
     {"type": "object", "properties": {"path": {"type": "string", "default": ""}}},
     _p("/save_file")),
    ("close_file",
     "Close a file by path, or close the active file if path is omitted.",
     {"type": "object", "properties": {"path": {"type": "string", "default": ""}}},
     _p("/close_file")),
    ("toggle_comment",
     "Toggle line comment (or block comment if block=true) on the current selection.",
     {"type": "object", "properties": {"block": {"type": "boolean", "default": False}}},
     _p("/toggle_comment")),
    ("sort_lines",
     "Sort the selected lines (or all lines if nothing is selected).",
     {"type": "object", "properties": {"case_sensitive": {"type": "boolean", "default": False}}},
     _p("/sort_lines")),
    ("select_lines",
     "Select lines begin through end (1-based, inclusive). end defaults to begin.",
     {"type": "object", "properties": {
         "begin": {"type": "integer"},
         "end": {"type": "integer", "default": 0},
     }, "required": ["begin"]},
     _p("/select_lines")),
    ("fold_lines",
     "Fold (collapse) lines begin through end (1-based) in the active file.",
     {"type": "object", "properties": {
         "begin": {"type": "integer"},
         "end": {"type": "integer"},
     }, "required": ["begin", "end"]},
     _p("/fold_lines")),
    ("insert_snippet",
     "Insert a snippet at the cursor using Sublime Text's snippet syntax (e.g. $1 for tab stops).",
     {"type": "object", "properties": {"contents": {"type": "string"}}, "required": ["contents"]},
     _p("/insert_snippet")),
    ("find_in_file",
     "Find all occurrences of pattern in the active file. Returns list of {line, col, text}.",
     {"type": "object", "properties": {
         "pattern": {"type": "string"},
         "case_sensitive": {"type": "boolean", "default": False},
         "regex": {"type": "boolean", "default": False},
     }, "required": ["pattern"]},
     _p("/find_in_file")),
    ("find_in_files",
     "Search for pattern across project folders (or the supplied folder list).\n"
     "Skips .git, __pycache__, node_modules, .venv. Returns list of {path, line, match}.",
     {"type": "object", "properties": {
         "pattern": {"type": "string"},
         "folders": {"type": "array", "items": {"type": "string"}},
         "case_sensitive": {"type": "boolean", "default": False},
         "regex": {"type": "boolean", "default": False},
         "max_results": {"type": "integer", "default": 200},
     }, "required": ["pattern"]},
     _p("/find_in_files")),
    ("set_syntax",
     "Set the syntax of the active file by name (case-insensitive partial match is fine).",
     {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
     _p("/set_syntax")),
    ("set_encoding",
     "Set the character encoding of the active file (e.g. 'UTF-8', 'Western (Windows 1252)').",
     {"type": "object", "properties": {"encoding": {"type": "string"}}, "required": ["encoding"]},
     _p("/set_encoding")),
    ("get_setting",
     "Get a Sublime Text setting by key. scope='view' (default) or 'window'.",
     {"type": "object", "properties": {
         "key": {"type": "string"},
         "scope": {"type": "string", "default": "view"},
     }, "required": ["key"]},
     _p("/get_setting")),
    ("set_setting",
     "Set a Sublime Text setting by key. scope='view' (default) or 'window'.",
     {"type": "object", "properties": {
         "key": {"type": "string"},
         "value": {},
         "scope": {"type": "string", "default": "view"},
     }, "required": ["key", "value"]},
     _p("/set_setting")),
    ("focus_group",
     "Move focus to a pane group by 0-based index.",
     {"type": "object", "properties": {"group": {"type": "integer"}}, "required": ["group"]},
     _p("/focus_group")),
    ("set_layout",
     "Set the window pane layout. layout must be a ST layout dict with cols, rows, cells keys.",
     {"type": "object", "properties": {"layout": {"type": "object"}}, "required": ["layout"]},
     _p("/set_layout")),
    ("eval_python",
     "Execute arbitrary Python in Sublime Text's main thread.\n"
     "Locals: sublime, window, view, print. Returns captured stdout in 'output'.",
     {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]},
     _p("/eval_python")),
    ("eval_python_latest",
     "Execute Python code using the system Python interpreter outside Sublime Text's embedded sandbox.\n"
     "Returns stdout, stderr, and returncode.",
     {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]},
     _p("/eval_python_latest")),
    ("str_replace_based_edit_tool",
     "ST-native file editor implementing the standard str_replace_based_edit_tool interface.\n"
     "Edits appear live in Sublime Text with full undo (Ctrl+Z), gutter diff markers,\n"
     "and 30-second highlight annotations showing what changed.\n\n"
     "command='str_replace': replace old_str with new_str in path.\n"
     "  old_str must match exactly once (whitespace-sensitive).\n"
     "  Returns error if 0 or 2+ matches, listing ambiguous line numbers.\n\n"
     "command='insert': insert insert_text after line insert_line (1-based).\n"
     "  insert_line=0 inserts at the very start of the file.\n\n"
     "command='create': create a new file at path with file_text content.\n"
     "  Syntax is auto-detected from the file extension. Errors if path exists.\n\n"
     "command='view': return file content with 1-based line numbers prepended.\n"
     "  Optional view_range=[start, end] to read a slice (end=-1 for EOF).\n\n"
     "All commands auto-open the file in ST if not already open.",
     {"type": "object", "properties": {
         "command": {"type": "string"},
         "path": {"type": "string", "default": ""},
         "old_str": {"type": "string"},
         "new_str": {"type": "string"},
         "insert_line": {"type": "integer"},
         "insert_text": {"type": "string"},
         "file_text": {"type": "string"},
         "view_range": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
     }, "required": ["command"]},
     _p("/edit_file")),
]


class _ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        import sys
        if isinstance(sys.exc_info()[1], (ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


class _MCPHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if urlparse(self.path).path == "/sse":
            self._handle_sse()
        else:
            self.send_error(404)

    def do_POST(self):
        if urlparse(self.path).path == "/messages":
            self._handle_message()
        else:
            self.send_error(404)

    def _handle_sse(self):
        session_id = str(_uuid.uuid4())
        q = _queue.Queue()
        _mcp_sessions[session_id] = q

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            endpoint = "/messages?sessionId=" + session_id
            self.wfile.write(("event: endpoint\ndata: " + endpoint + "\n\n").encode())
            self.wfile.flush()
            while True:
                try:
                    msg = q.get(timeout=30)
                except _queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    continue
                if msg is None:
                    break
                self.wfile.write(("data: " + json.dumps(msg) + "\n\n").encode())
                self.wfile.flush()
        except Exception:
            pass
        finally:
            _mcp_sessions.pop(session_id, None)

    def _handle_message(self):
        params = parse_qs(urlparse(self.path).query)
        session_id = params.get("sessionId", [None])[0]
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"{}")

        threading.Thread(target=_mcp_dispatch, args=(session_id, body), daemon=True).start()


def _mcp_send(session_id, msg):
    q = _mcp_sessions.get(session_id)
    if q:
        q.put(msg)


def _mcp_dispatch(session_id, msg):
    method = msg.get("method", "")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "sublime-mcp", "version": "1.3.0"},
            }
        elif method in ("notifications/initialized", "notifications/cancelled"):
            return
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            tools = []
            for name, desc, schema, _ in _MCP_TOOLS:
                input_schema = dict(schema) if schema else {}
                if "type" not in input_schema:
                    input_schema["type"] = "object"
                if "properties" not in input_schema:
                    input_schema["properties"] = {}
                tools.append({"name": name, "description": desc, "inputSchema": input_schema})
            result = {"tools": tools}
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}
            entry = next((t for t in _MCP_TOOLS if t[0] == tool_name), None)
            if entry is None:
                raise ValueError("Unknown tool: " + str(tool_name))
            data = entry[3](tool_args)
            result = {"content": [{"type": "text", "text": json.dumps(data)}]}
        else:
            raise ValueError("Unknown method: " + method)

        if msg_id is not None:
            _mcp_send(session_id, {"jsonrpc": "2.0", "id": msg_id, "result": result})
    except Exception as e:
        if msg_id is not None:
            _mcp_send(session_id, {"jsonrpc": "2.0", "id": msg_id,
                                   "error": {"code": -32603, "message": str(e)}})


# ── plugin lifecycle ──────────────────────────────────────────────────────────

_server = None
_mcp_server = None


def plugin_loaded():
    global _server, _mcp_server
    _install_console_capture()
    _server = HTTPServer(("127.0.0.1", _PORT), _Handler)
    t = threading.Thread(target=_server.serve_forever, daemon=True)
    t.start()
    _mcp_server = _ThreadingHTTPServer(("127.0.0.1", _MCP_PORT), _MCPHandler)
    t2 = threading.Thread(target=_mcp_server.serve_forever, daemon=True)
    t2.start()
    print(f"sublime-mcp: ST bridge on 127.0.0.1:{_PORT}, MCP SSE on 127.0.0.1:{_MCP_PORT}")


def plugin_unloaded():
    global _server, _mcp_server
    if _server:
        _server.shutdown()
        _server = None
    if _mcp_server:
        _mcp_server.shutdown()
        _mcp_server = None
    for q in list(_mcp_sessions.values()):
        q.put(None)
    _mcp_sessions.clear()
    print("sublime-mcp: stopped")


# ── helper text commands ──────────────────────────────────────────────────────


class McpReplaceRegionCommand(sublime_plugin.TextCommand):
    """Internal helper: replace an arbitrary character-offset region with new text.

    Called by _replace_lines() which converts line numbers to character offsets
    before dispatching here.  TextCommand is required because view.replace()
    needs an edit token.
    """

    def run(self, edit, begin, end, text):
        self.view.replace(edit, sublime.Region(begin, end), text)


class McpStrReplaceCommand(sublime_plugin.TextCommand):
    """Internal helper: replace a region and show a green underline highlight.

    Called by _edit_file(command='str_replace') after the unique match is found.
    Steps:
      1. Replace the matched region with new_str.
      2. Add a green 'mcp_edit' region with an annotation showing line number.
      3. Scroll the view to centre on the change.
      4. Schedule the region to be erased after _EDIT_HIGHLIGHT_MS milliseconds.

    Also sets the view's reference document to the pre-edit content so the
    ST gutter shows the diff markers.
    """

    def run(self, edit, begin, end, new_str):
        region = sublime.Region(begin, end)
        self.view.replace(edit, region, new_str)
        new_end = begin + len(new_str)
        new_region = sublime.Region(begin, new_end)
        row, _ = self.view.rowcol(begin)
        self.view.add_regions(
            "mcp_edit",
            [new_region],
            "region.greenish",
            "circle",
            sublime.DRAW_NO_FILL | sublime.DRAW_SOLID_UNDERLINE,
            annotations=[
                f'<div style="font-size:0.9em; padding:1px 4px;">'
                f"&#x270F; Claude &mdash; line {row + 1}</div>"
            ],
            annotation_color="#4CAF50",
        )
        self.view.show_at_center(new_region)
        sublime.set_timeout(
            lambda: self.view.erase_regions("mcp_edit"), _EDIT_HIGHLIGHT_MS
        )


class McpInsertTextCommand(sublime_plugin.TextCommand):
    """Internal helper: insert text at a character offset and show a cyan underline.

    Same highlight pattern as McpStrReplaceCommand but cyan/blue to
    distinguish insertions from replacements.
    """

    def run(self, edit, insert_pt, insert_text):
        self.view.insert(edit, insert_pt, insert_text)
        new_region = sublime.Region(insert_pt, insert_pt + len(insert_text))
        row, _ = self.view.rowcol(insert_pt)
        self.view.add_regions(
            "mcp_edit",
            [new_region],
            "region.cyanish",
            "dot",
            sublime.DRAW_NO_FILL | sublime.DRAW_SOLID_UNDERLINE,
            annotations=[
                f'<div style="font-size:0.9em; padding:1px 4px;">'
                f"&#x2795; Claude inserted &mdash; line {row + 1}</div>"
            ],
            annotation_color="#2196F3",
        )
        self.view.show_at_center(new_region)
        sublime.set_timeout(
            lambda: self.view.erase_regions("mcp_edit"), _EDIT_HIGHLIGHT_MS
        )


class McpCreateFileCommand(sublime_plugin.TextCommand):
    """Internal helper: populate a newly created (empty, retargeted) view with content."""

    def run(self, edit, file_text):
        self.view.insert(edit, 0, file_text)
        self.view.show_at_center(0)
