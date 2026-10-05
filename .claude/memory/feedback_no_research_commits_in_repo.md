---
name: no-research-commits-in-repo
description: Campaign baton/log/study notes must never be committed to the sublime-mcp repo; they are gitignored scratch files
metadata:
  node_type: memory
  type: feedback
  originSessionId: 20d54abe-2f32-4daf-93ee-a1da9540a1db
  modified: 2026-09-29T16:49:55.673Z
---

Never `git add`/commit `.package_skill_baton.md`, `.package_skill_test_log.md` or campaign study notes in the sublime-mcp repo. On 2026-09-29 Donald objected to "research commits" polluting his repo: my `rec.py` helper had been committing the baton after every package (77+ commits), and the baton was not in `.gitignore` (only the test log and `campaign_tools/` were).

**Why:** the repo is his real project; research notes are working memory, not part of it. He expects `.gitignore` to keep them out.

Donald also said (2026-09-29) these files already go to Google Drive via his backup, so git is never needed as a safety net for them.

**How to apply:** the baton and the buildview study file are now in `.gitignore`; `%TEMP%/rec.py` records log + baton lines only and does not commit. History was purged with git-filter-repo (local; backup bundle `%TEMP%/sublime-mcp-before-filter-2026-09-29.bundle`). Force-push to origin still needs Donald's OK. See [[project_session_baton_2026_09_29]].
