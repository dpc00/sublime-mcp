---
name: wsl-st-running-2026-10-06
description: 2026-10-06 the old WSL Sublime (Linux build 4200) was started with the current sublime-mcp pinned to Python 3.8; ports 9530/9532 up; launch order, scripts and what was changed
metadata:
  type: project
---

2026-10-06 Donald: "you were supposed to be willing to use the WSL-ST" and "don't need the debugger package in that".

State after setup: the WSL ST is the old Linux build 4200 (`~/.local/sublime/sublime_text/sublime_text`, config `~/.config/sublime-text`, hosts 3.3 and 3.8 only). Its `MCP Commander` was a symlink to the repo, whose `.python-version` says 3.14, which build 4200 does not have, so nothing listened. Replaced the symlink with a real folder holding the CURRENT `sublime_mcp.py` and `lib/` copied from the repo plus a `.python-version` of `3.8` (same trick as the Windows 4200 copy). User settings already had `mcp_port 9532`, `http_port 9530`; both open from Windows after the fix. The Debugger package was MOVED (not deleted) to `~/removed_packages/Debugger`.

Launch order that worked (no "[WARN:COPY MODE]" title, window drew normally): stop the four computer-use helper processes (`computer-use-mcp.cmd` cmd.exe, its node.exe, `computer-use-mcp.exe`, `CopilotComputerUse.exe`), `wsl --shutdown`, then start the WSL ST with `DISPLAY=:0 WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir GDK_BACKEND=x11 LIBGL_ALWAYS_SOFTWARE=1 setsid nohup ./sublime_text`. Computer-use stays unavailable until Donald reconnects it with `/mcp` AFTER the WSL window is up. Scripts live in the session scratchpad (wsl_launch.sh, wsl_restart.sh, wsl_fix.sh); the PowerShell tool hangs on `wsl -e` calls that start the GUI, so run those with Start-Process or in the background. The shell guard blocks `~` in wsl commands: use `--cd /home/dpchitester` and script files.

**Why:** Linux-only packages and Linux path/shell assumptions cannot be tested on the Windows portables. **How to apply:** tell him before restarting WSL; the MCP server name is `sublime-mcp-wsl` (needs `/mcp` reconnect by Donald); keep its plugin copy in sync by copying `sublime_mcp.py` and `lib/` again after repo changes. Related: [[reference_wsl_sublime_install]], [[feedback_wslg_window_froze_keyboard]].
