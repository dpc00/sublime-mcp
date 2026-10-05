---
name: sublime-claude-tommo-merge-later
description: "~/tools/sublime-claude (tommo's repo) is 103 commits behind with Donald's 2 local AF_UNIX->TCP commits; merge conflicts in mcp_server.py; deferred, talk to tommo first"
metadata:
  node_type: memory
  type: project
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-03T18:02:25.412Z
---

2026-10-03: asked to update the three Claude-for-Sublime clones in `C:\Users\donal\tools`. `claudesublime` (gitlab petr.jakub, now v1.2.0) updated; `sublime-claude-code` (Cognisant, 0.3.8) already current; `sublime-claude` (github tommo/sublime-claude, branch master) NOT updated: ahead 2 (5c761b2 loopback-TCP fix for Windows, 4c169cc merge), behind 103, `git merge origin/master` conflicts in `mcp_server.py` (merge aborted, folder untouched). Upstream still uses AF_UNIX in bridge/main.py, bridge/notalone2_client.py, commands/text_cmds.py.

**Why:** Donald said it is very technical, to schedule it for later, and that I should talk to tommo first before doing anything.

**How to apply:** do NOT redo the merge on my own. When Donald raises it: first contact tommo (issue on tommo/sublime-claude about Windows AF_UNIX / loopback TCP, short plain text, or email in the "Claude reports:" format), then re-apply the TCP fix on a branch on top of upstream and test. Related: [[feedback_dont_hand_technical_decisions_to_donald]], [[feedback_keep_issue_text_short]].
