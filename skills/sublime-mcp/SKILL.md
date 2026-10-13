---
name: sublime-mcp
description: Use a running Sublime Text instance as the primary way to inspect, search, edit, navigate, and save project code through the sublime-mcp server.
---

# Sublime Text coding workflow

Use sublime-mcp for editor and project operations when its tools are available.

At the beginning of the first Sublime operation in a session, call `get_help`. Use
`get_active_file` to establish the current buffer and `project_search` for project
text search. Prefer these over shell-based file inspection or search when they can
answer the request.

Use `batch` for two or more independent operations. It is also the gateway for an
advanced capability returned by `discover_tools`:

```text
discover_tools()                          # top-level categories with tool counts
discover_tools(category="selection")      # subcategories
discover_tools(category="selection/select")   # tools in one, with schemas
discover_tools(query="bookmarks")         # keyword search across all tools
batch(calls=[{"tool": "get_bookmarks", "args": {}}])
```

Case commands act on the selection (`select_all` first); `insert` types at the cursor;
closing a modified untitled tab opens a native "Save Changes?" dialog. `get_help`
has the details.

For packages, menus, the command palette and input prompts without `eval_python`
(`search_packages`, `install_package`, `get_menu_items`, `get_command_palette`,
`drive_input_panel`, `get_quick_panel`, `pick_quick_panel`, `click_menu_item`, and `run_command` with `show_overlay`), see "Packages, menus,
palette and input panels" in `get_help`. Do not reach for `eval_python` or scripts
for these.

To remove a package use `run_command remove_package` (not the palette text), and
expect a Windows confirmation dialog for every `delete_file` / `delete_folder` item;
"Removing packages, deleting files, reading the console, making folders" in `get_help`
has the details. `run_command` reports ok even for a command that does not exist, so check
for a visible effect; unknown arguments are dropped silently too. Package installs can run
for minutes with an unchanging status text.

Reading the console (tested 2026-10-11 on portable 4200 and 4215, identical results):
- Complete read: `get_console(mode="visible", force_focus=true)`. Use `tail=N` to keep the
  reply small. It raised the window, did not crash either portable, and returned
  `complete: true`. The window does NOT stay in front between calls (it was not in front
  seconds later), so pass `force_focus=true` on every call. Clicking the title bar does not
  bring it to the front. `get_console(force_focus=true)` (auto) gives the same result.
- Without `force_focus`, with the window behind: `visible`, `get_console_full` and
  `get_console_win` fail at once and change nothing; `auto` and `get_output_panel(name="console")`
  silently fall back to the captured text with `complete: false` and a `warning`. Check
  `complete`/`warning` before trusting a result.
- `mode="captured"` and `get_console_log` never need focus, but always report `complete: false`:
  they miss what Sublime printed before sublime-mcp loaded (startup lines, plugin load errors).
- `get_console_full` and `get_console_win` accept `force_focus` and work with it.
  `get_output_panel(name="console", force_focus=true)` passes it on (added 2026-10-11, tested on
  portable 4200 and 4215: `complete: true` with it, captured fallback with a `warning` without).
- Each successful visible read adds one `[sublime-mcp] console capture marker` line.
- Do not open the console panel with `show_panel` and read the screen.

`list_native_windows` and `dismiss_native_window` (Windows) work while a native dialog
or menu has blocked Sublime's main thread and the other tools time out; call them
through `batch`.

A dialog can open a moment after `run_command` returned ok, so a `list_native_windows`
in the same batch may miss it: pass `settle_ms=300` to `run_command` and read `dialogs`
in the result. `list_native_windows` returns no message text for a task dialog with
custom button text (for example "Install Terminus" / "Cancel"); read it with
computer-use. To close a tab that has no path use `close_file(name=...)` or
`close_file(index=...)`, never `run_command` `close` (it does nothing) and never
`close_file` with no arguments unless the active tab is the one you mean.
To close a tab that has unsaved edits without Sublime's "Save Changes?" dialog
(which blocks the main thread), pass `discard=true` (since 1.13.2): the edits are
thrown away and the result says `discarded`. If the dialog opens anyway, the
running Sublime has plugin code older than 1.13.2 (portable 4200 ran 1.12.5
on 2026-10-13; a portable holds its own copy of the package, so update it):
answer the dialog with `dismiss_native_window`.

Edit through `str_replace_based_edit_tool` so changes appear in Sublime with undo
and diff markers. Call `save_file` after an edit unless the user asks to leave the
buffer unsaved.

Fall back to ordinary filesystem or shell tools when sublime-mcp is unavailable,
returns an explicit limitation, or the operation is outside Sublime's scope. Do not
claim an editor operation succeeded unless its tool result confirms it.

Don't call `close_file` on an ai_terminal-hosted tab (any tab running an agent
CLI, including the one hosting this session) expecting it to close it.
GhostShell's ai_terminal package now blocks every native window-close command
outright for its own tabs (no dialog, just a no-op with a status message), so
the call does nothing rather than closing anything -- safe to call by
accident, but useless for actually closing one. Ask the user to use that
tab's own "Tab Close ▼" toolbar control instead if a tab needs to be ended or
detached.
