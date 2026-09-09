# Sublime-MCP: Universal AI Agent Connector for Sublime Text

Gives any MCP-speaking AI agent real control over a running Sublime Text 4
instance: run registered ST commands, read/write views and selections, inspect
tabs and project state, and `eval_python` in Sublime's plugin host for anything
the typed tools don't cover.

Controlling another installed Sublime package (a debugger, a language server,
anything else) doesn't need its own dedicated MCP server — `get_package_mcp_info`
plus `eval_python`/`run_command` covers it directly. See `skills/package-skill-generator`
to turn a one-time investigation into a small, reusable skill file instead.

## Toolset

Seven workflow tools are advertised by default. `discover_tools` searches the
complete internal catalog of 238 typed Sublime capabilities, and `batch` invokes
discovered capabilities without flooding the model's initial tool context.

Agent how-to: [AGENT_GUIDE.md](AGENT_GUIDE.md) (also served live by
`get_help`). Release history: [CHANGELOG.md](CHANGELOG.md).

## Ports

sublime-mcp serves **MCP streamable HTTP** at `/mcp`, legacy **MCP SSE** at
`/sse`, and a **plain HTTP bridge**.
The bundled Node/Python proxies use sublime-mcp's HTTP bridge only. Defaults:

| Plugin        | MCP SSE                         | HTTP bridge                     | Settings file                        |
| ------------- | ------------------------------- | ------------------------------- | ------------------------------------- |
| sublime-mcp   | 9502 (Win) / 9503 (macOS/Linux) | 9500 (Win) / 9501 (macOS/Linux) | `sublime-mcp.sublime-settings`        |

The settings file takes `"mcp_port"` and `"http_port"` keys; edit your copy
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

The repo root **is** the package. Symlink it into ST's `Packages/` directory as `sublime-mcp`.

**Windows (Command Prompt):**
```cmd
mklink /J "%APPDATA%\Sublime Text\Packages\sublime-mcp" "C:\path\to\sublime-mcp"
```

**macOS:**
```bash
ln -s "$(pwd)" "$HOME/Library/Application Support/Sublime Text/Packages/sublime-mcp"
```

**Linux:**
```bash
ln -s "$(pwd)" "$HOME/.config/sublime-text/Packages/sublime-mcp"
```

Restart Sublime Text after linking so the plugin loads. (Once published to
Package Control, installing is just `Package Control: Install Package` —
no symlink needed.)

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

For Codex, use its native streamable-HTTP configuration; no `mcp-remote`
wrapper is required:

```toml
[mcp_servers.sublime-mcp]
type = "http"
url = "http://127.0.0.1:9502/mcp"

[mcp_servers.debugger-mcp]
type = "http"
url = "http://127.0.0.1:9505/mcp"

[mcp_servers.lsp-mcp]
type = "http"
url = "http://127.0.0.1:9506/mcp"
```

Restart or open a new Codex session after changing MCP configuration. Verify
the entire path before debugging agent behavior:

```bash
npx sublime-mcp doctor
npx sublime-mcp doctor --all
```

The first command checks sublime-mcp. `--all` also checks debugger-mcp and
lsp-mcp. The report separately checks each HTTP bridge, MCP handshake, and
focused tool catalog. From Sublime's Command Palette,
`MCP Commander: Connection Doctor` shows the main server-side state.

Other MCP clients may use the legacy SSE URL (Windows example):

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

## Agent skill

Installable Codex skills are in `skills/sublime-mcp`,
`skills/sublime-debugger`, and `skills/sublime-lsp`. Copy the desired
directories to your Codex skills directory or install them through your normal
skill workflow.
