# Package MCP Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `register_mcp_tools` / `unregister_mcp_tools` / `run_st_command` public API and a `get_package_mcp_info` MCP tool to `sublime_mcp.py`, enabling AI agents to generate and install MCP extensions for any Package Control package.

**Architecture:** `_MCP_TOOLS` (already a list) becomes a live registry protected by `_mcp_tools_lock`. External ST plugin files call `register_mcp_tools(TOOLS)` in `plugin_loaded` and `unregister_mcp_tools(TOOLS)` in `plugin_unloaded`. The new `get_package_mcp_info` tool returns commands, settings keys, Python file listing, the output path, and a template — everything an AI needs to write the extension file.

**Tech Stack:** Python 3.8, Sublime Text plugin API (`sublime`, `sublime_plugin`), `threading.Lock`, `os.walk`, existing `httpx`-based integration test harness (port 9500).

---

## File Map

| File | Change |
|------|--------|
| `sublime_mcp.py` | Add lock, 3 public functions, `_EXTENSION_TEMPLATE`, `_get_package_mcp_info` handler, wire into `_POST` + `_MCP_TOOLS` + `_mcp_dispatch` |
| `tests/test_package_mcp.py` | New — integration tests against port 9500 |

---

## Task 1: Thread-safe tool registry + public API

**Files:**
- Modify: `sublime_mcp.py` — add lock after `_MCP_TOOLS`, wrap dispatch, add 3 public functions

### Step 1.1 — Write the failing tests

Create `tests/test_package_mcp.py`:

```python
"""Integration tests for register/unregister/run_st_command public API.

Requires Sublime Text running with sublime_mcp.py loaded.
Run: pytest tests/test_package_mcp.py -v
"""

import httpx
import pytest

BASE = "http://127.0.0.1:9500"
TIMEOUT = 10.0


def post(endpoint, **body):
    return httpx.post(f"{BASE}{endpoint}", json=body, timeout=TIMEOUT)


def ok(r):
    assert r.status_code == 200, f"{r.url} → {r.status_code}: {r.text}"
    return r.json()


@pytest.fixture(scope="session", autouse=True)
def require_server():
    try:
        httpx.get(f"{BASE}/open_files", timeout=5.0)
    except (httpx.ConnectError, httpx.ReadTimeout):
        pytest.skip("ST not running")


# ── register / unregister ────────────────────────────────────────────────────


def test_register_adds_tool():
    """Registering a tool makes it appear in the MCP tool list."""
    setup = (
        "import sublime_mcp\n"
        "sublime_mcp.register_mcp_tools([('_test_reg', 'desc', {}, lambda b: {'ok': True})])\n"
    )
    ok(post("/eval_python", code=setup))

    names = ok(post("/eval_python", code=(
        "import sublime_mcp\n"
        "[t[0] for t in sublime_mcp._MCP_TOOLS]"
    )))
    assert "_test_reg" in names["result"]


def test_unregister_removes_tool():
    """Unregistering a tool removes it from the MCP tool list."""
    tool = [("_test_unreg", "desc", {}, lambda b: {"ok": True})]
    setup = (
        "import sublime_mcp\n"
        "sublime_mcp.register_mcp_tools([('_test_unreg', 'desc', {}, lambda b: {'ok': True})])\n"
        "sublime_mcp.unregister_mcp_tools([('_test_unreg', 'desc', {}, lambda b: {'ok': True})])\n"
    )
    ok(post("/eval_python", code=setup))

    names = ok(post("/eval_python", code=(
        "import sublime_mcp\n"
        "[t[0] for t in sublime_mcp._MCP_TOOLS]"
    )))
    assert "_test_unreg" not in names["result"]


def test_register_builtin_collision_keeps_builtin():
    """Registering a tool whose name matches a built-in keeps the built-in."""
    setup = (
        "import sublime_mcp\n"
        "sublime_mcp.register_mcp_tools([('get_active_file', 'override', {}, lambda b: {'hijacked': True})])\n"
    )
    ok(post("/eval_python", code=setup))

    entry = ok(post("/eval_python", code=(
        "import sublime_mcp\n"
        "next(t for t in sublime_mcp._MCP_TOOLS if t[0] == 'get_active_file')"
    )))
    # description should still be the original, not 'override'
    assert "override" not in entry["result"][1]


def test_run_st_command_returns_ok():
    """run_st_command executes a valid command and returns ok."""
    result = ok(post("/eval_python", code=(
        "import sublime_mcp\n"
        "sublime_mcp.run_st_command('toggle_side_bar', scope='window')"
    )))
    # toggle twice so we leave ST in original state
    ok(post("/eval_python", code=(
        "import sublime_mcp\n"
        "sublime_mcp.run_st_command('toggle_side_bar', scope='window')"
    )))
    assert result["result"] == {"ok": True}
```

