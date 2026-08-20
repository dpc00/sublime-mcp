# Road forward: compiled engine for heavy MCP data work

Sublime’s plugin host is Python. That is fine for editor orchestration (views,
selections, commands, MCP JSON-RPC). It is the wrong place to burn cycles on
workspace-scale scan, diff, and token work that agents trigger constantly.

Do **not** rewrite the MCP server in assembly. Keep Python as the orchestrator;
offload only the hot loops to a compiled `.dll` / `.so` (C, optional SIMD)
loaded in-process via `ctypes` / CFFI.

```
[ AI agent ]
     │  MCP JSON-RPC
     ▼
[ ST plugin (Python) ]  ── ctypes / CFFI ──►  [ compiled engine ]
     │                                              │ mmap / SIMD scan
     └──────────── structured result ◄──────────────┘
```

## What to offload

Leave UI and buffer commands in Python (`split_layout`, scratch tabs, save,
`eval_python`). Move:

- Fuzzy / regex codebase search (today `find_in_files` still round-trips
  through ST’s panel; a compiled scanner can search buffers and mmap’d files
  without that)
- Diff / unique-match location before `str_replace`
- Token counting and context truncation before a large buffer is shipped to
  the model

## Shape of the engine

A small C library, not a second MCP stack. One concrete primitive: scan a
memory buffer (AVX2 32-byte chunks, scalar tail). Compile with
`-O3 -mavx2 -shared` to `fast_search.dll` (Windows) or `fast_search.so`
(macOS/Linux), load next to the plugin, set `argtypes` / `restype`, and call
from a tool handler.

The handler should pass a pointer into an already-open view
(`view.substr(...)` or, better, a mmap of the on-disk file) — do not
`open()`+`read()` from Python on the hot path.

Expose one or two MCP tools (`ultra_fast_buffer_scan`, later a mmap’d
workspace grep). Keep the existing typed tools as the default; this is an
accelerator, not a replacement.

## After the in-process engine

1. **mmap** workspace files so the engine walks them as memory, not as copied
   Python strings.
2. **IPC** for the standalone Node/Python proxy: Unix domain sockets or shared
   memory instead of localhost TCP, if measurement still shows the loopback
   hop as the limiter. Measure first — ST main-thread `set_timeout` is often
   the real fixed cost (see `batch`).

## Constraints

- ST’s API is not thread-safe. The compiled scan may run off-thread; handing
  results back into views still goes through `_on_main`.
- Do not SIMD-optimize command dispatch, layout, or MCP framing.
- Ship the `.dll`/`.so` beside the plugin; do not spawn a subprocess per
  search.
