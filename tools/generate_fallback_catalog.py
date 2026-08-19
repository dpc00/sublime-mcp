#!/usr/bin/env python3
"""Generate the proxy tool catalogs from the backend _MCP_TOOLS.

F10 fix. Both proxies used to carry their own hand-maintained copy of the
backend's tool list, and both had drifted from the 220 tools the backend
actually serves:

  * node-proxy discovers tools at runtime from `/mcp_tools` and only falls
    back to a static catalog when discovery fails. Its fallback had 71, so
    a discovery miss silently dropped 149 tools including `batch`.
  * python-proxy has no dynamic discovery at all, so its hand-written 72
    tools were the *entire* surface a Python-side agent ever saw. 148
    backend tools were permanently unreachable through it.

This script makes both catalogs build artifacts of the single source of
truth (`packages/st-plugin/sublime_mcp.py::_MCP_TOOLS`):

  * `packages/node-proxy/fallback-tools.json`
  * `packages/python-proxy/tool_catalog.py`

python-proxy gets a Python module rather than a data file because its
pyproject ships `py-modules` only, so a JSON data file would not be
installed alongside it.

Usage:
    python tools/generate_fallback_catalog.py           # write the catalogs
    python tools/generate_fallback_catalog.py --check   # fail if stale

`--check` is what CI/the test suite runs: exit 1 when a committed catalog
does not match what the current backend would produce.
"""

import argparse
import importlib.util
import json
import pathlib
import pprint
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "packages" / "st-plugin" / "sublime_mcp.py"
NODE_OUTPUT = ROOT / "packages" / "node-proxy" / "fallback-tools.json"
PYTHON_OUTPUT = ROOT / "packages" / "python-proxy" / "tool_catalog.py"

BANNER = (
    "GENERATED FILE - do not edit. Produced by "
    "tools/generate_fallback_catalog.py from "
    "packages/st-plugin/sublime_mcp.py::_MCP_TOOLS. "
    "Regenerate after changing the backend tool catalog."
)


class _Stub:
    """Stands in for any Sublime API object during a headless import."""

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return _Stub()

    def __call__(self, *args, **kwargs):
        return _Stub()


def _install_sublime_stubs():
    """Make `import sublime` / `import sublime_plugin` work outside ST.

    sublime_mcp.py only *uses* the Sublime API inside handlers, so import
    succeeds as long as the module objects and the plugin base classes exist.
    """
    for name in ("sublime", "sublime_plugin"):
        module = types.ModuleType(name)
        module.__getattr__ = lambda _name: _Stub()
        sys.modules[name] = module

    import sublime_plugin

    for cls in (
        "TextCommand",
        "WindowCommand",
        "ApplicationCommand",
        "EventListener",
        "ListInputHandler",
    ):
        setattr(sublime_plugin, cls, type(cls, (object,), {}))


def load_backend():
    """Import packages/st-plugin/sublime_mcp.py headlessly."""
    _install_sublime_stubs()
    # sublime_mcp.py falls back to a flat `import mcp_http_policy`.
    sys.path.insert(0, str(BACKEND.parent))
    spec = importlib.util.spec_from_file_location("sublime_mcp", BACKEND)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_catalog(backend):
    """Return the tool catalog in the same shape as GET /mcp_tools.

    Reuses the backend's own `_get_mcp_tools` so a generated catalog and the
    live discovery response cannot describe tools differently.
    """
    tools = backend._get_mcp_tools({})["tools"]
    return sorted(tools, key=lambda tool: tool["name"])


def render_node(tools):
    return json.dumps({"_comment": BANNER, "tools": tools}, indent=2) + "\n"


def render_python(tools):
    """Emit a Python module holding the same catalog.

    python-proxy builds real typed FastMCP tools from these entries at
    import time, so it needs the data importable rather than adjacent.
    """
    return (
        '"""{}"""\n\n'
        "TOOLS = {}\n".format(BANNER, pprint.pformat(tools, indent=4, width=100, sort_dicts=False))
    )


TARGETS = (
    (NODE_OUTPUT, render_node),
    (PYTHON_OUTPUT, render_python),
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if a committed catalog is stale instead of writing it",
    )
    args = parser.parse_args(argv)

    tools = build_catalog(load_backend())
    count = len(tools)

    if args.check:
        stale = []
        for path, render in TARGETS:
            if not path.exists():
                stale.append("{} is missing".format(path))
            elif path.read_text(encoding="utf-8") != render(tools):
                stale.append("{} does not match the backend catalog".format(path))
        if stale:
            print(
                "stale ({} backend tools):\n  {}\n"
                "Run: python tools/generate_fallback_catalog.py".format(
                    count, "\n  ".join(stale)
                )
            )
            return 1
        print("up to date: {} tools in {} catalogs".format(count, len(TARGETS)))
        return 0

    for path, render in TARGETS:
        path.write_text(render(tools), encoding="utf-8")
        print("wrote {} ({} tools)".format(path, count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
