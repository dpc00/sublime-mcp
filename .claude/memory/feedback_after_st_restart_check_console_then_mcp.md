---
name: after-st-restart-check-console-then-mcp
description: "after restarting ST, check the Python console to see whether plugins have finished loading, THEN test the MCP connection; MCP starts last"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-02T17:31:10.909Z
---

After any Sublime Text restart (portable 4215 or real), first read the console (`get_console_log` is not available until MCP is up, so use the HTTP bridge only if Donald allows, otherwise wait) to see whether the plugins have finished reloading. Only then test the MCP connection.

**Why:** 2026-10-02 Donald explained the MCP server starts after all the other plugins, so its startup is long; I asked him for `/mcp` too early. Related: [[feedback_test_mcp_before_asking_reconnect]], [[feedback_mcp_disconnect_notify_dont_bypass]].

**How to apply:** after a restart, wait (poll the process / give it a minute), then make one test call; ask for `/mcp` only if the call still errors after plugins have loaded.
