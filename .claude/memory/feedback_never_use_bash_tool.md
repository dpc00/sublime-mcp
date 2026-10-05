---
name: never-use-bash-tool
description: "2026-10-03 Donald: never use the Bash tool; he can only bear to look at tool calls for about a second; do not route Bash work through background agents either (he corrected that); use the dedicated tools, and PowerShell with a plain-English description and the code in a script file"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-05T01:59:05.298Z
---

Donald said "don't use Bash ever!" after repeatedly objecting that long commands shown in his conversation are confusing and hard to look at ("I can tolerate looking at those for about 1 second").

**Why:** the Bash tool shows the full command text in the conversation; he cannot read it and has to look away.

**CLARIFIED 2026-10-03 (later):** the objection is to Linux/Bash syntax, not to shells as such. Donald: "bash is a vile piece of linux shit that no one should be exposed to. Dos, use dos commands!" So: never the Bash tool; when a command line is really needed, use plain DOS (cmd.exe) commands (dir, copy, type, del, and so on), run through the PowerShell tool as `cmd /c ...`, kept tiny and readable. This replaces the "treat PowerShell the same / tell him you cannot" lines below. Prefer the dedicated tools (Read/Write/Edit/Glob/Grep, sublime-mcp) first.

**How to apply (earlier text, partly superseded):** never call Bash. "Don't use" means don't use: no workaround, and in particular do NOT route Bash work through a background agent (he corrected me on that). Use Read/Write/Edit/Glob/Grep, the sublime-mcp tools and the Gmail/GitHub MCP tools instead. If something cannot be done without a shell, say so in one line and let him decide. Treat PowerShell the same way unless he says otherwise. Related: [[feedback_permission_prompt_plain_english]], [[feedback_keep_output_small_he_scrolls]].
