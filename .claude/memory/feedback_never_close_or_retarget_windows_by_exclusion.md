---
name: feedback_never_close_or_retarget_windows_by_exclusion
description: "2026-09-24 closed Donald's main ST window (and Claude's own tab) by picking a test window via \"id != window.id()\"; never select/close windows that way"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 165e315a-efcb-49b3-8b31-7320fbdb0c43
  modified: 2026-09-24T21:41:38.417Z
---

On 2026-09-24, during the package bug hunt, I chose the throwaway test window with `[w for w in sublime.windows() if w.id() != window.id()][-1]`, then called `set_project_data` and `close_window` on it. In eval_python, `window` is the *active* window, and after `new_window` that is the new one -- so I retargeted and closed Donald's real project window, killing the tab hosting this Claude session.

**Why:** cost the user their open window/tabs and the live session; same family as [[feedback_closing_own_tab_via_sublime_mcp]] and [[feedback_st_restart_vs_tab_close_risk]].

**How to apply:** identify a test window only by diffing window ids captured *before* `new_window` (`before = {w.id() for w in sublime.windows()}`), assert exactly one new id, and never call close_window/set_project_data on anything else. Prefer not to open windows at all: test in scratch views in the current window. Also: package-hunt method = install via Package Control and file GitHub issues for confirmed findings (user corrected a clone-only attempt) -- see [[project_gadzillion_package_test_campaign]].

**Recurrence, 2026-09-24 (same day, later):** while live-testing LSP-copilot's `.copilotignore` handling, called `sublime.active_window().set_project_data({...sandbox folder...})` directly on Donald's real active window to give the plugin's `CopilotIgnore` class real `window.folders()` to read -- again without capturing the prior `project_data()`/`folders()` first. Wiped his open project folders. Recovered only because ST's `Local/Session.sublime_session` (periodic backup, distinct from the more frequently-written `Auto Save Session.sublime_session` which had already been overwritten with the sandbox folder) still had the pre-test folder list, and Donald tolerated it a second time -- do not count on that.

**Stronger rule:** never call `set_project_data`, `set_folders`/`run_command('close_workspace')`, or anything else that mutates `sublime.active_window()`'s folders/project, full stop -- not even "temporarily, then restore." If a test needs a window with real `folders()` (e.g. testing project-scoped plugin logic), open a *new* window via `sublime.active_window().new_window()`... no: use the id-diff pattern above to get its handle, `set_project_data` only on that new window's handle, and close only that window afterward (again by the diffed id, never by exclusion). If a live window absolutely must be touched, capture `win.project_data()` and `win.project_file_name()` *before* the first mutating call, in the same tool call that does the mutation -- never in a separate step that could be skipped or reordered.
