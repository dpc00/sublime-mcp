# Part 4: Claude `/ide` contract

Status: complete, 2026-08-16

## Evidence baseline

The installed client is Claude Code 2.1.233. Its `--help` documents `--ide` as
automatic connection when exactly one valid IDE is available. Current official
Claude Code IDE documentation describes supported integrations but does not
publish this local wire contract, so the details below were established by
narrow inspection of the installed executable. No proprietary source code is
copied into this repository.

## Discovery

Claude scans `<config>/.claude/ide/*.lock` (normally `~/.claude/ide`). A lock
file is named `<port>.lock` and contains:

```json
{
  "workspaceFolders": ["C:\\absolute\\workspace"],
  "pid": 1234,
  "ideName": "Sublime Text",
  "transport": "sse",
  "runningInWindows": true,
  "authToken": "opaque-secret"
}
```

The client checks workspace relevance, port reachability, and the recorded
process. `CLAUDE_CODE_SSE_PORT` can select the matching record. Sublime removes
same-process stale locks before atomically publishing its current record.

## Transport and authentication

- `transport: "sse"` maps to `http://127.0.0.1:<port>/sse`.
- `GET /sse` is legacy MCP SSE and first announces
  `/messages?sessionId=<uuid>` as an `endpoint` event.
- JSON-RPC requests are posted to that session endpoint; responses and server
  notifications arrive over the SSE stream.
- In Claude Code 2.1.233, `sse-ide` sends no auth header even when the lock
  contains `authToken`; the custom `X-Claude-Code-Ide-Authorization` header is
  used only by `ws-ide`. The SSE server is loopback-only and POST requests are
  gated by the announced random session ID. Qwen/Gemini `/mcp` remains bearer
  protected.
- The existing Qwen/Gemini `/mcp` transport and dispatcher remain separate.

## Observed Claude surface

- Notification `ide_connected` with Claude's PID after connection.
- Notification `selection_changed` with `filePath`, `text`, and a zero-based
  LSP-style `selection.start/end` (`line`, `character`).
- Notification `at_mentioned` with a file path and optional line bounds.
- Tool `getDiagnostics`, optionally passed `{ "uri": "file://..." }`. It
  returns one text content item containing a JSON array of
  `{ "uri", "diagnostics" }` records.
- Tool `openDiff` arguments are `old_file_path`, `new_file_path`,
  `new_file_contents`, and `tab_name`.
- Tool `close_tab` accepts `tab_name`.

Claude waits for `openDiff` to finish. The observed result sentinels are:

- accepted/saved: text `FILE_SAVED`, followed by a text item containing the
  accepted file contents;
- rejected: text `DIFF_REJECTED`;
- closed: text `TAB_CLOSED`.

## Implementation milestones

1. Complete: atomic discovery, loopback legacy SSE, separate Claude MCP
   dispatcher, selection notifications, LSP diagnostic conversion, and native
   reviewed-diff result mapping.
2. Complete: Claude Code 2.1.233 connected through `/ide`. The standard Claude
   account hit its weekly limit after receiving the selected-line attachment,
   so a configured Claude Code Ollama-provider profile completed the same
   protocol check. It reported the exact selected text and zero-based range,
   invoked `mcp__ide__getDiagnostics`, and received 48 Pyright diagnostics
   (2 errors, 46 hints) for the explicit source URI. No file was opened or
   changed by the test.
3. Complete: manual mode caused Claude's built-in `Edit` to call `openDiff`.
   The native review was independently verified in non-agent group 1 with disk
   unchanged until acceptance. Acceptance returned `FILE_SAVED` and produced a
   clean source buffer and disk. The adapter now moves newly opened source
   views out of agent groups as well as placing reviews there.
4. Complete: `/exit` removed the Claude terminal before recreation. A fresh
   Claude process in group 2 reconnected through `/ide` to the sole companion
   server. The disposable file and view were removed.

## Safety rules

- Keep Claude in an agent pane and source/review views in non-agent panes.
- Do not automate permission choices or assume focus after an editor action.
- For shutdown, send `/exit` and wait for explicit completion/process death
  before closing a leftover terminal view.
