#!/usr/bin/env python3
"""Classify eval_python usage without retaining raw code or transcript output."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import analyze_sublime_transcripts as base


CATEGORIES = {
    "terminal_control": r"\b(?:ai_terminal|terminus)[A-Za-z0-9_]*\b",
    "view_discovery": r"(?:active_window|\.windows|\.views|active_view|\.sheets|\.panels)",
    "focus_navigation": r"(?:focus_view|focus_group|get_view_index|active_view_in_group)",
    "buffer_inspection": r"(?:\.substr|\.size\(|\.sel\(|\.file_name|\.name\(|\.rowcol|\.text_point)",
    "tab_close_lifecycle": r"(?:\.close\(|close_file|set_scratch|is_dirty|is_valid)",
    "viewport_geometry": r"(?:viewport_|layout_|text_to_layout|layout_to_window|line_height|scroll_lines)",
    "settings_resources": r"(?:load_settings|save_settings|\.settings\(|packages_path|load_resource|find_resources|decode_value)",
    "selection_region": r"(?:sublime\.Region|\.sel\(|drag_select|move_to|\bmove\b)",
    "panel_console": r"(?:show_panel|hide_panel|active_panel|\.panels\(|console)",
    "clipboard": r"(?:get_clipboard|set_clipboard|\bcopy\b)",
    "command_execution": r"\.run_command\(",
    "buffer_mutation": r"(?:\binsert\b|\.erase\(|\.replace\(|set_text|send_to_view)",
    "plugin_reload_test": r"(?:reload_plugin|api_test|plugin_loaded|plugin_unloaded)",
    "timers_async": r"(?:set_timeout|set_timeout_async)",
}


def classify(code: str) -> list[str]:
    labels = [name for name, pattern in CATEGORIES.items() if re.search(pattern, code, re.I)]
    return labels or ["other"]


def scan(home: Path, repo: Path) -> dict:
    known = base.catalog(repo)
    category_calls = Counter()
    category_sessions: dict[str, set[str]] = defaultdict(set)
    api = Counter()
    commands = Counter()
    clients = Counter()
    dates = Counter()
    shapes = Counter()
    shape_categories: dict[str, Counter[str]] = defaultdict(Counter)
    session_calls = Counter()
    totals = Counter()

    for root in sorted(x for x in home.iterdir() if x.is_dir() and x.name.startswith(".")):
        client = root.name[1:]
        for path in root.rglob("*.jsonl"):
            seen: set[tuple[str, str]] = set()
            try:
                handle = path.open("r", encoding="utf-8", errors="replace")
            except OSError:
                continue
            with handle:
                for line_no, line in enumerate(handle, 1):
                    try:
                        record = json.loads(line)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    if not isinstance(record, dict):
                        continue
                    ts = base.timestamp_of(record)
                    for node in base.walk_dicts(record):
                        item = base.candidate(node)
                        if not item:
                            continue
                        raw, cid, args, _ = item
                        tool = base.normalize(raw, known)
                        if tool not in {"eval_python", "eval_python_latest"}:
                            continue
                        code = args.get("code")
                        if not isinstance(code, str):
                            totals["missing_code"] += 1
                            continue
                        digest = hashlib.sha256(code.encode("utf-8", errors="replace")).hexdigest()[:16]
                        key = (cid or f"line:{line_no}", digest)
                        if key in seen:
                            continue
                        seen.add(key)
                        totals["calls"] += 1
                        totals["characters"] += len(code)
                        totals["lines"] += code.count("\n") + 1
                        clients[client] += 1
                        session = str(path)
                        session_calls[session] += 1
                        if ts and len(ts) >= 10:
                            dates[ts[:10]] += 1
                        labels = classify(code)
                        for label in labels:
                            category_calls[label] += 1
                            category_sessions[label].add(session)
                            shape_categories[digest][label] += 1
                        shapes[digest] += 1
                        for receiver, method in re.findall(
                            r"\b(view|window|sublime)\.([A-Za-z_]\w*)", code
                        ):
                            api[f"{receiver}.{method}"] += 1
                        for command in re.findall(
                            r"\.run_command\(\s*['\"]([^'\"]+)['\"]", code
                        ):
                            commands[command] += 1

    repeated_calls = sum(count for count in shapes.values() if count > 1)
    return {
        "summary": {
            **totals,
            "sessions": len(session_calls),
            "unique_exact_snippets": len(shapes),
            "calls_in_repeated_snippets": repeated_calls,
            "max_calls_in_one_session": max(session_calls.values(), default=0),
        },
        "clients": dict(clients.most_common()),
        "dates": dict(sorted(dates.items())),
        "categories": [
            {
                "category": name,
                "calls": count,
                "sessions": len(category_sessions[name]),
            }
            for name, count in category_calls.most_common()
        ],
        "api": [{"name": name, "count": count} for name, count in api.most_common()],
        "commands": [
            {"name": name, "count": count} for name, count in commands.most_common()
        ],
        "repeated_shapes": [
            {
                "hash": digest,
                "calls": count,
                "categories": list(shape_categories[digest]),
            }
            for digest, count in shapes.most_common(100)
            if count > 1
        ],
        "busiest_sessions": [
            {"transcript": path, "calls": count}
            for path, count in session_calls.most_common(50)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--out", type=Path, default=Path("analysis/transcripts/eval_python_analysis.json")
    )
    args = parser.parse_args()
    result = scan(args.home, args.repo)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
