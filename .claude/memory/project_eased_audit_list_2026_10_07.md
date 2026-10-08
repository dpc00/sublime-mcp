---
name: eased-audit-list-2026-10-07
description: 2026-10-07 the fresh list was exhausted, so the push-date rule was eased from 2 to 4 years (top 1000 by installs only); 11 packages, all done; results and decisions
metadata:
  type: project
---

2026-10-07 Donald agreed to ease the one remaining rule: last push up to 4 years ago instead of 2, but only for the top 1,000 packages by installs (not archived, no flagged authors, at least 4 KB of Python, not already in the test log). The rebuild used about 50 network requests and saved its raw data in `C:\Users\donal\data\st_packages` (`popular_2026_10_07.jsonl`, `popular_gh_2026_10_07.jsonl`, `channel_v3_full_2026_10_07.json`, list `audit_list_2026_10_07_eased4y.tsv`). Result: 11 packages.

**Outcome (details in `.package_skill_test_log.md`):** ayu: issue dempfi/ayu#299 (its A File Icon popup Install link calls the nonexistent `advanced_install_package`). EasyClangComplete: fails to load on 4215 (module_reloader, 4215-only, not filed) and on 4200 (`typing` ImportError from mdpopups 4.3.5 for Python 3.3; traceback not seen in full, not filed). PHPGrammar, FileManager (release and master), SublimeAStyleFormatter: no defects. SideBarFolders: no release in the channel, skipped. SublimeCodeIntel: no completions on 4200, dead project, not filed. Skipped as long-dead (last release 2014-2022): Lua Love, Filter Lines, SublimeERB, Ecmascript Syntax.

**Why:** the audit exists to find sublime-mcp weaknesses; package findings are a side result. **How to apply:** the list is finished; do not ease further without Donald (older than 4 years means dead packages he does not want). New lessons are in the audit skill: swap master in only with a restart; test Python plugins on 4200 first; 4215-only failures are logged, not filed. Related: [[fresh-audit-list-2026-10-07]], [[feedback_skip_unmaintained_packages]].
