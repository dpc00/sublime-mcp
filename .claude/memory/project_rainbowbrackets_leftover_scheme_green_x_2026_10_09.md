---
name: rainbowbrackets-leftover-scheme-green-x-2026-10-09
description: 2026-10-09: RainbowBrackets test left two color-scheme files in User\Color Schemes; they cause the green x on untitled tabs; deleting them while Sublime runs made error dialogs and a light window; delete only with Sublime closed
metadata:
  type: project
---

**CORRECTION (2026-10-09, later):** the link between these files and the green x was WRONG. Donald had me close Sublime, recycle `Color Schemes\RainbowBrackets` and `color_helper.palettes` while it was closed, and restart. After that the untitled tab still has a green indicator (a green dot now, because Sublime restored the empty untitled tab as modified; the x was green before). So the green is just how his Default Dark theme with the Mariana scheme draws the untitled-tab indicator; a brand-new untitled tab showed it before any cleanup. The grey x I saw while the files were missing came from the fallback light theme, not from the missing files. The leftovers are cleaned up either way. The rest of this note (the error dialogs from deleting scheme files while Sublime runs) stays true.

**What:** the RainbowBrackets test (about 08:41 on 2026-10-09) left `Packages\User\Color Schemes\RainbowBrackets\Mariana.sublime-color-scheme` and `ai_terminal.sublime-color-scheme` (653 bytes each, rainbow bracket scope rules only, one color is green) even though the package was removed. Donald noticed a green x on the untitled tab that he had never seen before. Evidence for the link: with both files recycled the x turned grey; with both restored it is green again. The mechanism is not proven.

**What went wrong:** I recycled the two files while Sublime was running. Sublime still held them, so it raised several "Error loading colour scheme ... Unable to read Packages/User/Color Schemes/RainbowBrackets/..." dialogs (one per reload, for Mariana and for GhostShell's ai_terminal scheme) and the whole window turned light until the files were back. I answered each dialog with `dismiss_native_window` (action ok) and restored both files from the Recycle Bin with the Shell COM "undelete" verb. Everything is back to the earlier look. The two files are currently still there.

**Why:** test packages that generate files in `Packages\User` (color schemes, palettes) can leave them behind after `remove_package`; ColorHelper also left `User\color_helper.palettes` (modified 10:25).

**How to apply:**
- After removing a package, list `Packages\User` files changed since the test started and report leftovers; do not delete them while Sublime is open if Sublime may have loaded them (colour schemes especially).
- To clear these two: close Sublime first, recycle the folder `Packages\User\Color Schemes\RainbowBrackets`, start Sublime. Closing Sublime closes the Claude tab in it, so do it when Claude runs in Windows Terminal or at a planned restart. Needs Donald's word.
- `color_helper.palettes` is a separate small leftover; same rule.
- Never assume a leftover file is unused: check what loaded it before removing ([[feedback-destructive-tests-sandbox-only]] has the Packages junction warning).
