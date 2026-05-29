"""sublime-mcp — MCP server.

Wraps the HTTP API exposed by sublime_mcp.py (the ST plugin) and
presents it as MCP tools to Claude Code (or any MCP client).

Requirements: pip install mcp httpx
Run:          python mcp_server.py
Register:     add to ~/.claude/settings.json mcpServers
"""
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

BASE = "http://127.0.0.1:9500"
TIMEOUT = 10.0

mcp = FastMCP("sublime-mcp")


def _get(endpoint: str, **params) -> dict:
    r = httpx.get(f"{BASE}{endpoint}", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _post(endpoint: str, **body) -> dict:
    r = httpx.post(f"{BASE}{endpoint}", json=body, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


# ── read ──────────────────────────────────────────────────────────────────────


@mcp.tool()
def get_active_file() -> dict:
    """Return the active file's path, full content, cursor line/col, dirty flag, and syntax name."""
    return _get("/active_file")


@mcp.tool()
def get_selection() -> dict:
    """Return the current selection(s): text and begin/end line+col for each."""
    return _get("/selection")


@mcp.tool()
def get_cursor_context(lines: int = 10) -> dict:
    """Return `lines` lines above and below the cursor with 1-based line numbers prepended."""
    return _get("/cursor_context", lines=lines)


@mcp.tool()
def get_open_files() -> dict:
    """List all files open in the current window (path, name, is_dirty)."""
    return _get("/open_files")


@mcp.tool()
def get_sheets() -> dict:
    """List ALL sheets (tabs) in the current window by index, including images and untitled buffers.
    Returns index, type (TextSheet/ImageSheet), path, name, is_dirty for each.
    Use index with get_sheet_content to read a specific tab."""
    return _get("/sheets")


@mcp.tool()
def get_sheet_content(index: int) -> dict:
    """Return the content of any tab by its sheet index (from get_sheets).
    Works for text tabs including untitled buffers and Terminus tabs.
    For image tabs returns the file path only."""
    return _get("/sheet_content", index=index)


@mcp.tool()
def get_project_folders() -> dict:
    """Return the project's root folder paths."""
    return _get("/project_folders")


@mcp.tool()
def get_file_content(path: str) -> dict:
    """Return the full content of an already-open file by its path."""
    return _get("/file_content", path=path)


@mcp.tool()
def get_view_content(name: str = "", index: int = -1) -> dict:
    """Return the full content of any open tab by name (partial match, case-insensitive).
    Works for Terminus tabs and other nameless views that have no file path.
    Use index (0-based, from get_open_files) to target a tab by position instead of name.
    Omit both to read the active view."""
    return _get("/view_content", name=name, index=index)


@mcp.tool()
def get_view_size(name: str = "") -> dict:
    """Return the total character count of any open tab by name (partial match, case-insensitive).
    Use before get_view_chars to compute offsets — e.g. begin=size-5000, end=size for the tail.
    Omit name for the active view."""
    return _get("/view_size", name=name)


@mcp.tool()
def get_view_chars(begin: int, end: int, name: str = "") -> dict:
    """Return text at character offsets begin..end (0-based, end exclusive) from any open tab.
    Works for Terminus tabs and any other view.  Clamps to buffer bounds automatically.
    Use get_view_size first, then e.g. begin=size-5000, end=size to read the last 5000 chars.
    Omit name for the active view."""
    return _get("/view_chars", name=name, begin=begin, end=end)


@mcp.tool()
def get_view_phantoms(name: str = "", key: str = "") -> dict:
    """Return phantom HTML and extracted text from a view by name.
    If key is omitted, defaults to the common 'pybackup' phantom key."""
    return _get("/view_phantoms", name=name, key=key)


@mcp.tool()
def send_to_view(text: str, name: str = "", index: int = -1) -> dict:
    """Send a string to any open tab by name (partial match, case-insensitive).
    For Terminus tabs this types the text into the terminal as if the user typed it.
    Include a trailing newline (\\n) to execute a command.
    Use index (0-based, from get_open_files) to target a tab by position instead of name.
    Omit both name and index to target the active view."""
    return _post("/send_to_view", text=text, name=name, index=index)


@mcp.tool()
def get_output_panel(name: str = "") -> dict:
    """Return the text content of an output panel.
    If name is omitted, read the active output panel.  Use name='exec' for build output.
    """
    return _get("/output_panel", name=name)


@mcp.tool()
def get_symbols() -> dict:
    """Return all symbols (functions, classes, etc.) in the active file with line numbers."""
    return _get("/symbols")


@mcp.tool()
def lookup_symbol(symbol: str) -> dict:
    """Find where a symbol is defined across all open files."""
    return _get("/lookup_symbol", symbol=symbol)


@mcp.tool()
def get_project_data() -> dict:
    """Return the raw .sublime-project JSON data for the current project."""
    return _get("/project_data")


@mcp.tool()
def add_folder(path: str) -> dict:
    """Add a folder to the current project."""
    data = _get("/project_data").get("project_data") or {}
    folders = data.get("folders", [])
    if not any(f.get("path") == path for f in folders):
        folders.append({"path": path})
        data["folders"] = folders
        return _post("/set_project_data", data=data)
    return {"ok": True, "note": "already present"}


@mcp.tool()
def remove_folder(path: str) -> dict:
    """Remove a folder from the current project by path."""
    data = _get("/project_data").get("project_data") or {}
    folders = data.get("folders", [])
    new_folders = [f for f in folders if f.get("path") != path]
    if len(new_folders) == len(folders):
        return {"ok": False, "note": "folder not found"}
    data["folders"] = new_folders
    return _post("/set_project_data", data=data)


@mcp.tool()
def get_variables() -> dict:
    """Return Sublime Text's build variables: $file, $project_path, $platform, etc."""
    return _get("/variables")


# ── navigate ──────────────────────────────────────────────────────────────────


@mcp.tool()
def open_file(path: str, line: int = 0, col: int = 0) -> dict:
    """Open a file in Sublime Text, optionally jumping to a specific line and column."""
    return _post("/open_file", path=path, line=line, col=col)


@mcp.tool()
def goto_line(line: int, col: int = 1) -> dict:
    """Move the cursor to a line (and optional column) in the active file."""
    return _post("/goto_line", line=line, col=col)


@mcp.tool()
def show_panel(name: str = "exec") -> dict:
    """Bring an output panel to the front.  Use name='exec' for the build panel."""
    return _post("/show_panel", name=name)


# ── edit ──────────────────────────────────────────────────────────────────────


@mcp.tool()
def replace_selection(text: str) -> dict:
    """Replace the current selection(s) with text."""
    return _post("/replace_selection", text=text)


@mcp.tool()
def replace_lines(
    begin: int, end: int, text: str, path: str = "", index: int = -1
) -> dict:
    """Replace lines begin through end (inclusive, 1-based) in the active file with text.
    Pass path to target a specific open file regardless of which tab is focused.
    Use index (0-based, from get_open_files) to target a nameless tab by position."""
    return _post(
        "/replace_lines", begin=begin, end=end, text=text, path=path, index=index
    )


@mcp.tool()
def run_command(
    command: str, args: Optional[dict] = None, scope: str = "window"
) -> dict:
    """Run any Sublime Text command.  scope='window' (default) or 'view'."""
    return _post("/run_command", command=command, args=args or {}, scope=scope)


# ── build ─────────────────────────────────────────────────────────────────────


@mcp.tool()
def run_build(
    cmd: Optional[list] = None, shell_cmd: Optional[str] = None, working_dir: str = ""
) -> dict:
    """Trigger the current build system, or pass cmd/shell_cmd to run a specific command."""
    body = {}
    if cmd:
        body["cmd"] = cmd
    if shell_cmd:
        body["shell_cmd"] = shell_cmd
    if working_dir:
        body["working_dir"] = working_dir
    return _post("/run_build", **body)


# ── misc ──────────────────────────────────────────────────────────────────────


@mcp.tool()
def set_status(value: str, key: str = "sublime_mcp") -> dict:
    """Write a message to Sublime Text's status bar."""
    return _post("/set_status", key=key, value=value)


# ── file ops ──────────────────────────────────────────────────────────────────


@mcp.tool()
def save_file(path: str = "") -> dict:
    """Save a file. Pass path to save a specific open file; omit path to save the active file."""
    return _post("/save_file", path=path) if path else _post("/save_file")


@mcp.tool()
def save_all() -> dict:
    """Save all open files."""
    return _post("/save_all")


@mcp.tool()
def close_file(path: str = "") -> dict:
    """Close a file by path, or close the active file if path is omitted."""
    return _post("/close_file", path=path)


@mcp.tool()
def revert_file() -> dict:
    """Revert the active file to its last saved state, discarding unsaved changes."""
    return _post("/revert_file")


# ── edit ops ──────────────────────────────────────────────────────────────────


@mcp.tool()
def undo() -> dict:
    """Undo the last edit in the active file."""
    return _post("/undo")


@mcp.tool()
def redo() -> dict:
    """Redo the last undone edit in the active file."""
    return _post("/redo")


@mcp.tool()
def duplicate_line() -> dict:
    """Duplicate the current line(s) in the active file."""
    return _post("/duplicate_line")


@mcp.tool()
def toggle_comment(block: bool = False) -> dict:
    """Toggle line comment (or block comment if block=True) on the current selection."""
    return _post("/toggle_comment", block=block)


@mcp.tool()
def sort_lines(case_sensitive: bool = False) -> dict:
    """Sort the selected lines (or all lines if nothing is selected)."""
    return _post("/sort_lines", case_sensitive=case_sensitive)


@mcp.tool()
def select_lines(begin: int, end: int = 0) -> dict:
    """Select lines begin through end (1-based, inclusive).  end defaults to begin."""
    return _post("/select_lines", begin=begin, end=end or begin)


@mcp.tool()
def fold_lines(begin: int, end: int) -> dict:
    """Fold (collapse) lines begin through end (1-based) in the active file."""
    return _post("/fold_lines", begin=begin, end=end)


@mcp.tool()
def insert_snippet(contents: str) -> dict:
    """Insert a snippet at the cursor using Sublime Text's snippet syntax (e.g. $1 for tab stops)."""
    return _post("/insert_snippet", contents=contents)


# ── search ────────────────────────────────────────────────────────────────────


@mcp.tool()
def find_in_file(
    pattern: str, case_sensitive: bool = False, regex: bool = False
) -> dict:
    """Find all occurrences of pattern in the active file.  Returns list of {line, col, text}."""
    return _post(
        "/find_in_file", pattern=pattern, case_sensitive=case_sensitive, regex=regex
    )


@mcp.tool()
def find_in_files(
    pattern: str,
    folders: Optional[list] = None,
    case_sensitive: bool = False,
    regex: bool = False,
    max_results: int = 200,
) -> dict:
    """Search for pattern across project folders (or the supplied folder list).
    Skips .git, __pycache__, node_modules, .venv.  Returns list of {path, line, match}.
    """
    body = dict(
        pattern=pattern,
        case_sensitive=case_sensitive,
        regex=regex,
        max_results=max_results,
    )
    if folders:
        body["folders"] = folders
    return _post("/find_in_files", **body)


# ── syntax / encoding ─────────────────────────────────────────────────────────


@mcp.tool()
def get_syntaxes() -> dict:
    """List all syntax definitions available in Sublime Text (name + path)."""
    return _get("/syntaxes")


@mcp.tool()
def get_command_palette(
    package: str = "", command: str = "", caption: str = ""
) -> dict:
    """List Command Palette entries from installed *.sublime-commands resources.
    Optional filters: package, command id, or caption substring."""
    return _get("/command_palette", package=package, command=command, caption=caption)


@mcp.tool()
def get_commands(
    package: str = "", command: str = "", include_palette: bool = True
) -> dict:
    """List runnable Sublime command ids from loaded command classes, optionally enriched
    with matching Command Palette entries from installed packages."""
    return _get(
        "/commands",
        package=package,
        command=command,
        include_palette=str(include_palette).lower(),
    )


@mcp.tool()
def get_menu_items(menu: str = "", caption: str = "", command: str = "") -> dict:
    """List installed menu items from *.sublime-menu resources.
    Optional filters: menu filename, caption substring, or command id substring."""
    return _get("/menu_items", menu=menu, caption=caption, command=command)


@mcp.tool()
def get_active_panel() -> dict:
    """Return the active panel id and, if it is an output panel, its content."""
    return _get("/active_panel")


@mcp.tool()
def set_syntax(name: str) -> dict:
    """Set the syntax of the active file by name (case-insensitive partial match is fine)."""
    return _post("/set_syntax", name=name)


@mcp.tool()
def get_encoding() -> dict:
    """Return the character encoding of the active file."""
    return _get("/encoding")


@mcp.tool()
def set_encoding(encoding: str) -> dict:
    """Set the character encoding of the active file (e.g. 'UTF-8', 'Western (Windows 1252)')."""
    return _post("/set_encoding", encoding=encoding)


# ── cursor / scope ────────────────────────────────────────────────────────────


@mcp.tool()
def get_scope_at_cursor() -> dict:
    """Return the full syntax scope string at the cursor position."""
    return _get("/scope_at_cursor")


@mcp.tool()
def get_word_at_cursor() -> dict:
    """Return the word under the cursor and its line/col."""
    return _get("/word_at_cursor")


@mcp.tool()
def get_bookmarks() -> dict:
    """Return all bookmarked positions in the active file."""
    return _get("/bookmarks")


@mcp.tool()
def get_line_count() -> dict:
    """Return the total number of lines in the active file."""
    return _get("/line_count")


# ── settings ──────────────────────────────────────────────────────────────────


@mcp.tool()
def get_setting(key: str, scope: str = "view") -> dict:
    """Get a Sublime Text setting by key.  scope='view' (default) or 'window'."""
    return _post("/get_setting", key=key, scope=scope)


@mcp.tool()
def set_setting(key: str, value: object, scope: str = "view") -> dict:
    """Set a Sublime Text setting by key.  scope='view' (default) or 'window'."""
    return _post("/set_setting", key=key, value=value, scope=scope)


# ── window / layout ───────────────────────────────────────────────────────────


@mcp.tool()
def toggle_sidebar() -> dict:
    """Show or hide the Sublime Text sidebar."""
    return _post("/toggle_sidebar")


@mcp.tool()
def get_layout() -> dict:
    """Return the current window layout (groups, cells) and which files are in each group."""
    return _get("/layout")


@mcp.tool()
def focus_group(group: int) -> dict:
    """Move focus to a pane group by 0-based index."""
    return _post("/focus_group", group=group)


@mcp.tool()
def set_layout(layout: dict) -> dict:
    """Set the window pane layout.  layout must be a ST layout dict with cols, rows, cells keys."""
    return _post("/set_layout", layout=layout)


# ── scripting ─────────────────────────────────────────────────────────────────


@mcp.tool(name="str_replace_based_edit_tool")
def edit_file(
    command: str,
    path: str = "",
    old_str: Optional[str] = None,
    new_str: Optional[str] = None,
    insert_line: Optional[int] = None,
    insert_text: Optional[str] = None,
    file_text: Optional[str] = None,
    view_range: Optional[list] = None,
) -> dict:
    """ST-native file editor implementing the standard str_replace_based_edit_tool interface.
    Edits appear live in Sublime Text with full undo (Ctrl+Z), gutter diff markers,
    and 30-second highlight annotations showing what changed.

    command='str_replace': replace old_str with new_str in path.
      old_str must match exactly once (whitespace-sensitive).
      Returns error if 0 or 2+ matches, listing ambiguous line numbers.

    command='insert': insert insert_text after line insert_line (1-based).
      insert_line=0 inserts at the very start of the file.

    command='create': create a new file at path with file_text content.
      Syntax is auto-detected from the file extension. Errors if path exists.

    command='view': return file content with 1-based line numbers prepended.
      Optional view_range=[start, end] to read a slice (end=-1 for EOF).

    All commands auto-open the file in ST if not already open."""
    body: dict = {"command": command, "path": path}
    if old_str is not None:
        body["old_str"] = old_str
    if new_str is not None:
        body["new_str"] = new_str
    if insert_line is not None:
        body["insert_line"] = insert_line
    if insert_text is not None:
        body["insert_text"] = insert_text
    if file_text is not None:
        body["file_text"] = file_text
    if view_range is not None:
        body["view_range"] = view_range
    return _post("/edit_file", **body)


@mcp.tool()
def eval_python(code: str) -> dict:
    """Execute arbitrary Python in Sublime Text's main thread.
    Locals: sublime, window, view, print.  Returns captured stdout in 'output'."""
    return _post("/eval_python", code=code)


@mcp.tool()
def get_console_log(tail: int = 100) -> dict:
    """Return recent Sublime Text console output (plugin log messages and stdout).
    tail=N limits to the last N entries. tail=0 returns all captured entries."""
    return _get("/console_log", tail=tail)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
