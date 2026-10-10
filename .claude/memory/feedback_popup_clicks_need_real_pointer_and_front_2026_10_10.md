---
name: popup-clicks-need-real-pointer-and-front-2026-10-10
description: 2026-10-10 why computer-use clicks never hit Sublime popup links (Sublime hit-tests popups at the REAL pointer), how to click them, how to force a window to the front past Windows' focus lock, and why a test file opened in a background window has no ColorHelper rules
metadata:
  type: feedback
---

**Popup links:** Sublime decides which popup link a click hits from the real mouse pointer position, not from the coordinates inside the click message. computer-use `click` posts a message and never moves the real pointer, so a click on a popup link just lands on the editor and dismisses the popup (the popup's `on_navigate` is never called). Posted WM_MOUSEMOVE does not help. Proven 2026-10-10 by logging every `on_navigate` href (wrap `mdpopups.show_popup`): real pointer + click = href received; pointer over the link + posted click = received; posted click alone, or posted move then click = nothing. How to click one: PowerShell `SetProcessDPIAware`, `SetCursorPos` in 2-3 small steps over the link with 150 ms pauses, wait 400 ms, `mouse_event` down/up. Screen position = window rect origin + image coordinate x 1.017 (this machine, 96 DPI, window rect from `GetWindowRect`).

**Bring the test window to front (Donald: "you never bring the portable ST instance to front"; Windows blocks plain SetForegroundWindow, foreground stayed on his main Sublime):** press and release Alt (`keybd_event 0x12`), `AttachThreadInput` to the current foreground thread, `ShowWindow(9)`, `SetForegroundWindow`, detach; then CHECK `GetForegroundWindow() == hwnd`. Do this BEFORE every test in a portable.

**Background-window artefact:** a file opened with `open_file` through the bridge while the portable is in the background gets NO ColorHelper rules (`util.get_rules(view)` has no `color_class`), so `filters` is empty, `get_cursor_color()` returns None and the picker dialog opens on white. Re-activating the tab (`focus_view` another view, then back) creates the rules. Not a ColorHelper or PR bug.

**list_apps names drift:** the same portable window was listed once under the GhostShell cache exe path and later under `process:D:\st_portable_4215\sublime_text.exe`, while the main Sublime took the other name. Re-run `list_apps` before each action and address by the current path plus window id.

**Why:** I told Donald a click "could not be made to work" for hours, and tested with the window in the background. **How to apply:** see above; related [[feedback_bring_test_window_to_front]], [[colorhelper-maintainer-reply-2026-10-10]].
