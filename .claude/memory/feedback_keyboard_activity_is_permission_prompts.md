---
name: keyboard-activity-is-permission-prompts
description: "2026-10-05: Donald is 'at the keyboard' because he is approving my permission prompts, so an input-idle check is no reason to hold back focus-taking test steps; he rejected such a prompt and said don't let that stop you"
metadata:
  type: feedback
---

On 2026-10-05 I measured keyboard idle time (GetLastInputInfo) before bringing the portable test window forward for a console capture, saw 0 seconds, and held back. Donald rejected the next prompt: "of course I'm at the keyboard, you are popping permission prompts. Don't let that stop you."

**Why:** during unattended work his keyboard activity is mostly him pressing Enter on my permission prompts, so it says nothing about whether he is typing somewhere a focus steal would hurt.

**How to apply:** do not gate portable-window focus steps (front.py, capture.ps1) on an idle check. This agrees with [[feedback_bring_test_window_to_front]] (he asked for the window to be fronted for tests) and [[feedback_run_unattended_dont_ask_to_continue]]. Still avoid focus steals when he has said he is typing something specific, and prefer routes that need no focus (captured console on a 3.8 host) when they are equally good.
