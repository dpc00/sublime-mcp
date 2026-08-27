---
name: sublime-debugger
description: Control Sublime Text's Debugger package through debugger-mcp. Use for launching or controlling debug sessions, setting breakpoints, inspecting paused state, variables, call stacks, expressions, memory, or DAP behavior in Sublime Text.
---

# Sublime Debugger

Call `debugger_get_help` when a workflow or argument is unclear. Call
`debugger_open` if the Debugger package has not initialized in the window.

Use the seven visible workflow tools directly. For every other operation, call
`debugger_discover_tools` with a capability-oriented query, inspect the returned
schema, then call the exact result through `debugger_batch`. Combine independent
reads in one batch; keep state-changing debug controls sequential.

Breakpoint lines are 1-based. Before reading variables, call stacks, or
evaluating expressions, use `debugger_get_state` and require a paused session
with an active frame. Stop sessions when finished.
