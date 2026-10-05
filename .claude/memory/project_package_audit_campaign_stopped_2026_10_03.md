---
name: package-audit-campaign-stopped-2026-10-03
description: "Donald stopped the Sublime package audit on 2026-10-03 and restarted it the same day (\"continue with next package\"); from 2026-10-04 he wants it to run unattended. Read the whole note: the 'How to apply' paragraph is the original stop text and is superseded"
metadata:
  node_type: memory
  type: project
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-05T01:58:58.957Z
---

2026-10-03 Donald said he is sincerely tired of the package audit: the packages are ones he has never heard of, never uses, would not miss; he is in trouble with the Package Control people; it does not help eliminate the bugs and unwanted traits of GhostShell and sublime-mcp; every bug found in his own projects makes him think he must ship a release, and he does not want to ship a buggy or incomplete product (he already withdrew sublime-mcp once over the backlash about shipping a bad product).

**RESTARTED later the same day (2026-10-03, after he got home from the store request):** Donald said "continue with next package". The audit runs again, one package at a time, ONLY under his new rules: never use Bash or other shells, ask before any download over about 50 MB (log "needs big download, not tested" otherwise), no retests on request, never offer PRs in issue text, short plain issues, no replies to GitHub mail, keep tool output small. LSP-addon-breadcrumb was done first (no defect; symbol part skipped, needs a server download). If he again says stop, stop.

**Why:** the campaign was my method for finding bugs, and it has become pure cost to him (mail chime, retest requests, downloads on a limited connection, standing with the Package Control maintainers).

**Superseded by the restart above and by [[feedback_run_unattended_dont_ask_to_continue]] (2026-10-04); on 2026-10-05 the audit was running again at his request. The rules in the restart paragraph were later refined too: download limit and deferred list per [[feedback_defer_big_installs_dont_skip]], and PowerShell scripts with plain descriptions per [[feedback_permission_prompt_plain_english]] in place of "never use shells".** Original stop text follows:

**How to apply (original, 2026-10-03 morning):** no new package installs/tests/issues/PRs for the campaign; a bare "continue" does not restart it. Do not resume the queue at LSP-addon-breadcrumb / Quote With Marker. Existing open PRs and issues stay as they are; answer a maintainer only if Donald asks. Never suggest that a bug in GhostShell or sublime-mcp needs a release; fixes can stay local and unreleased, and there is no obligation to ship. If he wants work now, it is on GhostShell and sublime-mcp, on his terms. Supersedes [[project_package_audit_baton]] and [[project_campaign_queue_order_flaw]]. See also [[feedback_no_retests_no_big_downloads]] and [[feedback_no_retaliatory_audits_of_package_control]].
