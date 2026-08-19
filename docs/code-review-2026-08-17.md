# Code review findings (2026-08-17)

Audience: other agents continuing work on this repo.  
Scope: recent non-backup work on `main` (~2026-07-25 → 2026-08-16).  
Related: `docs/session-handoff.md`, `docs/roadmap.md`, `docs/product-direction.md`.

Focused unit tests run during review (29 passed):

```powershell
python -m pytest tests/test_ide_companion.py tests/test_acp_client.py tests/test_claude_ide.py tests/test_debugger_state_reporting.py -q --tb=line
```

---

## Overall verdict

**Strong direction, good engineering taste, a few real security/concurrency gaps before treating companions as production-ready.**

Recent work is disciplined for a fast-moving plugin repo:

- Protocol cores (`ide_companion.py`, `claude_ide.py`, `acp_client.py`) are Sublime-free and unit-testable
- Contracts/docs (`docs/part2-…`, `part3-…`, `part4-…`, roadmap/handoff) match code milestones
- Batch deliberately avoids one giant main-thread hold — correct for ST
- Debugger “inactive but loaded” reporting is agent-friendly and well tested

Highest risk: **local auth inconsistency** on the Claude legacy companion path, plus lifecycle/timeout sharp edges.

---

## What was reviewed

Primary surfaces:

| Area | Key paths |
| --- | --- |
| IDE Companion | `packages/st-plugin/ide_companion.py` |
| Claude IDE | `packages/st-plugin/claude_ide.py` |
| ACP prototype | `packages/st-plugin/acp_client.py` |
| Main MCP bridge | `packages/st-plugin/sublime_mcp.py` |
| HTTP policy | `packages/st-plugin/mcp_http_policy.py` |
| Proxies | `packages/node-proxy/index.js`, `packages/python-proxy/mcp_server.py` |
| Debugger | `packages/debugger-mcp/debugger_mcp.py` (+ inactive-state tests) |
| Contracts | `docs/part2-ide-companion-contract.md`, part3/part4 |

Also noted: transport hardening across sublime / debugger / lsp MCP bridges (threaded HTTP, keep-alive, streamable `/mcp`, OAuth discovery 404s).

---

## What’s going well

### 1. IDE Companion architecture

`packages/st-plugin/ide_companion.py`:

- Loopback bind (`127.0.0.1:0`)
- Bearer auth with `hmac.compare_digest`
- Origin allowlist for browser-like clients
- Atomic discovery writes (`mkstemp` + `fsync` + `os.replace`)
- Shared server + Gemini/Qwen discovery adapters
- Debounced context publish, 10-file / 16 KiB caps
- Diff accept/reject + disconnect cleanup

Matches the published companion contract and milestone writeups.

### 2. Batch design

In `sublime_mcp.py`, `_batch`:

- Caps at 50 calls
- Blocks self-recursion
- Isolates per-call errors
- Intentionally does **not** wrap the whole batch in one `_on_main()`

Correct for Sublime UI freezes/deadlocks.

### 3. Transport hardening

Across bridges:

- `ThreadingHTTPServer`
- HTTP/1.1 keep-alive
- Streamable HTTP `/mcp` with GET → 405
- OAuth discovery JSON 404 (`mcp_http_policy.py`) to stop client auth loops
- node-proxy JSON Schema → Zod conversion + retries for dynamic tools

### 4. Debugger state reporting

Commit `f5c70fe` style fix:

- Explicit `status: inactive|active`
- Clear “plugin loaded but not active in any window” messaging
- Adapter enumeration aligned to current Debugger API
- `configuration_name` → `configuration` mapping for start commands
- Good focused tests, including `log_message(self, format, …)` signature trap

### 5. Test strategy

Recent tests load modules by path and avoid live Sublime where possible. Right pattern for this codebase.

---

## Findings

### Critical / High

#### 1. Claude legacy `/sse` + `/messages` are unauthenticated

In `ide_companion.py`, modern `/mcp` requires bearer (or Claude header). Legacy paths only check Origin:

