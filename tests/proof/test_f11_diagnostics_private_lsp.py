"""F11 — _claude_get_diagnostics reaches into LSP private internals.

PROOF: F11 — 2026-08-17. Source lock: the function looks up
`LSP.plugin.core.registry` via sys.modules and reads
`storage._diagnostics`. Missing registry already returns []. The
`_diagnostics` walk is wrapped so a private-API reshape cannot raise
out of the Claude tool. Live runtime against a real LSP package is
still pending (needs Sublime + LSP).
"""
from pathlib import Path

BACKEND = Path(__file__).parents[2] / "packages" / "st-plugin" / "sublime_mcp.py"


def _function_source(text, signature, terminator):
    start = text.index(signature)
    end = text.index(terminator, start)
    return text[start:end]


def test_f11_diagnostics_reaches_private_lsp_registry_and_storage():
    text = BACKEND.read_text(encoding="utf-8")
    func = _function_source(
        text,
        "def _claude_get_diagnostics(arguments):",
        "def _claude_open_diff(arguments):",
    )
    assert 'sys.modules.get("LSP.plugin.core.registry")' in func
    assert "storage._diagnostics" in func
    assert "windows.lookup(window)" in func


def test_f11_missing_registry_returns_empty_list():
    text = BACKEND.read_text(encoding="utf-8")
    func = _function_source(
        text,
        "def _claude_get_diagnostics(arguments):",
        "def _claude_open_diff(arguments):",
    )
    collect = func.split("def collect():", 1)[1]
    assert 'if not registry_module:' in collect
    assert "return []" in collect.split("if not registry_module:", 1)[1][:120]


def test_f11_private_diagnostics_walk_is_guarded():
    """A missing `_diagnostics` attribute must not escape collect()."""
    text = BACKEND.read_text(encoding="utf-8")
    func = _function_source(
        text,
        "def _claude_get_diagnostics(arguments):",
        "def _claude_open_diff(arguments):",
    )
    collect = func.split("def collect():", 1)[1]
    # The private walk sits inside try/except so AttributeError becomes [].
    assert "storage._diagnostics" in collect
    before, after = collect.split("storage._diagnostics", 1)
    assert "try:" in before
    assert "except" in after
    assert "return []" in after
