"""F6 — python-proxy's batch docstring used to claim one main-thread dispatch
while backend sublime_mcp._batch deliberately does not.

PROOF: F6 — 2026-08-17. FIXED: the docstring no longer claims a shared
main-thread dispatch; corrected to describe the per-call behavior that
sublime_mcp._batch actually implements.

UPDATED 2026-08-19 (F10 second surface). python-proxy no longer carries a
hand-written batch docstring at all: its tools are generated from the
backend `_MCP_TOOLS`, so the tool description an agent sees now comes from
the backend entry. The correction was moved to that entry, which means it
reaches every surface at once (backend MCP, node-proxy dynamic discovery,
node-proxy fallback, and python-proxy) instead of only the Python one.
These tests therefore assert against the source of truth and the generated
artifacts rather than a per-proxy docstring.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
BACKEND = ROOT / "packages" / "st-plugin" / "sublime_mcp.py"
NODE_CATALOG = ROOT / "packages" / "node-proxy" / "fallback-tools.json"
PYTHON_CATALOG = ROOT / "packages" / "python-proxy" / "tool_catalog.py"
PROXY = ROOT / "packages" / "python-proxy" / "mcp_server.py"


def _backend_batch_description():
    """Pull the batch tool's advertised description out of _MCP_TOOLS."""
    text = BACKEND.read_text(encoding="utf-8")
    start = text.index('    ("batch",')
    end = text.index('{"type": "object"', start)
    return text[start:end]


def _catalog_batch_description(tools):
    return next(tool["description"] for tool in tools if tool["name"] == "batch")


def _python_catalog_tools():
    namespace = {}
    exec(compile(PYTHON_CATALOG.read_text(encoding="utf-8"), str(PYTHON_CATALOG), "exec"), namespace)
    return namespace["TOOLS"]


def test_f06_backend_description_no_longer_claims_one_main_thread_dispatch():
    description = _backend_batch_description()
    assert "not wrapped in one shared main-thread" in description
    # The original false claim was that the batch ran as a single dispatch.
    assert "in one main-thread" not in description


def test_f06_correction_reaches_every_generated_surface():
    """The fix is only real if the agent-visible description carries it."""
    node = _catalog_batch_description(
        json.loads(NODE_CATALOG.read_text(encoding="utf-8"))["tools"]
    )
    python = _catalog_batch_description(_python_catalog_tools())
    for surface, description in (("node-proxy", node), ("python-proxy", python)):
        assert "not wrapped in one shared main-thread" in description, (
            "{} batch description lost the F6 correction".format(surface)
        )
    assert node == python, "surfaces disagree about what batch does"


def test_f06_python_proxy_has_no_stale_hand_written_copy():
    """A hand-written docstring here would reintroduce the drift F6 found."""
    text = PROXY.read_text(encoding="utf-8")
    assert "def batch(" not in text, (
        "batch must come from the generated catalog, not a hand-written wrapper"
    )


def test_f06_backend_batch_explicitly_does_not_do_that():
    text = BACKEND.read_text(encoding="utf-8")
    start = text.index("def _batch(args):")
    end = text.index("\n\n\n", start)
    batch_source = text[start:end]
    assert "does NOT wrap the whole batch in one outer" in batch_source
    assert "_on_main()" in batch_source
