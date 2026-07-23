# Visible Terminal Skill

Run shell commands in a visible Sublime Text terminal tab instead of an invisible
subprocess. The user sees every command and its output in real-time — a full audit
trail in a scrollable ST tab.

## When to Use This

When sublime-mcp is available (ST is running, MCP server is connected), prefer this
over the native Bash tool for shell commands. Fall back to the native Bash tool only
when sublime-mcp is unavailable.

## The Tools

All existing typed sublime-mcp tools — no `run_command` escape hatch:

- **`eval_python`** — runs Python in ST's main thread. Used to find/open a terminal
  tab and send a command string to its PTY.
- **`get_view_size`** — returns the character count of a view. Used to record the
  buffer position before sending the command.
- **`get_view_chars`** — reads a range of characters from a view by offset. Used to
  read only the new output after the command runs.

## Step 1: Open a Bash Terminal (skip if one is already open)

```
eval_python(code="""
import importlib
mod = importlib.import_module('User.ai.ai_terminal')
w = sublime.active_window()
mod._spawn(w, w.folders()[0] if w.folders() else None, profile='Bash')
""")
```

Wait ~1 second for the shell to start.

## Step 2: Record Buffer Size

```
get_view_size(name="Bash")
```
Note the returned size — call it `N`. This is where new output will start.

## Step 3: Send the Command (with exit-code sentinel)

```
eval_python(code="""
w = sublime.active_window()
w.run_command("ai_terminal_send_string_window", {"string": "git status; echo \\"EXIT_CODE:$?\\"\\n"})
""")
```

The `echo "EXIT_CODE:$?"` suffix captures the exit code of the command.
The `ai_terminal_send_string_window` command finds the terminal tab automatically
and sends the string to its PTY — no need to focus the tab first.

## Step 4: Poll for Output

```
get_view_chars(begin=N, end=<current_size>, name="Bash")
```

Repeat with short sleeps (0.5s) until the returned text contains `EXIT_CODE:`
followed by a number. Use `get_view_size` to get the current end position each time.

## Step 5: Parse the Result

- **Output**: the text between the echoed command line and the `EXIT_CODE:N` line.
  Strip the first line (the echoed command) and the last line (the sentinel).
- **Exit code**: the number after `EXIT_CODE:`. `0` = success, non-zero = failure.
- **Timeout**: if `EXIT_CODE:` does not appear within 30 seconds, the command is
  still running or hung. Read whatever output is available and report a timeout.

## Worked Example: `git status`

```
# Step 1: Record buffer size
get_view_size(name="Bash")  → {"size": 4521, "name": "Bash"}

# Step 2: Send command
eval_python(code="w = sublime.active_window(); w.run_command('ai_terminal_send_string_window', {'string': 'git status; echo \"EXIT_CODE:$?\"\\n'})")

# Step 3: Poll (repeat until EXIT_CODE found)
get_view_chars(begin=4521, end=4689, name="Bash")
→ {"text": "git status; echo \"EXIT_CODE:$?\"\nOn branch main\nnothing to commit, working tree clean\nEXIT_CODE:0\n$ "}

# Step 4: Parse
# Output: "On branch main\nnothing to commit, working tree clean"
# Exit code: 0 (success)
```

## Worked Example: Failing Command

```
# Send: false; echo "EXIT_CODE:$?"
# Output text: "false; echo \"EXIT_CODE:$?\"\nEXIT_CODE:1\n$ "
# Exit code: 1 (failure)
# Command output: (empty — false produces no output)
```

## Edge Cases

- **Long-running commands**: Increase the poll timeout. The sentinel appears
  only after the command finishes. Keep polling; the user can watch progress in
  the terminal tab.
- **Multiline output**: The sentinel still works — it appears on the last line
  after all output.
- **No output**: Commands like `true` produce no output. The sentinel line
  still appears, giving you the exit code.
- **Multiple commands**: Send multiple commands to the same tab. Each one
  appends to the scrollback. Always record `get_view_size` before each new
  command to know where the new output starts.
- **No terminal tab found**: If `ai_terminal_send_string_window` returns
  `{"error": "no live terminal found"}`, open one first (Step 1).

## Exit Code Contract

| Sentinel | Meaning |
|---|---|
| `EXIT_CODE:0` | Success |
| `EXIT_CODE:N` (N>0) | Failure, exit code N |
| Not found within timeout | Command still running or hung |