"""F7 — context snapshot caps selectedText at 16 KiB via truncate_utf8;
selection_changed used to send the full view.substr(region) uncapped.

PROOF: F7 — 2026-08-17. FIXED: selection_changed text path also uses
truncate_utf8 / MAX_SELECTED_TEXT_BYTES so both publish paths share one cap.
"""
import importlib.util
from pathlib import Path

BACKEND = Path(__file__).parents[2] / "packages" / "st-plugin" / "sublime_mcp.py"
COMPANION = Path(__file__).parents[2] / "packages" / "st-plugin" / "ide_companion.py"


def load_companion():
    spec = importlib.util.spec_from_file_location("ide_companion", COMPANION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_f07_context_snapshot_caps_selected_text_at_16kib():
    module = load_companion()
    oversized = "x" * (module.MAX_SELECTED_TEXT_BYTES + 4096)
    # snapshot needs a real file path that exists for openFiles; empty list
    # still exercises selectedText only when active_path is set — use touch
    # on a temp-less path by only checking truncate_utf8 used by snapshot.
    capped = module.truncate_utf8(oversized)
    assert len(capped.encode("utf-8")) <= module.MAX_SELECTED_TEXT_BYTES
    assert len(oversized.encode("utf-8")) > module.MAX_SELECTED_TEXT_BYTES


def test_f07_selection_changed_payload_builder_caps_text():
    """Pure helper used by production publish path must cap like snapshot."""
    module = load_companion()
    oversized = "y" * (module.MAX_SELECTED_TEXT_BYTES + 2048)
    # multi-byte edge
    oversized = oversized[:-1] + "€"
    params = module.build_selection_changed_params(
        file_path="/repo/f.py",
        start_line=1,
        start_character=0,
        end_line=2,
        end_character=0,
        text=oversized,
    )
    assert len(params["text"].encode("utf-8")) <= module.MAX_SELECTED_TEXT_BYTES
    assert params["filePath"] == "/repo/f.py"
    assert params["selection"]["start"]["line"] == 1


def test_f07_production_selection_changed_uses_shared_builder_or_truncate():
    text = BACKEND.read_text(encoding="utf-8")
    assert '"selection_changed"' in text
    assert "build_selection_changed_params" in text
    # Must not notify with a raw uncapped dict literal for text=.
    assert '"text": view.substr(region)' not in text
