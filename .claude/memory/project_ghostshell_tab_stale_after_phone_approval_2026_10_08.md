---
name: ghostshell-tab-stale-after-phone-approval-2026-10-08
description: 2026-10-08 Donald: approving a permission prompt with "yes" from the phone leaves the GhostShell Claude tab stuck showing the old prompt (no repaint); he reported it earlier; my screenshots saw it (a stale "Do you want to proceed?" shown for many minutes after the command had run)
metadata:
  type: project
---

**Symptom (Donald, 2026-10-08):** when he answers a permission prompt on the phone, the Claude tab in Sublime (GhostShell terminal) does not update and stays "stuck in the past". He had reported it before.

**Evidence from my side:** screenshots of the Claude tab at about 14:54 and 18:4x showed an old permission prompt (a PowerShell zip listing, "Command compiles and loads .NET code") while the commands had already returned their results; the status block and conversation text also lagged. The tab only repainted after later activity.



**FIXED (same day, GhostShell commit 0056c45, pushed):** the tab froze on an old screen while a text selection existed in the view. _do_render released a stale selection after 2.5 s but AiTerminalRenderCommand._run called _selection_paint_blocked again, which restarted the timer and blocked the frame, so no frame was ever painted. Evidence: the program's screen buffer was current while the view ended at an answered permission prompt, with a 130-character selection inside it (	erm._paint_block_since recent, _render_pending True). Fix: the valve now collapses the abandoned selection when it releases. Proved live: a 100-character selection placed in the view was cleared and new output appeared within about 5 s. The cast shows the program redrew after every approval (gaps of seconds), so the phone is not the cause by itself.

**STILL OPEN:** what creates the selection by itself (Donald: he is not touching the laptop, a line gets selected). Not found. Candidates not yet ruled out: my own tools (get_console visible copies via the keyboard and prints 'Copied N characters'; computer-use synthetic input), GhostShell's mouse tap/multi-click fallback, a remote client. To find it: log the stack/time when a non-empty selection appears in the Claude view (on_selection_modified) and correlate with the cast.


**Correction, 2026-10-09 (Donald):** the frozen-tab bug was traced to AgentIDE reacting to an instruction from Claude. The GhostShell render-timer fix (0056c45) targeted the wrong cause, so its revert (7d31560) was right, and the sublime_mcp.py console-click guard in 1.12.2 is only a safety guard, not the fix for this freeze.
