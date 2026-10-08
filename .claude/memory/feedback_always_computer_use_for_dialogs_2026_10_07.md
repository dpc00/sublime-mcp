---
name: always-computer-use-for-dialogs-2026-10-07
description: 2026-10-07 Donald: always use computer-use for clicking dialogs, even after an Escape stop; never switch tools or stop because of it
metadata:
  type: feedback
---

2026-10-07: during the niceDarkTheme Terminus dialog, computer-use was stopped by his Escape key (a mistake on his part). I stopped and offered to use sublime-mcp instead. He said: never choose that; always insist on using computer-use no matter what happens, such as him pressing Escape by mistake.

**Why:** he wants dialogs handled with computer-use; sublime-mcp's dismiss_native_window ignored my button name and clicked Cancel instead of Install.
**How to apply:** after an Escape stop, retry computer-use (get_window_state then click); do not offer or switch to dismiss_native_window and do not wait for him. This supersedes the "use an alternative" advice in [[computer-use-false-escape-stop]].