- [ ] **Step 1.1:** Create `tests/test_package_mcp.py` with the content above.

### Step 1.2 — Run to confirm tests fail

```
cd C:\Users\donal\projects\sublime-mcp
pytest tests/test_package_mcp.py -v -k "register or unregister or run_st_command"
```

Expected: `AttributeError: module 'sublime_mcp' has no attribute 'register_mcp_tools'`

- [ ] **Step 1.2:** Run tests, confirm failure.

### Step 1.3 — Add lock + public API to `sublime_mcp.py`

Find line 2232 (the closing `]` of `_MCP_TOOLS`). Insert immediately after it:

```python
_mcp_tools_lock = threading.Lock()
_mcp_tools_builtin_names = frozenset(t[0] for t in _MCP_TOOLS)


def register_mcp_tools(tools):
    """Register additional MCP tools from an extension plugin.

    Call from plugin_loaded(). tools is a list of
    (name, description, input_schema, handler) tuples, the same format
    as _MCP_TOOLS.  Built-in tool names are protected: a collision logs
    a warning and keeps the built-in.
    """
    with _mcp_tools_lock:
        existing = {t[0] for t in _MCP_TOOLS}
        for entry in tools:
            name = entry[0]
            if name in _mcp_tools_builtin_names:
                print(f"sublime-mcp: register_mcp_tools: '{name}' is a built-in tool — skipped")
                continue
            if name in existing:
                print(f"sublime-mcp: register_mcp_tools: '{name}' already registered — skipped")
                continue
            _MCP_TOOLS.append(entry)
            existing.add(name)


def unregister_mcp_tools(tools):
    """Remove tools previously registered with register_mcp_tools.

    Call from plugin_unloaded(). Built-in tools are never removed.
    """
    names = {entry[0] for entry in tools} - _mcp_tools_builtin_names
    with _mcp_tools_lock:
        for i in range(len(_MCP_TOOLS) - 1, -1, -1):
            if _MCP_TOOLS[i][0] in names:
                _MCP_TOOLS.pop(i)


def run_st_command(command, args=None, scope="window"):
    """Run a Sublime Text command via the internal bridge.

    Convenience function for use in extension tool handlers.
    scope: 'text', 'window', or 'application'.
    Returns {"ok": True} on success or {"error": "..."} on failure.
    """
    return _run_command({"command": command, "args": args or {}, "scope": scope})
```

Also wrap the two `_MCP_TOOLS` accesses in `_mcp_dispatch` (around line 2338–2353) with the lock:

```python
        elif method == "tools/list":
            with _mcp_tools_lock:
                snapshot = list(_MCP_TOOLS)
            tools = []
            for name, desc, schema, _ in snapshot:
                input_schema = dict(schema) if schema else {}
                if "type" not in input_schema:
                    input_schema["type"] = "object"
                if "properties" not in input_schema:
                    input_schema["properties"] = {}
                tools.append({"name": name, "description": desc, "inputSchema": input_schema})
            result = {"tools": tools}
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}
            with _mcp_tools_lock:
                entry = next((t for t in _MCP_TOOLS if t[0] == tool_name), None)
            if entry is None:
                raise ValueError("Unknown tool: " + str(tool_name))
            data = entry[3](tool_args)
            result = {"content": [{"type": "text", "text": json.dumps(data)}]}
```

- [ ] **Step 1.3:** Apply the edits above to `sublime_mcp.py`.

### Step 1.4 — Reload plugin and run tests

In ST console: `import importlib, sublime_mcp; importlib.reload(sublime_mcp)`

Or use the MCP Commander: Server Status command to restart.

```
pytest tests/test_package_mcp.py -v -k "register or unregister or run_st_command"
```

Expected: all 4 tests PASS.

- [ ] **Step 1.4:** Reload plugin, run tests, confirm PASS.

### Step 1.5 — Commit

```bash
git add sublime_mcp.py tests/test_package_mcp.py
git commit -m "feat: add register_mcp_tools, unregister_mcp_tools, run_st_command public API"
```

- [ ] **Step 1.5:** Commit.

---

## Task 2: `get_package_mcp_info` tool

**Files:**
- Modify: `sublime_mcp.py` — add `_EXTENSION_TEMPLATE`, `_get_package_mcp_info`, wire into `_POST` and `_MCP_TOOLS`

