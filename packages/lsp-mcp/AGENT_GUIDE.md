# Agent Guide for lsp-mcp

This document teaches AI agents how to use lsp-mcp tools correctly.
Call `lsp_get_help` first if you're unsure how to navigate code, apply an
edit, or read diagnostics.

lsp-mcp wraps Sublime Text's **LSP** package (the Language Server Protocol
client) and exposes it as ~122 MCP tools. It serves MCP/SSE on port 9506
and a plain HTTP bridge on port 9516 (used by node-proxy / python-proxy,
not by direct SSE clients).

## Two tool families — pick the right one

1. **Hand-written LSP request wrappers** — `lsp_hover_info`,
   `lsp_goto_definition`, `lsp_find_references`, `lsp_get_diagnostics`,
   `lsp_get_symbols`, `lsp_get_code_actions`, `lsp_rename_symbol`,
   `lsp_get_completion`, `lsp_get_signature_help`, `lsp_get_implementation`,
   `lsp_get_type_definition`, `lsp_get_declaration`,
   `lsp_format_document`. These take explicit `line`/`column`/`file_path`
   arguments and return **structured JSON** — the results of a raw LSP
   request. Prefer these when you need data back to reason over.

2. **ST command passthroughs** — everything else (`lsp_symbol_rename`,
   `lsp_symbol_references`, `lsp_code_actions`, `lsp_hover`,
   `lsp_document_symbols`, `lsp_call_hierarchy`, ...). These call
   `view.run_command(<lsp_command>, args)` against the **active view's
   current cursor position** (no line/column args honored) and mostly
   return only `{"success": true}` — the real result opens as **interactive
   UI in Sublime Text** (a popup, a panel, a rename prompt, a quick-panel
   list). Don't expect structured data back from these; use them only when
   you specifically want to show something in the ST UI for the human, not
   to read a result yourself. As with sublime-mcp's own UI-interactive
   commands, be cautious about firing dialogs the user didn't ask for.

When in doubt: if the tool name looks like a hand-written wrapper above
(clear `get_`/`find_`/`rename_symbol` semantics with typed params), it's
(1). If it's a bare `lsp_<verb>` matching an ST command name with no real
params, it's (2).

## Coordinates are 0-based (LSP convention), not 1-based

Every hand-written wrapper takes `line`/`column` as **0-based** LSP
protocol positions — this differs from sublime-mcp's own tools (ST
convention, 1-based lines). Double-check which server a coordinate came
from before passing it to the other one; an off-by-one here is a common
mistake when combining sublime-mcp navigation with lsp-mcp queries in the
same task.

## Renaming is two steps, not one

`lsp_rename_symbol` only **calculates** the rename (issues a
`textDocument/rename` LSP request) and returns `{"workspace_edit": ...}`
— it does **not** touch any files. To actually apply it, pass that edit to
`lsp_apply_workspace_edit` (an ST command passthrough) separately, or use
the interactive `lsp_symbol_rename` command if you want ST's own rename UI
to handle both the calculation and the apply. Don't assume calling
`lsp_rename_symbol` alone changed anything on disk.

## Common workflow (read-then-navigate)

```
1. lsp_get_diagnostics                 (file_path optional — omit for all open files)
2. lsp_hover_info / lsp_get_symbols    (line, column both 0-based)
3. lsp_goto_definition / lsp_find_references / lsp_get_implementation
4. lsp_get_code_actions                (start_line required; end_line defaults to start_line)
5. lsp_rename_symbol  →  lsp_apply_workspace_edit   (two calls, not one)
6. lsp_format_document                 (file_path optional — defaults to active file)
```

## Diagnostics severity

`lsp_get_diagnostics` takes optional `min_severity` (1=Error, 2=Warning,
3=Info, 4=Hint, default 4 — i.e. everything). Pass `min_severity=1` to see
only errors.

## Full tool list

Use `tools/list` (MCP) or `GET /mcp_tools` (HTTP bridge) for the complete,
current set of ~122 tools with descriptions and JSON schemas — this guide
intentionally doesn't enumerate every tool since that list is always
available live and can drift from a static doc.
