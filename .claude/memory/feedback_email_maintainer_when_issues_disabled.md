---
name: email-maintainer-when-issues-disabled
description: When a package's GitHub issues are disabled or the repo is archived, SEND the finding by email to the maintainer's commit address (no drafts); noreply addresses cannot be emailed
metadata:
  type: feedback
---

2026-10-06 Donald: "if issues are disabled you should try to send an email", then "try to remind yourself of all the prior ones that you didn't craft emails for", then "don't make drafts, just send them."

**Why:** findings in repos with issues off or archived otherwise reach nobody. He explicitly approved sending (this overrides the old "no emails without his approval" note of 2026-09-26 in the audit log).

**How to apply:** find a real address from `gh api repos/<r>/commits?per_page=30` (author email, skip `users.noreply.github.com`; repos with only noreply addresses cannot be emailed). Write it in the accepted form from [[feedback_no_first_person_claims_in_users_emails]]: first words `Claude reports:`, impersonal, no greeting/thanks/signature/offers, say the repo has issues disabled or is archived, package + file:line + repro + cause, and say plainly whether it was found by reading the source or by running it. Verify the defect against current master first (a shallow clone and ruff), and never state numbers I did not count. Send with `send_message`; log it in the audit log.

Sent 2026-10-06 (19 emails): PKGBUILD (Donald sent his own draft), print-to-html, GoTools, UbuntuPaste, pawn-openmp kit, lightpaper, SideBarMenuAdvanced, ADBView, Atomizr, MarkLogic-Sublime, Sublimall, sublime-php-connector, sublime-dreams, sublime-phpunit, SublimeCache, BeautifyLatex, CPParser, SearchInProject, BinViewer, strings-resource-file. Skipped: STexercism (no real address), sublime-dblp (fixed in master), LOVELY2D (dead branch, not a bug), coreboot syntax (Gerrit mirror), Pieces (company repo), Emoji Code and GoToFullyQualifiedClass (repo not identified).
