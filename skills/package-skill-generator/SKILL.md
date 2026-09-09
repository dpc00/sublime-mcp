---
name: package-skill-generator
description: Generate a small skill file that teaches an agent how to directly control an installed Sublime Text package (its real commands, dispatch tables, and any async/API gotchas) via sublime-mcp's existing generic tools -- instead of generating a standalone MCP server for it. Use when asked to "make an MCP for <package>", "let Claude control <package>", or to document a package's real capability surface for reuse.
---

# Package Skill Generator

Produces a **skill file** (`SKILL.md`, standard Agent Skills format --
folder + frontmatter, no code) documenting exactly how to control one
target Sublime package directly through sublime-mcp's own generic tools
(`get_package_mcp_info`, `run_command`, `eval_python`) -- not a standalone
MCP server.

**Why a skill instead of a server, and when that's not the answer:**
confirmed directly (2026-09-08, against three real, structurally different
packages -- Debugger, GotoRelated, OpenFileOverSSH) that the generic loop
(discover -> read the target's real source -> call it with `run_command`/
`eval_python`) is sufficient on its own for an agent that already has that
generic access. A dedicated MCP server was never actually *required* for
control in any of those three cases -- confirmed by directly reading even
debugger-mcp's own deepest handlers (e.g. `mcp_debugger_get_variables`),
which turned out to be a couple of lines wrapping `core.run(...)`, not
bespoke logic that justified a ~2,000-line standalone package. A skill
captures the one genuinely valuable thing those bigger builds were for --
the *investigation* (the real dispatch table, the async-bridging trick,
the object graph) -- as cheap, editable text instead of a server.

A standalone server (see the older `package-mcp-generator` skill, kept for
this case) is still the right call in the narrow case a skill can't cover:
a client with **no** `eval_python`-equivalent of its own, or a capability
that must be reachable independent of any particular agent session. Ask
which situation this is before picking a path -- default to a skill.

## Step 0 — check for an existing skill first

Look in the environment's own skills location (for Claude Code, in the
absence of other instruction, `~/.claude/skills/<name>/`) for one already
covering this package. If one exists, read and update it rather than
generating a duplicate.

## Step 1 — introspect, but do not stop there

Same investigative work as before, because it's the part that's actually
valuable, independent of what the output format is:

Call `get_package_mcp_info(package)`. **This alone is not enough for
anything but the most trivial package** -- confirmed against Debugger:
introspection surfaced only 5 commands and missed ~28 of the ~33 real
actions a single dispatch-style command drives, because most were never
exposed via `.sublime-commands`. Read the `python_files` it lists --
particularly anything that looks like a command-dispatch table
(`commands.py`, `menus.py`) or a live-state module (`console.py`,
`session.py`) -- via `str_replace_based_edit_tool` or `eval_python`, not
just the introspection result.

Also confirmed independently on OpenFileOverSSH and a fresh install of
Debugger: a package installed or loaded moments ago may not be in
`sys.modules` yet, and `get_package_mcp_info` will report an empty result
that means "not loaded," not "genuinely has nothing." Check `sys.modules`
before trusting a zero. Don't hand-edit `sys.modules`/`sublime_plugin`'s
own bookkeeping to force this -- it desyncs the plugin host from reality;
wait, or ask for a restart.

**Check for async before documenting any live-state or control call as a
one-liner.** Confirmed via debugger-mcp's own source: calling an
`async def` method directly, unawaited, silently does nothing -- it just
builds a coroutine object. If a target method is async, find and document
the package's own sync-bridge (e.g. a `core.run(coro)`-style helper) and
show it in the skill, not a bare call.

Treat the target's internals as unstable, non-public API: any documented
attribute-access snippet should use `getattr(obj, "x", None)` defensively,
matching how the real debugger-mcp does it -- a Package Control package's
internal shape can change between versions with no notice.

## Step 2 — coverage audit, before writing the skill

Same as before: tally every action found in the dispatch source and every
state-bearing property found across every module actually read, against
what the skill will actually document. Confirmed repeatedly that this
number is the only honest way to answer "how complete is this" -- it
ranged from 100% (a package with exactly one real command) to ~40% (a
package with a large, only-partially-investigated internal API) across
the three packages tested so far.

## Step 3 — write the skill file

Standard Agent Skills format: a folder named for the package (e.g.
`<package>-control/`) containing `SKILL.md` with `name`/`description`
frontmatter, placed in the environment's own skills location (for this
project, mirror the existing `skills/sublime-debugger/`-style layout only
if it's meant to ship with this repo; otherwise the user's own
`~/.claude/skills/` is the real, standard location -- see
`get_package_mcp_info`'s own tool description for this same distinction).

Body content, concretely:
- What the package actually does (from Step 1's real findings, not the
  package's own marketing description).
- The exact `run_command`/`eval_python` calls to use, with real argument
  shapes -- copy-pasteable, not pseudocode.
- Any async-bridge, defensive-access, or "not loaded yet" gotchas from
  Step 1 that a future agent would otherwise have to rediscover.
- The Step 2 coverage tally, so a future reader knows the boundary without
  re-deriving it.

No server boilerplate, no ports, no `.python-version`, no MCP JSON-RPC
layer -- none of that machinery is needed because nothing is being served
independently; the skill's whole job is telling an agent what to type into
tools it already has.

## Step 4 — verify by actually using it

Before considering the skill done, follow it yourself for one real
action against the real package -- not a syntax check, an actual
`run_command`/`eval_python` call producing a real result. A skill that
looks complete but was never actually exercised is exactly the failure
mode Step 1's own lessons exist to prevent.

## Step 5 — report the gap honestly

Hand back the Step 2 coverage tally, not a vague caveat. Don't present a
generated skill as a complete API reference if it only covers what one
investigation pass actually found and verified.
