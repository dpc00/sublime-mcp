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

Eight workflow tools are advertised by default (`discover_tools`, `batch`,
`get_help`, `get_active_file`, `project_search`, `save_file`,
`str_replace_based_edit_tool`, `ui_screenshot`). `discover_tools` lists a tree of
categories (`category=`) or searches (`query=`) the
complete internal catalog of 411 typed Sublime capabilities, and `batch` invokes
discovered capabilities without flooding the model's initial tool context.

Since 1.9.0, 160 of those tools are generated wrappers named after Sublime Text's
own commands (`tools/generate_st_command_tools.py`, data in
`tools/st_commands_metadata.json`); what each was observed to do on a bare
Sublime Text 4215 is in `tools/st_commands_behavior.json`, and the hand-written
tools' behaviour is in `tools/st_hand_written_behavior.json`. Since 1.10.0,
`list_native_windows` and `dismiss_native_window` (Windows) list and dismiss a
native dialog or menu while it blocks Sublime's main thread. See
[AGENT_GUIDE.md](AGENT_GUIDE.md).

### What it can do now (1.10 to 1.13)

- **See and operate Sublime's own windows (Windows only, 1.13).** `ui_screenshot`
  returns a real image of any Sublime window, also one behind others, an open
  dialog or menu (`kind`, `window_title`), a not-front tab (`tab`), cropped or
  zoomed (`region`, `scale`, `max_width`); it is one of the eight default tools,
  and the image reaches the client as an image, also through `batch` and the
  proxies. `ui_press_key`, `ui_type_text`, `ui_click` and `ui_hover` (with a
  picture of the popup, including language-server hovers) operate palettes,
  quick panels and menus. Real mouse and keys wait until the person at the
  computer has been idle (`wait_idle_s`), so they never type over them.
- **Work through native dialogs (1.10, 1.12.4).** `list_native_windows` and
  `dismiss_native_window` list and dismiss a dialog or menu that has blocked
  Sublime's main thread; `close_file` with `discard` closes a tab with unsaved
  edits without the Save Changes dialog.
- **Drive quick panels and menus (1.12).** `get_quick_panel`, `pick_quick_panel`
  (with `wait_ms` for a list that is still loading) and `click_menu_item`;
  `install_package` now persists the install, `get_view_regions` and
  `get_view_phantoms` (with `last`, `html`, `max_chars`) inspect what a plugin drew.
- **Share one Sublime between agents (1.12.0).** `claim_resource`,
  `release_resource` and `list_claims` let agents take turns on the input and
  control panels.
- **Safer by default.** Browser-origin requests are refused (1.12.2), the
  visible-console read only touches Sublime's own window and restores focus and
  clipboard (1.12.1), `eval_python` cannot take down the plugin host with
  `sys.exit()` (1.12.3), and Windows-only tools are hidden on other platforms
  (1.11.2).
- **A tool tree (1.11).** `discover_tools` with no arguments walks 12 categories
  instead of dumping a catalog.

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

Browsers are kept out in two ways. The real tool-call endpoints send no
`Access-Control-Allow-Origin` header, and, because a missing CORS header does
not stop a request from being sent, with no `auth_token` and the default
loopback bind they also refuse any request whose `Origin` or `Host` header
names something other than loopback (including `Origin: null`). Command-line and desktop MCP clients send no `Origin` and are
not affected. This does not protect against another process on the same
machine: set `auth_token` for that.

## Installation

### 1. Install the Sublime Text plugin

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

Point your agent straight at the server the plugin starts inside Sublime Text.
No helper program is needed. Use the streamable-HTTP URL if your client
supports it (Codex example; no `mcp-remote` wrapper is required):

```toml
[mcp_servers.sublime-mcp]
type = "http"
url = "http://127.0.0.1:9502/mcp"
```

**Optional proxies.** Only for clients that cannot connect to a URL directly,
a small Node or Python proxy can sit in between:

```bash
cd packages/node-proxy && npm install . && npx sublime-mcp      # Node
cd packages/python-proxy && pip install . && sublime-mcp        # Python
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

The MCP server starts automatically when ST loads the plugin. To stop or
restart it, run "MCP Commander: Server Status" from the Command
Palette. Check View > Show Console for startup confirmation.

## Agent skill

Two skills ship with sublime-mcp: `skills/sublime-mcp` (how an agent uses the
tools) and `skills/package-skill-generator` (how to generate a small skill for
any Sublime package you use, such as a language server or a debugger). Copy the
directories to your agent's skills directory or install them through your normal
skill workflow. Skills for individual packages are not shipped: generate your own
with the generator.
