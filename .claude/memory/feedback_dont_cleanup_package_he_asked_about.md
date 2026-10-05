---
name: dont-cleanup-package-he-asked-about
description: "when Donald asks questions about a package under test, keep it installed until he says he is done; routine cleanup deleted LSP-basedpyright right after he asked about it"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-02T05:45:38.771Z
---

On 2026-10-01 Donald asked what LSP-basedpyright is, how it differs from the LSP-pyright he uses, and what the extra checks would do for him. My answers were buried in tool output, and then I ran my usual post-test cleanup and deleted the ~10-minute install. He was angry ("you spent all that time, didn't answer my question then deleted an install that took how long?", "that is a bug report to Anthropic").

**Why:** a question about the package means he may want to try it; the cleanup was my routine, not his request, and the install is expensive to redo.

**How to apply:** if Donald asks anything about the package being tested, answer it first as a plain, visible message and do NOT remove the package, its server or its test project until he says he is finished or asks to move on. Put the answer before further tool calls. Related: [[feedback-plain-short-answers-no-menus]].
