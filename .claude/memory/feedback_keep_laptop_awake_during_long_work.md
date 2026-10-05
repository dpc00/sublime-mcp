---
name: keep-laptop-awake-during-long-work
description: "Donald lies down while long campaign work runs and the laptop sleeps, suspending the session; he wants a wake-lock so work continues"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-05T02:00:09.492Z
---

On 2026-10-02 Donald lay down, the laptop went to sleep and the session was suspended ("don't let Windows put you out of commission"). He wants long-running work to keep going.

**Why:** the package campaign runs for hours unattended; sleep suspends me and my background waits.

**How to apply:** at the start of long unattended work, keep a wake-lock running: a script calling kernel32 `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)`, re-asserted every 30 s. It existed as `scratchpad/keep_awake.py` (session-temporary) and later as `C:\Users\donal\tools\keep_awake.ps1`; the 2026-10-02 note said to start it with Bash `run_in_background`, but Bash is no longer used (see [[feedback_never_use_bash_tool]]), so start it with PowerShell in the background instead. I did not check on 2026-10-05 whether one is currently running. It changes no power plan, lasts only while the process lives (dies with the session) and does not stop lid-close, the power button or an explicit Sleep. Tell him that limit. Check it is still running if the session was interrupted. Do NOT run `powercfg /requests` or similar unasked: he declined that check once.
