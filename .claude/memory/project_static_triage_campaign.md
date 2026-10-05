---
name: static-triage-campaign
description: 2026-09-25 switch from one-package-at-a-time live tests to whole-queue static triage (ruff + scans) with hand verification; where the tooling lives and what the yield was
metadata:
  node_type: memory
  type: project
  originSessionId: 1e07794b-efe6-4e5f-bbc3-7d3161a16a46
  modified: 2026-09-25T10:05:35.646Z
---

On 2026-09-25 the package bug hunt gained a bulk method: shallow-clone every queue repo (`campaign_tools/clone_all.py`, ~100 repos per 35 s), run ruff bug-class rules (F821 undefined names, B018/B015, F5xx format errors, PLE, S-rules), plus targeted scans (unverified TLS, tar extractall, http downloads, `os.system` interpolation, callbacks called instead of passed, undefined palette/menu commands, invalid Sublime JSON via `sublime.decode_value`, served-release syntax check). Every hit is verified by hand (reading context, `defcheck.py`, or running the package's own function in the ST 3.8 host / a sandbox) before filing with `gh issue create` via `campaign_tools/file_issues.py`.

**Why:** Donald wants every package covered ("just don't skip anything"); live-testing 3,800 packages one by one is not feasible, and the F821/`except ... as e`-closure class alone produced dozens of real bugs. Only packages that `PackageManager().list_available_packages()` serves on ST 4200 count (3,206 of 3,828 queue entries); the rest are ST2-era and are logged collectively as "not served".

**How to apply:** tooling and README are in `C:\Users\donal\projects\sublime-mcp\campaign_tools\`; results and every issue URL are in `.package_skill_test_log.md`. Before filing: check the repo is not archived / issues enabled, check for `globals()[...] =` and `try/except NameError` idioms (TernJS, Extend Selection, Baidu FE were false positives), verify captions/versions/claims (I edited several issues after filing). Use `gh issue create` (prints only the URL) instead of the MCP `create_issue` (~4k tokens of echo). Related: [[feedback-one-issue-per-finding]], [[feedback-report-bugs-never-patch-authors-code]], [[feedback-install-package-skips-libraries]].
