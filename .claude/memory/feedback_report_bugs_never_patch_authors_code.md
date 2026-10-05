---
name: report-bugs-never-patch-authors-code
description: Audit = issues by default. The 2026-10-02 policy of fulfilling every maintainer PR request was SUPERSEDED on 2026-10-03 by his stock reply (see feedback_stock_reply_to_pr_requests); unrequested patches are still not done
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-05T01:59:12.532Z
---

Default for the package audit: file issues only; do not open PRs or patch authors' code (Donald: too risky).

**Exception (2026-09-25):** several maintainers replied on issues asking for PRs (colinta on SublimeSimpleMovements#4 "do you have time to provide any PRs?", jfcherng on ST-WindowsContextMenu#4 "Could an AI file a PR?", michaelblyons on ExtractSublimePackage#6). Donald said "do whatever they desire", so for THOSE maintainers/repos I may open small, minimal PRs (fork under his account, one PR per issue, link the issue) and retest a maintainer's fix when asked (alimony asked to retest sublime-sort-numerically 1.0.7).

**Why:** maintainers asked directly; the risk Donald worried about is unrequested patches.

**How to apply:** only for a maintainer who explicitly asked; keep the diff tiny and verified by a live test; never for repos that didn't ask. Related: [[feedback_one_issue_per_finding]].

**2026-09-28 clarification:** Donald: "that rule doesn't always apply, all the time. It is a general rule, because I don't want to tangle with programmers that I've never met." So the rule's real scope is "stranger authors" -- it's a risk-avoidance default, not an absolute ban. It does NOT rigidly apply when Donald knows/has a relationship with the author, or he explicitly says to go fix something himself this session (separate from the maintainer-asked exception above). For the vast majority of campaign packages (authors Donald has no relationship with), keep defaulting to issue-only -- when in doubt, that's still the safe read. Don't assume this comment is blanket permission to start patching stranger repos; it's context for judgment, not a policy flip.

**2026-10-02 policy (superseded on 2026-10-03 by [[feedback_stock_reply_to_pr_requests]]):** Donald: "my policy now is to try to fulfill them" (maintainers' requests for PRs). Find them in his Gmail (GitHub notification mails, though he deletes some) AND with `gh search issues --author dpc00` + reading non-dpc00 comments for "PR/patch/try a fix". Many from 09-29/30 were already done (SublimeLinter-* PRs merged; kaste re-did tslint/cppcheck/javac himself). Done 2026-10-02: sublimelsp/LSP-Dart#17 -> PR #18 (rwols asked). I wrongly told Donald it was "the first time a maintainer asked directly" - I had not re-read this file; read it before claiming anything about PR history. He said there were TWO requests; I found only one outstanding, ask him for the other if still unknown.
