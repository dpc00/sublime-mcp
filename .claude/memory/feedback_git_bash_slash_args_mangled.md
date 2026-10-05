---
name: git-bash-slash-args-mangled
description: "In Git Bash, a gh/CLI argument starting with \"/\" (e.g. \"/review\") is rewritten to \"C:/Program Files/Git/...\" — use MSYS_NO_PATHCONV=1 or a body file; and fix own mistakes without asking"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 80ae38f1-7ab9-4aa3-be87-7693e48d1b6b
  modified: 2026-09-26T16:01:03.901Z
---

On 2026-09-26 `gh pr comment 9554 --body "/review"` posted `C:/Program Files/Git/review` on the public Package Control channel PR (bot still ran). Fixed by editing the comment via `MSYS_NO_PATHCONV=1 gh api -X PATCH .../issues/comments/<id> -F body=@file`.

**Why:** Git Bash converts leading-slash args to Windows paths. Donald also said plainly: correcting my own mistake needs no permission — just fix it and say so (don't ask "edit, delete or leave?").

**How to apply:** for any `gh`/CLI text argument starting with `/`, set `MSYS_NO_PATHCONV=1` or pass the text from a file with the Write tool; read the posted text back afterwards. When I notice I mangled something public, correct it immediately and report. Related: [[feedback_bash_tool_backslashes_and_gh]].
