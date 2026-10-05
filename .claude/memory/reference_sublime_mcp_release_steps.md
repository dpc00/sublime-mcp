---
name: sublime-mcp-release-steps
description: "sublime-mcp releases are three publishing cycles: GitHub release (me), PyPI (me, twine + ~/.pypirc), npmjs (Donald, in a DOS console in tab 2 because of auth); version lives in 5 files; regenerate tool lists first"
metadata:
  node_type: memory
  type: reference
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-05T02:01:59.241Z
---

2026-10-02: Donald: "sublime-mcp is three publishing cycles, one is npm which I have to do in dos console myself because of auth requirement (tab 2)." Cycles = GitHub release, PyPI, npmjs. (The MCP Registry listing, `io.github.dpc00/sublime-mcp`, is separate. A registry query on 2026-10-05 returned versions 1.0.0, 1.7.2, 1.7.3, 1.7.4 and 1.7.5, so it was last published at 1.7.5 or later; the 1.12.0 `server.json` in the repo may not have been published there. This note previously said 1.7.3, which was wrong.)

**Steps I did for 1.12.0 (repo `C:\Users\donal\projects\sublime-mcp`):**
1. If tools were added: `python tools/build_tool_tree.py` (tool_tree.json; fails `test/test_tool_tree.py` otherwise) and `python tools/generate_fallback_catalog.py` (writes `packages/node-proxy/fallback-tools.json` and `packages/python-proxy/tool_catalog.py`); update the tool count (README, AGENT_GUIDE, docs/AGENT_GUIDE, docs/COMMAND_TOOLS).
2. Version in 5 places: `sublime_mcp.py` `__version__`, `packages/node-proxy/package.json`, `packages/python-proxy/pyproject.toml`, `server.json` (twice). `packages/node-proxy/package.json` has a UTF-8 BOM since before; leave it.
3. CHANGELOG.md entry on top (dense paragraph style); tests: `python -m unittest discover -s test -p "test_*.py"` (run from repo root) and the three `node test/*.test.js`.
4. Commit "<what> (X.Y.Z)", `git tag vX.Y.Z`, push main and the tag, `gh release create vX.Y.Z --title "X.Y.Z" --notes-file <changelog section>` (no assets).
5. PyPI: in `packages/python-proxy`: `python -m build`, `python -m twine check dist/sublime_mcp-X.Y.Z*`, `python -m twine upload dist/sublime_mcp-X.Y.Z-py3-none-any.whl dist/sublime_mcp-X.Y.Z.tar.gz` (token comes from `~/.pypirc`, never print it). pip's index lags a minute or two; check `https://pypi.org/pypi/sublime-mcp/json`.
6. npmjs: Donald runs `cd C:\Users\donal\projects\sublime-mcp\packages\node-proxy` then `npm publish` in his DOS console (tab 2). I can verify beforehand with `npm pack --dry-run`; `npm view sublime-mcp version` shows the live version (registry lags about a minute).

**1.12.1 (2026-10-05):** safer console capture; GitHub release v1.12.1 and PyPI 1.12.1 done by me (tests: 30 python + 3 node passed; tool lists regenerated, count still 404); npm 1.12.1 left for Donald (live npm was 1.12.0). Release steps worked as listed below. **State on 2026-10-05 (checked with `gh release list`):** GitHub's latest release is 1.12.0 (2026-10-02), after 1.11.2 (2026-09-30), 1.11.0, 1.10.0, 1.9.0 and 1.8.9 (all 2026-09-26). **State as of 2026-10-02:** 1.11.2 was released on GitHub only; npm and PyPI jumped from 1.11.1 to 1.12.0 (2026-10-02). The 1.12.0 content is jcode's resource claims ([[project_sublime_mcp_explicit_targeting_deferred]] mentions the same +177 lines). Related: [[feedback_dont_hand_technical_decisions_to_donald]].
