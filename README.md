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
| sublime-mcp   | 9502 (Win) / 9503 (macOS/Linux) | 9500 (Win) / 9501 (macOS/Linux) | `MCP Commander.sublime-settings`      |

The settings file takes `"mcp_port"` and `"http_port"` keys; edit your copy
under `Packages/User/` (Preferences > Package Settings) to override the
defaults above — no env vars needed.

SSE URL form: `http://127.0.0.1:<sse-port>/sse`. The bundled Node/Python
proxies talk to sublime-mcp's **HTTP bridge**, not SSE; override with
`SUBLIME_MCP_BASE` (e.g. `http://127.0.0.1:9500`).

## Security

Both servers are **loopback-only (`127.0.0.1`) by default and have no
authentication** — one of the tools they expose (`eval_python`) is
arbitrary code execution in Sublime's own process, so treat this server
as equivalent in trust level to your own login session. All of the
following are keys in `MCP Commander.sublime-settings`:

- **`allow_lan_access`** (default `false`) — binds `0.0.0.0` instead of
  `127.0.0.1`, making both servers reachable from every other device on
  your network, still with no authentication. Only turn this on for a
  specific reason a client can't reach `127.0.0.1` directly (e.g. a WSL
  client when WSL's networking mode doesn't forward localhost to the
  Windows host).
- **`auth_token`** (default unset) — requires a matching
  `Authorization: Bearer <token>` header on every request. This is the
  one control that works regardless of bind address, since loopback-only
  doesn't protect against another process, or another user on a
  shared/multi-user machine, reaching `127.0.0.1` on the same host.
  Generate a real random value yourself; don't use a short or guessable
  string. Not every MCP client UI exposes custom headers — check yours
  supports one before relying on this. If you connect through the bundled
  Node/Python proxy instead of a direct SSE/HTTP URL, set the same value
  as `SUBLIME_MCP_TOKEN` in the proxy process's environment.
- **`disabled_tools`** (default `[]`) — a list of tool names to refuse
  and hide from discovery entirely, e.g. `["eval_python", "run_command"]`
  to remove the two tools with the broadest reach while keeping the rest
  of the server usable.

There is no cross-origin access at all: the real tool-call endpoints send
no `Access-Control-Allow-Origin` header, so a webpage's JavaScript running
in a browser cannot reach them even if it's running on the same machine.

## Installation

### 1. Install the Sublime Text plugin

**Package Control (recommended once available):** run `Package Control:
Install Package` and search for **MCP Commander**. This package is
[submitted to Package Control](https://github.com/sublimehq/package_control_channel/pull/9554)
and awaiting merge — until it lands, use the manual path below.

**Manual (also the path for developing sublime-mcp itself):**

```bash
git clone https://github.com/dpc00/sublime-mcp.git
cd sublime-mcp
```

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

Restart Sublime Text after linking so the plugin loads.

### 2. Configure your agent

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
```

Restart or open a new Codex session after changing MCP configuration. Verify
the entire path before debugging agent behavior:

```bash
npx sublime-mcp doctor
```

The report checks the HTTP bridge, MCP handshake, and focused tool catalog.
From Sublime's Command Palette, `MCP Commander: Connection Doctor` shows the
main server-side state. (Controlling a debugger or language server doesn't
need its own MCP server or `doctor` check — see "Toolset" above and
`skills/package-skill-generator`.)

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
