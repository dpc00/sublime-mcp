"""Probe what every generated Sublime Text command tool really does.

Windows only. Runs each command tool (no arguments) one at a time against a
DISPOSABLE bare Sublime Text instance that has only MCP Commander installed,
and records what happened: new native OS windows (dialogs), a blocked main
thread, panel / view / file / clipboard / settings changes, a visual change with
no state change (an in-app overlay or popup), new processes, or the app exiting.
After every command it closes stray windows, resets the sandbox and restarts the
instance if it quit or hung. Results go to tools/st_commands_behavior.json.

    python tools/probe_st_commands.py --exe D:\\st_bare_4215\\sublime_text.exe \\
        --port 9520 --sandbox D:\\st_bare_sandbox

NEVER point this at your real Sublime Text: it runs commands such as exit,
delete_file and revert. Every command is run; windows of a browser or file manager that a command
opens are closed afterwards and recorded.
"""

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sublime_mcp.py"
SNAPSHOT = ROOT / "tools" / "st_commands_metadata.json"
OUT = ROOT / "tools" / "st_commands_behavior.json"

# Process names that are noise (our own shell loops, OS services).
NOISE = {"sleep.exe", "conhost.exe", "tasklist.exe", "powershell.exe", "cmd.exe", "timeout.exe", "sppsvc.exe", "smartscreen.exe", "chrome-native-host.exe", "extension-host.exe"}
EXTERNAL_APPS = ("msedge.exe", "chrome.exe", "firefox.exe", "brave.exe", "explorer.exe", "sublime_merge.exe", "openwith.exe")

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
WM_CLOSE = 0x0010


# ---------------------------------------------------------------- bridge
def post(port, route, body=None, timeout=8):
    req = urllib.request.Request(
        "http://127.0.0.1:%d/%s" % (port, route.lstrip("/")),
        data=json.dumps(body or {}).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def eval_py(port, code, timeout=8):
    r = post(port, "eval_python", {"code": code}, timeout)
    if not r.get("ok", True):
        raise RuntimeError(r.get("error"))
    return r.get("output", "")


def alive(port, timeout=3):
    try:
        return eval_py(port, "print('pong')", timeout).strip() == "pong"
    except Exception:
        return False


# ---------------------------------------------------------------- process / windows
def find_pid(exe):
    ps = ("(Get-Process sublime_text -ErrorAction SilentlyContinue | "
          "Where-Object { $_.Path -eq '%s' } | Select-Object -First 1).Id" % exe)
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True).stdout.strip()
    return int(out) if out.isdigit() else None


def pid_running(pid):
    h = kernel32.OpenProcess(0x1000, False, pid)
    if not h:
        return False
    code = wt.DWORD()
    kernel32.GetExitCodeProcess(h, ctypes.byref(code))
    kernel32.CloseHandle(h)
    return code.value == 259  # STILL_ACTIVE


def windows_of(pid):
    found = {}
    proto = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

    def cb(hwnd, _):
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, 256)
            found[hwnd] = (cls.value, buf.value)
        return True

    user32.EnumWindows(proto(cb), 0)
    return found


def all_windows():
    found = {}
    proto = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            p = wt.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
            found[hwnd] = p.value
        return True

    user32.EnumWindows(proto(cb), 0)
    return found


def process_image(pid):
    h = kernel32.OpenProcess(0x1000, False, pid)
    if not h:
        return ""
    try:
        size = wt.DWORD(1024)
        buf = ctypes.create_unicode_buffer(1024)
        if not kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return ""
        return buf.value.rsplit("\\", 1)[-1].lower()
    finally:
        kernel32.CloseHandle(h)


def process_names():
    out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
    return set(re.findall(r'^"([^"]+)"', out, re.M))


def start(exe, port):
    subprocess.Popen([exe], cwd=os.path.dirname(exe))
    for _ in range(60):
        time.sleep(1)
        if alive(port, 2):
            time.sleep(1)
            return find_pid(exe)
    raise RuntimeError("instance did not come up")


