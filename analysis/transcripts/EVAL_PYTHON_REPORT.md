# What agents were doing with `eval_python`

This is a semantic follow-up to the general transcript audit. It analyzes the
code argument of `eval_python` calls without preserving raw code, prompts,
credentials, or tool output.

## Scope and correction to the first audit

- 1,424 `eval_python`/`eval_python_latest` invocation records were observed.
- Code was recoverable and classified for 1,406 calls across 66 transcripts.
- The dated portion spans 2026-07-10 through 2026-08-15: 22 active days in a
  37-day interval, not the full lifetime since the 2026-05-24 initial commit.
- 1,385 calls (97.3%) came from transcript paths associated with **SText** or
  **GhostShell**. Only 18 came from sessions rooted in `sublime-mcp` itself.
- Activity was bursty: 652 dated calls occurred in ISO week 33 alone.

This substantially qualifies the earlier conclusion. The data primarily
describes intensive development and testing of terminal packages inside
Sublime Text, performed by agents without a purpose-built skill. It is not a
representative sample of ordinary editor use over the MCP's full lifetime.

## Behavioral classification

Categories overlap because one code snippet can discover a view, inspect its
buffer, focus it, and invoke a terminal command.

| Behavior found in code | Calls | Sessions |
|---|---:|---:|
| AI Terminal/Terminus control | 915 | 53 |
| Window/view discovery | 659 | 44 |
| Buffer inspection | 548 | 50 |
| Sublime command execution | 277 | 28 |
| Settings/package-resource inspection | 219 | 35 |
| Selection/region manipulation | 108 | 20 |
| Tab closing and view lifecycle | 107 | 18 |
| View/group focus navigation | 100 | 14 |
| Plugin reload/testing | 69 | 23 |
| Buffer mutation | 65 | 7 |
| Viewport/layout geometry | 63 | 11 |
| Panel/console control | 41 | 9 |
| Timers/asynchronous scheduling | 13 | 6 |
| Clipboard access | 5 | 5 |
| Not classified by these patterns | 226 | 32 |

The surrounding requests in the busiest sessions concern terminal scrollback,
TUI keyboard protocols, cursor synchronization, copy mode, permission prompts,
mouse positioning, replaying terminal recordings, moving the terminal into the
GhostShell package, reloading plugins, and recovering after Sublime crashes.

## What this says about MCP holes

### Strong evidence of a hole: stable view identity and targeting

The most frequent API references were `sublime.active_window` (319),
`window.views` (208), `sublime.windows` (121), `view.id` (70),
`window.active_view` (66), and `window.focus_view` (48).

Agents repeatedly had to locate the correct window/view, distinguish terminal
views from ordinary buffers, focus a view, and then verify that focus or state
had changed. Existing tools are too active-view-oriented and do not provide a
single stable target model.

A better core should give every returned view a stable handle and accept that
handle on read, focus, selection, viewport, command, and lifecycle operations.

### Strong evidence of a hole: package-specific command schemas

Terminal commands dominated both escape hatches. Through `eval_python`, the
leading commands included `ai_terminal_keypress` (138), `ai_terminal_click`
(21), `ai_terminal_open_here` (18), and `ai_terminal_send_string` (14). Through
the public `run_command` tool, AI Terminal/Terminus commands accounted for at
least 83% of statically identified commands.

The hole is not “add hundreds more package commands to the core.” It is a
package capability protocol:

1. Packages register named capabilities with schemas and result contracts.
2. The MCP exposes those capabilities dynamically.
3. A package or skill documents safe sequences and state checks.
4. Raw `run_command` remains the fallback for unregistered packages.

### Strong evidence of a hole: terminal interaction as a stateful workflow

The agents were not merely sending strings. They were testing key events,
scrollback modes, mouse clicks, cursor location, screen dumps, copy mode,
permission prompts, and terminal focus. These operations depend on terminal
state and must be verified after each transition.

That supports a terminal adapter with operations such as:

- locate/open terminal and return a stable handle;
- read screen plus cursor/mode metadata;
- send text, keys, and mouse events;
- wait for screen/state change;
- enter/leave scrollback or copy mode;
- recover focus and report why input is unavailable.

This belongs in the terminal package integration, not as 100 generic Sublime
commands.

### Moderate evidence of a hole: atomic tab/view lifecycle

`close_file` was invoked 45 times from inside `eval_python`, and view lifecycle
patterns occurred in 107 calls. This agrees with the existing agent guide's
warnings about dirty/scratch tabs. The public close tool does not adequately
cover “identify exact view, decide how to handle dirty state, close, verify.”

### Moderate evidence of a hole: safe inspection primitives

Buffer inspection appeared in 548 calls even though several read tools exist.
Some of this was terminal-specific, but it also indicates fragmentation among
`get_view_content`, `get_sheet_content`, `get_view_size`, `get_view_chars`, and
active-file operations. One targeted read operation should cover file-backed,
scratch, panel, and terminal views consistently.

### Weak evidence: ordinary editing and LSP/debugging

Only 65 classified calls performed buffer mutation. Direct typed editing was
also rare. No Debugger tools and only two LSP tools were observed. Because the
corpus is dominated by terminal-package development and no MCP skills existed,
this does **not** prove those domains lack value. It proves only that this
corpus cannot justify their present default prominence.

## Effect of having no skills

The lack of skills is a major confounder in two directions:

1. Agents fell back to `eval_python` because they lacked a prescribed workflow
   for choosing and sequencing existing tools.
2. A 445-tool catalog is itself difficult to discover and reason about, so a
   skill alone would still need a much smaller recommended surface.

The correct experiment is not immediate deletion. Create one terminal-control
skill and one editor-state skill, then compare new sessions against this
baseline:

- escape-hatch calls per task;
- calls required to identify and target a view;
- repeated calls caused by focus/state uncertainty;
- failures and corrective retries;
- whether any supposedly unused typed tools become useful when routed by a
  skill.

## Recommended interpretation

The transcript evidence supports a staged conclusion:

1. **Certain:** terminal/package development drove nearly all escape-hatch use.
2. **Certain:** stable view targeting and package command schemas are missing.
3. **Likely:** terminal interactions need a stateful adapter rather than more
   serial command wrappers.
4. **Plausible but unproven:** many of the 409 unobserved tools can be removed
   from the default catalog.
5. **Not established:** LSP and Debugger capabilities are intrinsically
   useless. This corpus did not exercise those workflows.

The next sound step is to build the two small skills/adapters, collect another
meaningful period of usage, and compare behavior before deleting the legacy
surface.

## Supporting artifact

`analysis/transcripts/eval_python_analysis.json` contains the aggregate
categories, dates, API references, command names, repeated-snippet hashes, and
busiest transcript paths. It intentionally omits raw code and transcript
content.
