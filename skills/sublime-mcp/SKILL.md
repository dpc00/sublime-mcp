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
discover_tools(query="bookmarks")
batch(calls=[{"tool": "get_bookmarks", "args": {}}])
```

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
