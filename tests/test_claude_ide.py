import importlib.util
import json
import os
import shutil
import uuid
from pathlib import Path

import pytest


MODULE = Path(__file__).parents[1] / "packages" / "st-plugin" / "claude_ide.py"


def load_module():
    spec = importlib.util.spec_from_file_location("claude_ide", MODULE)
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


def test_claude_lock_file_matches_installed_client_contract(workspace_tmp_path):
    module = load_module()
    stale = workspace_tmp_path / "1111.lock"
    stale.write_text('{"pid":123}', encoding="utf-8")
    path = module.create_claude_discovery_file(
        port=4321,
        workspace_paths=[workspace_tmp_path],
        auth_token="secret",
        pid=123,
        directory=workspace_tmp_path,
    )
    assert Path(path).name == "4321.lock"
    assert not stale.exists()
    assert json.loads(Path(path).read_text(encoding="utf-8")) == {
        "workspaceFolders": [str(workspace_tmp_path.resolve())],
        "pid": 123,
        "ideName": "Sublime Text",
        "transport": "sse",
        "runningInWindows": os.name == "nt",
        "authToken": "secret",
    }


def test_claude_dispatch_keeps_agent_specific_tool_shapes():
    module = load_module()
    calls = []

    def record(name):
        def invoke(arguments):
            calls.append((name, arguments))
            return {"content": []}
        return invoke

    listed = module.claude_dispatch(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        record("diagnostics"),
        record("diff"),
        record("close"),
    )
    assert [tool["name"] for tool in listed["result"]["tools"]] == [
        "getDiagnostics", "openDiff", "close_tab"
    ]

    arguments = {
        "old_file_path": "old.py",
        "new_file_path": "new.py",
        "new_file_contents": "value = 2\n",
        "tab_name": "review",
    }
    response = module.claude_dispatch(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "openDiff", "arguments": arguments},
        },
        record("diagnostics"),
        record("diff"),
        record("close"),
    )
    assert response["result"] == {"content": []}
    assert calls == [("diff", arguments)]
