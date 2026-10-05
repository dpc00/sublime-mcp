---
name: feedback_computer_use_mcp_prompts_not_visible_remote
description: "computer-use-mcp's permission prompts render on the local desktop screen, not reachable from Donald's phone/remote session"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 165e315a-efcb-49b3-8b31-7320fbdb0c43
  modified: 2026-09-24T21:59:52.801Z
---

On 2026-09-24 Donald noted: computer-use-mcp pops up its own OS-level permission prompts on the machine's physical display. When he's connected remotely (phone), those prompts don't appear on the phone at all -- they're stuck on the desktop screen, unreachable, exactly when remote control is the reason he's not at the desktop to click them.

**Why:** using computer-use-mcp tools while Donald is on a remote/phone session can silently block forever on a prompt he can never see or answer -- worse than a normal permission wait, because there's no visible signal on his end that anything is waiting.

**How to apply:** Donald corrected me (2026-09-24): browser automation is NOT a substitute for computer-use-mcp -- it only covers browser tasks, and computer-use-mcp is often the only way to control a native app at all. Don't suggest swapping tools as the fix. Instead: when a computer-use-mcp call seems to hang in a session that might be remote/phone-driven, consider that an invisible local OS permission prompt is the likely cause (same family as [[feedback_sublime_mcp_batch_permission_hang]]) and say so plainly rather than retrying blindly or assuming the tool failed.
