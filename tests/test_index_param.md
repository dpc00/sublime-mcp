# Test Results: index parameter for send_to_view / get_view_content / replace_lines

## What was added
`send_to_view`, `get_view_content`, and `replace_lines` now accept an `index` parameter
(0-based, matching position in `get_open_files` output) to target nameless/untitled tabs
that cannot be addressed by name.

## Direct HTTP tests (curl against port 9500)

### get_view_content?index=3&name=
- **Result: PASS** — returned the Terminus tab content (name=" ", not the Claude tab)
- Command: `curl -s "http://127.0.0.1:9500/view_content?index=3&name="`
- Confirmed plugin correctly routes by index when name is empty

### get_view_content?index=0&name=
- **Result: PASS** — returned the Claude tab (index 0)

### get_view_content?name=sublime_mcp
- **Result: PASS** — name-based lookup still works (unaffected by change)

## MCP tool tests (via mcp__sublime__get_view_content)

### get_view_content(index=3)
- **Result: INCONCLUSIVE** — MCP tool returned Claude tab regardless of index value
- Likely cause: FastMCP may not be forwarding the `index` param as a query string param,
  or it sends `index=-1` as default overriding the specified value
- Needs further investigation: check what URL FastMCP actually sends to the HTTP server

## Plugin reload procedure
After copying `sublime_mcp.py` to `Packages/User/`, the HTTP server thread must be
restarted. Automatic reload by ST is not sufficient — server keeps old function refs.
Workaround used in testing:
```python
mod.plugin_unloaded()
mod.plugin_loaded()
```

## Known deployment issue
`sublime_mcp.py` must be manually copied to:
`C:\Users\donal\AppData\Roaming\Sublime Text\Packages\User\sublime_mcp.py`
after every change. A build step or symlink would eliminate this.

## Next step
Investigate FastMCP parameter forwarding for integer query params to confirm
`mcp__sublime__get_view_content(index=3)` actually sends `?index=3` to port 9500.
