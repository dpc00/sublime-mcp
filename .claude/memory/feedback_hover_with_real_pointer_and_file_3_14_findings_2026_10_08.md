---
name: hover-with-real-pointer-and-file-3-14-findings-2026-10-08
description: 2026-10-08 how to test hover features (SetCursorPos moves the real pointer, computer-use clicks do not reach the editor), and Donald's ruling that a Python 3.10+/3.14-only failure IS filed so the maintainer has a warning
metadata:
  type: feedback
---

**How to hover:** a background `computer-use` click never moved the caret or hovered in Sublime, and `run_command` cannot fire `on_hover` / `on_text_command` listeners. What works: move the REAL pointer with `user32.SetCursorPos(x, y)` over the symbol (screen x/y = window rect left/top + pixel position in a `mcp__screenshot__screenshot_window` image; nudge by 2 px to make Windows send a mouse-move), wait about 2 s, then `screenshot_region`. Put test files in a second layout group (`set_layout` rows [0,0.7,1] + `move_sheets_to_group`) so the Claude tab stays in front for his permission prompts. A language server (LSP-pyright) has its own hover popup that hides other packages' popups: test hover packages on a language with no server (a C file). sublime-mcp has no hover or real-pointer tool: that is a gap to report.

**What Donald said (2026-10-08, on HoverDocs):** "You don't file that? That's ridiculous. Now author has no warning." Then: "I didn't write a rule, you made that up." Checked: his typed message of 2026-10-03 (session fcb54aa2, line 40732) says only: "i don't think you should report 'won't start on 4215', because that is not a bug. That is lag behind the time. At any rate you should test on any version that they require." That is about plain won't-start reports, it is not a rule about defects with a visible cause. I stretched it to cover HoverDocs's float-to-show_popup TypeError and did not file it: my mistake, not his rule. File any defect whose cause is visible in the package code, even if it only shows on the 3.14 host; the 4215-lag wording applies only to bare 'won't start / won't import on 4215' reports.

**Consequence not yet done:** Evernote#225 (SyntaxWarnings) was closed by me the same day under the old rule; Alphanumeric Markdown Footnote (test.py ModuleNotFoundError on 3.14) was not filed. Ask/decide whether to reopen/file.

