---
name: no-standins-when-real-is-possible-2026-10-10
description: 2026-10-10 Donald: never test with a stand-in (stub/mock) when the real thing can be run; I tested PR #284 with a fake picker and he objected
metadata:
  type: feedback
---

2026-10-10: testing ColorHelper PR #284 I replaced the native color dialog with a sleeping stub "so nothing could freeze Sublime". Donald: "never use a stand-in when clearly you don't need to." The real dialog was safe to run in the portable (the PR runs it off the main thread, and I can close it from outside).

**Why:** a stub only proves my own logic, not that the real feature works; he also found my report confusing ("can't test" when I meant "did not repeat").
**How to apply:** run the real dialog/tool/package whenever it can be run, even if it is slower or needs a dialog dismissed (see [[feedback_dismiss_dialogs_with_computer_use]] and [[native-dialog-tests-from-windows-terminal-2026-10-09]]; the portable avoids moving the Claude session). Use a stand-in only if the real one is impossible, and say plainly that it is a stand-in and why. In reports say "did not run" or "cannot run", never "can't" for something I merely skipped. Related: [[colorhelper-maintainer-reply-2026-10-10]].
