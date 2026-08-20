"""Release guard: python-proxy's declared dependencies must be installable
into a working server.

Found 2026-08-19 by installing the published 1.4.1 wheel into a clean venv
and launching it: `pip install sublime-mcp` resolved `mcp` to 2.0.0, which
removed `mcp.server.fastmcp`, and the server died at import with
`ModuleNotFoundError: No module named 'mcp.server.fastmcp'`. The shipped
code was correct; the unpinned dependency was not. Nothing in the suite
caught it because every other test runs against the developer's already
pinned environment rather than a fresh resolve.

These tests are static so they always run. The full proof is the clean-venv
install documented in tests/proof/STATUS.md.
"""
import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
PYPROJECT = ROOT / "packages" / "python-proxy" / "pyproject.toml"
REQUIREMENTS = ROOT / "requirements.txt"
PROXY = ROOT / "packages" / "python-proxy" / "mcp_server.py"


def _declared_dependencies():
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r"^dependencies\s*=\s*\[(.*?)\]", text, re.S | re.M)
    assert match, "dependencies declaration missing"
    return re.findall(r'"([^"]+)"', match.group(1))


def test_proxy_still_depends_on_the_fastmcp_api():
    """If this import ever changes, the pin below must be revisited."""
    text = PROXY.read_text(encoding="utf-8")
    assert "from mcp.server.fastmcp import FastMCP" in text, (
        "mcp_server no longer uses mcp.server.fastmcp; re-evaluate the mcp<2 pin"
    )


def test_mcp_dependency_excludes_the_2x_line():
    """mcp 2.0.0 removed mcp.server.fastmcp. An unpinned install is broken."""
    deps = _declared_dependencies()
    mcp_specs = [d for d in deps if re.match(r"^mcp\b", d)]
    assert mcp_specs, "mcp dependency missing: {}".format(deps)
    spec = mcp_specs[0]
    assert spec != "mcp", (
        "mcp is unpinned; `pip install .` resolves to 2.x and the server dies "
        "at import with ModuleNotFoundError: mcp.server.fastmcp"
    )
    assert "<2" in spec, (
        "mcp must be capped below 2.0 while this server uses mcp.server.fastmcp; "
        "got {!r}".format(spec)
    )


def test_requirements_txt_agrees_with_pyproject():
    """A source checkout installs from requirements.txt, not the wheel."""
    deps = {re.split(r"[<>=!]", d)[0]: d for d in _declared_dependencies()}
    lines = [
        line.strip()
        for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    listed = {re.split(r"[<>=!]", line)[0]: line for line in lines}
    assert listed.get("mcp") == deps.get("mcp"), (
        "requirements.txt and pyproject disagree on the mcp pin: {!r} vs {!r}".format(
            listed.get("mcp"), deps.get("mcp")
        )
    )


# ── version consistency ───────────────────────────────────────────────────────
# Same class of release bug: three surfaces each carried their own version
# literal and had drifted apart (package.json 1.4.1, index.js 1.4.0, plugin
# serverInfo 1.3.1), so a client asking any given server what it was got a
# different answer depending on which one it asked.

PACKAGE_JSON = ROOT / "packages" / "node-proxy" / "package.json"
PLUGIN = ROOT / "packages" / "st-plugin" / "sublime_mcp.py"
NODE_INDEX = ROOT / "packages" / "node-proxy" / "index.js"


def _pyproject_version():
    text = PYPROJECT.read_text(encoding="utf-8")
    return re.search(r'^version\s*=\s*"([^"]+)"', text, re.M).group(1)


def test_all_published_surfaces_declare_the_same_version():
    import json

    versions = {
        "python-proxy/pyproject.toml": _pyproject_version(),
        "node-proxy/package.json": json.loads(
            PACKAGE_JSON.read_text(encoding="utf-8-sig")
        )["version"],
        "st-plugin/sublime_mcp.py": re.search(
            r'^__version__\s*=\s*"([^"]+)"', PLUGIN.read_text(encoding="utf-8"), re.M
        ).group(1),
    }
    assert len(set(versions.values())) == 1, (
        "version drift across published surfaces: {}".format(versions)
    )


def test_node_proxy_does_not_hardcode_a_second_version_literal():
    """index.js must read package.json rather than repeat the number."""
    text = NODE_INDEX.read_text(encoding="utf-8")
    match = re.search(r"new McpServer\(\{[^}]*\}\)", text)
    assert match, "McpServer construction not found"
    assert "VERSION" in match.group(0), (
        "index.js hardcodes a version again; it must derive it from package.json"
    )


def test_plugin_serverinfo_uses_the_version_constant():
    """serverInfo previously reported a stale hardcoded 1.3.1."""
    text = PLUGIN.read_text(encoding="utf-8")
    match = re.search(r'"serverInfo":\s*\{[^}]*\}', text)
    assert match, "serverInfo not found"
    assert "__version__" in match.group(0), (
        "serverInfo hardcodes a version again; it must use __version__"
    )
