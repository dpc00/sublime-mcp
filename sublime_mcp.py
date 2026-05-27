"""sublime-mcp — Sublime Text plugin.

Exposes a local HTTP API on 127.0.0.1:9500 so an external MCP server
can read and control Sublime Text.

Install: copy this file to Packages/User/ (or symlink it there).
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
from urllib.parse import parse_qs, urlparse

import sublime
import sublime_plugin

_PORT = 9500


# ── main-thread dispatch ──────────────────────────────────────────────────────


def _on_main(fn):
    """Run fn() on ST's main thread; block caller until done."""
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
        tag = v.settings().get("terminus_view.tag")
        if tag:
            w.run_command("terminus_send_string", {"string": text, "tag": tag})
        else:
            w.focus_view(v)
            w.run_command("terminus_send_string", {"string": text})
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
            "sublime_mcp_replace_region",
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
    """Runs on HTTP thread — no ST API needed for file I/O."""
    pattern = body.get("pattern", "")
    folders = body.get("folders") or []
    case = body.get("case_sensitive", False)
    use_re = body.get("regex", False)
    max_hits = int(body.get("max_results", 200))
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
    for folder in folders:
        for dirpath, dirnames, filenames in os.walk(folder):
            dirnames[:] = [d for d in dirnames if d not in SKIP]
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                try:
                    text = open(fpath, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                for m in rx.finditer(text):
                    line_no = text[: m.start()].count("\n") + 1
                    results.append({"path": fpath, "line": line_no, "match": m.group()})
                    if len(results) >= max_hits:
                        return {"results": results, "truncated": True}
    return {"results": results, "truncated": False}


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


# ── routing ───────────────────────────────────────────────────────────────────

_GET = {
    "/active_file": _get_active_file,
    "/selection": _get_selection,
    "/cursor_context": _get_cursor_context,
    "/open_files": _get_open_files,
    "/project_folders": _get_project_folders,
    "/file_content": _get_file_content,
    "/view_content": _get_view_content,
    "/view_size": _get_view_size,
    "/view_chars": _get_view_chars,
    "/view_phantoms": _get_view_phantoms,
    "/output_panel": _get_output_panel,
    "/console_log": _get_console_log,
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


# ── plugin lifecycle ──────────────────────────────────────────────────────────

_server = None


def plugin_loaded():
    global _server
    _install_console_capture()
    _server = HTTPServer(("127.0.0.1", _PORT), _Handler)
    t = threading.Thread(target=_server.serve_forever, daemon=True)
    t.start()
    print(f"sublime-mcp: listening on 127.0.0.1:{_PORT}")


def plugin_unloaded():
    global _server
    if _server:
        _server.shutdown()
        _server = None
    print("sublime-mcp: stopped")


# ── helper text command (needed for replace_lines) ────────────────────────────


class SublimeMcpReplaceRegionCommand(sublime_plugin.TextCommand):
    def run(self, edit, begin, end, text):
        self.view.replace(edit, sublime.Region(begin, end), text)
