---
name: sublime-mcp-explicit-targeting-deferred
description: "audit (2026-10-02) found 0 of 403 sublime-mcp tools accept window_id/view_id; Donald deferred the fix (\"important but too hard\"); the resource-claim tools (claim_resource etc.) written by jcode were later committed and released in 1.12.0 (commit 9aa34c9, 2026-10-02)"
metadata:
  node_type: memory
  type: project
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-05T01:55:05.712Z
---

2026-10-02: Donald asked me to help jcode (another agent, Tab 2) with concurrency questions about sublime-mcp. Outcome:

- My read-only audit (`C:\Users\donal\tools\sublime_mcp_targeting_audit.md`, script `audit_targets.py` in `C:\Users\donal\tools\sublime_mcp_snapshots\`): of 403 routes, 0 take an explicit window_id/view_id; ~360 act on "the active window/view" at call time; `_vc(cmd)` (137 routes) and `_wc(cmd)` (153 routes) are the two generic wrappers where one optional, backwards-compatible `view_id`/`window_id` change would cover most. Real incident this came from: `open_project_or_workspace` called via a non-active Window changed the active window's project.
- Proposed (NOT applied): add optional view_id/window_id to `_vc`/`_wc`/`_resolve_view`, error (no fallback) if the id is stale, return ids from the read tools; develop on the portable's copy first, test, show Donald a plain-English summary before touching the repo.
- jcode's change (written 2026-10-02, +177 lines, additive only: `claim_resource`/`release_resource`/`list_claims`, TTL-bounded advisory claims) was, when this note was first written, uncommitted and never run live. It was afterwards committed and released as 1.12.0 (commit 9aa34c9, tag v1.12.0, with `test/test_resource_claims.py` in the repo); I did not trace who made that commit or whether it was run live. Donald did not fully trust jcode editing sublime-mcp at the time. Saved copies from before the commit: `C:\Users\donal\tools\sublime_mcp_snapshots\` (patch, file with changes, original HEAD 4089b0e).
- My answers to jcode: `C:\Users\donal\tools\sublime_mcp_answers_from_claude.md`; field notes: `sublime_mcp_field_notes.md` (same folder).
- Decision: Donald wants this saved for later ("important but too hard"). Do NOT start it unasked; remind him once when he brings up sublime-mcp or concurrency.

**Why:** the fix is wanted but he finds it too hard to supervise right now; he is wary of agents editing his repo.
**How to apply:** when he raises it, restart from the audit file; keep edits additive, test on the portable first, plain-English diff summary, no commits without his say. Related: [[feedback_diff_review_ux]], [[feedback_report_bugs_never_patch_authors_code]].
