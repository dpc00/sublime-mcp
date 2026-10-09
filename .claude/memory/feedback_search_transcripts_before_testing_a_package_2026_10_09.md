---
name: search-transcripts-before-testing-a-package-2026-10-09
description: 2026-10-09: I re-tested LSP, LSP-pyright and LSP-json that earlier sessions had already tested or used, because a handoff note said "no log trace"; search transcripts first and tell Donald what exists
metadata:
  type: feedback
---

**What happened:** the evening baton listed LSP-pyright and LSP-json as "no log trace". I tested them without searching the session transcripts. A transcript search afterwards found: LSP tested 2026-10-08 (portable 4215, install only, and it has a row in `.tested_packages.tsv` that I had seen and ignored); LSP-pyright probed on 2026-09-10 and described as "hover/definition/references verified" in the campaign log by then; LSP-basedpyright (same engine) fully tested 2026-10-01; LSP-json never exercised before today. All three were already installed and in daily use in his main Sublime (his own `User\LSP-pyright.sublime-settings`), which I also did not check first. Donald: "Incompetent boobery", after asking why we tested them a second time.

**Why:** the repo records (tsv, log, baton) are incomplete; the retained transcripts under `C:\Users\donal\.claude\projects\` are the real record ([[where-campaign-records-live]]).

**How to apply:**
- Before testing any package: grep the tsv, the log headings, AND the transcripts (`LSP-xyz` with `-o` and a bounded regex, counts per file first; use a subagent for the heavy ones). Tell Donald what exists before doing anything.
- Check whether the package is already installed in his main Sublime (`Installed Packages`, `Packages\User\<name>.sublime-settings`); if it is part of his setup, say so and ask whether a test is wanted.
- Do not trust "no log trace" in a baton note.
- Related: [[computer-use-keys-go-where-his-focus-is-2026-10-09]] (the focus problem that made me move the test to the portable).
