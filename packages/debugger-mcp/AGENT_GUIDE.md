# Agent Guide for debugger-mcp

This document teaches AI agents how to use debugger-mcp tools correctly.
Call `debugger_get_help` first if you're unsure how to launch a session,
set breakpoints, or read stack/variable state.

debugger-mcp wraps Sublime Text's **Debugger** package (a DAP — Debug
Adapter Protocol — front end) and exposes it as ~101 MCP tools. It serves
MCP/SSE on port 9505 and a plain HTTP bridge on port 9515 (used by
node-proxy / python-proxy, not by direct SSE clients).

## Prerequisite: the Debugger package must be loaded and open

Almost every tool starts by calling `get_debugger()` internally, which
looks for a running or open instance of the **Debugger** ST package. If
it's not installed/enabled, or no debugger UI has ever been opened in the
current window, tools return `{"error": "Debugger package not loaded."}`.
Call `debugger_open` (or `debugger_open_and_start`) first if you get that
error.

## Two tool families

1. **DAP session tools** (hand-written wrappers around the Debugger
   package's Python API) — `debugger_get_state`, `debugger_evaluate`,
   `debugger_get_variables`, `debugger_get_callstack`,
   `debugger_set_breakpoints_for_file`, etc. These take real typed
   arguments and return structured JSON.
2. **ST command passthroughs** (`debugger_open`, `debugger_start`,
   `debugger_step_over`, `debugger_continue`, `debugger_stop`, ...) — thin
   wrappers around `window.run_command("debugger", {"action": ...})`.
   These mostly take no arguments (or just `configuration_name` for
   `debugger_start`) and return `{"success": true, "message": "..."}`
   rather than structured state — call `debugger_get_state` afterward if
   you need to see the result.

Use your MCP client's `tools/list` (or `GET /mcp_tools` on the HTTP bridge,
port 9515) to see every registered tool name with its live description and
JSON schema — more reliable than guessing from tool-name patterns.

## Critical mental model: "focus-independent" tools operate on the active thread/frame

You do **not** need to pass a `session_id` to most tools. The Debugger
package tracks one active session with a `selected_thread` and
`selected_frame`, and tools like `debugger_evaluate`, `debugger_get_variables`,
and `debugger_get_callstack` operate on whatever is currently selected —
pass `thread_id` only if you need a *different* thread than the selected
one. This is simpler than raw DAP, but it means these tools give
misleading results if called while nothing is paused — check
`debugger_get_state` first and confirm `is_paused: true` with a non-null
`active_frame` before evaluating expressions or reading variables.

## Common workflow

```
1. debugger_open                                   (open the UI if not already)
2. debugger_set_breakpoints_for_file                (file_path, breakpoints=[{line: N}])
3. debugger_start   or  debugger_open_and_start     (configuration_name optional)
4. debugger_get_state                               (poll — check is_paused)
   ... once paused ...
5. debugger_get_callstack                           (see where execution stopped)
6. debugger_get_variables                           (variables_reference optional — omit for top-level scope)
7. debugger_evaluate                                (expression="some_var.field")
8. debugger_step_over / debugger_step_in / debugger_continue
9. debugger_stop  or  debugger_terminate
```

## Breakpoints

- `debugger_set_breakpoints_for_file` **replaces** all breakpoints for
  that file — it is not additive. Pass the full desired set every time.
- `debugger_toggle_breakpoint` toggles a single breakpoint at the cursor
  in the active view (ST command, no `file_path`/`line` args — position
  comes from the current selection).
- `debugger_clear_breakpoints` removes everything, across all files.
- `debugger_set_function_breakpoints` / `debugger_set_data_breakpoints`
  are separate breakpoint classes (by function name / by variable
  read-write) — they don't interact with source breakpoints.

## Variables and nested structures

`debugger_get_variables` without `variables_reference` returns the
top-level scope of the selected frame. Each variable in the response may
carry its own `variables_reference` (a DAP handle) — pass that back in as
`variables_reference` to expand nested fields/children (objects, arrays).
This is a drill-down pattern, not a single flat dump.

## Reverse debugging

`debugger_step_back` / `debugger_reverse_continue` only work if the
active adapter supports reverse execution (most don't — e.g. standard
Python/Node debuggers won't). Expect an adapter-level error otherwise.

## Full tool list

Use `tools/list` (MCP) or `GET /mcp_tools` (HTTP bridge) for the complete,
current set of ~101 tools with descriptions and JSON schemas — this guide
intentionally doesn't enumerate every tool since that list is always
available live and can drift from a static doc.
