---
name: audit-installs-must-follow-user-flow-2026-10-07
description: 2026-10-07 Donald: every audit install must go through the command palette Install Package picker like a user; script installs prove nothing about installability
metadata:
  type: feedback
---

2026-10-07, Donald: "This is a package audit, and if you don't follow what a user does, how can you say whether or not there is any problem installing something?"

**Why:** I installed audit packages with PackageManager().install_package (a script), which skips what a user goes through, so it cannot show install problems such as post-install messages, missing libraries, dialogs, or Python-version failures at load time.

**How to apply:**
- Install every audit package like a user: command palette -> "Package Control: Install Package" -> type the name -> Enter, driven with computer-use (open the palette via show_overlay, type_text, press_key Return). Then wait for indexing and check dialogs, console and the Package Control Messages tab.
- Test both PC release and repo master as before. The release goes through the picker. Donald (same day): installing like a user is a goal, not reality, especially for the latest repo code, which cannot come from the picker; copying repo master in is valid.
- Install results logged before 2026-10-07 evening came from script installs: valid for runtime behaviour, not for installability. See [[diagnose-dont-retry-install-2026-10-07]].