# ---------------------------------------------------------------- state
STATE_CODE = r"""
import sublime, json, os
w = sublime.active_window()
v = w.active_view() if w else None
def listing(d):
    out = {}
    for root, dirs, files in os.walk(d):
        for f in files:
            p = os.path.join(root, f)
            try:
                s = os.stat(p); out[p] = [s.st_size, int(s.st_mtime)]
            except OSError:
                pass
    return out
data = os.path.dirname(sublime.packages_path())
st = {
 'windows': len(sublime.windows()),
 'views': len(w.views()) if w else 0,
 'panel': w.active_panel() if w else None,
 'file': v.file_name() if v else None,
 'size': v.size() if v else 0,
 'dirty': v.is_dirty() if v else None,
 'sel': [[r.a, r.b] for r in v.sel()] if v else [],
 'viewport': list(v.viewport_position()) if v else None,
 'folded': len(v.folded_regions()) if v else 0,
 'layout': w.get_layout() if w else None,
 'sidebar': w.is_sidebar_visible() if w else None,
 'minimap': w.is_minimap_visible() if w else None,
 'clipboard': sublime.get_clipboard(),
 'folders': w.folders() if w else [],
 'user_files': listing(os.path.join(data, 'Packages', 'User')),
 'local_files': listing(os.path.join(data, 'Local')),
 'sandbox_files': listing(SANDBOX),
}
print(json.dumps(st))
"""


def snapshot(port, sandbox):
    return json.loads(eval_py(port, "SANDBOX = %r\n" % sandbox + STATE_CODE, 8))


def diff_state(a, b):
    changes = []
    for k in a:
        if k in ("user_files", "local_files", "sandbox_files"):
            ch = sorted(set(a[k]) ^ set(b[k]) | {p for p in a[k] if p in b[k] and a[k][p] != b[k][p]})
            ch = [c for c in ch if not c.endswith(("Session.sublime_session", "Session.sublime_session.tmp", "Recent"))]
            if ch:
                changes.append(k + ":" + ",".join(os.path.basename(c) for c in ch[:4]))
        elif a[k] != b[k]:
            changes.append(k)
    return changes


def reset_sandbox(sandbox, pristine):
    """Empty the sandbox and copy the pristine files in. The folder itself is kept
    because Sublime may hold it open (Windows cannot delete a folder in use)."""
    os.makedirs(sandbox, exist_ok=True)
    for entry in os.listdir(sandbox):
        path = os.path.join(sandbox, entry)
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                os.remove(path)
            except OSError:
                pass
    for entry in os.listdir(pristine):
        src = os.path.join(pristine, entry)
        dst = os.path.join(sandbox, entry)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)


RESET_CODE = r"""
import sublime, os
A = os.path.join(SANDBOX, 'a.txt')
ws = sublime.windows()
first = ws[0]
for x in ws[1:]:
    for vv in x.views():
        vv.set_scratch(True)
    x.run_command('close_window')
for vv in first.views():
    vv.set_scratch(True)
    vv.close()
first.set_project_data({})
first.run_command('hide_panel')
first.run_command('hide_overlay')
sublime.set_clipboard('CLIP')
first.open_file(A)
print('reset ok')
"""


def reset(port, sandbox):
    eval_py(port, "SANDBOX = %r\n" % sandbox + RESET_CODE, 10)
    time.sleep(0.6)
    eval_py(port, "import sublime\nw=sublime.active_window()\nv=w.active_view()\nv.sel().clear()\nv.sel().add(sublime.Region(0,0))\nw.focus_view(v)\nprint('ok')", 5)


