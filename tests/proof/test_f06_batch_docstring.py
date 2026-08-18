"""F6 — python-proxy's batch docstring used to claim one main-thread dispatch
while backend sublime_mcp._batch deliberately does not.

PROOF: F6 — 2026-08-17. FIXED: docstring no longer claims a shared
main-thread dispatch; corrected to describe the per-call behavior that
sublime_mcp._batch actually implements. This test now locks the fix in as
a regression guard.
"""
import inspect
from pathlib import Path

PROXY = Path(__file__).parents[2] / "packages" / "python-proxy" / "mcp_server.py"
BACKEND = Path(__file__).parents[2] / "packages" / "st-plugin" / "sublime_mcp.py"


def _load_module(path, name):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    return module, spec


def test_f06_docstring_no_longer_claims_one_main_thread_dispatch():
    text = PROXY.read_text(encoding="utf-8")
    start = text.index('def batch(calls: list) -> dict:')
    end = text.index('return _post("/batch"', start)
    docstring = text[start:end]
    assert "one main-thread" not in docstring
    assert "not wrapped in one shared main-thread dispatch" in docstring


def test_f06_backend_batch_explicitly_does_not_do_that():
    text = BACKEND.read_text(encoding="utf-8")
    start = text.index("def _batch(args):")
    end = text.index("\n\n\n", start)
    batch_source = text[start:end]
    assert "does NOT wrap the whole batch in one outer" in batch_source
    assert "_on_main()" in batch_source
