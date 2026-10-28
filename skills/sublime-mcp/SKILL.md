---
name: sublime-mcp
description: Use a running Sublime Text instance as the primary way to inspect, search, edit, navigate, and save project code through the sublime-mcp server.
---

# Sublime Text coding workflow

Use sublime-mcp for editor and project operations when its tools are available. The full
how-to is `get_help` (the same text as `AGENT_GUIDE.md`); this skill is the short version
plus the traps that cost the most time.

## Start

- Call `get_help` once at the first Sublime operation. It is long: `get_help(section="console")`
  returns only the sections whose heading contains that word.
- `get_active_file` for the current buffer, `project_search` for project text search. Prefer
  these over shell-based file inspection or search when they can answer the request.
- `batch` runs two or more independent calls, and is the only way to run a hidden tool:

```text
discover_tools()                          # top-level categories with tool counts
discover_tools(category="selection")      # subcategories
discover_tools(category="selection/select")   # tools in one, with schemas
discover_tools(query="bookmarks")         # keyword search across all tools
batch(calls=[{"tool": "get_bookmarks", "args": {}}])
```

## Editing

- Edit through `str_replace_based_edit_tool` so changes appear in Sublime with undo and diff
  markers, then call `save_file` unless the user asks to leave the buffer unsaved.
- Case commands act on the selection (`select_all` first); `insert` types at the cursor.
- Do not claim an editor operation succeeded unless its tool result confirms it. `run_command`
  reports ok even for a command that does not exist, and unknown arguments are dropped
  silently: check for a visible effect. A TextCommand such as `insert_snippet` needs
  `scope="view"`, otherwise it does nothing and still returns ok.

## Packages, menus, palette, input prompts (no `eval_python`)

`search_packages`, `install_package`, `get_menu_items`, `get_command_palette`,
`drive_input_panel`, `get_quick_panel`, `pick_quick_panel`, `click_menu_item`, and
`run_command` with `show_overlay`: see "Packages, menus, palette and input panels" in
`get_help`. Do not reach for `eval_python` or scripts for these.

- Remove a package with `run_command remove_package` (not the palette text), and pick by exact
  name. Package installs can run for minutes with an unchanging status text.
- `pick_quick_panel` on a panel of a Python 3.3 package that raises a dialog in its callback
  (Jekyll's "Confirm Delete") answers `pending: true`: the pick went through and the dialog blocks
  Sublime; answer it with `list_native_windows` and `dismiss_native_window`.
- `delete_file` / `delete_folder` (and `revert_file`, `close_window`, `exit`, `eval_python`, `close_file` with
  `discard`) ask the person first; "Denied, nothing was changed" means no: do not retry or go around it.
  Once allowed, delete also raises a Windows confirmation dialog for every item.
- With a completion popup open, a posted Tab does not expand a snippet trigger: press Escape
  first, then Tab.

## Closing tabs

- A tab with no path: `close_file(name=...)` or `close_file(index=...)`. Never `run_command`
  `close` (it does nothing), and never `close_file` with no arguments unless the active tab is
  the one you mean.
- A tab with unsaved edits opens a native "Save Changes?" dialog that blocks the main thread.
  Pass `discard=true` (since 1.13.2): the edits are thrown away and the result says
  `discarded`. If the dialog opens anyway, the running Sublime has plugin code older than
  1.13.2 (portable 4200 did on 2026-10-13: it ran a stale copy, 1.12.5; it is a junction to the
  repo again). Answer the dialog with `dismiss_native_window`.
- Do not call `close_file` on an ai_terminal-hosted tab (any tab running an agent CLI,
  including the one hosting this session) expecting it to close. GhostShell blocks every native
  window-close command for its own tabs (no dialog, a no-op with a status message). Ask the
  user to use that tab's own "Tab Close ▼" toolbar control to end or detach it.

## Native dialogs

`list_native_windows` and `dismiss_native_window` (Windows) work while a native dialog or menu
has blocked Sublime's main thread and the other tools time out; call them through `batch`.

- A dialog can open a moment after `run_command` returned ok, so a `list_native_windows` in the
  same batch may miss it: pass `settle_ms=300` to `run_command` and read `dialogs` in the result.
- `list_native_windows` returns no message text for a task dialog with custom button text (for
  example "Install <package>" / "Cancel"); read it with computer-use.

## Reading the console

Details: `get_help(section="console")`. The short rules (tested 2026-10-11 on portable 4200 and
4215, identical results):

- Complete read: `get_console(mode="visible", force_focus=true)`, with `tail=N` to keep the reply
  small. The window does not stay in front between calls, so pass `force_focus=true` on every call;
  clicking the title bar does not bring it forward. A read takes about 150 ms. Windows refuses the
  raise on a freshly started Sublime and while the user is typing: the error says no input was
  sent, so call again a moment later.
- Without `force_focus` and with the window behind, `visible`, `get_console_full` and
  `get_console_win` fail at once and change nothing; `auto` and `get_output_panel(name="console")`
  fall back to the captured text with `complete: false` and a `warning`. Check `complete` and
  `warning` before trusting a result.
- `get_console_full`, `get_console_win` and `get_output_panel(name="console")` all accept
  `force_focus` too (added and tested 2026-10-11): `complete: true` with it.
- `mode="captured"` and `get_console_log` never need focus, but are always `complete: false`:
  they miss what Sublime printed before sublime-mcp loaded (startup lines, plugin load errors).
- Each successful visible read adds one `[sublime-mcp] console capture marker` line.
- Do not open the console panel with `show_panel` and read the screen.

## Typing into a terminal tab (GhostShell ai_terminal)

GhostShell has no command that sends text into a tab. Do it as a person does, and prove it arrived (full steps and traps:
"Typing into a GhostShell terminal tab" in `get_help`):

1. `get_sheets` with `settings=false` for the target's `id` and `index`, and your own id (the focused sheet). Ids change when
   Sublime restarts, so list them in the same turn.
2. `focus_sheet` on the target, then confirm it is the active tab (`get_sheets` with `settings=false`: the target
   shows `is_focused: true`). If `focus_sheet` errors or the focus is wrong, type nothing: `ui_type_text` types
   into whichever tab is active, and a failed focus would put the text into your own tab while still returning ok.
3. `ui_type_text` (a newline is sent as Return; leave it off to let the person press Enter, for example for `npm publish`), then
   `focus_sheet` back to your own tab.
4. `get_sheet_content` on the target, and quote the echoed line. `ok` from a tool never proves it.

## When sublime-mcp is not enough

Fall back to ordinary filesystem or shell tools when sublime-mcp is unavailable, returns an
explicit limitation, or the operation is outside Sublime's scope.
