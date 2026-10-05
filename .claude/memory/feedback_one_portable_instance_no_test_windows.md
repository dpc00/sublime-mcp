---
name: one-portable-instance-no-test-windows
description: "Run at most one portable ST instance, and don't run window-opening test suites (SublimeLinter's UnitTesting) without warning; flashing windows scare Donald"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 20d54abe-2f32-4daf-93ee-a1da9540a1db
  modified: 2026-10-05T01:53:10.678Z
---

On 2026-09-29 Donald saw a second portable ST window flashing and said "don't run more than one portable ST instance, that scares me." It was SublimeLinter's own test suite (its setUpClass runs `new_window`, opens scratch views, closes the window) run through UnitTesting inside the single portable process, but to him it looked like a second instance.

**Why:** unexpected windows appearing on his desktop are alarming; he can't tell a sandboxed test from something wrong.

**How to apply:** at the time only the 4215 portable existed, and the concern was a second copy of it, so keep one `D:\st_portable_4215\sublime_text.exe` process (check with Get-Process before launching). The older 4200 portable was added on 2026-10-03 as a separate build, and from then on both portables ran side by side with no complaint; the worry is windows he does not expect, not the number of portable builds. Before running UnitTesting suites that open windows, tell him first, and prefer tests that don't need windows (the small linter suites like SublimeLinter-php only create a stub `sublime.View(0)`, no windows). See [[reference_portable_st_4215]] and [[feedback_junk_tabs_other_group]].
