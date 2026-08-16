# Part 2 IDE Companion contract

Status: contract baseline, 2026-08-16

## Product boundary

Part 2 adds one shared Sublime Text IDE Companion implementation for published
Gemini CLI and Qwen Code clients. It is not tied to either model or agent. Any
client that implements the published companion contract should be able to use
the same server, with discovery-file adapters where client conventions differ.

Primary specifications:

- Gemini CLI:
  <https://github.com/google-gemini/gemini-cli/blob/main/docs/ide-integration/ide-companion-spec.md>
- Qwen Code:
  <https://github.com/QwenLM/qwen-code/blob/main/docs/users/ide-integration/ide-companion-spec.md>

## Shared wire contract

| Concern | Required behavior |
| --- | --- |
| Transport | A valid MCP server over loopback HTTP, using one endpoint such as `/mcp` |
| Port | Bind dynamically by requesting port `0` |
| Authentication | Generate a unique secret and require `Authorization: Bearer <token>` on every request |
| Workspace identity | Publish absolute open workspace roots using the OS path separator; the CLI rejects a CWD outside them |
| Context | Push `ide/contextUpdate` notifications when disk-backed files open, close, or focus, or when cursor/selection changes |
| Coordinates | Cursor line and character are both 1-based |
| Context limits | Prefer at most 10 recent files and 16 KiB selected text; virtual/untitled buffers are excluded |
| Diff tools | Expose `openDiff(filePath, newContent)` and `closeDiff(filePath)` |
| Diff result | Send `ide/diffAccepted` with final content or `ide/diffRejected` with the path |
| Lifecycle | Start server and create discovery record on activation; stop server and remove the record on deactivation |

Diagnostics are not present in the published shared `IdeContext` shape. They
remain a Part 2 product requirement, but should be layered as a separate
capability using the existing LSP core rather than inserted into the standard
context notification without evidence.

## Discovery adapters

### Gemini CLI

- Directory: `os.tmpdir()/gemini/ide/`
- Filename: `gemini-ide-server-${PID}-${PORT}.json`
- Required fields: `port`, `workspacePath`, `authToken`, and `ideInfo` with
  `name` and `displayName`
- Recommended integrated-terminal hint:
  `GEMINI_CLI_IDE_SERVER_PORT=<port>` for same-workspace window tie-breaking
- Optional client-side PID override: `GEMINI_CLI_IDE_PID`

### Qwen Code

Published documentation uses a lock file under `~/.qwen/ide/` with `port`,
`workspacePath`, `authToken`, `ppid`, and `ideName`. Before implementing this
adapter, verify its exact filename convention and authentication header from
the current primary specification or client tests. Do not assume the Gemini
filename or directory.

## Smallest vertical slice

Implement and validate in this order:

1. A transport-independent editor-state core for workspace roots, recent
   disk-backed files, active cursor, and selected text.
2. A dynamic-port loopback MCP server with strict bearer authentication and a
   read-only health/status path suitable for tests.
3. Gemini discovery-record creation, atomic replacement, stale-record cleanup,
   and deactivation cleanup.
4. A real Gemini CLI `/ide status` connection in the current Sublime project,
   followed by focus/cursor/selection context verification.
5. Native reviewed diff state and the `openDiff`/`closeDiff` tools, including
   accept/reject notifications and recovery after disconnect.
6. Diagnostics as a separately identified extension backed by the existing LSP
   implementation.
7. Qwen discovery adapter and the same acceptance scenario, reusing all shared
   server, state, and diff code.

## First implementation milestone

The first code milestone stops after item 3: Sublime starts an authenticated
dynamic-port MCP endpoint, publishes a valid Gemini discovery record for the
window/workspace, rejects missing or incorrect bearer tokens, and removes its
record cleanly. This establishes discovery, authentication, workspace matching,
and lifecycle before editor events or diff UI add asynchronous complexity.

Tests must not depend on a live CLI. Cover token validation, workspace
serialization on Windows, discovery filename/content, atomic cleanup, stale
record handling, and repeated start/stop. A live Gemini CLI connection is the
milestone's final integration check.

## Milestone 1 result

Implemented on 2026-08-16 in `packages/st-plugin/ide_companion.py` and wired
into `sublime_mcp.py` lifecycle. Five isolated tests cover workspace
serialization, discovery publication/stale cleanup, idempotent removal,
strict bearer authentication, MCP dispatch, and repeated server start/stop.

