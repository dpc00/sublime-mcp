# Agent Guide for debugger-mcp

Call `debugger_get_help` if you are unsure how to launch a session, set
breakpoints, or read stack/variable state.

Wraps Sublime Text's **Debugger** package (DAP). 102 MCP tools. MCP SSE on
port 9505; HTTP bridge on 9515 (`GET /mcp_tools` for the live catalog). Override
with `DEBUGGER_MCP_PORT` / `DEBUGGER_HTTP_PORT`.

## Prerequisite

Tools call `get_debugger()` internally. If the Debugger package is not
installed/enabled, or its UI has never been opened in this window, you get
`{"error": "Debugger package not loaded."}`. Call `debugger_open` first.

## Two tool families

1. **Hand-written DAP wrappers** — typed args, structured JSON. Prefer these:
   `debugger_get_state`, `debugger_control`, `debugger_toggle_breakpoint`,
   `debugger_get_variables`, `debugger_get_callstack`, `debugger_evaluate`,
   `debugger_set_breakpoints_for_file`, …
2. **ST command passthroughs** — `window.run_command("debugger", {action})`.
   Mostly `{"success": true}`. The real effect is ST UI. Use for opening the
   Debugger (`debugger_open`, `debugger_open_and_start`) or when you want the
   human to see a panel. Do not fire UI dialogs the user did not ask for
   (`debugger_settings`, `debugger_install_adapters`,
   `debugger_change_configuration`, `debugger_edit_configurations`,
   `debugger_example_projects`, `debugger_show_protocol`).

## Focus-independent tools use the selected thread/frame

You usually omit `session_id`. The Debugger tracks one active session with a
selected thread/frame. `debugger_evaluate`, `debugger_get_variables`, and
`debugger_get_callstack` use that selection (`thread_id` only to pick another
thread). Check `debugger_get_state` first: you need `is_paused: true` and a
non-null `active_frame` before evaluating or reading variables.

## Coordinates

`debugger_toggle_breakpoint` `line` is **1-based** (same as sublime-mcp, not
lsp-mcp).

## Workflow

```
1. debugger_open
2. debugger_toggle_breakpoint(file_path, line)     # 1-based line
   # or debugger_set_breakpoints_for_file(file_path, breakpoints=[{line: N}])
   #    — this REPLACES all breakpoints for that file
3. debugger_control(action="start", configuration_name="<launch config name>")
   # without configuration_name, action="start" only opens the Debugger UI
4. debugger_get_state                              # poll until is_paused
5. debugger_get_callstack
6. debugger_get_variables                          # omit variables_reference for top scope
7. debugger_evaluate(expression="some_var.field")
8. debugger_control(action="step_over"|"step_in"|"step_out"|"resume"|"pause"|"stop")
9. debugger_stop  or  debugger_terminate
```

## Breakpoints and variables

- `debugger_toggle_breakpoint(file_path, line)` — add/remove one source
  breakpoint. Not cursor-based.
- `debugger_set_breakpoints_for_file` — replace the whole set for that file.
- `debugger_clear_breakpoints` — all files.
- `debugger_set_function_breakpoints` / `debugger_set_data_breakpoints` are
  separate classes; they do not interact with source breakpoints.
- `debugger_get_variables` without `variables_reference` is the selected
  frame's top scope. Nested objects carry their own `variables_reference` —
  pass it back to expand children.

## Reverse debugging

`debugger_step_back` / `debugger_reverse_continue` only work if the adapter
supports reverse execution (most Python/Node adapters do not).

## Full tool list

`tools/list` (MCP) or `GET /mcp_tools` on port 9515. Do not rely on a static
enumeration.
