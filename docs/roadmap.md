# Incremental product roadmap

Status: completed plan, 2026-08-16

This roadmap deliberately divides the work into independent parts. Complete,
verify, and document one part before beginning the next. A later part must not
be allowed to expand the scope of the current part.

The architectural rationale remains in `docs/product-direction.md`. The agent
protocol inventory is in `analysis/ai-terminal-agent-protocols.md`.

## Completed part: 1 - Validate the existing MCP product

### Objective

Demonstrate that `agy`, running in an AI Terminal tab inside Sublime Text, can
reliably use the existing `sublime-mcp`, `lsp-mcp`, and `debugger-mcp` servers
to complete a realistic workflow in a Sublime Text project.

This part improves and validates what already exists. It does not implement
ACP, an IDE Companion server, Claude `/ide`, or hundreds of new tools.

### Known baseline

- Antigravity 2.0 is a standalone agent application, distinct from the optional
  Antigravity IDE and the `agy` CLI.
- Its MCP definitions were copied from the Claude configuration.
- All three local servers connect successfully after Antigravity is reloaded
  with `Ctrl+R`.
- A transient `session not found` error after an MCP update was cleared by that
  reload; direct checks showed all three SSE endpoints were healthy.
- The user has selected the simpler real workflow: `agy` runs in Sublime AI
  Terminal Tab 2. Antigravity 2.0 is no longer the active Part 1 client.
- First `agy` test (2026-08-16): `/mcp` definitively shows `debugger-mcp`,
  `lsp-mcp`, and `sublime-mcp` registered, but all three legacy SSE connections
  fail during `initialize` with `failed to connect (session ID: ): session not
  found`. Other stdio and Streamable HTTP servers connect. Before `/mcp` was
  inspected, the model incorrectly inferred absence from an internal directory,
  called `computer-use-mcp/get_window_state` without its required `app` target,
  and attempted unrelated filesystem/HTTP fallbacks. Classification: `agy`
  1.1.13 sees the definitions but does not complete these servers' SSE session
  handshake; the same servers work in Antigravity 2.0 after reload.
- Transport follow-up (2026-08-16): all three servers already implement
  Streamable HTTP at `POST /mcp`. Direct `initialize` requests to ports 9502,
  9505, and 9506 returned HTTP 200 and the correct server identities. Their
  `serverUrl` entries were changed from `/sse` to `/mcp` and saved. After the
  `agy` tab/client was reloaded, `/mcp` showed all three servers healthy.
  `Ctrl+R` is not an `agy` CLI reload command. Streamable HTTP is therefore the
  confirmed `agy` transport; legacy SSE remains available for compatible
  clients.
- First successful `agy` MCP workflow (2026-08-16): after explicit tool names
  were supplied, `agy` called `get_active_file`, `get_selection`,
  `get_open_files`, `lsp_get_diagnostics`, and `debugger_get_all_sessions`
  through the intended three servers, with no Bash or computer-use fallback.
  Sublime calls correctly identified the active Antigravity terminal buffer,
  empty selection, and three open views. LSP returned no diagnostics while the
  terminal/plain-text view was active, so source-file diagnostics remain
  untested. Debugger returned the actionable error `Debugger package not
  loaded.` `agy` displayed calls in the requested order but said it dispatched
  them simultaneously, so strict sequencing was not honored.
- Debugger-state correction (2026-08-16): `debugger_get_all_sessions` had
  conflated a loaded Debugger package with no per-window runtime instance and a
  genuinely missing package. It now returns an empty session list with
  `status: inactive` and an accurate message in the former case, retains the
  missing-package error in the latter, and reports `status: active` with live
  sessions. Regression tests pass and a live MCP call verified the inactive
  response after plugin reload.
- Pyright cleanup (2026-08-16): fixed the two genuine
  `BaseHTTPRequestHandler.log_message` override diagnostics by matching the
  base parameter name, and replaced an obsolete/invalid relative
  `AdaptersRegistry` import with Debugger's current loaded
  `dap.AdapterConfiguration` registry. Seven relevant tests pass. Live adapter
  enumeration returns 22 adapter names, and live Pyright diagnostics now show
  only the two expected unresolved Sublime-runtime imports.
- `agy` rerun after the correction (2026-08-16): all five calls succeeded from
  the agent's perspective. With `debugger_mcp.py` open, LSP returned five
  Pyright errors and 45 hints, validating real source-file diagnostics rather
  than the earlier terminal-view empty result. `debugger_get_all_sessions`
  returned the new `{sessions: [], status: inactive, ...}` response and `agy`
  interpreted it correctly. Large MCP results were stored by `agy` in its own
  generated step-output files and reread for summarization. Calls were again
  dispatched concurrently despite the requested order.
