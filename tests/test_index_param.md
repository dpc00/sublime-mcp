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

## MCP tool tests (via MCP tools after full ST restart + pybackup deploy)

### get_view_content(index=1)
- **Result: PASS** — returned "Command Prompt" (Terminus tab at index 1)

### send_to_view(index=1, text="echo index_test_ok\n")
- **Result: PASS** — command executed in Command Prompt tab, not Claude tab
- Output confirmed: `index_test_ok` appeared in terminal

### Pre-restart tests showed INCONCLUSIVE results
- Root cause: plugin file was not yet deployed; old code was still running
- Fix: run pybackup to deploy, then restart ST

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
