---
name: feedback-list-apps-misses-hidden-windows
description: computer-use list_apps can miss windows hidden behind other windows (a Cursor window opened behind ST was not listed); cross-check with Get-Process MainWindowTitle before concluding no window opened
metadata:
  type: feedback
---

2026-09-26: after launching Cursor from a test, `list_apps` showed no new Cursor window, and I briefly concluded the launch had opened nothing. Donald saw the window sitting behind Sublime Text. (Also: another window was later not targetable although it existed.)

**Why:** occluded/minimized windows may not appear in list_apps or be targetable, so "not listed" is not "not opened". Wrong conclusions here can leak into issue text.

**How to apply:** to decide whether a GUI app opened a window, ALSO check `Get-Process <name> | Where MainWindowTitle` (titles carry the workspace/file name and were decisive for the Cursor findings), and read titles before claiming absence. Keep testing on the portable/other-desktop where possible and tell Donald when I launch a visible app so he can look behind ST. Related: [[feedback-dismiss-dialogs-with-computer-use]], [[feedback-junk-tabs-other-group]].
