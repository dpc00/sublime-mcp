---
name: dismiss-dialogs-with-computer-use
description: "native ST error dialogs I trigger can be dismissed myself via computer-use-mcp; don't just ask Donald to click them"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1e07794b-efe6-4e5f-bbc3-7d3161a16a46
  modified: 2026-10-05T01:54:16.495Z
---

When a test I run pops a native Sublime dialog (e.g. RemoteSync's ssh error modal, KSP "syntax not found"), dismiss it myself with computer-use-mcp (list_apps -> get_window_state -> click/press_key) instead of asking Donald to close it.

**Why:** Donald said so on 2026-09-25 after a RemoteSync test left an ssh error dialog up; eval_python/sublime-mcp can't see or dismiss native dialogs.

**How to apply:** after any package test that could raise a modal (network/host errors, missing syntax/theme), check list_apps/get_window_state for a dialog row and dismiss it. Still avoid triggering modals where possible (use no-network paths). See [[feedback-computer-use-mcp-prompts-not-visible-remote]] for the caveat that its OS permission prompts can be invisible remotely.

**Update 2026-09-25 (worse incident):** after installing a syntax package (YamlPipelines) four modal "Error loading syntax file" dialogs sat for ~5 min because I never looked; Donald had to tell me twice. Check `list_apps` for extra Sublime windows after EVERY package install/uninstall (not only when a test could error), read the dialog text via `get_window_state` (it is a real finding, e.g. a missing base syntax), then click OK. If the tool answers "could not determine the foreground app", don't work around it - tell Donald immediately.

**Update 2026-09-25 (more stray UI after installs):** (1) packages that ship `messages.json` (e.g. MarkerStack) open a "Package Control Messages" view in DONALD's window, not my throwaway one; after every install, list `window.views()` of his window and close only that exact view (verify not dirty, no file, content matches). (2) Deleting a `Packages\X` copy while ST has X loaded can raise a modal "Settings must be a json object"; uninstall/unload first, then delete. (3) As of 2026-09-25 `get_console` default mode used OS-level UI automation and returned ~240 KB, so `mode='captured'` was the workaround. That advice is out of date: `captured` only hooks the Python 3.8 host and misses output from 3.3-host plugins (see [[reference_console_tee_log_4200]]), and the visible capture was rewritten with safety checks and committed in b4fe787 on 2026-10-04.
