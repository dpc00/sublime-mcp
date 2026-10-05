---
name: feedback-wait-for-command-registration-after-install
description: "after Package Control installs/reloads a package, a run_command test immediately after can silently no-op if the command hasn't finished registering yet -- looks exactly like \"no bug found\""
metadata:
  node_type: memory
  type: feedback
  originSessionId: a393e427-5520-48bb-9c04-b2887aafdba8
  modified: 2026-09-28T10:08:26.442Z
---

`view.run_command("some_command", ...)` silently does nothing if `some_command` isn't registered yet -- no exception, no console output, the view just doesn't change. Right after Package Control installs or reloads a package, there's a window where the module has been imported but the command class hasn't finished registering in `sublime_plugin.text_command_classes` (or `window_command_classes`/`application_command_classes`). A test run during that window looks identical to "the package has no bug here."

**Why:** Cost real time auditing SortBy (sublime-mcp package campaign, queue #611, 2026-09-28) -- ran the exact command that later proved buggy, got unchanged output, and almost logged it as clean. Checking `sublime_plugin.text_command_classes` for the command's class confirmed it genuinely wasn't registered yet at the time of the first test; a beat later it was, and the real test then surfaced two confirmed bugs.

**How to apply:** After installing/reloading a package and before trusting a "nothing happened" result from a live test, confirm the target command actually appears in the relevant `sublime_plugin.*_command_classes` list (or just retry after a short pause). Don't conclude "no bug" from an unchanged view without that check first. See also [[feedback_prioritize_dialogs_console_errors_during_install]] -- another install-cycle timing pitfall from the same session.
