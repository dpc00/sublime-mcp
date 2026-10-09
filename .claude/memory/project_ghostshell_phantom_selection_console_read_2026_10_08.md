---
name: ghostshell-phantom-selection-console-read-2026-10-08
description: 2026-10-08 the "selecting a line by itself" freeze of the Claude tab: Donald says it happens when I read the console; evidence, the sublime-mcp fix, what is still unproven
metadata:
  type: project
---

2026-10-08. The Claude tab froze twice (20:51:00 and 20:58:58) with the same stray selection: row 329, columns 0 to 24, the text " Do you want to proceed?" (the permission prompt line). A watcher (eval_python thread, `scratchpad\watch2.py`) logged it; the command history held only `ai_terminal_render`; the second time another tab was active. GhostShell's code never creates a non-empty selection (it only adds empty carets), so the range comes from an input event.

Donald: "Happens when read console." `get_console` in visible mode (`sublime_mcp.py`, `do_click_focused`) sends a real click at window-bottom minus 80 px, then Ctrl+A and Ctrl+C. The click assumes the console panel is open there; if it is not, it lands in the Claude tab's last rows, where the permission prompt sits. With `sublime.log_input(True)` the console showed `command: drag_select {x 738.5, y 763.5}` then `key evt: ctrl+a`, `ctrl+c` for each capture. The 20:51 and 20:58 times did not match a capture to the second, so the link is Donald's observation plus this mechanism, not a proven trace.

**Correction, same evening:** a third occurrence (21:01:12, row 329 again, 24 chars) was logged about a minute BEFORE the next console capture (21:02:21), so reading the console does not explain all of them. All three coincide with a permission prompt being on screen, and the selected text is the prompt line itself. Real cause still unknown (suspects: something that acts when the prompt appears, an outside UI-automation client, or the phone relay). The fix below is a hardening of the console capture, not a proven cure.

**Donald, later the same evening: "Always after reading console."** He sees the freeze every time after a visible read, whatever my timestamps say. From 21:10 I read the console only with `mode=captured` (no click, no keys). Captured mode can miss Sublime's own load errors, so say so when a verdict relies on it.

**Report from Donald, 21:5x (not a request):** he pressed Ctrl+Tab in Sublime and a computer-use permission prompt appeared in the Claude tab, though I had no computer-use call pending. So keyboard input to the Claude tab can raise or leave behind prompts; worth checking next time the tab freezes (what key was pressed just before).

**Evidence at 21:34 (4 occurrences: 20:51:00, 20:58:58, 21:01:12, 21:32:21):** each time the selection is the first line of the permission prompt (" Do you want to proceed?", row 327 or 329, columns 0 to 24); twice the active tab was NOT the Claude tab (so no mouse or key went to it); the command history held only ai_terminal_render; there is no code path in GhostShell that creates a non-empty selection (checked every sel/add/move call). Wrapping GhostShell's on_selection_modified at runtime does not work (Sublime binds listener methods at load), and a Python stack would not show the origin anyway. Not tried: log_commands (the render arguments make it flood the console). Untested hypothesis: an outside UI Automation client (computer-use-mcp, reconnected at 21:2x) touching the Sublime window when a prompt appears; Donald saw a computer-use prompt after pressing Ctrl+Tab. Experiment for him: disable computer-use-mcp for an hour and see whether the freezes stop.

**Screenshot at 21:43:** a PowerShell permission prompt ("Command contains expandable strings with embedded expressions") was on screen with the line "Do you want to proceed?" highlighted and Sublime's status bar reading "24 characters selected", with nothing sent by me. Also checked `_selection_paint_blocked`, `_selection_is_spurious`, `_clear_view_selection`: they only clear or test selections. So the range is created by something that acts when the prompt is drawn (cursor sits right after the "?" at column 24; selection runs from column 0 to the cursor). Next idea: check what GhostShell does with the terminal cursor position for this row (caret placement with an extend/anchor), and whether Claude Code's own TUI draws this row with a selection attribute.

**Stopgap from 21:53 (not a fix, lives only in the running Sublime, gone after a restart):** an eval_python thread (`scratchpad\watch3.py`) clears the selection only when it is exactly the 24-character text " Do you want to proceed?" starting at column 0 in an ai_terminal tab, and logs `AUTO-CLEARED` with the time to `scratchpad\watch2.log`. Other selections are never touched. Occurrences before that: 20:51:00, 20:58:58, 21:01:12, 21:32:21, 21:43:21, 21:50:59. Checked and ruled out: AgentIDE (selects text in opened files only), sublime_mcp `select_lines` (selects whole lines including the newline).

**Fix made (sublime_mcp.py):** record the active view's selection before a visible capture; refuse to click unless `window.active_panel() == "console"`; put the saved selection back at the end. Edited in a scratch copy, compiled, then applied.

**Why:** the stale 2026-10-08 "FIXED" paragraph in [[ghostshell-tab-stale-after-phone-approval-2026-10-08]] (clear the selection in GhostShell) was reverted: it would erase a user's real selection.

**How to apply:** prefer `get_console mode=captured` when the output is enough; use visible mode only when needed. If the tab freezes again, clear the stray selection with eval_python (`v.sel().clear()`), and read the console input log (`sublime.log_input(True)`, never `log_commands`: the render arguments flood the console with 600 KB).

**Correction, 2026-10-09 (Donald):** the frozen-tab bug was traced to AgentIDE reacting to an instruction from Claude. The GhostShell render-timer fix (0056c45) targeted the wrong cause, so its revert (7d31560) was right, and the sublime_mcp.py console-click guard in 1.12.2 is only a safety guard, not the fix for this freeze.
