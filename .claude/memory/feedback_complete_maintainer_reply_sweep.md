---
name: complete-maintainer-reply-sweep
description: "Donald cannot verify I read ALL maintainer replies and will not check each thread by hand; run the full ledger (tools/gh_status/kaste_ledger.py) and report every reply with answered/not-answered, never just the one he mentions"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-02T20:23:21.112Z
---

2026-10-02: kaste (and others) reply on many threads at once (ghc #8/#9, ruff #5, quick-linter-js #2, erblint PR, ...). Donald: "I can't confirm that you have read all the emails... I do not want to try to manually confirm every issue he has raised." When he says "X has an email" I answered only that one and missed the others.

**Why:** the sticking point is trust that nothing was missed; he will not audit it himself.

**How to apply:** when he mentions a maintainer reply (or at least once per session), run `python C:/Users/donal/tools/gh_status/kaste_ledger.py <since> [login]` (lists every comment/review/merge by others on threads dpc00 is in, with ANSWERED / NOT ANSWERED) and report the complete list, not one thread. Read comments via `gh`, not Gmail `get_message`/`get_thread` (marks mail read, see [[feedback_gmail_fetch_marks_read]]). Related: [[reference_gh_status_board]], [[project_monitor_maintainer_replies_via_github]].

**Attachments:** GitHub's reply-by-email drops attachments (Donald's 2026-10-02 email to package_control_channel#9554 carried 2 files; kaste saw none). Paste text inline, or use the GitHub web comment box, or a gist; do not rely on email attachments. The channel repo is off limits for me anyway ([[feedback_channel_repo_pr_banned]]).
