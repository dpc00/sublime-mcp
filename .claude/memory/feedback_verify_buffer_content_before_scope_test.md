---
name: feedback-verify-buffer-content-before-scope-test
description: "multi-line view.run_command(\"insert\", ...) tests can be silently corrupted by Sublime's auto-indent, producing false-positive \"wrong scope\" bug reports -- verify buffer content matches the source before trusting any character-offset scope lookup"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a393e427-5520-48bb-9c04-b2887aafdba8
  modified: 2026-09-28T11:47:37.399Z
---

`view.run_command("insert", {"characters": multiline_string})` treats embedded `\n` characters like real keystrokes, so Sublime's auto-indent logic runs on each one -- just like it would if the user pressed Enter. If the inserted text has genuine indentation (nested blocks, multiple indent levels), auto-indent can progressively alter the actual buffer content relative to what was intended, compounding line by line. Any subsequent `scope_name(idx)` lookup computed from offsets into the *original* string is then reading the wrong characters in the *actual*, silently-modified buffer -- producing a consistent, plausible-looking "everything is scoped wrong, shifted by N characters" pattern that looks exactly like a real syntax bug.

**Why:** This produced a real, filed, public false-positive bug report during the sublime-mcp package-audit campaign -- `ofekih/smpl-sublime#1`, filed as "if/then/else highlighting is shifted onto the wrong tokens throughout," which was actually just this test artifact. It was caught one package later (PureBasic, queue #618) by noticing the buffer's actual content had accumulating indentation that didn't match the source string. Had to post a retraction comment and close the issue.

**How to apply:** Before trusting ANY `scope_name(idx)` result on multi-line inserted content:
1. Set `view.settings().set("auto_indent", False)` before the `insert` call.
2. After inserting, verify `view.substr(sublime.Region(0, view.size())) == original_sample_string` exactly, before computing any offset-based scope lookup.
3. Samples with no leading whitespace on any line are safe either way (nothing for the compounding to act on) -- this is why some tests in the same campaign (Quarto, Xcode Configuration Settings, the .pbxproj portion of Old-Style ASCII Property Lists) were unaffected without ever applying the fix; only genuinely indented multi-line samples are at risk.
4. If a "bug" surfaces as a clean, systematic scope-shift pattern across many tokens in a live Sublime syntax test, treat that pattern itself as a red flag for this exact test artifact before writing it up as a real defect -- verify the raw buffer content first.
