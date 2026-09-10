# Changelog

## 1.7.6

Adds `drive_input_panel`: fills and submits/cancels Sublime's currently
open `show_input_panel`, e.g. a package's "Enter a path..." prompt.
Input-panel views aren't reachable through any documented API
(`window.views()`, `window.active_view()`, etc. all miss them), and
pressing Enter to submit is a native keybinding (`select`, gated by
`panel_has_focus`/`panel_type=="input"` in the default keymap) rather
than anything `view.run_command("insert", ...)` can trigger — a literal
inserted newline is silently accepted into the buffer without
submitting. `drive_input_panel` locates the panel's view directly and
drives it via Sublime's own built-in `select`/`hide_panel` commands,
which reach the panel's real `on_done`/`on_cancel` callback correctly
even when that callback belongs to a package running on the legacy
Python 3.3 plugin host (a separate OS process from the one `eval_python`
reaches) — no monkeypatching or OS-level keyboard injection required.

## 1.7.5

Removes dead `debugger-mcp`/`lsp-mcp` probing code from the Node proxy's
`doctor --all` path (`packages/node-proxy/bin/cli.js`) — those were
separate standing MCP servers removed in 1.7.0 when the repo flattened
to a single package; the CLI kept probing their old ports (9505/9506)
regardless. `doctor` now only checks sublime-mcp itself; the `--all`
flag is gone.

Also brings the README's install instructions up to date: Package
Control (search "MCP Commander") is now documented as the primary
install path, pending merge of the channel submission
([sublimehq/package_control_channel#9554](https://github.com/sublimehq/package_control_channel/pull/9554));
the manual clone+symlink steps are demoted to "for development." Removed
the stale Codex config example referencing the long-removed
`debugger-mcp`/`lsp-mcp` servers.

## 1.7.4

Fixes view-name matching (`run_command`'s `name` param and
`get_view_content`) silently failing for any normal saved file. The
lookup only checked `view.name()` (the tab-title override), which is
empty for a file-backed view that was never explicitly renamed — so
targeting a tab by its filename always missed, and the error's own
`open_views` diagnostic showed blank names instead of the real
filenames. Now falls back to the file's basename, matching what
`get_open_files` already did correctly.

## 1.7.3

Fixes a real regression introduced while responding to the Package Control
review bot: an attempted fix for its "don't import root-level plugin
module" finding removed the only import path that actually worked on
plugin reload, breaking the plugin entirely (`ModuleNotFoundError:
No module named 'search_results'`). The correct fix, per the bot's own
suggestion, is what's here now: `search_results.py`, `mcp_http_policy.py`,
`ide_companion.py`, `claude_ide.py`, and `acp_client.py` moved into a real
`lib/` subpackage, so they're no longer independently scanned as
root-level plugins and the relative import is unambiguous either way.

Also addresses the bot's other findings:
- Added a "Key Bindings" entry under Preferences > Package Settings >
  MCP Commander in `Main.sublime-menu` (the diff-review Escape/Ctrl+S/
  Ctrl+Shift+Enter bindings existed but had no menu entry to find them).
- `subprocess.Popen`/`subprocess.run` calls on Windows now pass
  `STARTUPINFO` with `SW_HIDE` to avoid a flashing console window.

## 1.7.2

Adds the `mcp-name: io.github.dpc00/sublime-mcp` marker required by the
MCP Registry to verify PyPI package ownership before publishing.

## 1.7.1

Adds `.gitattributes` (`export-ignore`) so a Package Control install ships
only the actual Sublime Text plugin, not the whole dev repo (tests, tools,
skills, proxy package sources, `.claude/`). Bumps the (previously stale)
MCP Registry manifest's version to match.

## 1.7.0

Removes debugger-mcp and lsp-mcp; the repo is now a single, flat Sublime Text
package instead of a multi-package nested layout.

- Removed `packages/debugger-mcp` and `packages/lsp-mcp`. Both were built on
  the assumption that controlling an installed package needs its own MCP
  server — `get_package_mcp_info` plus `eval_python`/`run_command` covers it
  directly, and their hard-won internals knowledge (async bridges, object
  graphs, real dispatch tables) is preserved as reusable skill files instead
  of frozen into standing servers. `skills/package-skill-generator` documents
  how to produce an equivalent skill for any other installed package.
- Flattened `packages/st-plugin/*` to the repo root, so the repo root is now
  directly the Package Control package — no more nested multi-package
  structure to translate at release time.
- Reframed `get_package_mcp_info`'s description around direct use (discover,
  read source, call directly) rather than only "write an MCP extension."
- Fixed the diff-review Accept/Reject banner rendering one line below its
  anchor (`add_phantom`/`LAYOUT_BLOCK` replaced with `add_regions`/annotations).
- Fixed IDE-companion listeners misattributing the agent's own tool-driven
  actions to the human user; added `diagnostics`/`main_thread_stack` tools
  (heartbeat, dispatch depth, listener event counts) for live introspection.
- Regenerated the Node/Python proxy fallback catalogs (238 tools).

## 1.6.0

Adds first-class support for Sublime Text's native tab multi-select and sheet
APIs.

- `get_sheets` now reports stable sheet IDs, group positions, selected state,
  focused state, and the active group.
- Adds dedicated tools for querying selected sheets, selecting or focusing
  sheets by ID/index, reordering sheets, and moving sheet collections between
  groups.
- Exposes Sublime's seven native directional tab-selection and focus commands.
- Correctly aggregates selected sheets across all editor groups while retaining
  optional per-group queries.
- Updates the Node and Python proxy catalogs, agent guides, catalog generator,
  and regression coverage for the expanded 236-tool surface.

## 1.5.1

Fixes an OS-level focus-stealing bug in the Windows `get_console`/`get_console_win`
backend introduced in 1.5.0.

- `get_console_win` now restores the OS foreground window that was active before
  the capture ran (previously it left keyboard focus on Sublime Text after every
  call, even when another application had focus beforehand).
- Cleanup on timeout is now idempotent: a slow capture chain and the timeout
  fallback can no longer race and restore UI state twice.

## 1.5.0

Reduces MCP context overhead while keeping the complete Sublime, debugger,
and LSP capability catalogs available on demand.

- Each server now advertises a focused seven-tool surface by default, with
  discovery and batch tools for advanced capabilities.
- Adds structured native project search, streamable HTTP support, health
  endpoints, a connection doctor, and installable Codex skills.
- Adds a unified `get_console` API. Prospective console capture is reload-safe
  and deduplicated, while the Windows full-history backend now restores the
  previous panel, editor focus, pointer position, and text clipboard.
- `get_output_panel(name="Console")` now routes through the working console
  backend instead of treating the built-in console as a normal output panel.
- Updates agent guides, generated proxy catalogs, and focused-surface tests.

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
