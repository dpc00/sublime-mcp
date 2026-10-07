---
name: trust-his-word-on-replies-2026-10-06
description: "2026-10-06: when Donald says he already replied (GitHub or email) or that a comment needs no reply, believe him; kaste_ledger.py cannot see email replies and wrongly shows NOT ANSWERED"
metadata:
  type: feedback
---

On 2026-10-06 I kept reporting two threads as unanswered or needing a reply (Jawuilp/Limitcode#9 and kaste's 2026-10-05 comment on sublimehq/package_control_channel#9554), drafted a reply for kaste and offered a release, after Donald had said "i already answer his question, both on github and in email", "it does not call for a reply, and i already replied" and "kaste's comment is fine". He had to repeat it three times and ended with "what more must I say?".

**Why:** `tools/gh_status/kaste_ledger.py` only sees what is posted on GitHub; his replies by email (not published, or published later) show as NOT ANSWERED. A tool's "not answered" is weaker evidence than his statement. The half-hour check's only job here is to surface items that need a decision.

**How to apply:** once he says a thread is answered or needs nothing, mark it done in my head and in the check; do not re-surface it, do not offer drafts or releases for it. The 2026-10-05 review comment by kaste on #9554 is closed from my side (Origin/Host check and README change are committed, unreleased; a no-server-without-auth_token change was NOT decided and he finds a password requirement for a Sublime package unreasonable, see [[feedback_dont_hand_technical_decisions_to_donald]]). Also explain jargon plainly when he asks ("auth_token" meant an optional secret setting), see [[feedback_plain_short_answers_no_menus]]. Related: [[feedback_complete_maintainer_reply_sweep]] (that note's ledger advice still holds for finding replies, not for deciding whether he answered).
