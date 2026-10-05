---
name: feedback_reduce_permission_prompts
description: "User's Enter key is physically wearing out from repeated permission-prompt approvals — proactively reduce prompt frequency, don't just accept it as background friction"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 69b34a17-8b23-4cbc-bdfd-4f309354256c
  modified: 2026-09-09T08:46:41.489Z
---

The user is wearing out their Enter key from repeatedly approving
permission prompts. This is a physical, real cost to them, not minor
friction to shrug off.

**Why**: stated directly 2026-09-09 while discussing wanting to
click instead of pressing Enter on numbered prompts.

**How to apply**: proactively suggest running the `fewer-permission-prompts`
skill (scans transcripts for repeatedly-approved read-only Bash/MCP
calls and adds them to `.claude/settings.json` allowlist) when a
session involves a lot of repeated similar tool approvals, rather than
waiting for the user to complain. Also lean toward batching independent
tool calls (fewer distinct prompts) and favoring already-allowlisted
tools/patterns when equivalent options exist.
