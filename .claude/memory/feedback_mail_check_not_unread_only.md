---
name: mail-check-not-unread-only
description: "2026-10-06: the half-hour mail check must list mail that still needs an answer, not just unread mail; Gmail tools can be missing from a session and that must be said first"
metadata:
  type: feedback
---

On 2026-10-06 I ran the half-hour check without any Gmail tool and mentioned it in a trailing clause; Donald objected ("you don't panic?"). After he installed a plugin the built-in Gmail connector (`mcp__claude_ai_Gmail__*`) appeared. I then reported "no unread mail" and he said "of course I read my emails, that does not mean anything".

**Why:** he opens mail without answering it; unread is not the same as handled. Missing Gmail means the check is blind on mail.

**How to apply:** if no Gmail tool is loaded, say that first in the check ("mail not checked") and look for it (ToolSearch "gmail", then tell him it needs reconnecting). When checking, search the inbox for the last few days (`in:inbox newer_than:3d`, snippets only, never get_thread) and surface threads where the last message is not from him and an answer is plausible, e.g. the 2026-10-05 eugenesvk request on st3-binaryplist#12. See [[feedback_gmail_fetch_marks_read]].
