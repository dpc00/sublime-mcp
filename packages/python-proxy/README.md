# sublime-mcp

Python MCP proxy for the [sublime-mcp](https://github.com/dpc00/sublime-mcp)
Sublime Text package.

The proxy exposes Sublime Text editor state and commands to MCP clients over
stdio. It connects to the local HTTP bridge provided by the installed
`sublime-mcp` Sublime Text plugin.

## Installation

```bash
pip install sublime-mcp
```

Install and configure the Sublime Text plugin before starting the proxy. See
the repository README for complete installation, port configuration, and MCP
client setup instructions.

Version 1.6.0 adds first-class support for Sublime Text's native tab
multi-selection and sheet APIs.
