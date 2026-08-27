---
name: sublime-lsp
description: Use Sublime Text's LSP package through lsp-mcp. Use for diagnostics, hover information, definitions, references, symbols, code actions, completion, formatting, semantic navigation, or LSP-backed refactoring in Sublime Text.
---

# Sublime LSP

Call `lsp_get_help` when a workflow or argument is unclear. Prefer structured
LSP request tools over UI command passthroughs.

Use the seven visible workflow tools directly. For every other operation, call
`lsp_discover_tools` with a capability-oriented query, inspect the returned
schema, then call the exact result through `lsp_batch`. Combine independent
read-only requests in one batch; keep edits sequential.

LSP line and column coordinates are 0-based. A rename returns a workspace edit
and does not modify files by itself; discover and call the workspace-edit tool
to apply it, then recheck diagnostics.
