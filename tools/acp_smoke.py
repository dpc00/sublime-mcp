"""Read-only OpenCode ACP lifecycle smoke test."""

import argparse
import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "packages", "st-plugin"))

from acp_client import AcpProcessClient  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("agent")
    parser.add_argument("--cwd", default=ROOT)
    parser.add_argument("--prompt")
    parser.add_argument("--model")
    args = parser.parse_args()
    updates = []

    def on_notification(method, params):
        if method == "session/update":
            update = params.get("update") or {}
            updates.append({
                "type": update.get("sessionUpdate"),
                "status": update.get("status"),
                "kind": update.get("kind"),
            })

    def on_request(method, _params):
        if method == "session/request_permission":
            return {"outcome": {"outcome": "cancelled"}}
        raise RuntimeError("Unsupported agent request: " + method)

    client = AcpProcessClient(
        [args.agent, "acp", "--pure"],
        os.path.abspath(args.cwd),
        on_notification=on_notification,
        on_request=on_request,
    ).start()
    try:
        initialized = client.initialize()
        session = client.new_session()
        if args.model:
            client.set_config_option(session["sessionId"], "model", args.model)
        result = None
        if args.prompt:
            result = client.prompt(session["sessionId"], args.prompt)
        print(json.dumps({
            "protocolVersion": initialized.get("protocolVersion"),
            "agentInfo": initialized.get("agentInfo"),
            "agentCapabilities": initialized.get("agentCapabilities"),
            "sessionId": session.get("sessionId"),
            "configOptionIds": [item.get("id") for item in session.get("configOptions", [])],
            "promptResult": result,
            "updates": updates,
        }, indent=2))
    finally:
        client.stop()


if __name__ == "__main__":
    main()
