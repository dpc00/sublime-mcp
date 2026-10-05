---
name: qwen-pr-10720-followup
description: "QwenLM/qwen-code PR #10720 (Ctrl+C exit warning) - conflict fixed 2026-10-04; reviewer's change and tests still open"
metadata:
  node_type: memory
  type: project
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-04T22:20:10.490Z
---

PR https://github.com/QwenLM/qwen-code/pull/10720 (fork dpc00/qwen-code, branch fix/ctrl-c-exit-warning-overflow). 2026-10-04: I replayed the 2 commits onto latest upstream (only Footer.tsx conflicted: kept upstream's executionSandbox block plus our statusRowCount check) and force-pushed with Donald's OK; now MERGEABLE, head 3bb93ee. Working copy: C:\Users\donal\tools\qwen_pr (partial clone, branch fix-rebased).

**Still open:** (1) DONE 2026-10-04 (commit 3e32d8d, shared helper statusLineWrappedRows; untested); (2) tests never run (needs full npm install, hundreds of MB, ask first); (3) check the 10 GitHub CI checks. My stray comment "C:/Program Files/Git/review" is on the PR (mangled /review, see [[feedback_git_bash_slash_args_mangled]]).

**Why:** Donald forgets things I do not tell him plainly and in sequence; he said "if you do things that way, I will forget".

**How to apply:** at each half-hour check, report this PR's state in one sentence until it is merged or closed. See [[reference_gh_status_board]].


**Rule learned 2026-10-04:** qwen-code's bot objects to rebase/force-push on an active PR (invalidates review comments; bots squash on merge). My force-push triggered the reminder. Only add normal commits to this PR; to resolve future conflicts merge upstream into the branch instead of rebasing. CI checks after the push: mostly pass/skipping, delay-automatic-review pending.
