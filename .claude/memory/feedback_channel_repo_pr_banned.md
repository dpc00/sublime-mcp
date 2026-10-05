---
name: channel-repo-pr-banned
description: "sublimehq/package_control_channel maintainer explicitly told us to stop opening PRs there -- hard stop, not a preference"
metadata:
  type: feedback
---

Never open another PR against `sublimehq/package_control_channel` (or its `wbond/package_control_channel` redirect).

**Why:** 2026-09-28 -- maintainer "braver" closed all 4 channel PRs from this campaign (Chromeless tag-pinning #9581, UVMLog platforms #9583, October Twig removal #9582, Old-Style ASCII Property Lists removal #9584) and wrote on #9584: "Please report problems with packages at their repository. We don't have the time or interest to verify your claims and then take action on them... your crusade is wasting people's time... please do not open PR's like this in the future, this activity is not appreciated." On #9581/#9583 the stated reasons were narrower ("you are not the package author", "report problems at the package's repository"); #9584 made it an explicit, general ban on future PRs, not just a rejection of those four.

**How to apply:** for this specific repo, drop channel-PR-based fixes entirely, even for objective schema issues (platform lists, dead/archived entries, obvious typos in the catalog itself) -- this overrides any earlier campaign note treating channel PRs there as fair game. If a channel-level problem is found in future campaign work, either skip it silently or, at most, mention it in the package's own test-log entry without filing anything against the channel repo. This does not affect filing issues on individual PACKAGE authors' own repos (e.g. prokopchukdim/light-search, trych/SmarterLineMoves, mawelborn/ZipContents) -- those are unaffected and continue as normal. See also [[feedback_report_bugs_never_patch_authors_code]] and [[feedback_one_issue_per_finding]].
