---
name: stino-menu-untitled-tabs-2026-10-07
description: 2026-10-07 Donald's unlogged account of Stino making ST misbehave (menu clicks opened untitled tabs); evidence lost, needs a clean reproduction before any report
metadata:
  type: project
---

2026-10-07: Donald says the Stino package (Robot-Will/Stino) caused Sublime to malfunction during an unattended run. When he returned, ST was up with two windows, one portable (he could not tell 4200 from 4215), and every click on a main menu opened a new "untitled" tab. A project recovery problem cut the session off, so nothing was logged, and the portables had already been cleaned, so no evidence remains on disk.

**Why:** he wants an intensive investigation and a report to Package Control, but only on evidence. Earlier Stino#539 was closed as 4215-only (see [[project-closed-4215-only-issues-2026-10-03]]).

**How to apply:** do not search the disks for remnants (he said they are gone). Static read of Stino (2026-10-07, repo Stino-Dev, last push 2023-01-21): ViewMonitor handlers use `stino` unguarded (None if plugin_loaded fails); PortListener and task threads are non-daemon and poll forever; Main.sublime-menu has no new_file command, so it does not explain the tabs. Next step is a clean reproduction (Stino alone, 4200 then 4215, click menus, watch console and tab count) only after Donald says to launch. Nothing goes to Package Control until he has seen the evidence. Stino is over 2 years stale, so [[feedback-skip-unmaintained-packages]] would normally skip it; this is his explicit exception.

**State at session end (2026-10-07):** the portable he saw on the right of the screen was 4215 (4200 was the wrong one to launch). Stino is NOT installed anywhere; one install attempt in 4215 had not landed. Donald hand-cleaned the 4215 portable after the malfunction (an "Arduino-like" package was part of it), so it holds only Package Control and MCP Commander. Limitcode messages.json was checked and is fine (standard format, nothing to report). I renamed the MCP servers to sublime-mcp-portable-4215 (port 9512), sublime-mcp-portable-4200 (9522) and sublime-mcp-wsl-4200 (9532) in .mcp.json, ~/.claude.json and three settings files; Donald says the names are still wrong and did not say what they should be, so ask him the names he wants before touching them again. Both portables (4200 pid 24036, 4215 pid 12988) were left running; he said leave 4200 alone. Donald was upset at too many questions and unrequested actions: do one small thing at a time and wait.
