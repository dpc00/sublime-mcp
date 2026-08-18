# Proof harness proposal: mock clients/servers that confirm or kill every review finding

Audience: anyone who will not accept latent-risk language without a failing test.  
Related: `docs/code-review-2026-08-17.md`.  
Date: 2026-08-17.

---

## Rule

Every finding from the 2026-08-17 review is either:

1. **PROVED** — a deterministic harness reproduces the claimed failure mode under controlled conditions, with a measurable assertion, or  
2. **KILLED** — the same harness runs the claimed attack/race/timeout path and the claimed failure does **not** occur; the finding is retracted or rewritten as non-defect.

No third option for “code looks bad.” Static reading is how candidates were nominated. This harness is how they stay or die.

**Definition of done for this proposal’s implementation:**  
`pytest tests/proof/` (and any listed JS proof scripts) is green, and every finding has a status file entry of `PROVED` or `KILLED` with the test path that decided it.

If a finding cannot be instrumented without a live Sublime GUI, the harness still isolates the protocol surface with fakes and marks only the GUI-bound remainder as `BLOCKED_ON_ST` — not as free pass.

---

## What already exists (do not rebuild)

| Asset | Role |
| --- | --- |
| `tests/test_ide_companion.py` | Real `IdeCompanionServer` over loopback; already proves unauth legacy SSE (empty headers → 200) and auth on `/mcp` |
| `tests/test_http_api.py` | Live ST HTTP bridge (opt-in; needs ST) |
| `tests/test_python_proxy.py` | Live python-proxy stdio → ST HTTP |
| `tests/test_mcp_sse.py` | Live MCP SSE |
| `packages/st-plugin/ide_companion.py` | Sublime-free companion core — primary SUT for pure protocol proofs |
| Diff/accept logic in `sublime_mcp.py` | Needs extraction or thin fakes for race proofs without full ST |

**Reuse pattern:** load modules by path (as companion tests already do). Prefer real servers on `127.0.0.1:0` over pure mocks when the SUT is already Sublime-free.

---

## Layout

```text
tests/
  proof/
    __init__.py
    conftest.py                 # shared ports, tokens, SSE readers, thread budgets
    fakes/
      fake_bridge.py            # HTTP backend for proxies (delay, bind, tools)
      fake_diff_host.py         # in-process stand-in for openDiff lifecycle
      fake_acp_peer.py          # stdio JSON-RPC peer for ACP
      malicious_local_client.py # unauthenticated companion attacker
      gemini_subscriber.py      # authenticated /mcp SSE consumer
      claude_legacy_client.py   # /sse + /messages client (auth optional)
    test_f01_legacy_auth.py
    test_f02_bind_scope.py
    test_f03_opendiff_hang.py
    test_f04_notification_crosstalk.py
    test_f05_proxy_timeouts.py
    test_f06_batch_docstring.py
    test_f07_selection_cap.py
    test_f08_istrusted.py
    test_f09_acp_lifecycle.py
    test_f10_proxy_catalog_drift.py
    test_f13_body_limit.py
    STATUS.md                   # generated or hand-maintained scoreboard
packages/
  proof-harness/                # optional shared helpers if tests get fat
    README.md
```

