---
name: feedback-diff-review-ux
description: "User cannot read code diffs; accept/reject decisions on /ide diff UI should be based on plain-English risk summary, not raw code"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 397d4b91-17fe-4702-83c6-481dab5c795f
  modified: 2026-08-21T21:24:54.244Z
---

The user cannot meaningfully read code diffs (any language/syntax). When shown Sublime's inline diff tab (Accept/Reject banner over old/new code) built for the `/ide` integration, they could not make an honest accept/reject decision from it — they went back to the chat-prompt Accept instead, out of habit, and admitted that even that is really a gamble based on: whether the change is git-revertible, whether it's additive/new vs. an edit to existing code, and whether it touches something vital vs. isolated.

**Why:** Stated directly (2026-08-21) after testing the inline-diff prototype built the previous session in response to their complaint about `/ide`'s two-tab diff UX. The prototype solved the wrong problem — it made the diff view nicer (single view, colored highlights, banner) but diffs were never the issue; the user's literacy bottleneck is upstream of rendering quality.

**How to apply:** For any future work on the `/ide` inline-diff feature, or any time proposing a code change for the user to approve — lead with a plain-English summary of what changed and why (this is what worked well for the win32.ts screenshot fix explanation), and explicitly call out the risk profile: is this reversible (git), is it new/additive vs. modifying existing behavior, is it isolated or does it touch something live/critical. Do not assume a nicer code diff view is progress on this problem — it isn't, for this user. If continuing the sublime-mcp `/ide` plugin work, the design goal should shift from "render diffs like an IDE" toward "surface a risk/change summary a non-code-reader can act on."

**Hard constraint (2026-08-21):** A diff review must never be larger than one screen of content. Forcing the user to scroll through a large multi-screen file to hunt for what changed is unacceptable — if the change requires scrolling to find, the review step has no informational value for a non-code-reader. Any `/ide` diff rework must crop to the changed region(s) plus minimal context, never dump the whole file.
