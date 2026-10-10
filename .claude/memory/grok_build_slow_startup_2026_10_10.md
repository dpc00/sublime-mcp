---
name: grok-build-slow-startup-2026-10-10
description: 2026-10-10 Grok Build took 2 min to answer hello; MCP timings, what was stripped from ~/.grok config, the CLAUDE.md that cannot be switched off, Cursor support thread
metadata:
  type: project
---

Donald does not use Grok Build (extra $30). On 2026-10-10 he asked why "hello" took 2 minutes (Cursor support had said Grok waits for all MCP servers; 12 of 14 were connected when he typed).

**Findings (`grok mcp doctor`, Grok 1.0.41 then 1.0.50):** all 7 servers I had disabled are correctly configured; `excel-csv-mcp-server` took 31.6 s to start, `sqlite` (npx) 7.2 s, others 0.3 to 3.3 s. Doctor says "not found" for disabled servers, so each had to be enabled temporarily. Five more failures came from Claude's configs that Grok imports: three `sublime-mcp-*` SSE servers (not running), `google-multi` (/bin/bash on Windows), `sourcegraph` (unset SOURCEGRAPH_ENDPOINT).

**Changes made (all in ~/.grok, nothing in Claude's files):** `config.toml` now has only the `sublime-mcp` MCP server (keys removed with the other sections); `[compat.claude]`, `[compat.cursor]`, `[compat.codex]` switches set to false; `trusted_folders.toml` has `sublime-mcp` set to `trusted = false`. Backups: `config.toml.bak-mcp-slim-20261010` (full original, contains API keys in plain text), `config.toml.bak-compat-20261010`, `trusted_folders.toml.bak-20261010`. GhostShell and SText are still trusted in Grok.

**Why untrusted:** Grok always loads a top-level CLAUDE.md (the compat `agents = false` switch does not cover it), and gitignore/`.git/info/exclude` did not hide it (tracked file). Project instruction loading needs folder trust, so untrusting the repo stops it. `grok -p "hello"`: 28 s in the repo before, 7.6 s after (7.4 s in an empty folder). Not checked: whether `.claude/settings.local.json` permissions are still read.

**Cursor support:** two replies in the thread "Tried a few times in last few weeks to use Grok Build CLI..." (hi@cursor.com): the MCP findings, then the CLAUDE.md follow-up, both sent by Donald after editing my drafts. Do not poll for an answer. Drafts in that thread may not show in Gmail's Drafts view because older messages in it are trashed.

**How to apply:** if he ever uses Grok again, check the config and trust file first; do not re-enable the removed servers without asking. [[feedback_no_scheduled_polling_2026_10_07]]
