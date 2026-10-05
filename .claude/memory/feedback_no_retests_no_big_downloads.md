---
name: no-retests-no-big-downloads
description: "2026-10-03 Donald is on Xfinity Internet Essentials, worried about data caps; does not want to retest on request; no big downloads without asking"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-05T01:55:30.065Z
---

Donald hears an email chime constantly and says there are far too many maintainer requests for retests; he does not want to retest anything, especially if it needs "enormous downloads" (Lean toolchain about 300 MB, LTeX server about 260 MB, TypeScript native, WSL tools). He is on Xfinity Internet Essentials and fears throttling, cut-off or extra charges (I could not confirm Xfinity's rules for his plan; told him to check his usage page).

**Why:** bandwidth worry plus notification fatigue. This overrides the older "install free tools, only cost is a barrier" rule for anything large.

**How to apply:**
- Ask before any download over about 50 MB (toolchains, language servers, WSL images); otherwise do not skip the package: put it on the deferred list (`C:\Users\donal\data\st_packages\deferred_big_installs.md`) to be done when he says it is off hours (his later rule the same day, see [[feedback_defer_big_installs_dont_skip]]), and mention in the log that it needs a big download. Reuse what is already cached in `C:\Users\donal\tools` and the npm cache; never download the same thing twice.
- Do not retest just because a maintainer asks. Retest only when it is cheap (no new download) and worth it; otherwise answer from what is already known and keep comments short.
- Do not ask him to retest or to decide; fewer notification mails (short comments, no pinging).
- If asked about bandwidth: counters so far were small (Wi-Fi counter 1.63 GB received since 2026-09-30 boot, a lower bound); a day of my downloads is about 1 GB at most.

Related: [[feedback_never_skip_for_missing_prereqs]] (now limited by this), [[feedback_recycle_bin_and_keep_big_tools]], [[feedback_keep_issue_text_short]].
