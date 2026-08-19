"""sublime-mcp — MCP server.

Wraps the HTTP API exposed by sublime_mcp.py (the ST plugin) and
presents it as MCP tools to Claude Code (or any MCP client).

Tools are built from `tool_catalog.py`, which is generated from the
backend's `_MCP_TOOLS` by `tools/generate_fallback_catalog.py`. This file
therefore contains no hand-maintained tool list: it used to carry 72
hand-written tools against a backend serving 220, which meant 148 tools
were permanently unreachable through this proxy (F10). Add tools to the
backend and regenerate; do not hand-write them here.

Requirements: pip install mcp httpx
Run:          python mcp_server.py
Register:     add to ~/.claude/settings.json mcpServers
"""

import inspect
import os
import sys
from typing import Annotated, Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent
from pydantic import Field

try:
    from tool_catalog import TOOLS
except ImportError:  # running from a source checkout without the package installed
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from tool_catalog import TOOLS

# Platform detection: Windows ST uses 9500, WSL/Linux ST uses 9501
DEFAULT_PORT = 9500 if sys.platform == "win32" else 9501
BASE = os.environ.get("SUBLIME_MCP_BASE", f"http://127.0.0.1:{DEFAULT_PORT}")
# PROOF: F5 — 2026-08-17. Per-endpoint HTTP timeouts. Quick reads stay at
# 10s so a hung backend fails fast; batch / install / search / find /
# eval_python_latest / run_build get 120s because those can legitimately
# exceed 10s while Sublime is still working.
DEFAULT_TIMEOUT = 10.0
SLOW_TIMEOUT = 120.0
SLOW_ENDPOINTS = frozenset({
    "/batch",
    "/install_package",
    "/search_packages",
    "/find_in_files",
    "/eval_python_latest",
    "/run_build",
})
TIMEOUT = DEFAULT_TIMEOUT


def _timeout_for(endpoint: str) -> float:
    return SLOW_TIMEOUT if endpoint in SLOW_ENDPOINTS else DEFAULT_TIMEOUT


print(f"sublime-mcp: BASE={BASE} sys.platform={sys.platform}", file=sys.stderr)
sys.stderr.flush()

mcp = FastMCP("sublime-mcp")
_client = httpx.Client(base_url=BASE, timeout=DEFAULT_TIMEOUT)


def _get(endpoint: str, **params) -> dict:
    r = _client.get(endpoint, params=params, timeout=_timeout_for(endpoint))
    r.raise_for_status()
    return r.json()


def _post(endpoint: str, **body) -> dict:
    r = _client.post(endpoint, json=body, timeout=_timeout_for(endpoint))
    r.raise_for_status()
    return r.json()


# ── generated tool registration ───────────────────────────────────────────────
# Every backend tool has a POST /{name} alias, so one uniform call shape
# works for all of them. FastMCP derives each tool's JSON Schema from the
# function signature, so the catalog's schema is replayed as real typed
# parameters rather than an untyped passthrough dict.

_JSON_TYPES = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _annotation(prop: dict):
    """Turn one JSON Schema property into a typed annotation.

    Descriptions and extra keywords (nested `items`, `maxItems`, ...) are
    carried through a pydantic Field so the client sees the same parameter
    documentation the backend publishes.
    """
    base = _JSON_TYPES.get(prop.get("type"), Any)
    extra = {
        key: value
        for key, value in prop.items()
        if key not in ("type", "description", "default", "title")
    }
    field_kwargs = {}
    if prop.get("description"):
        field_kwargs["description"] = prop["description"]
    if extra:
        field_kwargs["json_schema_extra"] = extra
    if not field_kwargs:
        return base
    return Annotated[base, Field(**field_kwargs)]


def _build_tool(name: str, description: str, schema: dict):
    """Create a typed function for one catalog entry."""
    properties = (schema or {}).get("properties") or {}
    required = set((schema or {}).get("required") or [])

    parameters = []
    annotations = {}
    for key, prop in properties.items():
        prop = prop if isinstance(prop, dict) else {}
        annotation = _annotation(prop)
        if key in required:
            default = inspect.Parameter.empty
        elif "default" in prop:
            default = prop["default"]
        else:
            # Optional with no backend default: omit it from the request
            # entirely rather than inventing a value.
            default = None
            annotation = Optional[annotation]
        parameters.append(
            inspect.Parameter(
                key, inspect.Parameter.KEYWORD_ONLY, default=default, annotation=annotation
            )
        )
        annotations[key] = annotation

    optional_without_default = {
        key
        for key, prop in properties.items()
        if key not in required and not (isinstance(prop, dict) and "default" in prop)
    }

    def call(**kwargs):
        body = {
            key: value
            for key, value in kwargs.items()
            if not (value is None and key in optional_without_default)
        }
        return _post("/" + name, **body)

    call.__name__ = name
    call.__doc__ = description
    call.__signature__ = inspect.Signature(parameters, return_annotation=dict)
    annotations["return"] = dict
    call.__annotations__ = annotations
    return call


for _tool in TOOLS:
    mcp.add_tool(_build_tool(_tool["name"], _tool["description"], _tool.get("inputSchema")))


# ── hand-written overrides ────────────────────────────────────────────────────
# Only for tools that need to post-process the backend response. Everything
# else comes from the generated catalog above. Each override replaces its
# generated twin, so registration order does not decide which one wins.

_OVERRIDDEN = ("get_sheet_content",)

for _name in _OVERRIDDEN:
    mcp.remove_tool(_name)


@mcp.tool(name="get_sheet_content")
def get_sheet_content(index: int):
    """Return the content of any tab by its sheet index (from get_sheets).
    Works for text tabs including untitled buffers and Terminus tabs.
    For image tabs returns the image directly as a renderable image."""
    result = _get("/sheet_content", index=index)
    b64 = result.get("content_base64")
    if b64:
        path = result.get("path", "")
        mime = "image/png" if path.lower().endswith(".png") else \
               "image/jpeg" if path.lower().endswith((".jpg", ".jpeg")) else \
               "image/gif" if path.lower().endswith(".gif") else "image/png"
        return [ImageContent(type="image", data=b64, mimeType=mime)]
    return result


def main():
    mcp.run()


if __name__ == "__main__":
    main()
