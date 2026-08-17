# Session handoff

Updated: 2026-08-17

## Resume instruction

Read `docs/roadmap.md`, then this file. Part 1 is complete on shared-product,
mixed-client evidence. Continue only Part 2 of the roadmap. Do not reopen ACP,
Claude `/ide`, or Antigravity IDE research during Part 2.

## Recent code review (for agents)

A full static review of recent `main` work (~2026-07-25 → 2026-08-16) is in
`docs/code-review-2026-08-17.md`. Use it for security/concurrency/test gaps
(companion auth, bind defaults, openDiff timeouts, proxy timeouts). It is a
review snapshot, not live workflow state — prefer this handoff for Part 1/2
runtime status.

## Current operating setup

- Codex runs in one Sublime AI Terminal tab.
- `agy` 1.1.13 runs in the Sublime tab named `Antigravity`.
- The practical test client is `agy`, not the Antigravity 2.0 desktop app.
- `sublime-mcp`, `lsp-mcp`, and `debugger-mcp` are registered globally in
  `C:\Users\donal\.gemini\config\mcp_config.json`.
- For `agy`, their `serverUrl` values must use Streamable HTTP:
  - `http://127.0.0.1:9502/mcp`
  - `http://127.0.0.1:9505/mcp`
  - `http://127.0.0.1:9506/mcp`
- Legacy `/sse` remains implemented and works with Antigravity 2.0, but `agy`
  lost the SSE session ID during initialization.
- `Ctrl+R` is not an `agy` CLI reload command. Reload/recreate its terminal tab
  after MCP configuration changes.

## Verified live behavior

Direct MCP `initialize` requests to all three `/mcp` endpoints returned HTTP
200 with the correct server identity. In `agy`, `/mcp` then showed all three
healthy.

`agy` successfully called:

- `sublime-mcp/get_active_file`
- `sublime-mcp/get_selection`
- `sublime-mcp/get_open_files`
- `lsp-mcp/lsp_get_diagnostics`
- `debugger-mcp/debugger_get_all_sessions`

It correctly read the active AI Terminal view, selection, open views, and real
Pyright diagnostics. It tends to dispatch independent calls concurrently even
when told to call them in order. Large results may be written to and reread from
its own `.system_generated/steps/.../output.txt` files.

## Fixes completed

In `packages/debugger-mcp/debugger_mcp.py`:

1. `debugger_get_all_sessions` now distinguishes:
   - package missing: error;
   - package loaded but no per-window instance: empty sessions and
     `status: inactive`;
   - active Debugger: sessions and `status: active`.
2. Both `BaseHTTPRequestHandler.log_message` overrides now use the compatible
   `format` parameter name.
3. Obsolete `AdaptersRegistry` import was replaced with the current loaded
   `Debugger.modules.dap.AdapterConfiguration` registry.

Regression coverage is in `tests/test_debugger_state_reporting.py`.

Last relevant test command:

```powershell
pytest -q tests\test_debugger_state_reporting.py tests\test_debugger_lsp_help.py
```

Result: 7 passed. Pytest emitted only a sandbox-related cache-write warning.

Live verification after plugin reload:

- `debugger_get_all_sessions` returned inactive status accurately.
- `debugger_get_adapters` returned 22 adapter names.
- Pyright errors for `debugger_mcp.py` dropped from five to the two expected
  unresolved embedded-runtime imports: `sublime` and `sublime_plugin`.

## How to send input to the AI Terminal correctly

Do not use `sublime-mcp/send_to_view`; it performs ordinary buffer insertion.
Find the view named `Antigravity`, focus it, and invoke its commands:

```python
window.focus_view(target)
target.run_command("ai_terminal_send_string", {"string": prompt})
target.run_command("ai_terminal_keypress", {"key": "enter"})
```

Sending the literal string `"\\r"` prints `\r`; it does not press Enter.

## Next step

The immediately preceding source-navigation and reversible-edit session is
invalid and must not be treated as acceptance evidence. Codex MCP permission
prompts diverted focus to the Codex tab; source-opening operations could then
move focus to a Python tab and hide the pending permission prompt. Keystrokes,
tool calls, and verification reads were consequently performed against tabs
whose identity was not reliably controlled. Tentative conclusions about
`lsp_open_location`, LSP coordinate interpretation, cursor-relative `insert`,
and the path-targeted editor must all be reproduced before they are accepted.

