---
name: project_gadzillion_package_test_campaign
description: "A week-long, cron-driven campaign (started 2026-09-09) randomly sampling installed Sublime Text packages to stress-test the \"discover -> read source -> call directly, no dedicated MCP needed\" thesis"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6baf5f30-f111-4757-8168-5593e86f5789
  modified: 2026-09-09T18:33:36.446Z
---

Started 2026-09-09, after the user pushed back hard on an earlier
architectural claim ("no dedicated MCP needed for most packages") having
only been tested against 3 packages. The user's own words: "I would give
it a week. A few a day, randomly selected. I am sure you are wrong."

**Why**: 3 samples wasn't enough to falsify or confirm the thesis. The
user had personally looked at ~5 packages and was "astounded at the
craftsmanship," suspecting well-built packages would resist the
discover/read-source/call-directly approach more than the easy cases
already tested.

**How to apply**: this is an ongoing, multi-day effort. State as of
2026-09-09 (day 1, 8 packages tested): the core thesis holds -- no
package needed a dedicated MCP server -- but a more precise, corrected
claim emerged: "run_command args alone are always enough" does NOT
hold; some commands are deliberately UI-only (no args, e.g. Notr's
`notr_open_project`) and need the deeper `eval_python`/`sys.modules`
internals-reach fallback instead. Real findings so far: 2 upstream bugs
filed (cepthomas/Notr#1 - broken Help link; tonylchang/sublime-llm#2 -
misleading rate-limit error masking a real no-credits case), 1 clean
success (OpenUri), 1 total load failure from a missing native dependency
(Helium/pyzmq -- a boundary case, not a thesis failure), multiple
blocking-modal-dialog traps found live (GitGutter's support_info, LLM's
clear_chat) that introspection alone never surfaces.

