import importlib.util
import json
import os
import shutil
import threading
import time
import uuid
from pathlib import Path

import httpx
import pytest


MODULE = Path(__file__).parents[1] / "packages" / "st-plugin" / "ide_companion.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ide_companion", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def workspace_tmp_path():
    path = Path.cwd() / ".test-artifacts" / uuid.uuid4().hex
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_workspace_path_value_is_absolute_unique_and_uses_requested_separator(workspace_tmp_path):
    module = load_module()
    first = workspace_tmp_path / "one"
    second = workspace_tmp_path / "two"
    value = module.workspace_path_value([first, first, second], path_separator=";")
    assert value == ";".join((str(first.resolve()), str(second.resolve())))


def test_discovery_file_has_required_name_and_content_and_replaces_stale(workspace_tmp_path):
    module = load_module()
    stale = workspace_tmp_path / "gemini-ide-server-123-111.json"
    unrelated = workspace_tmp_path / "gemini-ide-server-999-111.json"
    stale.write_text("{}", encoding="utf-8")
    unrelated.write_text("{}", encoding="utf-8")

    path = module.create_gemini_discovery_file(
        pid=123,
        port=456,
        workspace_paths=[workspace_tmp_path],
        auth_token="secret",
        directory=workspace_tmp_path,
    )

    assert Path(path).name == "gemini-ide-server-123-456.json"
    assert not stale.exists()
    assert unrelated.exists()
    assert json.loads(Path(path).read_text(encoding="utf-8")) == {
        "port": 456,
        "workspacePath": str(workspace_tmp_path.resolve()),
        "authToken": "secret",
        "ideInfo": {"name": "sublime", "displayName": "Sublime Text"},
    }


def test_remove_discovery_file_is_idempotent(workspace_tmp_path):
    module = load_module()
    path = workspace_tmp_path / "record.json"
    path.write_text("{}", encoding="utf-8")
    module.remove_discovery_file(path)
    module.remove_discovery_file(path)
    assert not path.exists()


def test_qwen_discovery_file_has_current_lock_contract(workspace_tmp_path):
    module = load_module()
    path = module.create_qwen_discovery_file(
        port=4321,
        workspace_paths=[workspace_tmp_path],
        auth_token="secret",
        parent_pid=123,
        directory=workspace_tmp_path,
    )
    assert Path(path).name == "4321.lock"
    assert json.loads(Path(path).read_text(encoding="utf-8")) == {
        "port": 4321,
        "workspacePath": str(workspace_tmp_path.resolve()),
        "authToken": "secret",
        "ppid": 123,
        "ideName": "Sublime Text",
        "ideInfo": {"name": "sublime", "displayName": "Sublime Text"},
    }


def test_server_requires_exact_bearer_and_dispatches_mcp():
    module = load_module()
    seen = []

    def dispatch(message):
        seen.append(message)
        return {"jsonrpc": "2.0", "id": message["id"], "result": {"ok": True}}

    server = module.IdeCompanionServer(dispatch, auth_token="expected")
    port = server.start()
    url = "http://127.0.0.1:{}/mcp".format(port)
    body = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
    try:
        assert httpx.post(url, json=body, timeout=2).status_code == 401
        assert httpx.post(
            url, json=body, headers={"Authorization": "Bearer wrong"}, timeout=2
        ).status_code == 401
        response = httpx.post(
            url,
            json=body,
            headers={"Authorization": "Bearer expected"},
            timeout=2,
        )
        assert response.status_code == 200
        assert response.json()["result"] == {"ok": True}
        assert seen == [body]
    finally:
        server.stop()


def test_server_exposes_session_scoped_legacy_sse_for_claude():
    module = load_module()

    def legacy_dispatch(message):
        return {"jsonrpc": "2.0", "id": message["id"], "result": {"legacy": True}}

    server = module.IdeCompanionServer(
        lambda message: None,
        auth_token="expected",
        legacy_dispatcher=legacy_dispatch,
    )
    port = server.start()
    headers = {}
    try:
        with httpx.stream(
            "GET", "http://127.0.0.1:{}/sse".format(port), headers=headers, timeout=3
        ) as response:
            assert response.status_code == 200
            lines = response.iter_lines()
            assert next(lines) == "event: endpoint"
            endpoint_line = next(lines)
            endpoint = endpoint_line.removeprefix("data: ")
            posted = httpx.post(
                "http://127.0.0.1:{}{}".format(port, endpoint),
                headers=headers,
                json={"jsonrpc": "2.0", "id": 7, "method": "ping"},
                timeout=2,
            )
            assert posted.status_code == 202
            assert next(lines) == ""
            payload_line = next(lines)
            assert json.loads(payload_line.removeprefix("data: "))["result"] == {
                "legacy": True
            }
    finally:
        server.stop()


def test_server_start_stop_are_repeatable():
    module = load_module()
    server = module.IdeCompanionServer(lambda message: None, auth_token="token")
    first = server.start()
    assert first == server.start()
    server.stop()
    server.stop()
    second = server.start()
    try:
        assert isinstance(second, int) and second > 0
    finally:
        server.stop()


