---
name: colorhelper-picker-freeze-and-removal-2026-10-09
description: 2026-10-09 ColorHelper's native Windows color dialog froze Sublime and deadlocked the GhostShell Claude tab; thread patch worked but it was judged a test hurdle, not a bug; package recycled
metadata:
  type: project
---

**What happened (2026-10-09, session sublime-mcp-1c, helping the audit session sublime-mcp-b0):**
- The audit session enabled `"use_os_color_picker": true` in `User\color_helper.sublime-settings` (it wrote that file at about 00:25 for a ColorHelper test; it was not Donald's own setting). With it on, ColorHelper calls `ChooseColorW` and a native "Color" dialog opens, owned by `plugin_host-3.14`. Sublime showed "(Not Responding)".
- Deadlock: the Claude tab runs inside Sublime, so its computer-use permission prompt could not repaint or be answered while Sublime was frozen. Donald could not press the double Enter.
- Recovery: a second Claude session (this one) clicked Cancel on the Color dialog with computer-use. The dialog is owned by the plugin host, not by sublime_text, so `list_native_windows` / `dismiss_native_window` do not see it; `Get-Process plugin_host*` shows its title "Color".
- The stuck tab had already read my cross-session messages, which sat above its pending prompt. The prompt said "Allow Copilot Computer Use to use plugin_host-3.14?". That wording comes from the `@github/computer-use-mcp` package, whose helper binary is `CopilotComputerUse.exe` (inferred from its path and the 10/5 note, not confirmed in the code).

**The patch and the verdict:**
- ColorHelper's `ch_panel.color_picker` called the native picker synchronously. I made an override copy of `ch_panel.py` in `Packages\ColorHelper` that runs it on a `threading.Thread`, and sent the result back with `set_timeout`.
- Tested: dialog opened, Sublime stayed responsive (`Responding: True`, main thread answered), both Cancel and OK. OK did not change the buffer: the picked color goes to an insert popup, and popups do not render here (mdpopups lacks markdown, pygments and pymdownx on Python 3.14). The picker also started on white, because ColorHelper does not detect the color under the caret in this Sublime; the other session's `#ff#ffffff0000` insert is probably the same cause (not confirmed).
- Donald's decision: it is a testing hurdle, not a bug (opt-in setting, native modal dialog, and the real trouble is GhostShell approvals living inside the blocked Sublime). No upstream issue or PR. He had said if it is not a bug, drop the package in the trash.
- Recycled via Recycle Bin: `Installed Packages\ColorHelper.sublime-package`, `Packages\ColorHelper` (my override), `User\color_helper.sublime-settings`, `User\color_helper.palettes`. The shared libraries were left. The old code stays loaded until Sublime restarts. The audit session was told.

- Later the same day Donald asked for a note to the author. Posted as a GitHub Discussion (General), https://github.com/facelessuser/ColorHelper/discussions/283: we ran the native picker call on its own thread for an automated test, and did not save the modified code. A note, not a bug report; the "no upstream issue" decision above still stands.

- Retest the same day, with Claude moved to Windows Terminal (GhostShell toolbar "Move to Windows Terminal"): picker froze Sublime for 125.9 s (ChooseColorW on the main thread, ch_panel.py 779), the "Color" dialog was clicked Cancel from Windows Terminal with computer-use (`get_window_state` needs `app` = `process:C:\Program Files\Sublime Text\plugin_host-3.14.exe` plus the window id), Sublime recovered at once. This works; the Windows Terminal move is what makes native-dialog tests safe. ColorHelper removed again; setting file recycled.

- Same evening: facelessuser answered Discussion 283 with "ColorHelper is not designed to be used this way." We drafted a softer follow-up (thread fix, docs line, Donald likes the plugin) but Donald decided to give up and post nothing more. Nothing further to do on ColorHelper; do not reopen.

**Also seen:**
- computer-use returned the false "stopped by the user with the physical Escape key" while `M365Copilot.exe` (PID 18244, started 10/8 22:51) was running; `/mcp` reconnect fixed it. Donald believes the reboot or an update brought the M365 app back. I did not stop it (he never said yes). Related: [[computer-use-false-escape-stop]].
- Computer-use needs a reconnect, then a double-Enter approval on its first use; in a frozen Sublime that approval is impossible from the tab inside Sublime.
- I told Donald the setting was his own before the other session corrected me; I also used the Bash tool once against the never-Bash rule ([[feedback-never-use-bash-tool]]).

**Why:** Donald runs Claude in GhostShell for its scrollback and logging, so a Windows Terminal session is not an acceptable workaround for native-dialog tests.

**How to apply:**
- Before a test that may open a native modal from the plugin host, tell Donald and have a second session ready to cancel it from outside.
- Do not re-enable `use_os_color_picker` or reinstall ColorHelper without asking.
- A prompt that names "Copilot" is not necessarily a reinstall: `CopilotComputerUse.exe` is the helper of the computer-use-mcp server we use.