### Step 2.1 — Write the failing tests

Add to `tests/test_package_mcp.py`:

```python
# ── get_package_mcp_info ──────────────────────────────────────────────────────


def test_get_package_mcp_info_known_package():
    """Returns expected keys for a package that is definitely installed."""
    r = ok(post("/package_mcp_info", package="Default"))
    assert r["package"] == "Default"
    assert "path" in r
    assert "output_file" in r
    assert isinstance(r["commands"], list)
    assert isinstance(r["settings_keys"], list)
    assert isinstance(r["python_files"], list)
    assert "extension_template" in r
    assert r["output_file"].endswith("default_mcp_tools.py")


def test_get_package_mcp_info_commands_have_required_keys():
    """Each command entry has command, scopes, caption, args."""
    r = ok(post("/package_mcp_info", package="Default"))
    for cmd in r["commands"]:
        assert "command" in cmd
        assert "scopes" in cmd
        assert "caption" in cmd
        assert "args" in cmd


def test_get_package_mcp_info_python_files_exist():
    """Returned python_files paths all end with .py."""
    r = ok(post("/package_mcp_info", package="Default"))
    for path in r["python_files"]:
        assert path.endswith(".py"), f"unexpected file: {path}"


def test_get_package_mcp_info_unknown_package():
    """Unknown package returns an error key."""
    r = ok(post("/package_mcp_info", package="__nonexistent_package_xyz__"))
    assert "error" in r


def test_get_package_mcp_info_missing_package_arg():
    """Missing package argument returns an error key."""
    r = ok(post("/package_mcp_info"))
    assert "error" in r
```

- [ ] **Step 2.1:** Add the 5 tests above to `tests/test_package_mcp.py`.

### Step 2.2 — Run to confirm they fail

```
pytest tests/test_package_mcp.py -v -k "package_mcp_info"
```

Expected: `404` errors (endpoint not registered yet).

- [ ] **Step 2.2:** Run tests, confirm failure.

### Step 2.3 — Add `_EXTENSION_TEMPLATE` constant

Add this constant near the top of the MCP SSE section (around line 1860, after `_mcp_sessions`):

```python
_EXTENSION_TEMPLATE = """\
Place this file in Packages/<YourPackage>/<yourpackage>_mcp_tools.py.
It is a standard Sublime Text plugin — ST loads and unloads it automatically.

from sublime_mcp import register_mcp_tools, unregister_mcp_tools, run_st_command

# Each entry: (name, description, input_schema, handler)
# handler(body: dict) -> dict  (must be JSON-serialisable)
# run_st_command(command, args=None, scope="window") runs any ST command.
# scope values: "text" (TextCommand), "window" (WindowCommand), "application" (ApplicationCommand)

TOOLS = [
    ("example_command",
     "One-line description of what this does.",
     {},
     lambda body: run_st_command("example_command", scope="window")),

    ("example_with_args",
     "Description of a command that takes arguments.",
     {"type": "object", "properties": {"arg1": {"type": "string"}}, "required": ["arg1"]},
     lambda body: run_st_command("example_command", args={"arg1": body["arg1"]}, scope="window")),
]

def plugin_loaded():
    register_mcp_tools(TOOLS)

def plugin_unloaded():
    unregister_mcp_tools(TOOLS)
"""
```

- [ ] **Step 2.3:** Add `_EXTENSION_TEMPLATE` to `sublime_mcp.py`.

### Step 2.4 — Add `_get_package_mcp_info` handler

Add this function before the `_MCP_TOOLS` list (around line 1904):

