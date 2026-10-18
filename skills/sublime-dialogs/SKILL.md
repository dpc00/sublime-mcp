---
name: sublime-dialogs
description: What an agent does when Sublime Text shows a native dialog, menu or the Update window, or a tool call times out with "main-thread timeout". Use after installing a package, after any command that may prompt, and whenever the window looks locked.
---

# Sublime dialogs: read them, act on them, close them

A dialog is Sublime or a package complaining, and it says what is wrong. One left open disables the
editor window and times out most tools, so none is ever left open. Which tools open dialogs is in
AGENT_GUIDE.md ("Tools with side effects").

1. **Look.** After a package install, a command that may prompt, or any "main-thread timeout after 5s",
   call `list_native_windows()`. It works while the main thread is blocked and shows each dialog's text
   and buttons and whether `main_thread_blocked` is true.
2. **Read and act.** The text names the cause. Fix the cause, not the symptom: a missing library means
   `satisfy_libraries`; a save prompt for a file you opened means answer it; a package error means read
   that package's console output and settings. Do not report each dialog to the person; report only what
   needs a decision or what you could not fix.
3. **Close it** at once with `dismiss_native_window`: the Cancel button when there is one (Save As, Open
   and Select Folder have Cancel and no OK), OK for an information dialog, `action="close"` for a menu or
   the "Update" window (Sublime shows it even with `update_check` false; never update a portable test
   build).
4. **If it comes back, stop it coming back.** Change what opens it (a setting, a missing dependency, the
   order of your steps). Closing it again each time is not a fix.
5. **Look again.** Dialogs often come in twos (one per plugin load). Then read `get_console` for the
   errors the dialog was about.

## Menus

A native menu blocks the main thread like a dialog, and a menu is part of what is being tested, so use the
real one with the real mouse: open it, `list_native_windows()` (kind `menu`, note its `hwnd`),
`ui_screenshot(hwnd=...)` to see it, `ui_click(x, y, hwnd=..., wait_idle_s=60)` with x, y counted from the
menu's top-left corner, then check the effect with a normal tool. If no click is wanted, close it with
`dismiss_native_window(action="close")` as the very next call. Never leave a menu open.

## Pickers and overlays: look before you restart, kill or close anything

A picker (quick panel, command palette, Goto Anything, color scheme or package picker) and the Find
panel are drawn by Sublime itself, not by Windows, so `list_native_windows` does not list them. Before
restarting or killing a Sublime, closing a window, or starting a new test step:

1. `ui_screenshot` the window and read what is on it. A picker may be waiting for an answer, and what it
   shows can be the information you need.
2. A picker opened by a package in the plugin host: `get_quick_panel` lists its items,
   `pick_quick_panel` answers it (index -1 cancels). Any other picker: answer it with `ui_press_key`
   (`Escape` to cancel, `Down` and `Return` to choose), then screenshot again.
3. Only then restart. Never restart "to get a clean state" while something is up.
