# MCP Commander

<!-- mcp-name: io.github.dpc00/sublime-mcp -->

Exposes Sublime Text to AI assistants (Claude Code, Cursor, etc.) via the
Model Context Protocol.  The MCP server is built directly into the ST plugin —
no separate process or external dependency required.

63 tools covering reading, navigation, editing, searching, build, Terminus
integration, settings, layout, menus, console log, and live Python scripting.

## Architecture

The plugin runs two local servers on startup:

| Server | Default port | Purpose |
|--------|-------------|---------|
| MCP SSE | 9502 (Win) / 9503 (Mac/Linux) | MCP 2024-11-05 SSE transport — connect your agent here |
| HTTP bridge | 9500 (Win) / 9501 (Mac/Linux) | Internal REST API used by the SSE dispatcher |

```
Claude Code (MCP client)
        │  MCP SSE  (port 9502)
        ▼
  sublime_mcp.py  ←  ST plugin — MCP server + HTTP bridge, all in one file
        │  sublime API
        ▼
  Sublime Text 4
```

## Installation

### 1. Install via Package Control

1. Open the Command Palette (`Ctrl+Shift+P`)
2. Run **Package Control: Install Package**
3. Search for **MCP Commander** and install

The plugin loads automatically.  Check `View › Show Console` for:

```
sublime-mcp: MCP SSE on 127.0.0.1:9502, HTTP bridge on 127.0.0.1:9500
```

> **Manual install:** copy `sublime_mcp.py` (and optionally `sublime_mcp_browse.py`)
> into your `Packages/User/` folder.

### 2. Register with Claude Code

Add to `~/.claude/settings.json` under `"mcpServers"`:

**Windows:**
```json
"sublime-mcp": { "type": "sse", "url": "http://127.0.0.1:9502/sse" }
```

**Mac / Linux:**
```json
"sublime-mcp": { "type": "sse", "url": "http://127.0.0.1:9503/sse" }
```

Restart Claude Code. Tools appear with the `mcp__sublime-mcp__` prefix.

## Server management

The MCP server starts automatically when ST loads the plugin.  To stop or
restart it, open the Command Palette and run:

> **MCP Commander: Server Status**

The panel shows whether the server is running and on which port, and lets you
start or stop it with a single keypress.

## Tab and Sheet Indexing

**IMPORTANT:** Users refer to tabs by 1-based numbering (tab 1, tab 2, etc.), but
`get_sheets()` returns 0-based indexes. Always convert user tab references before using:
- User **tab 1** = index 0
- User **tab 2** = index 1

When targeting a specific tab, call `get_sheets()` first to verify the index.

## Tools

### Read / Introspect

| Tool | Description |
|------|-------------|
| `get_active_file` | Path, full content, cursor line/col, dirty flag, and syntax name |
| `get_selection` | Current selection(s): text and begin/end line+col for each |
| `get_cursor_context` | `lines` lines above and below cursor, with 1-based line numbers prepended |
| `get_open_files` | All files open in the current window (path, name, is_dirty) |
| `get_sheets` | All sheets (tabs) in the window by index — includes images and untitled buffers |
| `get_sheet_content` | Content of any tab by sheet index (from `get_sheets`) |
| `get_project_folders` | Project root folder paths |
| `get_file_content` | Full content of any already-open file by path |
| `get_view_content` | Full content of any open tab by name (partial match, case-insensitive) |
| `get_view_size` | Total character count of any open tab |
| `get_view_chars` | Text at character offsets begin..end (0-based, end exclusive) |
| `get_view_phantoms` | Phantom HTML and extracted plain text from a named view |
| `get_output_panel` | Text content of a named output panel (`name='exec'` for build output) |
| `get_active_panel` | Active panel id and, if it is an output panel, its content |
| `get_symbols` | All symbols (functions, classes, etc.) in the active file with line numbers |
| `lookup_symbol` | Find where a symbol is defined across all open files |
| `get_project_data` | Raw `.sublime-project` JSON for the current project |
| `get_variables` | ST build variables: `$file`, `$project_path`, `$platform`, etc. |
| `get_command_palette` | Command Palette entries from installed `*.sublime-commands` resources |
| `get_commands` | Runnable command ids from loaded command classes |
| `get_menu_items` | Menu items from `*.sublime-menu` resources |
| `get_syntaxes` | All syntax definitions available in ST (name + path) |
| `get_scope_at_cursor` | Full syntax scope string at the cursor position |
| `get_word_at_cursor` | Word under the cursor and its line/col |
| `get_bookmarks` | All bookmarked positions in the active file |
| `get_line_count` | Total number of lines in the active file |
| `get_encoding` | Character encoding of the active file |
| `get_setting` | A ST setting by key. `scope='view'` (default) or `'window'` |
| `get_layout` | Current window layout (groups, cells) and which files are in each group |

### Navigate

| Tool | Description |
|------|-------------|
| `open_file` | Open a file, optionally jumping to a specific line and column |
| `goto_line` | Move cursor to line (and optional column) in the active file |
| `show_panel` | Bring an output panel to the front. Default `name='exec'` for the build panel |
| `focus_group` | Move focus to a pane group by 0-based index |

### Edit

