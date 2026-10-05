---
name: project-kaste-fixes-from-campaign
description: "Two real fixes landed by maintainer kaste from this package audit campaign's filed issues -- one was a deep multi-round live-debugging collaboration on a genuine Sublime Text core race, not just a quick static-scan finding"
metadata:
  node_type: memory
  type: project
  originSessionId: abbc045e-cea5-4731-ad7e-d010d8ceedc0
  modified: 2026-09-28T19:12:09.159Z
---

Two issues filed by this account (dpc00) during the Package Control audit campaign ([[project_package_audit_baton]]) against packages maintained by GitHub user `kaste` were fixed:

1. **kaste/FindInFiles-addon#2** — `typing_extensions` import not declared as a dependency (only worked on Donald's own ST because `lsp_utils` happened to provide it). Closed 2026-09-25, kaste: "Fixed in 1.5.6."
2. **SublimeLinter/SublimeLinter#1993** — a genuine Sublime Text *core* race condition (not a SublimeLinter bug per se): removing a no-op `.python-version` override with content identical to the packaged zip's own marker could trigger an unwanted reload into the legacy Python 3.3 host. This started as an ack'd/likely-wontfix report, but turned into an extensive multi-round live collaboration: built isolated test harnesses, eventually reproduced 11/11 on a pristine portable ST 4200 build per kaste's exact recipe, confirmed the core-bug theory. kaste then found and landed a real fix — removing the `sublime.set_timeout(check_all_plugins, 5000)` deferred check so plugin-host state goes eventually-consistent on the next ST restart instead of racing. Closed 2026-09-21.

**Why:** Donald noticed via a GitHub comment (from contributor `kaste`, 2026-09-28, on the sublimehq/package_control_channel PR thread: "I fixed both you did on the packages I maintain") that this had happened, and pointed out it was never logged anywhere in the campaign's own tracking. The #1993 thread in particular represents substantial, valuable live-debugging work (not just "filed and walked away") that the campaign log undersells — worth remembering as a concrete example of the campaign's methodology actually landing a real upstream fix, not just filing reports that sit unaddressed.

**How to apply:** When summarizing campaign impact/outcomes, these two are worth citing as fixed, and #1993 specifically as an example of deep collaborative debugging (not a one-shot static finding) succeeding. If similar "closed as fixed" outcomes happen on other filed issues, check whether they're logged in `.package_skill_test_log.md` or the baton and add a note if not — the log currently only captures the filing, not later outcomes, unless someone goes back and checks.
