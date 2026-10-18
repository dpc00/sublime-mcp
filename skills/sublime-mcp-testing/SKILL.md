---
name: sublime-mcp-testing
description: The facts an agent needs before testing sublime-mcp, GhostShell or Sublime Text itself on this machine: what sublime-mcp is allowed to contain, which Sublime instances and ports exist, how the portable test builds are set up and kept clean, which tools open browsers, quit Sublime, change settings or block the main thread, how to sweep all tools safely, and how releases are done. Use before running any tool sweep, launching a portable, installing a package for a test, or releasing.
---

# Testing sublime-mcp: the truth

Written 2026-10-18 from a long session. Everything below was observed, not guessed; the date and
version are given where a fact could change. Read `skills/sublime-dialogs/SKILL.md` too: it says how to
handle dialogs and menus.

## 1. What sublime-mcp is

A plain pass-through to Sublime's commands: dumb on purpose, so it cannot interfere with the agent.
It must contain **no** debugging code, watchdogs, logs, hooks, auto-handling of dialogs, or changes to
what an ST command or Package Control action does. Anything that observes, diagnoses or reacts goes in
a skill (this folder) or in a separate plugin (HangWatch, `C:\Users\donal\projects\HangWatch`, linked
into Packages; records the UI thread's stack when it stalls 3 s, `hang-watch.log` in the Cache folder;
commands `HangWatch: Show Log` and `HangWatch: Status`). The owner has said this several times. Do not
"fix" a Sublime or package behaviour by adding code to the plugin.

Version 1.14.3 = the 1.13.8 code plus nothing (1.14.0 to 1.14.2 added a heartbeat fix and a freeze
watchdog and were reverted). 8 default tools, 403 advanced, 411 total.

## 2. The Sublime instances

| What | Where | HTTP bridge / MCP |
|---|---|---|
| Main Sublime (4215, Python 3.14) | `C:\Program Files\Sublime Text`, this agent's own editor | 9500 / 9502 |
| Portable 4215 (Python 3.14) | `D:\st_portable_4215` | 9510 / 9512 |
| Portable 4200 (Python 3.8 host) | `D:\st_portable_4200` | 9520 / 9522 |

- Never kill, restart or run risky tools against the main Sublime: this conversation runs in it.
- The bridge also answers `/health` and `/list_native_windows` while the main thread is blocked.
- A portable's `Data\Packages` holds only junctions to the repos (`GhostShell` ->
  `C:\Users\donal\projects\GhostShell`, `MCP Commander` -> `C:\Users\donal\projects\sublime-mcp`) plus
  `User`. Never put a copy there, never use `git archive`: GhostShell's `ai_terminal.sublime-color-scheme`
  (about 450 KB, thousands of rules, grows on purpose, gitignored, with a guard that refuses to shrink it)
  is not in git, so a copy starts with the small base scheme and the terminal colors vanish.
- Sublime shows its "Update" window even with `update_check` false (it steers unregistered users to the
  purchase page). Close it; never download an update into a portable, the old build is the point.
- Ask the owner before launching a portable. Close it when done, by the PID of the process whose path is
  under `D:\st_portable_*`, never by name (the main Sublime has the same exe name).
- A portable must be left with no tabs, no terminal sessions (kill the broker processes that run
  `D:\st_portable_*\...\agent_broker.py`), no sessions in `Data\Local`, and unchanged `Preferences`.
  Stale GhostShell terminal tabs in a restored session reattach to dead brokers and can hang a 3.8 host.
- The owner's real preferences in `Data\Packages\User\Preferences.sublime-settings` of 4215:
  `update_check false`, `ignored_packages ["Vintage"]`, `index_files false`, `color_scheme Mariana`.
  Tools such as `increase_font_size` and `ignore_word` add keys (`font_size`, `added_words`,
  `ignored_words`); restore a saved copy after any sweep.

## 3. Tools that need care (observed on 1.14.3, build 4215)

- **Open a browser:** `html_print` (Sublime's print: renders the active tab as HTML in the browser with the
  print prompt), `open_in_browser`, `open_context_url`, `open_url`, `purchase_license`, `get_help`, `show_changelog` (not tried alone), the licence tools
  (`show_license_window`, `upgrade_license`, `remove_license`: do not run). Never
  sweep them; the owner ends up staring at a web page of whatever tab was active.
- **Quit Sublime:** `exit`, `hot_exit`. `close_window` and `close_all` on the last window also quit it.
- **Change settings or create files:** `increase_font_size`, `decrease_font_size`, `ignore_word`,
  `add_word`, `set_setting`, `open_file_settings` (creates an empty `User\JSON.sublime-settings` etc. and
  makes that file the active tab, which is what the browser tools then act on).
- **Open a native dialog that blocks the main thread** (the call returns HTTP 500 "main-thread timeout
  after 5s" and `list_native_windows` shows `main_thread_blocked: true`; dismiss it, see the dialogs
  skill): `prompt_open_file` ("Open"), `prompt_open_folder` and `prompt_add_folder` ("Select Folder"),
  `prompt_open_project_or_workspace` and `prompt_switch_project_or_workspace` ("Open"), `prompt_save_as`
  and `save_file` on an untitled buffer ("Save As"), `primary_j_changed` ("Key Binding Changed ... Join
  Lines"), `close_tag` when a settings file is modified ("Save Changes?"), `profile_plugins` (a message that
  the file is not a syntax file), and `run_command context_menu` (a popup menu).
- **Required arguments:** called with empty values, 43 tools answer `{"error": "<arg> required"}` or
  "index out of range". That is validation, not a failure.
- **Not safe to sweep:** `install_package`, `install_package_control`, `remove_package` (network and
  package changes). `install_package` installs only the package, not the libraries it needs (see 5).
