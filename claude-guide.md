# Claude + Sublime Text MCP: Speed & Efficiency Guide

## The Mental Model

Standard tools (Read, Edit, Grep, Bash) go through disk and the OS on every call.
ST MCP tools operate on **Sublime's in-memory buffer** — the file is already parsed,
indexed, and held in RAM. This means:

- `open_file` → file lands in ST's buffer (one-time cost)
- Every subsequent read/edit hits RAM, not disk
- Edits appear live with undo, gutter markers, and diff highlights
- Shell work via Terminus tabs never leaves the ST process context

**Rule of thumb:** If you're touching a file more than once in a session, open it in ST
first and never leave. The break-even is roughly 2 operations.

---

## Tool Decision Tree

```
Need to READ a file?
  ├─ Already open in ST?  →  get_file_content(path)           ← O(file), one call
  ├─ Not open yet?        →  open_file(path) → get_file_content(path)
  └─ Just a slice?        →  str_replace_based_edit_tool view, view_range=[start,end]

Need to EDIT a file?
  └─ str_replace_based_edit_tool str_replace (exact match, exact whitespace)
     • auto-opens the file if not already open
     • shows live diff highlight for 30 seconds in ST

Need to SEARCH across files?
  └─ find_in_files(pattern, folders=[narrow_path], regex=True)
     • returns {path, line, match} list
     • skips .git/__pycache__/node_modules automatically
     • NEVER pass a huge root folder — scope tightly

Need to READ a huge log / Terminus output?
  ├─ get_view_size(name="terminus")     ← O(1), get total chars
  └─ get_view_chars(begin=size-8000, end=size, name="terminus")  ← read tail only

Need to RUN a shell command?
  ├─ send_to_view("your command\n", name="terminus")   ← types into Terminus + Enter
  └─ get_view_chars(...)  ← read back output after it finishes
```

---

## The Core 5 Patterns (Use These Every Session)

### 1. Open-Once, Read-Many
```
open_file(path)                    # one round-trip to disk
get_file_content(path)             # RAM read, instant
... edit ...
get_file_content(path)             # still RAM, no re-open needed
```
Never re-open a file that's already in ST. `get_file_content` on an already-open file
is effectively free.

### 2. Surgical Edit with Zero Context Waste
```
str_replace_based_edit_tool(
  command="str_replace",
  path=...,
  old_str="exact old block",       # must match once, exactly
  new_str="replacement"
)
```
Send only the changed fragment. The diff is visible in ST immediately. No need to
re-read the whole file to verify — the gutter markers show it.

### 3. Scoped Cross-File Search
```
find_in_files(
  pattern=r"def backup_\w+",
  folders=["C:\\Users\\donal\\projects\\pybackup"],
  regex=True,
  max_results=50
)
```
Returns file+line+match. Use this instead of Grep when you need the results to feed
a multi-file edit loop.

### 4. Log Tail Without Loading the World
```
size = get_view_size(name="pybackup")          # e.g. 142000
get_view_chars(begin=size-6000, end=size, name="pybackup")  # last ~100 lines only
```
For a 500KB rotating log, this reads 6KB instead of 500KB. Critical for polling loops.

### 5. Shell Round-Trip via Terminus
```
send_to_view("python config.py --check\n", name="terminus")
# ... wait one beat ...
size = get_view_size(name="terminus")
get_view_chars(begin=size-3000, end=size, name="terminus")
```
No process spawn overhead. The terminal is already warm. Results land in the same
buffer you're already watching.

---

## Anti-Patterns (Each One Costs You)

