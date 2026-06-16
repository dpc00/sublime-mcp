"""Integration tests for register/unregister/run_st_command public API.

Requires Sublime Text running with sublime_mcp.py loaded.
Run: pytest tests/test_package_mcp.py -v
"""

import json
import httpx
import pytest

BASE = "http://127.0.0.1:9500"
TIMEOUT = 10.0

# ST loads the plugin as "User.sublime_mcp" in its module system.
# We reference it via sys.modules in eval_py calls.
_MODULE_REF = "sys.modules['User.sublime_mcp']"


def post(endpoint, **body):
    return httpx.post(f"{BASE}{endpoint}", json=body, timeout=TIMEOUT)


def ok(r):
    assert r.status_code == 200, f"{r.url} → {r.status_code}: {r.text}"
    return r.json()


def eval_py(code):
    """Run code in ST's eval_python and return parsed output."""
    r = ok(post("/eval_python", code=code))
    assert r.get("ok"), f"eval_python failed: {r.get('error')}"
    return r["output"].strip()


@pytest.fixture(scope="session", autouse=True)
def require_server():
    try:
        httpx.get(f"{BASE}/open_files", timeout=5.0)
    except (httpx.ConnectError, httpx.ReadTimeout):
        pytest.skip("ST not running")


# ── register / unregister ────────────────────────────────────────────────────


def test_register_adds_tool():
    eval_py(
        f"import sys\n"
        f"sm = {_MODULE_REF}\n"
        f"sm.register_mcp_tools([('_test_reg', 'desc', {{}}, lambda b: {{'ok': True}})])\n"
    )
    names = json.loads(eval_py(
        f"import sys, json\n"
        f"sm = {_MODULE_REF}\n"
        f"print(json.dumps([t[0] for t in sm._MCP_TOOLS]))"
    ))
    assert "_test_reg" in names


def test_unregister_removes_tool():
    eval_py(
        f"import sys\n"
        f"sm = {_MODULE_REF}\n"
        f"sm.register_mcp_tools([('_test_unreg', 'desc', {{}}, lambda b: {{'ok': True}})])\n"
        f"sm.unregister_mcp_tools([('_test_unreg', 'desc', {{}}, lambda b: {{'ok': True}})])\n"
    )
    names = json.loads(eval_py(
        f"import sys, json\n"
        f"sm = {_MODULE_REF}\n"
        f"print(json.dumps([t[0] for t in sm._MCP_TOOLS]))"
    ))
    assert "_test_unreg" not in names


def test_register_builtin_collision_keeps_builtin():
    eval_py(
        f"import sys\n"
        f"sm = {_MODULE_REF}\n"
        f"sm.register_mcp_tools([('get_active_file', 'override', {{}}, lambda b: {{'hijacked': True}})])\n"
    )
    desc = json.loads(eval_py(
        f"import sys, json\n"
        f"sm = {_MODULE_REF}\n"
        f"entry = next(t for t in sm._MCP_TOOLS if t[0] == 'get_active_file')\n"
        f"print(json.dumps(entry[1]))"
    ))
    assert "override" not in desc


def test_run_st_command_returns_ok():
    result = json.loads(eval_py(
        f"import sys, json\n"
        f"sm = {_MODULE_REF}\n"
        f"r = sm.run_st_command('toggle_side_bar', scope='window')\n"
        f"sm.run_st_command('toggle_side_bar', scope='window')\n"
        f"print(json.dumps(r))"
    ))
    assert result == {"ok": True}
