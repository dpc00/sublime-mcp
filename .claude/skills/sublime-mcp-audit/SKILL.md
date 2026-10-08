---
name: sublime-mcp-audit
description: How to run the Sublime package audit so it exposes sublime-mcp weaknesses. Use whenever installing, testing or removing Sublime packages through the portable Sublime instances: no scripts, no eval_python, no HTTP bridge, install like a user, which sublime-mcp tools to use for each step, and what counts as a finding.
---

# sublime-mcp package audit

Source: Donald's instructions of 2026-10-07 and the tool survey made the same day with `discover_tools`.

## Purpose

The audit is how we find weaknesses in sublime-mcp itself. Package bugs found along the way are a side result. Anything that hides a gap in the MCP defeats the audit.

## Hard rules

1. No scripts of any kind (Python, PowerShell, shell, one-liners that act as scripts).
2. No `eval_python`, for anything.
3. No HTTP calls to the MCP bridge ports (9510, 9520, 9532...). If a portable's MCP server drops or hangs, stop and report it; do not go around it.
4. Installing the way a user does is the GOAL, not always the reality. For the Package Control release, use the command palette: "Package Control: Install Package", type the name, Enter. The repo master (the latest code) cannot come from the picker, so it is copied in (see "Allowed" below). Test both, and say which one shows each result.
5. If sublime-mcp cannot do a step a user can, do NOT work around it. Record it as a sublime-mcp weakness and tell Donald.

Allowed, Donald confirmed: copying a package copy (for example repo master) into a Packages folder to test it; the sublime-mcp `run_command` tool, which mimics a user's menu clicks. Running a command from inside `eval_python` is not allowed.

## Which sublime-mcp tools to use

Call `get_help` first. The tool usage (packages, menus, command palette, input panels, native dialogs) is documented in sublime-mcp's own `AGENT_GUIDE.md` and `skills/sublime-mcp/SKILL.md`; do not duplicate it here. Note: `install_package` is not the user picker flow, so it does not replace rule 4.

## Known gap (to confirm)

No tool reads the items of an open quick panel (such as the Install Package picker) or picks one. That step is done with computer-use: type the package name, press Enter. Report it as a sublime-mcp gap.

## Dialogs and windows (computer-use)

- Click dialogs with computer-use (`get_window_state`, then `click` the button by element index), every time, even after a "stopped by Escape" error (a false stop; retry, and ask Donald to run `/mcp` if it persists).
- Keys and modifier chords fail on a window that has never been focused. Focus it first.
- Do not leave a test window always-on-top, and do not minimize it; put it back as it was.
- Never loop commands that raise modal dialogs: run one, check with `list_native_windows`.

## Per-package procedure

1. Say "Testing: <package>".
2. Install through the palette picker. Wait until the package is indexed (a command from it shows up) before running anything; running commands too early produces false "Unable to find ..." dialogs.
3. Check dialogs (`list_native_windows`), the Package Control Messages tab and the console after every step.
4. Exercise the package's commands. Look at the window after each command.
5. Repeat with the repo master copy.
6. Clean up: reset any theme or setting that points at the package before removing it; close the tabs and panels you opened; recycle test files.
7. Log the result in the test log and file one short, plain issue per finding (check existing issues first).

## Driving the pickers (learned 2026-10-07)

- Focus: a never-focused portable window ignores keys. Click its title bar (element index of AXTitleBar) first, then single key presses work (letters, `minus`, `space`, `Down`, `Return`); `type_text` and chords do not.
- Install: `run_command show_overlay {overlay: command_palette, text: "Package Control: Install Package"}`, click title bar, `Return`, wait until the package list is on screen (it takes a moment), type the name key by key, check the screenshot shows the right single match, `Return`.
- Remove: use `run_command remove_package`, not the palette text (the palette ranks "Remove Channel" first). The list contains `LSP`, `MCP Commander` and `Package Control`: filter by typing the package's name and check the highlighted entry before `Return`. Never remove MCP Commander or Package Control. Wait for "successfully removed" in the status bar before reopening the list, because a list opened too soon is stale.
- LSP-* wrappers installed during a session start their server only after a Sublime restart (`run_command exit`, then start the portable with computer-use `start_app`; its MCP server reconnects by itself or after the user runs /mcp). Many also need a separate syntax package (see the wrapper's README) and download Node or a binary, so "(installing...)" can last minutes.
- The app name for the portable in computer-use changes between listings: always take it from `list_apps` and use the `process:D:\...\sublime_text.exe` entry, never your real Sublime.
- `get_console` visible mode often fails to get focus; opening the console panel with `run_command show_panel {panel: console}` and reading the screen works.
- `delete_file` / `delete_folder` raise a Windows "permanently delete" confirmation per item on this drive and can stall; confirm each in computer-use.

## Portable instance not connected (fixed procedure, 2026-10-07)

1. Start the instance with computer-use `start_app` (the .exe path), unless it is already up.
2. Ask Donald to run `/mcp` and reconnect that server. Then wait for his word; do nothing else.
3. Test with one call. Connected: continue the task through sublime-mcp tools only (`remove_package`, never shell recycling or another server's tools). Not connected: ask again, or read the console on screen.
Never substitute another route (PowerShell, a different portable's server, HTTP) while the server is down.

## Testing repo master after the release (learned 2026-10-07)

Remove the release with `remove_package`, copy master into Packages, then QUIT the portable (`run_command exit`) and start it again with `start_app`. Swapping a package in a running Sublime can fail with "No module named '<Package>.<module>'" when the Python host differs between the release (3.3) and master (3.8): it is an artifact, not a package bug. After the restart a Package Control "restart for libraries" dialog may appear: click OK. The sublime-mcp server usually reconnects by itself (`ToolSearch` waits for it); ask Donald for `/mcp` only if it does not. The first key press after a restart needs a title-bar click first.

## Where the package fails: build matters

Test Python plugins on 4200 first (reportable). A failure only on 4215 is build age: log it, do not file (Donald's rule). Read a package's whole traceback before deciding who is at fault; if only the last lines are visible, say so in the log.

## After one failure, diagnose; do not retry

Read the package's code path and check that the command it calls exists, before trying the same action again (the niceDarkTheme Install button calls the nonexistent `advanced_install_package`; Package Control 4.2.8 has `install_package` and `install_packages`).
