"""F11 — _claude_get_diagnostics reaches into LSP private internals.

PROOF: F11 — 2026-08-17. Source lock: the function looks up
`LSP.plugin.core.registry` via sys.modules and reads
`storage._diagnostics`. Missing registry already returns []. The
`_diagnostics` walk is wrapped so a private-API reshape cannot raise
out of the Claude tool.

Live-runtime verified 2026-08-17 against a real Sublime Text + LSP
(Pyright) instance: opened packages/debugger-mcp/debugger_mcp.py,
waited for the language server to attach, and called
_claude_get_diagnostics directly through the live plugin module. It
returned 48 real diagnostics for that file through the try/except-
guarded path, confirming the guard does not interfere with the normal
success path. The failure branch (an actual LSP internals break) is
still only proved at the source level — reproducing that live would
require deliberately breaking a real LSP install, which isn't worth
doing against the user's working environment.
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
