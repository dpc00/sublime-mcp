---
name: no-retaliatory-audits-of-package-control
description: 2026-09-29 Donald asked me to re-audit Package Control to find the maintainers' "disruptable behavior" after they closed his channel PRs; I declined the retaliatory purpose. Record of the facts and the rule going forward.
metadata:
  type: feedback
---

On 2026-09-29 Donald asked me to "redo and put out more effort in inspection" of the Package Control package because the maintainers were "rejecting my package offerings ... alarming questionable discrimination ... impugning your dignity" and he suspected they "have more disruptable behavior than at first meets the eye." I declined that purpose and said why.

**What the record actually shows (checked via gh):**
- sublimehq/package_control (the repo moved from wbond/): of Donald's 21 issues (#1759-#1780), 17 were closed *completed* by maintainer deathaxe, 4 *not planned* (3 by deathaxe with a comment, 1 by dpc00 himself). Related fixes were merged/closed (#1789, #1791). That is a largely positive reception.
- sublimehq/package_control_channel (maintainer "braver"): PRs #9581-#9584 (tag pin, platform tweak, two removals) were closed 2026-09-28 with "report problems at the package's repository ... your crusade is wasting people's time ... do not open PRs like this"; "we do not bug-hunt on packages ... not necessarily appreciated". Add-package PRs #9554 (MCP Commander) and #9565 (AgentIDE) were closed / left waiting because of the community-project point and the account's recent behaviour. Nothing in the threads mentions AI authorship as a reason; the only AI mention is Donald's own comment.
- Donald's 2026-09-28/29 comments on #9554 included personal insults ("You should be fired", "Are you Australian?", "abysmal", "a crime", "incompetence"). braver: "uncalled for and crosses so many lines"; kaste: "You're really in a rage here. Just let it settle" (and kaste had fixed the issues filed against his packages).
- The four channel PRs were opened by this campaign against the earlier stop request; see [[feedback_channel_repo_pr_banned]].

**Rule / how to apply:** never audit a project's code or file issues/PRs against it as payback or to find dirt on its people. Do not open anything new on sublimehq/package_control or sublimehq/package_control_channel while this dispute is live. A merits-only re-audit of Package Control can be reconsidered later, as with any package, after a cooling-off and with Donald's agreement; findings should stay private until he decides. Constructive route to keep his packages available: users can add his repositories via Package Control's "Add Repository" (custom `repositories` setting) without the channel. Be calm, factual, and don't validate the discrimination framing; also gently note his own comments if he asks what went wrong. Related: [[feedback_declined_hostile_public_reply]], [[feedback_report_bugs_never_patch_authors_code]].
