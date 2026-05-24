"""sublime-mcp — Sublime Text plugin.

Exposes a local HTTP API on 127.0.0.1:9500 so an external MCP server
can read and control Sublime Text.

Install: copy this file to Packages/User/ (or symlink it there).
"""
import json
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
    exc    = [None]
    done   = threading.Event()
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
            "path":     v.file_name(),
            "name":     v.name(),
            "content":  v.substr(sublime.Region(0, v.size())),
            "line":     row + 1,
            "col":      col + 1,
            "is_dirty": v.is_dirty(),
            "syntax":   syn.name if syn else None,
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
            out.append({
                "text":       v.substr(r),
                "begin_line": ar + 1,
                "begin_col":  ac + 1,
                "end_line":   br + 1,
                "end_col":    bc + 1,
            })
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
        end_row   = row + n
        start_pt  = v.text_point(start_row, 0)
        end_line  = v.text_point(min(end_row, v.rowcol(v.size())[0]), 0)
        end_pt    = v.full_line(end_line).end()
        text      = v.substr(sublime.Region(start_pt, end_pt))
        lines     = text.split("\n")
        numbered  = "\n".join(f"{start_row + i + 1:4}: {l}" for i, l in enumerate(lines))
        return {
            "path":        v.file_name(),
            "cursor_line": row + 1,
            "cursor_col":  col + 1,
            "start_line":  start_row + 1,
            "context":     numbered,
        }
    return _on_main(fn)


def _get_open_files(params):
    def fn():
        w = sublime.active_window()
        return {"files": [
            {"path": v.file_name(), "name": v.name(), "is_dirty": v.is_dirty()}
            for v in w.views()
        ]}
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


def _get_output_panel(params):
    name = params.get("name", ["exec"])[0]
    def fn():
        v = sublime.active_window().find_output_panel(name)
        if not v:
            return {"error": f"panel not found: {name}"}
        return {"name": name, "content": v.substr(sublime.Region(0, v.size()))}
    return _on_main(fn)


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
        return {"locations": [
            {"path": l.path, "name": l.display_name, "line": l.row + 1, "col": l.col + 1}
            for l in locs
        ]}
    return _on_main(fn)


def _get_project_data(params):
    def fn():
        return {"project_data": sublime.active_window().project_data()}
    return _on_main(fn)


def _get_variables(params):
    def fn():
        return sublime.active_window().extract_variables()
    return _on_main(fn)


# ── POST handlers ─────────────────────────────────────────────────────────────

def _open_file(body):
    path = body.get("path")
    if not path:
        return {"error": "path required"}
    line = body.get("line", 0)
    col  = body.get("col", 0)
    def fn():
        w     = sublime.active_window()
        flags = sublime.ENCODED_POSITION if (line or col) else sublime.NewFileFlags.NONE
        fname = f"{path}:{line}:{col}" if (line or col) else path
        w.open_file(fname, flags)
        return {"ok": True}
    return _on_main(fn)


def _goto_line(body):
    line = body.get("line")
    col  = body.get("col", 1)
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
    end   = body.get("end")
    text  = body.get("text", "")
    if begin is None or end is None:
        return {"error": "begin and end required"}
    def fn():
        v = _active_view()
        if not v:
            return {"error": "no active view"}
        start_pt = v.text_point(begin - 1, 0)
        end_pt   = v.full_line(v.text_point(end - 1, 0)).end()
        v.run_command("sublime_mcp_replace_region", {
            "begin": start_pt, "end": end_pt, "text": text,
        })
        return {"ok": True}
    return _on_main(fn)


def _run_command(body):
    cmd   = body.get("command")
    args  = body.get("args") or {}
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
    key   = body.get("key", "sublime_mcp")
    value = body.get("value", "")
    def fn():
        v = _active_view()
        if v:
            v.set_status(key, value)
        return {"ok": True}
    return _on_main(fn)


# ── routing ───────────────────────────────────────────────────────────────────

_GET = {
    "/active_file":     _get_active_file,
    "/selection":       _get_selection,
    "/cursor_context":  _get_cursor_context,
    "/open_files":      _get_open_files,
    "/project_folders": _get_project_folders,
    "/file_content":    _get_file_content,
    "/output_panel":    _get_output_panel,
    "/symbols":         _get_symbols,
    "/lookup_symbol":   _lookup_symbol,
    "/project_data":    _get_project_data,
    "/variables":       _get_variables,
}

_POST = {
    "/open_file":          _open_file,
    "/goto_line":          _goto_line,
    "/show_panel":         _show_panel,
    "/replace_selection":  _replace_selection,
    "/replace_lines":      _replace_lines,
    "/run_command":        _run_command,
    "/run_build":          _run_build,
    "/set_status":         _set_status,
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
        parsed  = urlparse(self.path)
        params  = parse_qs(parsed.query)
        handler = _GET.get(parsed.path)
        if handler:
            try:
                self._json(handler(params))
            except Exception as e:
                self._json({"error": str(e)}, 500)
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        parsed  = urlparse(self.path)
        length  = int(self.headers.get("Content-Length", 0))
        body    = json.loads(self.rfile.read(length)) if length else {}
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
