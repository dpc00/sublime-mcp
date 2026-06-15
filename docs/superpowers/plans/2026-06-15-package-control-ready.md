# Package Control Ready Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make sublime-mcp properly distributable via Package Control for all platforms, with both Python (PyPI) and Node.js (npm) MCP servers available.

**Architecture:** The monorepo ships three artifacts: ST plugin via Package Control (`.py` files only), Python MCP server via PyPI (`mcp_server.py`), Node.js MCP server via npm (`index.js`). `.gitattributes` export-ignore fences keep Package Control from seeing anything but the plugin files.

**Tech Stack:** Python 3.10+, `mcp` + `httpx` (PyPI), setuptools, Node.js 18+ (existing)

---

## File Map

| File | Action | What changes |
|---|---|---|
| `sublime_mcp.py` | Modify | `_PORT` cross-platform, `_get_console_full` rewrite, `eval_python_latest` fix |
| `mcp_server.py` | Restore + extend | Recover from git, add 2 new tools |
| `pyproject.toml` | Restore + update | Recover from git, bump version to 1.2.5 |
| `.gitattributes` | Modify | Add export-ignore entries |
| `.gitignore` | Modify | Add `dist/` and `sublime_mcp.egg-info/` |
| `messages/install.txt` | Rewrite | Clear two-part setup instructions |
| `dist/` | Remove from git | `git rm -r --cached` |
| `sublime_mcp.egg-info/` | Remove from git | `git rm -r --cached` |

---

## Task 1: Fix `_PORT` — cross-platform port detection

**Files:**
- Modify: `sublime_mcp.py:72`

The plugin currently hardcodes `_PORT = 9500`. On Mac/Linux, Sublime Text should listen on `9501` to avoid conflicts with WSL. The MCP server already has this logic — the plugin must match it.

- [ ] **Step 1: Open sublime_mcp.py and locate line 72**

The current line reads:
```python
_PORT = 9500
```

- [ ] **Step 2: Replace with cross-platform detection**

Replace that single line with:
```python
_PORT = int(os.environ.get("SUBLIME_MCP_PORT", 9500 if sys.platform == "win32" else 9501))
```

`os` is already imported at line 62 and `sys` at line 64 — no new imports needed.

Also update the docstring at line 55 which says `Port: 9500`. Change it to:
```
Port: 9500 (Windows) / 9501 (Mac/Linux) — override with SUBLIME_MCP_PORT env var
```

- [ ] **Step 3: Commit**

```bash
git add sublime_mcp.py
git commit -m "Fix _PORT: cross-platform detection (9500 Windows, 9501 Mac/Linux)"
```

---

## Task 2: Fix `_get_console_full` — replace Windows-only clipboard hack

**Files:**
- Modify: `sublime_mcp.py:521-620` (approximately — the function ends before `_get_console_log` area)

The current implementation uses `ctypes.windll` (Windows API only). Replace it with a simple buffer read — the `_console_buf` already captures everything.

- [ ] **Step 1: Find the full extent of `_get_console_full`**

Run:
```bash
grep -n "^def _" sublime_mcp.py | grep -A1 "console_full"
```

This shows the line numbers of `_get_console_full` and the next function after it, so you know where to cut.

- [ ] **Step 2: Replace the entire `_get_console_full` function**

Delete everything from `def _get_console_full(params):` through the end of that function (before the next `def`), and replace with:

```python
def _get_console_full(params):
    """Return the entire captured ST console buffer (no tail limit)."""
    _install_console_capture()
    return {"entries": list(_console_buf), "total": len(_console_buf)}
```

- [ ] **Step 3: Verify no `ctypes.windll` or `ctypes.wintypes` references remain in the function**

```bash
grep -n "windll\|wintypes\|user32\|kernel32\|EnumWindows" sublime_mcp.py
```

Expected: no output (these were only in `_get_console_full`).

- [ ] **Step 4: Commit**

```bash
git add sublime_mcp.py
git commit -m "Fix get_console_full: replace Windows clipboard hack with portable buffer read"
```

---

## Task 3: Fix `eval_python_latest` — use `sys.executable`

**Files:**
- Modify: `sublime_mcp.py:1475`

The current call uses the string `"python"` which may not be on PATH on Mac/Linux. Use `sys.executable` instead.

- [ ] **Step 1: Locate the subprocess.run call**

```bash
grep -n 'subprocess.run.*python' sublime_mcp.py
```

It will show a line like:
```python
r = subprocess.run(["python", fname], capture_output=True, text=True, timeout=30)
```

- [ ] **Step 2: Replace `"python"` with `sys.executable`**

Change that line to:
```python
r = subprocess.run([sys.executable, fname], capture_output=True, text=True, timeout=30)
```

`sys` is already imported at line 64.

