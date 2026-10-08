---
name: debugger-control
description: Drive Sublime Text's Debugger package (daveleroy/SublimeDebugger) with sublime-mcp's generic tools, no per-package MCP -- configure, set breakpoints, start, read state / call stack / variables / evaluate, step, stop. Tested recipe (2026-10-08). Use when asked to debug code in Sublime Text.
---

# Debugger control

Verified 2026-10-08 on Sublime build 4215 (Python 3.14 host), Debugger 0.12.1, debugpy adapter, in both a
test copy and the user's main Sublime. A separate debugger MCP is NOT needed (see "Why no MCP"). Everything
marked NOT VERIFIED below was not run.

## Pick a route

- **Route A, `eval_python` (recommended): complete, 66 s for the whole task, structured results.** Reaches into
  the Debugger's own objects. Unstable internals (they changed between 0.11 and 0.12) but it is the only route
  that reads the call stack, variables and evaluates. The audit rules forbid eval_python; this recipe is for real work.
- **Route B, generic tools only (`run_command` + screenshots):** controls everything but state is readable only as
  pixels, and evaluate / watch / install adapters are impossible. See "Route B".

## One-time setup (both routes)

1. Install the package through the picker: `run_command install_package`, wait about 10 s, `get_quick_panel`
   (text "debugger"), `pick_quick_panel` (text "Debugger", an exact name beats look-alikes), wait about 30 s, then
   close the "Package Control Messages" tab it opens.
2. The Python adapter must exist at `<Package Storage>/Debugger/debugpy`. "Debugger: Install Adapters" is a
   list-input palette no tool can answer, so copy the folder from an existing install (a read-only local copy) or
   have the user install it once.
3. Add a configuration without any palette, in `Packages/User/Debugger.sublime-settings`:
   ```json
   {"global_debugger_configurations": [{
       "name": "Sample", "type": "debugpy", "request": "launch",
       "python": "C:\\path\\to\\real\\python.exe",
       "program": "C:\\path\\to\\script.py", "console": "internalConsole"}]}
   ```
   `"python"` must be a real interpreter: `python3` on Windows can be the Microsoft Store stub, and the run ends at
   once with "Debugging ended unexpectedly".
4. The window needs an open folder (`${folder}`), or start fails with "Unable to start adapter: 'folder'".

## Route A, eval_python (tested end to end)

Async calls run on the Debugger's own loop on the main thread and cannot be waited for, so use two calls: one
starts the work and parks results in `sublime._R`, the next call prints them.

```python
import sys
db = sys.modules['Debugger.modules.debugger']; core = sys.modules['Debugger.modules.core']
dbg = db.Debugger.get(sublime.active_window(), create=True)
print([(c.name, c.type) for c in dbg.project.configurations])      # the config must be listed

f = r'C:\path\to\script.py'
dbg.breakpoints.source.toggle(f, 2)          # TOGGLES: read dbg.breakpoints.source.breakpoints first
cfg = [c for c in dbg.project.configurations if c.name == 'Sample'][0]
core.run(dbg.start_with_configurations([cfg], False))               # two arguments (no_debug=False)
```
Wait 4 to 5 s (background timer), then:
```python
dbg = db.Debugger.get(sublime.active_window(), create=False); s = dbg.session
print(dbg.is_paused())                       # True at the breakpoint
def g(o, k): return o[k] if isinstance(o, dict) else getattr(o, k)   # thread/frame are dicts or objects
t, fr = s.selected_thread, s.selected_frame
R = sublime._R = {}
async def work():
    try:
        R['frames'] = [(g(x, 'name'), g(x, 'line')) for x in await s.stack_trace(g(t, 'id'))]
        loc = [v for v in s.variables if v.name == 'Locals'][0]
        R['locals'] = [(v.name, v.value) for v in await loc.children()]
        R['a+b'] = g(await s.evaluate_expression('a + b', 'repl'), 'result')
    except Exception as e:
        R['error'] = repr(e)
core.run(work())
```
Next call: `print(sublime._R)` gives `{'frames': [('add', 2), ('<module>', 7)], 'locals': [('a','0'),('b','10')], 'a+b': '10'}`.
Control the same way: `await s.step_over()`, `await s.resume()`, `await dbg.stop()` (inside a coroutine run by
`core.run`). After a step `dbg.is_paused()` is True and `g(s.selected_frame,'line')` moved on; after
`dbg.stop()`, `dbg.session` is None and `is_running()` is False. Re-read variables after every stop (references change).

## Route B, generic tools only (tested)

`run_command` with `command="debugger"`, args `{"action": ...}`: `open`, `toggle_breakpoint` (current line of the
active file), `start` with `"configuration": "<name>"`, `step_over`, `continue`, `stop` all work. Limits:
- Every call returns `ok` whatever happened. Verify by screenshot ("Stopped: breakpoint" in the editor, call stack and
  locals in the bottom pane). `get_active_panel` gives only console text.
- No text tool exposes the call stack / variables (the accessibility tree shows only window chrome); after a step
  the UI shows the Console tab, and a background click on the "Callstack" tab does nothing.
- Evaluate, watch expressions and Install Adapters need a list-input palette: not possible.
- `start` with no `configuration` opens a palette instead of running.

## Gotchas

- `run_command debugger {"action": "clear_breakpoints"}` does NOT clear. Toggle through `dbg.breakpoints.source`.
- `open_file` returns before the file has loaded; wait before cursor moves or `toggle_breakpoint`.
- Starting a session opens the debugger panel (bottom half) and the script's tab in the ACTIVE window, covering
  whatever was there, including a terminal tab. Do not run this in the window that hosts your own terminal unless
  you restore it, and tell the user first.
- **Incident, cause unknown:** in the user's main Sublime a cleanup call (breakpoint toggle, `debugger` action `quit`,
  `hide_panel`, `close_file`) was followed by Sublime exiting (no crash report, no Windows error). The same
  sequence was fine in a test copy. Until understood, clean up one small step per call, and prefer letting the
  user close the panel.
- In 0.12.1 `step_over` etc. are methods of the session (`dbg.session`), not the `Debugger` object, and
  `start_with_configurations` needs `(configurations, no_debug)`. The older text of this skill said otherwise.
- NOT VERIFIED: pause, step in/out, reverse debugging, function/column breakpoints, watch expressions,
  disassembly, memory, other adapters. PLUGIN DEBUGGING (type "sublime" adapter, runs a second Sublime): the debug
  Sublime process started but never opened a window or plugin hosts on the test machine; unsolved.

## Why no MCP (what was tested)

The old `debugger-mcp` (79 tools, in git history before 435cf12) was restored and run on build 4215 and on build
4200 (Python 3.8). Every async tool failed with "There is no current event loop": it called `core.run(coro)` from an
HTTP thread and used the return value as a result, but `core.run` creates a task. A 20-line shim
(`asyncio.run_coroutine_threadsafe(coro, Debugger.modules.core.asyncio.main_loop).result(timeout=15)`) fixed the
readers (call stack, variables, evaluate in one call each) but its typed step tools still failed on API changes in
0.12.1 and its breakpoint toggle returned HTTP 500 though it worked. A per-package server must follow its package
forever; Route A needs none. Full numbers: `.claude/memory/project_debugger_mcp_vs_nomcp_2026_10_08.md` in the
sublime-mcp repo.
