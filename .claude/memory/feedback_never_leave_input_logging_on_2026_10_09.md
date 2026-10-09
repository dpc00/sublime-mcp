---
name: never-leave-input-logging-on-2026-10-09
description: 2026-10-08 20:52 to 2026-10-09 about 00:55 I left sublime.log_input(True) on while hunting the Claude-tab freeze; Sublime printed every key and typed character Donald pressed into its console for about three hours
metadata:
  type: feedback
---

I enabled `sublime.log_input(True)` (and briefly `log_commands`) to find what selects a line in the Claude tab ([[ghostshell-phantom-selection-console-read-2026-10-08]]) and did not turn it off until 2026-10-09 around 00:55 (found when a console read showed `chr evt:` lines of Donald's own typing).

**What it exposes:** `key evt: <key>` and `chr evt: <character>` lines in Sublime's console for everything typed into Sublime. In memory only; not in sublime-mcp's capture buffer (checked: 0 entries); not on disk; a Sublime restart clears it. About a dozen typed characters reached my transcript in the last console read (harmless words).

**How to apply:** never switch on log_input or log_commands without writing the off-switch into the same step (e.g. a timer: `sublime.set_timeout(lambda: sublime.log_input(False), 120000)`), and turn it off the moment the diagnosis is over. Tell Donald when it is on. Prefer capturing one event at a time over leaving logging running. The console read from sublime-mcp also prints these lines, so any long console tail may contain his typing: keep tails short while logging is on.
