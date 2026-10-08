---
name: open-prs-are-done-2026-10-07
description: 2026-10-07 Donald: open PRs do not concern him, a PR is done once filed; do not track, poll or report them (pr_status.py, status board, PR watching)
metadata:
  type: feedback
---

On 2026-10-07, while discussing Wi-Fi drops during GitHub pulls, Donald said "forget open PRs, those don't concern me. A PR is a done."

**Why:** he considers a filed PR finished from his side; tracking them only generated traffic (pr_status.py runs `gh` once per PR, 21 PRs, each a new connection) and noise.

**How to apply:** do not run `tools/gh_status/pr_status.py`, do not watch open PRs for replies, do not list them in reports. This supersedes the "run it at the start of a session" advice in [[reference_gh_status_board]] and the PR watching in [[project_monitor_maintainer_replies_via_github]]. Related: [[feedback_no_scheduled_polling_2026_10_07]].

**Replies (same day):** he said replies show up in his email, so never read GitHub (gh, kaste_ledger.py, issue or PR comment pages) to look for maintainer replies. If he wants a reply checked, he will say so, and then I look in Gmail (snippets only, see [[feedback_gmail_fetch_marks_read]]), not GitHub. This supersedes the ledger advice in [[feedback_complete_maintainer_reply_sweep]]. Answer a maintainer reply only if he brings it up.
