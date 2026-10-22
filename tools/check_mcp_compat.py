#!/usr/bin/env python3
"""Tell the maintainer when sublime-mcp's MCP implementation needs an upgrade.

Checks, none of which need Sublime except the last:
  1. Spec: a revision in modelcontextprotocol/modelcontextprotocol docs/specification newer than
     the newest one in sublime_mcp._MCP_PROTOCOL_VERSIONS.
  2. Client: MCP-related entries in the oh-my-pi changelog newer than the version recorded in
     tools/mcp_compat_state.json (run with --ack to record the current version as seen).
  3. Server (with --url): the running server answers initialize with the version the client asked
     for, returns -32601 for an unknown method, and lists tools.

Exit status 1 when anything needs attention, so it can run from a scheduler or CI.
Usage: python tools/check_mcp_compat.py [--url http://127.0.0.1:9502/mcp] [--ack]
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE = os.path.join(HERE, "mcp_compat_state.json")
SPEC_API = "https://api.github.com/repos/modelcontextprotocol/modelcontextprotocol/contents/docs/specification"
OMP_CHANGELOG = "https://raw.githubusercontent.com/can1357/oh-my-pi/main/packages/coding-agent/CHANGELOG.md"
MCP_WORDS = re.compile(r"\bMCP\b|/mcp\b|notifications/", re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sublime-mcp-compat-check"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


def supported_versions(kind="PROTOCOL"):
    """Versions in sublime_mcp's _MCP_<kind>_VERSIONS (kind: MODERN, LEGACY); PROTOCOL = both."""
    src = open(os.path.join(ROOT, "sublime_mcp.py"), encoding="utf-8").read()
    if kind == "PROTOCOL":
        return supported_versions("MODERN") + supported_versions("LEGACY")
    m = re.search(r"_MCP_%s_VERSIONS\s*=\s*\(([^)]*)\)" % kind, src)
    return re.findall(r"\d{4}-\d{2}-\d{2}", m.group(1))


def check_spec(problems):
    ours = max(supported_versions())
    names = [x["name"] for x in json.loads(fetch(SPEC_API))]
    published = sorted(n for n in names if re.fullmatch(r"\d{4}-\d{2}-\d{2}", n))
    newer = [n for n in published if n > ours]
    print("spec: newest implemented %s; published %s" % (ours, ", ".join(published)))
    for n in newer:
        problems.append("spec revision %s is newer than %s; read its changelog: "
                        "https://modelcontextprotocol.io/specification/%s/changelog" % (n, ours, n))


def vkey(v):
    return tuple(int(p) for p in v.split("."))


def check_omp(problems, ack):
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    seen = state.get("omp_seen", "0")
    text = fetch(OMP_CHANGELOG)
    version, lines, latest = None, [], None
    for line in text.splitlines():
        m = re.match(r"## \[(\d+\.\d+\.\d+)\]", line)
        if m:
            version = m.group(1)
            latest = latest or version
        elif version and line.startswith("- ") and MCP_WORDS.search(line):
            if vkey(version) > vkey(seen if seen != "0" else "0.0.0"):
                lines.append((version, re.sub(r"\s*\(\[#\d+\].*$", "", line)[:240]))
    print("omp: latest %s, last acknowledged %s, %d MCP-related entries since" % (latest, seen, len(lines)))
    if lines:
        problems.append("oh-my-pi changed MCP behavior since %s; review:\n  " % seen
                        + "\n  ".join("[%s] %s" % l for l in lines))
    if ack and latest:
        state["omp_seen"] = latest
        json.dump(state, open(STATE, "w"), indent=2)
        print("recorded omp_seen = %s" % latest)


