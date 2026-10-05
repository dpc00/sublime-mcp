---
name: no-first-person-claims-in-users-emails
description: "Reports emailed to maintainers in Donald's name: start with \"Claude reports:\", no greeting/thanks/signature, no I/you/we claims; he sent the Jq one on 2026-10-01 in this form"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-02T00:37:23.676Z
---

Emails written in Donald's name must not claim experiences or intentions that are not his ("I use your package", "I found two bugs", "I am writing to", "I am willing to ..."). He called such statements "LIES" (2026-10-01, Jq maintainer email). He also said a report is a finding, not a request to be considered for communication.

**Final accepted form (he sent it himself, 2026-10-01):**
- First words: `Claude reports:`
- No "Hello <name>", no "Thank you", no signature, no offers ("if issues are preferred, say so"; there was no way to file one anyway).
- Impersonal findings: package + version + environment, then numbered bugs with repro, cause, expected behaviour.
- The one first-person line he dictated himself: `I do not have GitLab access.` (true for him). Do not invent other "I" lines.

**How to apply:**
- Put the draft straight into his Gmail drafts (create_draft; update_draft to change it) AND show the full text in chat. A draft sends nothing, so do not wait for permission to create it. Sending needs his explicit yes (he sent this one himself).
- Gmail does not refresh an already open compose window: tell him to close any open copy and reopen from Drafts; if it still looks stale, a screenshot (with his OK) shows what he sees (it was an old compose box).
- GitHub issues I file under his account also say "I ran / I did not test"; he has not objected, and I told him so.
- Related: [[feedback_plain_short_answers_no_menus]], [[feedback_report_bugs_never_patch_authors_code]].
