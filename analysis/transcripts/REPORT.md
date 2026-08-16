# Sublime MCP transcript usage audit

> **Follow-up qualification:** deeper inspection found that 97.3% of
> `eval_python` calls came from SText/GhostShell sessions devoted largely to
> terminal-package development and testing during a short, bursty window. Read
> `EVAL_PYTHON_REPORT.md` before using the unused-tool counts to make removal
> decisions.

Generated from all `*.jsonl` files beneath user-level dot directories on
2026-08-15. The project began on 2026-05-24. The scanner parsed 1,154 files
(about 1.03 GB) from 13 client roots and counted structured tool invocations,
not text mentions.

## Executive result

- Current catalog: 445 tools
- Observed invocations: 2,832 (2,826 direct plus 6 calls inside `batch`)
- Tools ever observed: 36 (8.1% of the current catalog)
- Never observed: 409 (91.9%)
- Top three tools: 1,954 calls (69.0%)
- Top eight tools: 2,569 calls (90.7%)
- No Debugger MCP tool was observed.
- Only two LSP calls were observed: one `lsp_get_sessions` and one
  `lsp_get_diagnostics`, both in one Gemini transcript.
- Package tooling was represented by two `get_package_mcp_info` calls. No
  `search_packages` or `install_package` call was observed.
- `batch` was called only three times.

The product used in practice is an editor-introspection and arbitrary-Python
bridge, primarily for controlling terminal packages inside Sublime Text. It is
not being used as a broad typed Sublime/LSP/DAP command suite.

## Every observed public tool

| Tool | Calls | Sessions | Main clients |
|---|---:|---:|---|
| `eval_python` | 1,421 | 84 | Claude 959, Gemini 336, Kimi 108 |
| `get_view_content` | 338 | 34 | Claude 322 |
| `get_console_log` | 195 | 63 | Claude 103, Gemini 76 |
| `run_command` | 185 | 22 | Claude 171 |
| `get_sheet_content` | 179 | 30 | Gemini 111, Claude 59 |
| `get_sheets` | 110 | 53 | Claude 72, Gemini 24 |
| `get_open_files` | 74 | 46 | Claude 56 |
| `get_active_file` | 67 | 12 | Claude 64 |
| `get_console_full` | 35 | 27 | Claude 19, Gemini 11 |
| `get_view_size` | 34 | 4 | Kimi 32 |
| `get_commands` | 33 | 11 | Claude 28 |
| `get_view_chars` | 24 | 2 | Kimi 24 |
| `get_console_win` | 23 | 13 | Claude 18 |
| `str_replace_based_edit_tool` | 18 | 4 | Gemini 16 |
| `open_file` | 14 | 5 | Gemini 11 |
| `save_file` | 11 | 5 | Gemini 10 |
| `send_to_view` | 11 | 3 | Gemini 8, Claude 3 |
| `get_menu_items` | 10 | 5 | Claude 9 |
| `close_file` | 9 | 3 | Claude 8 |
| `get_file_content` | 8 | 3 | Gemini 6 |
| `get_selection` | 5 | 3 | Claude 4 |
| `batch` | 3 | 2 | Claude 2, Kiro 1 |
| `eval_python_latest` | 3 | 2 | Kimi 2, Gemini 1 |
| `get_command_palette` | 3 | 3 | Claude 3 |
| `get_project_folders` | 3 | 3 | Gemini 2, Grok 1 |
| `next_view` | 3 | 2 | Claude 3 |
| `get_active_panel` | 2 | 2 | Claude 2 |
| `get_layout` | 2 | 2 | Claude 1, Gemini 1 |
| `get_package_mcp_info` | 2 | 1 | Gemini 2 |
| `find_in_file` | 1 | 1 | Gemini 1 |
| `get_help` | 1 | 1 | Claude 1 |
| `lsp_get_diagnostics` | 1 | 1 | Gemini 1 |
| `lsp_get_sessions` | 1 | 1 | Gemini 1 |
| `prev_view` | 1 | 1 | Claude 1 |
| `replace_lines` | 1 | 1 | Grok 1 |
| `show_panel` | 1 | 1 | Claude 1 |

## What `eval_python` actually did

`eval_python` alone accounts for 50.2% of all calls. The scanner extracted
1,684 recognizable Sublime API references from its code. The dominant ones
were:

| API | References |
|---|---:|
| `sublime.active_window` | 319 |
| `window.views` | 208 |
| `sublime.windows` | 121 |
| `sublime.packages_path` | 102 |
| `sublime.Region` | 77 |
| `view.id` | 70 |
| `window.active_view` | 66 |
| `view.run_command` | 60 |
| `view.name` | 50 |
| `window.focus_view` | 48 |
| `window.run_command` | 47 |
| `view.size` | 40 |
| `view.sel` | 39 |
| `view.viewport_position` | 39 |
| `view.settings` | 37 |

