---
name: test-mcp-before-asking-reconnect
description: "After a portable relaunch, make a test call to sublime-mcp-portable before asking Donald to /mcp reconnect; it usually reconnects on its own"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 20d54abe-2f32-4daf-93ee-a1da9540a1db
  modified: 2026-09-29T15:19:16.241Z
---

After relaunching the portable ST, the MCP connection often comes back by itself (blue checkmark). On 2026-09-29 I asked for a reconnect without testing and the very next call worked.

**Why:** Donald's time and Enter key are limited; an unnecessary reconnect is a wasted action. He said so plainly.

**How to apply:** after relaunch, wait a few seconds and make a cheap call (get_console_log via batch). Only if it errors, ask for `/mcp`. This refines [[feedback_mcp_disconnect_notify_dont_bypass]]: still don't silently use the raw HTTP bridge when the MCP is really down, but test first. Also [[feedback_reduce_permission_prompts]].
