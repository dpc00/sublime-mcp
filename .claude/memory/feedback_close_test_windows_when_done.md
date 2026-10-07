---
name: close-test-windows-when-done
description: 2026-10-06: Donald finds extra Sublime/test windows annoying ("windows galore"); close my test windows right after each test and quit the test instances when I stop
metadata:
  type: feedback
---

On 2026-10-06, after a long WSL audit run, Donald said the number of windows was annoying and that when I am through I should close the windows. He had closed all the test Sublime windows himself, which also dropped the sublime-mcp-wsl, portable and portable-4200 connections.

**Why:** every test left windows on his desktop (the WSL Sublime, my test windows, restored session windows after restarts, dialogs). Restarting an instance restores windows from its saved session, so closing views alone does not stop that.

**How to apply:**
- Close every test window and tab the moment its test is finished (by id, never by exclusion), and close all views before any restart so the session does not restore them.
- Keep at most one WSL Sublime window open while auditing (the MCP link needs a running instance); when I stop or hand back to Donald, quit that instance too (`pkill -x sublime_text` in WSL).
- Do not leave the 4200/4215 portables running unless a test needs them; when one drops its connection, ask Donald for `/mcp` reconnect with the exact server name instead of using the HTTP bridge ([[feedback_mcp_disconnect_notify_dont_bypass]]).
- Related: [[feedback_clean_portable_overlays_and_tabs]], [[project_wsl_st_running_2026_10_06]].
