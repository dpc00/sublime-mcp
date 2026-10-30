"""Ask the person before an agent does something destructive.

computer-use-mcp asks its user through the MCP protocol itself (elicitation), so Claude Code
draws the prompt in the terminal whatever the client's allow list says. This does the same for
sublime-mcp. On a 2026-07-28 connection a destructive tools/call is answered with
resultType "input_required" and an elicitation/create question; the client repeats the call with
the answer, and the action runs only on "accept". A client that cannot be asked, an answer that is
not "accept", a stale or reused token, or a changed call all mean "denied, nothing was changed".

The pending question is kept here, not in the token: the token is a random key into this table,
valid once, for the exact same tool and arguments, for a few minutes. A client cannot make one up.

This module must not import sublime — ST loads every .py in the package.
"""

import hashlib
import json
import secrets
import threading
import time

REQUEST_KEY = "consent"

# Whole tools that destroy or run arbitrary things whatever their arguments.
DESTRUCTIVE_TOOLS = frozenset({
    "delete_file", "delete_folder", "revert_file", "revert",
    "close_window", "close_workspace", "remove_folder",
    "exit", "eval_python",
})

# Sublime commands that run_command must not run unasked.
DESTRUCTIVE_COMMANDS = frozenset({
    "delete_file", "delete_folder", "revert",
    "close_window", "close_workspace", "remove_folder", "exit",
})


# The person approves eval_python by reading its code, so the prompt carries all of it. Code too
# long to read is refused rather than shown cut off (an approval of unseen lines is no approval).
EVAL_REVIEW_LIMIT = 6000
EVAL_TOO_LONG = "code is too long to review in a prompt ({} characters, limit {}); send it in smaller pieces"


def _short(value, limit=200):
    try:
        text = json.dumps(value, sort_keys=True, default=str)
    except Exception:
        text = str(value)
    return text if len(text) <= limit else text[:limit] + "..."


def _log_text(items, limit=160):
    text = "; ".join(" ".join(item.split()) for item in items)
    return text if len(text) <= limit else text[:limit] + "..."


def eval_codes(name, args, _depth=0):
    """The Python code of every eval_python call a tools/call would run (also inside a batch)."""
    if not isinstance(args, dict):
        args = {}
    if name == "batch" and _depth == 0:
        codes = []
        for call in args.get("calls") if isinstance(args.get("calls"), list) else []:
            if isinstance(call, dict):
                codes.extend(eval_codes(call.get("tool"), call.get("args") or {}, 1))
        return codes
    return [str(args.get("code", "")).strip()] if name == "eval_python" else []


def destructive_items(name, args, _depth=0, prompt=False):
    """One line per destructive action a tools/call would run; empty when it is safe.

    A batch is read call by call, so one destructive call makes the whole batch ask once,
    before any call of it runs. With prompt=True an eval_python item is the short text for the
    question: the whole code is in the panel the gate opens, because a client such as Claude Code
    folds a long prompt to about three short lines."""
    if not isinstance(args, dict):
        args = {}
    items = []
    if name == "batch" and _depth == 0:
        calls = args.get("calls")
        if isinstance(calls, list):
            for call in calls:
                if isinstance(call, dict):
                    items.extend(destructive_items(call.get("tool"), call.get("args") or {}, 1, prompt))
        return items
    if name == "eval_python":
        code = str(args.get("code", "")).strip()
        if len(code) > EVAL_REVIEW_LIMIT:
            items.append("eval_python: " + EVAL_TOO_LONG.format(len(code), EVAL_REVIEW_LIMIT))
        elif prompt:
            first = (code.splitlines() or [""])[0][:60]
            items.append("eval_python: runs Python code ({} lines). READ ALL OF IT in the panel at the "
                         "bottom of Sublime before accepting. It starts: {}".format(len(code.splitlines()), first))
        else:
            items.append("eval_python: runs this Python code in the editor (one line, \\n is a line break): "
                         + json.dumps(code, ensure_ascii=False))
    elif name == "close_file":
        if args.get("discard"):
            items.append("close_file with discard: unsaved edits are thrown away: " + _short(
                {k: args[k] for k in ("path", "name", "index") if k in args}))
    elif name == "run_command":
        command = args.get("command")
        if command in DESTRUCTIVE_COMMANDS:
            items.append("run_command {}: {}".format(command, _short(args.get("args") or {})))
    elif name in DESTRUCTIVE_TOOLS:
        items.append("{}: {}".format(name, _short(args)))
    return items


def client_can_elicit(meta):
    """True when the request's _meta says the client can show a form question."""
    if not isinstance(meta, dict):
        return False
    return caps_can_elicit(meta.get("io.modelcontextprotocol/clientCapabilities"))