- [ ] **Step 3: Commit**

```bash
git add sublime_mcp.py
git commit -m "Fix eval_python_latest: use sys.executable for cross-platform compatibility"
```

---

## Task 4: Restore `mcp_server.py` and add two missing tools

**Files:**
- Restore: `mcp_server.py` (from git history)

The Python MCP server was deleted on June 11. It needs to be recovered from git and extended with `get_console_full` and `eval_python_latest`.

- [ ] **Step 1: Restore from git history**

```bash
git show d356c6f^:mcp_server.py > mcp_server.py
```

Verify it restored correctly:
```bash
wc -l mcp_server.py
```
Expected: `554 mcp_server.py`

- [ ] **Step 2: Verify the file ends with `main()`**

```bash
tail -10 mcp_server.py
```

Expected output (last lines):
```python
def main():
    mcp.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Add `get_console_full` tool**

Insert the following before the `def main():` line (i.e., after the last `@mcp.tool()` block):

```python
@mcp.tool()
def get_console_full() -> dict:
    """Return the entire captured ST console buffer with no tail limit.
    Use this when get_console_log (tail=N) doesn't show enough history."""
    return _get("/console_full")


```

- [ ] **Step 4: Add `eval_python_latest` tool**

Insert the following immediately after the `get_console_full` block, still before `def main()`:

```python
@mcp.tool()
def eval_python_latest(code: str) -> dict:
    """Run code using the system Python interpreter (outside ST's embedded sandbox).
    Useful when you need access to packages not available in ST's Python.
    Returns stdout, stderr, and returncode."""
    return _post("/eval_python_latest", code=code)


```

- [ ] **Step 5: Verify tool count**

```bash
grep -c "@mcp.tool" mcp_server.py
```

Expected: the old count + 2. The old server had these tools (count them):
```bash
git show d356c6f^:mcp_server.py | grep -c "@mcp.tool"
```
The new file should return that number + 2.

- [ ] **Step 6: Smoke-test the file parses correctly**

```bash
python -c "import ast; ast.parse(open('mcp_server.py').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add mcp_server.py
git commit -m "Restore mcp_server.py from git history, add get_console_full and eval_python_latest tools"
```

---

## Task 5: Restore `pyproject.toml` and update version

**Files:**
- Restore: `pyproject.toml`

The pyproject.toml was deleted along with mcp_server.py. Recover it and bump the version to match current (1.2.5).

- [ ] **Step 1: Restore from git history**

```bash
git show d356c6f^:pyproject.toml > pyproject.toml
```

- [ ] **Step 2: Update version to 1.2.5**

The restored file will have `version = "1.2.4"`. Change it to:
```toml
version = "1.2.5"
```

- [ ] **Step 3: Verify the entry point is correct**

```bash
grep "sublime-mcp\|py-modules" pyproject.toml
```

Expected output:
```
sublime-mcp = "mcp_server:main"
...
py-modules = ["mcp_server"]
```

- [ ] **Step 4: Verify dependencies**

```bash
grep "dependencies" pyproject.toml
```

Expected:
```
dependencies = ["mcp", "httpx"]
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "Restore pyproject.toml, bump version to 1.2.5"
```

---

## Task 6: Update `.gitattributes` — export-ignore new entries

**Files:**
- Modify: `.gitattributes`

Package Control uses `export-ignore` to skip files when packaging. We need to add the JS server files, Python server files, and docs so Package Control only sees the ST plugin `.py` files.

- [ ] **Step 1: Read the current `.gitattributes`**

```bash
cat .gitattributes
```

Current content:
```
tests/                  export-ignore
dist/                   export-ignore
sublime_mcp.egg-info/   export-ignore
pyproject.toml          export-ignore
requirements.txt        export-ignore
server.json             export-ignore
sonnet.txt              export-ignore
claude-guide.md         export-ignore
CLAUDE.md               export-ignore
.gitignore              export-ignore
```

- [ ] **Step 2: Append new export-ignore entries**

Add these lines to the end of `.gitattributes`:

```
index.js                export-ignore
package.json            export-ignore
node_modules/           export-ignore
mcp_server.py           export-ignore
docs/                   export-ignore
__pycache__/            export-ignore
.ruff_cache/            export-ignore
```

- [ ] **Step 3: Commit**

```bash
git add .gitattributes
git commit -m "Update .gitattributes: export-ignore JS server, Python server, docs for Package Control"
```

---

## Task 7: Remove built artifacts from git tracking

**Files:**
- Remove from tracking: `dist/`, `sublime_mcp.egg-info/`
- Modify: `.gitignore`

These generated files don't belong in git. They're already in `.gitattributes` `export-ignore` but are still tracked.

- [ ] **Step 1: Remove from git tracking (keep files on disk)**

```bash
git rm -r --cached dist/
git rm -r --cached sublime_mcp.egg-info/
```

- [ ] **Step 2: Add to `.gitignore`**

The `.gitignore` already exists. Add these two lines to it:
```
dist/
sublime_mcp.egg-info/
```

- [ ] **Step 3: Verify they no longer appear as tracked**

```bash
git status
```

Expected: `dist/` and `sublime_mcp.egg-info/` appear as deleted (staged), `.gitignore` appears as modified.

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "Remove dist/ and sublime_mcp.egg-info/ from git tracking"
```

