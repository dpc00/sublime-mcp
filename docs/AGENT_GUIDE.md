# Agent Guide for sublime-mcp (MCP Commander)

Canonical copy for repo readers. `get_help` serves
`AGENT_GUIDE.md` (repo root) — keep these two files in sync.

How to use sublime-mcp tools. Call `get_help` if you are unsure how to
save, close tabs, or run ST Python.

Seven workflow tools are shown by default; the complete typed catalog (401
tools) remains available through `discover_tools` and `batch`. Prefer a named capability over
`run_command`, which often opens UI that steals focus from the agent chat.

On the first Sublime operation, call `get_help` once.

ST tools use **1-based** line/column (`get_active_file`, `open_file`,
`goto_line`, `replace_lines`). lsp-mcp uses **0-based**. Subtract 1 when
passing an ST cursor into an `lsp_*` tool.

## Quick start

Seven tools are listed and are called directly: `get_help`, `get_active_file`,
`project_search`, `str_replace_based_edit_tool`, `save_file`, `batch`, `discover_tools`.
Every other tool is hidden. Find it with `discover_tools`, run it with `batch`.
`discover_tools` never returns the seven listed tools, so do not search for them.

```
discover_tools(query="sort lines")                    # find a tool by words
discover_tools()                                      # or browse: categories -> subcategories -> tools
batch(calls=[{"tool": "sort_lines"}])                 # run it (also for a single call)
```

A new tab with text, sorted and upper-cased, then read back (one round trip):

```
batch(calls=[
  {"tool": "new_file"},
  {"tool": "insert", "args": {"characters": "pear\napple\nmango"}},
  {"tool": "select_all"},
  {"tool": "sort_lines"},
  {"tool": "upper_case"},
  {"tool": "get_active_file"}
])
```

Close that tab without saving (only the active, modified, untitled tab is touched):

```
batch(calls=[{"tool": "eval_python", "args": {"code": "v = window.active_view()\nif v.is_dirty() and not v.file_name() and not v.settings().get('ai_terminal_view'):\n    v.set_scratch(True)\n    v.close()\n    print('closed')"}}])
```

- `insert` types at the cursor, so calling it twice puts the text in twice.
- Case commands (`upper_case`, `lower_case`, `title_case`, `swap_case`) act on the
  selection: `select_all` first. `sort_lines` sorts the whole buffer when nothing is selected.
- `get_active_file` returns untitled tabs too (`path` is null).
- `close_file` on a modified untitled tab opens a native "Save Changes?" dialog that blocks
  every tool; see "When a native dialog blocks Sublime" below. Once, `set_scratch` followed
  by `close_file` in one `batch` was followed by Sublime exiting (cause not established).

A file on disk: create it, change it, save it, read it back, close it. The first four are
listed tools, called directly:

```
str_replace_based_edit_tool(command="create", path="C:\\dir\\notes.txt", file_text="hello world")
str_replace_based_edit_tool(command="str_replace", path=..., old_str="hello", new_str="goodbye")
save_file(path=...)
str_replace_based_edit_tool(command="view", path=...)
batch(calls=[{"tool": "close_file", "args": {"path": "..."}}])      # hidden tool, saved file: no prompt
```

`create` opens the new tab itself (no `open_file` needed) and fails if the file already exists;
the file reaches the disk when `save_file` runs. `str_replace` and `insert` edit the open tab, so
they also need `save_file`. `create` does not make missing folders. To open an existing file use
the hidden tool `open_file(path=...)`.

Hidden tools (everything except the seven) are only reachable through `batch`; calling one
directly gives "No such tool". `get_sheets` returns every tab's full settings (over 100 lines per
tab); the hidden `get_open_files` returns just each tab's path, name and dirty flag.

## Batch (cuts round trips)

Each call pays a trip through ST's main-thread scheduler. For 2+ independent
calls, use `batch` (max 50; cannot call itself):

```
batch(calls=[
  {"tool": "get_active_file"},
  {"tool": "get_selection"},
  {"tool": "get_cursor_context", "args": {"lines": 20}}
])
```

