---
name: fresh-audit-list-2026-10-07
description: 2026-10-07 Donald's rules for choosing audit packages, how the fresh list was built (network, once), what was tested and filed that day, and what is left
metadata:
  type: project
---

**His rules (said 2026-10-07):** do not select old, unused or archived packages, nor packages by dead or hostile authors; only the most-installed or the largest matter; newest first; leave out packages already tested. "Start over" meant: rebuild the list from scratch with fresh data, reusing only the test log to remove done packages (the first attempt reused the old 2026-10-03 ranking and he stopped it). He also said not to defer anything (a 61 MB runtime download was done, after checking its real size). Order for easing the cut: do the strict list first, then ease the last rule step by step.

**How the list was built:** one pass over the network, one reused connection per site, paced: Package Control `channel_v3.json` (names to GitHub repos), `browse/popular.json` pages 1-40 (installs), and GitHub GraphQL in batches of 100 for all 4,751 repos (archived, last push, languages). About 110 requests, no failures. Filters in order: not archived, pushed in the last 2 years, not a flagged author (Sainan/PlutoLang, alepez, Naereen), at least 4 KB of Python (real plugins), top 1,000 by installs or at least 100 KB of Python, not named anywhere in `.package_skill_test_log.md`. Result file: `C:\Users\donal\data\st_packages\audit_list_2026_10_07.tsv` (rewritten after each easing step). The scripts were in a session scratchpad and may be gone.

**What the list showed:** only 4 strict items. At the loosest tier (any real plugin, 4 KB or more) only 29 packages remain, because 346 of the 375 maintained real plugins were already in the log. Easing further would mean packages older than 2 years, which he does not want.

**Tested 2026-10-07 (all logged in the test log, all removed afterwards):**
- SettingsUI: no defects; works in both portables and in his main Sublime.
- LSP-MaaFramework: no defects confirmed; runtime install tested (one partial install not reproduced).
- SublimeLinter-contrib-sublime-syntax: issue FichteFoll/SublimeLinter-contrib-sublime-syntax#9 (native error dialog on an unknown syntax in the first line).
- Advanced PLSQL: issues are disabled, so the finding (Build silently does nothing on a file with no create statement) was emailed to the maintainer in the "Claude reports:" form.
- MarkdownPreviewOverlay: no defects confirmed.
- Sema: no defects; the real sema 1.36.1 is kept in `C:\Users\donal\tools\sema-1.36.1`.
- ToolRunner: issue KuttKatrea/sublime-toolrunner#3 (tmpfile output modes lose all output).
Remaining tier-4 items (mostly small LSP-* wrappers) were not started.

**Working lessons from that day:** package tests run in the portables; "test here" meant his main Sublime only for the SettingsUI report he made himself. Waiting for library installs sat idle for minutes and he objected ("you just wasted minutes of my time"): start independent work while installs run, and keep progress lines short. Do not read the whole console log (it ignores `tail` and prints everything). Related: [[feedback_skip_unmaintained_packages]], [[feedback_defer_big_installs_dont_skip]], [[project_limitcode_full_test_2026_10_06]].
