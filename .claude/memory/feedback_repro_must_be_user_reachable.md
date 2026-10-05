---
name: feedback-repro-must-be-user-reachable
description: bug repros must be reachable through real user actions; emptying internal state (e.g. a module's _history) to trigger an exception got SublimeText/SwitchWindow#5 closed as not planned by deathaxe
metadata:
  type: feedback
---

2026-09-26: I filed SublimeText/SwitchWindow#5 ("IndexError when history is empty") after forcing `_history` to `[]` from the test harness. deathaxe closed it as not planned: "manipulating state in inadequate ways can produce all sorts of theoretically possible invalid states"; in real use an empty window always gets a scratch view and `on_activated` fires, so the state never occurs. My claim "window without tabs" was wrong.

**Why:** a finding is only worth filing if a normal user action reaches it. Maintainers (and Package Control/ST core people) will dismiss contrived repros and it costs Donald's credibility.

**How to apply:** before filing, ask "what real sequence of UI actions produces this state?" and reproduce THAT (open real files, real layouts, real settings, real commands). If I had to poke internals to get the exception, don't file (or say plainly that it is defensive-hardening only). Check listener/lifecycle assumptions (e.g. on_activated always fires for a new window). Related: [[feedback-install-package-skips-libraries]], [[feedback-one-issue-per-finding]].

**Second example (2026-10-04):** braver/ColorHints#12 claimed a 'Show Color Hints' sidebar entry crashed; the package ships no such entry (only the palette command 'Color Hint', which works), I had built the failing call myself, braver closed it NOT_PLANNED and was right. Before filing, find the entry point in the package's own menu/commands/keymap files and use exactly that.
