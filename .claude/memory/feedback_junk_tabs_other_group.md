---
name: junk-tabs-other-group
description: "any tab I open in ST (test views, Find Results, PC messages) goes in a different group so the Claude tab stays visible and focused; never leave it covered"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a3788352-49e6-4a4a-bacb-4c22de216ce3
  modified: 2026-09-25T16:38:51.798Z
---

When I open a view in Sublime (Find Results, Package Control Messages, throwaway test buffers, files I open to exercise a package), it must NOT land in the group holding the Claude tab (tab 1) and must not take focus from it.

**Why:** 2026-09-25 Donald: when a new tab takes focus, it covers my tab, so he cannot see permission prompts there. From his phone the computer-use-mcp permission prompt is not transmitted at all, and it only fires when I actually call computer-use. He waits ~30 s, then checks tab 1, and that disrupts the computer-use call. See [[feedback-computer-use-mcp-prompts-not-visible-remote]].

**How to apply:**
- Before opening anything, make sure a second group exists (`window.set_layout` with 2 columns if needed) and keep the Claude tab's group focused.
- Move any view I create or that a package opens (installs open a "Package Control Messages" tab, Find in Files opens "Find Results") into the other group with `window.set_view_index(view, 1, 0)`, then restore focus with `window.focus_group(<claude group>)` / `focus_view(claude_view)`.
- Prefer hidden output panels for throwaway tests (worked well this session); only use a real tab when the feature needs one.
- Do not switch focus to the second group to call computer-use until Donald has acked any pending permission prompt in tab 1; then switch, call, and return focus to tab 1.
- Close my own junk tabs by exact id/name (see [[feedback-never-close-or-retarget-windows-by-exclusion]]).