| Tool | Description |
|------|-------------|
| `str_replace_based_edit_tool` | ST-native editor: `str_replace`, `insert`, `create`, `view`. Full undo, gutter diff, 30s highlight |
| `replace_selection` | Replace the current selection(s) with text |
| `replace_lines` | Replace lines begin..end (inclusive, 1-based) in the active file |
| `insert_snippet` | Insert at the cursor using ST snippet syntax |
| `duplicate_line` | Duplicate the current line(s) |
| `toggle_comment` | Toggle line comment, or block comment if `block=True` |
| `sort_lines` | Sort selected lines, or all lines if nothing is selected |
| `select_lines` | Select lines begin..end (1-based, inclusive) |
| `fold_lines` | Fold (collapse) lines begin..end in the active file |
| `undo` | Undo the last edit |
| `redo` | Redo the last undone edit |
| `run_command` | Run any ST command with optional args |

### Search

| Tool | Description |
|------|-------------|
| `find_in_file` | Find all occurrences of a pattern in the active file |
| `find_in_files` | Search across project folders. Skips `.git`, `__pycache__`, `node_modules`, `.venv` |

### File / Project

| Tool | Description |
|------|-------------|
| `save_file` | Save the active file (or a specific file by path) |
| `save_all` | Save all open files |
| `close_file` | Close a file by path, or the active file if path is omitted |
| `revert_file` | Revert the active file to its last saved state |
| `add_folder` | Add a folder to the current project |
| `remove_folder` | Remove a folder from the current project by path |

### Syntax / Encoding

| Tool | Description |
|------|-------------|
| `set_syntax` | Set the syntax of the active file by name (case-insensitive partial match) |
| `set_encoding` | Set the character encoding of the active file |

### Settings / Window

| Tool | Description |
|------|-------------|
| `set_setting` | Set a ST setting by key |
| `toggle_sidebar` | Show or hide the sidebar |
| `set_layout` | Set the window pane layout |
| `set_status` | Write a message to ST's status bar |

### Build

| Tool | Description |
|------|-------------|
| `run_build` | Trigger the current build system, or pass `cmd`/`shell_cmd` for a custom command |

### Terminus Integration

[Terminus](https://github.com/randy3k/Terminus) is a popular ST terminal package.
`send_to_view` is Terminus-aware: when targeting a Terminus tab it uses
`terminus_send_string` to type text into the terminal session.

| Tool | Description |
|------|-------------|
| `send_to_view` | Send text to any open tab. For Terminus tabs, types as if the user typed it. Include `\n` to execute |

### Scripting

| Tool | Description |
|------|-------------|
| `eval_python` | Execute arbitrary Python in ST's main thread. Returns captured stdout in `output` |
| `eval_python_latest` | Execute Python in the system interpreter outside ST's sandbox |
| `get_console_log` | Recent ST console output. `tail=N` limits to last N entries |
| `get_console_full` | Entire captured ST console buffer since startup |

## Configuration

### Ports

| Server | Windows | Mac/Linux | Env var override |
|--------|---------|-----------|-----------------|
| MCP SSE | 9502 | 9503 | `SUBLIME_MCP_MCP_PORT` |
| HTTP bridge | 9500 | 9501 | `SUBLIME_MCP_PORT` |

### Telling Claude how to use the tools

Add a section like this to your project's `CLAUDE.md` (or `~/.claude/CLAUDE.md`):

```markdown
## Sublime Text MCP tools

MCP Commander is connected. Prefer it over standard file tools when working in ST:

- Read files with `get_active_file` or `get_file_content` rather than the Read tool
- Edit with `str_replace_based_edit_tool` — edits appear live with gutter diff and undo
- Use `find_in_files` for project-wide search
- Use `send_to_view` to run commands in a Terminus terminal tab
- Use `eval_python` for one-off ST scripting (no plugin file needed)
- Check `get_console_log` when a plugin isn't behaving as expected

Tab indexing: `get_sheets()` returns 0-based indexes; users refer to tabs
1-based. Always call `get_sheets()` first when targeting a specific tab.
```

## Security note

Both servers bind to `127.0.0.1` only and accept any request without
authentication. Do not expose these ports to a network interface.

## Requirements

- Sublime Text 4
- Terminus package (optional — only required for `send_to_view` on terminal tabs)

## Known limitations

- **No multi-window support** — tools target the most recently focused ST window
- **No image editing** — `get_sheet_content` returns the path for image tabs, not pixel data
- **No ST3 support** — the plugin uses ST4 APIs throughout

## Testing

The test suite requires Sublime Text to be running with `sublime_mcp.py` loaded.

```
cd /path/to/sublime-mcp
pip install httpx pytest
pytest tests/ -v
```

## Contributing

**Adding a tool:**
1. Add a handler function in `sublime_mcp.py` (run via `_on_main` for ST API calls)
2. Add an entry to `_MCP_TOOLS` and the `_GET` / `_POST` routing dicts
3. Add a row to the Tools table in `README.md`

**Good first issues:**
- Multi-window support (`sublime.windows()` instead of `sublime.active_window()`)
- `get_diagnostics` — expose LSP error/warning annotations
- `set_bookmark` / `clear_bookmarks` — write counterparts to `get_bookmarks`

Open an issue or PR on [GitHub](https://github.com/dpc00/sublime-mcp).
