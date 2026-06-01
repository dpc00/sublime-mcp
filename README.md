# sublime-mcp

<!-- mcp-name: io.github.dpc00/sublime-mcp -->


MCP server for Sublime Text 4. Lets Claude Code (or any MCP client) read and
control a running ST instance via a local HTTP bridge.

59 tools covering reading, navigation, editing, searching, build, Terminus
integration, settings, layout, and live Python scripting.

## Architecture

```
Claude Code (MCP client)
        │  stdio / MCP protocol
        ▼
  mcp_server.py          ← Python process you run outside ST
        │  HTTP  127.0.0.1:9500
        ▼
  sublime_mcp.py         ← ST plugin, HTTP server on ST's main thread
        │  sublime API
        ▼
  Sublime Text 4
```

| File | Role |
|------|------|
| `sublime_mcp.py` | ST plugin — runs an HTTP server inside Sublime Text |
| `mcp_server.py` | MCP server — wraps the HTTP API for MCP clients |

## Installation

### 1. Install the ST plugin

Copy `sublime_mcp.py` to your Sublime Text `Packages/User/` folder:

```
%APPDATA%\Sublime Text\Packages\User\sublime_mcp.py
```

ST loads it automatically on start (or via `Tools › Developer › New Plugin…`
then save over it). You should see:

```
sublime-mcp: listening on 127.0.0.1:9500
```

in the ST console (`View › Show Console`).

### 2. Install the MCP server

```
pip install sublime-mcp
```