# ---------------------------------------------------------------- screenshot
def capture(hwnd):
    try:
        from PIL import Image
        rect = wt.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        w, h = rect.right - rect.left, rect.bottom - rect.top
        if w <= 0 or h <= 0:
            return None
        hdc = user32.GetWindowDC(hwnd)
        gdi = ctypes.windll.gdi32
        mdc = gdi.CreateCompatibleDC(hdc)
        bmp = gdi.CreateCompatibleBitmap(hdc, w, h)
        gdi.SelectObject(mdc, bmp)
        user32.PrintWindow(hwnd, mdc, 2)
        class BMI(ctypes.Structure):
            _fields_ = [("s", wt.DWORD), ("w", wt.LONG), ("h", wt.LONG), ("p", wt.WORD), ("b", wt.WORD),
                        ("c", wt.DWORD), ("si", wt.DWORD), ("x", wt.LONG), ("y", wt.LONG), ("u", wt.DWORD), ("i", wt.DWORD)]
        bmi = BMI(ctypes.sizeof(BMI), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
        buf = ctypes.create_string_buffer(w * h * 4)
        gdi.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bmi), 0)
        gdi.DeleteObject(bmp); gdi.DeleteDC(mdc); user32.ReleaseDC(hwnd, hdc)
        return Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("L")
    except Exception:
        return None


def visual_change(a, b):
    if a is None or b is None or a.size != b.size:
        return None
    from PIL import ImageChops
    d = ImageChops.difference(a, b).point(lambda p: 255 if p > 24 else 0)
    hist = d.histogram()
    return round(hist[255] / float(a.size[0] * a.size[1]) * 100, 2)


# ---------------------------------------------------------------- main
def synth_args(sandbox, meta):
    """Plausible sandbox-only arguments for every documented argument of a command."""
    a_txt = os.path.join(sandbox, "a.txt")
    sub = os.path.join(sandbox, "sub")
    body = {}
    for arg in meta.get("args") or []:
        n = arg.get("name") or ""
        t = (arg.get("type") or "").lower()
        if n in ("file", "path", "file_path", "filename"):
            v = a_txt
        elif n in ("files", "paths"):
            v = [a_txt]
        elif n in ("dir", "directory", "folder"):
            v = sub
        elif n in ("dirs", "folders"):
            v = [sub]
        elif n == "encoding":
            v = "UTF-8"
        elif n == "commands":
            v = [["hide_overlay"]]
        elif n == "panel":
            v = "console"
        elif n in ("width", "height"):
            v = 600
        elif t.startswith("list"):
            v = []
        elif t in ("object", "dict") or t.startswith("dict"):
            v = {}
        elif t in ("boolean", "bool"):
            v = False
        elif t == "int":
            v = 0
        elif t == "float":
            v = 1.0
        else:
            v = "x"
        body[n] = v
    return body


def hand_written_tools():
    """{tool name: (route, inputSchema)} for hand-written tools that are plain _p routes."""
    import ast
    src = SOURCE.read_text(encoding="utf-8")
    generated = set(generated_names())
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_MCP_TOOLS" for t in node.targets):
            for e in node.value.elts:
                name, handler = e.elts[0].value, e.elts[3]
                if name in generated:
                    continue
                if isinstance(handler, ast.Call) and getattr(handler.func, "id", "") == "_p" and handler.args                         and isinstance(handler.args[0], ast.Constant):
                    out[name] = (handler.args[0].value.lstrip("/"), ast.literal_eval(e.elts[2]))
    return out


def synth_from_schema(sandbox, schema):
    """Sandbox-only arguments for every property of a tool's input schema."""
    a_txt = os.path.join(sandbox, "a.txt")
    body = {}
    for n, spec in (schema.get("properties") or {}).items():
        t = spec.get("type")
        if spec.get("enum"):
            v = spec["enum"][0]
        elif n in ("path", "file", "file_path", "filename", "name") and t == "string":
            v = a_txt
        elif n in ("folder", "dir", "directory") and t == "string":
            v = os.path.join(sandbox, "sub")
        elif t == "string":
            v = "x"
        elif t == "integer":
            v = 1
        elif t == "number":
            v = 1.0
        elif t == "boolean":
            v = False
        elif t == "array":
            v = []
        elif t == "object":
            v = {}
        else:
            v = "x"
        body[n] = v
    return body


