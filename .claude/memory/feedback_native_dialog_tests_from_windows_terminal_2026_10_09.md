---
name: native-dialog-tests-from-windows-terminal-2026-10-09
description: 2026-10-09 Donald's method for tests that can freeze Sublime on a native dialog: move the Claude session to Windows Terminal first; it worked on the ColorHelper picker
metadata:
  type: feedback
---

For a test that may open a native modal dialog and freeze Sublime (the ColorHelper picker is the proven case), Donald has the Claude session moved to Windows Terminal first: GhostShell toolbar, "Move to Windows Terminal". He clicks it; I cannot and must not do it myself.

**Why:** my GhostShell tab lives inside Sublime, so a frozen Sublime also hides the computer-use approval prompt and the tab itself. In Windows Terminal the prompts stay reachable. Tested 2026-10-09: ColorHelper picker froze Sublime for 125.9 s, the "Color" dialog was cancelled from Windows Terminal, Sublime recovered at once ([[colorhelper-picker-freeze-and-removal-2026-10-09]]).

**How to apply:**
- Tell Donald before the risky step; ask for the move; after it, run one harmless computer-use call (`list_apps`) so the first-use approval is done while Sublime still responds.
- If computer-use answers "stopped by the physical Escape key" at once, it is the known false stop: Donald runs `/mcp` and reconnects `computer-use-mcp` ([[computer-use-false-escape-stop]]).
- The dialog belongs to `plugin_host-3.14.exe`, so `list_native_windows` does not see it. `list_apps` shows it. `get_window_state` needs `app` = `process:C:\Program Files\Sublime Text\plugin_host-3.14.exe` plus the window id; then click the button by `element_index`.
- Once the Claude tab has left Sublime the window may have no views: `active_view()` is None and some packages' callbacks raise. Make a scratch view for the test.
- Afterwards turn the setting off, remove the package, and let Donald restart Sublime.
