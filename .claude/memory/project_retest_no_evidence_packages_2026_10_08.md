---
name: retest-no-evidence-packages-2026-10-08
description: 2026-10-08 Donald ordered a retest of the 57 packages that are in .tested_packages.tsv only because of queue position (no trace in the test log); list file, the procedure that worked on the first one (MarLant), hazards, his rules, what is done and what is open
metadata:
  type: project
---

**Order (Donald, 2026-10-08, "definitely... serious omissions/failures"):** retest every package that the tested list marks done only by queue position and that appears nowhere in `.package_skill_test_log.md`. 386 rows were "recovered from queue order"; 57 of them have no trace in the log. Work list: `C:\Users\donal\data\st_packages\retest_no_evidence_2026_10_08.txt` (one name per line). PROGRESS: a package is done when `.tested_packages.tsv` has a row for it whose text starts "retested in the main Sublime"; remaining = the list file minus those names. Done so far (nothing left installed in his Sublime): MarLant (issue #16), Adept, Miking Syntax Highlighting, LSP-R (loads only; R install deferred), SublimeLinter-gjslint (tool is Python 2 only; inconclusive), Mooon Light Theme, Extract Sublime Package, CodeLines (issue #3), AlgoLang, Display numbers (popup unverified), RegexMatch (issue #1), Advanced Substation Alpha (ASS), Highlight Duplicates, PyScript, ImportHelper (issue #121), Codam Headers, Meteor Reval (issue #4), NativeScript Core XML Syntax, QColor (issue #11), Icon Fonts, Clickable WSDL (issue #2), Monokai++, ProjectNotes (archived, project path not exercised), Algo2-TADs (issue #1), CppFastOlympicCoding (issues #107, #108, fully exercised), Ebitengine Kage (issue #1), HoverDocs (issue #9, hover really tested), Justify, WebFont (issue #9), Smithy, CNC BoschRexroth MTX, MikrotikScript (issue #14), Jedi (issue #336), TabNav (issue #6), Alphanumeric Markdown Footnote (needs 4200, not filed), Twilight+, Evernote (issue #225 closed again: 4215-only), EraBasic, TemplateToolkit (issue #1), DocBlockr_Python, Taskfile, TypeShort, Snowflake, CustomStatusMessage, Hivacruz Theme, Fall Syntax Colorscheme, ALE Syntax Highlight, Yara Rule Syntax, Coddy Colour Scheme (issue #1), PokemonTeamSyntax, Caddyfile Syntax, WebAssembly Text Syntax, Visual Studio Dark, Language 1C (BSL) (issue #11), mIRC (first on the list, done after Ruby Slim; Sublime raised a Save-less "Error loading syntax file" dialog on removal once), Ruby Slim, Switch Window (redone with two windows; 57 of 57 (LSP-R only loaded); no defect except MarLant; Switch: Window list palette not visible via screenshot). Order used: the list order. Compaction warning: his context window was at 96% when this was written. Do it in his MAIN Sublime, no portables (only 4200 if needed), one window, with the COMPLETE console read. Record each result as a new dated row in `.tested_packages.tsv` plus a short entry in the test log (both gitignored); file one short issue per real finding after checking existing issues.

**Procedure that worked (MarLant, about 20 calls; aim for about 6 messages per package):**
1. `run_command install_package`, wait about 12 s (foreground sleeps over about 20 s are blocked; use a background timer for longer), `pick_quick_panel text="<exact name>"` (an exact name beats look-alikes; `get_quick_panel text=...` first if unsure), wait about 15 s.
2. `list_native_windows` (dialogs) + `get_console mode=visible tail=25` (complete:true, reversible: it briefly opens the console and restores panel, focus, pointer and clipboard). Do NOT trust `mode=captured` for "no errors": the log's own standing rule says it can drop tracebacks.
3. See what the package holds: list the installed zip (`Installed Packages\<name>.sublime-package`, PowerShell ZipFile) by extension: plugin .py, syntaxes, color schemes, themes, commands files, syntax tests. Channel info (description, labels, home) is in `C:\Users\donal\data\st_packages\channel_v3_2026_10_08.json`.
4. Exercise: syntax via `set_syntax name=...` on a test buffer (or a saved file with the right extension); plugin commands via `get_command_palette caption=...` then `run_command ... scope="text"` for TextCommands (window scope returns ok but does nothing); use a SAVED file in the session scratchpad for file-based commands; color schemes via `set_setting color_scheme` at view scope; do not apply UI themes (global). Read the console again after exercising.
5. Clean up: close test tabs (closing a dirty tab raises "Save Changes?": `dismiss_native_window button="No"`), `run_command remove_package`, `pick_quick_panel` exact name, verify the zip/folder/User settings are gone.

**Hazards:** the ONLY original tab in his window is the Claude tab; never call `close_file` unless `get_layout` shows a test tab is the active view (use `close_by_index group=0 index=N` for a specific tab instead). Package Control opens a "Package Control Messages" tab after install that covers his Claude tab: close it at once. `get_active_file` on the Claude tab returns the whole terminal text (huge): avoid it when that tab is active. Do not use the Debugger/quit/hide_panel cleanup combination (his Sublime once exited right after it, cause unknown). If Sublime exits, start `C:\Program Files\Sublime Text\sublime_text.exe`; GhostShell reattaches the Claude tab (it lives in a broker process).

**MarLant (queue v1, v0.7.0), done 2026-10-08:** installs clean (full console: "successfully installed", plugin loaded, no dialogs); one syntax "SubRip / SRT" highlights numbers, timings and text; auto-detected on a saved .srt; renumber/validate work on a saved file. Defect: "MarLant: Renumber titles" raises `TypeError ... not 'NoneType'` (`pathlib.Path(...file_name())`, marlant.py line 586) on an unsaved tab and does nothing visible; the name is only needed when a project file is open; the other three commands that read `file_name()` need one by nature. Filed https://github.com/retifrav/marlant/issues/16 (no existing issue covered it). Not checked: what "Validate all titles" reports for the bad timing in my sample (it printed nothing and showed no marks), split/join/shift/translation commands. Removed cleanly.

**Still open (offered to Donald, not yet started):** (2) every earlier "no console errors" verdict from `captured` mode is provisional (the log says so); my own results earlier today (LSP, A File Icon, JSON Color Schemes, SquareTable, StringEncode, Debugger) also relied on captured reads, though I also checked results directly; (3) 104 lines of the log mention crash/hang/abort/incomplete and have not been triaged for tests that were cut short. The two "stale" baton notes were checked: phplint (queue v2 #10, tool dead on PHP 8) and Jester (queue 577, issues #4 and #5) were both completed later, so they were not aborts; Donald has not yet agreed to recycle them.

**His working rules in this task:** one window; short messages (one line per batch); do not ask whether to continue; notes go in the repo; do not commit in other repos. Related: [[audit-exhausted-and-reload-hang-2026-10-08]], [[eased-list-weak-records-2026-10-08]].























FOUND 2026-10-08: the main Sublime 4215 has only a Python 3.14 plugin host; a .python-version of 3.3 or 3.8 in an unpacked copy starts no other host. Packages that only fail on 3.14 must be tested on the 4200 portable (see [[feedback_dont_report_newest_build_lag]]) and not filed from 4215. Batch them for one 4200 session: Alphanumeric Markdown Footnote so far.












FILING CLEANUP 2026-10-08 (Donald: 'file anything you find'): after he said the old 'not filed (age/4215-only)' log entries were a mess, a background agent filed the real skipped findings: Flake8Lint#126, CSScheme#20, exalt#24, DoxyDoc#17, SourcePawnCompletions#18, sublime-phpactor-plugin#2, SwitchDictionary#3, Sublime-Minifier#38, SublimeSBT#49, sublime-keymaps#35, SublimeLinter-inline-errors#13, EasyClangComplete#781. Skipped by it: SublimeZilla (already #27), MSBuild (already #15, #16), JavascriptExtractFunction (archived), MOHAA (no repo), Advanced PLSQL (issues disabled, emailed 2026-10-07). Issue bodies: scratchpad\agent_issues.
















CLEANUP 2026-10-08: Donald said I left something from the package tests. Restored his single-pane layout (I had added a second group for test tabs and left it); removed the Debugger package and User\Debugger.sublime-settings (recycled), which had stayed from the debugger comparison. For future retests: tests go in a second group ONLY while running, and restore set_layout cols [0,1] rows [0,1] cells [[0,0,1,1]] right after each package. The white outline boxes in the Claude tab were Highlight Duplicates region DuplicatesHighlightListener (it auto-highlights duplicate lines in the active tab; the Claude tab was active when it installed); erased with view.erase_regions via eval_python (sublime-mcp has no erase-regions tool: gap). Before testing an auto-acting package, make a test tab active so it cannot act on the Claude tab; after any package, look at the Claude tab for leftovers.








HAZARD 2026-10-08: CodeLines left a hidden output panel (FileSize) whose syntax vanished with the package; every later package reload raised a modal 'Error loading syntax file FileSize.sublime-syntax'. Fix: window.destroy_output_panel('FileSize') (eval_python). Before removing any package that creates output panels or views, destroy/close them first.