```python
def _get_package_mcp_info(body):
    package = body.get("package", "").strip()
    if not package:
        return {"error": "package required"}

    def fn():
        pkg_path = os.path.join(sublime.packages_path(), package)
        if not os.path.isdir(pkg_path):
            return {"error": f"Package '{package}' not found in Packages/"}

        # ── commands from loaded command classes ──────────────────────────
        commands = {}
        for scope_name, classes in (
            ("application", getattr(sublime_plugin, "application_command_classes", [])),
            ("window", getattr(sublime_plugin, "window_command_classes", [])),
            ("text", getattr(sublime_plugin, "text_command_classes", [])),
        ):
            for cls in classes:
                module = getattr(cls, "__module__", "")
                pkg = module.split(".", 1)[0] if module else ""
                if pkg.lower() != package.lower():
                    continue
                cmd = _command_name_from_class(cls)
                entry = commands.setdefault(cmd, {"command": cmd, "scopes": [], "caption": "", "args": {}})
                if scope_name not in entry["scopes"]:
                    entry["scopes"].append(scope_name)

        # ── enrich with .sublime-commands captions/args ───────────────────
        for resource in sorted(sublime.find_resources("*.sublime-commands")):
            if _package_name_from_resource(resource) != package:
                continue
            try:
                data = sublime.decode_value(sublime.load_resource(resource))
            except Exception:
                continue
            if not isinstance(data, list):
                continue
            for item in data:
                if not isinstance(item, dict):
                    continue
                cmd = item.get("command", "")
                if not cmd:
                    continue
                entry = commands.setdefault(cmd, {"command": cmd, "scopes": [], "caption": "", "args": {}})
                if item.get("caption"):
                    entry["caption"] = item["caption"]
                if item.get("args"):
                    entry["args"] = item["args"]

        # ── settings keys from .sublime-settings files ────────────────────
        settings_keys = []
        seen_keys = set()
        for resource in sorted(sublime.find_resources("*.sublime-settings")):
            if _package_name_from_resource(resource) != package:
                continue
            try:
                data = sublime.decode_value(sublime.load_resource(resource))
            except Exception:
                continue
            if isinstance(data, dict):
                for k in data:
                    if k not in seen_keys:
                        settings_keys.append(k)
                        seen_keys.add(k)

        # ── .py file listing ──────────────────────────────────────────────
        python_files = []
        for root, dirs, files in os.walk(pkg_path):
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d != "__pycache__")
            for fname in sorted(files):
                if fname.endswith(".py"):
                    python_files.append(os.path.join(root, fname))

        # ── output file path ──────────────────────────────────────────────
        safe_name = package.lower().replace(" ", "_").replace("-", "_")
        output_file = os.path.join(pkg_path, f"{safe_name}_mcp_tools.py")

        return {
            "package": package,
            "path": pkg_path,
            "output_file": output_file,
            "commands": list(commands.values()),
            "settings_keys": settings_keys,
            "python_files": python_files,
            "extension_template": _EXTENSION_TEMPLATE,
        }

    return _on_main(fn)
```

- [ ] **Step 2.4:** Add `_get_package_mcp_info` to `sublime_mcp.py`.

### Step 2.5 — Wire into `_POST` and `_MCP_TOOLS`

In `_POST` dict (around line 1801), add:

```python
    "/package_mcp_info": _get_package_mcp_info,
```

In `_MCP_TOOLS` list (before the closing `]`), add:

```python
    ("get_package_mcp_info",
     "Return everything needed to write an MCP extension for an installed Package Control package.\n"
     "Returns: path, output_file, commands (with captions and args), settings_keys, python_files, extension_template.\n"
     "Write the extension to output_file following extension_template; ST loads it automatically.",
     {"type": "object", "properties": {"package": {"type": "string"}}, "required": ["package"]},
     _get_package_mcp_info),
```

- [ ] **Step 2.5:** Add the `_POST` entry and `_MCP_TOOLS` entry.

### Step 2.6 — Reload plugin and run tests

In ST console: `import importlib, sublime_mcp; importlib.reload(sublime_mcp)`

```
pytest tests/test_package_mcp.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 2.6:** Reload plugin, run all tests, confirm PASS.

### Step 2.7 — Run the full test suite

```
pytest tests/ -v
```

Confirm no regressions in `test_http_api.py`.

- [ ] **Step 2.7:** Full suite passes.

### Step 2.8 — Commit

```bash
git add sublime_mcp.py tests/test_package_mcp.py
git commit -m "feat: add get_package_mcp_info MCP tool for Package Control package introspection"
```

- [ ] **Step 2.8:** Commit.

---

## Self-Review Notes

- `_EXTENSION_TEMPLATE` is placed before `_get_package_mcp_info` (it references it) — order matters.
- `_package_name_from_resource` does an exact string match (`!= package`), not case-insensitive. This is correct — package names in resource paths match their directory name exactly.
- `_mcp_tools_builtin_names` is a frozenset captured at module load, so it is stable even after extensions add tools.
- The lock is a `threading.Lock`, not `RLock` — `register_mcp_tools` and `unregister_mcp_tools` are called from ST's main thread, never re-entrantly from inside the lock.
- Plugin reload (`importlib.reload`) resets `_MCP_TOOLS` to the built-in list and rebuilds `_mcp_tools_builtin_names`. Extension plugins must call `register_mcp_tools` again after a plugin reload — which ST handles naturally via `plugin_loaded`.
