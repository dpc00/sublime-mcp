# sublime-mcp — Agent Context

---

## What This Project Is
MCP server that exposes Sublime Text commands and state to Claude and other AI agents.
5638 Sublime Text packages exist — potential to auto-generate MCPs from them.

## Critical Assumption
Plugin edits in this repo are NOT live in Sublime Text until deployed to the installed Sublime Text Packages directory. Never assume test results are valid until the file has been copied there. If something isn't working, check deployment before investigating the code.

## The Three MCPs

This repo ships **three independent MCP servers**, each a separate ST plugin
exposing tools over HTTP+SSE on its own port. They do not depend on each
other; connect to the subset your task needs.

| MCP            | ST plugin dir              | Port | Tool prefix | Purpose                                                     |
| -------------- | -------------------------- | ---- | ----------- | --------------------------------------------------------- |
| **sublime-mcp** | `packages/st-plugin`       | 9500 (Win) / 9501 (Linux/WSL) | *(none)* | Editor state + built-in ST commands (218 tools)           |
| **debugger-mcp** | `packages/debugger-mcp`   | 9505 | `debugger_` | DAP debugging (breakpoints, stepping, variables, callstack) |
| **lsp-mcp**     | `packages/lsp-mcp`         | 9506 | `lsp_`      | Language Server Protocol (diagnostics, hover, refs, rename)  |

Ports are overridable via env vars: `SUBLIME_MCP_BASE`,
`DEBUGGER_MCP_PORT`, `LSP_MCP_PORT`.

## Key Files
- `packages/st-plugin/sublime_mcp.py` (161KB, 4089 lines) — Main MCP server; 218 typed tools (`_MCP_TOOLS`) covering ST's built-in text/window/application commands + read-only state getters
- `packages/debugger-mcp/debugger_mcp.py` (1983 lines) — Debugger MCP; `TOOLS` list (line 1350) exposes ~75 `debugger_*` tools (DAP session-level + ST command wrappers in `_DEBUGGER_ST_COMMANDS` at line 1273)
- `packages/lsp-mcp/lsp_mcp.py` (2047 lines) — LSP MCP; `TOOLS` list (line 1358) exposes ~120 `lsp_*` tools (hand-written request wrappers + ST command wrappers in `_LSP_ST_COMMANDS` at line 722)
- `packages/python-proxy/mcp_server.py` — Python agent-side proxy (FastMCP → HTTP bridge to port 9500/9501)
- `packages/node-proxy/index.js` — Node agent-side proxy (@modelcontextprotocol/sdk → HTTP bridge)

## Connecting an Agent

### Option A — Bundled agent-side proxy (recommended for sublime-mcp)
The proxy speaks MCP to your agent and HTTP+SSE to the ST plugin.

**Python:**
```bash
cd packages/python-proxy
pip install .
sublime-mcp   # reads SUBLIME_MCP_BASE, defaults to http://127.0.0.1:9500 on Windows
```

**Node:**
```bash
cd packages/node-proxy
npm install .
npx sublime-mcp
```

### Option B — Point an MCP client directly at the SSE endpoint
Each ST plugin serves `GET /sse` + `POST /messages` at its port. Any MCP
client with streamable-HTTP transport can connect directly:
```json
{
  "mcp": {
    "sublime-mcp":   { "url": "http://127.0.0.1:9500" },
    "debugger-mcp":  { "url": "http://127.0.0.1:9505" },
    "lsp-mcp":       { "url": "http://127.0.0.1:9506" }
  }
}
```

---

# How to Use the MCPs to Accomplish Real Work

The three MCPs are designed to **combine**. The agent's job is rarely "use
one tool"; it is a workflow like *understand → navigate → edit → verify →
(debug if needed) → confirm clean*. Each MCP owns one leg of that loop.
Skim the workflows below before reaching for any tool.

## Mental Model

