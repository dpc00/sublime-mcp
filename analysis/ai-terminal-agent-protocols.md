# AI Terminal agent protocol inventory

Date inspected: 2026-08-16

Source profile file: `C:\Users\donal\projects\GhostShell\ai_terminal.sublime-settings`

Variants that only change model, provider, flags, or terminal presentation are collapsed into one agent family. Shells, the Pybackup TUI, and the testing mock are listed separately because they are not coding-agent integrations.

## Results

| Configured family | Installed version | Structured integration found | Entry point / transport | Assessment for Sublime |
|---|---:|---|---|---|
| Antigravity (`agy`) | 1.1.13 | Embedded IDE command and internal language-server architecture found; public ACP/companion contract not yet located | `agy`; internal `third_party/jetski/cortex/command/ide_command.go`; launches local HTTPS/gRPC and HTTP language-server ports | Treat as an active investigation target, not terminal-only. Its Gemini-derived lineage and embedded `/ide` implementation make an editor companion plausible, but the wire contract still needs to be established before claiming Gemini-spec compatibility or ACP. |
| Claude Code | 2.1.233 | Claude's proprietary IDE integration | `/ide`; local hidden IDE MCP connection | A Sublime companion can provide editor context and diff/diagnostic tools while Claude remains in its terminal. This is not ACP. |
| Codex | 0.147.0 | Codex app-server; ACP through the `codex-acp` adapter | `codex app-server`; adapter translates ACP to app-server | Viable for a native ACP UI, but it has one more compatibility layer than agents with a native `acp` command. `codex mcp-server` is the reverse relationship and is not an IDE-agent transport. |
| Grok Build | 1.0.4 | Native ACP agent mode | `grok agent stdio`; also `grok agent serve` over WebSocket | Strong ACP candidate; supports sessions, streamed output, tools, and permissions. |
| jcode | 0.76.0 | Native ACP adapter | `jcode acp`, JSON-RPC over stdio | Strong ACP candidate. Local help says it is backed by the jcode daemon and retains its broad provider surface. |
| Junie | 26.8.10 | Native ACP mode | `junie --acp true`, stdio | Strong ACP candidate. Junie's own `/ide` reports its JetBrains connection; it should not be confused with the Gemini companion protocol. |
| Kimi | 0.31.0 | Native ACP server | `kimi acp`, stdio | Strong ACP candidate. Local help explicitly identifies an ACP server and terminal-auth entry point. |
| Kiro | 2.16.2 | Native ACP agent | `kiro-cli acp`, JSON-RPC over stdio | Strong ACP candidate, including explicit tool-approval controls and agent/model selection. |
| Mimo | 0.1.10 | Native ACP server inherited/preserved in the OpenCode-derived CLI | `mimo acp`; also `mimo serve` | Strong ACP candidate. This was uncertain from public indexing, but the installed executable confirms it directly. |
| OpenCode | 1.18.18 | Native ACP agent; separate HTTP server | `opencode acp`, stdio; `opencode serve`, HTTP/OpenAPI | Strong ACP candidate. Mini and Ollama profiles do not alter the transport. |
| Qwen Code | 0.21.8 | Native ACP **and** Gemini-derived IDE Companion integration | `qwen --acp`, stdio; in-session `/ide`, local HTTP MCP companion | Supports both architectural directions. `--acp` is a stable hidden top-level flag rather than a subcommand, which is why ordinary `--help` initially obscured it. |
| Vibe | installed (`vibe-acp`) | Native ACP executable | `vibe-acp`, stdio | Strong ACP candidate. The dedicated adapter executable is already installed. |

## Profiles collapsed into those families

- Claude: standard, `--chrome`, Ollama, and Ollama `--chrome`.
- Codex: standard and Ollama.
- Grok Build: standard and `--minimal`.
- OpenCode: standard, `--mini`, Ollama, and Ollama `--mini`.
- Qwen: standard and Ollama.
- All other rows correspond to one configured profile each.

## Non-agent profiles

`Bash`, `Dos Console`, `PowerShell`, and `WSL Bash` are ordinary shells. `Pybackup Go TUI` is an application TUI. `Testing Agent` is a mock used to exercise terminal behavior. None belongs in an ACP or IDE-companion implementation matrix.

## The protocol directions are different

