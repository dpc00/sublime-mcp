# sublime-mcp: Package Control Ready — Design Spec
Date: 2026-06-15

## Goal

Make sublime-mcp properly distributable via Package Control for all platforms,
with a clean install story for users: Package Control installs the ST plugin;
`pip install sublime-mcp` or `npx sublime-mcp` installs the MCP server.

## Architecture

Three shipping artifacts from one monorepo:

| Artifact | Channel | Files |
|---|---|---|
| ST plugin | Package Control | `sublime_mcp.py`, `sublime_mcp_browse.py`, `messages/` |
| Python MCP server | PyPI (`sublime-mcp`) | `mcp_server.py`, `pyproject.toml` |
| Node.js MCP server | npm (`sublime-mcp`) | `index.js`, `package.json` |

Package Control only sees the ST plugin files — `.gitattributes` `export-ignore`
entries fence off everything else.

## Changes

### 1. ST Plugin — cross-platform port

`sublime_mcp.py` currently hardcodes `_PORT = 9500` (Windows only).
Change to:

```python
import sys
_PORT = int(os.environ.get("SUBLIME_MCP_PORT", 9500 if sys.platform == "win32" else 9501))
```

This matches the MCP server's existing port logic and lets users override via env var.

### 2. ST Plugin — fix `get_console_full` for cross-platform

The current `_get_console_full` implementation uses `ctypes.windll` (Windows clipboard
API) — it does not work on Mac/Linux. Replace it with a platform-neutral version that
returns the entire `_console_buf` buffer (no tail limit), same data source as
`get_console_log`:

```python
def _get_console_full(params):
    _install_console_capture()
    return {"entries": list(_console_buf), "total": len(_console_buf)}
```

Also fix `eval_python_latest`: it calls `python` which on Mac/Linux may not be on PATH.
Use `sys.executable` instead so it always calls the same Python that ST is running:

```python
r = subprocess.run([sys.executable, fname], ...)
```

### 3. Python MCP Server — restore and update

- Restore `mcp_server.py` from git commit `d356c6f^` (554 lines, deleted June 11)
- Add two tools missing from the old version:
  - `get_console_full` — returns full ST console output (calls `/console_full`)
  - `eval_python_latest` — runs code via system Python (calls `/eval_python_latest`)
- Both tools call their corresponding HTTP endpoints already present in the ST plugin

### 4. .gitattributes — export-ignore additions

Add to the existing export-ignore list:

```
index.js                export-ignore
package.json            export-ignore
package-lock.json       export-ignore
node_modules/           export-ignore
mcp_server.py           export-ignore
docs/                   export-ignore
.ruff_cache/            export-ignore
__pycache__/            export-ignore
```

### 5. Repo cleanup — remove built artifacts from git

- `git rm -r --cached dist/` — stop tracking built wheels/tarballs; they belong on PyPI only
- `git rm -r --cached sublime_mcp.egg-info/` — generated file, should not be in git
- Add both to `.gitignore`

### 6. install.txt — rewrite

Clear two-part setup message:

```
sublime-mcp
===========

The ST plugin is now running. Complete setup in two steps:

STEP 1 — Install the MCP server (run once in your terminal)

  Python:  pip install sublime-mcp
  Node.js: npx sublime-mcp   (no install needed)

STEP 2 — Register with Claude Code

Add to ~/.claude/settings.json under "mcpServers":

  "sublime-mcp": { "command": "sublime-mcp" }          # Python
  "sublime-mcp": { "command": "npx", "args": ["sublime-mcp"] }  # Node.js

Restart Claude Code. Tools appear as mcp__sublime-mcp__*.

The plugin listens on 127.0.0.1:9500 (Windows) or 9501 (Mac/Linux).
Override with env var SUBLIME_MCP_PORT.

Full docs: https://github.com/dpc00/sublime-mcp
```

### 7. Package Control channel entry (PR #9447)

- Remove `"platforms"` restriction (omitting it means all platforms supported)
- Reply to reviewer summarising fixes, then request re-review

### 8. pyproject.toml — verify PyPI packaging

- Confirm `mcp_server.py` is the console script entry point (`sublime-mcp = mcp_server:main`)
- Confirm dependencies: `mcp`, `httpx`
- Bump version to match current (`1.2.5`)

## Out of scope

- Changing the package name (reviewer flagged 'sublime' but it's already published)
- Addressing command-prefix warning (cosmetic, low priority)
- Any new tools or features

## Success criteria

- `pip install sublime-mcp && sublime-mcp` starts the MCP server successfully on Windows, Mac, Linux
- `npx sublime-mcp` continues to work as before
- Package Control installs only `sublime_mcp.py` and `sublime_mcp_browse.py`
- PR #9447 reviewer concerns are all addressed