- `GET /sse` → no auth
- `POST /messages?sessionId=…` → no auth

`test_server_exposes_session_scoped_legacy_sse_for_claude` connects with empty headers and expects 200.

**Impact:** any local process can open `/sse`, get a session, and call Claude tools (`openDiff`, `close_tab`, `getDiagnostics`) without the discovery token. Loopback-only → local multi-process trust, not remote RCE — but undermines the auth model the discovery file advertises.

**Fix direction:** require the same `_request_authorized()` on legacy SSE/message paths. If Claude’s client omits headers on SSE connect, authenticate on `/messages` at minimum, or gate legacy mode behind an explicit setting.

#### 2. Main MCP bridges still bind `0.0.0.0` with no auth

Companion is careful (`127.0.0.1` + token). Core bridges are not:

```text
HTTP bridge / MCP SSE → 0.0.0.0, no auth
includes eval_python, edit_file, install_package, etc.
```

Predates newest work; companion contrast makes it glaring. On multi-user machines, WSL port forwards, or loose firewall rules, this is a powerful unauthenticated control plane.

**Fix direction:** default bind `127.0.0.1`; keep `0.0.0.0` as opt-in. Longer-term: optional shared-secret for non-loopback.

---

### Medium

#### 3. Claude `openDiff` blocks a worker thread indefinitely

`_claude_open_diff()` does bare `event.wait()` with no timeout.

Unblocked by accept/reject/close/disconnect cleanup — good — but:

- A forgotten review pins a thread forever
- Under ThreadingHTTPServer this is survivable, not ideal
- No client-visible cancellation path except disconnect/close

**Fix:** `event.wait(timeout=…)` + explicit timeout error; ensure `close_tab` sets the event directly (don’t rely only on `on_close` ordering).

#### 4. Accept path can emit both accept result and reject notification race

Accept:

1. sets `claude_event`
2. pops state
3. erases `ide_companion_diff_path`
4. closes review

Ordering is mostly correct. But `close_tab` relies on `review.close()` → `on_close` to set the event, and `on_close` always publishes `ide/diffRejected` even when Claude result was `TAB_CLOSED`.

Because Gemini/Qwen/Claude share one companion server/notification hub, Claude tab-close can broadcast Gemini-style `ide/diffRejected` to other subscribers.

**Fix:** distinguish close reasons (`accepted` / `rejected` / `tab_closed` / `disconnected`) and only notify the relevant protocol audience.

#### 5. Proxy timeouts vs batch / long tools

Both proxies use ~10s HTTP timeouts:

- `packages/node-proxy/index.js` → `TIMEOUT = 10_000`
- `packages/python-proxy/mcp_server.py` → `TIMEOUT = 10.0`

A 50-call batch, slow `find_in_files`, or package install can blow past that even when the backend is fine.

**Fix:** higher timeout for `batch` (and maybe install/search tools), or per-tool timeout overrides.

#### 6. `python-proxy` batch docstring is wrong

It says batch shares “one main-thread dispatch”. Backend comments/code say the opposite on purpose.

Agents reading the tool description may form the wrong mental model.

#### 7. `selection_changed` leaks uncapped selection text

Context snapshot truncates at 16 KiB (`truncate_utf8`). Claude-oriented `selection_changed` in `_publish_ide_context()` sends full `view.substr(region)` with no cap.

Large selections become large SSE payloads on every debounced selection event.

#### 8. `isTrusted=True` is hard-coded

Companion always reports trusted workspace state. If a client uses that for permission policy, Sublime over-claims trust.

---

### Low / Maintainability

#### 9. ACP client is a solid prototype, not finished runtime

`acp_client.py` strengths: locks, pending-map cleanup on EOF, permission request path, smoke tests.

Gaps:

- unbounded thread-per-agent-request
- `close()` doesn’t shut down the reader side cleanly / join read loop
- invalid JSON lines silently dropped
- no Sublime integration yet (retained prototype — fine if labeled that way)

