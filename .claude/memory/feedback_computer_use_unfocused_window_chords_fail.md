---
name: feedback-computer-use-unfocused-window-chords-fail
description: "computer-use modifier-key chords and clicks fail (no_viable_candidate) on a window that never had real OS focus, even with the tool's foreground fallback; bare nav keys work fine in the background; type_text can triple its input"
metadata:
  node_type: memory
  type: feedback
  originSessionId: abbc045e-cea5-4731-ad7e-d010d8ceedc0
  modified: 2026-10-05T01:54:18.894Z
---

On a window that was spawned in the background and never actually had real Windows focus (e.g. a portable Sublime Text instance launched via `Start-Process`), `computer-use`'s `press_key` with modifier chords (`Ctrl+Shift+P`, `Alt+T`) and `click` both fail with `no_viable_candidate` / `rejected`, even though the tool claims to attempt a session-authorized foreground fallback. This held across many distinct attempts (raw chord, alt-menu chord, click-then-chord, title-bar-click-then-chord) -- not a one-off flake.

Bare, unmodified keys (`Home`, `Right`, `Delete`, single letters) DO work reliably in the background regardless, confirmed via `view.sel()` state changes.

Separately, `type_text` unreliably tripled its input on this same window/app combo (typing "Expand Swap Word" once produced it three times concatenated in the target field) -- a tool quirk, not anything about the target app.

**Why:** Found 2026-09-28 while trying to live-test a Sublime Text package's Command Palette-driven feature (`aafulei/sublime-expand-and-edit`, queue #642 in [[project_package_audit_baton]]). Wasted several turns retrying modifier chords/clicks before realizing the fix was external (Donald manually clicking the target window once).

**2026-10-05 observation:** with the portable 4200 window brought to the front first, `press_key` with bare keys (`Down`, `Return`) was accepted, but a coordinate `click` on a quick-panel row and the keys did not change the quick panel's selection (the keys went to the editor behind it). Posted `Return` through Win32 `PostMessage` also went to the editor. So a quick panel could be seen and read in a screenshot but not driven through these routes in that test.

**How to apply:** If a `computer-use` modifier-chord or click keeps returning `no_viable_candidate`/`rejected` against a background-launched window, don't keep retrying blindly -- ask the user to click the target window once to give it real OS focus, then retry; chords and clicks start working normally afterward. For typing short strings into a field, prefer sending characters individually via `press_key` rather than `type_text` if the bulk call's result looks suspicious (verify with a `get_window_state` image read) -- it may silently multiply the input.

**From the tool descriptions (read 2026-10-05, the package README is empty so these are the only docs):** press_key sends to the focused element unless element_index is given, and Sublime's quick/input panels are not accessibility elements, so keys reach the editor behind them. Modifier chords need the foreground fallback; bare navigation keys can be posted in the background. A reply 'user input was detected ... call get_window_state' is a safety guard that clears after re-reading the window with get_window_state. Coordinate clicks use pixels of the screenshot just taken (capture_mode image) and are the escape hatch for surfaces with no accessibility node. The server also stops itself with a 'stopped by the user with the physical Escape key' message (see computer_use_false_escape_stop).