| You want to...                                  | Use                | Why                                                                          |
| ----------------------------------------------- | ------------------ | --------------------------------------------------------------------------- |
| See what the user is looking at right now        | sublime-mcp        | `get_active_file` / `get_cursor_context` read the *focused* view, not disk. |
| Find where a symbol lives (def / refs / impl)   | lsp-mcp            | Language servers index the project; `lsp_goto_definition` returns locations. |
| Understand a type, signature, or docstring      | lsp-mcp            | `lsp_hover_info` returns markdown docs + signature; no equivalent in editor. |
| Know what's broken in the project right now      | lsp-mcp            | `lsp_get_diagnostics` aggregates errors across all active LSP servers.     |
| Edit a file the user has open in ST             | sublime-mcp        | Edits land in the live buffer; ST's undo + gutter diff reflect them.         |
| Edit a file the user does NOT have open         | filesystem (edit)  | Then `open_file` in ST so the user sees it.                                 |
| Rename a symbol safely across the project        | lsp-mcp            | `lsp_rename_symbol` is compiler-checked; raw text replace is not.           |
| Apply a quick-fix / refactor the LSP offered     | lsp-mcp            | `lsp_get_code_actions` returns the exact actions the server offers.         |
| Walk a failing test / crash interactively        | debugger-mcp       | Breakpoints, stepping, variable inspection — see "Debugging" below.         |
| Inspect a running process's memory / disassembly | debugger-mcp      | `debugger_read_memory`, `debugger_disassemble`.                             |
| Run a build / test shell command                 | **your own shell** | Never ST's `exec`. User can't cancel it. See "Never" list.                   |

## Editor Authority (the rule that makes the MCPs worth using)

**Default to sublime-mcp for everything — read, edit, save, close, find,
navigation, selection, outside-workspace paths, all of it.** Fall back to
built-in filesystem tools (`read`/`edit`/`write`/`grep`/`glob`) ONLY when ST
or the sublime-mcp bridge is non-responsive (frozen, crashed, plugin-load
failure, MCP HTTP error). The fallback trigger is ST being down — not the
path being outside the workspace, not a sandbox restriction, not
"convenience." There is no sandbox on this machine; outside-workspace is
just a path and `open_file` opens it like any other.

This rule is not aesthetic. It is benchmarked:

### Benchmarks (2026-07-21, real workspace file, warm averages)

| Operation      | Built-in tool | sublime-mcp     | Winner            |
| -------------- | ------------- | --------------- | ----------------- |
| Read 68KB file | `read` ~0.3 ms | ~0.4 ms         | **Sublime ~11× faster** |
| Single-line edit | `edit` ~0.9 ms | ~0.02 ms        | **Sublime ~45× faster** |
| Project search | `grep` 21-28 ms | ~15 ms (see caveat) | Sublime ~1.4× (was misleading — see below) |

The performance argument for the built-in filesystem tools does not exist
in this workspace. A 45× per-edit speed advantage means even a 50-file
refactor is faster through ST (50 × 0.02 ms = 1 ms) than through built-in
`edit` (50 × 0.9 ms = 45 ms warm).

**Search caveat:** the original `find_in_files` was a Python `os.walk`
reimplementation that bypassed ST's real C++ Find engine — so the search
benchmark measured two reimplementations, not ST's native find. It has
since been replaced with a real call to ST's Find-in-Files panel (the
three-box Ctrl+Shift+H panel with the full `${...}` Where syntax: folder
paths, `*.py`, `-*.md`, `${project}`, `${open_files}`, regex with
capture-group backrefs, `preserve_case`, `in_selection`, diff-preview
multi-file replace). The native C++ engine is faster than both Python
walks and the built-in `grep`.

### The qualitative wins that don't show in milliseconds
1. **You can see it.** sublime-mcp edits show up in the buffer instantly
   with gutter diff markers and a 30-second highlight annotation.
   Built-in `edit` writes to disk silently — the user only knows it
   happened if they go look.
2. **Undo works.** Ctrl+Z in ST reverses the agent's edit. Built-in
   `edit` has no undo path — it's a file overwrite.
3. **Save is a real, visible step.** Buffer goes dirty, user sees it,
   agent calls `save_file` explicitly. Built-in `edit` auto-saves to
   disk and the user is blind to it.
4. **Close is a real step.** `close_file` retires the tab. Built-in tools
   never open a tab, so files accumulate as anonymous dirty buffers in
   ST when the user opens them later — now out of sync with what the
   agent wrote.
5. **No out-of-band drift.** The "reformatter changed my file" confusion
   happens because built-in `edit` writes disk while ST holds a stale
   buffer. Routing through ST eliminates the two-sources-of-truth problem
   entirely.