Before rerunning, establish a layout with separately visible, non-overlapping
surfaces for: (1) Codex and its permission prompt, (2) the `agy` Antigravity
terminal, and (3) the source editor. If Sublime cannot keep all three visible,
use a procedure that pauses after every permission request and requires manual
confirmation of the focused view before any keypress. Do not automate a prompt
selection and an Enter keypress as a pair.

Then restart at the recorded source-navigation checkpoint: focus a real Python
view, retrieve diagnostics for its explicit path, navigate to one diagnostic or
named symbol, and independently verify the exact view and cursor. Only after
that clean run should the reversible edit be repeated. Breakpoint testing is
again deferred until these steps are valid.

## Clean rerun result

The three-surface grid rerun completed the invalidated checkpoints without
automated permission keystrokes. `agy` retrieved 50 diagnostics for the exact
`debugger_mcp.py` path and correctly treated LSP line 4 as zero-based. Its
explicit `open_file` call targeted one-based line 5, column 1; independent
inspection confirmed the selected upper-right source sheet at `(4, 0)` on
`import sublime`.

The path-targeted reversible edit also passed. The marker was independently
observed at `(3, 0)`, then removed with an exact path-targeted replacement. The
entire 76,062-character buffer matched the on-disk file afterward. The source
still reports dirty because the edit and revert are separate undoable buffer
operations. The earlier cursor-relative `insert` observation was not rerun and
must not be classified from the invalid session.

Next, continue with Part 1 acceptance step 7: inspect existing breakpoints,
then set one harmless breakpoint at an explicit source file and line. Verify it
independently before removing it or retaining it for the debugger-session test.
Keep the same three-surface grid and do not automate permission keystrokes.

Layout rule: reserve agent tabs/groups for Codex and `agy`. Whenever a source
file is opened or focused, explicitly place it in a non-agent tab/group; never
replace or cover either agent surface with a source file. In the current
four-tab grid, preserve all four panes and verify the target group before any
source navigation or mutation.

## Breakpoint checkpoint

The first clean-grid `agy` call to `debugger_get_breakpoints({})` incorrectly
returned `Debugger package not loaded.` Independent Sublime inspection showed
91 Debugger modules loaded but no per-window Debugger instance. The breakpoint
read path was fixed to distinguish package missing, loaded/inactive, and active
states, matching the session-state behavior. Ten relevant tests pass. The
installed plugin was updated and explicitly reloaded; a direct live module call
returned empty breakpoint lists with `status: inactive`.

The post-fix `agy` confirmation did not run: `agy` stopped with `Individual
quota reached` and displayed a reset interval of about 154 hours. Do not count
the direct module result as `agy` acceptance evidence. Once quota is available,
rerun exactly `debugger_get_breakpoints({})` in the lower-left agent pane. Only
after it returns the corrected inactive state should Debugger be explicitly
opened and a harmless breakpoint set, independently verified, and removed.

## Grok fallback and completed breakpoint test

The user authorized Grok Build as the fallback because waiting roughly 154
hours for `agy` is impractical. Keep all evidence client-qualified: Grok results
validate the MCP servers and tool contracts but do not prove `agy`-specific
behavior. Grok's MCP host requires `server__tool` names.

Grok confirmed the corrected inactive breakpoint response, explicitly opened
Debugger, and left the four-pane layout intact. Live breakpoint enumeration
then exposed and prompted a fix for current Debugger API fields: source
breakpoint condition and log message are `bp.dap.condition` and
`bp.dap.logMessage`. Ten relevant tests pass.

One persisted line-1 breakpoint restored during plugin reload was inspected and
removed. Grok then set an explicit breakpoint at one-based line 94 of
`tests/test_debugger_state_reporting.py`. Independent verification confirmed
the API record at line 94 and its gutter marker at zero-based row 93 in the
lower-right non-agent source pane. Grok removed it, after which both breakpoint
lists and gutter regions were empty. Part 1 acceptance step 7 is complete for
Grok.

Next, continue Part 1 step 8 with Grok: inspect available debugger
configurations, choose or create a minimal disposable Python configuration,
start one session, inspect its state, and stop it cleanly. Preserve the
four-pane grid and place any source file in a non-agent pane. Do not claim this
as `agy` session-control evidence.

## Debug-session blocker

