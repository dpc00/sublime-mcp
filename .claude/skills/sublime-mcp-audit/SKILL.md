---
name: sublime-mcp-audit
description: How to run the Sublime package audit so it exposes sublime-mcp weaknesses. Use whenever installing, testing or removing Sublime packages through the portable Sublime instances: no scripts, no eval_python, no HTTP bridge, install like a user, which sublime-mcp tools to use for each step, and what counts as a finding.
---

# sublime-mcp package audit

Public, general version of this method for other people: https://github.com/dpc00/sublime-package-audit (`.claude/skills/sublime-package-audit/SKILL.md` and `PROCEDURE.md`). This file is the private working copy with Donald's local rules and paths; when a lesson is general, put it in the public skill too.

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

## What was already tested: use the small file, not the log

`.tested_packages.tsv` (repo root, about 25 KB) lists every tested or skipped package: name, date, the line of its entry in the log, and a note (packages recovered from the queue order, for example "queue v1 #12 (done through #707)", or skip reasons). It was rebuilt on 2026-10-07 from the log headings plus queue v1 positions 1-707 and queue v2 positions 1-181; v2 positions after 181 and later-phase packages that have no log entry may still be missing. Search it (for example Grep for the package name) to decide whether a package is done. When you finish or skip a package, append one row with the same columns and a short note for skips.

`.package_skill_test_log.md` (over 1 MB, backed up to Google Drive) is Donald's record of how the audit is done. Keep adding entries to it, but do not read it whole and do not use it to look up what was tested; read only the lines you need, using the line number from the tsv.

### Check "already tested" before EVERY package (Donald, 2026-10-11: "you missed some")

Do all four, not just the tsv name column:
1. `.tested_packages.tsv`: search the name anywhere in the row, with word boundaries (names carry version suffixes like `name 1.2.5` and queue prefixes like `#681 name`).
2. `.package_skill_test_log.md`: search the WHOLE text, not only `##` headings. Old entries are also dated lines without a heading (`2026-10-03 SublimeLinter-contrib-codespell (kaste): tested ...`) and grouped headings (`## LSP-some-sass, LSP-pyproject, LSP-taplo`).
3. Transcripts in `C:\Users\donal\.claude\projects\C--Users-donal-projects-sublime-mcp\*.jsonl`: search `Installed package` plus the name (the Grep tool does 730 MB in seconds).
4. Judge each hit by eye: a substring hit is not a match (Bicep syntax vs LSP-Bicep, "Mar" inside "Make Bookmarklet", `Lean` vs `LSP-lean` are different packages).
When a miss is found, add a retroactive row to the tsv at once.

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
- Console: use `get_console(mode="visible", tail=N, force_focus=true)` for a complete read, on every call (tested 2026-10-11 on 4200 and 4215: no crash, `complete: true`; the window does not stay in front, and a title-bar click does not raise it). Without `force_focus` visible mode fails at once; `auto` and `get_output_panel` (which now also takes `force_focus`; tested, gives a complete read with it) fall back to captured text (`complete: false`, with a `warning`). `captured`/`get_console_log` miss startup output. Do not open the console panel and read the screen. Details: `skills/sublime-mcp/SKILL.md`.
- `delete_file` / `delete_folder` raise a Windows "permanently delete" confirmation per item on this drive and can stall; confirm each in computer-use.
- Learned 2026-10-11 (AI package audit, portable 4200):
  - After `show_overlay` (or any `run_command` that changes the UI) the next computer-use key press can come back "interrupted: user input detected" for every key until you call `get_window_state` once; do that, then type. A freshly started portable answers "no_viable_candidate" to keys until its title bar is clicked.
  - Order that works for the Install picker: `run_command show_overlay` -> `get_window_state` (image) -> `Return` -> wait about 6 s for the list -> **`get_window_state` (image) and confirm the package list is on screen (not still the palette text "Package Control: Install Package")** -> one key press per letter of the name -> `get_window_state` (image) to see the match -> `Return`. Donald's rule (2026-10-11): never send the name letter by letter until a screenshot shows the Enter took effect. A press_key result of `no_viable_candidate` or `interrupted` means the keys did NOT land: click the title bar (element index of AXTitleBar), call `get_window_state`, and retry the Return first.
  - The Remove picker highlights its first row, which is often MCP Commander or Package Control: type the package's name first and check the screenshot shows the single right entry before `Return`.
  - Dialogs: read them with `list_native_windows`; if `messages` is empty (a task dialog with custom button text) read the text with computer-use. A click by `element_index` on those buttons did nothing; click the pixel position from a `capture_mode="image"` snapshot. A message box may need a second or two to close after the click, so list again before clicking twice.
  - Use `run_command` with `settle_ms=300` when a command may show a dialog; it returns the new dialog in `dialogs`.
  - A package linked in as a junction does not get its `dependencies.json` libraries: run `run_command satisfy_libraries`, then restart the portable before testing. Libraries installed that way are not removed with the package; list them as leftovers.
  - Close a pathless tab with `close_file(name=...)`; `run_command close` with scope view does nothing.
  - After a portable restart its MCP server may reconnect by itself: test with a call before asking for `/mcp`.
  - Settings files written from outside Sublime are picked up late (about one command later). Run something harmless first, or check the console for "reloading settings Packages/User/...".

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