def test_server_rejects_non_loopback_origin():
    module = load_module()
    server = module.IdeCompanionServer(lambda message: None, auth_token="token")
    port = server.start()
    try:
        response = httpx.post(
            "http://127.0.0.1:{}/mcp".format(port),
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
            headers={"Authorization": "Bearer token", "Origin": "https://evil.example"},
            timeout=2,
        )
        assert response.status_code == 403
    finally:
        server.stop()


def test_authenticated_get_stream_receives_server_notification():
    module = load_module()
    subscribed = threading.Event()
    received = []
    server = module.IdeCompanionServer(
        lambda message: None,
        auth_token="token",
        on_subscribe=subscribed.set,
    )
    port = server.start()

    def listen():
        with httpx.stream(
            "GET",
            "http://127.0.0.1:{}/mcp".format(port),
            headers={"Authorization": "Bearer token", "Accept": "text/event-stream"},
            timeout=5,
        ) as response:
            assert response.status_code == 200
            for line in response.iter_lines():
                if line.startswith("data: "):
                    received.append(json.loads(line[6:]))
                    return

    listener = threading.Thread(target=listen)
    listener.start()
    try:
        assert subscribed.wait(2)
        assert server.notify("ide/contextUpdate", {"workspaceState": {}}) == 1
        listener.join(timeout=3)
        assert received == [{
            "jsonrpc": "2.0",
            "method": "ide/contextUpdate",
            "params": {"workspaceState": {}},
        }]
    finally:
        server.stop()
        listener.join(timeout=2)


def test_context_snapshot_filters_orders_limits_and_uses_active_details(workspace_tmp_path):
    module = load_module()
    paths = []
    for index in range(12):
        path = workspace_tmp_path / ("file-{}.py".format(index))
        path.write_text("pass\n", encoding="utf-8")
        paths.append(path)
    tracker = module.IdeContextTracker(clock=lambda: 99)
    for index, path in enumerate(paths):
        tracker.touch(path, timestamp=index)
    missing = workspace_tmp_path / "missing.py"

    context = tracker.snapshot(
        list(paths) + [missing, paths[-1]],
        active_path=paths[-1],
        cursor=(4, 7),
        selected_text="chosen",
    )
    files = context["workspaceState"]["openFiles"]
    assert len(files) == 10
    assert files[0] == {
        "path": str(paths[-1].resolve()),
        "timestamp": 99000,
        "isActive": True,
        "cursor": {"line": 4, "character": 7},
        "selectedText": "chosen",
    }
    assert all(item["path"] != str(missing) for item in files)
    assert context["workspaceState"]["isTrusted"] is True


def test_selected_text_truncation_preserves_utf8_boundary():
    module = load_module()
    text = "a" * (module.MAX_SELECTED_TEXT_BYTES - 1) + "€"
    truncated = module.truncate_utf8(text)
    assert truncated == "a" * (module.MAX_SELECTED_TEXT_BYTES - 1)
    assert len(truncated.encode("utf-8")) <= module.MAX_SELECTED_TEXT_BYTES


def test_companion_dispatch_advertises_only_diff_contract():
    module = load_module()
    response = module.companion_dispatch(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        lambda arguments: None,
        lambda arguments: None,
    )
    assert [tool["name"] for tool in response["result"]["tools"]] == [
        "openDiff",
        "closeDiff",
    ]


def test_companion_dispatch_routes_diff_tools_and_rejects_general_tools():
    module = load_module()
    opened = []
    closed = []
    open_response = module.companion_dispatch(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "openDiff", "arguments": {"filePath": "x"}},
        },
        lambda arguments: opened.append(arguments) or {"content": []},
        lambda arguments: closed.append(arguments),
    )
    rejected = module.companion_dispatch(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "get_open_files", "arguments": {}},
        },
        lambda arguments: None,
        lambda arguments: None,
    )
    assert open_response["result"] == {"content": []}
    assert opened == [{"filePath": "x"}]
    assert closed == []
    assert rejected["error"]["message"] == "Unknown tool: get_open_files"


def test_last_stream_disconnect_callback_and_reconnection():
    module = load_module()
    subscribed = threading.Event()
    disconnected = threading.Event()
    server = module.IdeCompanionServer(
        lambda message: None,
        auth_token="token",
        on_subscribe=subscribed.set,
        on_last_disconnect=disconnected.set,
    )
    port = server.start()

    def connect_once():
        with httpx.stream(
            "GET",
            "http://127.0.0.1:{}/mcp".format(port),
            headers={"Authorization": "Bearer token", "Accept": "text/event-stream"},
            timeout=5,
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    return json.loads(line[6:])

    first_result = []
    first = threading.Thread(target=lambda: first_result.append(connect_once()))
    first.start()
    try:
        assert subscribed.wait(2)
        server.notify("ide/contextUpdate", {"sequence": 1})
        first.join(timeout=3)
        assert first_result[0]["params"] == {"sequence": 1}
        assert disconnected.wait(2)

        subscribed.clear()
        second_result = []
        second = threading.Thread(target=lambda: second_result.append(connect_once()))
        second.start()
        assert subscribed.wait(2)
        server.notify("ide/contextUpdate", {"sequence": 2})
        second.join(timeout=3)
        assert second_result[0]["params"] == {"sequence": 2}
    finally:
        server.stop()
