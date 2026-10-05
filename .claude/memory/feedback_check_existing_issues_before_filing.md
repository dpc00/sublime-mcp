---
name: check-existing-issues-before-filing
description: "Read the repo's open/closed issue list in a separate step BEFORE `gh issue create`; a duplicate was filed on RoadBookmarks 2026-09-25"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a3788352-49e6-4a4a-bacb-4c22de216ce3
  modified: 2026-09-26T01:58:57.172Z
---

Run `gh issue list -R <repo> --state all` (and search the key words) as its own step and read it before creating an issue; never put the list and the `gh issue create` in the same command.

**Why:** 2026-09-25 I filed stevengpa/RoadBookmarks#2 (SQLite folder never created) although #1 (opened 2026-09-12) already reported it; the list was printed in the same command as the create so I saw it too late. Had to close my own issue as a duplicate.

**How to apply:** for every finding, list existing issues first; if the finding exists, skip (or add a comment only if I have new evidence). Related: [[feedback_one_issue_per_finding]].

Third slip (later the same day, 1000ch/Sublime-svgo#33): I again ran `gh issue list` and `gh issue create` chained in ONE command (with `&&`, and a second package's list printed in between), so I saw the existing open #27 (same CR bug, filed 2023) only after creating a duplicate; fixed by commenting my evidence on #27 and closing #33. Chaining is the failure: ALWAYS a separate tool call for the list, read it, then create.

Second slip the same day (JunLang_package#1): I wrote "same rule at HEAD" without having read HEAD before filing (the grep was in the same command as `gh issue create`); HEAD had been rewritten and Package Control serves an older tag. Always read HEAD AND the served tag in a separate step first, and say which one shows the bug.
