# Sublime-MCP: Universal AI Agent Connector for Sublime Text

Gives any MCP-speaking AI agent real control over a running Sublime Text 4
instance: run registered ST commands, read/write views and selections, inspect
tabs and project state, and `eval_python` in Sublime's plugin host for anything
the typed tools don't cover.

Two optional companion plugins extend this:

- **debugger-mcp** — Debugger package DAP tools (breakpoints, stepping,
  variables, call stacks) over MCP
- **lsp-mcp** — LSP tools (definition, references, diagnostics, rename, hover)
  over MCP

## Toolset

220 typed sublime-mcp tools cover ST's built-in text/window/application
commands plus read-only state getters, a `batch` tool (max 50 calls per
request), and `eval_python`. debugger-mcp adds 102 `debugger_*` tools;
lsp-mcp adds 123 `lsp_*` tools.

Agent how-to: [docs/AGENT_GUIDE.md](docs/AGENT_GUIDE.md) (also served live by
`get_help`). Workflow across all three MCPs: [docs/agents.md](docs/agents.md).
Release history: [CHANGELOG.md](CHANGELOG.md).

## Ports

Each plugin serves **MCP SSE** (direct clients) and a **plain HTTP bridge**.
The bundled Node/Python proxies use sublime-mcp's HTTP bridge only. Defaults:

| Plugin        | MCP SSE                         | HTTP bridge                     | Settings file                        |
| ------------- | ------------------------------- | ------------------------------- | ------------------------------------- |
| sublime-mcp   | 9502 (Win) / 9503 (macOS/Linux) | 9500 (Win) / 9501 (macOS/Linux) | `sublime-mcp.sublime-settings`        |
| debugger-mcp  | 9505                            | 9515                            | `debugger-mcp.sublime-settings`       |
| lsp-mcp       | 9506                            | 9516                            | `lsp-mcp.sublime-settings`            |

Each settings file takes `"mcp_port"` and `"http_port"` keys; edit your copy
under `Packages/User/` (Preferences > Package Settings) to override the
defaults above — no env vars needed.

SSE URL form: `http://127.0.0.1:<sse-port>/sse`. The bundled Node/Python
proxies talk to sublime-mcp's **HTTP bridge**, not SSE; override with
`SUBLIME_MCP_BASE` (e.g. `http://127.0.0.1:9500`).

## Installation

### 1. Clone

```bash
git clone https://github.com/dpc00/sublime-mcp.git
cd sublime-mcp
```

### 2. Install the Sublime Text plugin

Symlink `packages/st-plugin` into ST's `Packages/` directory as `sublime-mcp`.

**Windows (Command Prompt):**
```cmd
mklink /J "%APPDATA%\Sublime Text\Packages\sublime-mcp" "C:\path\to\sublime-mcp\packages\st-plugin"
```

**macOS:**
```bash
ln -s "$(pwd)/packages/st-plugin" "$HOME/Library/Application Support/Sublime Text/Packages/sublime-mcp"
```

**Linux:**
```bash
ln -s "$(pwd)/packages/st-plugin" "$HOME/.config/sublime-text/Packages/sublime-mcp"
```

### 3. Optional companion plugins

Same pattern: symlink `packages/debugger-mcp` and/or `packages/lsp-mcp` into
`Packages/` under those names.

**Windows:**
```cmd
mklink /J "%APPDATA%\Sublime Text\Packages\debugger-mcp" "C:\path\to\sublime-mcp\packages\debugger-mcp"
mklink /J "%APPDATA%\Sublime Text\Packages\lsp-mcp" "C:\path\to\sublime-mcp\packages\lsp-mcp"
```

**macOS:**
```bash
ln -s "$(pwd)/packages/debugger-mcp" "$HOME/Library/Application Support/Sublime Text/Packages/debugger-mcp"
ln -s "$(pwd)/packages/lsp-mcp" "$HOME/Library/Application Support/Sublime Text/Packages/lsp-mcp"
```

**Linux:**
```bash
ln -s "$(pwd)/packages/debugger-mcp" "$HOME/.config/sublime-text/Packages/debugger-mcp"
ln -s "$(pwd)/packages/lsp-mcp" "$HOME/.config/sublime-text/Packages/lsp-mcp"
```

Restart Sublime Text after linking so the plugins load.

### 4. Configure your agent

**Node:**
```bash
cd packages/node-proxy
npm install .
npx sublime-mcp
```

**Python:**
```bash
cd packages/python-proxy
pip install .
sublime-mcp
```

Or point an MCP client with SSE transport at the SSE URL (Windows example):

```json
{
  "mcpServers": {
    "sublime-mcp": { "type": "sse", "url": "http://127.0.0.1:9502/sse" }
  }
}
```

Each plugin's MCP server starts automatically when ST loads it. To stop or
restart sublime-mcp's, run "MCP Commander: Server Status" from the Command
Palette. Check View > Show Console for startup confirmation.