- `ui_click`, `ui_hover`, `ui_press_key` refuse unless the person at the keyboard has been idle for
  `min_idle_s` (default 8 s); pass `wait_idle_s` (up to 120) instead of retrying.

## 4. Sweeping all tools safely

`sweep.py` (next to this file) runs each tool once with the minimum arguments, clears any dialog it sees
(Cancel if there is a Cancel button), pings the main thread after every call, and on a hang kills and
restarts the portable from an empty session with `Preferences` restored. Result of the sweep on
2026-10-18 (1.14.3, portable 4215, Python 3.14), all 411 tools accounted for:

| Outcome | Tools |
|---|---|
| Ran and answered normally | 349 |
| Answered "argument required" / "index out of range" (empty arguments, validation) | 43 |
| Opened a native dialog that blocked the main thread until dismissed (the call returns HTTP 500) | 11: `primary_j_changed`, `prompt_add_folder`, `prompt_open_file`, `prompt_open_folder`, `prompt_open_project_or_workspace`, `prompt_save_as`, `prompt_switch_project_or_workspace`, `save`, `save_file`, `save_project_and_workspace_as`, `save_workspace_as` |
| Not run | 8: `install_package`, `install_package_control`, `open_url`, `purchase_license`, `remove_license`, `show_license_window`, `upgrade_license`, `show_changelog` |

- The 349 include `exit` and `hot_exit` (each quit the portable, as intended), `close_window` (closed the
  only window, which quits Sublime) and the four browser tools that ran by mistake in the first pass
  (`html_print`, `open_in_browser`, `open_context_url`, `get_help`). `sweep.py` now skips them.
- **No tool failed because of a defect in sublime-mcp.** A sweep that times out from its first call is a
  portable in a bad state (restored session, a dialog left open, extra windows): `ignore_word` and `noop`
  timed out on a hung portable and returned instantly on a clean one. A dialog with no OK button (Save As:
  Save, Cancel, Help) must be answered with Cancel; answering OK fails and leaves the main thread blocked,
  which makes every later call look broken.
- Rules for a sweep: ask first; use a clean portable; never the main Sublime; check
  `list_native_windows` after each call; keep a copy of `Preferences` and restore it; leave the portable
  empty and closed; do not run licence, install or browser tools.

## 5. Package testing facts

- MarkdownGlance 0.6.0 needs the Package Control libraries Markdown and pymdown-extensions. A package loads
  the moment it is installed, so without them it opens a "needs the Package Control libraries" dialog (one
  per load). Correct order: add the package to `ignored_packages`, `install_package`, run
  `satisfy_libraries`, remove it from `ignored_packages`. Verified in both portables: libraries installed
  (Markdown 3.2.2 / pymdown 8.1.1 on 3.8, 3.11.1 / 12.3 on 3.14), no dialog, and
  `mdglance_open_side_by_side` rendered a changelog preview. Remove with `PackageManager().remove_package`
  then `cleanup_libraries`.
- Do not run Package Control operations from `eval_python` while a Package Control background thread is
  still working (opening a file during the install finished hung the UI thread inside `open_file` once).
  Wait for "reloading plugin <package>" in the console.

## 6. Editing and releasing sublime-mcp

- The repo is LF. The `edit` tool on Windows writes CRLF; after any edit check
  `grep -c $'\r$' file` and restore LF (the 1.14.0 and 1.14.1 commits converted whole files to CRLF by
  accident). Python `open(..., newline="")` keeps the endings.
- Release: update README, `AGENT_GUIDE.md` and `docs/AGENT_GUIDE.md` (counts, new text) **before**
  tagging; version in `sublime_mcp.py`, `packages/node-proxy/package.json`,
  `packages/python-proxy/pyproject.toml`, `server.json` (twice); CHANGELOG entry; if tools changed run
  `tools/build_tool_tree.py` and `tools/generate_fallback_catalog.py`; commit, tag, push, `gh release
  create --notes-file`; PyPI with `python -m build` and `twine upload` in `packages/python-proxy`; npm is
  published by the owner's DOS console (a cmd tab in the main Sublime): type
  `cd /d C:\Users\donal\projects\sublime-mcp\packages\node-proxy && npm publish` into it
  (`ai_terminal_send_string` with a trailing `\r`) and the owner presses Enter at the browser login.
- Commit messages and release notes go through a file (`git commit -F`, `gh --notes-file`).
- Verify a release by installing it: `npm install sublime-mcp@X` then `npx sublime-mcp doctor`, and
  `pip install sublime-mcp==X` then the `sublime-mcp` console script (MCP handshake lists 8 tools).

## 7. GhostShell facts

- A long omp transcript used to keep the main thread busy: the omp tab redrew all 650 to 800 panels on
  every spinner tick (220 ms each). Fixed in 0.2.13 (only changed panels redraw).
- Menus asked every profile whether its program exists, searching PATH about 150 times per open
  (0.5 s). Fixed in 0.2.13 with a 15 s cache.
- Portable builds on the Python 3.8 host (build 4200) are not a release target; the owner said so.
- Terminal sessions live in broker processes (`agent_broker.py`); closing a tab detaches, End Session
  stops. A tab's colors come from `ai_terminal.sublime-color-scheme` (section 2).

## 8. Windows hang evidence

Windows Error Reporting has logged `AppHangB1`/`AppHang` for `sublime_text.exe` repeatedly since July
(for example 2026-10-17 22:31) and many `AppCrash` reports on 2026-10-03 and 04. The reports are under
`C:\ProgramData\Microsoft\Windows\WER\ReportArchive` (admin rights needed to open them). The one
reproduced cause of a freeze that involved sublime-mcp: a command that opens a native menu or dialog
blocks the main thread until it is dismissed (`run_command context_menu`; fixed by dismissing it).
