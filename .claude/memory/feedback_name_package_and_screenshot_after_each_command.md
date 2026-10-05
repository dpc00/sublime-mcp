---
name: name-package-and-screenshot-after-each-command
description: "Donald's 2026-10-05 rule for package tests - announce the package under test, and screenshot the test window after every command to catch panels/dialogs"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-05T01:16:07.868Z
---

Before each package test, say one plain line: "Testing: <package name>". After EVERY command run in a portable Sublime (4200 or 4215), take a screenshot of that window (computer-use get_window_state with capture_mode=image; list_apps gives the window id) and look for quick panels, input/mini panels, popups and dialogs. If one appears: name it, say what it shows, and dismiss/answer it, before continuing.

**Why:** Donald saw a mini panel appear during testing and could not tell which package it belonged to, because I never said which package I was testing; he said "If a panel appears, you are supposed to know it, and fix it. No excuse." My scripts only read active_panel(), which does not see quick panels, so I missed panels (CiteBibtex quick panel had to be pointed out by him: "quick panel, doe2019 smith2020").

**How to apply:** this adds to [[feedback_poll_for_dialogs_and_say_what_to_press]] and [[feedback_clean_portable_overlays_and_tabs]]. Bring the 4200 window to the front first (front.py with the window id) or computer-use clicks/keys will not reach it; with it in front, press_key works but a click on a quick-panel item did not. Dismiss native dialogs with okdialog.py ('none close').

**Tooling (2026-10-05):** scratchpad peek4200.py [4200|4215] saves peek4200.png of the portable window without focusing it (PrintWindow); Read the PNG after each command to spot quick panels/mini panels/dialogs. Also: Donald's mid-turn messages can show up as a tool rejection ('user doesn't want to proceed') - that is NOT him cancelling; never say he rejected/aborted anything, just carry on and answer his message. show_pkg_code.py prints a package's Python source before testing it.

**PREDICT FIRST, SILENTLY (Donald 2026-10-05, angry about missed mini-panels/dialogs/browser tabs; then 'you do not have to tell me anything'):** before running any command of a package, run find_ui_calls.py <pkg> and read the code of the commands I will call, and work out for myself what UI it will raise (quick/input panel, dialog, popup, browser tab, network call, files written). Do NOT narrate the prediction to him. Run the command, Read peek4200.png, and handle whatever appeared (dismiss it, close any browser tab I caused). He only wants to hear about real problems.
