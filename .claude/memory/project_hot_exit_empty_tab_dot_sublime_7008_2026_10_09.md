---
name: hot-exit-empty-tab-dot-sublime-7008-2026-10-09
description: 2026-10-09: empty untitled tab comes back with a gray-green modified dot after a Sublime restart (hot_exit); reproduced on plain portable 4215; filed sublimehq/sublime_text#7008; what the dot and the title "untitled •" mean; portable launch was allowed by Donald
metadata:
  type: project
---

**What he saw:** after a restart an empty untitled tab showed a dot where it had shown a plain x. He first thought it was green (a green x on untitled tabs, seen from 2026-10-09), then gray; I measured the dot at RGB 132,170,131, a muted gray-green. The x/dot color is just this theme (Default Dark + Mariana).

**Test and result:**
- Main Sublime, twice: clean empty untitled tab (`is_dirty` false) before exit, `is_dirty` true after restart with hot_exit "always".
- Plain portable `D:\st_portable_4215` (no OpenUri, no GhostShell; only MCP Commander and the debugger packages), with its Preferences temporarily set to hot_exit "always" and remember_open_files true (backup restored afterwards, back to "disabled"/false): same result, x before, dot after. So it is Sublime's own behavior, not OpenUri (`OUIB_is_dirty` is OpenUri's private "recompute links" flag, not Sublime's modified state) and not GhostShell or sublime-mcp.
- Closing a dotted empty tab shows no Save prompt (three times). A dotted tab that holds text does prompt.
- The window title "untitled •" appears for any untitled tab, even a clean one (seen in the portable); it is not a dirty indicator.
- Filed: https://github.com/sublimehq/sublime_text/issues/7008 (low priority, cosmetic).

**Why:** Donald found the dot alarming because it implies he touched the buffer; the answer is that it does not.

**How to apply:**
- Tell him a dotted empty tab is safe to close; a dotted tab with text is real unsaved text.
- Mistakes of mine in this thread, so they are not repeated: I wrongly blamed leftover RainbowBrackets scheme files (see [[rainbowbrackets-leftover-scheme-green-x-2026-10-09]], corrected), I wrongly reported a "listing gap" in get_sheets/get_open_files (the empty group has no tab; withdrawn), and I first called the dot "by design" before the portable test.
- Portable 4215 may be launched when Donald asks for it (his word 2026-10-09). Key chords and menus do not work on it through computer-use; its sublime-mcp needs his `/mcp` reconnect, then the tools work (`mcp__sublime-mcp-portable-4215__*`). Quit it and restore any setting changed.
- Related: [[computer-use-keys-go-where-his-focus-is-2026-10-09]].
