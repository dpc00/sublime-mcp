"""Run every sublime-mcp tool once against a PORTABLE Sublime and record what happens.

Usage: python sweep.py --port 9510 --root D:/st_portable_4215 --exe D:/st_portable_4215/sublime_text.exe
Needs the portable running with sublime-mcp loaded (HTTP bridge on --port). Never point it at the main
Sublime. Ask the owner before running it; read SKILL.md section 3 first.

For each tool: call it with the minimum arguments (required ones, empty values), clear any native dialog
or menu it opened (Cancel if there is a Cancel button, else OK, else close), ping the main thread, and
write one record to --out. If the portable stops answering it is killed and restarted from an empty
session with the saved Preferences put back. Tools that open a browser, quit Sublime, touch the licence
or install packages are not run (SKIP below).
"""
import argparse, json, os, re, shutil, subprocess, time, urllib.error, urllib.request

SKIP = re.compile(r"(browser|_url$|^open_url|html_print|open_context_url|^get_help|show_changelog|license"
                  r"|^exit$|^quit|hot_exit|close_window|close_all|install_package|remove_package|uninstall)", re.I)

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
ap.add_argument("--root", required=True, help="portable folder, e.g. D:/st_portable_4215")
ap.add_argument("--exe", required=True)
ap.add_argument("--out", default="sweep.json")
a = ap.parse_args()
PREFS = a.root + "/Data/Packages/User/Preferences.sublime-settings"
PREFS_BAK = a.out + ".preferences.bak"
shutil.copy2(PREFS, PREFS_BAK)


def call(path, d, t=14):
    r = urllib.request.Request("http://127.0.0.1:%d%s" % (a.port, path), data=json.dumps(d).encode(),
                               headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=t))


def ev(code, t=30):
    return call("/eval_python", {"code": code}, t).get("output", "")


def clear_dialogs():
    """Close every dialog, menu and Update window; return (what was there, was the main thread blocked)."""
    found = []
    d = call("/list_native_windows", {}, 8)
    for w in d["windows"]:
        if w["kind"] in ("dialog", "menu") or w.get("title") == "Update":
            buttons = [b["text"] for b in w.get("buttons", [])]
            found.append({"kind": w["kind"], "title": w.get("title"), "text": " ".join(w.get("messages") or [])[:200]})
            if "Cancel" in buttons:
                act = {"action": "button", "button": "Cancel"}
            else:
                act = {"action": "ok"} if w["kind"] == "dialog" else {"action": "close"}
            try:
                call("/dismiss_native_window", dict(hwnd=w["hwnd"], **act), 8)
            except Exception:
                pass
    return found, d.get("main_thread_blocked")


def setup():
    ev("""
import sublime
for w in sublime.windows()[1:]: w.run_command('close_window')
w = sublime.windows()[0]
for s in list(w.sheets()):
    v = s.view()
    if v: v.set_scratch(True)
    s.close()
v = w.new_file(); v.set_scratch(True); v.run_command('append', {'characters': 'alpha beta\\ngamma delta\\n'}); w.focus_view(v)
""")


def restart():
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_Process -Filter \"Name='sublime_text.exe'\" | ? { $_.ExecutablePath -like '%s*' }"
                    " | % { taskkill /PID $_.ProcessId /T /F | Out-Null }" % a.exe.replace("/", "\\").rsplit("\\", 1)[0]])
    time.sleep(3)
    for f in os.listdir(a.root + "/Data/Local"):
        if f.endswith(".sublime_session"):
            os.remove(a.root + "/Data/Local/" + f)
    shutil.copy2(PREFS_BAK, PREFS)
    subprocess.Popen(["powershell", "-NoProfile", "-Command", "Start-Process '%s'" % a.exe.replace("/", "\\")])
    for _ in range(40):
        time.sleep(2)
        try:
            ev("print(1)", 5)
            break
        except Exception:
            pass
    setup()


def default(sch):
    if "enum" in sch:
        return sch["enum"][0]
    return {"string": "", "integer": 1, "number": 1, "boolean": False, "array": [], "object": {}}.get(sch.get("type"), "")


tools = json.loads(ev("import sys, json\nm = sys.modules['MCP Commander.sublime_mcp']\n"
                      "print(json.dumps([[t[0], t[2]] for t in m._MCP_TOOLS]))"))
setup()
records = []
for name, sch in tools:
    rec = {"tool": name}
    if SKIP.search(name):
        rec["status"] = "not run"
        records.append(rec)
        continue
    sch = sch or {}
    props = sch.get("properties", {}) or {}
    args = {k: default(props[k]) for k in sch.get("required", []) if k in props}
    t0 = time.time()
    try:
        r = call("/" + name, args)
        rec["status"] = "error-reply" if isinstance(r, dict) and r.get("error") else "ok"
        if rec["status"] == "error-reply":
            rec["error"] = str(r["error"])[:160]
    except urllib.error.HTTPError as e:
        rec["status"] = "http%d" % e.code
    except Exception as e:
        rec["status"] = "exception"
        rec["error"] = str(e)[:100]
    rec["secs"] = round(time.time() - t0, 1)
    try:
        rec["dialogs"], rec["blocked"] = clear_dialogs()
    except Exception as e:
        rec["list_err"] = str(e)[:60]
    time.sleep(0.6)
    try:
        ev("print(1)", 8)
    except Exception:
        rec["ping"] = "HUNG"
        records.append(rec)
        print("HUNG after", name, flush=True)
        restart()
        continue
    records.append(rec)
    json.dump(records, open(a.out, "w"), indent=1)
ev("""
import sublime
w = sublime.windows()[0]
for s in list(w.sheets()):
    v = s.view()
    if v: v.set_scratch(True)
    s.close()
""")
shutil.copy2(PREFS_BAK, PREFS)
json.dump(records, open(a.out, "w"), indent=1)
from collections import Counter
print(Counter(r["status"] for r in records))
