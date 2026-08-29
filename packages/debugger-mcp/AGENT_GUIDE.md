# Agent Guide for debugger-mcp

Call `debugger_get_help` if you are unsure how to launch a session, set
breakpoints, or read stack/variable state.

Wraps Sublime Text's **Debugger** package (DAP). Seven tools are advertised by
default; 104 are available through discovery and batch. MCP SSE on
port 9505; HTTP bridge on 9515 (`GET /mcp_tools` for the live catalog). Override
via `debugger-mcp.sublime-settings` (`"mcp_port"` / `"http_port"`).

## Prerequisite

Tools call `get_debugger()` internally. If the Debugger package is not
installed/enabled, or its UI has never been opened in this window, you get
`{"error": "Debugger package not loaded."}`. Call `debugger_open` first.

## Two tool families

The focused surface is `debugger_get_help`, `debugger_batch`,
`debugger_discover_tools`, `debugger_open`, `debugger_get_state`,
`debugger_control`, and `debugger_toggle_breakpoint`. Search for every other
capability with `debugger_discover_tools(query=...)`, then invoke its exact
name through `debugger_batch(calls=[{"tool": ..., "args": {...}}])`.

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

## Debugging Sublime Text plugins

Prefer Debugger's `sublime` adapter over attaching debugpy to the live Sublime
Text process. The adapter launches a separate `Sublime Text (Debug)` instance
with its own data directory. A breakpoint in plugin code can suspend that
instance without freezing the editor window that hosts debugger-mcp and the AI
client.

First confirm the adapter and project configuration are visible:

```
debugger_open
debugger_discover_tools(query="adapters configurations")
debugger_batch(calls=[
  {"tool": "debugger_get_adapters", "args": {}},
  {"tool": "debugger_get_configurations", "args": {}}
])
```

`debugger_get_adapters` should contain `{"name": "sublime"}`. If it does not,
the user must install that adapter through Sublime Debugger. Do not open the
adapter installation UI or download an adapter without the user's consent.

Add a configuration to the project's `.sublime-project` file:

```json
{
  "folders": [{ "path": "." }],
  "debugger_configurations": [
    {
      "name": "Plugin (isolated Sublime)",
      "type": "sublime",
      "request": "launch",
      "entry": "PackageName.plugin_module",
      "args": ["-n", "${project_path}/Project.sublime-project"],
      "linked_packages": [
        "${project_path}",
        "${packages}/User/Preferences.sublime-settings"
      ]
    }
  ]
}
```

Important details:

- `linked_packages` is required. Linking `${project_path}` makes the repository
  available as a package named after its directory.
- `entry` is the importable plugin module, for example
  `GhostShell.ai_terminal`. It enables Debugger's reload-on-save support and is
  optional if reload support is not wanted.
- Link only the User files the test instance actually needs. Linking all of
  `Packages/User` can make the supposedly isolated environment noisy and hard
  to reproduce.
- Opening a `.sublime-project` that contains the configuration is necessary;
  merely creating the file does not add it to an already-open different
  project.
- Starting the configuration visibly launches another Sublime instance. Treat
  that as a user-visible action and obtain consent when the user did not
  explicitly request a launch.
- Avoid attaching to or pausing the production Sublime plugin host unless the
  user specifically accepts the risk of freezing that editor and disrupting
  its MCP connections.

After opening the project, use the normal workflow above with
`configuration_name="Plugin (isolated Sublime)"`. Set breakpoints against the
source file in the linked repository; the isolated package is a symlink to the
same files.

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

Use `debugger_discover_tools`; `tools/list` with `surface="all"` and
`GET /mcp_tools?surface=all` expose the raw catalog for diagnostics. Do not rely
on a static enumeration.
