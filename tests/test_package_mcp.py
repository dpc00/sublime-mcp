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


# ── get_package_mcp_info ──────────────────────────────────────────────────────


def test_get_package_mcp_info_known_package():
    """Returns expected keys for a package that is definitely installed unpacked."""
    r = ok(post("/package_mcp_info", package="sublime-mcp"))
    assert r["package"] == "sublime-mcp"
    assert "path" in r
    assert "output_file" in r
    assert isinstance(r["commands"], list)
    assert isinstance(r["settings_keys"], list)
    assert isinstance(r["python_files"], list)
    assert "extension_template" in r
    assert r["output_file"].endswith("sublime_mcp_mcp_tools.py")


def test_get_package_mcp_info_commands_have_required_keys():
    """Each command entry has command, scopes, caption, args."""
    r = ok(post("/package_mcp_info", package="sublime-mcp"))
    for cmd in r["commands"]:
        assert "command" in cmd
        assert "scopes" in cmd
        assert "caption" in cmd
        assert "args" in cmd


def test_get_package_mcp_info_python_files_exist():
    """Returned python_files paths all end with .py."""
    r = ok(post("/package_mcp_info", package="sublime-mcp"))
    for path in r["python_files"]:
        assert path.endswith(".py"), f"unexpected file: {path}"


def test_get_package_mcp_info_packed_package():
    """Works for a zipped .sublime-package (Default is bundled and always packed)."""
    r = ok(post("/package_mcp_info", package="Default"))
    assert "error" not in r, f"unexpected error: {r.get('error')}"
    assert r["package"] == "Default"
    assert r["path"].endswith(".sublime-package")
    assert isinstance(r["commands"], list) and len(r["commands"]) > 0
    assert isinstance(r["python_files"], list) and len(r["python_files"]) > 0
    for path in r["python_files"]:
        assert path.endswith(".py")


def test_get_package_mcp_info_unknown_package():
    """Unknown package returns an error key."""
    r = ok(post("/package_mcp_info", package="__nonexistent_package_xyz__"))
    assert "error" in r


def test_get_package_mcp_info_missing_package_arg():
    """Missing package argument returns an error key."""
    r = ok(post("/package_mcp_info"))
    assert "error" in r


# ── search_packages / install_package ────────────────────────────────────────


def test_search_packages_with_query():
    """Returns matching packages with required keys."""
    r = ok(post("/search_packages", query="json", limit=5))
    assert "packages" in r
    assert "total_matches" in r
    assert isinstance(r["packages"], list)
    assert len(r["packages"]) <= 5
    for pkg in r["packages"]:
        assert "name" in pkg
        assert "description" in pkg
        assert "author" in pkg
        assert "homepage" in pkg
        assert "labels" in pkg


def test_search_packages_empty_query_returns_all():
    """Empty query returns all packages (up to limit)."""
    r = ok(post("/search_packages", query="", limit=100))
    assert r["total_matches"] > 1000


def test_search_packages_no_results():
    """Query that matches nothing returns empty list."""
    r = ok(post("/search_packages", query="__zzz_no_such_package_xyz__"))
    assert r["packages"] == []
    assert r["total_matches"] == 0


def test_install_package_unknown():
    """Unknown package returns error."""
    r = ok(post("/install_package", package="__nonexistent_xyz__"))
    assert "error" in r


def test_install_package_missing_arg():
    """Missing package arg returns error."""
    r = ok(post("/install_package"))
    assert "error" in r
