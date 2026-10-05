---
name: read-popups-with-screenshot-and-postmessage
description: "Autocomplete/popup contents CAN be read: mcp__screenshot__screenshot_window plus PostMessage VK keys; never say \"couldn't read the popup\" and skip"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-05T01:54:38.569Z
---

On 2026-10-03 I wrote "couldn't read the popup" after LaravelTestingCompletions and moved on; Donald said he could read it, so I should be able to, and told me to retest. The retest found a real defect (completing right after `$this->` inserted a second `$this->`).

**Why:** a popup is visible UI, so a screenshot reads it; skipping an unverified suspicion hides real bugs.

**How to apply:** open the file, call `view.run_command('auto_complete')`, bring the window front with scratchpad front.py, wait ~2 s, then `mcp__screenshot__screenshot_window` (title match) to read the list. Scroll the popup by posting keys to the ST hwnd with scratchpad keys.py (`PostMessageW(hwnd, WM_KEYDOWN, VK_DOWN)`; `tab` accepts the entry), then read the buffer text through eval_python. `view.run_command('move')` does NOT drive the popup (it closes it). Scope: this worked for the autocomplete popup. On 2026-10-05 a `PostMessage` `Return` aimed at an open *quick panel* (CiteBibtex) went to the editor instead and inserted newlines, so do not assume the same route works for quick panels. Related: [[feedback-poll-for-dialogs-and-say-what-to-press]].
