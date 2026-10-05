---
name: wslg-window-froze-keyboard
description: "Starting the WSL Sublime through WSLg (a visible msrdc window) froze Donald's laptop keyboard for a long time; never launch WSLg GUI windows while he is at the keyboard, and run the WSL rig headless instead"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 20d54abe-2f32-4daf-93ee-a1da9540a1db
  modified: 2026-09-30T01:01:36.685Z
---

2026-09-29: after I launched the WSL Sublime (WSLg window, titled "[WARN:COPY MODE] ... (Ubuntu)" under msrdc.exe) Donald's laptop keyboard stopped working entirely ("it simply froze keyboard entry"). He tried the phone but messages typed there only queue behind the running turn, so he could not stop me. He was furious: "you should not do what you did that froze the keyboard."

**CORRECTION (Donald, same day):** no Linux window appeared on screen at all; the "[WARN:COPY MODE]" title means WSLg could not display windows until `wsl --shutdown`. So the cause of the frozen keyboard is NOT established (an invisible focused msrdc window is a guess); my kills, the MCP registration and computer-use on msrdc were all unlikely causes. I ignored the COPY MODE warning, which was my error. Fixed by `wsl --shutdown` and the headless X server (see [[reference_wsl_sublime_install]]).

**Why (unproven guess):** a WSLg/msrdc window can grab or wedge keyboard input, and the computer-use permission prompt for that window also hung. Donald cannot interrupt a running turn from the phone, so any action that can take his keyboard is unrecoverable for him.

**How to apply:**
- Do NOT start GUI programs in WSL through WSLg while he may be at the keyboard. Kill leftovers with `pkill -x sublime_text` (exact names, at most 15 chars).
- If the WSL rig is wanted, run it headless: an X server that draws nothing on screen (Xvfb/Xvnc unpacked from a downloaded deb without sudo, `DISPLAY=:99`), never `DISPLAY=:0`. Tell him before starting anything, and prefer times he is away.
- Never use computer-use on msrdc windows (its permission prompt hung).
- Related: [[reference_wsl_sublime_install]], [[feedback_poll_for_dialogs_and_say_what_to_press]].
