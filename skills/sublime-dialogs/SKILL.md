---
name: sublime-dialogs
description: How an agent handles native dialogs, popups and other complaints from Sublime Text while working through sublime-mcp. Use after installing or removing a package, running a command that may prompt, or whenever a tool call times out with "main-thread timeout" or the window looks locked.
---

# Sublime dialogs: read them, act on them, close them

A dialog is Sublime (or a package) complaining. It says what is wrong. A dialog left open
disables the editor window, blocks the person at the keyboard and times out most tools, so it is
never left open.

## When to look

Look before assuming anything is wrong, and look every time after:

- installing, removing or upgrading a package (`install_package`, Package Control commands)
- running a command that may prompt (save, close, delete, open file, anything from a package)
- a "main-thread timeout after 5s" error (see below)
- a tool result that does not match what you just did, or a screenshot that shows a greyed window

`list_native_windows()` shows every dialog, menu and extra window with its text and buttons, and
works while the main thread is blocked. Call it, do not guess. A window titled `Update`
(Sublime's own "Update Available") is a window, not a dialog; it is listed too.

## What to do with each one

1. **Read the text.** It says what is wrong. Make sense of it.
2. **Act on it.** Fix the cause, not the symptom:
   - "needs the Package Control libraries X": `install_package` installs only the package, not the
     libraries it depends on, and a package loads the moment it is installed. Run `Package Control:
     Satisfy Libraries` (run_command `satisfy_libraries`), then reload the package. To avoid the
     dialog altogether next time: add the package to `ignored_packages` first, `install_package`,
     `satisfy_libraries`, then remove it from `ignored_packages`, so it loads once with its libraries.
   - A save/close prompt for a file you opened: you own that file, answer it and move on.
   - A package error: read that package's console output and settings, correct it.
3. **Close it** with `dismiss_native_window` (Cancel when there is a Cancel button, which Save As, Open
   and Select Folder dialogs have instead of OK; OK for information dialogs; for a choice, the button
   that is right, never a blind default). Do it at once, not later.
4. **If it comes back, stop it from coming back.** Find what opens it and change that: a setting, a
   missing dependency, the order you do things in, a package that should stay disabled. Do whatever
   it takes; closing it again each time is not a fix.

Do not report each dialog to the person. Report only what needs a decision or what you could not
fix. The text is not lost when the dialog closes: copy anything worth keeping into your notes or
the summary before you press the button.

## The Update window

Sublime shows "Update Available" even with `update_check` false: it steers unregistered users to
the purchase page. Close it (`dismiss_native_window` on its `hwnd`, action `close`) whenever it
shows. In the portable test builds (4200, 4215) never download or install an update: the old build
is the point of the portable.

## "main-thread timeout after 5s"

The error names the cause when it can: a native window blocks the main thread (read it, act,
close it), or no dialog is open and the main thread is busy (a package loading or installing; wait a
few seconds and call again). Do not retry in a loop against a blocked main thread.

## After closing

Call `list_native_windows()` again: dialogs often come in twos (one per plugin load). Then check the
console (`get_console`) for the errors the dialog was about.

## Menus and popups: test the real menu

A menu is part of what is being tested, so open the real one and use it with the real mouse, as a
person would. Do not swap in a shortcut that runs the entry's command without the menu; that proves
nothing about the menu.

An open native menu blocks Sublime's main thread: while it is open every tool that needs the main
thread times out ("main-thread timeout after 5s"), and so does anything else waiting on Sublime. The
tools that work without the main thread are `list_native_windows`, `dismiss_native_window`,
`ui_screenshot` and `ui_click`/`ui_press_key`. Procedure, tried 2026-10-18 in the 4215 portable with
the editor's right-click menu (`run_command` `context_menu`):

1. Open the menu. The call that opens it returns the timeout error after 5 s; that is expected, send
   it from a thread or ignore the error.
2. `list_native_windows()`: `main_thread_blocked: true` and a window of kind `menu`; note its `hwnd`.
3. `ui_screenshot(hwnd=<menu hwnd>)`: the picture of the open menu, to read the items and pick a point.
4. `ui_click(x, y, hwnd=<menu hwnd>, wait_idle_s=60)`: x, y count from the menu's top-left corner in
   that picture. (Tried: clicked "Select All"; the menu closed, `main_thread_blocked` went back to
   `false`, and the buffer selection was the whole text.)
5. Check the effect through a normal tool (here `eval_python` reading the selection).

If no click is wanted, close the menu with `dismiss_native_window(hwnd, action="close")` as the very
next call. Never leave a menu open, and after any timeout look with `list_native_windows` before
retrying.
