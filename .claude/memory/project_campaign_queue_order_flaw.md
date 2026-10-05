---
name: campaign-queue-order-flaw
description: RESOLVED 2026-09-29 -- the old audit queue was sorted by last-modified, so the campaign drifted into abandoned packages; rebuilt by installs (campaign_tools/queue_v2_by_installs.json). Campaign still paused until Donald says resume.
metadata:
  type: project
---

Found 2026-09-29 when Donald asked "are we sorting by # of installs? ... we are picking dogs." `queue.json` (3,911 entries) is ordered by `last_modified` descending: #700 is a 2021 package, #1000 2019, #3000 2014. Sorting by installs was never done. Of the top 300 by unique_installs (packagecontrol.io/browse/popular.json?page=N): 11 done, 108 still ahead of #708 (ConvertToUTF8 = #709, 1.38M installs), 31 audited in the earlier phase, 73 only mentioned in the log, 77 never queued or mentioned (SublimeCodeIntel 1.86M, Color Highlighter 1.26M, many themes/snippet packs). Only 23 of the top 100 have a queue position <=707 or their own log entry.

**Why it matters:** low-install, long-abandoned packages get no response (475 of our 508 open issues have zero comments) and yield little value; popular, maintained packages are where fixes and credit come from.

**How to apply:** before resuming the campaign, rebuild the queue ranked by unique_installs (prefer packages with a live maintainer, last commit within ~3 years; deprioritise pure themes/colour schemes/snippet packs), and skip anything already covered by the log. Donald has paused the campaign at #708 and said he sees no point continuing on the current list; get his go-ahead on the new ordering first. Related: [[project_package_audit_baton]].

**RESOLVED 2026-09-29:** Donald said 'do it, fix it up'. New queue: `C:/Users/donal/projects/sublime-mcp/campaign_tools/queue_v2_by_installs.json` (3,782 packages: tier A 273 maintained plugins by installs, B 2,435 older plugins, C 1,074 themes/snippets/syntax), built by `campaign_tools/build_queue_by_installs.py`; old queue kept as `queue_v1_by_recency.json`. Emmet, SideBarEnhancements, BracketHighlighter, WakaTime etc. are EXCLUDED because the early phase already audited them (Donald pointed out WakaTime and SFTP are in the logs; the log uses several formats, so ALWAYS grep the whole log for a package name and read every hit before starting it). Not resumed yet: wait for Donald's go.
