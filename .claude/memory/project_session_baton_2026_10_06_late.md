---
name: session-baton-2026-10-06-late
description: Handoff written 2026-10-06 evening before Donald restarts the session: audit state, rig state, rules he corrected, what is pending
metadata:
  type: project
---

Written 2026-10-06 (evening) at Donald's request, before restarting the session.

**Audit state**
- Log: `C:\Users\donal\projects\sublime-mcp\.package_skill_test_log.md` (gitignored; append with here-string plus `Add-Content -Encoding utf8`). Read its last PROGRESS NOTE and the newest entries first.
- Linux/macOS-only list (`C:\Users\donal\data\st_packages\served_on_linux_not_windows.tsv`) is done by name. Three entries are deferred (TestExUnit, SuperElixir, real-Erlang Erlyman) and Conda is deferred, all listed in `data\st_packages\deferred_big_installs.md`.
- Ranking file: `score_pkgs.tsv` in the scratchpad of session fcb54aa2. Filter for unlogged packages with the `next_pkgs.py` helper (checks the repo name against the log).
- Done this stretch: Cscope (inconclusive), Minifier (partial; retired default endpoint, already #27), Guna, Hayaku, IndentX (#22-24), Haxe (#281), Djaneiro (skipped, syntax-only), ActualVim (partial, needed nvim), npm (filed #49), Keymaps (partial), View In Browser, Maven (partial, no mvn), SublimeSBT (partial), PHPIntel (partial), Conda (deferred), MSBuild (full retest; filed tillig/SublimeMSBuild#15 and #16).
- [CORRECTED 2026-10-06, next session; Donald: "there is no list with those on it"] This line is unfounded, do not act on it. LSP-bash, LSP-intelephense and LSP-rust-analyzer are already logged in `.package_skill_test_log.md` (2026-10-01 entries, no defects). Whether Pywin32 or HTML5 are pending is NOT established. Always grep the whole log for a package name and read every hit before starting it.

**Rig state at handoff**
- WSL Sublime (sublime-mcp-wsl): MCP disconnected. Needs `/mcp` from Donald before any WSL test. Packages installed there: LSP, Package Control, SublimeLinter only.
- Windows portable 4215 (`D:\st_portable_4215`): running, MCP sublime-mcp-portable reconnected. Its installed packages are the pre-existing ones (Limitcode, LSP, MCP Commander, Package Control, SublimeLinter, Vala-TMBundle). MSBuild was removed after the test.
- Real Windows Sublime (the baton window) is not part of the audit; do not touch it.
- User PATH: `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin` added permanently at Donald's instruction. Keep it.

**Rules Donald corrected (follow these)**
- Never use Bash. Use the PowerShell tool and the MCP.
- Test through the MCP only. Do not call a portable's HTTP port (9510) to drive it; that bypasses the connection. If an MCP drops, ask Donald for `/mcp` and wait.
- No stand-ins when the real tool exists. Install the real prerequisite, or say you are deferring it. No half-jobs.
- Test the package's own build or run command, not a hand-written copy of it.
- When a dialog or picker blocks Sublime: read it first (screenshot, or computer-use image capture of that window), tell Donald what it says, and close it only when he says to. Computer-use is approved for the quick-panel picker in the Windows portable.
- Report bugs by filing them: check existing issues first, one finding per issue, short plain text.
- Donald runs the package list; do not ask him to launch instances. Launch the portable yourself, then tell him.
- Never mention or reopen Qwen. Never reply to GitHub mail. Never post publicly without his word (filing bugs under the campaign rule is fine).

**Half-hour check (rerun at restart)**
- Gmail search (snippets only): the last run found nothing unread.
- PR status board (`C:/Users/donal/tools/gh_status/pr_status.py`): last run had one known item, the Glama bot comment on punkpeye/awesome-mcp-servers#15729. That run was interrupted, so rerun it.
- Forum topic 79298 (kaste): no reply as of 2026-10-06; rerun.
- ccstatusline#656: 0 comments as of 2026-10-06; rerun.

**Open items**
- Nothing waiting on Donald except the reconnect for WSL MCP if he wants WSL tests.
- Dialog from the Keymaps test was closed by Donald. Keymaps' syntax-path error was not confirmed in source (package was removed).
- Default-variant Debug output of MSBuild was not captured separately; it was covered by the picker run afterward.

Related: [[project_wsl_st_running_2026_10_06]], [[feedback_safety_check_stopped_phpintel]], [[feedback_close_test_windows_when_done]]
