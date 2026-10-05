---
name: dont-report-newest-build-lag
description: "2026-10-03 Donald: \"won't start on build 4215\" is not a bug, it is lag behind the times; test each package on the Sublime/Python versions it requires, and only report real defects there"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-05T01:53:28.228Z
---

After the top-ten run (golang/sublime-build#45, zsong/SqlBeautifier#31, Robot-Will/Stino#539, ternjs/tern_for_sublime#192, SublimeHaskell/SublimeHaskell#460 were all "fails to load on 4215/Python 3.14"), Donald said: "I don't think you should report 'won't start on 4215', because that is not a bug. That is lag behind the time. At any rate you should test on any version that they require."

**Why:** old packages written for Python 3.3/3.8 hosts naturally break on 4215's Python 3.14 (removed `cgi`, `async` keyword, missing libraries). That is age, not a defect, and filing it just annoys maintainers (he is already in trouble with Package Control people).

**How to apply:** for every package read its `.python-version` / README for the Sublime and Python it needs and test there (the older portable `D:\st_portable_4200`, Python 3.3 and 3.8 hosts; see [[reference_portable_st_4200_older_build]]). If it only fails on 4215, log "fails on 4215 only (age)" and do NOT file. File only defects that reproduce on a version the package supports. Do not stop at the first load failure: after it, retest on 4200 and look for real bugs. Also do not file general "old library on a newer system Python" issues unless they hit the package's required setup.

Resolved: he approved closing the five "4215" issues on 2026-10-03 (see [[project_closed_4215_only_issues_2026_10_03]]). Related: [[project_package_audit_campaign_stopped_2026_10_03]], [[feedback_keep_issue_text_short]].
