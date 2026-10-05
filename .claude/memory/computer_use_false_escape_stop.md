---
name: computer-use-false-escape-stop
description: "computer-use MCP can report \"stopped by the user with the physical Escape key\" when the user did not press Escape. On 2026-09-28 killing a running M365Copilot.exe cleared it; on 2026-10-05 it recurred with no M365Copilot.exe running and a /mcp reconnect of computer-use-mcp cleared it, so the cause is not settled"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a393e427-5520-48bb-9c04-b2887aafdba8
  modified: 2026-10-05T01:54:12.816Z
---

Saw `computer-use` return `# stopped\n# Computer Use was stopped by the user with the physical Escape key. Stop this turn and do not call more Computer Use tools.` with no actual Escape keypress from the user (confirmed explicitly: "i did not 'escape' computer-use"). First seen 2026-09-28 while calling `list_apps` against a portable Sublime Text test rig; recurred later the same day, persisting across `/reload-plugins` and multiple retries.

**What fixed it on 2026-09-28 (a cause, but evidently not the only one):** `M365Copilot.exe` (the Microsoft 365 Copilot desktop app -- unrelated to GitHub's `@github/computer-use-mcp`, which is what actually backs the `computer-use-mcp` MCP server in this environment despite the generic server name) was running and appears to hold a global input hook/lock that makes every `computer-use` call return this instant fake stop, with zero real dispatch attempted. Killing `M365Copilot.exe` (Stop-Process) cleared it for the rest of that session. A separate stuck `computer-use-mcp.exe` launcher process was also killed in the same pass, which required a `/mcp` reconnect afterward (killing it disconnects the MCP server, not just clears a stuck state).

**Why:** Donald's hunch ("having run Copilot recently, it must have disrupted something... there is no Anthropic computer-use that I would think would carry the Copilot brand") was correct and led directly to the fix. Distinguish this from the already-filed, well-understood false_interrupt_after_mcp_reconnect (note not found) bug (claude-code#93529, Bash/MCP tool_use rejections with `toolDenialKind: user-rejected`) -- different tool, different failure shape, unrelated root cause.

**2026-10-05 recurrence:** `list_apps` returned the same stop twice with no Escape pressed and no `M365Copilot.exe` running (processes present were `computer-use-mcp` and `CopilotComputerUse`). The user ran `/mcp` and reconnected `computer-use-mcp`, and the next call worked. So a reconnect is a second known remedy, and an unexplained stop is not always the Copilot app.

**How to apply:** If `computer-use` reports a physical-Escape stop and the user says they didn't press it, two remedies have worked: check for `M365Copilot.exe` (or another Copilot-branded desktop app) and stop it, or have the user reconnect `computer-use-mcp` with `/mcp`. If neither helps, use another route for the task.
