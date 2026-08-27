# sublime-mcp — Agent Context

MCP servers that expose a running Sublime Text 4 instance to AI agents.

## Critical assumption

Plugin edits in this repo are **not live** in Sublime Text until the files
are in ST's `Packages/` directory (this repo is usually a symlink target).
If something isn't working, check that the plugin loaded before debugging
the code.

## The three MCPs

Independent ST plugins. Connect to the subset you need.

| MCP            | Plugin dir                 | MCP SSE                         | HTTP bridge                     | Tools                          |
| -------------- | -------------------------- | ------------------------------- | ------------------------------- | ------------------------------ |
| **sublime-mcp**  | `packages/st-plugin`     | 9502 (Win) / 9503 (macOS/Linux) | 9500 (Win) / 9501 (macOS/Linux) | 7 default, 215 discoverable    |
| **debugger-mcp** | `packages/debugger-mcp`  | 9505                            | 9515                            | 7 default / 104 total          |
| **lsp-mcp**      | `packages/lsp-mcp`       | 9506                            | 9516                            | 7 default / 125 total          |

Ports are configured per-plugin via `<name>.sublime-settings` (`"mcp_port"` /
`"http_port"`), overridable in `Packages/User/`. The proxy → HTTP bridge URL
is the one remaining env var: `SUBLIME_MCP_BASE`.

Guides (also served by `get_help` / `debugger_get_help` / `lsp_get_help`):
`packages/st-plugin/AGENT_GUIDE.md`, `packages/debugger-mcp/AGENT_GUIDE.md`,
`packages/lsp-mcp/AGENT_GUIDE.md`.

**Coordinates:** sublime-mcp and `debugger_toggle_breakpoint` are **1-based**.
lsp-mcp hand-written wrappers are **0-based**. Convert when crossing
(`lsp_line = st_line - 1`).

## Connecting

### Option A — bundled proxy (sublime-mcp HTTP bridge)

```bash
cd packages/python-proxy && pip install . && sublime-mcp
# or
cd packages/node-proxy && npm install . && npx sublime-mcp
```

Defaults to `http://127.0.0.1:9500` on Windows, `:9501` on macOS/Linux. If
the proxy runs in WSL against Windows ST, set
`SUBLIME_MCP_BASE=http://127.0.0.1:9500` (or the Windows host IP).

The bundled proxies do **not** speak to debugger-mcp or lsp-mcp. Point an
SSE client at those ports separately.

### Option B — MCP SSE directly

```json
{
  "mcpServers": {
    "sublime-mcp":  { "type": "sse", "url": "http://127.0.0.1:9502/sse" },
    "debugger-mcp": { "type": "sse", "url": "http://127.0.0.1:9505/sse" },
    "lsp-mcp":      { "type": "sse", "url": "http://127.0.0.1:9506/sse" }
  }
}
```

Use `:9503` for sublime-mcp SSE on macOS/Linux. HTTP bridges also serve
`GET /mcp_tools`.

## How to use the three together

Workflow is *orient → navigate → edit → verify → (debug) → confirm*. Each
MCP owns one leg.

| You want…                                      | Use               | Tool |
| ---------------------------------------------- | ----------------- | ---- |
| What the user is looking at                    | sublime-mcp       | `get_active_file` / `get_cursor_context` (live buffer, not disk) |
| Symbol def / refs / impl                       | lsp-mcp           | `lsp_goto_definition`, `lsp_find_references`, `lsp_get_implementation` |
| Type, signature, docstring                     | lsp-mcp           | `lsp_hover_info` |
| What's broken                                  | lsp-mcp           | `lsp_get_diagnostics` |
| Edit a file ST has open                        | sublime-mcp       | `str_replace_based_edit_tool` then `save_file` |
| Edit a file ST does not have open              | sublime-mcp       | `open_file` then edit the buffer |
| Rename a symbol                                | lsp-mcp           | `lsp_rename_symbol` **then** `lsp_apply_workspace_edit` |
| Quick-fix the LSP offered                      | lsp-mcp           | `lsp_get_code_actions` then apply |
| Step a failing test                            | debugger-mcp      | breakpoints + `debugger_control` |
| Memory / disassembly                           | debugger-mcp      | `debugger_read_memory`, `debugger_disassemble` |
| Run a build / test                             | **your shell**    | never ST `exec` / `run_build` |

### Default to sublime-mcp

Read, edit, save, close, find, navigate, and open paths (inside or outside
the workspace) through sublime-mcp. Fall back to host filesystem tools only
when ST or the HTTP/SSE bridge is down (frozen, crashed, plugin failed to
load, connection refused). Outside-workspace is not a fallback trigger —
`open_file` opens any path.

Why the live buffer, not a disk write:

- The user sees the edit, gutter diff, and a short highlight.
- Ctrl+Z undoes it. A silent disk overwrite has no ST undo.
- Dirty/save/close are real steps the user can see.
- No two-sources-of-truth with a stale ST buffer vs disk.

If you did write disk behind ST's back, `revert_file` (or reopen) so the
buffer resyncs.

### Never `run_command` as generic dispatch

Named typed tools put intent in the tool-call args. `run_command` is opaque
and often steals focus into an ST panel. If a capability is missing, that
is an MCP gap — not a reason to use `run_command`.

### Orient first

