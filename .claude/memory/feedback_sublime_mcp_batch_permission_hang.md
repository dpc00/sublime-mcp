---
name: feedback-sublime-mcp-batch-permission-hang
description: "sublime-mcp calls that time out: on 2026-09-08 the cause was a wedged plugin-host main thread (every call failed, even get_help), not batch logic; a silent permission prompt was suggested by the user but not reproduced"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6baf5f30-f111-4757-8168-5593e86f5789
  modified: 2026-10-05T01:51:57.844Z
---

Tested directly (2026-09-08): `batch` with one bad call (unknown tool name) mixed with one good call returns `{"ok": true, ...}` for the good one and `{"error": "unknown tool: ..."}` for the bad one — both slots present, nothing dropped, matching its own documented contract. Running each call standalone afterward gave identical results. So a plain bad/unknown call does NOT make `batch` silently quit or swallow other results.

What actually caused the earlier "everything times out" episode: the Sublime plugin_host's main thread got wedged (alive, listening, burning CPU, but unresponsive to every request type — including trivial ones like `get_help` that touch no permissions or main-thread state). Root cause was most likely my own test cleanup calls that closed windows/views outside the normal command path (e.g. `_close_ide_diff` / `close_window` called directly via `eval_python` rather than through the plugin's own commands). Restarting Sublime Text fixed it immediately.

**Why:** User asserted batch silently quits on a permission failure rather than asking; direct testing (bad-tool-name case) didn't reproduce that — it degraded gracefully instead. Couldn't test an actual Claude-Code-harness permission denial from inside the session (that gate is the CLI prompting the user, not something sublime-mcp enforces internally).

**How to apply:** If a `sublime-mcp` call (batch or standalone) times out, a quick check is whether ALL calls fail the same way (including no-op ones like `get_help`/`discover_tools`). When they did on 2026-09-08, the plugin_host's main thread was wedged and restarting Sublime Text fixed it. A timeout where other calls still work points elsewhere (for example a permission prompt waiting for the user, which the user has seen but I could not reproduce from inside a session). Closing windows/views directly through `eval_python` was the *probable* trigger of the wedge on 2026-09-08; that was not proven.