Node side (finding #5/#10 only):

```text
packages/node-proxy/proof/
  fake-bridge.mjs
  test-timeout.mjs              # node:test or plain assert script
```

Run:

```powershell
python -m pytest tests/proof -q --tb=short
node packages/node-proxy/proof/test-timeout.mjs
```

No live Sublime required for PROVE/KILL of findings 1, 3–8, 9, 13, and the proxy half of 5/10.  
Finding 2 needs either a bind-assert unit test on the construction site or a short live smoke; see below.

---

## Shared harness primitives

### `ClaudeLegacyClient`

- `connect(port, headers=None)` → opens `GET /sse`, parses `event: endpoint`
- `call(method, params, headers=None)` → `POST` to session `/messages`
- `iter_events(timeout=)` → yields JSON payloads
- Default headers empty (attacker). Optional bearer / `X-Claude-Code-Ide-Authorization`.

### `GeminiSubscriber`

- Authenticated `GET /mcp` SSE
- Collects `ide/*` and other notifications into a thread-safe list with timestamps

### `FakeDiffHost`

Extract or reimplement the **control flow** under test (not the Sublime UI):

```text
open_diff() → registers state + Event, blocks waiter thread on event.wait([timeout])
accept()    → sets result FILE_SAVED, pops state, clears path flag, closes review
reject()    → sets DIFF_REJECTED, notify ide/diffRejected, close
close_tab() → sets TAB_CLOSED, close review → on_close
on_close()  → sets event if still waiting; currently always notify ide/diffRejected
disconnect()→ reject leftovers, set events
```

The point is to drive the **same ordering and hub publish rules** as `sublime_mcp.py` (`AcceptIdeCompanionDiffCommand`, `on_close`, `_claude_open_diff`, `_claude_close_tab`) against a real `IdeCompanionServer` notification hub.

If extraction is too invasive for v1, copy the lifecycle into `fake_diff_host.py` as a **behavioral twin** locked by comments citing source line ranges. Twin must be updated when production changes; a single “parity checklist” test compares twin call graph names to source via AST/string presence.

### `FakeBridge` (HTTP)

Minimal `ThreadingHTTPServer` on `127.0.0.1:0`:

| Route | Behavior |
| --- | --- |
| `GET /active_file` | fast JSON |
| `POST /batch` | sleeps `delay_s` then returns N results; optional per-call delay |
| `POST /slow` | sleeps past proxy timeout |
| `GET /mcp_tools` | configurable tool list for catalog tests |
| bind host selectable | `127.0.0.1` vs `0.0.0.0` for bind proofs |

Proxies point at it via `SUBLIME_MCP_BASE`.

### Thread / hang detector

```text
assert_thread_unblocked(event_or_future, within_s=…)
assert_thread_still_blocked(after_s=…)
count_blocked_waiters()
```

Used for openDiff and ACP close tests. No “hope it finishes.”

---

## Finding-by-finding contracts

Status vocabulary used in assertions and `STATUS.md`:

| Status | Meaning |
| --- | --- |
| **PROVED** | Harness demonstrates the defect as claimed |
| **KILLED** | Harness demonstrates the claimed failure does not happen; finding wrong or overstated |
| **NARROWED** | Part proved, part killed; rewrite the finding |
| **BLOCKED_ON_ST** | Needs live Sublime; protocol half still proved if possible |

---

### F1 — Legacy `/sse` + `/messages` unauthenticated

**Claim:** Any local process can open legacy SSE and invoke Claude tools without the discovery token.

**SUT:** real `IdeCompanionServer` + `legacy_dispatcher` that records calls (including a fake `tools/call` for `openDiff`).

**Harness:**

1. Start server with `auth_token="secret"`.
2. `ClaudeLegacyClient` with **empty headers**: connect + `tools/call`.
3. Parallel control: `/mcp` without bearer must 401 (existing test).
4. Optional: second client with wrong bearer on legacy path — today expected to **still succeed** if claim holds.

**PROVE if:**

- `GET /sse` → 200 with no auth  
- `POST /messages` → 202 and dispatcher invoked with no auth  
- Dispatcher can be a dangerous tool (`openDiff` / `getDiagnostics` stand-in)

**KILL if:**

- Legacy paths return 401 without token (behavior already fixed), **or**  
- Legacy connect works but **tool dispatch** refuses unauthenticated sessions (narrower security boundary — then NARROWED, not full kill)

**Note:** `test_server_exposes_session_scoped_legacy_sse_for_claude` already almost PROVES this. The proof test upgrades it: empty headers are **asserted as the attack**, dispatcher records a privileged method, and STATUS marks PROVED. Do not leave it as a happy-path “feature” test only.

**Effort:** S (hours). Highest ROI. Do first.

---

### F2 — Core bridges bind `0.0.0.0` with no auth

**Claim:** HTTP/MCP servers listen on all interfaces without auth.

**Problem:** Bind happens inside `plugin_loaded` / `_start_servers` with real Sublime ports. Full process bind is awkward in unit tests.

**Harness (two layers):**

**2a. Construction proof (no ST)**  
Refactor-light approach preferred: extract bind host to a constant/function e.g. `_bind_host()` defaulting to `"0.0.0.0"`. Unit test:

```text
assert bind_host() == "0.0.0.0"          # today’s default → PROVED config defect
assert bind_host() in source of sublime_mcp, debugger_mcp, lsp_mcp
```

If extraction is refused, AST/source test:

```text
assert '_ThreadingHTTPServer(("0.0.0.0"' in source  # brittle but honest
```

**2b. Socket proof (optional CI job, may need admin/network)**  
Start `FakeBridge` or a thin copy of `_Handler` on `0.0.0.0:0`, then:

- Connect via `127.0.0.1` → OK  
- Connect via non-loopback local address (enumerate `psutil`/netifaces) → OK if all-interfaces bind  
- Assert no `Authorization` check on `GET /active_file`

**PROVE if:** default bind is all-interfaces **and** a no-auth route succeeds.

**KILL if:** default is already loopback **or** auth is required on those routes.

**Effort:** S for 2a, M for 2b. 2a is enough to stop arguing about “what the code says.”

---

### F3 — `openDiff` blocks a worker forever

**Claim:** `_claude_open_diff` uses bare `event.wait()`; forgotten review pins a thread indefinitely.

**SUT:** production function if importable with fakes; else `FakeDiffHost` twin that mirrors `event.wait()` with no timeout.

**Harness:**

1. Start companion + legacy client.  
2. Call `openDiff` on a background thread.  
3. Do **not** accept/reject/close.  
4. After T=2s: assert waiter still alive and not done.  
5. After T=5s still blocked → hang confirmed.  
6. Then accept (or disconnect) and assert unblock + correct payload.  
7. Separate case: `close_tab` must unblock (today via `on_close`); assert event set and result `TAB_CLOSED`.  
8. **Timeout probe:** if production ever grows `wait(timeout=)`, assert waiter completes with explicit error before T_max and no zombie thread.

**PROVE if:** steps 4–5 hold on current code (blocked with no client-visible error).

**KILL if:** wait has a finite timeout and returns a structured error without external accept/reject.

**Effort:** M (fake host + threading). No ST UI if twin is used; add one live ST smoke later optional.

---

### F4 — Notification cross-talk / double reject

**Claim:** Shared hub + `on_close` always publishes `ide/diffRejected`, so Claude tab-close (or accept→close) can deliver reject-style notifications to Gemini/Qwen subscribers; accept path can race.

**SUT:** real `IdeCompanionServer` hub + `FakeDiffHost` implementing accept/reject/close/on_close **exactly** as `sublime_mcp.py` does today (including unconditional `ide/diffRejected` in `on_close`).

**Harness matrix:**

| Scenario | Actors | Assert |
| --- | --- | --- |
| A | Gemini SSE subscribed; Claude `openDiff` then Accept | Claude waiter gets `FILE_SAVED`; Gemini must **not** receive `ide/diffRejected` for that path after accept. If it does → PROVED cross-talk / double signal |
| B | Gemini subscribed; Claude `close_tab` | Claude gets `TAB_CLOSED`; Gemini receives `ide/diffRejected` → PROVED protocol bleed |
| C | Gemini subscribed; user Reject | Both may see reject depending on design; document expected. Fail only if Claude waiter never unblocks or double-finalizes inconsistently |
| D | Two Claude sessions, one accept one reject | No crossed `claude_result` between keys |
| E | Accept ordering stress (N=50 rapid accept) | No hang; at most one terminal notification per filePath per design rule |

**PROVE if:** Scenario A or B shows Gemini receiving `ide/diffRejected` for a Claude-owned close/accept path while Claude already got a non-reject terminal result (or tab_closed).

**KILL if:** under the real hub + real on_close ordering, Gemini never sees reject for Claude-only lifecycle, and accept never double-publishes reject.

**Important:** This is the finding most likely to be **NARROWED**. The harness must record the exact event sequence with timestamps, not a vibe.

**Effort:** M–L.

---

### F5 — Proxy timeouts vs slow batch / long tools

**Claim:** 10s client timeout kills legitimate slow `batch` / long tools while backend is fine.

**SUT:** real `packages/python-proxy/mcp_server.py` and `packages/node-proxy` against `FakeBridge`.

**Harness:**

1. FakeBridge `POST /batch` sleeps 12s, then 200 `{results:[…]}`.  
2. Launch python-proxy with `SUBLIME_MCP_BASE=http://127.0.0.1:<fake>`.  
3. MCP stdio client calls `batch`.  
4. Expect failure: httpx timeout / tool error within ~10–11s; backend still completes (fake logs completion after 12s).  
5. Control: sleep 1s batch succeeds.  
6. Repeat for node-proxy (`TIMEOUT = 10_000`).  
7. Optional: 50 fast sub-calls that sum >10s wall time if sequential on backend.

**PROVE if:** backend succeeds and proxy surfaces timeout/error to the MCP client.

**KILL if:** proxy waits long enough for 12s backend (timeout already raised) **or** batch uses a higher dedicated timeout.

**Effort:** M. Reuses mental model of `test_python_proxy.py` but **must not** require live ST.

---

### F6 — python-proxy batch docstring wrong

**Claim:** Docstring says “one main-thread dispatch”; backend intentionally does not.

**This is not a runtime failure.** Proof is textual + behavioral:

1. **Static PROVE:** docstring contains `main-thread` (or equivalent).  
2. **Behavioral:** FakeBridge `/batch` handler records whether it received one HTTP request with N calls (true) vs N main-thread claims (untestable in proxy alone).  
3. Cross-check backend `sublime_mcp._batch` source/comments for “not one main-thread” / per-call `_on_main` pattern via source assertion.

**PROVE (doc defect) if:** proxy docstring claims single main-thread dispatch **and** backend batch implementation schedules per-call main-thread work (or documents that it does).

**KILL if:** docstring already matches backend.

**Effort:** S. Still required so “doc bug” is not opinion.

---

### F7 — `selection_changed` uncapped text

**Claim:** Context snapshot caps at 16 KiB; `selection_changed` sends full `view.substr(region)`.

**SUT:** Prefer extracting pure publish payload builder; if not, twin of `_publish_ide_context` selection branch + real `server.notify` + Gemini/Claude SSE listener.

**Harness:**

1. Build selected_text of size `16 * 1024 + 4096` (UTF-8 edge: include multi-byte chars).  
2. Publish both `ide/contextUpdate` and `selection_changed` as production does.  
3. Assert context path’s `selectedText` ≤ 16 KiB (existing `truncate_utf8`).  
4. Assert `selection_changed.data.text` length **equals full input** (or raw byte length).

**PROVE if:** asymmetry holds (snapshot capped, selection event full).

**KILL if:** selection event also truncated to the same cap.

**Effort:** S–M.

---

### F8 — `isTrusted=True` hard-coded

**Claim:** Companion always reports trusted workspace.

**SUT:** `_current_ide_context` path or `IdeContextTracker.snapshot(..., is_trusted=True)` call site.

**Harness:**

1. Source/unit: snapshot called with `is_trusted=True` constant (AST or direct call of builder).  
2. Runtime: subscribe SSE, force context publish with fake open files, assert `workspaceState.isTrusted is True` always across N publishes.  
3. Negative control: if an API existed to set untrusted, flip it — today no API → hard-coded PROVED.

**PROVE if:** no code path yields `isTrusted: false`.

**KILL if:** trust is configurable or derived and can be false in test.

**Effort:** S.

**Impact note for STATUS:** PROVED code fact ≠ PROVED client privilege escalation. Optionally add a **policy mock client** that grants extra tools only when `isTrusted` is true; then F8 impact is PROVED only if that client would enable them. Without a real client contract in-repo, mark **defect: over-claim in protocol payload**, impact **policy-dependent**.

---

### F9 — ACP client lifecycle gaps

**Claim:** unbounded thread-per-request; `close()` doesn’t join reader; bad JSON dropped.

**SUT:** real `acp_client.py` + `fake_acp_peer` stdio process.

**Harness:**

| Case | Assert |
| --- | --- |
| Flood 100 concurrent agent requests | thread count growth (or documented semaphore); PROVE unbounded if N threads ≈ N requests |
| `close()` then write from peer | reader stops; no hang on process exit within T; join or equivalent |
| Peer sends invalid JSON line then valid response | valid still processed **or** PROVE silent drop of invalid (claim) without killing session |
| EOF mid-pending | pending map cleared (existing strength — regression guard) |

**PROVE/KILL per sub-bullet independently → likely NARROWED.**

**Effort:** M.

---

### F10 — node-proxy static catalog drift

**Claim:** fallback catalog drifts from backend schemas.

**Harness:**

1. FakeBridge `/mcp_tools` returns schema set S_backend.  
2. Force dynamic discovery fail (bridge down on first N tries) so fallback catalog loads.  
3. Diff tool names + required fields: `S_fallback` vs `S_backend`.  
4. PROVE if any tool in both differs on required props or type; or backend-only tools missing from fallback when dynamic failed.

**KILL if:** fallback is generated from the same source or diff is empty by construction.

**Effort:** M (node).

---

### F11 — Diagnostics private LSP API

**Out of scope for mock servers** as a stability claim. Optional: mock `LSP.plugin.core.registry` module in `sys.modules` and assert failure mode when structure missing. Mark **soft** — PROVE brittle import path, not runtime break in the wild.

---

### F12 — Docs bulk

**Not a mock-server concern.** Skip harness. Track as repo hygiene only.

---

### F13 — No request body size limit

**Claim:** handlers trust `Content-Length` / unbounded `rfile.read`.

**Harness:**

1. Real companion `/mcp` with auth: POST body of 20–50 MiB (or smaller if CI-constrained, e.g. 5 MiB) with huge `Content-Length`.  
2. Assert either rejection (limit exists → KILL) or full read attempted / memory spike / success (PROVE unbounded).  
3. Same against FakeBridge copy of bridge handler if companion differs.

**Careful:** keep default proof size CI-safe (e.g. 5 MiB) with an env-gated stress size.

**Effort:** S.

---

## Execution order (do not reshuffle casually)

| Order | Finding | Why |
| --- | --- | --- |
| 1 | F1 | Already half-written; security; minutes to PROVE |
| 2 | F8, F6, F13 | Cheap static/runtime proofs |
| 3 | F7 | Small publish-path test |
| 4 | F3, F4 | Shared FakeDiffHost; core concurrency story |
| 5 | F5 | FakeBridge + both proxies |
| 6 | F2 | Bind constant / source proof |
| 7 | F9, F10 | Secondary surfaces |
| 8 | F11 optional | Adapter brittleness |

After each finding’s tests land, update `tests/proof/STATUS.md`:

```markdown
| ID | Status | Test | One-line evidence |
| F1 | PROVED | test_f01_... | empty-header tools/call reached dispatcher |
| F4 | NARROWED | test_f04_... | reject on close_tab yes; accept double-reject no |
...
```

**Review doc obligation:** patch `docs/code-review-2026-08-17.md` (or a short addendum) so every finding cites PROVED/KILLED/NARROWED. Findings KILLED get struck or moved to “non-issues.” No silent disagreement between review and harness.

---

## What “to the hilt” means here

- Real bytes on the wire (HTTP/SSE/stdio), not only reading source into a narrative.  
- Attackers and peers are **clients and servers we own**, with empty tokens, slow backends, large selections, concurrent subscribers.  
- Time bounds are numeric. Hangs are detected, not assumed.  
- Each test ends in one of: assertion failure (harness bug), PROVED, KILLED, NARROWED.  
- If the harness cannot construct the scenario, that is a **harness gap**, logged as such — it does **not** keep the finding alive by default. Unprovable after a good-faith instrument attempt → **drop or rewrite the finding**.

---

## Explicit non-goals

- Full Gemini CLI / Claude Code / Qwen binaries as dependencies (too heavy, nondeterministic). Protocol-level mocks are enough.  
- Proving remote RCE (loopback design makes that the wrong claim).  
- Replacing the existing unit suite — proof tests **add** `tests/proof/`, they don’t gut happy-path tests.  
- Fixing the defects in the same PR as the harness (allowed later; harness should fail red on PROVED defects until fixed, then go green as regression locks).

---

## Fix-forward policy (after proof)

When a finding is PROVED, the fix PR must:

1. Keep the proof test.  
2. Flip expectations from “attack succeeds” to “attack fails” (or hang no longer occurs).  
3. Leave a short comment: `PROOF: Fk — <date>`.

When KILLED:

1. Delete or rewrite the review bullet.  
2. Keep a minimal characterization test so the kill stays true (e.g. “legacy requires auth”).

---

## Minimal first PR (ship this week)

Scope lock — do not expand:

1. `tests/proof/` skeleton + conftest + SSE helpers  
2. `ClaudeLegacyClient` + F1 PROVE (upgrade of existing legacy SSE test)  
3. F8 + F6 + F13 cheap proofs  
4. `STATUS.md` with those four decided  
5. One-paragraph addendum on the code review doc pointing at STATUS

Second PR: `FakeDiffHost` + F3 + F4.  
Third PR: `FakeBridge` + F5 (+ node script) + F2 source bind assert.

---

## Bottom line

The review used code facts. This harness turns each fact into a **reproducible trial**.

- If the trial shows the gun fires → finding stays, now with a regression test.  
- If the trial shows the gun does not fire → finding dies, and we stop repeating it.  
- If we cannot build the trial → we do not get to keep preaching the finding.

Build the mocks. Run the trials. Update the scoreboard. Everything else is commentary.
