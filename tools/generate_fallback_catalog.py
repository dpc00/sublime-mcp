#!/usr/bin/env python3
"""Generate the node-proxy fallback tool catalog from the backend _MCP_TOOLS.

F10 fix. The node-proxy discovers tools at runtime from the backend's
`/mcp_tools` endpoint. When that discovery fails (backend not up yet,
retries exhausted) it falls back to a static catalog. That catalog used to
be hand-maintained and had drifted to 71 of the backend's 220 tools, so a
discovery miss silently dropped 149 tools including `batch`.

This script makes the fallback a build artifact of the single source of
truth (`packages/st-plugin/sublime_mcp.py::_MCP_TOOLS`) instead of a second
hand-maintained list.

Usage:
    python tools/generate_fallback_catalog.py           # write the catalog
    python tools/generate_fallback_catalog.py --check   # fail if stale

`--check` is what CI/the test suite runs: exit 1 when the committed catalog
does not match what the current backend would produce.
"""

import argparse
import importlib.util
import json
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "packages" / "st-plugin" / "sublime_mcp.py"
OUTPUT = ROOT / "packages" / "node-proxy" / "fallback-tools.json"


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
    """Return the fallback catalog in the same shape as GET /mcp_tools.

    Reuses the backend's own `_get_mcp_tools` so the fallback and the live
    discovery response cannot describe tools differently.
    """
    tools = backend._get_mcp_tools({})["tools"]
    return {
        "_comment": (
            "GENERATED FILE - do not edit. Produced by "
            "tools/generate_fallback_catalog.py from "
            "packages/st-plugin/sublime_mcp.py::_MCP_TOOLS. "
            "Regenerate after changing the backend tool catalog."
        ),
        "tools": sorted(tools, key=lambda tool: tool["name"]),
    }


def render(catalog):
    return json.dumps(catalog, indent=2, sort_keys=False) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if the committed catalog is stale instead of writing it",
    )
    args = parser.parse_args(argv)

    catalog = build_catalog(load_backend())
    rendered = render(catalog)
    count = len(catalog["tools"])

    if args.check:
        if not OUTPUT.exists():
            print("stale: {} is missing".format(OUTPUT))
            return 1
        if OUTPUT.read_text(encoding="utf-8") != rendered:
            print(
                "stale: {} does not match the backend catalog ({} tools).\n"
                "Run: python tools/generate_fallback_catalog.py".format(OUTPUT, count)
            )
            return 1
        print("up to date: {} tools".format(count))
        return 0

    OUTPUT.write_text(rendered, encoding="utf-8")
    print("wrote {} ({} tools)".format(OUTPUT, count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
