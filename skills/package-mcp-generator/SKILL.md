---
name: package-mcp-generator
description: Generate a standalone MCP server plugin that lets an AI agent control an installed Sublime Text package. SECONDARY path -- default to the package-skill-generator skill instead (a cheap skill file, not a server) unless the client genuinely has no eval_python-equivalent of its own, or the capability must be reachable independent of any agent session. Use this one only when that specific condition applies.
---

# Package MCP Generator

**Read this first: default to `package-skill-generator`, not this skill.**
Confirmed directly (2026-09-08) against three real packages that the
generic discover-then-call loop (`get_package_mcp_info` -> read source ->
`run_command`/`eval_python`) is sufficient on its own for an agent that
already has that access -- no standalone server required in any of them,
including debugger-mcp's own deepest handlers on inspection. Reach for
*this* skill only in the narrow remaining case: the client calling has no
`eval_python`-equivalent of its own, or the capability genuinely needs to
be reachable independent of any particular agent session. If neither is
true, stop and use `package-skill-generator` instead.

Produces a **new, standalone** Sublime Text plugin — its own Packages/ folder,
own settings file, own port, own tool catalog — that bridges one target
package to an MCP-speaking agent. Matches the shape of `debugger-mcp` and
`lsp-mcp` exactly. Never merges the result into sublime-mcp's own tool
catalog via `register_mcp_tools`; that reintroduces the command-namespace
mixing a Package Control reviewer already flagged once for this codebase.
`register_mcp_tools` is available as a last-resort option only for a
single trivial one-off wrapper too small to justify its own package —
default to a standalone package.

## Step 0 — refuse if the target is already MCP-serving

Never generate an MCP wrapper for something that already speaks MCP itself.
Check, in order:

1. Hardcoded denylist: `sublime-mcp`, `debugger-mcp`, `lsp-mcp`, and any
   other package this same generator has already produced.
2. Name/description contains "mcp" or "model context protocol"
   (case-insensitive).
3. Source scan for `register_mcp_tools`, `/mcp`, `/sse` route registration,
   or "Model Context Protocol" text in the target's own `.py` files.

If any check hits, stop and tell the user why, naming the specific match.

## Step 1 — introspect, but do not stop there

Call `get_package_mcp_info(package)` (sublime-mcp). It returns registered
command classes, `.sublime-commands` entries (with captions/args), settings
keys, and a flat list of the package's `.py` files.

