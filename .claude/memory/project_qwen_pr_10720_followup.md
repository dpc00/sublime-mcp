---
name: qwen-pr-10720-followup
description: "CLOSED 2026-10-05 at Donald's request: he wants Qwen out of his life; PR #10720 closed, CLI removed, working copy recycled. Do not work on Qwen or mention it in checks"
metadata:
  type: project
---

**Final state (2026-10-05):** Donald said "I want to get rid of qwen from my life" and approved "all of it". Done that day: PR https://github.com/QwenLM/qwen-code/pull/10720 closed with a short note ("I will not be continuing work on it. Thank you for the reviews, and sorry for the noise."); global npm `@qwen-code/qwen-code` 0.23.0 uninstalled; the standalone install `%LOCALAPPDATA%\qwen-code` and the working copy `C:\Users\donal\tools\qwen_pr` (288 MB) sent to the Recycle Bin; the half-hour check no longer looks at Qwen.

**Why:** the qwen-code review bot (qwen3.8-max) kept producing new findings every round (round 3 on 2026-10-05 had 10, two critical, among them 8 `Footer.test.tsx` tests broken by my untested commit 3e32d8d), Donald found the volume overwhelming, and fixing needed a full npm install of hundreds of MB.

**Not removed (he did not list them, so ask before touching):** the config/history folder `C:\Users\donal\.qwen`, the fork `dpc00/qwen-code` on GitHub, and the Qwen mentions in older notes. Earlier history: conflict fixed 2026-10-04 by rebase and force-push, which the repo bot objected to ([[feedback_git_bash_slash_args_mangled]] for the mangled `/review` comment).

**How to apply:** never reopen the PR, never reinstall Qwen, never mention it in progress reports; if Qwen mail arrives, ignore it. See [[feedback_dont_hand_technical_decisions_to_donald]] and [[feedback_no_retests_no_big_downloads]].
