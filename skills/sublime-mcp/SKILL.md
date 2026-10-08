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
has the details and the console-reading workaround. `run_command` reports ok even for a
command that does not exist, so check for a visible effect; unknown arguments are dropped
silently too. Package installs can run for minutes with an unchanging status text, and the
console cannot be read reliably through the tools (see the same guide section).

`list_native_windows` and `dismiss_native_window` (Windows) work while a native dialog
or menu has blocked Sublime's main thread and the other tools time out; call them
through `batch`.

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
