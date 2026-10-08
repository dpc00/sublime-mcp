---
name: diagnose-dont-retry-install-2026-10-07
description: 2026-10-07 niceDarkTheme test: five failed Terminus installs because I retried instead of diagnosing; how to drive an install like a user
metadata:
  type: feedback
---

2026-10-07, niceDarkTheme: I clicked "Install" in its Terminus dialog five times and Terminus never installed. The cause was the package (it runs the nonexistent command advanced_install_package; Package Control 4.2.8 has install_package and install_packages), found only after Donald pushed me. Filed aaortizb/niceDarkTheme#1.

**Why:** I retried and blamed timing or Donald instead of reading the source and the Package Control command list after the first failure.
**How to apply:**
- After one failed action, read the code path and check the command exists before trying again.
- Install like a user: command palette, "Package Control: Install Package", type the name, Enter (open the palette with show_overlay via the API, then drive the picker with computer-use). Do not use raw API or direct commands as the test.
- Wait for indexing (find_resources shows the package files) before running a package's commands, or you get false "Unable to find colour scheme" dialogs. After removing a theme package, reset theme/color_scheme in Preferences first.
- computer-use: keys and chords fail on an unfocused window; bring it to the front with SetForegroundWindow plus AttachThreadInput first. Related [[always-computer-use-for-dialogs-2026-10-07]].

- After forcing a test window to the front (2026-10-07) it stayed always-on-top and Donald had to tell me. When done, clear WS_EX_TOPMOST (SetWindowPos HWND_NOTOPMOST) and send it behind other windows without activating it (SetWindowPos HWND_BOTTOM + SWP_NOACTIVATE). Do NOT minimize it: Donald said that was also wrong. Check it myself; don't wait to be told.

