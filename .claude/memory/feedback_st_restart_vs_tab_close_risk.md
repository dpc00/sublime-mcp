---
name: st-restart-vs-tab-close-risk
description: Restarting sublime_text.exe is low-risk; closing/replacing the ai_terminal tab hosting the live coordinating session is the real danger
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 275b0307-2424-404e-9e00-6c7593435096
  modified: 2026-10-05T01:51:57.939Z
---

Killing and relaunching `sublime_text.exe` itself carries little liability — GhostShell's detachable-broker architecture is designed so sessions survive an ST process restart and reattach. The real, substantial liability is any action (spawn, cleanup sweep, view.close()) that closes or replaces the specific ai_terminal tab currently hosting the live coordinating Claude session — if that tab's underlying broker/child process actually dies (not just detaches), the running conversation is gone with no recovery.

**Why:** During a 2026-09-15 GhostShell menu-deadlock investigation, repeated `Stop-Process -Name sublime_text.exe -Force` restarts were treated as uniformly risky, but the actual loss event was a Claude tab's broker no longer being registered/running afterward (confirmed via `_registered_brokers()` showing only one Claude entry post-restart, no orphaned broker process anywhere). The user corrected the risk model directly: don't lump "restart ST" in with "close tabs" as equally dangerous — they are not.

**Caveat (added 2026-10-05):** the 2026-09-15 finding in [[feedback_closing_own_tab_via_sublime_mcp]] is that the bare Claude Code CLI exited by itself when its terminal tab was detached, whereas `omp` survived. So "a restart is low risk because sessions reattach" is the user's stated view and holds for portable test instances; it was NOT verified for a restart of the Sublime that hosts a live Claude Code tab.

**How to apply:** Restarting a portable test `sublime_text.exe` for testing/diagnostics is fine on its own. Before or after any restart, do NOT run bulk `_spawn(...)` calls, view-cleanup sweeps, or anything touching tab identity for the profile likely hosting the current coordinating session (commonly "Claude") without first confirming which broker pipe_name/child_pid that session is on, so continuity can be verified afterward. If unsure which tab hosts the live session, treat every close/spawn touching an ai_terminal view as the dangerous action, not the process restart.
