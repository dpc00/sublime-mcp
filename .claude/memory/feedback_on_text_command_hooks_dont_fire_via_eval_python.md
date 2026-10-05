---
name: feedback_on_text_command_hooks_dont_fire_via_eval_python
description: "sublime_plugin EventListener.on_text_command/on_post_text_command never fire for commands run via eval_python's view.run_command() in this environment -- confirmed systemic, not a package bug"
metadata:
  node_type: memory
  type: project
  originSessionId: 165e315a-efcb-49b3-8b31-7320fbdb0c43
  modified: 2026-10-05T01:55:10.106Z
---

On 2026-09-24, while bug-hunting KeepPastedTextSelected and FixSelectionAfterIndent (both rely on `EventListener.on_text_command`/`on_post_text_command` to react to `paste_and_indent`/`indent`), live testing via `view.run_command(...)` in `eval_python` showed the listeners never firing -- selections stayed unchanged, no traceback, nothing.

(Observed on the user's real Sublime 4200 build on 2026-09-24; not rechecked on other builds.) Confirmed this is **not** a bug in either package: wrote a from-scratch control `EventListener`, manually registered it into `sublime_plugin.all_callbacks['on_text_command']`/`['on_post_text_command']`, and it *also* never fired for either `paste_and_indent` or the very common built-in `indent` command when invoked via `view.run_command()` from eval_python. `on_window_command` hooks DID fire correctly under the same conditions (confirmed separately against OverrideEditSettingsDefaultContents and RememberCommandPaletteInput) -- this is specific to the text-command hook pair, not window-command hooks.

**Why:** without knowing this, a `view.run_command()`-based live test of any `on_text_command`/`on_post_text_command`-based package will look like a total functional failure and risks a false-positive bug report -- exactly what almost happened twice in one session ([[project_gadzillion_package_test_campaign]]).

**How to apply:** for the package audit, do not conclude a package is broken based on `on_text_command`/`on_post_text_command` not firing when triggered via `eval_python`'s `view.run_command()`. If a plugin's core logic lives in those hooks, either (a) find another way to verify it (e.g. call the plugin's own handler function directly with contrived arguments, bypassing the event system), or (b) note the limitation and don't file. `on_window_command` and other event hooks are not affected -- this is specific to the text-command pair. If a future session finds the actual root cause (e.g. a threading/dispatch nuance in how eval_python's exec context differs from a real UI-triggered command), update this note.
