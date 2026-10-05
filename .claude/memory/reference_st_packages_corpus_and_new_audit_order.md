---
name: st-packages-corpus-and-new-audit-order
description: "Where Donald's package corpus lists live (C:\\Users\\donal\\data\\st_packages), that the repos folder is gone, and his 2026-10-03 rule: audit largest packages first, skip syntax/snippet/theme-only ones"
metadata:
  node_type: memory
  type: reference
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-04T01:43:30.066Z
---

`C:\Users\donal\data\st_packages` (his ~/data/st_packages) holds the lists only: `all_files.txt` (every file of ~4,879 packages, paths as `owner_repo\path`), `clone_list.tsv`, `channel_v3.json`, `manifest_github.jsonl`, `FINDINGS.md` (June 2026 census), `rename_plan.tsv`. The `repos\` folder it describes no longer exists on disk (checked 2026-10-03), so byte sizes are unavailable.

**Donald's rule (2026-10-03):** order the audit by package size, largest first, and ignore insignificant syntax-only, snippet-only, theme and colour-scheme packages. Because there are no repos, I rank by number of Python files from `all_files.txt` (script in the scratchpad: rank_pkgs.py, output rank_pkgs.tsv; vendored folders and tests excluded; names matched against `.package_skill_test_log.md` to mark done ones). 3,063 packages have Python; 2,380 of them not found in the log.

**BETTER METRIC (same day, Donald: "come up with a metric which includes all the statistics with some appropriate weights", "eliminate any archived projects"):** scratchpad script `score_pkgs.py` fetches GitHub stats for every GitHub-hosted package in `manifest_github.jsonl` (GraphQL via gh, cached in gh_stats.json) and ranks by weighted percentile ranks: Python bytes 0.30, Package Control installs 0.25 (from queue_v2_by_installs.json), stars 0.15, forks 0.10, recency of last push 0.10, open issues 0.05, watchers 0.05. Drops archived repos and anything under 4 KB of Python. Output `score_pkgs.tsv` (scratchpad); 1,499 scored, 943 not yet in the log (name match, approximate). Top: Arduino-like IDE, SublimeHaskell, SublimePythonIDE, FileHeader, Python Flake8 Lint, JavaScript Completions, Nodejs, Hayaku, Golang Build.

**How to apply:** use that ranking, not the popularity queue (`campaign_tools/queue_v2_by_installs.json`). Many top entries need paid software or large servers (3ds Max, Maya, Swift, Elasticsearch): log them as skipped with the reason, per [[feedback_no_retests_no_big_downloads]]. Related: [[project_package_audit_campaign_stopped_2026_10_03]].
