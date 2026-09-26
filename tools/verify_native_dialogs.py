"""Live check of list_native_windows / dismiss_native_window on a bare Sublime Text.

For every command that was observed to block Sublime's main thread behind a native
window (tools/st_commands_behavior.json), this opens the real dialog through the
command's tool route, confirms Sublime is really blocked (eval_python stops
answering), then lists the window and dismisses it with the new tools and confirms
Sublime answers again. Windows only. Use a disposable instance:

    python tools/verify_native_dialogs.py --port 9520 --sandbox D:\\st_bare_sandbox
"""

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_st_commands as P  # noqa: E402  (reuses post/alive/reset helpers)

BEHAVIOR = Path(__file__).resolve().parent / "st_commands_behavior.json"
OUT = Path(__file__).resolve().parent / "st_dialog_dismissal_results.json"


def call_in_thread(port, route, body):
    """Run a tool call that will hang on a blocking dialog without blocking us."""
    box = {}

    def run():
        try:
            box["result"] = P.post(port, route, body, timeout=12)
        except Exception as e:  # timeout or connection error is expected
            box["error"] = "%s: %s" % (type(e).__name__, e)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t, box


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9520)
    ap.add_argument("--sandbox", required=True)
    ap.add_argument("--only")
    args = ap.parse_args()
    sandbox = os.path.normpath(args.sandbox)
    pristine = sandbox + "_pristine"
    data = json.loads(BEHAVIOR.read_text(encoding="utf-8"))["commands"]
    snap = json.loads(P.SNAPSHOT.read_text(encoding="utf-8"))["commands"]

    todo = []
    for name, rec in sorted(data.items()):
        for label, r in (("no args", rec), ("with args", rec.get("with_args"))):
            if r and "BLOCKS_MAIN_THREAD" in r.get("tags", []):
                body = {} if label == "no args" else P.synth_args(sandbox, snap[name])
                todo.append((name, label, body))
                break
    if args.only:
        wanted = args.only.split(",")
        todo = [t for t in todo if t[0] in wanted]

    results = []
    for name, label, body in todo:
        P.reset_sandbox(sandbox, pristine)
        P.reset(args.port, sandbox)
        row = {"command": name, "called": label}
        thread, box = call_in_thread(args.port, name, body)
        time.sleep(2.5)
        row["frozen_while_dialog_open"] = not P.alive(args.port, 3)
        try:
            listing = P.post(args.port, "list_native_windows", {}, timeout=8)
            row["main_thread_blocked_reported"] = listing.get("main_thread_blocked")
            row["blocked_by"] = listing.get("blocked_by")
            row["windows"] = [
                {"kind": w["kind"], "title": w["title"], "buttons": [b["text"] for b in w.get("buttons", [])],
                 "messages": w.get("messages", [])[:2]}
                for w in listing["windows"] if w["kind"] in ("dialog", "menu", "window")
            ]
            dismissed = P.post(args.port, "dismiss_native_window", {"action": "cancel"}, timeout=8)
            row["dismiss"] = {k: dismissed.get(k) for k in ("ok", "closed", "did", "title", "error")}
        except Exception as e:
            row["error"] = "%s: %s" % (type(e).__name__, e)
        time.sleep(1.0)
        row["answers_again"] = P.alive(args.port, 6)
        thread.join(timeout=15)
        row["tool_call_outcome"] = json.dumps(box)[:140]
        results.append(row)
        print("%-36s frozen=%-5s dismissed=%-5s answers_again=%s" % (
            name, row.get("frozen_while_dialog_open"), (row.get("dismiss") or {}).get("closed"), row["answers_again"]), flush=True)
        if not row["answers_again"]:
            print("  !! still frozen - stopping so nothing piles up")
            break
    OUT.write_text(json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
