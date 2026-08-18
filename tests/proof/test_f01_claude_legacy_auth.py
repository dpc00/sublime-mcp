"""F1 — Claude legacy /sse + /messages accept requests with no auth token.

PROVE if: an empty-header client can open /sse, get a session, and have a
tools/call reach the dispatcher and return a real result.
KILL if: the legacy path rejects unauthenticated requests.
"""
import importlib.util
import json
from pathlib import Path

import httpx

MODULE = Path(__file__).parents[2] / "packages" / "st-plugin" / "ide_companion.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ide_companion", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_f01_empty_header_client_completes_legacy_tools_call():
    module = load_module()

    def legacy_dispatch(message):
        if message.get("method") == "tools/call":
            return {"jsonrpc": "2.0", "id": message["id"], "result": {"content": []}}
        return {"jsonrpc": "2.0", "id": message.get("id"), "result": {}}

    server = module.IdeCompanionServer(
        lambda message: None,
        auth_token="real-secret-token",
        legacy_dispatcher=legacy_dispatch,
    )
    port = server.start()
    try:
        with httpx.stream(
            "GET", "http://127.0.0.1:{}/sse".format(port), headers={}, timeout=3,
        ) as response:
            assert response.status_code == 200
            lines = response.iter_lines()
            assert next(lines) == "event: endpoint"
            endpoint = next(lines).removeprefix("data: ")

            posted = httpx.post(
                "http://127.0.0.1:{}{}".format(port, endpoint),
                headers={},
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": "openDiff", "arguments": {"filePath": "x", "newContent": "y"}},
                },
                timeout=2,
            )
            assert posted.status_code == 202

            assert next(lines) == ""
            payload = json.loads(next(lines).removeprefix("data: "))
            assert payload["result"] == {"content": []}
    finally:
        server.stop()


def test_f01_modern_mcp_path_does_require_auth_for_contrast():
    module = load_module()
    server = module.IdeCompanionServer(lambda message: {"ok": True}, auth_token="real-secret-token")
    port = server.start()
    try:
        response = httpx.post(
            "http://127.0.0.1:{}/mcp".format(port),
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            timeout=2,
        )
        assert response.status_code == 401
    finally:
        server.stop()