### When NOT to fall back
- **Outside the workspace** is NOT a fallback trigger. ST has no
  sandbox; `open_file` opens any path on the machine. Treat
  outside-workspace paths exactly like inside-workspace paths.
- **"Gemini's sandbox wouldn't let me"** is NOT a fallback trigger.
  That sandbox was the agent host's, not ST's. Using `eval_python` or
  `run_command` to escape it is the bug, not the design.
- **"It's faster to just use `edit`"** is false — see the benchmarks.

### When to fall back
- ST is frozen, crashed, or the plugin failed to load.
- The sublime-mcp HTTP bridge is unresponsive (timeout, connection
  refused, error response).
- The view API is returning errors (e.g. `no active view` repeatedly
  when there should be one).

In those cases, use the built-in filesystem tools to keep working, then
`revert_file` (or reopen) the affected files in ST once ST recovers so the
buffers resync from disk.

### Never use `run_command` as a generic dispatch
`run_command` is opaque — the agent calls
`run_command("find_in_files", {"where": "...", "pattern": "..."})` and
the user sees nothing: no visible panel, no args preview, no "here's
what I'm about to do." Dedicated MCP tools with typed schemas put the
agent's *intent* in the tool-call arguments, visible in the chat before
the action lands. Reach for the named typed tool, not `run_command`. If
the capability isn't exposed as a named tool, that's a gap to fix in the
MCP — not a reason to fall back to `run_command`.

### First move: ground yourself in the user's focus
Before editing, the agent must know **what file the user is actually looking
at** and **where their cursor is**. The user's mental context is the buffer
in front of them, not whatever file the agent last touched.

```
get_active_file()         → { path, content, line, col, is_dirty, syntax }
get_cursor_context(lines=15)  → ±15 lines around the cursor, with line numbers
get_selection()           → any highlighted text (the user's "look here" signal)
```

`get_active_file` returns the full buffer content + cursor position in one
call. This is the single most important orienting tool. Use it at the start
of any edit task, and again after long tool chains in case the user moved.

### Where is the symbol? LSP, not grep
When the user says "fix the bug in `calculate_total`", do not grep. Ask the
language server:
```
lsp_goto_definition(line, column)        → file + range of the definition
lsp_find_references(line, column)        → every call site
lsp_get_implementation(line, column)     → concrete impl of an interface
lsp_get_type_definition(line, column)    → the type, not the variable
lsp_search_workspace_symbols(query="calculate_total")  → when you only have a name
```
All take 0-based `line`/`column` and optional `file_path` (defaults to the
active view). Returns structured locations you can immediately
`open_file(path, line=...)` to visit.

### What's broken right now? Diagnostics, not reading every file
After any non-trivial edit, check the project's health in one call:
```
lsp_get_diagnostics(file_path=..., min_severity=1)   # 1=Error only
lsp_get_diagnostics(min_severity=2)                  # errors+warnings across project
```
This is how you know your edit didn't break a caller three files away —
without reading every file. Treat it as the compile step you never had.

### Editing — the sublime-mcp discipline
**Golden rule:** the live ST buffer is the source of truth while the user
works. Disk is secondary. Edit the buffer, then save.

1. **Prefer `str_replace_based_edit_tool`** for targeted edits — it lands in
   the live buffer with full undo and gutter diff markers the user can see.
2. **Always `save_file(path=...)` afterward** — `str_replace_based_edit_tool`
   does NOT persist to disk. Skipping `save_file` causes desync: ST shows
   your edit, `git diff` shows nothing.
3. **For whole-line / multi-line inserts use `replace_lines`**, never
   `insert` with large content — ST's auto-indent accumulates indentation
   on every line and destroys formatting.
4. **If you used the `edit` filesystem tool** on a file ST has open, call
   `revert_file()` so ST reloads from disk — otherwise ST keeps showing the
   stale buffer and the user's edits land on the old text.
5. **Closing a dirty tab hangs the tool** (ST prompts the user). Save first,
   or mark scratch via `eval_python` (see AGENT_GUIDE.md).
6. **Never `run_command`** for editor operations. It is focus-dependent and
   the user's AI console must hold focus. Use the typed tool instead
   (`save_file`, `open_file`, `goto_line`, `find_in_file`, etc.).