- Invalidated workflow run (2026-08-16): retract the source-navigation and
  reversible-edit results from the immediately preceding inspection session.
  Codex MCP permission prompts changed focus to the Codex tab, while other
  operations changed focus to a Python source tab and hid the permission
  prompt. Some keystrokes and tool effects therefore landed in a different tab
  from the one assumed by the test procedure. The resulting observations cannot
  reliably distinguish `agy`, Codex permission UI, server behavior, or operator
  focus errors. None of that run counts as Part 1 acceptance evidence and its
  tentative defect classifications must be reproduced before being retained.
- Clean grid-layout rerun (2026-08-16): Codex was isolated in upper-left,
  `agy` in lower-left, and source files in upper-right. No permission-selection
  keystrokes were automated. `agy` called `lsp_get_diagnostics` with the exact
  `debugger_mcp.py` path and returned 50 Pyright diagnostics (two errors and 48
  hints), explicitly preserving LSP's zero-based coordinates. It then called
  `sublime-mcp/open_file` with the same path and one-based line 5, column 1.
  Independent inspection confirmed the selected upper-right source sheet,
  cursor `(4, 0)`, and line text `import sublime`.
- Clean reversible-edit rerun (2026-08-16): `agy` used only the path-targeted
  `str_replace_based_edit_tool` to insert `# Part 1 clean reversible edit` after
  line 3. Independent inspection found the exact marker at zero-based `(3, 0)`
  in the upper-right source buffer. A second explicit-path `str_replace` removed
  the marker. Full-buffer comparison then matched all 76,062 characters on
  disk. The buffer remains dirty because the insert and removal are retained as
  separate undoable changes, so dirty state alone is not proof of content drift.
  These rerun results replace only the corresponding invalidated navigation and
  path-targeted edit observations; claims about cursor-relative `insert` remain
  invalid and unclassified.
- Breakpoint inspection follow-up (2026-08-16): the first `agy`
  `debugger_get_breakpoints({})` call returned `Debugger package not loaded.`,
  but independent Sublime inspection found 91 loaded Debugger modules and no
  per-window instance. This exposed the same loaded-versus-inactive reporting
  defect previously fixed for sessions. `debugger_get_breakpoints` now returns
  empty source/function breakpoint lists with `status: inactive` when the
  package is loaded without a window instance, preserves the missing-package
  error, and reports `status: active` with live breakpoints. Ten relevant tests
  pass. The updated installed plugin was explicitly reloaded, and a direct live
  module call returned the corrected inactive response.
- The required `agy` confirmation call was attempted after reload but was
  blocked before completion by its `Individual quota reached` response (reset
  shown as approximately 154 hours). No breakpoint was set or removed, and the
  server-side result must not be counted as an `agy` acceptance result.
- Fallback-client decision (2026-08-16): because the `agy` quota blocks work for
  roughly 154 hours, the user authorized Grok Build for the remaining Part 1
  server/tool validation. Results are client-qualified and do not replace
  missing `agy`-specific behavior or reconnection evidence. Grok requires MCP
  names in `server__tool` form rather than `server/tool`; the slash-qualified
  first attempt was rejected by the host before reaching debugger-mcp.
- Grok breakpoint workflow (2026-08-16):
  `debugger-mcp__debugger_get_breakpoints({})` connected and confirmed the
  corrected loaded/inactive response. `debugger_open({})` created an open,
  non-running per-window Debugger instance without changing the four-pane grid.
  Live breakpoint enumeration then exposed a second defect: current Debugger
  `SourceBreakpoint` objects store condition and log message under
  `bp.dap.condition` and `bp.dap.logMessage`, not direct attributes. The
  serializer was corrected and the same ten regression tests pass.
- After removing one persisted line-1 breakpoint restored during plugin reload,
  Grok toggled an explicit breakpoint at one-based line 94 of
  `tests/test_debugger_state_reporting.py`. Independent verification found the
  live API record at line 94 and the lower-right non-agent source gutter region
  at zero-based row 93 on `test_get_breakpoints_reports_package_missing`.
  Grok removed the same breakpoint; independent verification confirmed empty
  source/function lists and no remaining gutter regions. Acceptance step 7 is
  complete for the Grok fallback client.
- Debug-session attempt (2026-08-16): a temporary named Python launch
  configuration exposed a third debugger-mcp contract defect. The generated
  `debugger_start` wrapper advertised `configuration_name` but forwarded that
  key unchanged; current Debugger expects `configuration`, so it opened an
  interactive selection panel. A subsequent inspection call stole focus and
  dismissed the panel, invalidating that attempt. The wrapper now maps named
  `start` and `open_and_start` calls to `configuration` while preserving other
  command arguments. Twelve relevant tests pass.
