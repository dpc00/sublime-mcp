#!/usr/bin/env python3
"""Mine agent JSONL histories for actual sublime-mcp invocations.

The scanner is deliberately conservative: it counts structured tool-call records,
not mentions of tool names in prompts or prose. Results are written as JSON and CSV.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator


CREATED_AT = "2026-05-24T03:51:53-06:00"
PREFIXES = (
    "mcp__sublime-mcp__",
    "mcp__sublime_mcp__",
    "sublime-mcp/",
    "sublime_mcp/",
    "mcp_sublime-mcp_",
    "mcp_sublime_mcp_",
)


@dataclass
class Call:
    client: str
    transcript: str
    line: int
    timestamp: str | None
    tool: str
    call_id: str | None
    status: str
    batched: bool = False


def assignment_strings(path: Path, names: set[str]) -> dict[str, list[Any]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: dict[str, list[Any]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [x.id for x in node.targets if isinstance(x, ast.Name)]
        wanted = next((x for x in targets if x in names), None)
        if not wanted or not isinstance(node.value, (ast.List, ast.Tuple)):
            continue
        values: list[Any] = []
        for elt in node.value.elts:
            if not isinstance(elt, (ast.Tuple, ast.List)):
                continue
            row: list[Any] = []
            for cell in elt.elts:
                try:
                    row.append(ast.literal_eval(cell))
                except (ValueError, TypeError):
                    row.append(None)
            values.append(tuple(row))
        found[wanted] = values
    return found


def catalog(repo: Path) -> set[str]:
    st = assignment_strings(
        repo / "packages/st-plugin/sublime_mcp.py", {"_MCP_TOOLS"}
    ).get("_MCP_TOOLS", [])
    lsp = assignment_strings(
        repo / "packages/lsp-mcp/lsp_mcp.py", {"TOOLS", "_LSP_ST_COMMANDS"}
    )
    dbg = assignment_strings(
        repo / "packages/debugger-mcp/debugger_mcp.py",
        {"TOOLS", "_DEBUGGER_ST_COMMANDS"},
    )
    names = {x[0] for x in st if isinstance(x, tuple) and x and isinstance(x[0], str)}
    names |= {
        x[0]
        for x in lsp.get("TOOLS", [])
        if isinstance(x, tuple) and x and isinstance(x[0], str)
    }
    names |= {
        x[0]
        for x in lsp.get("_LSP_ST_COMMANDS", [])
        if isinstance(x, tuple) and x and isinstance(x[0], str)
    }
    names |= {
        x[0]
        for x in dbg.get("TOOLS", [])
        if isinstance(x, tuple) and x and isinstance(x[0], str)
    }
    names |= {
        "debugger_" + x[0]
        for x in dbg.get("_DEBUGGER_ST_COMMANDS", [])
        if isinstance(x, tuple) and x and isinstance(x[0], str)
    }
    return names


def normalize(name: str, known: set[str]) -> str | None:
    name = name.strip()
    for prefix in PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix) :]
            break
    if name in known:
        return name
    # Some clients encode MCP tools as server__tool or server/tool.
    m = re.search(r"(?:^|[_/.-])sublime[-_]mcp(?:__|/)([A-Za-z0-9_]+)$", name)
    if m and m.group(1) in known:
        return m.group(1)
    return None


def timestamp_of(record: dict[str, Any]) -> str | None:
    for key in ("timestamp", "ts", "created_at", "createdAt"):
        value = record.get(key)
        if isinstance(value, (str, int, float)):
            return str(value)
    payload = record.get("payload")
    if isinstance(payload, dict):
        return timestamp_of(payload)
    return None


def walk_dicts(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def candidate(node: dict[str, Any]) -> tuple[str, str | None, dict[str, Any], str] | None:
    """Return name, id, args and status for a structured invocation node."""
    typ = str(node.get("type", "")).lower()
    kind = str(node.get("kind", "")).lower()
    if typ in {"tool_use", "tool_call", "function_call", "tool.call"}:
        name = node.get("name") or node.get("tool_name") or node.get("toolName")
        args = node.get("input") or node.get("args") or node.get("arguments") or {}
        cid = node.get("id") or node.get("call_id") or node.get("toolCallId") or node.get("uuid")
        if isinstance(name, str):
            return name, str(cid) if cid else None, args if isinstance(args, dict) else {}, "unknown"
    if kind == "tooluse" and isinstance(node.get("data"), dict):
        data = node["data"]
        name = data.get("name")
        if isinstance(name, str):
            return name, data.get("toolUseId"), data.get("input") or {}, "unknown"
    call = node.get("functionCall")
    if isinstance(call, dict) and isinstance(call.get("name"), str):
        return call["name"], call.get("id"), call.get("args") or {}, "unknown"
    fn = node.get("function")
    if isinstance(fn, dict) and isinstance(fn.get("name"), str) and any(
        k in fn for k in ("arguments", "args")
    ):
        return fn["name"], node.get("id"), fn.get("arguments") or fn.get("args") or {}, "unknown"
    ui = node.get("uiEvent")
    if isinstance(ui, dict) and isinstance(ui.get("function_name"), str):
        status = "success" if ui.get("success") is True else "failed" if ui.get("success") is False else "unknown"
        return ui["function_name"], ui.get("call_id"), ui.get("function_args") or {}, status
    # Grok emits authoritative start/completion MCP events.
    if typ == "mcp_tool_call_started" and isinstance(node.get("tool_name"), str):
        if str(node.get("server_name", "")).replace("_", "-") == "sublime-mcp":
            return node["tool_name"], node.get("call_id"), {}, "unknown"
    return None


def outcome(node: dict[str, Any], known: set[str]) -> tuple[str | None, str | None, str] | None:
    typ = str(node.get("type", "")).lower()
    if typ == "tool_result":
        cid = node.get("tool_use_id") or node.get("toolCallId")
        failed = node.get("is_error") is True
        return None, str(cid) if cid else None, "failed" if failed else "success"
    response = node.get("functionResponse")
    if isinstance(response, dict):
        body = response.get("response")
        failed = isinstance(body, dict) and "error" in body
        return None, response.get("id"), "failed" if failed else "success"
    if typ == "tool.result":
        cid = node.get("toolCallId") or node.get("parentUuid")
        body = node.get("result")
        failed = isinstance(body, dict) and any(k in body for k in ("error", "exception"))
        return None, str(cid) if cid else None, "failed" if failed else "success"
    if typ == "mcp_tool_call_completed" and isinstance(node.get("tool_name"), str):
        if str(node.get("server_name", "")).replace("_", "-") == "sublime-mcp":
            tool = normalize(node["tool_name"], known)
            status = "success" if node.get("success") is True else "failed"
            return tool, node.get("call_id"), status
    return None


def expand_batch(args: dict[str, Any], known: set[str]) -> Iterator[str]:
    calls = args.get("calls")
    if not isinstance(calls, list):
        return
    for item in calls:
        if not isinstance(item, dict):
            continue
        raw = item.get("tool") or item.get("name")
        if isinstance(raw, str):
            tool = normalize(raw, known)
            if tool:
                yield tool


def inspect_inner(tool: str, args: dict[str, Any], inner: dict[str, Counter[str]]) -> None:
    if tool == "run_command":
        command = args.get("command")
        if isinstance(command, str) and command:
            inner["run_command_commands"][command] += 1
        scope = args.get("scope")
        if isinstance(scope, str) and scope:
            inner["run_command_scopes"][scope] += 1
    if tool not in {"eval_python", "eval_python_latest"}:
        return
    code = args.get("code")
    if not isinstance(code, str):
        return
    for receiver, method in re.findall(r"\b(view|window|sublime)\.([A-Za-z_]\w*)", code):
        inner["eval_python_api"][f"{receiver}.{method}"] += 1
    for command in re.findall(
        r"\.run_command\(\s*['\"]([^'\"]+)['\"]", code
    ):
        inner["eval_python_run_commands"][command] += 1


def scan(home: Path, known: set[str]) -> tuple[list[Call], dict[str, Any], dict[str, Counter[str]], dict[str, Counter[str]]]:
    calls: list[Call] = []
    corpus = Counter()
    inner: dict[str, Counter[str]] = defaultdict(Counter)
    outcomes: dict[str, Counter[str]] = defaultdict(Counter)
    for root in sorted(x for x in home.iterdir() if x.is_dir() and x.name.startswith(".")):
        client = root.name[1:]
        files = list(root.rglob("*.jsonl"))
        if not files:
            continue
        corpus[f"{client}:files"] += len(files)
        for path in files:
            corpus[f"{client}:bytes"] += path.stat().st_size
            seen: set[tuple[str, str]] = set()
            outcome_seen: set[tuple[str, str]] = set()
            ids: dict[str, str] = {}
            try:
                handle = path.open("r", encoding="utf-8", errors="replace")
            except OSError:
                corpus[f"{client}:unreadable"] += 1
                continue
            with handle:
                for line_no, line in enumerate(handle, 1):
                    corpus[f"{client}:lines"] += 1
                    try:
                        record = json.loads(line)
                    except (json.JSONDecodeError, ValueError):
                        corpus[f"{client}:invalid_json"] += 1
                        continue
                    if not isinstance(record, dict):
                        continue
                    ts = timestamp_of(record)
                    for node in walk_dicts(record):
                        result = outcome(node, known)
                        if result:
                            result_tool, result_id, result_status = result
                            resolved = result_tool or (ids.get(str(result_id)) if result_id else None)
                            result_key = (str(result_id), result_status)
                            if resolved and result_key not in outcome_seen:
                                outcomes[resolved][result_status] += 1
                                outcome_seen.add(result_key)
                        item = candidate(node)
                        if not item:
                            continue
                        raw, cid, args, status = item
                        tool = normalize(raw, known)
                        if not tool:
                            continue
                        # Cumulative transcript snapshots can repeat the same call.
                        key = (cid or f"line:{line_no}", tool)
                        if key in seen:
                            continue
                        seen.add(key)
                        if cid:
                            ids[str(cid)] = tool
                        calls.append(
                            Call(client, str(path), line_no, ts, tool, cid, status)
                        )
                        inspect_inner(tool, args, inner)
                        if tool == "batch":
                            for nested in expand_batch(args, known):
                                calls.append(
                                    Call(client, str(path), line_no, ts, nested, cid, status, True)
                                )
    return calls, dict(corpus), inner, outcomes


def write_outputs(
    calls: list[Call],
    known: set[str],
    corpus: dict[str, Any],
    inner: dict[str, Counter[str]],
    outcomes: dict[str, Counter[str]],
    out: Path,
) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with (out / "sublime_tool_calls.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(calls[0]).keys()) if calls else ["tool"])
        writer.writeheader()
        writer.writerows(asdict(x) for x in calls)

    counts = Counter(x.tool for x in calls)
    direct = Counter(x.tool for x in calls if not x.batched)
    batched = Counter(x.tool for x in calls if x.batched)
    clients: dict[str, Counter[str]] = defaultdict(Counter)
    sessions: dict[str, set[str]] = defaultdict(set)
    first: dict[str, str] = {}
    last: dict[str, str] = {}
    for call in calls:
        clients[call.tool][call.client] += 1
        sessions[call.tool].add(call.transcript)
        if call.timestamp:
            first[call.tool] = min(first.get(call.tool, call.timestamp), call.timestamp)
            last[call.tool] = max(last.get(call.tool, call.timestamp), call.timestamp)

    pairs = Counter()
    by_file: dict[str, list[Call]] = defaultdict(list)
    for call in calls:
        if not call.batched:
            by_file[call.transcript].append(call)
    for seq in by_file.values():
        for left, right in zip(seq, seq[1:]):
            pairs[(left.tool, right.tool)] += 1

    report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_created_at": CREATED_AT,
        "corpus": corpus,
        "summary": {
            "catalog_tools": len(known),
            "calls": len(calls),
            "direct_calls": sum(direct.values()),
            "batched_inner_calls": sum(batched.values()),
            "used_tools": len(counts),
            "unused_tools": len(known - set(counts)),
        },
        "tools": [
            {
                "tool": tool,
                "calls": counts[tool],
                "direct": direct[tool],
                "batched": batched[tool],
                "sessions": len(sessions[tool]),
                "clients": dict(clients[tool]),
                "first_seen": first.get(tool),
                "last_seen": last.get(tool),
                "outcomes": dict(outcomes.get(tool, {})),
            }
            for tool in sorted(counts, key=lambda x: (-counts[x], x))
        ],
        "unused": sorted(known - set(counts)),
        "inner_commands": {
            group: [{"name": name, "count": count} for name, count in values.most_common()]
            for group, values in inner.items()
        },
        "top_sequences": [
            {"from": pair[0], "to": pair[1], "count": count}
            for pair, count in pairs.most_common(100)
        ],
    }
    (out / "sublime_tool_usage.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, default=Path("analysis/transcripts"))
    args = parser.parse_args()
    known = catalog(args.repo)
    calls, corpus, inner, outcomes = scan(args.home, known)
    write_outputs(calls, known, corpus, inner, outcomes, args.out)
    print(f"catalog={len(known)} calls={len(calls)} used={len({x.tool for x in calls})}")


if __name__ == "__main__":
    main()
