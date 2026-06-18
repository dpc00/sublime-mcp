# sublime-mcp — Agent Context

**Root law:** If you need the org map, go to C:\Users\donal\router.md
**If this isn't the right place for your task, go back to:** C:\Users\donal\agents.md

---

## What This Project Is
MCP server that exposes Sublime Text commands and state to Claude and other AI agents.
5638 Sublime Text packages exist — potential to auto-generate MCPs from them.

## Key Files
- sublime_mcp.py (111KB) — Main MCP server implementation
- mcp_server.py — MCP server entry point
- MCP Commander.sublime-commands — Command palette entries (may be incomplete)
- index.js — JavaScript component

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
