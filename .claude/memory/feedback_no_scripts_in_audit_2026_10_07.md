---
name: no-scripts-in-audit-2026-10-07
description: 2026-10-07 Donald: the audit exists to find sublime-mcp weaknesses; use only sublime-mcp's own tools, no scripts, no side channels
metadata:
  type: feedback
---

2026-10-07, Donald: "Dont use ANY scripts." and then: "This audit thing is to find Sublime-mcp weaknesses. That shouldn't involve ANY scripts." My first reading (use computer-use instead of scripts) was wrong.

**Why:** the point of the audit is to see where sublime-mcp falls short when an agent uses Sublime like a user. Scripts (eval_python code, PowerShell/HTTP helpers, install/remove/test scripts) bypass sublime-mcp and hide its weaknesses.

**How to apply:** drive Sublime only with sublime-mcp's own tools (run_command, window/view tools, etc.), installing through the palette Install Package picker as a user does ([[audit-installs-must-follow-user-flow-2026-10-07]]). Native dialogs still go through computer-use ([[always-computer-use-for-dialogs-2026-10-07]]). When sublime-mcp cannot do something a user can, do NOT work around it with a script; record it as a sublime-mcp weakness and tell Donald. No eval_python, no HTTP calls to the bridge, no scripts of any kind.