### IDE Companion / Claude `/ide`

The user continues interacting with the agent's CLI/TUI. Sublime runs a small local server that supplies structured editor state and editor actions to that external agent. This is the least disruptive extension of AI Terminal.

```text
user -> agent TUI -> Sublime companion server -> views, selections, diagnostics, diffs
```

Qwen follows the published Gemini IDE Companion design. Claude follows a similar idea through its own non-standard IDE integration. They require separate adapters behind a shared Sublime editor-service core.

### ACP

Sublime becomes the client UI. It launches the agent in protocol mode, sends prompts and permission decisions, and renders streamed messages and tool activity. This can replace terminal emulation for supported agents.

```text
user -> Sublime conversation UI -> ACP over stdio -> agent -> tools/files
```

ACP therefore does **not** mean that the editor itself uses an agent. It means a Sublime package could present the interaction currently presented by each agent's terminal UI.

## Product consequence

The settings file is unexpectedly good market evidence for ACP: Grok Build, jcode, Junie, Kimi, Kiro, Mimo, OpenCode, Qwen, and Vibe already expose a common agent transport locally. Codex can join through its adapter. One ACP client could therefore replace nine separate TUI integrations (ten with Codex), while keeping terminal profiles as a fallback.

The companion-server work remains useful and should not be discarded. It solves the inverse integration and can share its editor-facing core with ACP:

- active view, open files, selections, cursor and diagnostics;
- workspace identity and lifecycle;
- diff preview, edit application, navigation and permission UI;
- capability negotiation and adapter-specific translation.

The rational architecture is one editor-service core with two front doors:

1. an IDE Companion server for Qwen, followed by a Claude `/ide` adapter;
2. an ACP client for the nine native ACP families, followed by Codex adapter support.

Do not expand the MCP tool surface to 440 tools first. Protocol coverage, lifecycle reliability, permissions, streaming, diff review, and a small set of excellent editor primitives provide more leverage. Higher-level workflows can then be added as composed operations after transcript evidence shows repeated demand.

## Evidence notes

- Installed executable versions and help output were inspected locally on the date above.
- Mimo, jcode, Kimi, and Kiro ACP entry points were confirmed directly from local `--help` output.
- Qwen's installed package confirms both paths: `--acp` is marked stable in its bundled settings reference and its source recognizes `--acp`/deprecated `--experimental-acp`; IDE Companion support is an in-session feature.
- Antigravity's public/local top-level help exposes interactive/print operation and plugins but omits an IDE entry point. Binary inspection nevertheless found `third_party/jetski/cortex/command/ide_command.go` and embedded `references/ide.md`. A controlled `agy -p "/ide"` launch also started Antigravity's internal language server on random local HTTPS/gRPC and HTTP ports before authentication stopped the test. This invalidates a confident "terminal-only" conclusion; authentication and protocol tracing are needed to determine whether it implements the Gemini companion contract, a private Antigravity contract, or only connectivity to the Antigravity desktop IDE.
- A CLI being an MCP **client**, or offering an MCP **server** that exposes the agent as tools, is not automatically equivalent to ACP or an IDE companion.

## Primary references

- Gemini IDE Companion specification: <https://github.com/google-gemini/gemini-cli/blob/main/docs/ide-integration/ide-companion-spec.md>
- Qwen Code IDE integration: <https://github.com/QwenLM/qwen-code/blob/main/docs/users/ide-integration/ide-integration.md>
- OpenCode ACP: <https://dev.opencode.ai/docs/acp/>
- OpenCode server: <https://dev.opencode.ai/docs/server/>
- Grok Build CLI: <https://docs.x.ai/build/cli/reference>
- Grok Build agent mode: <https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/15-agent-mode.md>
- jcode IDE integration: <https://www.j-code.net/docs/overview/ide-integration>
- Junie ACP: <https://junie.jetbrains.com/docs/junie-cli-acp.html>
- Kimi CLI: <https://moonshotai.github.io/kimi-code/en/reference/kimi-command>
- Kiro ACP: <https://kiro.dev/docs/cli/acp/>
- Vibe ACP setup: <https://github.com/mistralai/mistral-vibe/blob/main/docs/acp-setup.md>
- Codex ACP adapter: <https://github.com/agentclientprotocol/codex-acp>