Returns `{"results": [...]}` in call order. A failed call is `{"error": ...}`
in its slot; the rest still run.

## Finding tools (discover_tools)

`discover_tools()` lists the categories (`app`, `editing`, `files`, `packages_and_dev`, `project`,
`read`, `run`, `search`, `selection`, `settings`, `tabs`, `view`); `category="editing"` opens one,
`category="editing/lines"` lists its tools with schemas; `query="upper case"` searches all tools.
Run any result with `batch(calls=[{"tool": "<name>", "args": {...}}])`.

## Editing

`str_replace_based_edit_tool` edits the **buffer**, not disk. Always save:

1. `str_replace_based_edit_tool(command="str_replace", path=..., old_str=..., new_str=...)`
2. `save_file(path=...)` — omit `path` to save the active file

Skip save and ST looks edited while `git diff` is empty.

- Disk `edit`/`write` on a file ST has open → `revert_file` so the buffer reloads.
- Short plain text into an empty tab: `insert` is fine. Indented or large multi-line
  content: use `replace_lines(begin, end, text)`, because `insert` (and
  `view.run_command("insert", ...)`) auto-indents every line and piles indentation.
- `str_replace` `old_str` must match **exactly once**.
- Commands: `str_replace`, `insert` (after 1-based `insert_line`; `0` = start),
  `create`, `view`.

## Closing tabs

A dirty view makes `close_file` open ST's save prompt. Save first, or use the
scratch snippet in the Quick start. Find a path with `window.find_open_file(path)`
(there is no `find_open_by_name`).

## eval_python

Runs in ST's plugin host. Use `print(expr)` — top-level `return` is a syntax
error; bare expressions produce no output. In scope: `sublime`, `window`,
`view`. Timeout is 5s (main-thread).

`eval_python_latest` is **system** Python on PATH, not the ST host — no
`sublime`/`window`/`view`.

## Common tools

```
get_active_file()                  # path, full content, 1-based line/col, is_dirty, syntax
get_cursor_context(lines=10)       # ±N lines, numbered
get_selection()                    # highlighted text
get_sheets()                       # every tab: stable id, group/index, selection/focus, path/name
get_sheet_content(index=2)         # untitled / scratch / Terminus too
open_file(path=..., line=42, col=1)
save_all()
revert_file()                      # active view only
project_search(pattern=..., where=...)  # ST Find-in-Files, structured matches
discover_tools()                        # categories; see "Finding tools"
get_commands()                     # command ids, scopes, packages, palette captions
```

`project_search` `where` accepts folder paths, `*.py`, `-*.md`, `${project}`,
`${open_files}`, `${folder:Name}`.

## When a native dialog blocks Sublime (Windows)

If a tool call fails with "main-thread timeout after 5s", or a command just
opened a native dialog or menu, Sublime's main thread is blocked and almost
every tool will time out. Two tools still work, because they never use the main
thread:

```
list_native_windows()                     # dialogs/menus with buttons + message text,
                                          # main_thread_blocked, blocked_by (the tool)
dismiss_native_window()                   # default action "cancel": Cancel/No, else close
dismiss_native_window(action="ok")        # OK / Yes / the default button (this CONFIRMS)
dismiss_native_window(action="button", button="Remove")   # a named button
dismiss_native_window(hwnd=..., action="close")           # a specific window
```

The default action is `cancel`: on the `delete_file` confirmation it clicks
**No**, on `remove_license` it clicks **Cancel**. `action="ok"` clicks OK / Yes /
the default button, which confirms the action (on `delete_file` the file is
deleted; on `remove_license` the license is removed). The tools act only on windows of the Sublime Text process, and they are Windows
only (they use Win32). Verified on all 16 blocking commands with
`tools/verify_native_dialogs.py`: each froze Sublime, was listed and dismissed
by these tools, and Sublime answered again.

## More

The 160 tools generated from Sublime's command list, what each was observed to do, and
known issues are in `docs/COMMAND_TOOLS.md` in the repository.

