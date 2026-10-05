---
name: feedback-wont-use-omp-again
description: "user has permanently ruled out Oh-My-Pi (omp) for hands-on GUI/dialog-driven work after the 2026-09-27 package-audit meltdown -- don't suggest it for that kind of task"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a393e427-5520-48bb-9c04-b2887aafdba8
  modified: 2026-09-28T08:28:46.114Z
---

Donald has decided he cannot go back to using Oh-My-Pi (omp) for tasks requiring multi-window GUI/dialog management (like driving the package-audit test rig via computer-use). Reason given 2026-09-28: "the pain is indelibly etched in my brain. The time consumption (wastage of tokens)." This follows the meltdown documented in the omp session transcripts from 2026-09-27 (window-identity confusion, false "console is clean" claims, a burned-usage repeating-output loop).

**Why:** Direct, explicit statement of a settled decision, not just a bad-day observation -- this isn't "omp had an off day," it's "I'm done trying this with omp."

**How to apply:** Don't propose omp for GUI/dialog-heavy, verification-critical work (package-install test loops, computer-use-driven dialog handling) going forward. omp may still be fine for other things (feedback_scope_is_ghostshell_bugs_only (note not found) notes it was doing an "impressive job" generally, right up until handed this specific task) -- the ruling-out is scoped to this failure mode, not a blanket verdict on the tool. If asked to compare AI coding tools/subscriptions, this is a data point to surface, not a reason to volunteer unprompted.

**2026-09-28 mitigating discovery:** the "Package Control not installed" fights that dominated the meltdown were not omp being clueless -- the portable test rig's Package Control was genuinely broken (ancient 3.4.1 build crashing on import under Python 3.14 with a regex-flags error in its bundled `semver.py`; fixed by replacing it with the real 4.2.8 release). No amount of UI-level reinstalling could have fixed that; the real fix required recognizing a Python version incompatibility and swapping the `.sublime-package` file directly. So at least part of the frustration was fighting an unfixable-by-omp infrastructure fault, not evidence of omp misunderstanding Package Control fundamentals. Donald's own reaction: "that explains why omp simply appeared to refuse to use Package Control... I was so shocked that I made a loud exclamation about it. But it did not know that that was serious." The window-identity confusion and false "console is clean" claims documented above are separate, real issues that still stand on their own.

Donald's own framing of the causal chain (2026-09-28): "the net effect was to put me in a spin so bad I got disgusted and didn't want to use omp any more." So the ruling-out decision itself is genuinely downstream of a broken test rig compounding with omp's real weaknesses (window confusion, false-clean claims) -- not purely a verdict on omp's capability. Still respect the decision as settled (per the top of this note), but weigh it as "burned by a bad combination," not "omp is incompetent," when judging omp's general capability elsewhere.
