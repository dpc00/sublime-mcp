---
name: clean-portable-overlays-and-tabs
description: "After each package test, leave both portable STs clean: close tabs AND any open overlay/quick panel (e.g. Flake8Lint error list), and verify with a screenshot"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-04T15:54:02.714Z
---

2026-10-04 Donald twice complained the portables were "dirty with unclosed tab leftovers"; the second time he pointed at a leftover "mini-panel" (a Flake8 Lint quick panel / overlay with "D100: Missing docstring in public module") and a PHP test buffer left in 4215.

**Why:** he watches the portable windows on screen; my tab-only cleanup missed overlays, and the loops that restart a portable keep restoring old tabs from its session.

**How to apply:** at the end of every package test run `hide_overlay` + `hide_panel` + close all views (set_scratch then close) + clear project data on BOTH portables (4200 bridge 9520, 4215 bridge 9510; script `scratchpad\t_clean4200.py <port>`), recycle my test files, then take one screenshot to confirm. See [[feedback_end_test_agent_tabs]] and [[feedback_junk_tabs_other_group]].
