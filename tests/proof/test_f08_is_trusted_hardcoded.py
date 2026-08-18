"""F8 — IdeContextTracker.snapshot always reports isTrusted: true; there is
no code path that can make it false.

PROVE if: no argument/flag exists to obtain isTrusted: false from a real
snapshot call as the production call site actually invokes it.
KILL if: trust is configurable or derived and can be made false.
"""
import importlib.util
from pathlib import Path

MODULE = Path(__file__).parents[2] / "packages" / "st-plugin" / "ide_companion.py"
BACKEND = Path(__file__).parents[2] / "packages" / "st-plugin" / "sublime_mcp.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ide_companion", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_f08_default_snapshot_call_is_always_trusted():
    module = load_module()
    tracker = module.IdeContextTracker(clock=lambda: 1)
    context = tracker.snapshot([])
    assert context["workspaceState"]["isTrusted"] is True


def test_f08_production_call_site_hardcodes_is_trusted_true():
    text = BACKEND.read_text(encoding="utf-8")
    assert "is_trusted=True" in text
    assert "is_trusted=False" not in text
    assert "is_trusted=" in text and text.count("is_trusted=True") >= 1
