# Agent Guide for sublime-mcp (MCP Commander)

This document teaches AI agents how to use sublime-mcp tools correctly.
Read this before editing files, closing tabs, or running ST commands.

## Critical Rules

### Editing Files
**The `str_replace_based_edit_tool` edits the ST buffer in memory but does NOT save to disk.**
After every edit, you MUST call `save_file` with the file path:

1. `str_replace_based_edit_tool` (command="str_replace") → edits buffer
2. `save_file` (path="C:\\path\\to\\file.py") → writes to disk

If you skip step 2, the file will be dirty in ST but unchanged on disk.
This causes desync — ST shows your edits but `git diff` shows nothing.

### Disk vs Buffer
- `edit` tool (OpenClaw): writes directly to disk, ST buffer may be stale
- `str_replace_based_edit_tool` (sublime-mcp): writes to ST buffer, disk may be stale
- If you use `edit` on a file open in ST, call `revert_file` after so ST reloads from disk
- If you use `str_replace_based_edit_tool`, call `save_file` after so disk matches buffer

### Closing Tabs
`close_file` takes a `path` parameter. If the file is dirty (unsaved changes),
ST will prompt the user to save — the tool will hang.

To close a dirty/scratch tab safely:
```python
# eval_python: mark as scratch and close
v = window.find_open_by_name("untitled")  # or find by id
v.set_scratch(True)
v.close()
```

`eval_python` works — use `print()` to get output. The environment has:
- `sublime` — the sublime module
- `window` — the active window
- `view` — the active view
- `print` — writes to captured output

### eval_python Usage
- Use `print()` to return values — the output is captured and returned
- Do NOT use `return` at top level (syntax error)
- Do NOT use bare expressions expecting output (use `print(expr)`)
- The environment has `sublime`, `window`, `view` available

## Key ST API Methods for Agents

### Window
- `window.views()` — list all views in the window
- `window.active_view()` — get the focused view
- `window.active_group()` — get active group index
- `window.find_open_file(path)` — find a view by file path
- `window.open_file(path)` — open a file
- `window.run_command(cmd, args)` — run a window command
- `window.new_file()` — create untitled buffer
- `window.sheets()` — list all sheets (tabs)

### View
- `view.file_name()` — file path (None for untitled)
- `view.name()` — display name
- `view.is_dirty()` — has unsaved changes
- `view.set_scratch(True)` — mark as scratch (no save prompt on close)
- `view.close()` — close the view (may prompt if dirty)
- `view.run_command(cmd, args)` — run a text command on this view
- `view.substr(region)` — get text in region
- `view.size()` — total character count
- `view.find_all(pattern, flags)` — find all matches

### Sheet
- `sheet.close()` — close a sheet (may not work on dirty sheets)
- `sheet.view()` — get the view for a text sheet

## Common Operations

### Save a file
```
save_file(path="C:\\path\\to\\file.py")
```
Omit path to save the active file.

### Save all open files
```
save_all()
```

### Revert file (discard unsaved changes, reload from disk)
```
revert_file()
```
Works on the active file only.

### Close a file by path
```
close_file(path="C:\\path\\to\\file.py")
```
Only works if the file is NOT dirty. If dirty, save first or use eval_python with set_scratch.

### Close a dirty/untitled/scratch tab
```python
# eval_python
for v in window.views():
    if v.name() == "Config warnings:" or (v.is_dirty() and not v.file_name()):
        v.set_scratch(True)
        v.close()
        print("closed")
        break
print("done")
```

### Open a file at a specific line
```
open_file(path="C:\\path\\to\\file.py", line=42, col=1)
```

### Run a Sublime command
```
run_command(command="close_file", scope="window")
```
Scopes: "window" (default), "view", "application".
Check available commands with `get_commands`.

### Get all tabs info
```
get_sheets()
```
Returns index, type, path, name, is_dirty for each tab.

### Read a tab by index
```
get_sheet_content(index=2)
```

## Tool Reliability Notes

- `str_replace_based_edit_tool` reports success but does NOT persist to disk
- `close_file` by path works only for non-dirty files
- `eval_python` works reliably — use `print()` for output
- `save_file` by path works reliably when the file is open in ST
- `get_sheets` / `get_sheet_content` work reliably for reading tab state
- `run_command` works but you must know the correct command name and scope
- `find_in_files` works for searching project files
- `get_commands` lists available commands but without descriptions or arg schemas

## Gaps to Address in sublime-mcp

1. **str_replace should auto-save** (or offer a save option)
2. **close_file should handle dirty files** (set_scratch + close, or return error with guidance)
3. **get_commands should return descriptions and arg schemas** (not just IDs)
4. **No close_sheet by index/ID** — must use eval_python workaround
5. **eval_python output can be empty if code uses return instead of print**
6. **No tool to check if buffer matches disk** (is_dirty is available but not "is stale")

## Critical Lessons Learned

### NEVER use `insert` command to paste large content
ST's auto-indent will mangle every line by accumulating indentation. Using `v.run_command("insert", {"characters": content})` on a full file will destroy the indentation — each line gets indented on top of the previous line's indentation.

**Instead use:**
- `str_replace_based_edit_tool` for targeted text replacements
- `replace_lines` to replace specific line ranges by line number
- For copying content between views: read source with `substr`, then use `replace_lines` on the target

### To revert a file to disk state
`revert` command sometimes doesn't fully reload the buffer. Reliable approach:
```python
# eval_python
path = view.file_name()
view.set_scratch(True)
view.close()
window.open_file(path)
```

### To apply edits from a preview tab to the real file
Do NOT copy entire file content via `insert`. Instead:
1. Make targeted edits directly on the real file using `str_replace_based_edit_tool`
2. Save with `save_file`
3. Verify with `is_dirty` check (should be False after save)

### File editing workflow with diff preview
1. Open the real file in ST
2. Create a new untitled tab with a copy of the file content (use `replace_lines` not `insert`)
3. Make edits in the preview tab
4. Use DiffTabs (`diff_tabs_palette`) or side-by-side layout to review
5. After approval, make the same targeted edits on the real file with `str_replace_based_edit_tool`
6. Save with `save_file`
7. Close the preview tab
