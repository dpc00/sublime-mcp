"""Stdio ACP peer for F9 proof tests. Modes via ACP_PEER_MODE."""
import json
import os
import sys

MODE = os.environ.get("ACP_PEER_MODE", "echo")


def _write(message):
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def main():
    if MODE == "bad_then_request":
        sys.stdout.write("this is not json\n")
        sys.stdout.flush()
        _write({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "session/request_permission",
            "params": {"options": [{"optionId": "allow-once"}]},
        })
        sys.stdin.readline()
        return

    if MODE == "echo":
        for line in sys.stdin:
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in message and "method" in message:
                _write({"jsonrpc": "2.0", "id": message["id"], "result": {"ok": True}})
        return

    if MODE == "hold":
        # Ignore stdin close; stay alive so a parent that doesn't join/kill hangs.
        import time
        time.sleep(30)
        return


if __name__ == "__main__":
    main()
