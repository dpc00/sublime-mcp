---
name: monitor-maintainer-replies-via-github
description: "Donald trashed the GitHub notification mails on 2026-09-29 and relies on me to watch maintainer replies; check GitHub with gh, not his inbox"
metadata:
  node_type: memory
  type: project
  originSessionId: 20d54abe-2f32-4daf-93ee-a1da9540a1db
  modified: 2026-09-29T18:32:44.532Z
---

Donald finds the GitHub notification volume too high (kaste answers within minutes and every PR generates several mails). On 2026-09-29 he trashed all of it and said he is "relying on" me to watch for replies and act. He also invited me to look through the Trash.

**Why:** unread mail is his to-do list, but the traffic overwhelmed it; and reading threads through the Gmail connector marks them read (see [[feedback_gmail_fetch_marks_read]]).

**How to apply:** at the start of each work stretch, check GitHub directly with `gh` (no read/unread side effects): `gh pr view <n> -R <repo> --json state,comments,reviews` and `gh issue view <n> --json comments` for my open PRs/issues. Open as of 2026-09-29: SublimeLinter-php#58, SublimeLinter-pylint#69, SublimeLinter-json#24 and #25, SublimeLinter#1999 (rework of the #1998 fix); issues xmllint#14 (offered a byte->char PR), json#23. Merged so far: flake8#132, jshint#126, csslint#27, php#57. Use Gmail search only for non-GitHub mail, and never touch his personal threads (Michelle, the Thistle lease). Summarise to him only what needs a decision or is a nice outcome (merged, praise). See [[project_package_audit_baton]].
