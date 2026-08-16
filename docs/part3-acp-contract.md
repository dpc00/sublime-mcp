# Part 3 ACP client contract

Status: transport baseline, 2026-08-16

## Boundary

Part 3 builds one minimal native Sublime ACP client against OpenCode. It does
not generalize to other installed ACP agents. The transport is newline-delimited
JSON-RPC 2.0 over the stdin/stdout of `opencode acp`.

## Required lifecycle

1. Start and own the agent subprocess.
2. Negotiate with `initialize`.
3. Create one workspace session with `session/new`.
4. Send prompts through `session/prompt` and render streamed `session/update`
   notifications.
5. Present `session/request_permission` choices and return the selected outcome.
6. Upsert tool state from `tool_call` and `tool_call_update` events.
7. Cancel active work with the `session/cancel` notification.
8. Close the session when supported and shut down the subprocess gracefully.

## Milestone 1 result

`packages/st-plugin/acp_client.py` implements a Sublime-independent NDJSON
JSON-RPC connection and OpenCode process wrapper. It correlates concurrent
requests, dispatches notifications, answers agent-to-client requests, unblocks
pending calls on EOF, drains stderr, sends cancellation, and owns graceful then
forced process shutdown. Three mock-agent tests pass.

A live read-only probe against installed OpenCode 1.18.18 negotiated protocol
version 1 and created a real session. OpenCode advertised session
load/close/fork/list/resume, MCP HTTP/SSE, embedded-context and image prompt
capabilities, and returned model, effort, and build/plan configuration options.

## Milestone 2 result

`tools/acp_smoke.py` provides a bounded lifecycle probe whose permission policy
always cancels agent requests. OpenCode's default `opencode-go/glm-5.2` model
rejected inference for insufficient account balance; this was a provider error,
not a transport failure. The client then used standard
`session/set_config_option` to select the session-advertised free
`opencode/mimo-v2.5-free` model.

The non-mutating prompt completed with `stopReason: end_turn`. The client
received streamed `available_commands_update`, `agent_thought_chunk`,
`agent_message_chunk`, and `usage_update` notifications. No tool or permission
request was issued. Avoid repeating this probe casually: OpenCode reported a
large workspace-context input token count even for the minimal prompt.

Next add the smallest Sublime conversation view, then explicit permission UI,
tool-call upserts, cancellation controls, and session close.