- After reload, the corrected Grok named-start call selected the disposable
  configuration non-interactively and reached Python adapter installation.
  No session was created because Debugger's current `PythonInstaller` expects
  `debugpy_info.json`, but the downloaded Microsoft
  `vscode-python-debugger` `v2026.6.0` tree did not contain that file. The
  Debugger Console recorded the exact missing-file error under
  `Package Storage/Debugger/debugpy.tmp`. Classification: upstream Debugger
  adapter-installer compatibility/setup failure. The temporary project
  configuration and target source were removed; the downloaded `debugpy.tmp`
  directory was left untouched. Step 8 remains incomplete.
- Python adapter recovery and completed Grok session (2026-08-16): official
  repository tag checks found that stable `v2025.18.0` contains
  `debugpy_info.json`, while stable `v2026.4.0` and the failing `v2026.6.0` do
  not. The last checked compatible prerelease was `v2025.19.10262205`; the next
  checked prerelease, `v2025.19.10550348`, lacked the file. Debugger's release
  lookup only examined the first GitHub release page and could not select the
  older stable tag by version, so its normal install/post-install pipeline was
  invoked once with the official `v2025.18.0` zipball. It installed debugpy
  1.8.19 and now reports adapter version `2025.18.0`.
- The first post-install launch selected the WindowsApps `python3.exe` alias and
  ended immediately. Pinning the disposable configuration to the actual
  Python 3.12 `python.exe` produced one live `Part 1 Disposable Python` session
  in `State.RUNNING`; the Debugger Console printed target value 42. Grok
  independently retrieved the running session and then called `debugger_stop`.
  Direct verification confirmed zero sessions and `running: false`. Temporary
  project configuration/source were removed, the one-time installer override
  was restored, and the compatible adapter remains installed. Part 1 step 8 is
  complete for the Grok fallback client.
- Grok restart/reconnection (2026-08-16): the first attempt incorrectly called
  `view.close()` directly, terminating the ConPTY instead of asking Grok to exit;
  it does not count as graceful lifecycle evidence. It did reveal a readiness
  window: the replacement initially showed MCP `10/13` and rejected a tool
  lookup until a later retry connected.
- The corrected run sent `/exit` to Grok view 67 and waited. Grok exited,
  GhostShell automatically removed the view, and its terminal registry entry
  disappeared; no manual close was required. A fresh Grok view 69 was created
  in the same lower-left group using the configured profile, preserving Codex
  and both non-agent panes. After a 20-second MCP readiness wait,
  `debugger_get_breakpoints({})` connected and returned empty breakpoint lists
  with `status: active`. Classification: graceful shutdown, automatic tab
  cleanup, fresh-process startup, and MCP reconnection all passed for Grok.
  Clients still need a readiness wait; `agy` restart evidence remains unavailable
  due quota.

### Part 1 classification and improvement synthesis

The recorded failures now have explicit classifications:

- **Server defects:** debugger session and breakpoint reads originally
  conflated a loaded-but-inactive Debugger package with a missing package;
  breakpoint serialization used obsolete direct fields.
- **Tool-contract defects:** named `debugger_start` and
  `debugger_open_and_start` advertised `configuration_name` but did not map it
  to Debugger's required `configuration` command argument.
- **Client behavior:** `agy` 1.1.13 cannot complete the legacy SSE handshake,
  tends to dispatch requested sequential reads concurrently, and exhausted its
  quota before steps 7-9. Grok has a measurable MCP startup-readiness window
  and uses `server__tool` names rather than `server/tool` names.
- **Setup/upstream compatibility problems:** the current Python-adapter release
  no longer includes the `debugpy_info.json` expected by Debugger's installer;
  the WindowsApps `python3.exe` alias was not a usable launch target.
- **Operator/procedure errors:** permission prompts and source navigation
  changed focus during the invalidated run; the first Grok restart killed the
  view before graceful client shutdown. Neither run is acceptance evidence.
- **Unsupported or unclassified behavior:** cursor-relative `insert` was not
  cleanly rerun and no conclusion is retained. Explicit-path editing is the
  verified alternative.

Evidence-backed next tool-surface improvements, in priority order:

1. Make debugger state reads consistently return structured
   `missing`/`inactive`/`active` status instead of ambiguous errors, using the
   session and breakpoint fixes as the pattern for the remaining read tools.
2. Align public MCP schemas with the Debugger command API and add contract
   tests for every wrapper that translates argument names.