## Current practice, 2026-10-13 (supersedes older lines above where they differ)

Where the older text says computer-use is needed for pickers or that scripts are forbidden: since 2026-10-08 the sublime-mcp tools `get_quick_panel` / `pick_quick_panel` / `drive_input_panel` / `list_native_windows` / `dismiss_native_window` / `ui_press_key` exist and are used. Small helper scripts that only read data outside Sublime (zip contents, gh API calls, file hashes, simulating a user's file add) are fine and always written with the Write tool, never inline shell.

### Steps for one package on portable 4200 (`D:\st_portable_4200`)
1. Build the "untested" list with a CHECKED filter. Never trust a column guess: the 2026-10-13 filter read the tier column as the name and listed already-tested packages (ACP was retested by mistake). Look at the header, print a few rows, and test the filter on a package known to be done. Then check each candidate with the four-point check above (tsv by name AND by repo owner/name, log text, transcripts).
2. Back up `Data\Packages\User\Preferences.sublime-settings` and `Package Control.sublime-settings` to the scratchpad (`Preferences.backup`, `PC4200.backup`). Add one line to `C:\Users\donal\data\test_installs_to_remove_2026_10_11.txt` BEFORE installing.
3. Launch: `Start-Process 'D:\st_portable_4200\sublime_text.exe'`, wait for port 9522. Then reconnect through the MAIN Sublime: `run_command ai_terminal_send_string` with scope view, name "Claude", string `/mcp reconnect sublime-mcp-portable-4200\r`; wait about 12 s; `ToolSearch select:mcp__sublime-mcp-portable-4200__batch`. If computer-use was stopped by Escape: `/mcp reconnect computer-use-mcp` the same way, immediately; do not drop it.
4. Install via palette: `show_overlay` command_palette text "Package Control: Install Package", `ui_press_key Return`, then `pick_quick_panel text=<name> wait_ms 30000`. If the palette picks a different command (Remove Package once opened "Remove Channel"), quit and delete the package the fallback way instead of retrying.
5. Inspect the package source first (zip in `Data\Installed Packages`; read with `python -I -X utf8`); then run real commands; read the console and any plugin log panel; use the REAL external tool when the package needs one (install the free one in its own folder under `tools`, own package.json), never a stub.
6. Prove before filing: reproduce, find the cause in the source, try the fix on an unpacked copy in `Data\Packages\<name>` (restart first, a package folder added while Sublime runs may not load its Preferences), check existing issues, one short factual issue per finding, text starts "Claude reports:", say plainly whether a visible effect was seen.
7. Cleanup, in this order: close all tabs (set_scratch + close) so no Save dialog blocks; `exit` the portable; wait until no process remains; recycle the zip, the unpacked copy, user settings files the test created, the downloaded tools and clones with the `recycle-delete` skill (admin through `run-as-admin` when Windows asks for it); restore both settings from the backups and compare file hashes; append the log section, the `.tested_packages.tsv` row and the `test_installs_to_remove` line.

### Console reads and the clipboard (2026-10-13)
`get_console(mode="visible", ...)` reads the console through Donald's clipboard (sentinel, copy, read, restore); his clipboard syncs to his phone, so each visible read put console text on his phone. Default to `mode="captured"`. When a traceback or startup line is needed that captured misses (plugin load errors do show only in the visible read), tell him first and keep it to one read per package, with a small `tail`. A traceback can also be found by reading the package source and the library versions, or from a tee log if one exists.

### When in doubt, search GitHub issues first (2026-10-13)
Before judging odd behaviour as a package defect, a Sublime quirk or a sublime-mcp gap, search issues: the package's own repo, `sublimehq/sublime_text`, `sublimehq/package_control_channel`, `sublimelsp/LSP`, and for harness questions `anthropics/claude-code` (`gh search issues --repo <owner/repo> "<words>" --limit 8 --json number,title,state`). Cite what you used in the log entry (ERB Snippets: matthewrobertson/ERB-Sublime-Snippets#32 already reported the scope problem). Keep the output small.

### Findings that change how to judge
- A package's `Preferences.sublime-settings` added while Sublime runs is NOT merged until restart (sublimehq/sublime_text#7012, tested 2026-10-13; own `Foo.sublime-settings` files load at once). A theme or package that "ignores its defaults" right after install: restart before judging. Edits to a file Sublime already knew at startup are live.
- `eval_python` runs on the main thread: a `time.sleep` in it freezes the editor and trips the tool's 5 s timeout. Never sleep in it.
- ACP-style permission prompts are quick panels: read with `get_quick_panel`, answer with `pick_quick_panel` (index or text, pass the argument inside `args`).
- An input panel (prompt box) is filled and submitted with `drive_input_panel`.
- The user's global instructions (memory scans) make Claude-based agents start with file-read permission prompts; decline them, they are not part of the package.
- 2026-10-13 (LSP-R, FileTabRename, simpleifdef, LanguageTool): (a) when you remove a package zip by hand, restore `Package Control.sublime-settings` from the backup BEFORE the next launch, otherwise Package Control sees the package in `installed_packages` and downloads it again at startup, and the Install list no longer offers it. (b) PowerShell `Expand-Archive` refuses `.sublime-package`; unpack with python `zipfile`. (c) PowerShell variable names are case-insensitive: `$p` overwrote `$P` and a cleanup script half-ran; use distinct names. (d) Passing a single path to `recycle.ps1` through `@items` splats a string into characters: always `@(...)`-wrap the list. (e) A freshly installed LSP helper may not start until the window config is updated (sublimelsp/LSP#3074, only packages that register two plugins such as LSP-R); check `windows.lookup(w).get_config_manager().all` before judging a "server never starts". (f) The R language server skips diagnostics for files inside the Windows temp folder: never put R test files in the scratchpad. (g) `eval_python` selection changes (`sel().add`) do not fire `on_selection_modified` here; a real `move` command does. (h) Plugins on build 4200 need real build-4215 scope names sometimes (Simple Ifdef 0.4.0 does nothing on 4200): test on the 4215 portable and do not report it as a bug. (i) Look inside the package code for a PATH/config assumption first (LSP-R calls `R` from PATH: launch the portable with the tool's bin folder in PATH for that process only).
- pick_quick_panel index is the position in the FULL picker list (the indexes that get_quick_panel returns for a filtered list), not the position in the filtered result. Pick by 	ext (exact name) to be safe. 2026-10-13: index 0 after a filter installed an unrelated package.