```
get_active_file()              # full buffer + 1-based cursor
get_cursor_context(lines=15)
get_selection()                # user's "look here"
```

### Symbols: LSP, not grep

```
lsp_goto_definition(line, column)                 # 0-based
lsp_find_references(line, column)
lsp_get_implementation(line, column)
lsp_get_type_definition(line, column)
lsp_search_workspace_symbols(query="calculate_total")
```

`file_path` optional (defaults to active view). Then
`open_file(path, line=...)` with **1-based** `line`.

### After edits: diagnostics

```
lsp_get_diagnostics(file_path=..., min_severity=1)   # 1=Error
lsp_get_diagnostics(min_severity=2)                  # errors+warnings, all open files
```

### Edit discipline

1. `str_replace_based_edit_tool` for targeted edits (exact unique `old_str`).
2. `save_file(path=...)` — the edit tool does **not** persist.
3. Multi-line inserts: `replace_lines`, never `insert` (auto-indent piles up).
4. Dirty `close_file` hangs on ST's save prompt — save first or
   `view.set_scratch(True)` via `eval_python`.

### Rename / format

```
lsp_rename_symbol(line, column, new_name="newTotal")  # returns workspace_edit only
lsp_apply_workspace_edit(session_name=..., edit=<workspace_edit>)  # session_name from lsp_get_sessions
lsp_get_diagnostics(min_severity=1)
lsp_format_document(file_path=...)                    # then sublime-mcp save_file
```

### Reading code

- `lsp_hover_info` — signature + markdown docs at the call site
- `lsp_get_symbols` — file outline
- `get_sheets` + `get_sheet_content` — any tab, including untitled / Terminus

### Debugging

Need the Debugger package loaded (`debugger_open` if you get
"Debugger package not loaded.").

```
debugger_toggle_breakpoint(file_path, line)   # 1-based
debugger_control(action="start", configuration_name="<launch config>")
# without configuration_name, action="start" only opens the UI
debugger_get_state                            # wait for is_paused
debugger_get_callstack
debugger_get_variables
debugger_evaluate(expression="self.items[0].price")
debugger_control(action="step_over"|"step_in"|"step_out"|"resume"|"stop")
debugger_add_watch_expression("len(self.items)")
debugger_get_exception_info()
debugger_control(action="stop")
debugger_clear_breakpoints()
```

`debugger_set_breakpoints_for_file` **replaces** that file's breakpoints.
`debugger_set_data_breakpoints` fires on write. `debugger_step_back` /
`debugger_reverse_continue` need adapter support (most don't). Don't leave
sessions running: `debugger_terminate()`.

## Worked example: fix a failing test

User is on `test_cart.py`, ST cursor line 42 (1-based).

```
get_active_file()
lsp_get_diagnostics(file_path="…/test_cart.py", min_severity=1)
lsp_goto_definition(line=41, column=20)          # 0-based = ST line 42 - 1
# → cart.py:88 (LSP range; convert to 1-based for open_file)
open_file(path="…/cart.py", line=88)
get_cursor_context(lines=30)
str_replace_based_edit_tool(command="str_replace", path="…/cart.py",
    old_str="return sum(i.price for i in self.items)",
    new_str="return sum(i.price * i.qty for i in self.items)")
save_file(path="…/cart.py")
lsp_get_diagnostics(min_severity=1)

# if the test still fails:
debugger_toggle_breakpoint(file_path="…/cart.py", line=88)
debugger_control(action="start", configuration_name="pytest")
debugger_get_variables()
debugger_evaluate(expression="[i.qty for i in self.items]")
debugger_control(action="stop")
debugger_clear_breakpoints()
```

`configuration_name` must be a Debugger launch config, not a shell command.

## Verifying new tools

POSTing a route **runs** it on the user's ST. For UI-interactive commands,
registry-only checks (`TOOLS` / `_MCP_TOOLS` / `_POST`) are enough. Do not
live-invoke:

- sublime-mcp: `prompt_goto_line`, `quick_panel`, `select_color_scheme`,
  `select_theme`, `open_in_browser`, `html_print`, `customize_*`,
  `convert_*`, `edit_syntax_settings`
- debugger-mcp: `debugger_open` (unless you need the UI), `debugger_settings`,
  `debugger_install_adapters`, `debugger_change_configuration`,
  `debugger_edit_configurations`, `debugger_example_projects`,
  `debugger_show_protocol`
- lsp-mcp: `lsp_toggle_server_panel`, `lsp_show_diagnostics_panel`,
  `lsp_document_symbols`, `lsp_workspace_symbols`, `lsp_call_hierarchy`,
  `lsp_type_hierarchy`

Silent buffer tools: prefer a scratch tab.

## Road forward

Compiled in-process engine for search / diff / token work:
[MCP Speedup Response.md](../MCP%20Speedup%20Response.md). Python stays the
orchestrator; only hot loops move to C.

## Lessons

- Never `insert` large content — ST auto-indent mangles it. Use
  `str_replace_based_edit_tool` or `replace_lines`.
- `eval_python`: `print()`, not `return`. `sublime` / `window` / `view` in
  scope. Main-thread timeout 5s.
- Never ST `exec` for shell. Use the agent's own terminal.
- `batch` for 2+ independent sublime-mcp calls (max 50).
