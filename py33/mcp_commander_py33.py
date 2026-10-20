"""Quick panel recorder for the Python 3.3 plugin host.

sublime-mcp runs in the 3.8 host, so it cannot see quick panels that packages in the 3.3 host open
with window.show_quick_panel. sublime-mcp copies this file into the companion package
"MCP Commander Py33" (no .python-version, so Sublime loads it in the 3.3 host). It records the
panel last opened in this host per window and answers the command mcp_py33_quick_panel; the
answer goes to a JSON file because a command cannot return a value across hosts.

Keep this file Python 3.3 compatible (no f-strings, no type hints).
"""
import json
import os

import sublime
import sublime_plugin

_PANELS = {}  # window id -> record of the quick panel last opened from this host


def _item(item):
    if isinstance(item, str):
        return item
    if isinstance(item, (list, tuple)):
        return [str(x) for x in item]
    if hasattr(item, "trigger"):
        return {"trigger": str(item.trigger), "details": str(getattr(item, "details", "")),
                "annotation": str(getattr(item, "annotation", ""))}
    return str(item)


def _first_line(item):
    first = item["trigger"] if isinstance(item, dict) else (item[0] if isinstance(item, list) and item else item)
    return str(first).strip().lower()


def _install_recorder():
    cur = sublime.Window.show_quick_panel
    orig = getattr(cur, "_mcp_py33_orig", cur)

    def show_quick_panel(self, items, on_select=None, *args, **kwargs):
        if on_select is None:
            on_select = kwargs.pop("on_done", None)
        items = list(items)
        try:
            rec = {"raw": items, "on_select": on_select,
                   "flags": args[0] if args else kwargs.get("flags", 0),
                   "selected_index": args[1] if len(args) > 1 else kwargs.get("selected_index", -1),
                   "picked": False}
            wid = self.id()
        except Exception:
            return orig(self, items, on_select, *args, **kwargs)

        def done(index):
            if _PANELS.get(wid) is rec:
                del _PANELS[wid]
            if rec["picked"] and index == -1:
                return  # the cancel produced by our own hide_overlay
            if on_select is not None:
                return on_select(index)

        _PANELS[wid] = rec
        try:
            return orig(self, items, done, *args, **kwargs)
        except BaseException:
            if _PANELS.get(wid) is rec:
                del _PANELS[wid]
            raise

    show_quick_panel._mcp_py33_orig = orig
    sublime.Window.show_quick_panel = show_quick_panel


def _remove_recorder():
    cur = sublime.Window.show_quick_panel
    if hasattr(cur, "_mcp_py33_orig"):
        sublime.Window.show_quick_panel = cur._mcp_py33_orig


def _write(req, data):
    folder = os.path.join(sublime.cache_path(), "MCP Commander")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    path = os.path.join(folder, "py33_qp_%s.json" % req)
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(path + ".tmp", path)  # the reader never sees a half-written file


def _items(rec):
    if "items" not in rec:
        rec["items"] = [_item(i) for i in rec["raw"]]
    return rec["items"]


def _list(rec, args):
    items = _items(rec)
    text = str(args.get("text") or "").strip().lower()
    limit = max(1, min(int(args.get("limit", 100)), 1000))
    offset = max(0, int(args.get("offset", 0)))
    indexes = [n for n, it in enumerate(items) if not text or text in _first_line(it)]
    page = indexes[offset:offset + limit]
    return {"items": [items[n] for n in page], "indexes": page, "total": len(items),
            "matched": len(indexes), "offset": offset, "flags": rec["flags"],
            "selected_index": rec["selected_index"]}


def _pick(window, wid, rec, args):
    items = _items(rec)
    i, text = args.get("index"), args.get("text")
    if i is not None and text:
        return {"error": "give index or text, not both"}
    if isinstance(i, bool):
        return {"error": "index must be an integer"}
    if i is None and text:
        low = str(text).strip().lower()
        firsts = [_first_line(it) for it in items]
        hits = [n for n, f in enumerate(firsts) if f == low]  # an exact match wins
        if len(hits) != 1:
            hits = [n for n, f in enumerate(firsts) if low in f]
        if len(hits) != 1:
            return {"error": "text matched %d items; give a more exact text or an index" % len(hits),
                    "matches": hits}
        i = hits[0]
    if i is None:
        return {"error": "give index or text"}
    if not isinstance(i, int) or not -1 <= i < len(items):
        return {"error": "index must be -1 (cancel) or 0..%d" % (len(items) - 1)}
    if i == -1:
        window.run_command("hide_overlay")
        return {"ok": True, "picked": -1}
    _PANELS.pop(wid, None)
    rec["picked"] = True
    window.run_command("hide_overlay")
    if rec["on_select"] is not None:
        try:
            rec["on_select"](i)
        except Exception as e:  # the package's own code failed; say so instead of "ok"
            return {"error": "the panel was closed and the package's callback raised %s: %s"
                             % (type(e).__name__, e), "picked": i, "item": items[i]}
    return {"ok": True, "picked": i, "item": items[i]}


class McpPy33QuickPanelCommand(sublime_plugin.WindowCommand):
    def run(self, req, action="list", **args):
        rec = _PANELS.get(self.window.id())
        if rec is None:
            _write(req, {"open": False})
            return
        try:
            if action == "pick":
                result = _pick(self.window, self.window.id(), rec, args)
            else:
                result = _list(rec, args)
        except Exception as e:
            result = {"error": "%s: %s" % (type(e).__name__, e)}
        _write(req, {"open": True, "result": result})


def plugin_loaded():
    _install_recorder()


def plugin_unloaded():
    _remove_recorder()
