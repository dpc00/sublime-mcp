"""Claude Code ``/ide`` discovery and MCP contract helpers.

This module is independent of Sublime's Python runtime so discovery and wire
shapes can be regression-tested with ordinary Python.
"""

import json
import os
import tempfile


CLAUDE_IDE_TOOLS = (
    {
        "name": "getDiagnostics",
        "description": "Get IDE diagnostics, optionally for one file URI.",
        "inputSchema": {
            "type": "object",
            "properties": {"uri": {"type": "string"}},
        },
    },
    {
        "name": "openDiff",
        "description": "Open a native IDE diff and wait for its disposition.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "old_file_path": {"type": "string"},
                "new_file_path": {"type": "string"},
                "new_file_contents": {"type": "string"},
                "tab_name": {"type": "string"},
            },
            "required": [
                "old_file_path",
                "new_file_path",
                "new_file_contents",
                "tab_name",
            ],
        },
    },
    {
        "name": "close_tab",
        "description": "Close an IDE tab by its Claude-provided name.",
        "inputSchema": {
            "type": "object",
            "properties": {"tab_name": {"type": "string"}},
            "required": ["tab_name"],
        },
    },
)


def claude_discovery_directory(config_directory=None):
    root = config_directory or os.environ.get("CLAUDE_CONFIG_DIR")
    if not root:
        root = os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.join(root, "ide")


def create_claude_discovery_file(
    port,
    workspace_paths,
    auth_token,
    pid,
    directory=None,
    ide_name="Sublime Text",
):
    """Atomically publish Claude Code's ``<PORT>.lock`` discovery record."""
    target_dir = directory or claude_discovery_directory()
    os.makedirs(target_dir, exist_ok=True)
    for name in os.listdir(target_dir):
        if not name.endswith(".lock"):
            continue
        candidate = os.path.join(target_dir, name)
        try:
            with open(candidate, "r", encoding="utf-8") as stream:
                existing = json.load(stream)
            if int(existing.get("pid", -1)) == int(pid):
                os.remove(candidate)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
    target = os.path.join(target_dir, "{}.lock".format(int(port)))
    payload = {
        "workspaceFolders": [
            os.path.abspath(os.path.normpath(path))
            for path in workspace_paths
            if path
        ],
        "pid": int(pid),
        "ideName": ide_name,
        "transport": "sse",
        "runningInWindows": os.name == "nt",
        "authToken": auth_token,
    }
    fd, temporary = tempfile.mkstemp(prefix=".claude-ide-", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except Exception:
        try:
            os.remove(temporary)
        except FileNotFoundError:
            pass
        raise
    return target


def claude_dispatch(message, get_diagnostics, open_diff, close_tab):
    """Dispatch the Claude-specific IDE MCP surface."""
    method = message.get("method", "")
    message_id = message.get("id")
    params = message.get("params") or {}
    try:
        if method == "initialize":
            result = {
                "protocolVersion": params.get("protocolVersion") or "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "sublime-claude-ide", "version": "0.1.0"},
            }
        elif method in ("notifications/initialized", "notifications/cancelled"):
            return None
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": list(CLAUDE_IDE_TOOLS)}
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if name == "getDiagnostics":
                result = get_diagnostics(arguments)
            elif name == "openDiff":
                result = open_diff(arguments)
            elif name == "close_tab":
                result = close_tab(arguments)
            else:
                raise ValueError("Unknown tool: " + str(name))
        else:
            raise ValueError("Unknown method: " + method)
        if message_id is None:
            return None
        return {"jsonrpc": "2.0", "id": message_id, "result": result}
    except Exception as error:
        if message_id is None:
            return None
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "error": {"code": -32603, "message": str(error)},
        }
