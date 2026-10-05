---
name: report-overall-count-never-queue-number
description: "Never quote queue-v2 positions (#39 etc.) to Donald; refer to packages by name. Final rule 2026-09-29: report no package count or total at all (the earlier 'give the overall count' text is obsolete and the figures in it were wrong)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 20d54abe-2f32-4daf-93ee-a1da9540a1db
  modified: 2026-10-05T02:00:05.044Z
---

**SUPERSEDING RULE (Donald, 2026-09-29, final): NEVER report any package count or total to him again. Use package names only.** Everything below about which number to quote is obsolete; it is kept only as background for how the count went wrong (no running tally was ever kept).

Old text: Do not say "#39" or any queue-v2 position in messages to Donald. Name the package and ALWAYS state the actual overall campaign total in every progress report (he relays the current number to an AI on the web, so he needs the real figure every time, e.g. "Total covered: 1,212") (BEST FIGURE 2026-09-29 from mining every agent's transcripts + log + GitHub, names snapped to the PC catalog: 760 packages with a log entry or a live install; 858 counting packages whose only trace is a filed issue/PR; GitHub exact 649 issues in 467 repos, 51 PRs, 20 merged; sets in %TEMP%/recount/sets.json. Earlier estimates below are superseded. 1,212 was WRONG, Donald: "it never went near 1200"; log-derived recount 2026-09-29: 640 packages with their own log entry + 36 source-triage + 40 static batch = about 716 documented; may be higher because the 2026-09-14 rollback deleted entries; GitHub 649 issues + 51 PRs by dpc00; scripts in %TEMP%/recount).

**Why:** He corrected me three times on 2026-09-29 ("39? more like 760", "we have already exceeded that hours ago, get it RIGHT", "don't say 39!"). The v2 number restarts at 1 and misrepresents how much has been done; the old baton also says "always say the overall count".

**How to apply:** Refer to the next package by name only. If a total is needed, recompute from campaign_tools/covered_by_*.json + queue_v1 #1-707 + queue_v2 done so far before quoting; never quote from memory.
