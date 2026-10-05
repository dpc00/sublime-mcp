---
name: permission-prompt-plain-english
description: "Permission prompts must show a plain-English \"I have written a little script to ...\" description, with the code kept out of sight in a script file, because Donald cannot read code"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 20d54abe-2f32-4daf-93ee-a1da9540a1db
  modified: 2026-09-30T00:04:04.915Z
---

Every command that will raise a permission prompt gets a description that starts "I have written a little script to ..." followed by what it does and whether it only reads or changes something. Keep the code itself out of the prompt: write the script to a file in the scratchpad directory (no prompt) and run it with a short command such as `python <scratchpad>\name.py`.

**Why:** 2026-09-29: Donald rejected a prompt that showed a block of Python: "humans cannot read that garbage. You need to put 'I have written a little script to ...' and nothing else." He already cannot read diffs ([[feedback_diff_review_ux]]) and was overwhelmed by prompts ([[feedback_poll_for_dialogs_and_say_what_to_press]]).

**How to apply:** scripts go in the scratchpad dir, one short command per prompt, description in plain English saying read-only vs. changes. No inline heredocs or long one-liners in the command.

**Repeated 2026-10-03:** Donald again: "I really wish you had the common sense to never put a confusing tool call up in my conversation." I had been pasting inline python heredocs, long one-line commands and `eval_python` code strings all session. Rule, no exceptions: every script goes into a file in the scratchpad first; the tool call is then one short command (`python file.py`, or exec of that file) with a plain description. No inline code, no long pipelines, no heredocs in the visible call.