The first named `debugger_start` attempt opened an input panel because the MCP
wrapper forwarded `configuration_name`, whereas current Debugger's start action
requires `configuration`. A later read stole focus and dismissed that panel, so
the attempt is invalid. The wrapper now maps named `start` and
`open_and_start` calls correctly; twelve relevant tests pass.

The corrected Grok call selected `Part 1 Disposable Python` without a selection
panel and reached adapter installation, but created no session. The Debugger
Console showed:

`Failed: [Errno 2] No such file or directory: ...\\Debugger\\debugpy.tmp/debugpy_info.json`

Debugger downloaded Microsoft `vscode-python-debugger` tag `v2026.6.0`; the
extracted tree lacks the `debugpy_info.json` file expected by Debugger's current
`PythonInstaller`. Treat this as an upstream adapter-installer compatibility or
setup failure, not MCP success. The temporary project configuration and Python
target were removed, and live configuration/session lists are empty. The
incomplete `debugpy.tmp` download remains in Package Storage and was not
deleted.

Next decide on a safe adapter path before retrying step 8: repair/pin Debugger's
Python adapter installer, install a compatible adapter by an approved method,
or choose another already installed adapter if one becomes available. Do not
use an interactive configuration panel; pause and instruct the user before any
UI that requires input.

## Adapter recovery and successful Grok session

The adapter blocker was resolved by pinning an earlier official release.
Repository tag checks established that stable `v2025.18.0` still contains
`debugpy_info.json`; stable `v2026.4.0` and `v2026.6.0` do not. The last checked
compatible prerelease was `v2025.19.10262205`, with the file absent by
`v2025.19.10550348`. Debugger's installer could not find the older stable tag
because it only inspected the first GitHub release page, so the normal
install/post-install pipeline was invoked once with the official
`v2025.18.0` zipball. It installed debugpy 1.8.19 and reports version
`2025.18.0`.

The first launch then chose the WindowsApps `python3.exe` alias and exited.
Pinning the disposable configuration to the working Python 3.12 `python.exe`
fixed that setup issue. A live session named `Part 1 Disposable Python` reached
`State.RUNNING`, printed `part1 debugger target: 42`, was inspected by Grok,
and was stopped by Grok. Independent verification found zero sessions and
`running: false`. The temporary configuration and target were removed, and the
one-time installer method override was restored. The installed adapter remains.
Part 1 step 8 is complete for Grok, not `agy`.

Next perform Part 1 step 9 with the available fallback client: close/restart its
AI Terminal tab, confirm the four-pane layout is restored, and verify MCP
reconnection with one read-only call. Preserve client qualification; `agy`
restart evidence remains unavailable while its quota is exhausted.

## Grok restart/reconnection result

The first Grok restart attempt was procedurally invalid because it called
`view.close()` directly and killed the ConPTY. Do not repeat that sequence. The
required lifecycle is: send `/exit`, wait for the process to end, confirm
GhostShell removes the view/terminal registry entry, and call `view.close()`
only if a dead view remains.

The corrected run sent `/exit` to view 67. Grok exited, the view disappeared
automatically, and no terminal registry entry remained. A fresh Grok view 69
was then created in lower-left group 2 with the configured profile; Codex and
both non-agent panes were preserved. After waiting 20 seconds for MCP startup,
`debugger-mcp__debugger_get_breakpoints({})` connected and returned empty
source/function lists with `status: active`. Step 9 passes for Grok with a
documented readiness delay. `agy` restart remains untested because of quota.

Shutdown timing rule: `/exit` is asynchronous. Some agents first print
`shutting down...`, continue cleanup for several seconds, and only then emit a
resume command line. Do not close or recreate the view merely because the first
shutdown message appeared or because a fixed sleep elapsed. Wait for an explicit
resume command/final exit output when the client provides one, or independently
confirm that the child process is no longer alive and its GhostShell terminal
registry entry is gone. Only then close a leftover dead view or create its
replacement.

## Part 1 completion decision

Failure classification and the evidence-backed tool-surface improvement list
are now recorded in `docs/roadmap.md`. No additional Grok exploration is
needed; its remaining quota was reported as 17%, resetting on 2026-08-20.

Part 1 is complete. The product under validation is the shared Sublime MCP
tooling, not an agent-specific upgrade. `agy` validated steps 1-6 and Grok
validated steps 7-9 against the same servers. Their different transport,
tool-name, readiness, lifecycle, and quota behavior remains client-qualified
compatibility evidence rather than a shared-product completion blocker.

