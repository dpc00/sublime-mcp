# sublime-mcp

MCP server for Sublime Text 4. Lets Claude Code (or any MCP client) read and
control a running ST instance via a local HTTP bridge.

## Components

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

ST will load it automatically. You should see `sublime-mcp: listening on 127.0.0.1:9500` in the ST console.

### 2. Install the MCP server

```
pip install mcp httpx
```

### 3. Register with Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "sublime": {
      "command": "python",
      "args": ["C:/path/to/sublime-mcp/mcp_server.py"]
    }
  }
}
```

Then restart Claude Code.

## Tools

### Read
| Tool | Description |
|------|-------------|
| `get_active_file` | Path, full content, cursor position, syntax, dirty flag |
| `get_selection` | Current selection(s) with text and line/col ranges |
| `get_cursor_context` | N lines around the cursor with line numbers |
| `get_open_files` | All open files in the current window |
| `get_project_folders` | Project root folders |
| `get_file_content` | Content of any open file by path |
| `get_output_panel` | Content of a named output panel, or the active output panel if omitted |
| `get_symbols` | Functions/classes in the active file |
| `lookup_symbol` | Find a symbol's definition across open files |
| `get_project_data` | Raw `.sublime-project` JSON |
| `get_variables` | ST build variables (`$file`, `$project_path`, etc.) |
| `get_command_palette` | Installed Command Palette entries from `.sublime-commands` resources |
| `get_commands` | Runnable command ids from loaded command classes, optionally merged with palette metadata |
| `get_menu_items` | Installed menu items from `.sublime-menu` resources |
| `get_active_panel` | Active panel id and, for output panels, the current panel content |

### Navigate
| Tool | Description |
|------|-------------|
| `open_file` | Open a file, optionally at line:col |
| `goto_line` | Move cursor to line (and col) in the active file |
| `show_panel` | Bring an output panel to the front |

### Edit
| Tool | Description |
|------|-------------|
| `replace_selection` | Replace the current selection with text |
| `replace_lines` | Replace a line range (1-based, inclusive) with text |
| `run_command` | Run any ST command with optional args |

### Build
| Tool | Description |
|------|-------------|
| `run_build` | Trigger the current build system or a custom command |

### Misc
| Tool | Description |
|------|-------------|
| `set_status` | Write a message to ST's status bar |

## Port

Default port is `9500`. To change it, edit `_PORT` in `sublime_mcp.py` and
`BASE` in `mcp_server.py`.

## Requirements

- Sublime Text 4
- Python 3.10+ (for the MCP server)
- `pip install mcp httpx`
