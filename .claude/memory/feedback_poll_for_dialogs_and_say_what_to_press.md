---
name: poll-for-dialogs-and-say-what-to-press
description: "While any portable-ST test runs, poll for native dialogs every ~10 s and dismiss safe ones myself; never leave Donald a decision without saying what to press and the consequence"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 20d54abe-2f32-4daf-93ee-a1da9540a1db
  modified: 2026-10-01T19:00:06.489Z
---

While a portable ST test is running, check for native dialogs about every 10 seconds (list_apps rows titled "Sublime Text", or the MCP "main-thread timeout" message) and dismiss the safe ones myself with computer-use. Do not wait for Donald to notice.

**Hard rule (Donald, 2026-09-29):** before ANY tool call that might raise a permission prompt, first run list_apps (now allow-listed, no prompt), read any dialog, and close it, so a prompt never lands on top of a dialog. Do this first, every time. This includes any mini-panel or small popup window, not only modal dialogs.

**Why:** 2026-09-29: LSP-clangd's own "install clangd?" dialog appeared on the portable while Donald was answering a computer-use permission prompt; his Enter went to the dialog instead, he was furious ("USELESS ... PROGRAM"). Earlier the same day a Liquid test left "Error loading syntax file" dialogs after I removed the package with test views still open. He also said: "you never tell me what to do. How am I to decide when I don't know the consequences."

**2026-10-01 repeat (Donald: "not watching out for dialogs!"):** I ran `run_syntax_tests` four times on test files kept in %TEMP%; each raised a modal "The current file can not be used for testing since it is not loaded by Sublime Text ... not located in the Packages folder" and the output panel stayed silently empty. Four dialogs piled up before I looked. Syntax test files must live under Data\Packages (e.g. Packages\User\) to run; an EMPTY exec panel after run_syntax_tests means a dialog, not a pass. Dialogs are stacked and only the top one's OK is enabled: click, re-list, repeat. Enumerate the portable's windows (EnumWindows, class #32770) as well as list_apps.

Cheapest dialog check on the portable: the sublime-mcp tool `list_native_windows` (via batch; reports kind editor_window / dialog and main_thread_blocked) and `dismiss_native_window`; computer-use list_apps works too. Run it after every run_syntax_tests / build / install command.

**2026-10-01 (Donald, twice: "mini-panel", then "there is a quick-panel. When I point that out I expect you to HANDLE IT, not go on through 50 more steps"):** a one-word nudge like "dialog", "mini-panel" or "quick-panel" means a UI element is open right now. Stop everything else and handle it in my very next action: list windows (computer-use list_apps / list_native_windows), look at the portable window with get_window_state or a screenshot, and dismiss it (Escape for quick/input panels, OK for dialogs). Only then resume. Note list_native_windows does NOT show quick panels or the command palette; they live inside the editor window, so check `window.active_panel()` and the window state, and press Escape if in doubt.

**How to apply:**
- Before running a test, ask whether the package can raise a prompt (downloads, installs, first-run dialogs). If yes and it needs a person, skip it and say why, do not run it while he is at the keyboard.
- Close test views before removing a package.
- Whenever I need him to press something: one line saying what it is, which button, and what happens with the other button. If I can dismiss it safely, do it and do not ask.
- Related: [[feedback_dismiss_dialogs_with_computer_use]], [[feedback_one_dialog_command_per_call]], [[feedback_one_portable_instance_no_test_windows]].