def rpc(url, msg):
    req = urllib.request.Request(url, json.dumps(msg).encode(), {
        "Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    with urllib.request.urlopen(req, timeout=15) as r:
        body = r.read().decode()
    return json.loads(body) if body else None


def post(url, msg, headers=None):
    """POST one JSON-RPC message; (http status, parsed body or None)."""
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    h.update(headers or {})
    req = urllib.request.Request(url, json.dumps(msg).encode(), h)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            status, body = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read().decode()
    return status, (json.loads(body) if body else None)


def modern(msg, version, extra=None):
    """A modern-era request: version, client identity and capabilities in params._meta."""
    params = dict(msg.get("params") or {})
    params["_meta"] = {"io.modelcontextprotocol/protocolVersion": version,
                       "io.modelcontextprotocol/clientInfo": {"name": "compat-check", "version": "0"},
                       "io.modelcontextprotocol/clientCapabilities": {}}
    out = dict(msg, params=params)
    headers = {"MCP-Protocol-Version": version, "Mcp-Method": msg["method"]}
    if msg["method"] == "tools/call":
        headers["Mcp-Name"] = params["name"]
    headers.update(extra or {})
    return out, headers


def expect(problems, what, ok, got):
    if not ok:
        problems.append("%s: unexpected answer %r" % (what, got))


def check_server(url, problems):
    for v in supported_versions("LEGACY"):
        _, got = post(url, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                            "params": {"protocolVersion": v, "capabilities": {},
                                       "clientInfo": {"name": "compat-check", "version": "0"}}})
        expect(problems, "initialize(%s)" % v, got["result"]["protocolVersion"] == v, got)
    _, bogus = post(url, {"jsonrpc": "2.0", "id": 2, "method": "no/such/method"})
    expect(problems, "legacy unknown method", bogus.get("error", {}).get("code") == -32601, bogus)
    _, tools = post(url, {"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    n = len(tools["result"]["tools"])
    for v in supported_versions("MODERN"):
        msg, h = modern({"jsonrpc": "2.0", "id": 4, "method": "server/discover"}, v)
        status, got = post(url, msg, h)
        r = (got or {}).get("result", {})
        expect(problems, "server/discover(%s)" % v,
               status == 200 and r.get("resultType") == "complete" and v in r.get("supportedVersions", [])
               and "ttlMs" in r and r.get("cacheScope") in ("public", "private"), (status, got))
        msg, h = modern({"jsonrpc": "2.0", "id": 5, "method": "tools/list"}, v)
        status, got = post(url, msg, h)
        r = (got or {}).get("result", {})
        expect(problems, "modern tools/list(%s)" % v,
               status == 200 and len(r.get("tools", [])) == n and "ttlMs" in r and "cacheScope" in r,
               (status, got))
        msg, h = modern({"jsonrpc": "2.0", "id": 6, "method": "no/such/method"}, v)
        status, got = post(url, msg, h)
        expect(problems, "modern unknown method", status == 404 and got["error"]["code"] == -32601,
               (status, got))
        msg, h = modern({"jsonrpc": "2.0", "id": 7, "method": "tools/list"}, v, {"Mcp-Method": "tools/call"})
        status, got = post(url, msg, h)
        expect(problems, "modern header mismatch", status == 400 and got["error"]["code"] == -32020,
               (status, got))
    msg, h = modern({"jsonrpc": "2.0", "id": 8, "method": "tools/list"}, "1900-01-01")
    status, got = post(url, msg, h)
    expect(problems, "modern unsupported version",
           status == 400 and got["error"]["code"] == -32022 and "supported" in got["error"]["data"],
           (status, got))
    print("server: %s ok, %d tools listed" % (url, n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="MCP endpoint of the running server, e.g. http://127.0.0.1:9502/mcp")
    ap.add_argument("--ack", action="store_true", help="record the current oh-my-pi version as reviewed")
    args = ap.parse_args()
    problems = []
    for name, fn in (("spec", lambda: check_spec(problems)),
                     ("omp", lambda: check_omp(problems, args.ack)),
                     ("server", lambda: check_server(args.url, problems) if args.url else None)):
        try:
            fn()
        except Exception as e:  # a check that cannot run is itself a warning, never silence
            problems.append("%s check could not run: %r" % (name, e))
    if problems:
        print("\nNEEDS ATTENTION:")
        for p in problems:
            print("- " + p)
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