### Renaming / refactoring — let the compiler check it
Do not text-replace across files for renames. The language server does a
compiler-validated rename in one call:
```
lsp_rename_symbol(line, column, new_name="newTotal")
```
This touches every reference the LSP knows about, and refuses if the
name is invalid. Follow up with `lsp_get_diagnostics` to confirm no new
errors, then `lsp_save_all` (or sublime-mcp `save_all`) to persist.

For quick-fixes the LSP itself offered (missing import, wrap in try, etc.):
```
lsp_get_code_actions(start_line, ...)  → list of available actions
```
Inspect the returned actions; apply the right one via
`lsp_apply_text_document_edit` / `lsp_apply_workspace_edit`.

### Format on save — let the LSP do it
When the project uses black/ruff/clang-format/etc. via LSP:
```
lsp_format_document(file_path=...)
```
Run this as the last step before `save_file`. Do not hand-format.

### Reading code you don't understand
- `lsp_hover_info(line, column)` — type definition, signature, and
  **markdown documentation** for the symbol. This is the fastest way to
  understand an unfamiliar API without leaving the call site.
- `lsp_get_symbols(file_path)` — outline of the file (functions, classes,
  methods) so you can navigate a large file by structure, not by scrolling.
- `get_cursor_context(lines=20)` — the ±20 lines around the cursor, with
  line numbers. Use this to understand what the user is pointing at.
- `get_sheets()` + `get_sheet_content(index)` — read ANY tab, including
  untitled buffers, scratch tabs, and Terminus output that has no file path.

### Debugging — when the test fails and you don't know why
This is where debugger-mcp earns its keep. The workflow is:
1. **Set a breakpoint where the failure originates**, not where it's
   reported:
   ```
   debugger_toggle_breakpoint(file_path, line)
   ```
2. **Start the session** with the relevant configuration:
   ```
   debugger_control(action="start", configuration_name="pytest")
   ```
3. **When it pauses**, inspect the callstack top-down to find the frame
   where the assumption was violated:
   ```
   debugger_get_callstack()       # frames, most recent first
   debugger_get_variables()       # locals in the selected frame
   debugger_get_scopes()          # scope structure
   debugger_evaluate(expression="self.items[0].price")  # ad-hoc probe
   ```
4. **Step to narrow the failure**:
   - `debugger_control(action="step_over")` — stay in the current function
   - `debugger_control(action="step_in")` — descend into the callee
   - `debugger_control(action="step_out")` — run to caller
   - `debugger_control(action="resume")` — continue to next breakpoint
5. **Watch key expressions as you step**:
   ```
   debugger_add_watch_expression("len(self.items)")
   debugger_get_watch_expressions()   # read current values each pause
   ```
6. **If it crashed**, read the exception:
   ```
   debugger_get_exception_info(thread_id)
   ```
7. **When done**, clean up:
   ```
   debugger_control(action="stop")
   debugger_clear_breakpoints()
   ```

For reverse-debugging adapters (if supported): `debugger_step_back` and
`debugger_reverse_continue` let you walk backwards from the failure to find
when the bad value was first written — often the only way to diagnose a
heisenbug.

**Debugging wisdom:**
- Breakpoint at the *symptom* (the assert, the exception) and inspect locals
  there first. If they look fine, walk up the callstack until they don't.
- `debugger_evaluate` is your ad-hoc probe — use it liberally on paused
  frames to test hypotheses ("is `self.cached` stale?").
- Set a **data breakpoint** (`debugger_set_data_breakpoints`) on a field
  that changes unexpectedly — it fires on the *write*, not the read.
- Don't leave sessions running when you finish — `debugger_terminate()`
  frees the adapter and the user's terminal.

## Worked Example: "Fix the failing test in `test_cart.py`"

A real task ties all three MCPs together. Assume the user is looking at the
failing test in ST.

