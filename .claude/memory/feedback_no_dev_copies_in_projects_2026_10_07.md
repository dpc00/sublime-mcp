---
name: no-dev-copies-in-projects-2026-10-07
description: 2026-10-07 pybackup commits and pushes every repo under ~/projects, so temporary worktrees or clones must live outside it
metadata:
  type: feedback
---

2026-10-07, Donald: "pybackup will attempt to commit and push any repo in ~/projects." I had made a git worktree for a sublime-mcp fix at `C:\Users\donal\projects\sublime-mcp-dev`, which pybackup would have treated as a repo (committing and possibly pushing its branch). It was merged into main (fast-forward, commit c9a3965) and then removed, with the branch deleted.

**Why:** pybackup runs unattended and does not know a folder is a scratch copy; a stray branch or half-finished work could be pushed to GitHub.

**How to apply:** put worktrees, clones and test copies outside `~/projects` (for example `C:\Users\donal\data\dev\<name>`), and remove them when the work is merged. Develop on a branch there, test on the 4200 portable by pointing its shim (`D:\st_portable_4200\Data\Packages\MCP Commander\sublime_mcp.py`, the `_REPO_FILE` line) at the copy, and put the shim back afterwards. Never edit `main` directly while the real Sublime and the 4215 portable load it. Related: [[reference_sublime_mcp_release_steps]].
