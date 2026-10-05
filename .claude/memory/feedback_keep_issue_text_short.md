---
name: keep-issue-text-short
description: "2026-10-03 a maintainer (Sainan, Pluto#40) said the issue would be more readable had it not been AI-written; keep issue bodies short and plain"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-03T17:03:11.178Z
---

On PlutoLang/Syntax-Highlighting#40 the maintainer replied that my issue "would've been so much more readable had you not used AI", and also questioned the diagnosis (said the `file_regex` came from Sublime's own Lua build and Pluto does not change error messages). I answered with a short factual reply, no argument about AI.

**Why:** long, formatted reports read as machine-written and invite dismissal; the finding itself was real (Pluto prefixes `syntax error:`), so the delivery was the weak part.

**How to apply:** future issues: title, 3-4 line repro, the exact output, one sentence on cause; no headings or bold, no side notes. Never argue back about AI authorship. Mark anything I did not test as untested. See [[feedback_one_issue_per_finding]] and [[feedback_plain_short_answers_no_menus]].
