# sublime-mcp — Claude Code notes

## Project structure

- `mcp_server.py` — MCP server. Published to PyPI as `sublime-mcp`. This is the only file in the PyPI package.
- `sublime_mcp.py` — ST plugin. NOT in the PyPI package. Distributed via Package Control.
- `sublime_mcp_browse.py` — ST browse commands. Also distributed via Package Control.
- `pyproject.toml` — single source of version truth.

## Publishing

1. Bump `version` in `pyproject.toml`
2. `python -m build`
3. `twine upload dist/sublime_mcp-<ver>*`
4. Commit dist files + pyproject.toml + egg-info

Only `mcp_server.py` ships in the PyPI dist (`[tool.setuptools] py-modules = ["mcp_server"]`).
`sublime_mcp.py` and `sublime_mcp_browse.py` are distributed via Package Control (PR #9447).
`.gitattributes` marks dev/build files as `export-ignore` so Package Control only installs the plugin files.

## ST MCP tool usage

- `str_replace_based_edit_tool create` opens in ST's buffer but does NOT flush to disk until `save_file` is called.
- Call `save_file` when the file needs to be on disk (git, linter, pyright). For casual editing, save when done.
- When creating a new file with no path specified, default to the project directory.

## Ports

- Windows ST listens on `9500` (default `_PORT` in `sublime_mcp.py`)

## Tab indexing

`get_sheets()` returns 0-based indexes; users refer to tabs 1-based. Always
call `get_sheets()` first when targeting a specific tab by number.
