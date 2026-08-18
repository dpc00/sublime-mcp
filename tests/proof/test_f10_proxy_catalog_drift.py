"""F10 — node-proxy static fallback catalog vs backend _MCP_TOOLS.

PROOF: F10 — 2026-08-17. Fallback is a hand-maintained subset (71 tools)
of the backend catalog (220). No fallback-only ghosts. 149 backend tools
are missing from the fallback, including batch — that is the drift risk
when /mcp_tools discovery fails. A full fallback generator is deferred;
this test fails if the overlap required-fields diverge or if the fallback
advertises a tool the backend does not have.
"""
import re
from pathlib import Path

BACKEND = Path(__file__).parents[2] / "packages" / "st-plugin" / "sublime_mcp.py"
NODE = Path(__file__).parents[2] / "packages" / "node-proxy" / "index.js"


def _backend_catalog():
    text = BACKEND.read_text(encoding="utf-8")
    start = text.index("_MCP_TOOLS = [")
    end = text.index("\n_mcp_tools_lock", start)
    chunk = text[start:end]
    catalog = {}
    # Split on the tuple-start used by every _MCP_TOOLS entry.
    parts = re.split(r'\n    \("', chunk)
    for part in parts[1:]:
        name = part.split('"', 1)[0]
        required = []
        match = re.search(r'"required":\s*\[(.*?)\]', part)
        if match:
            required = re.findall(r'"([^"]+)"', match.group(1))
        catalog[name] = frozenset(required)
    return catalog


def _fallback_catalog():
    text = NODE.read_text(encoding="utf-8")
    start = text.index("function registerFallbackTools()")
    end = text.index("if (!await loadDynamicTools())")
    chunk = text[start:end]
    catalog = {}
    for match in re.finditer(r"\['([a-z0-9_]+)'", chunk):
        catalog[match.group(1)] = frozenset()
    # registerTool('name', { ... inputSchema: { ... }, ...
    for match in re.finditer(
        r"server\.registerTool\('([a-z0-9_]+)',\s*\{(.*?)\n\}, async",
        chunk,
        re.S,
    ):
        name = match.group(1)
        body = match.group(2)
        schema_match = re.search(r"inputSchema:\s*\{(.*?)\}", body, re.S)
        required = set()
        if schema_match:
            fields = schema_match.group(1).strip()
            if fields:
                pieces = re.split(
                    r",\s*(?=[A-Za-z_][A-Za-z0-9_]*\s*:)",
                    fields,
                )
                for piece in pieces:
                    field = re.match(
                        r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)",
                        piece.strip(),
                    )
                    if not field:
                        continue
                    field_name, expr = field.group(1), field.group(2)
                    if ".optional()" in expr or ".default(" in expr:
                        continue
                    required.add(field_name)
        catalog[name] = frozenset(required)
    return catalog


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
    assert mismatches == [], "F10 PROVED schema drift on overlap:\n" + "\n".join(mismatches)


def test_f10_fallback_is_a_strict_subset_so_discovery_failure_drops_tools():
    """Characterization of the dual-catalog risk: fallback is smaller.
    A generator that emits fallback from _MCP_TOOLS would kill this gap;
    until then this test records the missing set so it cannot grow
    silently without someone noticing the assertion message."""
    backend = _backend_catalog()
    fallback = _fallback_catalog()
    missing = sorted(set(backend) - set(fallback))
    assert "batch" in missing, (
        "F10: batch used to be the headline omission; if it is now in the "
        "fallback, drop this assert and keep the count cap"
    )
    assert len(missing) >= 100, (
        "F10 PROVED: fallback is missing {} backend tools when dynamic "
        "discovery fails: {}".format(len(missing), missing[:20])
    )
    # Lock the current missing count so silent growth is a failure.
    # Shrink is fine (fallback catching up). Growth means more drift.
    assert len(missing) <= 149, (
        "fallback lost ground: {} backend tools now missing (was 149). "
        "Missing sample: {}".format(len(missing), missing[:30])
    )
