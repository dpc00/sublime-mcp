---
name: feedback-console-log-for-tracebacks
description: when testing packages in the portable ST, read the console log (bridge get_console_log) for tracebacks; swapping sys.stderr misses exceptions raised inside ST event handlers
metadata:
  type: feedback
---

Swapping `sys.stderr` around a test only catches exceptions raised in the same call chain. Tracebacks from ST event listeners (`on_modified`, `on_activated`, async handlers, timers) are printed by ST itself and never reach my StringIO. I wrongly concluded "no bug" for Text Highlighter (kdnk/sublime_text_highlighter#7) until `POST http://127.0.0.1:9510/get_console_log {"tail": 200}` showed the AttributeError.

**Why:** the console log is the only place these show up; the buffer is short, so old tracebacks scroll away.

**How to apply:** after every bridge test that exercises listeners/timers, immediately fetch the console log tail and grep for `Traceback`. Related: [[reference-portable-st-4215]]. Also for syntax packages, `w.run_command("run_syntax_tests")` on the open `syntax_test_*` file prints results to the `exec` output panel.
