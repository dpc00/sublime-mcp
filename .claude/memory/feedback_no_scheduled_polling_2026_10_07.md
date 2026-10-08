---
name: no-scheduled-polling-2026-10-07
description: 2026-10-07 Donald had the half-hour check removed entirely; too much network traffic, he cut his Wi-Fi. No CronCreate jobs, no scheduled GitHub/Gmail/forum polling
metadata:
  type: feedback
---

On 2026-10-07 the half-hour job fired during a Limitcode retest. `pr_status.py` ran twice (it queries every open PR, 21 of them), plus `gh api` and forum calls, on top of the Limitcode test traffic. Donald said "killed wifi", then "too much traffic", then "eradicate it entirely, don't kill my wifi".

**Update, same day:** he said it has killed his Wi-Fi "more than once" and that "GitHub is killing my wifi". Cause not confirmed (adapter showed Up afterwards, no system-log events). Treat any burst of GitHub calls as a risk: no `pr_status.py` or looped `gh` calls unless he asks, and then one at a time.

**Why:** his connection is limited (see [[feedback_no_retests_no_big_downloads]]); polling every 30 minutes is too much.

**How to apply:** do not create any recurring job at session start. The "Half-hour check" section was removed from `C:\Users\donal\.claude\rules\repo-memories.md`. Check PRs, mail or the forum only when he asks, one call at a time. This supersedes the polling advice in [[project_monitor_maintainer_replies_via_github]]. Never run `pr_status.py` twice in one pass.
