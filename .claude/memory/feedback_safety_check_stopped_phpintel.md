---
name: safety-check-stopped-phpintel
description: 2026-10-06 a safety classifier stopped my response while I was testing PHPIntel; the withheld calls did not run
metadata:
  type: project
---

On 2026-10-06 the response I was writing during the PHPIntel test was stopped by a safety classifier, not by a tool error. The rest of that response, and any tool call in it that had not finished, was withheld. I was told not to reproduce that content.

**Why:** The stop came from the classifier, so the withheld steps never ran. The PHPIntel index test was left unfinished and logged as partial.

**How to apply:** If a response is stopped like this, check the rig (installed packages, open windows, /tmp test folders) before continuing. Do not redo the withheld steps unless they are needed for the test. Log the stop in the test log and move on to the next package.

Related: [[project_wsl_st_running_2026_10_06]]
