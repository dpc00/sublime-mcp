# Changelog

## 1.4.6

Removes vestigial Package Control artifacts. This project isn't listed in
Package Control's default channel (an earlier attempt was abandoned in
favor of the current clone-and-symlink install method), so the
`.gitattributes` `export-ignore` rules (mostly pointing at paths from a
pre-`packages/` repo layout that no longer exist) and the
`messages.json`/`messages/*.txt` version-message system (which only
auto-displays when Package Control is tracking an install) were dead
weight. Their content is now this file plus the Installation section of
README.md.

No functional or tool changes.

## 1.4.5

Fixes the Preferences > Package Settings menu added in 1.4.4.

- The three plugins' `Main.sublime-menu` entries used a non-standard
  `open_file` x2 pattern (separate "Settings" / "Settings – User" items).
  Replaced with the standard `edit_settings` command, matching how every
  other Sublime Text package exposes its settings (a synced default/user
  split view opened from a single "Settings" menu item).
- Also added the "Preferences" (mnemonic n) and "Package Settings"
  (mnemonic P) caption/mnemonic pair on the parent menu nodes, matching
  Sublime's own Default package and third-party packages like TreeSitter,
  so the menu merges correctly instead of relying on another package
  having already defined those captions.

No functional or tool changes; ports and defaults are unchanged from 1.4.4.

## 1.4.4

Replaces the port-configuration env vars with real Sublime Text settings.

- sublime-mcp, debugger-mcp, and lsp-mcp each read their MCP SSE / HTTP
  bridge ports from a `<name>.sublime-settings` file (`"mcp_port"` /
  `"http_port"`) instead of env vars (`SUBLIME_MCP_MCP_PORT`,
  `SUBLIME_MCP_PORT`, `DEBUGGER_MCP_PORT`, `DEBUGGER_HTTP_PORT`,
  `LSP_MCP_PORT`, `LSP_HTTP_PORT` — all removed).
- Each plugin now has a Preferences > Package Settings menu entry so
  overriding a port is a normal ST settings edit, not a shell
  environment variable.
- sublime-mcp's old naming (`SUBLIME_MCP_MCP_PORT`/`SUBLIME_MCP_PORT`)
  was also inconsistent with debugger-mcp/lsp-mcp's
  `<NAME>_MCP_PORT`/`<NAME>_HTTP_PORT` convention; this removes the
  inconsistency along with the env vars.

`SUBLIME_MCP_BASE` (used by the bundled Node/Python proxies to find
sublime-mcp's HTTP bridge) is unaffected — that's a proxy-side override,
not a plugin port binding.

Default ports are unchanged: sublime-mcp 9502/9500 (Win), 9503/9501
(Mac/Linux); debugger-mcp 9505/9515; lsp-mcp 9506/9516.

## 1.4.3

Fixes the mcp 2.0 pin and a `get_sheet_content` bug.

- `mcp>=1.2,<2` is now `mcp>=1.2`. `mcp_server.py` binds `FastMCP`
  (mcp<2) or `MCPServer` (mcp>=2.0, which renamed it) at import time,
  so both major versions work without a dependency ceiling.
- `get_sheet_content` assumed the backend returned a dict with a
  `"content_base64"` key. It never did — that key only ever existed
  in the docstring. Image tabs now parse the actual response shape
  (a list of content blocks), and the image's MIME type is sniffed
  from its magic bytes instead of trusted from the file extension
  (which was wrong or absent for some files).

No tool or API changes otherwise.

## 1.4.2

Fixes a broken 1.4.1 install and version drift.

- `pip install sublime-mcp` resolved `mcp` to 2.0.0, which removed
  `mcp.server.fastmcp`. The server died at import with
  `ModuleNotFoundError`. The dependency is now pinned to `mcp>=1.2,<2`.
- The version reported over MCP had drifted across surfaces:
  package.json said 1.4.1, node-proxy advertised 1.4.0, and the
  Sublime plugin reported 1.3.1. All three now derive from one place,
  so they cannot disagree again.

No tool or API changes. 1.4.1's 220-tool catalog work is unchanged.

## 1.4.1

Fix: both the node and Python MCP proxies hand-maintained their own copy
of the tool catalog, and both had drifted from the 220 tools the backend
actually serves. The Python proxy was worst affected — it only exposed
72 of 220 tools, silently hiding 148 backend tools from any Python-side
agent.

Both proxies now generate their tool catalogs directly from the
backend's `_MCP_TOOLS`, so the proxy surface can no longer drift out of
sync with what the backend actually implements.

## 1.4.0

220 typed MCP tools are now documented (up from 63), covering view, tab,
pane, edit, selection, scroll, macro, file, project, marks, jumps, folds,
transform, and browser commands, plus read-only getters, `batch`, and
`eval_python`.

- New: `batch` tool — send multiple tool calls in one round trip (capped
  at 50 calls per request), available in both the Python and Node
  proxies.
- New: `get_help` added to debugger-mcp and lsp-mcp for in-session tool
  discovery.
- Fixes: threaded HTTP bridges (no more blocking under concurrent
  requests), keep-alive on bridge/SSE handlers, several MCP bridge
  routing and startup-race fixes.

## 1.3.0

The MCP server is now built directly into the ST plugin — no external
process (pip or npx) is required.

New: "MCP Commander: Server Status" in the Command Palette lets you stop
or restart the server without reloading the plugin.
