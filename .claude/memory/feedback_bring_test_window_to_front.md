---
name: bring-test-window-to-front
description: "Before testing in any Sublime instance (portable, WSL, main), force that window to the front so Donald can see it and computer-use can act on it; plain SetForegroundWindow fails, use the AttachThreadInput script"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 20d54abe-2f32-4daf-93ee-a1da9540a1db
  modified: 2026-10-05T01:53:29.501Z
---

2026-09-29 Donald: "if you're testing something in a ST instance, bring that damn window to the front first. Then computer-use will work." and, when my first attempt silently failed ("foreground now: False"): "you are not doing it."

**How:** a small script (I kept it as `front.py <hwnd>` in the session scratchpad, which is temporary, so recreate it if missing) (ctypes): GetForegroundWindow -> AttachThreadInput(me, foregroundThread, True) -> ShowWindow(SW_RESTORE=9) -> BringWindowToTop -> SwitchToThisWindow -> SetForegroundWindow -> detach; then print whether GetForegroundWindow() == hwnd. Always check that printed result; plain SetForegroundWindow alone returns False because Windows blocks it. Get the hwnd from `list_native_windows` (portable 9510 / main 9500) or mcp__screenshot__list_windows.

**Caveat:** this takes keyboard focus. He asked for it explicitly for testing, but still do not do it while he is typing in another window; otherwise say so first. Related: [[feedback_poll_for_dialogs_and_say_what_to_press]], [[feedback_wslg_window_froze_keyboard]].
