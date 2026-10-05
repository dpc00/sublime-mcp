---
name: stray-multicursor-escape
description: "Donald's main-ST bug: multi-cursor turns on by itself while editing files, and Escape then closes an open panel instead of clearing cursors; Escape half fixed 2026-09-29, cause of the stray cursors unknown"
metadata:
  node_type: memory
  type: project
  originSessionId: 20d54abe-2f32-4daf-93ee-a1da9540a1db
  modified: 2026-09-29T19:38:58.154Z
---

**Symptom (Donald, 2026-09-29, "bug one"):** in his main Sublime, multi-cursor turns on with no request while he is coding; with a panel (build output) open, Escape closes the panel instead of clearing the cursors, so he has already typed into several places and lost the panel. He has NOT seen it in ~5 weeks (he mostly talks to me in the terminal tab now); it never happens in the Claude terminal tab.

**Escape half (fixed):** Sublime's default keymap ranks `hide_panel` (panel_visible) above `single_selection`. Donald's principle: Escape goes to whatever has focus. Implemented in `Packages\User\Default.sublime-keymap` (backup `Default.sublime-keymap.bak.20260929-escape`): rule 1 `cancel` when a text view is focused and a panel is visible; rule 2 `ai_terminal_keypress escape` in terminal tabs with a panel visible (GhostShell's own rule requires no panel); rule 3 `single_selection` with several cursors. A focused panel, popups, auto-complete, overlay, snippet fields and command mode keep Escape. Not tested with real key presses (can't from here).

**Cause of the stray cursors (unknown):** suspects were a stray Ctrl+click / middle-click / three-finger tap, Alt+F3, Ctrl+D, Ctrl+Alt+Up/Down, or something automated (a plugin or my own tools changing the selection). Proposed but NOT installed: a small visible logger in Packages\User that, when the selection goes from 1 to >1 cursors, prints the last commands to the console. Offer it again only if he reports the bug recurring.

Related: [[feedback_dismiss_dialogs_with_computer_use]] (my tools act in his main ST), [[project_st_trackpad_zoom_freeze]] (touchpad gestures can misbehave in ST).
