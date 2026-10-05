---
name: end-test-agent-tabs
description: End every test-agent ai_terminal tab I open as soon as its result is read; never leave finished agents piled up
metadata:
  node_type: memory
  type: feedback
  originSessionId: 80ae38f1-7ab9-4aa3-be87-7693e48d1b6b
  modified: 2026-09-26T21:19:24.223Z
---

When I launch a fresh agent (omp etc.) in an ai_terminal tab for a test, end that tab's session and close it as soon as I have read its result.

**Why:** 2026-09-26, Donald: "not cleaning up old agents" — four finished omp tabs had piled up in the right-hand pane.

**How to apply:** `run_command ai_terminal_end_session {"group": G, "index": I}` targets one specific tab (it is a WindowCommand taking group/index; it does not use the active tab). First list tabs and confirm profile and cwd, end the highest index first so indices stay valid, and re-list afterwards to confirm the Claude tab is still active. Never use kill_session/close_file without group/index (they act on the active tab, which is my own). See [[feedback_never_close_or_retarget_windows_by_exclusion]] and [[feedback_junk_tabs_other_group]].
