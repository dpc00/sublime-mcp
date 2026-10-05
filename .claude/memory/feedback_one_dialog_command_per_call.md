---
name: one-dialog-command-per-call
description: "never loop a command that can call error_message; run one per call and check list_apps at once, or piled-up modal dialogs land on Donald's screen"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a3788352-49e6-4a4a-bacb-4c22de216ce3
  modified: 2026-09-26T02:51:51.569Z
---

When testing a package command that can call `sublime.error_message`/`message_dialog` (formatters, node bridges, converters), run ONE invocation per tool call and call `list_apps` in the same step. Do not put several runs (different inputs/settings) into one eval loop.

**Why:** 2026-09-26 Autoprefixer: I ran 8 commands in two loops, each raised a modal dialog ("caniuse-lite is outdated"), so 5+ native windows stacked up on Donald's screen and he had to message "Dialog" (third time that day, after Templ and clean-css). Each dialog blocks the plugin host and the results of my own loop were silently wrong (unchanged buffers).

**How to apply:** first run the package's underlying script directly (node/python in a shell) to see stderr/exit code; only then, if needed, one in-ST run; when outputs stay unchanged suspect a dialog first. Also wait until find_resources lists a freshly created test syntax before assigning it (else an "Unable to stat" dialog). Related: [[feedback-dismiss-dialogs-with-computer-use]], [[feedback-computer-use-mcp-prompts-not-visible-remote]].
