---
name: portable-st-4215
description: "a signed portable Sublime Text 4215 lives at D:\\st_portable_4215 for testing new builds without touching Donald's real 4200 install"
metadata:
  node_type: memory
  type: reference
  originSessionId: a3788352-49e6-4a4a-bacb-4c22de216ce3
  modified: 2026-10-05T01:52:58.324Z
---

Donald is afraid to update his real ST (4200, customised with GhostShell/MCP packages), so on 2026-09-26 I set up a portable ST 4215 at `D:\st_portable_4215` (official zip, Authenticode-verified Sublime HQ, own `Data` folder via `Data\KEEPME`). When first set up it had no Package Control and no MCP bridge and was used for one-off checks (e.g. a probe plugin that writes JSON to `D:\st_portable_4215\results` and calls `sublime.run_command("exit")`). Since then (checked 2026-10-05) it has Package Control and the MCP Commander package, and is kept running and driven over its HTTP port, as described under "Persistent instance" below.

**Why:** lets me answer "does it still happen on the newest build?" (BuildSock `AF_UNIX` on Windows: still missing on 4215, Python 3.14.6) without risking the live session or his Data folder.

**How to apply:** launch with `Start-Process ... -WindowStyle Minimized` and only address processes whose `Path` is `D:\st_portable_4215\sublime_text.exe`; remove any probe plugin afterwards (a probe that quits ST would quit every launch); the live install under `%APPDATA%\Sublime Text` is the user's real editor, so test things in the portable instead. At the time the user wanted to be asked before anything visible was launched; later (2026-10-05) he asked for the test window to be brought to the front when needed. Related: [[feedback-st-restart-vs-tab-close-risk]].

**Python hosts (verified 2026-09-25):** in the portable 4215 a package with no `.python-version`, one with `3.3` and one with `3.8` ALL run on Python 3.14.6 (probe plugins wrote `sys.version`). So 4215 results reflect 3.14 (removed stdlib APIs such as `plistlib.readPlist` fail there), whereas Donald's real 4200 still uses the 3.3/3.8 hosts. When filing "fails on new builds" bugs (e.g. poucotm/Log-Highlight#52) say build 4215/Python 3.14, not 4200. Job stderr can be captured by swapping `sys.stderr` in the driver job (works, all plugins share the host).

**Persistent instance (2026-09-26, Donald's idea):** sublime-mcp is copied (not junctioned) into `D:\st_portable_4215\Data\Packages\MCP Commander` with `User\MCP Commander.sublime-settings` = `{"mcp_port": 9512, "http_port": 9510}`; the portable instance is kept RUNNING (Donald: "just keep the instance running"). Drive it with `POST http://127.0.0.1:9510/<tool>` (e.g. `/eval_python` body `{"code": "..."}`) instead of one-shot jobs; its Python is 3.14.6. The old `zz_driver` job plugin was moved to `D:\st_portable_4215\disabled\zz_driver` (renaming it inside Packages does NOT disable it: it still loaded and quit ST after ~14 s). Use scratch views only, never edit real files there (save prompt blocks exit). Kill only the process whose Path is the portable exe.
