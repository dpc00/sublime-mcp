---
name: console-full-read-fix-2026-10-03
description: "get_console mode=visible (full console) was broken: it sent Ctrl+A/Ctrl+C to ANY window titled \"Sublime Text\" incl. the Claude tab; fixed 2026-10-03 in sublime_mcp.py (own-process windows only + focus guard + focus on worker thread). Tee log was a rejected workaround."
metadata:
  node_type: memory
  type: reference
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-05T01:52:41.423Z
---

Donald wants the console read IN FULL via the real sublime-mcp functions, never a screenshot or a tee workaround ("crude workaround"; the tee plugin was deleted). See [[feedback_prioritize_dialogs_console_errors_during_install]].

**Root cause found:** `_capture_console_win` in `sublime_mcp.py` searched EVERY window system-wide titled "Sublime Text" and took the foreground one, then did SetForegroundWindow + click + global SendInput Ctrl+A/Ctrl+C. With the Claude tab's window in front, Ctrl+C reached the Claude TUI. This could explain some "false interrupt" / false Escape stops while a capture was running; it cannot explain interrupts that happen at the permission prompt before any code runs. The cause of those is unknown (the user reports pressing no key; computer-use reported an Escape press on 2026-10-05).

**Fix (committed and pushed as b4fe787 on 2026-10-04; it was uncommitted on 2026-10-03):** only windows owned by this Sublime process (`os.getpid()` or parent `os.getppid()`, because plugins run in plugin_host); `own_window_has_focus()` guard before every click/key, abort with no input sent if not focused; `force_focus` runs on a worker thread (doing ShowWindow/SetForegroundWindow on the plugin-host main thread deadlocked the plugin host, heartbeat likely_wedged). Proven on 4215: complete:True, 3042 chars, no crash, nothing leaked to other windows. NOT yet compared line-by-line with Donald's screen.

**Not possible via commands:** window/application `select_all`+`copy` do not reach the console panel; posted Ctrl keys (PostMessage) do not register. Real SendInput is the only way.

**4200 portable:** package folder `D:\st_portable_4200\Data\Packages\MCP Commander` is a real folder with `.python-version` 3.8, a shim `sublime_mcp.py` that exec()s the repo file, and a junction `lib` -> repo `lib` (repo `.python-version` is 3.14, no 3.14 host on 4200; symlinks need admin). Ports in User\MCP Commander.sublime-settings (4200: 9522/9520; 4215: 9512/9510). Project .mcp.json has `sublime-mcp-portable-4200` (9522).

**Official confirmation (2026-10-04):** sublimehq/sublime_text#2929 (closed): maintainers say the console is NOT an output panel, `find_output_panel('console')` returning None is correct; wbond: exposing it is not simple because modifying the console can deadlock. Open feature request #2984 "Ability to query for the console's view object ... its buffer read" (since 2019), also #299 no command to clear console. Binary scan of 4215: only console command is `console_python_version`; view-id sweep and 6 panel-lookup name variants found nothing. So keyboard copy (click + Ctrl+A/Ctrl+C) is the only way to read it. Console buffer is limited (#1416 mentions 3000 lines). Ghostshell "Switch Panel" only calls show_panel.

**get_console(captured) only hooks the 3.8 host's stdout: it silently MISSES everything printed by Python 3.3-host plugins** (seen with Python Debugger's "Started Debugging"). Only the visible capture shows those. If a modal prompt/input panel is open (e.g. the debugger's), the visible capture's marker check refuses (focus is in the input field).

**Current design (sublime_mcp.py, committed in b4fe787; `_capture_console_win` starts around line 1095, which moves when the file changes):** get_console(visible) only runs if this Sublime window is in front and its title matches the active tab; force_focus=true raises it via minimize+restore (crashes a portable ~1 in 6, worse with many packages loaded); a printed marker line proves the copy is the console. Measured crash rates per Win32 call are in .package_skill_test_log.md. Closest upstream hit for the crash: #1950 (IME focus crash, fixed in 3200), not the same.

**Crashes:** sublime_text 4200 and 4215 crashed 4 times on 2026-10-03 (CoreMessaging.dll, 0xe0464645) around focus/console actions; not reproduced in later bisect trials on 4215. Cause unknown.
