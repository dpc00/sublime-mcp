---
name: feedback-skip-unmaintained-packages
description: Audit only maintained packages; skip archived, obsolete or long-dead ones, they only cause trouble
metadata:
  type: feedback
---

2026-10-07: Donald said the audit must not hit old, archived, obsolete packages. Skip anything that is not maintained.

**Why:** issues filed on dead projects get no fix, cost time, and have drawn hostile or "unmaintained, can't help" replies (e.g. alepez/LiveReloadMake 2026-10-07, Naereen/SwitchDictionary: maintainer left Sublime years ago).

**How to apply:** before picking a package, check its repo (gh): skip if archived, if the last commit is over 2 years old, or the README says deprecated/unmaintained/replaced. Skip silently: no install, no test, no issue, no log entry. Do not file bugs on skipped packages. Related: [[feedback-never-skip-for-missing-prereqs]] (that one is about missing tools, not dead projects).