Live Sublime verification found an authenticated server on dynamic loopback
port 57697 and the correctly named record
`gemini-ide-server-3776-57697.json`. The record contained the open Windows
workspace roots, Sublime identity, and a generated 43-character token. A POST
without the token returned HTTP 401; an authenticated MCP `initialize`
returned HTTP 200 with `sublime-mcp` server identity.

Gemini CLI 0.55.1 initially rejected three obsolete `serverUrl` entries in
its user settings. They were backed up and migrated to the documented
Streamable HTTP `httpUrl` form. The subsequent read-only `/ide status` check
did not reach IDE discovery: Gemini authentication returned
`IneligibleTierError` because the individual Code Assist client tier is no
longer supported and directed the user to Antigravity. Classify this as an
external client/account eligibility blocker, not a companion failure.

Continue implementation with the editor-context core. Live acceptance may use
Qwen Code or another contract-compatible client; Gemini can be retried if an
eligible authentication path becomes available.

## Milestone 2 result: editor context

The companion now supports authenticated `GET /mcp` SSE streams for
server-to-client notifications and validates any supplied `Origin` as
loopback-only. The state core tracks focus timestamps, excludes virtual and
untitled buffers, converts cursor coordinates to 1-based values, caps selected
text at 16 KiB without splitting UTF-8 characters, and publishes at most the
ten most recent disk-backed files. Sublime open/focus/save/close/selection
events are debounced by 50 ms and a fresh snapshot is sent when a client
subscribes.

Nine focused tests pass. A live authenticated subscriber received
`ide/contextUpdate` over SSE with positive timestamps and three disk-backed
files; the currently focused virtual Codex terminal was correctly excluded.

The ten-file bound applies only to the automatically pushed IDE context packet,
as specified by Gemini's companion contract. It does not limit explicit MCP
file enumeration or operations: the existing product has separately handled a
75-file test, and that capability remains unchanged.

Next implement the native reviewed-diff state and `openDiff`/`closeDiff`
contract, including explicit accept/reject notifications and disconnect-safe
cleanup.

## Milestone 3 result: native reviewed diffs

The IDE Companion dispatcher is now isolated from the general Sublime MCP
catalog and advertises exactly `openDiff` and `closeDiff`. `openDiff` creates an
editable scratch review buffer using Sublime's native incremental-diff
reference document, preferentially places it in a non-active group already
used for source files, and leaves the original buffer unchanged until explicit
acceptance. Command Palette actions accept or reject the active review.

Acceptance copies the user-reviewed final content into the original buffer and
sends `ide/diffAccepted` with the path and content. Rejection or manual review
closure leaves the original untouched and sends `ide/diffRejected`. The
`closeDiff` tool returns the review buffer's final content and closes it without
a save prompt.

Thirteen focused tests pass. Live reject verification opened the review in
non-agent group 1 while the source remained in group 3, preserved the original
byte-for-byte, cleared review state, and delivered `ide/diffRejected`. Live
accept verification used identical final content to avoid source drift,
cleared state, and delivered `ide/diffAccepted` with matching path and content.
An authenticated HTTP `tools/list` returned only `openDiff` and `closeDiff`.

Disconnect-safe cleanup is now implemented and live-verified: closing the last
authenticated SSE connection rejects and closes its orphaned review while
leaving the source unchanged.

## Qwen Code live compatibility result

Qwen Code 0.21.8 connected through its normal `/ide enable` workflow using the
shared companion. Its installed implementation requires an `ideInfo`
compatibility field in addition to the documented `ideName`; the Qwen discovery
adapter publishes both without changing the shared server or editor-state core.
`/ide status` reported the real Sublime open-file context.

Graceful lifecycle validation also passed. Qwen received `/exit`, its PTY was
confirmed dead before the terminal view was recreated, and a fresh Qwen process
immediately reconnected and again reported the live Sublime file context.

The client-driven reviewed-edit scenario is now live-verified. In Ask
Permissions mode, Qwen's built-in `edit` tool automatically invoked the
companion's non-model-facing `openDiff`. Sublime opened the protected review in
a non-agent group. Rejecting it delivered `ide/diffRejected`, cancelled the
Qwen edit, and preserved the original on disk. A second edit opened another
native review; accepting it delivered `ide/diffAccepted`, Qwen completed the
built-in edit, and both the clean source buffer and disk contained the accepted
content. A final accepted review restored the disposable target before cleanup.
This completes the published end-to-end acceptance requirement.

Diagnostics remain separate from the published companion context contract and
are already available alongside it through the existing `lsp-mcp` server. Do
not invent a non-standard `IdeContext` diagnostics field without client
evidence.
