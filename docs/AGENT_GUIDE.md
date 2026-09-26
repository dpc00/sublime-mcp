# Agent Guide for sublime-mcp (MCP Commander)

Canonical copy for repo readers. `get_help` serves
`AGENT_GUIDE.md` (repo root) — keep these two files in sync.

How to use sublime-mcp tools. Call `get_help` if you are unsure how to
save, close tabs, or run ST Python.

Seven workflow tools are shown by default; the complete typed catalog (399
tools since 1.9.0) remains available through `discover_tools` and `batch`. Prefer a named capability over
`run_command`, which often opens UI that steals focus from the agent chat.

On the first Sublime operation, call `get_help` once.

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
get_sheets()                       # every tab: stable id, group/index, selection/focus, path/name
get_selected_sheets(group=0)      # native tab multi-selection, optionally by group
select_sheets(ids=[...])           # select tabs together; indices=[...] also works
focus_sheet(id=...)                # focus one sheet without replacing the selected set
move_sheets_to_group(ids=[...], group=0)  # move a selected tab collection together
get_sheet_content(index=2)         # untitled / scratch / Terminus too
open_file(path=..., line=42, col=1)
save_all()
revert_file()                      # active view only
project_search(pattern=..., where=...)  # ST Find-in-Files, structured matches
discover_tools(query="bookmarks")       # find an advanced capability
get_commands()                     # command ids, scopes, packages, palette captions
```

`project_search` `where` accepts folder paths, `*.py`, `-*.md`, `${project}`,
`${open_files}`, `${folder:Name}`.

## Sublime Text command tools (since 1.9.0)

160 of the 399 tools are generated wrappers named exactly after a Sublime Text
command (`add_word`, `fold_all`, `invert_selection`, `scroll_to_eof`, `chain`,
`build`, `close_others_by_index`, ...). They come from a snapshot of
CommandsBrowser's Sublime Text command list, written by
`tools/generate_st_command_tools.py`. Find one with
`discover_tools(query="fold")` and run it with `batch`, like any other tool.

- **Kind.** The description ends with `(TextCommand)`, `(WindowCommand)` or
  `(ApplicationCommand)`: text commands run on the active view, window
  commands on the active window (86 window, 59 text, 15 application).
- **Arguments** are forwarded unchanged to the Sublime command, with Sublime's
  own names and conventions (for example `group` and `index` are 0-based). They
  do **not** follow the 1-based line/column of the hand-written tools. Nothing
  is marked required in the schema; Sublime rejects a missing argument itself.
  60 of these tools take arguments, 100 take none.
- **`{"ok": true}` only means the command was dispatched.** Confirm the effect
  with a read tool (`get_selection`, `get_sheets`, ...).
- **Prefer the hand-written tool** when one exists for the same job
  (`save_file`, `open_file`, `close_file`, `replace_lines`): it handles prompts,
  focus and edge cases the raw command does not.

### What the command tools were observed to do

Every generated tool was run on a disposable, bare Sublime Text 4215 (only
MCP Commander installed): once with no arguments, and, for the 59 that take
arguments, once more with sandbox arguments. What was seen is in
`tools/st_commands_behavior.json` (harness: `tools/probe_st_commands.py`), and
44 tool descriptions say so ("Observed on Sublime Text 4215: ..."). Read that
sentence before calling a command tool.

- **Blocks Sublime's main thread until a person dismisses a native window (16).**
  Nothing can answer the window through this server, and every other tool
  stalls (`eval_python` times out after 5 s) until it is closed: `context_menu`,
  `delete_file` and `delete_folder` (confirmation dialogs), `open_project_or_workspace`,
  `primary_j_changed`, `prompt_add_folder`, `prompt_open_file`, `prompt_open_folder`,
  `prompt_open_project_or_workspace`, `prompt_save_as`,
  `prompt_switch_project_or_workspace`, `remove_license`,
  `save_project_and_workspace_as`, `save_workspace_as`, `sublime_merge_blame_file`,
  `sublime_merge_file_history`. Never call these unattended.
- **Quits Sublime Text (3), and the server with it:** `exit`, `hot_exit`, and
  `close_window` (closing the last window quits).
- **Opens a window that does not block (7):** `prompt_select_workspace`,
  `set_file_type`, `show_about_window`, `show_changelog`, `show_license_window`,
  `show_progress_window`, `update_check`. `new_window` opens a new Sublime window.
- **Leaves an in-app panel, popup or overlay open (6):** `auto_complete`,
  `build`, `prompt_open`, `rename_path`, `replace_completion_with_auto_complete`,
  `toggle_show_open_files`. Dismiss with `hide_overlay`, `hide_panel` or `hide_popup`.
- **Opens the browser or file manager:** `upgrade_license` (seen), and from
  their documentation, not run by the probe: `purchase_license`, `open_url`,
  `open_dir`.
- **Writes something:** settings (`add_word`, `ignore_word`,
  `increase_font_size`, `decrease_font_size`, `reset_font_size`), files (`save`,
  `open_project_or_workspace`), the clipboard (`copy_as_html`).
- **Discards data (from the command documentation):** `revert`, `revert_hunk`,
  `revert_modification`; `delete_file` / `delete_folder` move to the recycle bin
  after the confirmation dialog.
- The other **116** showed no effect in the probe. That does not prove they do
  nothing: many need a selection, an open panel, a project or specific arguments.
- `disabled_tools` in `MCP Commander.sublime-settings` refuses any tool by name.
- The 239 hand-written tools were not part of this probe.

## Known issues

- `get_console(mode='visible')` / `mode='auto'` (and the `get_console_full`
  / `get_console_win` aliases) read Sublime's console via OS-level UI
  automation on Windows. In Claude Code specifically, this can trigger an
  upstream harness bug where the client shows "Interrupted, what do you
  want to do instead?" even though nothing was actually interrupted — no
  permission prompt appears, and the call has already completed by the
  time the message shows up. This is a bug in Claude Code's own bundled
  code (filed as anthropics/claude-code#93529), not in sublime-mcp; it has
  been confirmed not to be caused by any individual mechanism the Windows
  console reader uses (focus changes, clipboard access, `set_timeout`
  hops).
  `mode='captured'` does not use OS-level automation and does not trigger
  this, but it is **not a guaranteed substitute**: it only contains
  messages observed since capture began, so an error emitted earlier (e.g.
  before the MCP connection was established, or before this specific
  capture buffer started) will not appear there even though it did happen.
  Pick the mode deliberately based on what you're trying to catch, rather
  than treating one as a strictly safer default for the other.

## Do not

- Run shell/builds via ST `exec` / `run_build` — the user cannot reliably cancel.
- Live-invoke UI tools while verifying new routes: `prompt_goto_line`,
  `quick_panel`, `select_color_scheme`, `select_theme`, `open_in_browser`,
  `html_print`, `customize_*`, `convert_*`, `edit_syntax_settings`, and any
  generated command tool whose description says it "blocks Sublime's main
  thread", "quits Sublime Text", "opens the web browser" or starts with
  "Warning:" (see "What the command tools were observed to do"). Confirm they
  exist in `_MCP_TOOLS`; do not POST them at the user.

## Reliable reload

If `revert_file` is not enough:

```python
path = view.file_name()
view.set_scratch(True)
view.close()
window.open_file(path)
```
