---
name: where-campaign-records-live
description: Where evidence of already-audited packages lives (repo log formats, GitHub, retained Claude Code transcripts) and that ~/data/logs was purged; always search all of them before queuing or starting a package.
metadata:
  type: reference
---

Donald (2026-09-29): "you are supposed to record everything. There are logs" -- WakaTime and SFTP were already logged and my first queue missed them. Later: "too many logs were purged ... logging was established long ago, many months, but alarming build-up of files alarmed me."

**Places to check (all of them):**
1. `C:/Users/donal/projects/sublime-mcp/.package_skill_test_log.md` -- at least four entry formats: `### Day N (date): Name`, `## Package N: Name`, `## Name (queue N)`, `## #NNN Name`, plus early-phase bullets `- Name (#rank, installs, author) -- verdict`. Bullets like "needs dedicated MCP: no" / "DROPPED: no .python-version" are analysis/drop notes, not bug audits, but the early phase covered installs ranks ~15-304.
2. GitHub: issues/PRs authored by dpc00 (`campaign_tools/github_record_stats.py`; 624 issues in 445 repos as of 2026-09-29).
3. Retained Claude Code transcripts `C:/Users/donal/.claude/projects/C--Users-donal-projects-sublime-mcp/*.jsonl` (55 sessions, 214 MB, since 2026-09-01) -- `campaign_tools/transcript_coverage.py`.
4. `~/data/logs/ghostshell/session_text_logs` only covers 2026-09-19..09-28: older logs were deliberately purged by Donald because of file build-up. Do not recreate that build-up; if a new durable record is wanted, ask first and keep it to one small file (GhostShell AGENTS.md rule 13 also requires owner approval for new log locations).

Queue: `campaign_tools/queue_v2_by_installs.json` (see [[project_campaign_queue_order_flaw]]).
