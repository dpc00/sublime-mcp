---
name: feedback_one_issue_per_finding
description: "File one GitHub issue per distinct finding; bundling three PEP 440 findings in sublimehq/package_control#1761 let deathaxe close all with one line about only one of them"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 165e315a-efcb-49b3-8b31-7320fbdb0c43
  modified: 2026-09-24T17:28:13.565Z
---

On 2026-09-24 I filed sublimehq/package_control#1761 bundling three separate PEP 440 specifier deviations (local versions; `>`/`<` against pre/dev/post specifiers; `.postN.devM` not a pre-release). Maintainer deathaxe closed it "not planned" with one line ("Local versions are not of any interest in this implementation") that only addressed the first point; the other two were left unaddressed by the closure.

**Why:** a maintainer can dismiss the weakest/out-of-scope item and take the strong ones down with it. Also lead with the strongest, most defensible finding, and state real-world impact honestly (here `check_version` is only used for PyPI `requires_python`).

**How to apply:** one issue per distinct finding (one root cause each), strongest evidence first; keep low-impact conformance nitpicks separate from real bugs. If a maintainer dismisses part of a bundled issue, reply politely and offer to split rather than argue. Related: [[project_gadzillion_package_test_campaign]].