def mcp_call(mcp_port, name, args, timeout=12):
    """Call a tool through the MCP endpoint (JSON-RPC tools/call), the path direct MCP clients use."""
    msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}
    req = urllib.request.Request("http://127.0.0.1:%d/mcp" % mcp_port, data=json.dumps(msg).encode(),
                                 headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    raw = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")
    for line in raw.splitlines():
        if line.startswith("data:"):
            raw = line[5:].strip()
            break
    return json.loads(raw)


def other_tools():
    """Hand-written tools that are not plain _p routes (GET reads, meta tools, MCP-only)."""
    import ast
    src = SOURCE.read_text(encoding="utf-8")
    generated = set(generated_names())
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_MCP_TOOLS" for t in node.targets):
            for e in node.value.elts:
                name, handler = e.elts[0].value, e.elts[3]
                if name in generated or (isinstance(handler, ast.Call) and getattr(handler.func, "id", "") == "_p"):
                    continue
                out[name] = ast.literal_eval(e.elts[2])
    return out


def generated_names():
    src = SOURCE.read_text(encoding="utf-8")
    blk = re.search(r"# BEGIN GENERATED ST COMMAND TOOLS.*?# END GENERATED ST COMMAND TOOLS", src, re.S).group(0)
    return re.findall(r'^    \("([a-z0-9_]+)",$', blk, re.M)


def probe_one(name, exe, port, sandbox, pristine, pid, results, body=None, route=None, caller=None):
    """Run one command; return (record, pid) - pid changes if the app was restarted."""
    rec = {"tags": [], "changes": [], "new_windows": [], "new_processes": []}
    reset_sandbox(sandbox, pristine)
    reset(port, sandbox)
    base_wins = windows_of(pid)
    main = next(iter(base_wins), None)
    before = snapshot(port, sandbox)
    procs_before = process_names()
    all_before = all_windows()
    img_before = capture(main) if main else None

    try:
        resp = caller(body or {}) if caller else post(port, route or name, body or {}, timeout=8)
        rec["response"] = json.dumps(resp)[:120]
    except Exception as e:
        rec["response"] = "error: %s" % type(e).__name__
    time.sleep(1.6)

    if not pid_running(pid):
        rec["tags"].append("EXITS_APP")
        return rec, start(exe, port)

    new = {h: v for h, v in windows_of(pid).items() if h not in base_wins}
    if new:
        rec["tags"].append("NEW_OS_WINDOW")
        rec["new_windows"] = ["%s | %s" % v for v in new.values()][:4]
    if not alive(port, 4):
        rec["tags"].append("BLOCKS_MAIN_THREAD")
        for h in new:
            user32.PostMessageW(h, WM_CLOSE, 0, 0)
        time.sleep(1.5)
        if not alive(port, 6):
            rec["tags"].append("HUNG_NEEDED_KILL")
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            time.sleep(2)
            return rec, start(exe, port)
    after = snapshot(port, sandbox)
    rec["changes"] = diff_state(before, after)
    img_after = capture(main) if main else None
    vis = visual_change(img_before, img_after)
    rec["visual_change_pct"] = vis
    if vis is not None and vis > 0.3 and not rec["changes"] and not new:
        rec["tags"].append("VISUAL_ONLY_OVERLAY_OR_POPUP")
    for h in new:
        user32.PostMessageW(h, WM_CLOSE, 0, 0)
    for hwnd, wpid in all_windows().items():
        if hwnd not in all_before and wpid != pid and process_image(wpid) in EXTERNAL_APPS:
            rec.setdefault("closed_external_windows", []).append(process_image(wpid))
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    newp = sorted(n for n in process_names() - procs_before if n.lower() not in NOISE)
    if any(n.lower() in EXTERNAL_APPS for n in newp):
        rec["tags"].append("STARTS_EXTERNAL_APP")
    if newp:
        rec["tags"].append("STARTED_PROCESS")
        rec["new_processes"] = newp[:4]
        for n in newp:
            if n.lower().startswith("sublime_merge") or n.lower().startswith("git"):
                subprocess.run(["taskkill", "/F", "/IM", n], capture_output=True)
    if any(c.startswith("sandbox_files") for c in rec["changes"]):
        rec["tags"].append("CHANGES_FILES")
    if "clipboard" in rec["changes"]:
        rec["tags"].append("CHANGES_CLIPBOARD")
    if any(c.startswith(("user_files", "local_files")) for c in rec["changes"]):
        rec["tags"].append("CHANGES_SETTINGS_OR_SESSION")
    if "panel" in rec["changes"]:
        rec["tags"].append("OPENS_PANEL")
    if "windows" in rec["changes"]:
        rec["tags"].append("NEW_ST_WINDOW")
    if not rec["tags"] and not rec["changes"]:
        rec["tags"].append("NO_OBSERVABLE_EFFECT")
    return rec, pid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--port", type=int, default=9520)
    ap.add_argument("--sandbox", required=True)
    ap.add_argument("--only")
    ap.add_argument("--other-tools", action="store_true", help="probe the hand-written tools that are not plain routes, through the MCP endpoint")
    ap.add_argument("--mcp-port", type=int, default=9522)
    ap.add_argument("--hand-written", action="store_true", help="probe the hand-written tools instead (two passes: no args, schema args)")
    ap.add_argument("--with-args", action="store_true", help="second pass: commands that take arguments, called with synthesized sandbox arguments")
    ap.add_argument("--out")
    ap.add_argument("--redo", action="store_true")
    args = ap.parse_args()
    args.exe = os.path.normpath(args.exe)
    args.sandbox = os.path.normpath(args.sandbox)
    global OUT
    if args.out:
        OUT = Path(args.out)

    pristine = args.sandbox + "_pristine"
    if not os.path.isdir(pristine):
        os.makedirs(pristine)
        Path(pristine, "a.txt").write_text("alpha\n    beta\ngamma\n", encoding="utf-8")
        Path(pristine, "b.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        Path(pristine, "sub").mkdir()
        Path(pristine, "sub", "c.txt").write_text("c\n", encoding="utf-8")

    names = generated_names()
    if args.only:
        names = [n for n in names if n in args.only.split(",")]
    results = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() and not args.redo else {"_meta": {}, "commands": {}}
    results["_meta"] = {"sublime_text_build": "4215", "app": "bare portable, MCP Commander only",
                        "method": "each command called with no arguments via its tool route; see tools/probe_st_commands.py"}

    pid = find_pid(args.exe) or start(args.exe, args.port)
    if args.other_tools:
        tools = other_tools()
        out_path = Path(args.out) if args.out else ROOT / "tools" / "st_other_tools_behavior.json"
        res = {"_meta": {"sublime_text_build": "4215", "app": "bare portable, MCP Commander only",
                         "method": "each tool called through the MCP endpoint (tools/call); pass 1 no arguments, pass 2 schema-derived sandbox arguments"},
               "tools": {}}
        todo = [n for n in sorted(tools) if (not args.only or n in args.only.split(","))]
        for i, name in enumerate(todo, 1):
            schema = tools[name]
            entry = {}
            for label, body in (("no_args", {}), ("with_args", synth_from_schema(args.sandbox, schema) if schema.get("properties") else None)):
                if body is None:
                    continue
                if not pid_running(pid) or not alive(args.port, 5):
                    pid = find_pid(args.exe) or start(args.exe, args.port)
                try:
                    rec, pid = probe_one(name, args.exe, args.port, args.sandbox, pristine, pid, {}, body,
                                         caller=lambda b, n=name: mcp_call(args.mcp_port, n, b))
                except Exception as e:
                    rec = {"tags": ["PROBE_ERROR"], "note": "%s: %s" % (type(e).__name__, e)}
                    pid = find_pid(args.exe) or start(args.exe, args.port)
                rec["args_used"] = body
                entry[label] = rec
            res["tools"][name] = entry
            out_path.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
            print("%3d/%d %-30s %s" % (i, len(todo), name, " | ".join(",".join(v["tags"]) for v in entry.values())), flush=True)
        return
    if args.hand_written:
        tools = hand_written_tools()
        out_path = Path(args.out) if args.out else ROOT / "tools" / "st_hand_written_behavior.json"
        res = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() and not args.redo else {"_meta": {}, "tools": {}}
        res["_meta"] = {"sublime_text_build": "4215", "app": "bare portable, MCP Commander only",
                        "method": "hand-written _p-routed tools; pass 1 no arguments, pass 2 schema-derived sandbox arguments",
                        "skipped": "nothing: every hand-written tool with a _p route is run"}
        todo = [n for n in sorted(tools) if (not args.only or n in args.only.split(","))]
        for i, name in enumerate(todo, 1):
            route, schema = tools[name]
            if name in res["tools"] and not args.only:
                continue
            entry = {}
            for label, body in (("no_args", {}), ("with_args", synth_from_schema(args.sandbox, schema) if schema.get("properties") else None)):
                if body is None:
                    continue
                if not pid_running(pid) or not alive(args.port, 5):
                    pid = find_pid(args.exe) or start(args.exe, args.port)
                try:
                    rec, pid = probe_one(name, args.exe, args.port, args.sandbox, pristine, pid, {}, body, route)
                except Exception as e:
                    rec = {"tags": ["PROBE_ERROR"], "note": "%s: %s" % (type(e).__name__, e)}
                    pid = find_pid(args.exe) or start(args.exe, args.port)
                rec["args_used"] = body
                entry[label] = rec
            res["tools"][name] = entry
            out_path.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
            print("%3d/%d %-34s %s" % (i, len(todo), name, " | ".join(",".join(v["tags"]) for v in entry.values())), flush=True)
        return
    if args.with_args:
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["commands"]
        names = [n for n in names if snap[n].get("args")]
        for i, name in enumerate(names, 1):
            body = synth_args(args.sandbox, snap[name])
            if not pid_running(pid) or not alive(args.port, 5):
                pid = find_pid(args.exe) or start(args.exe, args.port)
            try:
                rec, pid = probe_one(name, args.exe, args.port, args.sandbox, pristine, pid, results, body)
            except Exception as e:
                rec = {"tags": ["PROBE_ERROR"], "note": "%s: %s" % (type(e).__name__, e)}
                pid = find_pid(args.exe) or start(args.exe, args.port)
            rec["args_used"] = body
            results["commands"].setdefault(name, {})["with_args"] = rec
            OUT.write_text(json.dumps(results, indent=1, sort_keys=True), encoding="utf-8")
            print("%3d/%d %-40s %s" % (i, len(names), name, ",".join(rec["tags"])), flush=True)
        return
    for i, name in enumerate(names, 1):
        if name in results["commands"] and not args.only:
            continue
        if True:
            if not pid_running(pid) or not alive(args.port, 5):
                pid = find_pid(args.exe) or start(args.exe, args.port)
            try:
                rec, pid = probe_one(name, args.exe, args.port, args.sandbox, pristine, pid, results)
            except Exception as e:
                rec = {"tags": ["PROBE_ERROR"], "note": "%s: %s" % (type(e).__name__, e)}
                pid = find_pid(args.exe) or start(args.exe, args.port)
            results["commands"][name] = rec
        OUT.write_text(json.dumps(results, indent=1, sort_keys=True), encoding="utf-8")
        print("%3d/%d %-40s %s" % (i, len(names), name, ",".join(results["commands"][name]["tags"])), flush=True)


if __name__ == "__main__":
    main()