The code passed through `eval_python` invoked 35 distinct Sublime commands
327 times. The leading commands were `ai_terminal_keypress` (138),
`close_file` (45), `ai_terminal_click` (21), `ai_terminal_open_here` (18),
`ai_terminal_send_string` (14), and `show_panel` (9).

This indicates two real missing abstractions:

1. Reliable view/window discovery and focus control.
2. A first-class terminal interaction API for AI Terminal/Terminus-like views.

## What `run_command` actually did

Of 185 public `run_command` calls, 182 contained a statically extractable
command name. Seventeen distinct commands were used:

| Command | Calls |
|---|---:|
| `ai_terminal_open_here` | 97 |
| `ai_terminal_send_string_window` | 25 |
| `ai_terminal_dump_screen` | 19 |
| `ai_terminal_keypress` | 8 |
| `close_by_index` | 6 |
| `terminus_keypress` | 6 |
| `st_config_open` | 5 |
| `settings_editor_open` | 4 |
| `ai_terminal_send_string` | 3 |
| `terminus_send_string` | 2 |
| seven one-off commands | 7 |

At least 151 of the 182 identified commands (83.0%) operated AI Terminal or
Terminus. `run_command` is therefore serving mainly as a package-specific
terminal protocol, not as a general editor-command facility.

## Common call transitions

The strongest adjacent-call patterns were:

| From | To | Occurrences |
|---|---|---:|
| `eval_python` | `eval_python` | 962 |
| `get_view_content` | `eval_python` | 202 |
| `eval_python` | `get_view_content` | 162 |
| `get_console_log` | `eval_python` | 88 |
| `get_view_content` | `get_view_content` | 84 |
| `get_sheet_content` | `get_sheet_content` | 83 |
| `eval_python` | `get_console_log` | 78 |
| `get_sheets` | `get_sheet_content` | 49 |
| `run_command` | `run_command` | 49 |
| `eval_python` | `run_command` | 48 |
| `run_command` | `get_view_content` | 42 |

Repeated `eval_python` calls and the `get_sheets` → `get_sheet_content`
two-step are clear candidates for higher-level operations. The almost unused
`batch` tool did not solve this in practice.

## Recorded outcomes

An outcome could be correlated for 2,820 calls. Most tools were reliable, but
the notable exceptions were:

- `get_console_win`: 10 failures in 23 calls.
- `eval_python`: 25 failures in 1,421 calls.
- `get_sheet_content`: 7 failures in 179 calls.
- `get_console_log`: 5 failures in 195 calls.
- `get_active_file`: 3 failures in 67 calls.

These are transcript-recorded client outcomes, not root-cause classifications.
The CSV provides transcript and line provenance for examining individual
failures without copying potentially sensitive result bodies into this report.

## Architectural implications

1. Retain `eval_python` as an opt-in escape hatch until its repeated patterns
   have explicit replacements. Removing it now would break most demonstrated
   use.
2. Build `workspace_snapshot` around windows, views, sheets, focus, selection,
   and dirty state. Those operations currently require repeated discovery.
3. Build a terminal provider with open/send/read/key/click/wait semantics. This
   is the actual package workflow represented by the transcripts.
4. Consolidate console access into one reliable tool; retire `get_console_win`
   after covering its distinct behavior.
5. Keep the small file/view core. Typed editing is rare but real and should be
   made atomic: edit, save, and verify in one operation.
6. Move the 409 unobserved tools, including the entire Debugger catalog and
   almost the entire LSP catalog, behind capability discovery or an opt-in
   legacy surface. Transcript evidence does not justify advertising them by
   default.
7. Package Control does not warrant a separate public MCP surface based on the
   observed history.

## Limits and security note

- “Unused” means absent from the available JSONL corpus and current catalog
  matching. Deleted historical tool names without a recognizable Sublime MCP
  prefix could be missed.
- Some clients store cumulative snapshots. Calls are deduplicated per
  transcript using call IDs; records without IDs are conservatively counted by
  line.
- Timestamps are absent in some Kimi records, so date ranges are incomplete.
- Several transcripts contain plaintext credentials inside command output.
  The generated CSV and JSON do not copy arguments or result bodies, but the
  original transcript stores should be treated as sensitive. Any still-active
  exposed credentials should be rotated.

## Artifacts

- `tools/analyze_sublime_transcripts.py` — reproducible scanner
- `analysis/transcripts/sublime_tool_usage.json` — complete aggregate,
  including all 409 unused catalog names and the top 100 transitions
- `analysis/transcripts/sublime_tool_calls.csv` — one row per observed call,
  with client, transcript path, line, timestamp, and batch marker
