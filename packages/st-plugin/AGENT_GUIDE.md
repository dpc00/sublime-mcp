# Agent Guide for sublime-mcp (MCP Commander)

How to use sublime-mcp tools. Call `get_help` if you are unsure how to
save, close tabs, or run ST Python.

220 typed tools. Prefer a named tool over `run_command`. `run_command` often
opens ST UI that steals keyboard focus from the agent chat.

ST tools use **1-based** line/column (`get_active_file`, `open_file`,
`goto_line`, `replace_lines`). lsp-mcp uses **0-based**. Subtract 1 when
passing an ST cursor into an `lsp_*` tool.

## Batch (cuts round trips)

Each call pays a trip through ST's main-thread scheduler. For 2+ independent
calls, use `batch` (max 50; cannot call itself):

```
batch(calls=[
  {"tool": "get_active_file"},
  {"tool": "get_selection"},
  {"tool": "get_cursor_context", "args": {"lines": 20}},
])
```

Returns `{"results": [...]}` in call order. A failed call is `{"error": ...}`
in its slot; the rest still run.

## Editing

`str_replace_based_edit_tool` edits the **buffer**, not disk. Always save:

1. `str_replace_based_edit_tool(command="str_replace", path=..., old_str=..., new_str=...)`
2. `save_file(path=...)` — omit `path` to save the active file

Skip save and ST looks edited while `git diff` is empty.

- Disk `edit`/`write` on a file ST has open → `revert_file` so the buffer reloads.
- Whole-line / multi-line insert → `replace_lines(begin, end, text)`, never `insert`.
- `insert` (and `view.run_command("insert", ...)`) auto-indents every line and
  piles indentation. Do not paste large content with it.
- `str_replace` `old_str` must match **exactly once**.
- Commands: `str_replace`, `insert` (after 1-based `insert_line`; `0` = start),
  `create`, `view`.

## Closing tabs

`close_file(path=...)` hangs if the view is dirty (ST save prompt). Save
first, or mark scratch via `eval_python`:

```python
for v in window.views():
    if v.is_dirty() and not v.file_name():
        v.set_scratch(True)
        v.close()
        print("closed")
        break
```

Find a path with `window.find_open_file(path)` (there is no
`find_open_by_name`).

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
get_sheets()                       # every tab: index, type, path, name, is_dirty
get_sheet_content(index=2)         # untitled / scratch / Terminus too
open_file(path=..., line=42, col=1)
save_all()
revert_file()                      # active view only
find_in_files(pattern=..., where=...)   # ST C++ Find-in-Files (Ctrl+Shift+H)
get_commands()                     # command ids, scopes, packages, palette captions
```

`find_in_files` `where` accepts folder paths, `*.py`, `-*.md`, `${project}`,
`${open_files}`, `${folder:Name}`.

## Do not

- Run shell/builds via ST `exec` / `run_build` — the user cannot reliably cancel.
- Live-invoke UI tools while verifying new routes: `prompt_goto_line`,
  `quick_panel`, `select_color_scheme`, `select_theme`, `open_in_browser`,
  `html_print`, `customize_*`, `convert_*`, `edit_syntax_settings`. Confirm
  they exist in `_MCP_TOOLS`; do not POST them at the user.

## Reliable reload

If `revert_file` is not enough:

```python
path = view.file_name()
view.set_scratch(True)
view.close()
window.open_file(path)
```
