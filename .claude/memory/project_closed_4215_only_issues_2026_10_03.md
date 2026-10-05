---
name: closed-4215-only-issues-2026-10-03
description: "On 2026-10-03 Donald approved closing the five \"fails on 4215\" issues; they were closed as not planned with a short apology note"
metadata:
  node_type: memory
  type: project
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-04T03:34:03.229Z
---

Closed with Donald's yes on 2026-10-03: golang/sublime-build#45, zsong/SqlBeautifier#31, Robot-Will/Stino#539, ternjs/tern_for_sublime#192, SublimeHaskell/SublimeHaskell#460. Comment used: "Closing: this was only seen on Sublime Text build 4215, which is newer than this package targets. Sorry for the noise."

**Why:** "won't start on 4215" is age, not a bug ([[feedback_dont_report_newest_build_lag]]). Retest on the 4200 portable showed SqlBeautifier, tern_for_sublime and Arduino-like IDE work there; Nodejs's messages.json trailing comma is already issue #112.

**How to apply:** do not file new 4215-only issues; closing public issues still needs his explicit yes each time.
