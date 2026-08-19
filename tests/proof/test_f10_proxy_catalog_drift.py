"""F10 — node-proxy fallback catalog vs backend _MCP_TOOLS.

PROOF: F10 — 2026-08-17. The node-proxy's static fallback (used when
`/mcp_tools` discovery fails) was a hand-maintained subset: 71 tools
against the backend's 220. A discovery miss silently dropped 149 tools,
including `batch`.

FIXED — 2026-08-19. The fallback is now a generated artifact,
`packages/node-proxy/fallback-tools.json`, emitted from the single source
of truth by `tools/generate_fallback_catalog.py`. These tests are the
drift lock:

  * the committed catalog matches what the backend produces right now
    (`--check`), so editing `_MCP_TOOLS` without regenerating fails CI;
  * the catalog is exactly the backend catalog — no ghosts, nothing
    missing, and required fields match per tool;
  * `index.js` registers from the generated file rather than a
    hand-written list, so the old drift cannot be reintroduced by hand.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
BACKEND = ROOT / "packages" / "st-plugin" / "sublime_mcp.py"
NODE = ROOT / "packages" / "node-proxy" / "index.js"
CATALOG = ROOT / "packages" / "node-proxy" / "fallback-tools.json"
GENERATOR = ROOT / "tools" / "generate_fallback_catalog.py"


def _backend_catalog():
    """Parse _MCP_TOOLS out of the plugin source.

    Deliberately textual: it reads the same file a human edits, so it
    cannot be fooled by the generator's own import machinery.
    """
    text = BACKEND.read_text(encoding="utf-8")
    start = text.index("_MCP_TOOLS = [")
    end = text.index("\n_mcp_tools_lock", start)
    chunk = text[start:end]
    catalog = {}
    # Split on the tuple-start used by every _MCP_TOOLS entry.
    parts = re.split(r'\n    \("', chunk)
    for part in parts[1:]:
        name = part.split('"', 1)[0]
        # An entry can contain a nested "required" (e.g. batch's per-call
        # items schema). The top-level one is emitted last, so take the
        # final match rather than the first.
        matches = re.findall(r'"required":\s*\[(.*?)\]', part)
        required = re.findall(r'"([^"]+)"', matches[-1]) if matches else []
        catalog[name] = frozenset(required)
    return catalog


def _fallback_catalog():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    return {
        tool["name"]: frozenset((tool.get("inputSchema") or {}).get("required", []))
        for tool in data["tools"]
    }


def test_f10_committed_catalog_is_not_stale():
    """Editing _MCP_TOOLS without regenerating must fail here, not in prod."""
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "fallback-tools.json is stale. Run:\n"
        "    python tools/generate_fallback_catalog.py\n\n" + result.stdout + result.stderr
    )


def test_f10_fallback_has_no_ghost_tools():
    backend = _backend_catalog()
    fallback = _fallback_catalog()
    ghosts = sorted(set(fallback) - set(backend))
    assert ghosts == [], "fallback advertises tools the backend does not have: {}".format(ghosts)


def test_f10_overlap_required_fields_match_backend():
    backend = _backend_catalog()
    fallback = _fallback_catalog()
    mismatches = []
    for name in sorted(set(backend) & set(fallback)):
        if backend[name] != fallback[name]:
            mismatches.append(
                "{}: backend required {} vs fallback required {}".format(
                    name, sorted(backend[name]), sorted(fallback[name])
                )
            )
    assert mismatches == [], "F10 schema drift on overlap:\n" + "\n".join(mismatches)


def test_f10_fallback_covers_the_whole_backend_catalog():
    """The original F10 defect, inverted into a lock.

    Previously 149 backend tools (including `batch`) vanished on a
    discovery miss. The generated catalog must now be complete.
    """
    backend = _backend_catalog()
    fallback = _fallback_catalog()
    missing = sorted(set(backend) - set(fallback))
    assert missing == [], (
        "F10 regression: {} backend tools missing from the fallback: {}".format(
            len(missing), missing[:30]
        )
    )
    assert "batch" in fallback, "batch was the headline F10 omission; it must stay covered"
    assert len(fallback) == len(backend)


def test_f10_index_js_registers_from_the_generated_catalog():
    """Lock the wiring: no hand-maintained second list may come back."""
    text = NODE.read_text(encoding="utf-8")
    assert "fallback-tools.json" in text, "index.js must load the generated catalog"
    start = text.index("function registerFallbackTools()")
    end = text.index("if (!await loadDynamicTools())")
    body = text[start:end]
    assert "FALLBACK_TOOLS" in body, "fallback registration must iterate the generated catalog"
    hardcoded = re.findall(r"server\.registerTool\('([a-z0-9_]+)'", body)
    assert hardcoded == [], (
        "hand-maintained fallback tools reintroduced in registerFallbackTools: {}".format(hardcoded)
    )
