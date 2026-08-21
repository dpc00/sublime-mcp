# Agent Guide for lsp-mcp

Call `lsp_get_help` if you are unsure how to navigate, apply an edit, or
read diagnostics.

Wraps Sublime Text's **LSP** package. 123 MCP tools. MCP SSE on port 9506;
HTTP bridge on 9516 (`GET /mcp_tools` for the live catalog). Override via
`lsp-mcp.sublime-settings` (`"mcp_port"` / `"http_port"`).

## Two tool families

1. **Hand-written LSP request wrappers** — explicit `line`/`column`/`file_path`,
   structured JSON. Prefer these when you need data back:
   `lsp_hover_info`, `lsp_goto_definition`, `lsp_find_references`,
   `lsp_get_diagnostics`, `lsp_get_symbols`, `lsp_get_code_actions`,
   `lsp_rename_symbol`, `lsp_get_completion`, `lsp_get_signature_help`,
   `lsp_get_implementation`, `lsp_get_type_definition`, `lsp_get_declaration`,
   `lsp_format_document`, `lsp_search_workspace_symbols`.
2. **ST command passthroughs** — `lsp_symbol_rename`, `lsp_symbol_references`,
   `lsp_code_actions`, `lsp_hover`, `lsp_document_symbols`, `lsp_call_hierarchy`,
   … These run `view.run_command` at the **active view's current cursor** (no
   line/column honored) and return `{"success": true}`; the result is ST UI.
   Use only to show something to the human. Do not fire
   `lsp_toggle_server_panel`, `lsp_show_diagnostics_panel`,
   `lsp_document_symbols`, `lsp_workspace_symbols`, `lsp_call_hierarchy`,
   `lsp_type_hierarchy` just to "verify" them.

## Coordinates are 0-based

Hand-written wrappers take LSP **0-based** `line`/`column`. sublime-mcp tools
are **1-based**. Convert before crossing servers (`lsp_line = st_line - 1`).

## Rename is two steps

`lsp_rename_symbol` only **calculates** `textDocument/rename` and returns
`{"workspace_edit": ...}` — it does not touch files. Apply with
`lsp_apply_workspace_edit(session_name=..., edit=<that workspace_edit>)`
(`session_name` from `lsp_get_sessions`), or use interactive
`lsp_symbol_rename` for ST's own rename UI. Same pattern for code actions:
`lsp_get_code_actions` then `lsp_apply_text_document_edit` /
`lsp_apply_workspace_edit`.

## Workflow

```
1. lsp_get_diagnostics                 # file_path optional; omit for all open files
2. lsp_hover_info / lsp_get_symbols    # line, column 0-based
3. lsp_goto_definition / lsp_find_references / lsp_get_implementation
4. lsp_get_code_actions                # start_line required; end_line defaults to start_line
5. lsp_rename_symbol → lsp_apply_workspace_edit
6. lsp_format_document                 # file_path optional — defaults to active file
```

## Diagnostics severity

`lsp_get_diagnostics` `min_severity`: 1=Error, 2=Warning, 3=Info, 4=Hint
(default 4 = everything). Use `min_severity=1` for errors only.

## Full tool list

`tools/list` (MCP) or `GET /mcp_tools` on port 9516.
