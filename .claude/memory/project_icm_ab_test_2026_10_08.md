---
name: icm-ab-test-2026-10-08
description: 2026-10-08 Donald asked whether restructuring these notes the ICM way would improve things; A/B test of the current layout against a two-level catalog copy, 8 questions each, result and verdict
metadata:
  type: project
---

**Question (Donald):** he wants to learn the icm-architect skill and was not convinced by my walk-test list (which only showed rule compliance). I ran an A/B on a COPY, nothing in the repo moved.

**Design:** 8 questions whose answers sit in one specific note each (bash tool, no scheduled polling, where notes go, stock PR reply, no baton commits, no dev copies in projects, email claims, Qwen status). 16 headless `claude -p` runs (sonnet, read-only tools, one empty folder per arm, told to read only that folder; all 16 stayed inside their folder). Arm A: today's CLAUDE.md + full MEMORY.md (132 notes, about 5,800 tokens). Arm B: same note files, entry index of about 375 tokens listing 7 topic folders, each with its own small INDEX.md (200 to 1,900 tokens), the 3 stale notes in `_archive/`. Topics were assigned mechanically from keywords in each note's name and description, not tuned to the questions.

**Result:** accuracy tie, 8/8 and 8/8, right note found 8/8 in both (ceiling effect: the questions were too easy to separate them). Steps per lookup: A 1.4 tool calls, B 2.8 (the extra topic-index step). Seconds about 9 vs 10. Tokens per run similar (A 60.6k, B 70.5k, mostly the fixed prompt re-read on each turn; the cost figures are confounded by prompt caching and not trustworthy). The real difference is what loads at the start of every session: about 5,800 tokens vs about 375 (plus 200 to 1,900 only when a topic is opened). Side effects: in A one answer cited a note that the index itself flags as superseded (answer still right); B's archive removed that trap. B's mechanical grouping misfiled one note (the email-claims note landed in repo_hygiene), which cost that run 6 calls instead of 2.

**Verdict:** an ICM-style restructure does not improve correctness (not shown) and costs about one extra step per lookup; its measurable benefit is about 5,000 fewer tokens in the context of every session, and a cheap, low-risk piece is archiving stale notes. Not worth a wholesale move unless session-start size matters; if done, the grouping must be done by hand, not by keywords. **Not done:** a harder question set (answers spread over several notes, or questions the index cannot answer), a flat slimmed index arm (estimated only about 25% smaller, because 132 names and paths dominate), real-session timing. The scripts lived in the session scratchpad and were not kept.

Related: [[audit-exhausted-and-reload-hang-2026-10-08]] (same day), the icm-architect skill (`~/.claude/skills/icm-architect`).
