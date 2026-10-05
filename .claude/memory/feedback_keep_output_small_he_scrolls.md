---
name: keep-output-small-he-scrolls
description: 2026-10-03 Donald scrolls a lot to read my oversize responses and junk tool output; the small viewport shifts in GhostShell are his own scrolling
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-03T18:49:03.369Z
---

Donald said he scrolls a lot "to put everything in view or to read your oversize response or junk tool output". So the 200-500 px viewport shifts with no GhostShell call in the recorder are his deliberate scrolling, not a bug, and the tab growing by tens of thousands of characters comes largely from my own output.

**Why:** big tool outputs (whole PATH dumps, JSON blobs, full console logs, long file listings) and long answers push the tab up and make him hunt for the command line.

**How to apply:** cap every tool output (`| head`, `| tail`, `cut -c`, `--jq` filters, grep the one line); never print environment/PATH/secrets; read big files in slices; keep replies to a few short lines; put detail in a file, not the chat. Related: [[feedback_plain_short_answers_no_menus]], feedback_ghostshell_follow_patch (note not found; see project_ghostshell_follow_patch_2026_10_03 in the GhostShell repo) (see [[project_ghostshell_follow_patch_2026_10_03]]).