Log lives at `C:\Users\donal\projects\sublime-mcp\.package_skill_test_log.md`
(gitignored, not committed -- a working log, not a deliverable). Skills
were meant to go to `~/.claude/skills/<package>-control/SKILL.md` as they're
verified [CHECK 2026-10-05: that folder holds only three, `debugger-control`, `lsp-control` and `openuri-control`, so most packages tested in this campaign never got a skill file; this note is the historical 2026-09-09 plan, and the later audit campaign works differently]. A CronCreate job (session-scoped, dies if the session/terminal
closes, auto-expires after 7 days per the platform's own limit) was set
up to continue picking 2-3 new random packages daily -- but cron jobs in
this harness are NOT durable across session restarts, so if a new
session starts without the job still running, the week's cadence needs
to be picked back up manually by re-reading the log for what's already
been tested and continuing from there, biasing toward substantial/
complex/actively-maintained packages rather than truly random trivial
ones (that's where the thesis actually gets tested).

See also [[project_ghostshell_secrets_hardening]], a real follow-up task
that came out of this campaign's LLM package investigation.

**Update 2026-09-09 (end of day 1, 10 packages tested)**: thesis held
across all 10 (AssistantAI, GitGutter, Notr, OpenUri, LLM, Helium,
FileBrowser, and others) -- no package required a dedicated MCP server;
`discover -> read source -> eval_python`/`run_command` internals-reach
plus a generated skill file was always sufficient, even for the hardest
case (FileBrowser's invisible input-panel views). The user has
confirmed this is now established well enough to stop treating it as
open: **it is not necessary to build MCPs for Sublime Text packages --
generated skills suffice.** Packages installed only for testing were
uninstalled afterward (settings entry removed, `.sublime-package`
deleted) to keep the environment clean between rounds -- except OpenUri
(detects/opens URIs from links in a file), which the user kept
installed for real use, surprised enough by its usefulness ("hard to
believe") to make it the one exception. Why it earns its keep: without
it, opening a link found in a text file means manually selecting the
link text, hitting ctrl-c, switching to Edge, pasting, and pressing
enter -- OpenUri collapses that whole sequence into one action from
inside Sublime. Continuing the campaign now is
about breadth/confidence and catching edge cases, not about
re-litigating the core claim.

**Update 2026-09-09 (real bug found via TreeSitter testing)**: while
testing TreeSitter (package 11, using the newer `get_package_mcp_info`
discover-tools workflow), a real bug in sublime-mcp itself surfaced --
`_find_view_by_name`/`_resolve_view`/`_get_view_size`/`_get_view_chars`
all matched tabs against `view.name()` only, which is empty for any
normal saved file never explicitly renamed via `set_name()`, so
`run_command`'s/`get_view_content`'s `name=` targeting silently failed
for ordinary files (only `get_open_files` had the correct basename
fallback). Fixed with a shared `_view_display_name()` helper, released
as sublime-mcp 1.7.4 (PyPI, npm, MCP Registry, GitHub `main` all
updated same session). Editing the live plugin file mid-session while
it was serving requests wedged the plugin_host main thread (all calls,
even `get_help`, hung) -- fixed by restarting Sublime Text, consistent
with [[feedback_sublime_mcp_batch_permission_hang]]'s "check if ALL
calls hang uniformly" diagnostic. Good validation of the campaign's own
method: the bug was found by actually using the discover-source-call
loop on a real package, not by auditing sublime-mcp directly.

**GitSavvy tested 2026-09-09 (package 12)**: largest command surface
in the campaign (~340 commands). Verified `gs_show_status` against the
real sublime-mcp repo -- accurate branch/HEAD/untracked-files output,
cross-checked against real `git status`. Found another real
blocking-modal-dialog trap (same family as GitGutter/LLM found
earlier): GitSavvy's repo-detection reads the *active view's file
path*, not the window's project folders, so calling a GitSavvy
WindowCommand while a no-path tab (like the Claude control tab) has
global focus makes it think the window isn't a git repo and pop a
blocking native `ok_cancel_dialog`, wedging the main thread for 5+
seconds. Fix: always focus a real in-repo file view via `eval_python`
before invoking GitSavvy commands. Uninstalled after testing.

**Terminus tested 2026-09-09 (package 13)**: this is the package
GhostShell's own `ai_terminal` panel is meant to replace -- verified
live (real spawned `cmd.exe`, real PTY write/read round-trip via
`terminus_send_string`). Confirmed working correctly. Worth remembering
for [[project_ghostshell_secrets_hardening]] or any future GhostShell/
ai_terminal comparison work: Terminus terminals opened as a panel are Sublime *output
panels*, not regular views (Terminus can also open them as tabs; this was the panel case), so sublime-mcp's `get_view_content`/
`run_command` name-targeting (even post-1.7.4) can't reach them --
needs `eval_python` + `window.find_output_panel(name)` directly. A
`get_panel_content`-style tool would be a real, useful sublime-mcp
enhancement if output-panel-based packages come up again. Uninstalled
after testing.

**Sampling method upgraded 2026-09-09**: true random sampling across
all 4,713 Package Control packages would take 600+ days at this pace
and mostly hits trivial asset-only packages (color schemes, syntax
bundles, snippets, localizations) that have zero command surface and
don't test the thesis at all. New standing method: pull candidates from
`packagecontrol.io/browse/popular.json` (real `unique_installs`/
`installs_rank` data -- confirmed live, e.g. GitSavvy is installs_rank
275), skip asset-only entries, and pick from what's left. This biases
toward exactly the well-crafted, actually-relied-upon packages the
user's original hypothesis was about, rather than uniform random noise.
Emmet (installs #2, 6.1M) and SublimeLinter (#5, 2.3M) were already
covered under this list by coincidence. Untested top-25 candidates
noted for next rounds: SideBarEnhancements, BracketHighlighter,
WakaTime, SublimeCodeIntel, AutoFileName, Alignment, ColorPicker,
Pretty JSON, Git (the simpler non-GitSavvy one), DocBlockr.
SublimeREPL deliberately skipped -- the user recently uninstalled it
themselves, so not a fair random pick right now.

**BracketHighlighter tested 2026-09-09 (package 16, #4 by real
installs)**: hit a genuine missing-library boundary case on install
(`ModuleNotFoundError: backrefs`, a declared-but-not-yet-satisfied
Package Control dependency) -- fixed live via the real
`satisfy_libraries` ApplicationCommand rather than restarting ST.
`swap_brackets` turned out to be the hardest single command since
FileBrowser (quick-panel-only, multi-stage internals with reused-index
semantics between stages); confirmed the menu/detection logic is real
and accurate, captured the real quick-panel callback once via the same
monkeypatch technique used for FileBrowser, but full scripted
end-to-end invocation wasn't reliably reproducible in a reasonable time
budget -- documented honestly as a partial success. `bh_toggle_high_visibility`
confirmed straightforward (flips a real in-memory module global).

User context: has personally used Pretty JSON (currently) and
SideBarEnhancements (long ago, not currently) -- both from the top-25
popular-packages list. Doesn't block testing them, but worth knowing
these aren't blind picks for the user the way most of this campaign's
packages are.

**DocBlockr tested 2026-09-09 (package 17, #23 by real installs)**:
real methodology finding -- `get_package_mcp_info` only found 2 minor
commands because DocBlockr's actual core command (`jsdocs`) is declared
*only* in a context-gated `.sublime-keymap` binding (Enter after
`/**`), never in `.sublime-commands`. Found by reading the keymap files
directly. General lesson: a thin command list from the discovery tool
doesn't mean a package is simple -- check `*.sublime-keymap` too.
Verified real signature-aware parsing (correctly typed a `callback`
param as `Function` vs generic placeholders for other params).

**Update 2026-09-09 (resumed after session restart, 19 packages tested)**:
session-scoped CronCreate job died with the session, as expected --
picked back up manually per this memory's own instructions, reading the
log for what's tested and continuing. Two more packages tested,
targeting failure-mode axes nothing earlier in the campaign had hit:

- **SideBarEnhancements** (#1 by real installs): confirmed its
  `paths`-arg commands (which look context-menu-only, since every
  Command Palette entry shows `args: {}`) are directly scriptable --
  passing an explicit path list via `run_command` works with no sidebar
  selection needed. Also found `side_bar_delete` has a source-level
  `confirmed="True"` bypass for its own confirmation dialog (documented
  from source only, not invoked live -- destructive and not worth the
  risk to confirm what the code already shows).
- **ColorPicker**: found the first case in the campaign of a real,
  unbridgeable boundary -- on Windows it calls
  `ctypes.windll.Comdlg32.ChooseColorW` directly, a native Win32 modal
  dialog with no Python-reachable callback at all (unlike Sublime's own
  `ok_cancel_dialog`/`show_quick_panel`, which can be dodged or
  monkeypatched). Confirmed from source only, deliberately not invoked
  live (would pop a real un-scriptable modal). This is the boundary of
  the whole thesis stated precisely: "no dedicated MCP needed" was
  always about Sublime's own package layer, not about replacing
  OS-native UI -- that would need a `computer-use`-style tool driving
  the dialog by window handle, not a sublime-mcp gap.

**Correction, same session**: both of those "uninstalled" claims were
initially false. `run_command("remove_package", {"package": name})`
returned `ok: true` but the real ST console showed
`TypeError: run() got an unexpected keyword argument 'package'` --
Package Control's `remove_package` command is quick-panel-only with no
scriptable package-name arg at all (`ExistingPackagesCommand` base;
`on_done` only fires after a live UI pick). Both packages were still
genuinely installed. Fixed by going straight to Package Control's
internals via `eval_python`: `PackageTaskRunner(PackageManager()).
remove_packages({names}, progress)`. **Standing lesson for this
campaign and beyond**: `run_command` returning `ok: true` only means
sublime-mcp's dispatcher didn't except -- it does not prove the
underlying ST command succeeded. Cross-check consequential calls
against the real console before trusting them, same as the
FileBrowser/GitSavvy dialog traps taught to pre-focus before assuming
state.

A third package, **WakaTime**, tested the same session: found a new
trap variant (auto-opens a `show_input_panel` for its API key on
package *load*, not on any command -- installing it alone leaves an
unnoticed input panel open, closed via `hide_panel`), plus a real
`sys.modules` lookup gap (the loaded module never appeared under any
key/substring search, worked around via
`importlib.util.spec_from_file_location` against the known file path
as a fallback pattern worth remembering). Confirmed its whole
heartbeat pipeline runs via direct function calls with no ST command
involved. All three packages (SideBarEnhancements, ColorPicker,
WakaTime) verified actually uninstalled via `list_packages()`. 20
packages tested total as of this update.

Standing note for future resumption: only log entries that surface a
new failure mode / methodology lesson / sublime-mcp defect get a full
section now; plain repeats get one line.

**Unresolved side note**: the user recalled TreeSitter being "mentioned in
conjunction with PyCharm," possibly from a YouTube video -- likely
referring to PyCharm's TreeSitterViewer plugin (github.com/Enaium/
intellij-tree-sitter-viewer, only ~110 downloads). Searched TubeAlfred
with several query variants, no matching video found. TreeSitter has
since been uninstalled (it had zero real dependents on this machine --
confirmed via grep across every installed package's source, live and
zipped, for `sublime_tree_sitter`/`tree_sitter` imports; only kaste's
niche git-clone-only `TreeSitter-calls-and-callers` addon uses it in
the wild). Left as an open mystery, not worth further search credits.
