# Reply — 2026-08-18 (on-the-fly package MCP)

You are right. I had the wrong object.

There is a plan for a **sublime-mcp tool** that creates an MCP
on the spot for any Sublime package — whether that package is
already installed or not yet installed. On the fly.

That tool is not in sublime-mcp yet. It is not a tool yet. It is
not `get_package_mcp_info`. It is not this agent-plugin spec.

What that means for the plugin:

- Required: sublime-mcp only.
- debugger-mcp / lsp-mcp / Debugger / LSP are not shipped,
  not junctioned, not auto-installed. They were an earlier
  sketch of "MCP for a package," which the future tool is
  supposed to cover for any package.
- `install_package` can still install a package the user
  names. That does not generate an MCP.

The spec is corrected.

`docs/superpowers/specs/2026-08-18-agent-plugin-design.md`
