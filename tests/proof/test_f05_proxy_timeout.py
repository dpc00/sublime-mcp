"""F5 — both proxies used a hard ~10s HTTP timeout against the Sublime
backend. A healthy 12s /batch completed on the backend while the proxy
raised a client timeout.

PROOF: F5 — 2026-08-17. FIXED: per-endpoint timeouts. batch / install /
search / find_in_files / eval_python_latest / run_build use SLOW_TIMEOUT
(120s); quick reads stay at 10s. These tests lock the fix in: a healthy
12s batch reaches the client, and a 12s read still fails at the default.
"""
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import httpx
import pytest

from tests.proof.fakes.fake_bridge import FakeBridge

ROOT = Path(__file__).parents[2]
PYTHON_PROXY = ROOT / "packages" / "python-proxy" / "mcp_server.py"
NODE_HTTP = ROOT / "packages" / "node-proxy" / "http.js"
NODE_INDEX = ROOT / "packages" / "node-proxy" / "index.js"
NODE_PROBE = Path(__file__).parent / "fakes" / "node_post.mjs"

BACKEND_DELAY_S = 12.0
_LOAD_COUNTER = 0


def load_python_proxy(base_url):
    global _LOAD_COUNTER
    _LOAD_COUNTER += 1
    os.environ["SUBLIME_MCP_BASE"] = base_url
    spec = importlib.util.spec_from_file_location(
        "mcp_server_f05_{}".format(_LOAD_COUNTER), PYTHON_PROXY
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_f05_python_proxy_fast_batch_still_succeeds():
    bridge = FakeBridge(delay_s=0.2)
    bridge.start()
    module = None
    try:
        module = load_python_proxy(bridge.base_url)
        result = module._post("/batch", calls=[{"tool": "get_line_count"}])
        assert result == {"results": [{"ok": True}]}
        assert bridge.completed.is_set()
    finally:
        if module is not None:
            module._client.close()
        bridge.stop()


def test_f05_python_proxy_batch_survives_healthy_12s_backend():
    """Regression lock: a healthy 12s /batch must reach the MCP client.

    On current (unfixed) code this fails with httpx.TimeoutException at ~10s
    even though FakeBridge still completes — that is the F5 proof.
    """
    bridge = FakeBridge(delay_s=BACKEND_DELAY_S)
    bridge.start()
    module = None
    try:
        module = load_python_proxy(bridge.base_url)
        result = module._post("/batch", calls=[{"tool": "get_line_count"}])
        assert result == {"results": [{"ok": True}]}
        assert bridge.completed.wait(2.0), "backend must finish its 12s work"
    except httpx.TimeoutException as exc:
        backend_finished = bridge.completed.wait(BACKEND_DELAY_S + 2.0)
        pytest.fail(
            "F5 PROVED: python-proxy timed out ({}) while the backend "
            "was still healthy (completed={})".format(exc, backend_finished)
        )
    finally:
        if module is not None:
            module._client.close()
        bridge.stop()


def test_f05_node_proxy_batch_survives_healthy_12s_backend():
    """Same trial against node-proxy's production post()."""
    if not NODE_PROBE.is_file():
        pytest.skip("node post probe not present yet")
    bridge = FakeBridge(delay_s=BACKEND_DELAY_S)
    bridge.start()
    try:
        env = os.environ.copy()
        env["SUBLIME_MCP_BASE"] = bridge.base_url
        proc = subprocess.run(
            ["node", str(NODE_PROBE)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=BACKEND_DELAY_S + 8,
        )
        if proc.returncode != 0:
            backend_finished = bridge.completed.wait(BACKEND_DELAY_S + 2.0)
            pytest.fail(
                "F5 PROVED: node-proxy timed out or errored while the backend "
                "was still healthy (completed={}, stderr={})".format(
                    backend_finished, proc.stderr.strip()
                )
            )
        assert json.loads(proc.stdout) == {"results": [{"ok": True}]}
        assert bridge.completed.is_set()
    finally:
        bridge.stop()


def test_f05_python_proxy_quick_read_still_capped_at_default():
    """Hung /active_file must still fail at the 10s default — we did not
    just raise every timeout to 120s."""
    bridge = FakeBridge(delay_s=BACKEND_DELAY_S, payload={"path": "x.py"})
    bridge.start()
    module = None
    try:
        module = load_python_proxy(bridge.base_url)
        with pytest.raises(httpx.TimeoutException):
            module._get("/active_file")
        assert bridge.completed.wait(BACKEND_DELAY_S + 2.0)
    finally:
        if module is not None:
            module._client.close()
        bridge.stop()


def test_f05_python_slow_tools_get_more_headroom_than_reads():
    module = load_python_proxy("http://127.0.0.1:9")
    try:
        assert module.DEFAULT_TIMEOUT == 10.0
        assert module.SLOW_TIMEOUT == 120.0
        for endpoint in (
            "/batch",
            "/install_package",
            "/search_packages",
            "/find_in_files",
            "/eval_python_latest",
            "/run_build",
        ):
            assert module._timeout_for(endpoint) == module.SLOW_TIMEOUT
        assert module._timeout_for("/active_file") == module.DEFAULT_TIMEOUT
        assert module._timeout_for("/selection") == module.DEFAULT_TIMEOUT
    finally:
        module._client.close()


def test_f05_node_slow_tools_get_more_headroom_than_reads():
    http_js = NODE_HTTP.read_text(encoding="utf-8")
    index_js = NODE_INDEX.read_text(encoding="utf-8")
    assert "export const DEFAULT_TIMEOUT_MS = 10_000" in http_js
    assert "export const SLOW_TIMEOUT_MS = 120_000" in http_js
    for endpoint in (
        "/batch",
        "/install_package",
        "/search_packages",
        "/find_in_files",
        "/eval_python_latest",
        "/run_build",
    ):
        assert "'{}'".format(endpoint) in http_js
    assert "AbortSignal.timeout(timeoutMsFor(endpoint))" in http_js
    assert "const TIMEOUT = 10_000" not in index_js
    assert "from './http.js'" in index_js
