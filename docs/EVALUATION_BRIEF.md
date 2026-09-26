# sublime-mcp: brief for an outside evaluator

Written 2026-09-26. Everything below is a record of what was done and seen; it
contains no recommendations. The author of the code is an AI (Claude) working
for the repository owner, who asked for an independent expert to evaluate it.

## What it is

`sublime-mcp` (Sublime Text package name "MCP Commander") is a Sublime Text 4
plugin that runs an HTTP bridge (ports 9500/9501) and an MCP endpoint
(SSE/streamable, ports 9502/9503) inside Sublime's plugin host, plus two
optional proxies (`packages/node-proxy` on npm, `packages/python-proxy` on
PyPI). Current version 1.10.0. Source: `sublime_mcp.py` (single large module),
`lib/native_windows.py`.

The catalog is 401 tools: 7 advertised by default, the rest reachable through
`discover_tools` and `batch`. 160 are generated wrappers named exactly after
Sublime Text commands (from a snapshot of CommandsBrowser's command list,
`tools/st_commands_metadata.json`, MIT, source noted in the file); 241 are
hand-written. `eval_python`, `exec`, `run_command`, file edit/delete and
similar tools are in the catalog; `disabled_tools` in the settings file
refuses tools by name (empty by default).

Tools that run on Sublime's main thread wait at most 5 s. Since 1.10.0,
`list_native_windows` and `dismiss_native_window` (Windows only, Win32 via
ctypes) work without the main thread so a native dialog that blocks it can be
listed and dismissed.

## What was checked, and how

All runs used a bare, disposable Sublime Text 4215 (only MCP Commander
installed, ports 9520/9522), not the owner's working install.

| Check | Method | Evidence in repo |
|---|---|---|
| Each of the 160 generated command tools | run once with no arguments, and (59 that take arguments) once with sandbox arguments; before/after diff of files, settings, clipboard, processes, native windows, screenshot | `tools/st_commands_behavior.json`, harness `tools/probe_st_commands.py` |
| Hand-written tools | 195 routed tools run the same way (`--hand-written`) | `tools/st_hand_written_behavior.json` |
| 44 remaining tools | called through the MCP endpoint `tools/call` (`--other-tools`) | `tools/st_other_tools_behavior.json` |
| Native dialog dismissal | for each of the 16 commands seen to block the main thread: run it, confirm Sublime stops answering, list and dismiss the dialog with the two tools, confirm Sublime answers again | `tools/st_dialog_dismissal_results.json` (16/16), `tools/verify_native_dialogs.py` |
| Window helper | unit tests that open real Windows message boxes in child processes | `test/test_native_windows.py` |
| Proxy catalogs | fallback catalogs regenerated from `_MCP_TOOLS` | `tools/generate_fallback_catalog.py`, `test/*.test.js` |
| Releases | GitHub release, PyPI and npm publishes for 1.9.0, 1.9.1, 1.10.0 (npm published by the owner) | `CHANGELOG.md`, registry pages |

Observed results, from the JSON files: 16 commands block the main thread behind a native window; 3
(`exit`, `hot_exit`, `close_window`) quit Sublime; 7 open a non-blocking window; 6 leave an in-app panel,
popup or overlay; `purchase_license` and `upgrade_license` start the web browser; some write settings,
files or the clipboard; 116 of the 160 showed no effect. The 44 tools outside the route table all
returned a reply; 43 showed no effect and for `get_output_panel` the harness recorded a Windows
system process (`backgroundTaskHost.exe`) starting during the call.

## What was not checked

- Non-Windows behaviour (macOS/Linux ports 9501/9503 were not exercised in this work); the native window
  tools are Windows only.
- "No observable effect" is the harness's finding, not proof of a no-op: many commands need a selection,
  open panel, project or specific arguments that the synthesised arguments did not supply.
- Arguments were synthesised from the schema or from the command metadata; real-world argument shapes were not
  exhaustively tried.
- The command names and argument descriptions come from CommandsBrowser's snapshot; they were not
  independently derived from Sublime Text. Whether the snapshot lists every command Sublime Text has was not
  verified.
- Selection with real keyboard/mouse was used for only a few dialogs; most dismissal was via Win32 messages.
- Concurrency, authentication and network exposure of the HTTP/MCP servers were not reviewed in this work.
  (The servers listen on 127.0.0.1; whether anything else can reach them was not tested.)
- No independent code review of `sublime_mcp.py` has been done.

## Mistakes made during this work

- A GitHub comment containing `/review` was mangled by Git Bash path conversion (`C:/Program Files/Git/review`) and had to be edited.
- Reported that an npm publish "did not go through" after checking about a minute after publishing; registry
  lag was the cause and the publish had succeeded.
- Told the owner a tab could not be seen without first trying to read it; it could be read.
- `upgrade_license` was run by the probe and opened a web browser on the owner's desktop.
- The probe's OpenWith "Pick an app" dialog was left open on the desktop (flashing taskbar icon) until closed by hand; the harness was then changed to close it.
- Early keyword-based lists of "dialog-opening" commands and of "dangerous" commands were wrong (10 found vs
  16 observed blockers) and were replaced by observed data. The docs briefly contained warnings and
  judgement wording; the owner objected and they were removed. There is no skip list or disallow list.
- The first `list_native_windows` returned nothing because the plugin runs in a child host process; the
  window owner is the parent, which the code now resolves.
- After a hot reload of the plugin the old `lib/native_windows` module stayed loaded until Sublime was
  restarted. Reloading `lib` modules is not implemented.
- A first full probe pass was invalid (53 `FileExistsError`s from an unclean sandbox) and was rerun.
- More than one Sublime process was left running at one point; cleaned up by exact executable path.
- The probe counted Sublime's autosave session temp file as an effect of `get_package_mcp_info`; that was
  noise and the filter was corrected in commit 4f21d3e.

## How to reproduce

1. Copy a Sublime Text 4215 portable install to a scratch folder, install the plugin into its `Packages`,
   set `http_port`/`mcp_port` (for example 9520/9522), start it.
2. `python tools/probe_st_commands.py` (also `--with-args`, `--hand-written`, `--other-tools --mcp-port 9522`;
   `--only NAME` for one tool, `--out FILE`).
3. `python tools/verify_native_dialogs.py` for the 16-dialog dismissal test.
4. `python -m unittest discover -s test -p "test_*.py"` (run from the repo root; do not use `python -m unittest test.x`, the standard library `test` package shadows it).
5. `python tools/generate_st_command_tools.py` then `python tools/generate_fallback_catalog.py` regenerate the
   generated tool blocks and proxy catalogs; both are idempotent.

## Where to look first

`sublime_mcp.py`: `_POST` / `_GET` route tables, `_MCP_TOOLS`, `_on_main`, the two `native_windows` handlers.
`lib/native_windows.py`: all Win32 calls. `AGENT_GUIDE.md`: what agents are told.
