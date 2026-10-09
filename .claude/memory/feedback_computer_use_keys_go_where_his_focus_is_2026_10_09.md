---
name: computer-use-keys-go-where-his-focus-is-2026-10-09
description: 2026-10-09: computer-use keys typed into the Claude tab because Donald's focus was there answering my permission prompts; not a sublime-mcp gap; prefer sublime-mcp tools, or move Claude to Windows Terminal
metadata:
  type: feedback
---

While Claude runs inside a Sublime tab, Donald has to keep his focus on that tab to answer permission prompts. Those prompts appear AFTER I have already chosen a computer-use action, so I cannot check focus first and have it stay true. Result on 2026-10-09 (FTPSync install): `press_key` was refused five times ("user input detected"), then `type_text "FTPSync"` landed in the Claude prompt line instead of the Install Package picker. I blamed sublime-mcp for it in the log and he corrected me.

**Why:** the focus is his, not a property of the tools. Do not log it as a sublime-mcp gap.

**How to apply:**
- For Package Control pickers use `run_command install_package`, then `get_quick_panel` (with a filter in mind: the list is 4718 items) and `pick_quick_panel` by text. No computer-use needed. See [[audit-installs-must-follow-user-flow-2026-10-07]] for the user-flow rule.
- When keyboard-driven GUI work is unavoidable, have Claude moved to Windows Terminal first ([[native-dialog-tests-from-windows-terminal-2026-10-09]]); then the active Sublime view stops flipping to the Claude tab too (commands on "the current file" hit the Claude tab until then).
- If text ends up in the prompt line, tell him and clear it; never send Return into it.
- Same cause, other direction (2026-10-09, LSP-pyright test): `open_file`, `new_file`, `move_to_group` and similar move the keyboard focus to the new tab, so Donald's Enter presses for my permission prompts land in that file (three newlines ended up in a test file). While Claude runs inside a Sublime tab, do not open, create or move tabs; or return focus at once with `run_command focus_group {group: 0}`. For anything that needs tabs (editor tests), ask him to click "Move to Windows Terminal" first.
- Keep tool output small: `get_sheets` and an unfiltered `get_quick_panel` each dumped tens of KB.