#### 10. node-proxy fallback vs dynamic split is good, still dual-maintenance

Dynamic discovery first, static fallback second is correct. The fallback catalog remains a large second source of truth and will drift from backend tool schemas over time.

**Resolved 2026-08-19.** Neither proxy is hand-maintained now. `tools/generate_fallback_catalog.py` emits `packages/node-proxy/fallback-tools.json` and `packages/python-proxy/tool_catalog.py` from the backend `_MCP_TOOLS`, and both proxies register from those. The same pass found that python-proxy was the worse case: with no dynamic discovery at all, its 72 hand-written tools were the entire surface, so 148 backend tools were permanently unreachable rather than merely dropped on a discovery miss. It now exposes all 220. `tests/proof/test_f10_proxy_catalog_drift.py` and `tests/proof/test_f10_python_proxy_catalog.py` fail if a committed catalog is stale or a hand-written tool list reappears. See `tests/proof/STATUS.md`.

#### 11. Diagnostics implementation is brittle by necessity

`_claude_get_diagnostics` reaches into `LSP.plugin.core.registry` and `storage._diagnostics`. Useful, but private-API-dependent; will break on LSP package refactors. Worth isolating behind a tiny adapter with a clear failure mode.

#### 12. Docs/analysis bulk

Recent commits added a lot of roadmap/transcript/analysis weight. Helpful for handoff; consider keeping generated CSV/JSON out of the main branch long-term if the repo is meant to stay product-focused.

#### 13. No request body size limit

HTTP handlers trust `Content-Length` and `rfile.read(length)` with no ceiling. Local-only reduces urgency; still an easy DoS against the ST process.

---

## Test gaps worth filling next

| Area | Gap |
| --- | --- |
| Companion auth | Assert legacy `/sse` and `/messages` require token (once fixed) |
| Claude diff lifecycle | Integration test: openDiff wait → accept/reject/close_tab unblocks with correct payload |
| Shared hub | Ensure Claude actions don’t emit Gemini notifications incorrectly |
| Batch | Backend unit test for max-50, unknown tool, nested batch, ordered results |
| Proxies | Timeout behavior for slow batch |
| Debugger | Already strong for inactive state; keep an ST-live smoke path in docs only |

---

## Priority order if shipping continues

1. **Auth-close the Claude legacy companion path** (or document/disable it)
2. **Bind core MCP bridges to loopback by default**
3. **Timeout + explicit completion reasons for Claude openDiff**
4. **Cap `selection_changed` text; fix batch tool description**
5. **Per-route proxy timeouts**
6. **Then ACP productization**

---

## Bottom line

High-quality incremental systems work: protocol isolation, contract-driven milestones, and tests that don’t require a live GUI for core logic. The companion stack is close to “real product,” not spike quality.

Do **not** call the Claude legacy transport secure yet. Do **not** advertise the broad MCP bridges as safe beyond single-user loopback without bind/auth changes. Everything else looks like tighten-and-ship, not rewrite.

---

## Suggested next agent actions

If picking up from this review:

1. Fix finding #1 (legacy companion auth) and flip/add tests in `tests/test_ide_companion.py`.
2. Change default bind host for sublime/debugger/lsp MCP HTTP servers to `127.0.0.1` with opt-in `0.0.0.0`.
3. Add openDiff timeout + close-reason enum so Claude/Gemini notification fans don’t cross-talk.
4. Patch python-proxy batch tool description; raise timeouts for `batch` / long tools.
5. Cap selection text in Claude `selection_changed` publish path.

Do not treat this file as a substitute for `docs/session-handoff.md` live workflow state; this is a static review snapshot from 2026-08-17.

---

## Proof obligation

Latent findings above are **candidates**, not closed incidents. The bar to keep them is a deterministic mock client/server trial:

→ `docs/proof-harness-proposal-2026-08-17.md`  
→ scoreboard (when implemented): `tests/proof/STATUS.md`

Each finding must end **PROVED**, **KILLED**, or **NARROWED**. Uninstrumented claims do not get to linger as settled bugs.
