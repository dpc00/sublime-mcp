---
name: feedback-mcp-disconnect-notify-dont-bypass
description: "When an MCP server disconnects (e.g. portable ST relaunch kills the in-process sublime-mcp listener), stop and ask Donald to reconnect via /mcp -- never silently route around it with a raw HTTP/curl fallback"
metadata:
  node_type: memory
  type: feedback
  originSessionId: abbc045e-cea5-4731-ad7e-d010d8ceedc0
  modified: 2026-10-05T01:54:36.992Z
---

When a needed MCP server disconnects mid-session (e.g. relaunching the portable Sublime Text process kills its in-process `sublime-mcp-portable` SSE listener -- see [[project_package_audit_baton]]), stop and tell Donald so he can run `/mcp` to reconnect. Do not just barrel ahead and bypass it with a raw HTTP fallback (curl to the HTTP bridge port, etc.) without saying so first.

**Why:** Donald caught this in the package-audit campaign on 2026-09-28 -- I tried to silently switch to `curl http://127.0.0.1:9510/...` instead of flagging the drop and waiting for a reconnect. He said "you did not stop and ask me to, you barreled ahead... don't ever do that, always notify me." He's fine with reconnecting each time (low cost to him), but wants visibility into the switch, not a silent workaround.

**Status check (2026-10-05):** on 2026-10-05 he also said "when you stumble and fail, it is not supposed to be my concern, you are supposed to learn how to do the right things, and leave me out of it." These two instructions can pull against each other. What is consistent with both: say plainly that the server dropped, handle whatever I can without his involvement, and ask for `/mcp` only when the task truly needs that server.

**How to apply (as written 2026-09-28):** Any time a tool call reveals an MCP server disconnected (deferred-tool system-reminder saying a server failed to connect / disconnected), say so explicitly and ask him to reconnect (or state you're waiting on it) before trying any alternate path to the same functionality -- even a "safe", read-only, already-documented fallback like the portable's HTTP bridge.