After the `agy` quota resets, the following sequence may be run as optional
client-compatibility coverage, but it must not block Part 2:

1. In the lower-left `agy` pane, call
   `debugger-mcp/debugger_get_breakpoints({})` and confirm the corrected
   structured active or inactive response.
2. Recreate the disposable Python configuration with the pinned real Python
   3.12 executable, start it by name, inspect the running session, and stop it.
   Independently verify the live and stopped states; remove the temporary
   configuration and target afterward.
3. Send `/exit`, wait for explicit completion or independently verified process
   and registry removal, recreate the `agy` terminal in the same pane, wait for
   MCP readiness, and make one read-only breakpoint call.

Do not repeat diagnostics, navigation, editing, adapter research, or Grok
tests merely to duplicate the shared-product evidence.

## Current Part 2 next step

Begin the published Gemini/Qwen-compatible IDE Companion vertical slice with
contract discovery and a smallest-end-to-end design: discovery,
authentication, workspace matching, editor context, diagnostics, native diff
review, and reconnection. Reuse the editor-state core proven in Part 1 and do
not expand the work into ACP, Claude `/ide`, or a broad tool-surface project.

The initial contract discovery is recorded in
`docs/part2-ide-companion-contract.md`. Continue with its first implementation
milestone: a dynamic-port loopback MCP endpoint, strict bearer validation, and
Gemini discovery-record lifecycle. Keep Qwen's discovery filename as an open
verification item; share the server and editor-state core rather than creating
agent-specific implementations.

Milestone 1 is now implemented and locally/live verified: dynamic loopback
port, bearer rejection/acceptance, discovery file, environment hint, and
plugin lifecycle all work. Gemini CLI 0.55.1 cannot provide the final client
check under the current account because it exits with `IneligibleTierError`
before IDE discovery. Continue with the editor-context core and use Qwen or
another compatible client for live acceptance if available.

Milestone 2 is also implemented and live-verified. The authenticated SSE stream
delivers debounced `ide/contextUpdate` notifications containing recent
disk-backed files, 1-based cursor/selection context, and real focus timestamps;
virtual agent terminals are excluded. Nine focused tests pass. The ten-file
automatic-context limit does not affect explicit MCP operations, including the
recorded 75-file test. Continue with native reviewed-diff state and the
`openDiff`/`closeDiff` contract.

Milestone 3 is implemented and live-verified. The authenticated companion
advertises only `openDiff` and `closeDiff`; native scratch review buffers use
Sublime incremental diffs and are placed in non-agent source groups. Both
accept and reject notifications were observed over SSE, original content was
independently verified unchanged in the disposable checks, and eleven focused
tests pass. Continue with disconnect-safe review cleanup, the separate
diagnostics capability, and compatible-client reconnection validation.

Disconnect-safe orphan cleanup and the Qwen discovery adapter are now complete;
thirteen focused tests pass. Qwen Code 0.21.8 connected through `/ide`, reported
real Sublime context, exited gracefully, and reconnected from a fresh terminal
process. The installed client needed both documented `ideName` and the
implementation-compatible `ideInfo` lock-file fields.

Part 2 client acceptance is complete. A clean Qwen 0.21.8 session was placed in
Ask Permissions mode and used its built-in `edit` tool. Qwen automatically
invoked the companion's non-model-facing `openDiff`; Sublime opened protected
native reviews in non-agent groups. The rejection branch cancelled Qwen's edit
and preserved disk, while the acceptance branch delivered `ide/diffAccepted`,
allowed Qwen to complete the edit, and left disk plus the source buffer clean
with the accepted content. A final accepted review restored the disposable
target before it was removed. Diagnostics remain standards-compliant through
the existing parallel `lsp-mcp` capability rather than a fabricated companion
context field. Continue with Part 3 of `docs/roadmap.md`.

Part 3 milestones 1 and 2 are now complete. `packages/st-plugin/acp_client.py`
owns an OpenCode ACP subprocess and implements NDJSON JSON-RPC request
correlation, notifications, agent-to-client requests, EOF handling,
`session/cancel`, configuration changes, and shutdown. Three mock-agent tests
pass. Live OpenCode 1.18.18 negotiated ACP v1, created a session, switched via
`session/set_config_option` from the insufficient-balance default model to the
advertised free `opencode/mimo-v2.5-free` model, and completed a non-mutating
prompt with streamed command, thought, message, and usage updates.

