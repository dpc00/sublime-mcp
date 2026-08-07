# Handoff for Claude — sublime-mcp review + fixes

**From:** Grok (this session)  
**Date:** 2026-08-07  
**Status:** Implemented, committed, pushed to `origin/main` as `4c0d150`

## Context

Repo: `C:\Users\donal\projects\sublime-mcp`  
Three MCPs: **sublime-mcp** (`packages/st-plugin/sublime_mcp.py`), **debugger-mcp**, **lsp-mcp**.  
Node proxy: `packages/node-proxy/index.js` (dynamic discovery via `GET /mcp_tools` then `POST /{tool.name}`).

ST loads the plugin via link:

`%APPDATA%\Sublime Text\Packages\sublime-mcp\sublime_mcp.py` → `packages/st-plugin/sublime_mcp.py`

## What was reviewed

Branch-style review of recent MCP work (`ae5cf75~1` → HEAD at review time): HTTP bridges, dynamic tool discovery, `batch`, `get_help`, keep-alive, bind-address, proxy parity.

Review notes (temp; may expire):

- `C:\Users\donal\AppData\Local\Temp\grok-donal\grok-review-cd4b655b.md`
- `C:\Users\donal\AppData\Local\Temp\grok-donal\grok-review-summary-cd4b655b.md`

## Critical findings (from review)

1. **node-proxy dynamic tools broken for many sublime tools** — discovery always `POST /{tool.name}`, but REST routes often differ (`get_active_file` → GET `/active_file`, edit → POST `/edit_file`). When ST is up, dynamic load skips static fallback → 404s.
2. **`batch` + outer `_on_main` deadlock risk** — whole batch ran on ST main thread; tools that `time.sleep` while polling (e.g. `_ensure_view`) freeze UI / hang.
3. **Bind `0.0.0.0`** — intentional for WSL (no mirror). **Do not “fix” back to 127.0.0.1** unless the user asks.
4. **node-proxy discarded JSON Schemas** → `z.object({}).passthrough()`.
5. **`_on_main` timeout** returned silent `None`.

Also open (not fixed): keep-alive only on sublime; python-proxy still static; no batch size cap; bare `json.loads`; machine-hardcoded path in `tests/test_python_proxy.py`; doc count drift (218 vs 219).

## What was implemented (fixes 1, 2, 4 only)

### 1. MCP name → HTTP aliases — `packages/st-plugin/sublime_mcp.py`

After `_MCP_TOOLS` is defined:

- Populate `_POST["/" + name] = handler` **only if path not already in `_POST`** (avoids infinite recursion for `_p("/save_all")`-style wrappers).
- Track added paths in `_POST_MCP_ALIASES`.
- `register_mcp_tools` / `unregister_mcp_tools` add/remove aliases for extensions.

### 2. Batch on worker thread — same file

- Removed outer `_on_main(fn)` around the batch loop.
- Loop runs on HTTP worker; each nested tool still does its own `_on_main`.

### 4a. Schema pass-through — `packages/node-proxy/index.js`

- `jsonSchemaToZod()` / `jsonSchemaPropToZod()` shallow-convert backend `inputSchema`.
- Dynamic registration uses that Zod shape (`.passthrough()` for extra keys).

### 4b. `_on_main` timeout — `sublime_mcp.py`

```python
if not done.wait(5.0):
    raise TimeoutError("main-thread timeout after 5s")
```

## Intentionally not changed

- **`0.0.0.0` bind** — user needs it for WSL without port mirror.
- debugger-mcp / lsp-mcp keep-alive / ThreadingHTTPServer suggestions.
- python-proxy dynamic discovery.

## Commit

```
4c0d150 fix: make node-proxy dynamic tools work and harden batch
```

Files:

- `packages/st-plugin/sublime_mcp.py`
- `packages/node-proxy/index.js`

Pushed to `https://github.com/dpc00/sublime-mcp.git` (`main`).

## Verification already done

- `python -m py_compile packages/st-plugin/sublime_mcp.py`
- `node --check packages/node-proxy/index.js`
- Live HTTP: aliases for `get_active_file`, `get_line_count`, `str_replace_based_edit_tool`; `save_all` still OK; batch partial failure OK
- `cd packages/node-proxy && node test_batch.mjs` — PASS
- MCP client: full schemas on tools; `get_active_file` works through node-proxy

## Suggested next steps

1. Optional hardening: batch max size; ThreadingHTTPServer on HTTP bridges; HTTP/1.1 keep-alive on debugger/lsp bridges; fix `PROXY_DIR` hardcode in `tests/test_python_proxy.py`; sync AGENT_GUIDE tool counts.
2. Optional test: extend `packages/node-proxy/test_batch.mjs` to call `get_active_file` and assert `str_replace_based_edit_tool` inputSchema has `required: ['command']`.

## Smoke commands

```bash
# ST must be running with plugin loaded (bridge :9500)
curl -s -X POST http://127.0.0.1:9500/get_active_file -H "Content-Type: application/json" -d "{}"
curl -s -X POST http://127.0.0.1:9500/batch -H "Content-Type: application/json" -d "{\"calls\":[{\"tool\":\"get_line_count\"},{\"tool\":\"get_selection\"}]}"
cd packages/node-proxy && node test_batch.mjs
```
