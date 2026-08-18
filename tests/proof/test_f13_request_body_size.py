"""F13 — companion HTTP handlers used to trust Content-Length and read the
full body with no size ceiling.

PROOF: F13 — 2026-08-17. FIXED: MAX_REQUEST_BODY_BYTES (64 MiB) added;
requests over the cap get 413 before the body is read. These tests lock
the fix in: legitimate bodies still work, oversized ones are rejected.
"""
import importlib.util
from pathlib import Path

import httpx

MODULE = Path(__file__).parents[2] / "packages" / "st-plugin" / "ide_companion.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ide_companion", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_f13_five_mib_authenticated_body_is_still_fully_accepted():
    module = load_module()
    seen_sizes = []

    def dispatch(message):
        seen_sizes.append(len(message.get("params", {}).get("padding", "")))
        return {"jsonrpc": "2.0", "id": message["id"], "result": {}}

    server = module.IdeCompanionServer(dispatch, auth_token="token")
    port = server.start()
    try:
        padding = "x" * (5 * 1024 * 1024)
        body = {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {"padding": padding}}
        response = httpx.post(
            "http://127.0.0.1:{}/mcp".format(port),
            json=body,
            headers={"Authorization": "Bearer token"},
            timeout=15,
        )
        assert response.status_code == 200
        assert seen_sizes == [len(padding)]
    finally:
        server.stop()


def test_f13_over_cap_body_is_rejected_with_413():
    module = load_module()
    dispatched = []
    server = module.IdeCompanionServer(
        lambda message: dispatched.append(message) or {"jsonrpc": "2.0", "id": 1, "result": {}},
        auth_token="token",
    )
    port = server.start()
    try:
        oversized_body = b"x" * (module.MAX_REQUEST_BODY_BYTES + 1)
        response = httpx.post(
            "http://127.0.0.1:{}/mcp".format(port),
            headers={"Authorization": "Bearer token", "Content-Type": "application/json"},
            content=oversized_body,
            timeout=15,
        )
        assert response.status_code == 413
        assert dispatched == []
    finally:
        server.stop()


def test_f13_connection_does_not_desync_after_413():
    """PROOF: F13 keep-alive residual — 2026-08-17. The 413 handler closes
    the connection instead of leaving an undrained declared body on the
    socket, so a pooled client's next request never gets misframed as
    leftover body bytes from the rejected one."""
    module = load_module()
    dispatched = []
    server = module.IdeCompanionServer(
        lambda message: dispatched.append(message) or {"jsonrpc": "2.0", "id": message["id"], "result": {"ok": True}},
        auth_token="token",
    )
    port = server.start()
    try:
        with httpx.Client(timeout=15) as client:
            oversized_body = b"x" * (module.MAX_REQUEST_BODY_BYTES + 1)
            first = client.post(
                "http://127.0.0.1:{}/mcp".format(port),
                headers={"Authorization": "Bearer token", "Content-Type": "application/json"},
                content=oversized_body,
            )
            assert first.status_code == 413

            second = client.post(
                "http://127.0.0.1:{}/mcp".format(port),
                json={"jsonrpc": "2.0", "id": 2, "method": "ping"},
                headers={"Authorization": "Bearer token"},
            )
            assert second.status_code == 200
            assert second.json()["result"] == {"ok": True}
            assert [m["id"] for m in dispatched] == [2]
    finally:
        server.stop()
