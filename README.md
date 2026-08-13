# Sublime-MCP: Universal AI Agent Connector for Sublime Text

Gives any MCP-speaking AI agent (Claude Code, etc.) real control over a
running Sublime Text 4 instance — not just file edits, but the editor
itself: run any registered ST command, read/write views and selections,
drive the command palette, inspect open tabs and project state, and
execute arbitrary Python directly in Sublime's plugin host for anything
the API doesn't expose a dedicated tool for. Two optional companion
plugins extend this further: **debugger-mcp** exposes the Debugger
package's DAP tools (breakpoints, stepping, variable inspection, call
stacks) over MCP, and **lsp-mcp** exposes LSP tools (go-to-definition,
references, diagnostics, rename, hover) the same way — both served over
MCP SSE so an agent can debug and navigate code with full language-server
awareness, not just text search.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/dpc00/sublime-mcp.git
cd sublime-mcp
```

### 2. Install the Sublime Text Plugin

**Windows (Command Prompt):**
```cmd
mklink /J "%APPDATA%\Sublime Text\Packages\sublime-mcp" "C:\path\to\your\sublime-mcp\repo\packages\st-plugin"
```

**macOS/Linux:**
```bash
ln -s "`pwd`/packages/st-plugin" "~/Library/Application Support/Sublime Text/Packages/sublime-mcp"
```

*(Remember to replace `C:\path\to\your\sublime-mcp\repo` with the actual path to where you cloned the repository.)*

### 3. Install Optional Standalone MCP Plugins

The repo ships two additional standalone Sublime Text plugins that expose
debugging (DAP) and language-server (LSP) tools over MCP. Install them the
same way as the main plugin, by symlinking each package into your Sublime
Text `Packages/` directory.

**debugger-mcp** (serves Debugger DAP tools over MCP SSE on port 9505):

**Windows (Command Prompt):**
```cmd
mklink /J "%APPDATA%\Sublime Text\Packages\debugger-mcp" "C:\path\to\your\sublime-mcp\repo\packages\debugger-mcp"
```

**macOS/Linux:**
```bash
ln -s "`pwd`/packages/debugger-mcp" "~/Library/Application Support/Sublime Text/Packages/debugger-mcp"
```

**lsp-mcp** (serves LSP tools over MCP SSE on port 9506):

**Windows (Command Prompt):**
```cmd
mklink /J "%APPDATA%\Sublime Text\Packages\lsp-mcp" "C:\path\to\your\sublime-mcp\repo\packages\lsp-mcp"
```

**macOS/Linux:**
```bash
ln -s "`pwd`/packages/lsp-mcp" "~/Library/Application Support/Sublime Text/Packages/lsp-mcp"
```

The ports can be overridden with the `DEBUGGER_MCP_PORT` and `LSP_MCP_PORT`
environment variables. Restart Sublime Text after linking so the plugins load.

### 4. Configure Your Agent

Install the agent-side proxy and configure your agent:

**For Node.js agents:**
```bash
cd packages/node-proxy
npm install .
npx sublime-mcp
```

**For Python agents:**
```bash
cd packages/python-proxy
pip install .
sublime-mcp
```