| What you did | Why it's slow | Do this instead |
|---|---|---|
| `Read(path)` after already editing | Disk round-trip, burns context | `get_file_content(path)` |
| `Grep(pattern)` across whole repo | Spawns rg process, eats context | `find_in_files(pattern, folders=[tight_scope])` |
| `Bash("cat file")` | Two hops: shell spawn + disk | `get_file_content(path)` |
| `get_file_content` before `open_file` | Fails — file not in buffer | Always `open_file` first if unsure |
| `send_to_view` without trailing `\n` | Texts sits in prompt, never runs | Always end with `\n` |
| `get_view_content(name="terminus")` on huge log | Reads entire buffer | `get_view_size` → `get_view_chars` tail |
| `find_in_files(folders=["C:\\"])` | Scans everything, may crash | Scope to project root or subfolder |
| `str_replace` with wrong whitespace | Match fails silently | Copy old_str from `view` output verbatim |
| `run_command(scope="view")` | Focus-dependent, fragile | Use `scope="window"` or avoid |
| `find_in_file` (singular) | Searches only active tab | Use `find_in_files` (plural) |
| `toggle_comment()` | No path/name — broken | Use `str_replace` instead |

---

## Composite Recipes

### Recipe A: Read → Edit → Verify (no disk)
```
open_file("ui/app.py")                          # once
str_replace_based_edit_tool view, view_range=[40,60]   # check context
str_replace_based_edit_tool str_replace ...     # edit
str_replace_based_edit_tool view, view_range=[38,65]   # verify ±3 lines
```
Four ST calls. Zero disk reads after `open_file`.

### Recipe B: Find Symbol → Jump → Edit
```
find_in_files("class BackupJob", folders=["C:\\Users\\donal\\projects\\pybackup"])
# → returns path + line number
open_file(path, line=N)                         # jump straight to it
str_replace_based_edit_tool str_replace ...
```

### Recipe C: Run Script → Check Output
```
send_to_view("python -m pytest tests/ -x -q\n", name="terminus")
# ... tests run ...
size = get_view_size(name="terminus")
get_view_chars(begin=size-4000, end=size, name="terminus")
```

### Recipe D: Multi-file Edit (same pattern, multiple files)
```
results = find_in_files("OLD_CONSTANT", folders=[...], regex=False)
# for each result:
str_replace_based_edit_tool str_replace, path=result.path, old_str="OLD_CONSTANT", new_str="NEW_CONSTANT"
```
Each edit auto-opens the file. All files end up open in ST with gutter diffs visible.

### Recipe E: Poll a Log While a Job Runs
```
# Kick off the job:
send_to_view("python backup.py\n", name="terminus")

# After expected completion, read tail:
size = get_view_size(name="pybackup.log")
get_view_chars(begin=size-3000, end=size, name="pybackup.log")
```

---

## Speed Comparison (approximate)

| Operation | Standard tools | ST MCP |
|---|---|---|
| Read 500-line file | Read → disk → context | open_file + get_file_content → RAM |
| Edit 3 lines | Edit → disk read + write | str_replace → buffer update |
| Search 20 files | Grep → rg spawn → parse | find_in_files → ST index |
| Run + read output | Bash → shell spawn + stdout | send_to_view + get_view_chars |
| Read log tail | Bash "tail -n 50" | get_view_size + get_view_chars |

ST MCP is 2–4× faster in practice because:
1. No process spawns for reads/edits
2. Files stay warm across the entire session
3. Search uses ST's already-built index
4. Context usage is lower (no full-file echoes when you only need a slice)

---

## Session Setup Checklist

At the start of any session touching pybackup:
1. `open_file("C:\\Users\\donal\\projects\\pybackup\\ui\\app.py")`
2. `open_file("C:\\Users\\donal\\projects\\pybackup\\config.py")`
3. Open or verify Terminus tab is alive (`get_open_files` → check for "terminus")
4. Open the log: `open_file("C:\\Users\\donal\\.cache\\pybackup\\pybackup.log")`

Everything after that is RAM-resident.

---

## The One Rule That Covers 80% of Cases

> **If you're going to touch a file more than once, open it in ST at session start.**
> **Use `str_replace_based_edit_tool` for all edits.**
> **Use `get_view_chars` tail for all logs.**
> **Never use Bash for file content — only for things ST can't do.**