3. Add adapter-install compatibility checks and an actionable failure that
   names the incompatible release/file, plus a supported way to select a known
   compatible adapter version.
4. Add a debugger launch preflight that resolves and validates the executable
   before starting, avoiding Windows application-execution aliases.
5. Expose MCP readiness/connection state, or make fresh AI-terminal clients
   wait for registered servers before accepting tool calls.
6. Prefer explicit-path, explicit-position navigation and editing contracts;
   document coordinate bases in results and reserve cursor-relative mutations
   for workflows that first verify the active view.
7. Provide a small, read-only MCP health tool so reconnection can be verified
   without invoking a domain operation.

This completes the classification and tool-surface-list criteria. Part 1 is
complete on shared-product evidence: `agy` validated steps 1-6 and Grok
validated steps 7-9 against the same Sublime, LSP, and Debugger MCP servers.
The client qualification remains important compatibility evidence, but it is
not a reason to make a server/tool upgrade depend on one agent. Repeating steps
7-9 with `agy` after its quota reset is optional compatibility coverage, not a
Part 1 completion requirement.

### Acceptance workflow

Using one real, disposable test project, ask `agy` in Sublime Tab 2 to:

1. list the Sublime windows, open views, and active view;
2. read the active buffer, including unsaved content if supported;
3. identify and explain the current selection;
4. retrieve LSP diagnostics;
5. navigate to a symbol or explicit file location;
6. make one small, reversible edit and verify the resulting buffer;
7. inspect or set a breakpoint;
8. start, inspect, or control one debugger session;
9. survive closing/restarting its AI Terminal tab and reconnect cleanly.

### Evidence to capture

- the prompt used for each step;
- tools Antigravity selected and their arguments;
- returned results and visible Sublime state;
- failures, retries, wrong-view operations, and confusing tool descriptions;
- missing operation the agent attempted to approximate;
- whether the result was independently verified after every mutation.

Prefer sanitized transcripts and small reproducible cases. Do not infer a
missing feature from one failed prompt until the tool and server logs have been
checked.

### Completion criteria

Part 1 is complete when:

- the nine-step workflow has a recorded result;
- failures have been classified as server defect, tool-contract defect,
  client behavior, setup problem, or unsupported capability;
- high-impact defects found in scope are fixed and regression-tested;
- restart/reconnection behavior is documented;
- there is an evidence-backed list of the next tool-surface improvements.

### Explicitly deferred

- installing the optional Antigravity IDE;
- reverse-engineering `agy /ide`;
- building a Sublime ACP client;
- implementing Gemini/Qwen IDE Companion support;
- implementing Claude `/ide` compatibility;
- expanding toward a 440-tool public surface;
- creating skills before workflows and APIs stabilize.

## Part 2 - Published IDE Companion vertical slice (complete)

Implement the smallest published Gemini/Qwen-compatible companion path:
discovery, authentication, workspace matching, editor context, diagnostics,
native diff review, and reconnection. Reuse the editor-state core proven in
Part 1.

Contract baseline and implementation sequence:
`docs/part2-ide-companion-contract.md`.

Completion means one compatible CLI connects through its normal `/ide`
workflow and completes a selection-to-reviewed-edit scenario.

Completed (2026-08-16): Qwen Code 0.21.8 connects through `/ide`, receives real
Sublime context, exits gracefully, and reconnects from a fresh terminal.
Dynamic discovery, bearer authentication, context notifications, native diff
accept/reject, and disconnect cleanup are live-verified; thirteen focused tests
pass. In Ask Permissions mode, Qwen's built-in `edit` tool automatically opened
the protected Sublime review. Both rejection (source preserved, Qwen edit
cancelled) and acceptance (Qwen edit completed, clean buffer and disk updated)
passed end-to-end. The explicit 75-file MCP test also passed; the companion's
ten-file recent-context cap is not a general file-operation limit.

## Paused part: 3 - ACP client prototype with one agent

Build a minimal Sublime ACP client against one native implementation, initially
OpenCode unless Part 1 or Part 2 provides evidence for a better choice. Cover
process lifecycle, initialization, one session, streamed messages, permission
requests, tool updates, cancellation, and shutdown.

Completion means one end-to-end coding task works without terminal emulation.
Do not generalize to the other agents during this part.

Paused by product decision (2026-08-16): retain the working protocol client,
tests, smoke utility, contract notes, and live OpenCode evidence because they
are useful research and already incurred development/token cost. Do not build a
general Sublime ACP conversation interface now: reproducing each CLI's richer
tools and slash-command experience would be a separate product. Resume only if
a concrete ACP-native workflow justifies that investment.

