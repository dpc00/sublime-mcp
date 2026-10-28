# sublime-mcp — Agent Context

MCP server that exposes a running Sublime Text 4 instance to AI agents.

## Critical assumption

Plugin edits in this repo are **not live** in Sublime Text until the files
are in ST's `Packages/` directory (this repo is usually a symlink target,
and as of 2026-09-08 is symlinked at the repo root, not a subfolder).
If something isn't working, check that the plugin loaded before debugging
the code.

## sublime-mcp itself

| MCP            | Plugin dir | MCP SSE                         | HTTP bridge                     | Tools                          |
| -------------- | ---------- | -------------------------------- | -------------------------------- | ------------------------------ |
| **sublime-mcp**  | repo root | 9502 (Win) / 9503 (macOS/Linux) | 9500 (Win) / 9501 (macOS/Linux) | 7 default, 406 discoverable    |

Ports are configured via `MCP Commander.sublime-settings` (`"mcp_port"` /
`"http_port"`), overridable in `Packages/User/`. The proxy → HTTP bridge URL
is the one remaining env var: `SUBLIME_MCP_BASE`.

Guide (also served by `get_help`): `AGENT_GUIDE.md` (repo root).

Since 1.9.0, 160 tools are generated wrappers for Sublime Text commands
(`tools/generate_st_command_tools.py`); since 1.10.0, `list_native_windows` and
`dismiss_native_window` (Windows) work while a native dialog blocks the main thread.

**Coordinates:** sublime-mcp tools are **1-based**.

## Connecting

### Option A — bundled proxy (sublime-mcp HTTP bridge)

```bash
cd packages/python-proxy && pip install . && sublime-mcp
# or
cd packages/node-proxy && npm install . && npx sublime-mcp
```

Defaults to `http://127.0.0.1:9500` on Windows, `:9501` on macOS/Linux. If
the proxy runs in WSL against Windows ST, set
`SUBLIME_MCP_BASE=http://127.0.0.1:9500` (or the Windows host IP).

### Option B — MCP streamable HTTP directly

```json
{
  "mcpServers": {
    "sublime-mcp":  { "type": "http", "url": "http://127.0.0.1:9502/mcp" }
  }
}
```

Use `:9503` on macOS/Linux. A client without streamable HTTP can use the
deprecated SSE form, `{ "type": "sse", "url": "http://127.0.0.1:9502/sse" }`.
HTTP bridge also serves `GET /mcp_tools`.

## Workflow

Orient → navigate → edit → verify.

| You want…                                      | Use               | Tool |
| ---------------------------------------------- | ----------------- | ---- |
| What the user is looking at                    | sublime-mcp       | `get_active_file` / `get_cursor_context` (live buffer, not disk) |
| Edit a file ST has open                        | sublime-mcp       | `str_replace_based_edit_tool` then `save_file` |
| Edit a file ST does not have open              | sublime-mcp       | `open_file` then edit the buffer |
| Run a build / test                             | **your shell**    | never ST `exec` / `run_build` |

### Default to sublime-mcp

Read, edit, save, close, find, navigate, and open paths (inside or outside
the workspace) through sublime-mcp. Fall back to host filesystem tools only
when ST or the HTTP/SSE bridge is down (frozen, crashed, plugin failed to
load, connection refused). Outside-workspace is not a fallback trigger —
`open_file` opens any path.

Why the live buffer, not a disk write:

- The user sees the edit, gutter diff, and a short highlight.
- Ctrl+Z undoes it. A silent disk overwrite has no ST undo.
- Dirty/save/close are real steps the user can see.
- No two-sources-of-truth with a stale ST buffer vs disk.

If you did write disk behind ST's back, `revert_file(name=...)` (it asks the person) or reopen so the
buffer resyncs.

### Never `run_command` as generic dispatch

Named typed tools put intent in the tool-call args. `run_command` is opaque
and often steals focus into an ST panel. If a capability is missing, that
is an MCP gap — not a reason to use `run_command`.

### Orient first

```
get_active_file()              # full buffer + 1-based cursor
get_cursor_context(lines=15)
get_selection()                # user's "look here"
```

### Edit discipline

1. `str_replace_based_edit_tool` for targeted edits (exact unique `old_str`).
2. `save_file(path=...)` — the edit tool does **not** persist.
3. Multi-line inserts: `replace_lines`, never `insert` (auto-indent piles up).
4. Dirty `close_file` hangs on ST's save prompt — save first or pass `discard=true`
   (asks the person). Always name the tab (`name` or `index`).

### Reading code

- `get_sheets` + `get_sheet_content` — any tab, including untitled / terminal tabs

## Verifying new tools

POSTing a route **runs** it on the user's ST. For UI-interactive commands,
registry-only checks (`TOOLS` / `_MCP_TOOLS` / `_POST`) are enough. Do not
live-invoke:

- sublime-mcp: `prompt_goto_line`, `quick_panel`, `select_color_scheme`,
  `select_theme`, `open_in_browser`, `html_print`, `customize_*`,
  `convert_*`, `edit_syntax_settings`

Silent buffer tools: prefer a scratch tab.

## Lessons

- Never `insert` large content — ST auto-indent mangles it. Use
  `str_replace_based_edit_tool` or `replace_lines`.
- `eval_python`: `print()`, not `return`. `sublime` / `window` / `view` in
  scope. Main-thread timeout 5s.
- Never ST `exec` for shell. Use the agent's own terminal.
- `batch` for 2+ independent sublime-mcp calls (max 50).
