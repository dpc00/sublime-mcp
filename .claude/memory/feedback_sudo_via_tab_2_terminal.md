---
name: sudo-via-tab-2-terminal
description: For WSL sudo installs, send the command into Donald's tab-2 WSL terminal tab myself with ai_terminal_send_string; do not hand him commands to run
metadata:
  type: feedback
---

2026-10-06 Donald: "sudo just requires a password" and, when I offered him the command to run, "you put the command into Tab 2. Do it yourself."

**Why:** the main Sublime window (mcp__sublime-mcp, build 4215) has the Claude tab first and a WSL terminal tab second (title like `dpchitester@HPLaptop1: /mnt/c/Users/donal/projects`, an ai_terminal view, id 142 that session). He keeps sudo warm there, so installs run without a password prompt; if it does ask, he types the password in that tab.

**How to apply:** find the terminal view by title, never the Claude tab, check `settings().get('ai_terminal_view')` and that it is not the Claude tab's id, then `view.run_command('ai_terminal_send_string', {'string': 'sudo apt-get install -y <pkg>\n'})` via eval_python on mcp__sublime-mcp. Read the tail of the view text to confirm. Installed that way 2026-10-06: x11-utils (xprop). Related: [[project_wsl_st_running_2026_10_06]].
