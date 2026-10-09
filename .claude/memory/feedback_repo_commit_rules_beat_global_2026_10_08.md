---
name: repo-commit-rules-beat-global-2026-10-08
description: 2026-10-08 Donald said the global "do not commit or push" rule is too general; a repo's own AGENTS.md (GhostShell: commit each finished piece, push to origin/main, stage only your own files) decides, the global rule is only the default
metadata:
  type: feedback
---

Donald (2026-10-08): "global rule is too general (commits)". `C:\Users\donal\.claude\rules\repo-memories.md` says not to commit or push unless he asks. In a repo that has its own AGENTS.md with commit rules (GhostShell does: commit each finished piece, push to origin/main, stage only files you changed, never discard others' work), follow the repo's rules.

**Why:** the global line was written for the sublime-mcp research files and the pybackup tool; it was never meant to override a repo that tells agents to commit.

**How to apply:** read AGENTS.md / CLAUDE.md of the repo first. If it says commit and push, do so for finished work only (after it is proven working), staging only my own files. Elsewhere (no repo rule) keep the global default. Related: [[feedback-no-dev-copies-in-projects-2026-10-07]].

Same day he called GhostShell's logging "a shambles" that "requires a completely new logging strategy" (trigger: logging stops when an agent tab is moved to Windows Terminal). Nothing implemented yet; GhostShell rules 13/14 (AGENTS.md) say new log files need his approval and an entry in docs/LOG_DIRECTORIES.md, and rule 7a says no unit tests, prove changes in the live Sublime.
