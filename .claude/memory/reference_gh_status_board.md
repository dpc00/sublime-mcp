---
name: gh-status-board
description: "C:/Users/donal/tools/gh_status/pr_status.py lists Donald's open PRs, maintainer PR requests with no PR yet, and recent replies; run it so he never feels he is dropping the ball"
metadata:
  node_type: memory
  type: reference
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-02T13:47:24.191Z
---

2026-10-02 Donald: "just do whatever is appropriate and don't leave me thinking that I am dropping the ball and losing track of things."

**Tool:** `python C:/Users/donal/tools/gh_status/pr_status.py [days]` (needs `gh` logged in as dpc00; ~1-2 min). Prints: (1) every open PR of dpc00 with review state and who has the last word (">>> NEEDS YOU" = a maintainer replied after our last comment), (2) open issues where a maintainer asked for a PR and none of our PRs (open/merged/closed) mentions the issue, (3) replies on his issues in the last N days, (4) a MANUAL watch list at the bottom of the script (edit by hand: items the script cannot judge, e.g. design disputes).

**How to apply:** run it at the start of a session, after finishing a PR, and whenever Donald asks where things stand; summarise in 5-10 plain lines (what needs him, what needs me, what is only waiting on maintainers). Act on anything marked NEEDS YOU without waiting to be asked. Update the MANUAL list when opening/answering PRs. Complements [[project_monitor_maintainer_replies_via_github]] and [[feedback_report_bugs_never_patch_authors_code]].

**State 2026-10-02:** 21 open PRs, mostly waiting on maintainers. Merged today: LSP-Dart#18 (rwols). Open: LSP-kotlin#19 (rwols), TestExplorer#5 (IPWright83). SublimeLinter#1999: kaste criticised the delta rework ("worse than the one before", 09-30) and Donald's replies there were not technical; on 10-02 I posted a disclosed-AI comment asking kaste which design he wants (first commit's elect-level check vs the ignored_packages delta). Waiting on kaste.