def caps_can_elicit(caps):
    """True when these client capabilities (initialize, or a request's _meta) allow a form question."""
    elicitation = caps.get("elicitation") if isinstance(caps, dict) else None
    return isinstance(elicitation, dict) and ("form" in elicitation or not elicitation)


def _fingerprint(name, args):
    raw = json.dumps({"name": name, "arguments": args}, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _denied(items, why):
    text = ("Denied, nothing was changed: {}. Do not retry the same action; ask the person. "
            "Actions held back: {}".format(why, "; ".join(items)))
    return {"content": [{"type": "text", "text": text}], "isError": True}


class ConsentGate:
    def __init__(self, ttl=300, max_pending=100, clock=time.time, log=None, show_code=None):
        self._ttl = ttl
        self._max = max_pending
        self._clock = clock
        self._log = log or (lambda text: None)
        # show_code(codes) puts the whole eval_python code where the person can read it while the
        # question is open and returns True when it did; show_code(None) takes it away again.
        self._show_code = show_code
        self._pending = {}
        self._lock = threading.Lock()

    def _clear_code(self):
        if self._show_code:
            try:
                self._show_code(None)
            except Exception:
                pass

    def _take(self, token):
        with self._lock:
            entry = self._pending.pop(token, None)
        if entry and entry[1] >= self._clock():
            return entry[0]
        return None

    def _put(self, fingerprint):
        token = secrets.token_urlsafe(24)
        now = self._clock()
        with self._lock:
            for key in [k for k, v in self._pending.items() if v[1] < now]:
                del self._pending[key]
            while len(self._pending) >= self._max:
                self._pending.pop(next(iter(self._pending)))
            self._pending[token] = (fingerprint, now + self._ttl)
        return token

    def _question(self, name, args, items):
        """The text of the approval question; eval_python code goes to the code panel first."""
        codes = eval_codes(name, args)
        shown = False
        if codes and self._show_code:
            try:
                shown = bool(self._show_code(codes))
            except Exception as error:
                self._log("consent: could not show the code panel: {}".format(error))
        if shown:
            items = destructive_items(name, args, prompt=True)
        return "sublime-mcp wants to do this in Sublime Text. Accept to allow it:\n- " + "\n- ".join(items)

    def check_legacy(self, name, args, ask):
        """check() for a 2025-11-25 connection, where the client cannot repeat the call with an
        answer: ask(message) sends elicitation/create to the client, waits, and returns the
        person's action ("accept", "decline", "cancel") or None when no answer came."""
        items = destructive_items(name, args)
        if not items:
            return None
        if any(EVAL_TOO_LONG.split("{}")[0] in item for item in items):
            self._log("consent: denied, code too long to review: " + _short(items[0], 120))
            return _denied(items, "code too long to show the person")
        self._log("consent: asking: " + _log_text(items))
        try:
            action = ask(self._question(name, args, items))
        except Exception as error:
            self._log("consent: the question failed: {}".format(error))
            action = None
        finally:
            self._clear_code()
        if action == "accept":
            self._log("consent: approved: " + _log_text(items))
            return None
        if action is None:
            self._log("consent: no answer: " + _log_text(items))
            return _denied(items, "the client gave no answer to the approval question")
        self._log("consent: {} ({}): {}".format(
            "declined" if action == "decline" else "not approved", action, _log_text(items)))
        return _denied(items, "the person did not approve")

    def check(self, name, args, params, can_ask):
        """None when the call may run; otherwise the tools/call result to send instead."""
        items = destructive_items(name, args)
        if not items:
            return None
        if any(EVAL_TOO_LONG.split("{}")[0] in item for item in items):
            self._log("consent: denied, code too long to review: " + _short(items[0], 120))
            return _denied(items, "code too long to show the person")
        fingerprint = _fingerprint(name, args)
        state = params.get("requestState") if isinstance(params, dict) else None
        answers = params.get("inputResponses") if isinstance(params, dict) else None
        if isinstance(state, str) and isinstance(answers, dict):
            if self._take(state) == fingerprint:
                self._clear_code()
                answer = answers.get(REQUEST_KEY)
                action = answer.get("action") if isinstance(answer, dict) else None
                if action == "accept":
                    self._log("consent: approved: " + _log_text(items))
                    return None
                self._log("consent: {} ({}): {}".format(
                    "declined" if action == "decline" else "not approved", action, _log_text(items)))
                return _denied(items, "the person did not approve")
        if not can_ask:
            self._log("consent: denied, the client cannot be asked: " + _log_text(items))
            return _denied(items, "this client cannot be asked for approval (no elicitation support)")
        token = self._put(fingerprint)
        self._log("consent: asking: " + _log_text(items))
        message = self._question(name, args, items)
        return {
            "resultType": "input_required",
            "inputRequests": {REQUEST_KEY: {"method": "elicitation/create", "params": {
                "mode": "form", "message": message,
                "requestedSchema": {"type": "object", "properties": {}}}}},
            "requestState": token,
        }