**A package installed moments ago — by any method, a raw directory drop or
a proper Package Control install — may not be loaded into the running
process yet.** Confirmed empirically twice: right after installing a test
target, `get_package_mcp_info` returned empty `commands`/`settings_keys`
both times, not because the package has none, but because Sublime's own
loader hadn't picked it up yet (`eval_python`: `import sys;
'<Package>' in ' '.join(sys.modules)` came back empty). An empty result
here is not proof the target has no commands — check whether the target's
module is actually in `sys.modules` (via `eval_python`) before trusting it,
and if it isn't, either wait and retry or ask the user to confirm it's
working (visible in a menu, runs from the command palette) before treating
the introspection as final.

**Do not manually delete entries from `sys.modules` or otherwise hand-edit
Sublime's plugin bookkeeping to force a reload.** Confirmed the hard way:
doing this desynced `sublime_plugin`'s internal registries from reality —
a command class stayed registered and fully functional in
`text_command_classes` for a deleted package whose files were long gone
from disk, and separately a genuinely-installed package's module flickered
in and out of `sys.modules` between successive checks, both traceable to
manual `sys.modules` surgery earlier in the same run. If a target needs to
be loaded and waiting doesn't work, ask for a restart rather than hand-edit
Python's or Sublime's live bookkeeping — the debugging cost of a desynced
process is much higher than the cost of one restart.

**This alone is not enough for anything but the most trivial package.**
Confirmed empirically against the real Debugger package: introspection
surfaced only 5 commands, and for the single dispatch-style `"debugger"`
command that actually drives ~33 distinct actions via an `action` argument,
it captured exactly **one** example value — because most of those actions
are exposed only through the package's own menus, not `.sublime-commands`.
The real debugger-mcp's full action table only exists because someone
opened and read the target's own `modules/commands.py`.

So: after the introspection call, look at the returned `python_files` list
for the target's own command-dispatch or menu-definition source (names like
`commands.py`, `menus.py`, `actions.py`) and actually read it — via
`str_replace_based_edit_tool` (command="view") or `eval_python` — to find
the real, complete action/command surface.

Do not stop at the dispatch table. Also find and read every module that
holds *live state* a capability might need (session status, console
buffers, breakpoints, variables, results) — not just the one or two needed
for a minimal working set. Confirmed empirically: for the real Debugger
package, the dispatch table plus a basic state/breakpoint/control layer
covers roughly 40% of what the hand-maintained debugger-mcp actually
exposes (33 mechanical actions + 9 tools vs. its ~104) — the other ~60% is
entirely deep session/variable/protocol reads (call stacks, evaluate,
threads, disassembly, memory, custom protocol requests) that only exist
because someone read `modules/dap/session.py`, `modules/dap/variable.py`,
and `modules/dap/dap.py` specifically. Treat every plausible state-bearing
module in the target's `python_files` list as in scope, not just the first
one that makes something work end to end.

**Check for async before wiring any live-state or control method to a
tool.** Confirmed empirically: the real debugger-mcp's own `mcp_debugger_control`
calls `dbg.start()` / `.pause()` / `.stop()` directly, but those are
`async def` methods in the target's actual source — called without being
awaited or run, that just constructs a coroutine object and silently does
nothing. If a target method is `async def`, find the target's own
sync-execution bridge (grep its source for how it runs its own coroutines
internally — e.g. a `core.run(coro)`-style helper) and use that same
bridge; never assume a plain call to an async method has any effect.

Treat the target's internals as unstable, non-public API throughout: guard
every access defensively (e.g. `getattr(obj, "buffer", None) or ""`,
wrapped in `try/except`), the way the real debugger-mcp does — a Package
Control package's internal shape can change between versions with no
notice.

## Step 2 — coverage audit, before writing anything

Before generating the package, produce an explicit tally: every action
found in the dispatch source, every state-bearing method/property found
across every module actually read, and which of those the generated
`TOOLS` list will actually implement. This is the artifact that makes
"how complete is this" answerable with a number instead of a feeling —
show it to the user before or alongside the generated package, not buried
in a comment.

## Step 3 — generate a complete standalone package, directly in Packages/

Output goes straight into Sublime's real `Packages/<package>-mcp/`
directory (`sublime.packages_path()`) as its own independent, uncommitted
plugin — **not** inside the sublime-mcp repo's own `packages/` tree, and
not registered into sublime-mcp's own tool catalog. sublime-mcp's repo
holds only its own hand-maintained, deliberately-chosen companions
(debugger-mcp, lsp-mcp); a generator meant to be thrown at any of 4700+
installed packages must not accumulate its output there.

Layout:

- `.python-version` containing `3.8` (copy debugger-mcp's/lsp-mcp's file
  verbatim). **Required, not optional.** Confirmed empirically: without it,
  ST loads the same plugin into both of its plugin_host processes (3.3 and
  3.8 run simultaneously) at once, and both independently bind the same
  hardcoded port — two servers listening on one port, with which one
  actually answers a given request effectively random. Symptom looked like
  a flaky server ("empty reply from server" on some requests, fine on
  others) with no obvious cause until `netstat` showed two different PIDs
  owning the same port.
- `<package>_mcp.py` — the plugin. Reuse debugger-mcp's/lsp-mcp's generic
  MCP-server boilerplate **verbatim** (the `_ThreadingHTTPServer`,
  `_MCPHandler` do_GET/do_POST/SSE handling, `register_mcp_tools`/
  `unregister_mcp_tools`, the seven-default-tools-plus-`discover_tools`-
  plus-`batch` pattern) — that part is generic MCP-server plumbing, not
  target-package-specific, and is safe to copy mechanically.

  **The boilerplate that actually matters is the real MCP JSON-RPC layer —
  `initialize` / `tools/list` / `tools/call` served over `/mcp` (streamable
  HTTP) and/or `/sse` + `/messages` (legacy SSE), exactly as
  `_mcp_dispatch`/`_MCPHandler` implement it in debugger-mcp. A URL-path-
  per-tool-name REST shortcut (`POST /<tool_name>` returning the raw tool
  result) is NOT MCP, even though it looks similar and even though calling
  it directly with curl appears to work fine.** Confirmed the hard way:
  built exactly that REST shortcut, verified each tool endpoint individually
  with curl, and called it "verified working end-to-end" — it was not. It
  had no `/mcp` or `/sse` route at all, so any real MCP client (Claude Code
  via `claude mcp add`, or anything else) would fail immediately at
  `initialize`. The gap only surfaced when asked "would this work if
  registered in Claude Code's MCP config" — a question worth asking of
  every generated package before declaring it done, not after. The REST
  shortcut can still be included as a bonus convenience (sublime-mcp's own
  `_GET`/`_POST` dict-by-path pattern is exactly this, and is legitimate
  there because it's a documented *additional* bridge, not the only
  transport) — it must never be the *only* thing generated.

  "Verbatim" means literally that, not "reimplemented from memory of the
  pattern": confirmed empirically that paraphrasing it produced a plugin that
  answered `get_help` in testing but returned "empty reply from server" on
  a real tool call, because the rewrite dispatched the handler via
  `sublime.set_timeout` onto the main thread and returned before the
  response was written, racing the HTTP connection closed. The real
  debugger-mcp does not do that — it calls the tool handler directly on the
  HTTP worker thread (`entry[3](tool_args)` inside `_mcp_dispatch`, no
  main-thread marshaling at all) and writes the response synchronously
  right after. Copy that exact shape; do not "improve" it toward
  sublime-mcp's own `_on_main` pattern, which solves a different problem
  (sublime-mcp is a single shared server every tool call goes through;
  each generated package is its own small server and doesn't need it).
  Only the `TOOLS` list and its handlers are genuinely new, written from
  what Step 1 actually found in the target's source.
- `<package>-mcp.sublime-settings` — `mcp_port`/`http_port` keys. Pick ports
  outside the existing 9500–9506 / 9515–9516 range already used by
  sublime-mcp/debugger-mcp/lsp-mcp, and outside any other generated
  package's ports already present in `Packages/`.
- `AGENT_GUIDE.md` — served by a `<prefix>_get_help` tool, same convention
  as the other MCPs, and includes the Step 2 coverage tally verbatim so a
  future agent reading it knows the boundary without re-deriving it.
- A companion Claude Code skill, if the user's environment uses one, placed
  wherever that environment's other per-package skills live (for this
  repo's own established companions that's `skills/<package>-mcp/`, but a
  generated package is not part of this repo, so prefer the user's global
  skills location unless told otherwise), modeled on `skills/sublime-debugger/`.

## Step 4 — verify against the real protocol, then a real client

Calling individual tool endpoints directly (however that's wired) only
proves the business logic runs — it proves nothing about whether the
package actually speaks MCP. After reloading the generated plugin, verify
in this order:

1. Raw JSON-RPC against `/mcp` with curl: `initialize`, then `tools/list`,
   then `tools/call` for each tool. All three must round-trip correctly
   before this counts as "working."
2. Register it for a real client: `claude mcp add --transport http
   --scope project <name> http://127.0.0.1:<port>/mcp`. Default to
   `--scope project` (writes to `.mcp.json` at the repo root) for testing a
   generated package, not `--scope user` (writes to the top-level
   `mcpServers` key in `~/.claude.json`, available from every project on
   the machine) — a generated/test package should stay contained and
   trivially removable (`claude mcp remove <name> --scope project`, or just
   delete `.mcp.json`) rather than polluting a global, shared config.
   `--scope user` is the right call only if the user explicitly wants this
   specific generated package available everywhere, not as the default for
   verifying one just got built. A new project-scope server needs
   interactive approval the first time (`claude mcp list` shows "⏸ Pending
   approval" until a human runs `claude` and approves it in that project)
   — this cannot be self-approved, by design, and that's correct: don't try
   to work around it.
3. Once approved, `claude mcp list` shows "✔ Connected" from any terminal,
   including this one — that alone does not prove tools are callable from
   *this* session. An already-running session never picks up a newly-added
   server on its own, no matter how long you wait. To call it from that
   same session, a user-run `/reload-plugins` is required — that's the step,
   not an optional nicety — or start a fresh session instead. Don't assume
   "it must be a session-start-only thing" (it isn't — `/reload-plugins`
   fixes it live) or treat another terminal's "✔ Connected" as proof this
   session can call it.
4. The reverse is not symmetric: after `claude mcp remove`, confirmed
   empirically that `/reload-plugins` in an already-running session does
   NOT drop a removed server from that session's live tool list, even
   though the same command picks up a newly-*added* one. Verify a removal
   actually took effect the same way as an addition — a fresh CLI check
   (`claude mcp list` in a new terminal) or a fresh session, not
   `/reload-plugins`, not the still-running session that had it loaded.

Only a tool call that round-tripped through this whole chain — a real
client, a real approval, a real invocation — is "verified." Everything
before that is a good sign, not proof.

## Step 5 — report the gap honestly

Hand back the Step 2 coverage tally, not a vague caveat: what fraction of
the target's real surface got implemented, exactly what's missing and
which source files would need reading to close each gap. Don't present a
generated package as equivalent in confidence to a hand-verified one
without saying so.
