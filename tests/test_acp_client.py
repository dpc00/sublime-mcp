import importlib.util
import json
import queue
import threading
from pathlib import Path

import pytest


MODULE = Path(__file__).parents[1] / "packages" / "st-plugin" / "acp_client.py"


def load_module():
    spec = importlib.util.spec_from_file_location("acp_client", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class QueueReader:
    def __init__(self):
        self.lines = queue.Queue()

    def readline(self):
        return self.lines.get(timeout=2)

    def send(self, message):
        self.lines.put(json.dumps(message) + "\n")

    def close(self):
        self.lines.put("")


class RecordingWriter:
    def __init__(self):
        self.messages = queue.Queue()
        self.closed = False

    def write(self, text):
        self.messages.put(json.loads(text))

    def flush(self):
        pass

    def close(self):
        self.closed = True


def test_request_response_and_streamed_notification():
    module = load_module()
    reader, writer = QueueReader(), RecordingWriter()
    notifications = []
    connection = module.AcpConnection(
        reader, writer, on_notification=lambda method, params: notifications.append((method, params))
    ).start()

    result_box = []
    thread = threading.Thread(
        target=lambda: result_box.append(connection.request("initialize", {"protocolVersion": 1}))
    )
    thread.start()
    request = writer.messages.get(timeout=1)
    assert request["method"] == "initialize"
    reader.send({"jsonrpc": "2.0", "id": request["id"], "result": {"protocolVersion": 1}})
    reader.send({"jsonrpc": "2.0", "method": "session/update", "params": {"sessionId": "s1"}})
    thread.join(timeout=1)
    assert result_box == [{"protocolVersion": 1}]
    assert notifications == [("session/update", {"sessionId": "s1"})]
    reader.close()


def test_agent_permission_request_gets_selected_outcome():
    module = load_module()
    reader, writer = QueueReader(), RecordingWriter()
    connection = module.AcpConnection(
        reader,
        writer,
        on_request=lambda method, params: {
            "outcome": {"outcome": "selected", "optionId": params["options"][0]["optionId"]}
        },
    ).start()
    reader.send({
        "jsonrpc": "2.0", "id": 9, "method": "session/request_permission",
        "params": {"options": [{"optionId": "allow-once"}]},
    })
    response = writer.messages.get(timeout=1)
    assert response == {
        "jsonrpc": "2.0", "id": 9,
        "result": {"outcome": {"outcome": "selected", "optionId": "allow-once"}},
    }
    reader.close()


def test_cancel_is_notification_and_eof_unblocks_pending_request():
    module = load_module()
    reader, writer = QueueReader(), RecordingWriter()
    connection = module.AcpConnection(reader, writer).start()
    connection.notify("session/cancel", {"sessionId": "s1"})
    assert writer.messages.get(timeout=1) == {
        "jsonrpc": "2.0", "method": "session/cancel", "params": {"sessionId": "s1"}
    }

    errors = []
    thread = threading.Thread(
        target=lambda: pytest.raises(module.AcpError, lambda: connection.request("session/new", {}))
    )
    thread.start()
    writer.messages.get(timeout=1)
    reader.close()
    thread.join(timeout=1)
    assert not thread.is_alive()
