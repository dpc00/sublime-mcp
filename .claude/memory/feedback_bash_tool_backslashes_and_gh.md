---
name: bash-tool-collapses-double-backslashes
description: "In this harness the Bash tool turns two backslashes in a command into one, which breaks Python source, regexes and issue bodies passed via heredocs; write files with the Write tool instead"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1e07794b-efe6-4e5f-bbc3-7d3161a16a46
  modified: 2026-09-25T10:05:40.228Z
---

Observed repeatedly on 2026-09-25: `replace('\\', '/')` arrived as `replace('\', '/')` (SyntaxError), and heredoc bodies containing `\\` or unbalanced quotes made the whole `bash -c` fail to parse.

**Why:** the command string is unescaped once before the shell sees it.

**How to apply:** for any script or issue body containing backslashes, regex escapes or quote-heavy text, create the file with the Write tool (or use `chr(92)` in one-liners) and run it; put issue batches into a Python file of `(repo, title, body)` tuples and file them with `campaign_tools/file_issues.py`. Also: `get_console` inside `batch` ignores `tail` and dumps ~240 KB - use `mode='captured'` (it only sees the 3.8 host, not 3.3-host tracebacks). See [[project-static-triage-campaign]].

**2026-09-26 cost of this trap:** sublimehq/package_control#1771 was posted with its backslashes stripped (`\?\UNC` instead of `\?\UNC`); deathaxe replied "the reproduction or proposed fixes are invalid". The analysis was right, the text was garbled. Always write issue bodies with the Write tool (or a quoted heredoc), build backslash strings with `chr(92)` in test code, and after posting run `gh issue view N --json body` and eyeball the backslash-heavy lines.