---

## Task 8: Rewrite `messages/install.txt`

**Files:**
- Modify: `messages/install.txt`

The current install.txt says `pip install sublime-mcp` with no explanation of what that installs, and no mention of the Node.js alternative. Rewrite for clarity.

- [ ] **Step 1: Replace the entire content of `messages/install.txt`**

```
sublime-mcp
===========

Sublime Text MCP server — lets Claude Code (or any MCP client) read and
control a running ST instance via a local HTTP bridge.

The ST plugin is now running. Complete setup in two steps:


STEP 1 — Install the MCP server (run once in your terminal)
------------------------------------------------------------

  Python (pip):   pip install sublime-mcp
  Node.js (npx):  npx sublime-mcp        (no install needed)

Choose either. Both provide the same tools.


STEP 2 — Register with Claude Code
------------------------------------

Add to ~/.claude/settings.json under "mcpServers":

  Python:
    "sublime-mcp": { "command": "sublime-mcp" }

  Node.js:
    "sublime-mcp": { "command": "npx", "args": ["sublime-mcp"] }

Restart Claude Code. Tools appear with the mcp__sublime-mcp__ prefix.


Plugin port
-----------

  Windows:  127.0.0.1:9500
  Mac/Linux: 127.0.0.1:9501

Override with the SUBLIME_MCP_PORT environment variable.
Check View > Show Console for:  sublime-mcp: listening on 127.0.0.1:NNNN


Full documentation: https://github.com/dpc00/sublime-mcp
```

- [ ] **Step 2: Commit**

```bash
git add messages/install.txt
git commit -m "Rewrite install.txt: clear two-part setup, Python + Node.js options, cross-platform ports"
```

---

## Task 9: Reply to PR #9447 reviewer

**Files:** none (GitHub PR comment)

Respond to reviewer `kaste` on `sublimehq/package_control_channel` PR #9447 summarising what was fixed.

- [ ] **Step 1: Post the reply comment on GitHub**

Go to: `https://github.com/sublimehq/package_control_channel/pull/9447`

Post this comment:

> Thanks for the detailed review — here's what's been addressed:
>
> **Platforms:** The plugin now detects the OS at startup and listens on `127.0.0.1:9500` (Windows) or `127.0.0.1:9501` (Mac/Linux), overridable via `SUBLIME_MCP_PORT`. Works on all three platforms.
>
> **Stray JS files / Node.js dependency:** The `.gitattributes` now marks `index.js`, `package.json`, and `node_modules/` as `export-ignore`, so Package Control never installs them. The Node.js server is an optional alternative for users who prefer npm.
>
> **`pip install sublime-mcp` loop-link:** This was confusing because the PyPI package (`mcp_server.py`, the MCP server process) and the ST plugin are two separate things from the same repo. The install.txt has been rewritten to make this clear: Package Control installs the plugin; users then separately install the MCP server via `pip install sublime-mcp` or `npx sublime-mcp`.
>
> **dist/ and egg-info:** Removed from git tracking entirely.
>
> **Python requirements in ST:** The `mcp` and `httpx` packages are only required by `mcp_server.py` (the external MCP server process, not the ST plugin). They are not needed inside ST. The `requirements.txt` and `mcp_server.py` are both `export-ignore`d from Package Control installs.
>
> The plugin itself (`sublime_mcp.py`, `sublime_mcp_browse.py`) has no external dependencies — it uses only ST's embedded Python and stdlib.
>
> Happy to make any further changes you need.

---

## Final verification

- [ ] Confirm Package Control export contains only plugin files:

```bash
git archive HEAD --format=tar | tar -t | grep -v "^\.git"
```

Expected: only `sublime_mcp.py`, `sublime_mcp_browse.py`, `messages/`, `README.md`, `LICENSE`, `.gitattributes` visible — no `index.js`, `mcp_server.py`, `dist/`, `node_modules/`.

- [ ] Confirm Python server parses:

```bash
python -c "import ast; ast.parse(open('mcp_server.py').read()); print('OK')"
```

- [ ] Confirm pyproject.toml entry point:

```bash
grep "sublime-mcp = " pyproject.toml
```

Expected: `sublime-mcp = "mcp_server:main"`
