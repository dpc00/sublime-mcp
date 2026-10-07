---
name: project-glama-check-fails-because-of-proxies
description: Glama badge check on awesome-mcp-servers#15729 fails because Glama reads the wrong file (the project has proxies); known, not a decision for Donald
metadata:
  type: project
---

2026-10-06: the github-actions bot on punkpeye/awesome-mcp-servers#15729 asked for a Glama evaluation. Donald explained that this project has proxies, so Glama does not read the right file and the project cannot pass its check.

**Why:** the failure comes from the repo layout, not from a defect in sublime-mcp.
**How to apply:** in the half-hour check, do not surface the Glama bot comment as needing a decision. Mention #15729 only if a human reviewer comments or it is merged or closed. Post nothing there without his word.