```
# 1. Orient: what's the user looking at?
get_active_file()                    # test_cart.py, line 42, cursor on assertEqual

# 2. Diagnose: what does the language server know?
lsp_get_diagnostics(file_path="…/test_cart.py", min_severity=1)   # none in this file
lsp_goto_definition(line=41, column=20)                           # → cart.py:88, Cart.calculate_total
lsp_hover_info(line=88, column=10, file_path="…/cart.py")         # docstring + signature

# 3. Read the suspect function
open_file(path="…/cart.py", line=88)
get_cursor_context(lines=30)         # see calculate_total body + neighbours

# 4. Edit the fix in the live buffer
str_replace_based_edit_tool(command="str_replace", path="…/cart.py",
    old_str="return sum(i.price for i in self.items)",
    new_str="return sum(i.price * i.qty for i in self.items)")
save_file(path="…/cart.py")

# 5. Verify: did the project get healthier?
lsp_get_diagnostics(min_severity=1)  # no new errors anywhere

# 6. If the test still fails, debug it
debugger_toggle_breakpoint(file_path="…/cart.py", line=88)
debugger_control(action="start", configuration_name="pytest test_cart.py")
# paused at the breakpoint
debugger_get_variables()             # see self.items
debugger_evaluate(expression="i.qty for i in self.items")  # confirm the field exists
debugger_control(action="resume")   # run to completion / next breakpoint
debugger_control(action="stop")
debugger_clear_breakpoints()

# 7. Confirm the user sees the saved result
get_active_file()  # is_dirty should be False after save_file
```

Every step uses the right MCP: sublime-mcp to orient and edit, lsp-mcp to
navigate and verify, debugger-mcp to inspect the live failure. No grep, no
guessing, no focus-stealing `run_command`.

## Verifying Newly Added Tools — Do Not Live-Invoke UI Commands
When adding new routes to `TOOLS` / `_POST`, "live verification" means POSTing
to the route — which actually *invokes* the command on the user's running ST.
For most tools this is harmless (set_mark, sort_lines, etc. just mutate the
buffer). But for UI-interactive commands it fires real dialogs/overlays on
the user's screen:

- sublime-mcp: `prompt_goto_line`, `quick_panel`, `select_color_scheme`,
  `select_theme`, `open_in_browser`, `html_print`, `customize_*`,
  `convert_*`, `edit_syntax_settings`
- debugger-mcp: `debugger_open`, `debugger_settings`,
  `debugger_install_adapters`, `debugger_change_configuration`,
  `debugger_edit_configurations`, `debugger_example_projects`,
  `debugger_show_protocol`
- lsp-mcp: `lsp_toggle_server_panel`, `lsp_show_diagnostics_panel`,
  `lsp_document_symbols`, `lsp_workspace_symbols`, `lsp_call_hierarchy`,
  `lsp_type_hierarchy`

**Policy:** For UI-interactive commands, registry-only verification is
sufficient — confirm the route exists in `_POST` and the entry exists in
`TOOLS`. Do NOT POST to live-invoke. Only live-invoke silent
buffer-mutation commands, and even then prefer a no-op target (empty
buffer / scratch tab) so the user's work isn't disturbed.

## Critical Lessons Learned

### NEVER use `insert` to paste large content
ST's auto-indent accumulates indentation on every line and destroys
formatting. Use `str_replace_based_edit_tool` for targeted edits, or
`replace_lines` for whole-line ranges.

### `revert_file` is the reliable reload
`revert` sometimes doesn't fully reload. Reliable approach:
```python
# eval_python
path = view.file_name()
view.set_scratch(True)
view.close()
window.open_file(path)
```

### Never use ST's built-in `exec` to run shell commands
The user loses control and can't always "cancel build". Run builds and
tests in **your own shell**, not through ST.

### eval_python: use `print()`, not `return`
Top-level `return` is a syntax error. Bare expressions don't output. Use
`print(expr)`. `sublime`, `window`, `view` are in scope. Great for
operations the typed tools don't cover (closing dirty tabs, inspecting
sheets, batch view operations).

## Known Issues
- MCP Commander.sublime-commands may be incomplete
- Some commands in C:\Users\donal\projects\SText\Default.sublime-commands may belong here

## Active Ideas
- Auto-generate MCPs from installed ST packages
- See https://modelcontextprotocol.io/extensions/apps/overview for the target vision

## Related Projects
- SText (uses this MCP server)
- joelekstrom's sublime-context-MCP (external, Donal left a comment there)
- OmkarGowda990's sublime-text-mcp (external)
