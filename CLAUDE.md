# sublime-mcp — Claude Code notes

## Project structure

- `mcp_server.py` — MCP server. Published to PyPI as `sublime-mcp`. This is the only file in the PyPI package.
- `sublime_mcp.py` — ST plugin. NOT in the PyPI package. Users install manually by copying to ST's `Packages/User/` folder.
- `pyproject.toml` — single source of version truth.

## Publishing

1. Bump `version` in `pyproject.toml`
2. `python -m build`
3. `twine upload dist/sublime_mcp-<ver>*`
4. Commit dist files + pyproject.toml + egg-info

Only `mcp_server.py` ships in the PyPI dist (`[tool.setuptools] py-modules = ["mcp_server"]`).
`sublime_mcp.py` is repo-only.

## ST MCP tool usage

- `str_replace_based_edit_tool create` opens in ST's buffer but does NOT flush to disk until `save_file` is called.
- Call `save_file` when the file needs to be on disk (git, linter, pyright). For casual editing, save when done.
- When creating a new file with no path specified, default to the project directory.

## Ports

- Windows ST listens on `9500` (default `_PORT` in `sublime_mcp.py`)
- WSL ST listens on `9501` (change `_PORT = 9501` in the WSL copy of the plugin)
- MCP server auto-detects: Windows → 9500, Linux/WSL → 9501
- Override via `SUBLIME_MCP_BASE` env var

## Tab indexing

`get_sheets()` returns 0-based indexes; users refer to tabs 1-based. Always
call `get_sheets()` first when targeting a specific tab by number.