## Completed part: 4 - Claude `/ide` adapter

Establish Claude's actual contract using sanitized fixtures, then adapt the
shared editor-service core. Do not assume wire compatibility with the Gemini
IDE Companion specification.

Completion means Claude Code discovers Sublime, reads active editor context,
receives diagnostics, and performs a reviewed edit.

Contract and implementation sequence:
`docs/part4-claude-ide-contract.md`.

Milestone 1 is implemented and locally verified. Claude Code 2.1.233's lock
discovery and legacy MCP-over-SSE contract were established from the installed
client. The shared loopback server now provides a separate authenticated
Claude dispatcher, selection notifications, LSP diagnostics, and Claude's
blocking native-diff result sentinels without changing the verified Qwen `/mcp`
surface. Sixteen focused Claude/companion tests pass. Next reload the plugin
and perform a read-only live `/ide` connection check.

Read-only live acceptance now passes. Claude Code 2.1.233 discovered and
connected to Sublime, consumed an exact selected-line notification, and called
`mcp__ide__getDiagnostics` for the selected file. It received 48 Pyright
diagnostics (2 errors and 46 hints). The standard account reached its weekly
limit after connection/selection, so the completed diagnostic call used the
configured Claude Code Ollama-provider profile; this changes the model backend,
not the Claude `/ide` client or wire protocol. Installed-client inspection also
corrected the auth contract: `sse-ide` sends no auth header, while
`X-Claude-Code-Ide-Authorization` is exclusive to `ws-ide`. Next perform one
disposable native reviewed edit, then graceful restart/reconnection.

Completed (2026-08-16): in manual mode, Claude's built-in `Edit` invoked the
IDE `openDiff` tool and blocked on a native Sublime review. The proposed
`value = 42` review appeared in non-agent group 1 while Claude remained in
group 2; disk still contained `value = 41` before acceptance. Accepting the
review returned Claude's `FILE_SAVED` result and left both buffer and disk clean
at `value = 42`. The adapter was also corrected to move a newly opened source
view out of the agent group along with its review. Claude then exited through
`/exit`, GhostShell removed the terminal automatically, and a fresh Claude
process in group 2 connected through `/ide`. The disposable file and view were
removed. Part 4 is complete.

## Paused part: 5 - Additional ACP agents

Add agents individually using the protocol inventory. Each agent gets a small
compatibility record and the same acceptance suite before it is declared
supported. Current candidates include Grok Build, jcode, Junie, Kimi, Kiro,
Mimo, Qwen, Vibe, and Codex through its adapter.

Paused with Part 3: do not add more ACP agents while there is no product
decision to build the general Sublime ACP conversation interface.

## Completed part: 6 - Optional Antigravity IDE and `agy /ide` research

Install the optional Antigravity IDE only if direct `agy` editor integration is
still a product priority and public documentation remains insufficient. Capture
discovery, environment, transport, authentication, editor context, and diff
behavior without copying proprietary implementation code.

This research is not required for Antigravity 2.0, which already consumes the
three Sublime MCP servers directly.

Completed as a bounded unsupported-path result (2026-08-16): the installed
Antigravity IDE is a VS Code fork with a bundled extension that spawns its own
private language-server child. The observed running instance used an ephemeral
Windows named pipe, dynamic loopback ports, per-process CSRF values, and a
one-shot stdin credential handshake. No public discovery record or supported
command for attaching the separately installed `agy` CLI to that already
running IDE was established. Sensitive runtime values captured by the IDE
agent were deliberately not retained here and became invalid when the IDE was
closed; process inspection confirms no Antigravity IDE process remains.

This does not mean `agy` lacks all internal IDE machinery. Earlier installed-
binary evidence found an internal `ide_command.go` path, and a controlled
`agy -p "/ide"` invocation started `agy`'s own language-server services before
authentication stopped the test. The evidence supports a narrower conclusion:
the installed versions do not expose a verified user-facing path for attaching
`agy` to the separate running Antigravity IDE. Sublime integration remains the
working shared MCP path: Antigravity IDE, `agy`, and other clients can consume
`sublime-mcp`, `lsp-mcp`, and `debugger-mcp` without an IDE-process attachment.

The IDE was closed after inspection, and the temporary Sublime scratch/output
tabs created by its agent were closed by the user. No further Antigravity IDE,
SDK-wrapper, ACP UI, or attachment work is required by this roadmap.

## Working rule for future sessions

At the start of a session, read this file and work only on the current part.
Update the known baseline and evidence as results arrive. Move the `Current
part` marker only after its completion criteria are satisfied. New ideas go in
the deferred or later-parts sections rather than expanding active scope.
