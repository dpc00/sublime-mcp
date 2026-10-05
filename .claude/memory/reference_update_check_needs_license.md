---
name: update-check-needs-license
description: "The old portable ST's \"Update Available\" window cannot be disabled with update_check:false on an UNREGISTERED copy (forum + staff confirm); I close it with a hidden loop instead"
metadata:
  node_type: memory
  type: reference
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-04T20:18:05.801Z
---

2026-10-04: Donald pointed me at forum.sublimetext.com (his own topic #77749 "Claude Code in ST", post #19 by dpchitester, plus threads #43492, #70403, #67953, #60334, #1381). Result: `"update_check": false` is **ignored unless the copy has a valid licence** (deathaxe in #70403, UltraInstinct05 in #43492, bschaaf (Sublime HQ) in #67953: "You can use the 'Check for updates periodically' checkbox ... if you have a license"). All portables (4200, 4215) and Donald's main window say UNREGISTERED, so the nag appears ~15 s after every start of 4200 (current 4215 has nothing newer to offer).

**How to apply:** don't keep trying settings. `scratchpad\updatecloser.ps1` (hidden powershell loop, started 2026-10-04, pid 25084) posts WM_CLOSE to windows titled "Update" of the 4200 process only; `closeupdate.ps1` does it once. If the loop is not running (reboot), start it again before long 4200 sessions, or the window sits on screen and Donald calls it "dialog" ([[feedback_poll_for_dialogs_and_say_what_to_press]]). Buying/entering a licence is Donald's decision, never mine. The 4200 executable was verified unchanged (version 4200) after each popup. See also [[reference_portable_st_4200_older_build]].