Product decision: keep all ACP implementation, tests, utilities, documentation,
and evidence, but pause the general ACP interface. Matching the existing CLIs'
tools and slash commands would require substantial agent-specific product work.
The active roadmap item is now Part 4, Claude `/ide`. Continue by establishing
Claude Code 2.1.233's actual local IDE discovery and wire contract with narrow,
read-only inspection before launching or attaching a live Claude session.

Part 4 milestone 1 is now implemented. The installed client confirmed
`~/.claude/ide/<port>.lock`, process/workspace validation, loopback legacy
MCP SSE at `/sse` plus `/messages`, `selection_changed`, `getDiagnostics`, and
the `openDiff` result sentinels `FILE_SAVED`, `DIFF_REJECTED`, and `TAB_CLOSED`.
The plugin now publishes Claude discovery and serves a separate Claude
dispatcher while preserving Qwen's `/mcp` surface. Sixteen focused tests pass.
The next step is to reload the installed plugin, then use the existing Claude
agent tab for a read-only `/ide` connection, selection, and diagnostics check.
Keep all source views in non-agent panes and do not automate prompt input.

The read-only Part 4 live check is complete. The first two `/ide` attempts
failed because the implementation initially required bearer/custom-header
authentication. Narrow installed-binary inspection proved that Claude 2.1.233
uses `X-Claude-Code-Ide-Authorization` only for WebSocket and sends no auth
header for `sse-ide`; the loopback legacy SSE path was corrected and retested.
Claude then connected and displayed the selected line from the group-3 source
view. The standard account hit its weekly limit before diagnostics, so it was
gracefully `/exit`ed and its tab disappeared before a configured Claude Code
Ollama-provider profile was launched. That client connected, reported the exact
selection/range, called `mcp__ide__getDiagnostics`, and received 48 Pyright
items (2 errors, 46 hints). The transcript confirms the tool result and a clean
end turn. No source content changed. Next use a disposable file for one native
reviewed edit, verify the review stays in a non-agent pane, then `/exit`, wait
for termination, recreate Claude, and verify reconnection.

Part 4 is complete. Claude's first edit in auto mode bypassed `openDiff`, which
is retained as client-mode evidence; the disposable target was restored. After
Shift+Tab changed Claude to manual mode, its built-in `Edit` called
`mcp__ide__openDiff` and waited. The review contained `value = 42` in group 1,
Claude stayed in group 2, and disk still contained `value = 41`. Acceptance
completed Claude's edit and left both buffer and disk clean at `value = 42`.
Independent inspection found that the adapter's hidden source view had opened
behind Claude in group 2, so `_ide_open_diff` was fixed to move the source sheet
to the chosen non-agent review group before creating the review. The source was
moved out immediately and sixteen focused tests pass.

Claude was then sent `/exit`; GhostShell removed its view before recreation.
The disposable view was closed cleanly and its file deleted. Exactly one live
companion server remained. A fresh Claude Code Ollama-provider terminal was
created in group 2 and `/ide` reported `Connected to Sublime Text.` Part 4's
review, lifecycle, and reconnection criteria all pass. Part 5 is paused with
the general ACP product decision. The active roadmap marker is now optional
Part 6 Antigravity IDE / `agy /ide` research; do not install anything without
confirming that this optional research remains desired.

Part 6 was subsequently completed as bounded research. The user launched the
installed Antigravity IDE, which is a VS Code fork, and used its embedded agent
for local inspection. Sanitized evidence showed a private bundled-extension
language-server lifecycle using an ephemeral Windows named pipe, dynamic
loopback ports, per-process CSRF values, and a one-shot stdin handshake. No
public discovery record or supported `agy` command for attaching to that
already-running IDE was established. Do not retain or reproduce the live
tokens that appeared in an IDE-generated scratch tab.

Keep the conclusion narrow: earlier `agy.exe` evidence found internal IDE
machinery and `agy -p "/ide"` started its own language-server services, but
that does not establish attachment to the separate Antigravity IDE process.
The supported, verified interoperability path is shared MCP access to Sublime,
LSP, and Debugger. The user closed Antigravity IDE and the generated Sublime
scratch tabs; a final process check found no Antigravity IDE process. Parts 1,
2, 4, and 6 are complete. Parts 3 and 5 remain intentionally paused, with all
ACP prototype work retained.