### 3. Register with Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "sublime": {
      "command": "sublime-mcp"
    }
  }
}
```

Then restart Claude Code. Tools will appear with the `mcp__sublime__` prefix.

Then restart Claude Code. Tools will appear with the `mcp__sublime__` prefix.

## Tab and Sheet Indexing

**IMPORTANT:** Users refer to tabs by 1-based numbering (tab 1, tab 2, etc.), but 
`get_sheets()` returns 0-based indexes. Always convert user tab references before using:
- User **tab 1** = index 0
- User **tab 2** = index 1
- User **tab 3** = index 2
- etc.

When closing or targeting a specific tab, always verify the index by calling `get_sheets()` 
first, and close by path (preferred) or by focusing then closing the active file. 
**Never change focus without user awareness.**

## Tools

### Read / Introspect

| Tool | Description |
|------|-------------|
| `get_active_file` | Path, full content, cursor line/col, dirty flag, and syntax name |
| `get_selection` | Current selection(s): text and begin/end line+col for each |
| `get_cursor_context` | `lines` lines above and below cursor, with 1-based line numbers prepended |
| `get_open_files` | All files open in the current window (path, name, is_dirty) |
| `get_project_folders` | Project root folder paths |
| `get_file_content` | Full content of any already-open file by path |
| `get_view_content` | Full content of any open tab by name (partial match). Works for Terminus tabs and nameless views |
| `get_view_size` | Total character count of any open tab. Use to compute offsets before `get_view_chars` |
| `get_view_chars` | Text at character offsets begin..end (0-based, end exclusive). Clamps to buffer bounds |
| `get_view_phantoms` | Phantom HTML and extracted plain text from a named view; filters by phantom key |
| `get_output_panel` | Text content of a named output panel. Omit name for the active panel; `name='exec'` for build output |
| `get_active_panel` | Active panel id and, if it is an output panel, its content |
| `get_symbols` | All symbols (functions, classes, etc.) in the active file with line numbers |
| `lookup_symbol` | Find where a symbol is defined across all open files |
| `get_project_data` | Raw `.sublime-project` JSON for the current project |
| `get_variables` | ST build variables: `$file`, `$project_path`, `$platform`, etc. |
| `get_command_palette` | Command Palette entries from installed `*.sublime-commands` resources; filterable by package, command, or caption |
| `get_commands` | Runnable command ids from loaded command classes, optionally merged with palette metadata |
| `get_menu_items` | Menu items from `*.sublime-menu` resources; filterable by menu filename, caption, or command |
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
| `edit_file` | ST-native editor: `str_replace` (unique match), `insert` (after line N), `create` (new file), `view` (numbered content). Full undo, gutter diff, 30s highlight. Auto-opens file if needed |
| `replace_selection` | Replace the current selection(s) with text |
| `replace_lines` | Replace lines begin..end (inclusive, 1-based) in the active file |
| `insert_snippet` | Insert at the cursor using ST snippet syntax (`$1` for tab stops, etc.) |
| `duplicate_line` | Duplicate the current line(s) |
| `toggle_comment` | Toggle line comment, or block comment if `block=True` |
| `sort_lines` | Sort selected lines, or all lines if nothing is selected |
| `select_lines` | Select lines begin..end (1-based, inclusive) |
| `fold_lines` | Fold (collapse) lines begin..end in the active file |
| `undo` | Undo the last edit |
| `redo` | Redo the last undone edit |
| `run_command` | Run any ST command with optional args. `scope='window'` (default) or `'view'` |

### Search

| Tool | Description |
|------|-------------|
| `find_in_file` | Find all occurrences of a pattern in the active file. Returns `{line, col, text}` list |
| `find_in_files` | Search across project folders (or a supplied list). Skips `.git`, `__pycache__`, `node_modules`, `.venv`. Returns `{path, line, match}` list, capped at `max_results` (default 200) |

### File / Project

| Tool | Description |
|------|-------------|
| `save_file` | Save the active file |
| `save_all` | Save all open files |
| `close_file` | Close a file by path, or the active file if path is omitted |
| `revert_file` | Revert the active file to its last saved state |
| `add_folder` | Add a folder to the current project (no-op if already present) |
| `remove_folder` | Remove a folder from the current project by path |

### Syntax / Encoding

| Tool | Description |
|------|-------------|
| `set_syntax` | Set the syntax of the active file by name (case-insensitive partial match) |
| `set_encoding` | Set the character encoding of the active file (e.g. `'UTF-8'`, `'Western (Windows 1252)'`) |

### Settings / Window

| Tool | Description |
|------|-------------|
| `set_setting` | Set a ST setting by key. `scope='view'` (default) or `'window'` |
| `toggle_sidebar` | Show or hide the sidebar |
| `set_layout` | Set the window pane layout. Accepts a ST layout dict with `cols`, `rows`, `cells` |
| `set_status` | Write a message to ST's status bar |

### Build

| Tool | Description |
|------|-------------|
| `run_build` | Trigger the current build system, or pass `cmd`/`shell_cmd` + `working_dir` for a custom command |

### Terminus Integration

[Terminus](https://github.com/randy3k/Terminus) is a popular ST terminal package.
`send_to_view` is Terminus-aware: when targeting a Terminus tab it uses
`terminus_send_string` to type text into the terminal session rather than
inserting into a buffer.

| Tool | Description |
|------|-------------|
| `send_to_view` | Send a string to any open tab by name. For Terminus tabs, types the text as if the user typed it. Include a trailing `\n` to execute a command |

### Scripting

| Tool | Description |
|------|-------------|
| `eval_python` | Execute arbitrary Python in ST's main thread. Locals available: `sublime`, `window`, `view`, `print`. Returns captured stdout in `output` |

## Configuration

### Port

Default is `9500`. To change it, edit `_PORT` in `sublime_mcp.py` and `BASE` in `mcp_server.py`.

### Timeout

The MCP server waits up to 10 seconds for each HTTP response. Edit `TIMEOUT` in
`mcp_server.py` if you need longer (e.g. for slow `eval_python` calls).

## Security note

The HTTP server binds to `127.0.0.1` only and accepts any request without
authentication. Do not expose port 9500 to a network interface.

## Requirements

- Sublime Text 4
- Python 3.10+ (for the MCP server process)
- `pip install mcp httpx`
- Terminus package (optional, required only for `send_to_view` on terminal tabs)
