---
name: gmail-fetch-marks-read
description: "Fetching a Gmail thread with the connector's get_thread marks it read; Donald wants to see new mail unread himself"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 20d54abe-2f32-4daf-93ee-a1da9540a1db
  modified: 2026-09-29T17:58:26.403Z
---

On 2026-09-29 Donald noticed that mail I had fetched with `get_thread` was already read "before I ever saw it". Fetching (and possibly other reads) through the claude.ai Gmail connector marks the message read.

**Why:** he uses unread state as his own to-do list for maintainer replies; me clearing it hides new items from him.

**How to apply:** prefer `search_threads` (snippet + subject are usually enough); only `get_thread` when the full body is needed, and afterwards put the state back with `label_thread` labelIds ["UNREAD"] on threads that stay in the inbox. Never trash or otherwise touch personal mail (Michelle, lease). Related: [[feedback_good_deeds_ok_and_inbox_deletes]].
