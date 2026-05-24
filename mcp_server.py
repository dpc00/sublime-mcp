"""sublime-mcp — MCP server.

Wraps the HTTP API exposed by sublime_mcp.py (the ST plugin) and
presents it as MCP tools to Claude Code (or any MCP client).

Requirements: pip install mcp httpx
Run:          python mcp_server.py
Register:     add to ~/.claude/settings.json mcpServers
"""
import httpx
from mcp.server.fastmcp import FastMCP

BASE    = "http://127.0.0.1:9500"
TIMEOUT = 10.0

mcp = FastMCP(
    "sublime-mcp",
    description="Read and control Sublime Text from an MCP client.",
)


def _get(path: str, **params) -> dict:
    r = httpx.get(f"{BASE}{path}", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _post(path: str, **body) -> dict:
    r = httpx.post(f"{BASE}{path}", json=body, timeout=TIMEOUT)
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
def get_project_folders() -> dict:
    """Return the project's root folder paths."""
    return _get("/project_folders")


@mcp.tool()
def get_file_content(path: str) -> dict:
    """Return the full content of an already-open file by its path."""
    return _get("/file_content", path=path)


@mcp.tool()
def get_output_panel(name: str = "exec") -> dict:
    """Return the text content of an output panel.  Use name='exec' for build output."""
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
def replace_lines(begin: int, end: int, text: str) -> dict:
    """Replace lines begin through end (inclusive, 1-based) in the active file with text."""
    return _post("/replace_lines", begin=begin, end=end, text=text)


@mcp.tool()
def run_command(command: str, args: dict = None, scope: str = "window") -> dict:
    """Run any Sublime Text command.  scope='window' (default) or 'view'."""
    return _post("/run_command", command=command, args=args or {}, scope=scope)


# ── build ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def run_build(cmd: list = None, shell_cmd: str = None, working_dir: str = "") -> dict:
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


if __name__ == "__main__":
    mcp.run()
