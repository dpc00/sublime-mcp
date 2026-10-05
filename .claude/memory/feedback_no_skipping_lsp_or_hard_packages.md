---
name: no-skipping-lsp-or-hard-packages
description: "Never skip a package because the test rig makes it awkward (LSP-* wrappers, packages with server downloads or install prompts); solve the rig, answer prompts myself in the portable, and test it"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 20d54abe-2f32-4daf-93ee-a1da9540a1db
  modified: 2026-09-30T00:39:55.834Z
---

On 2026-09-29 I skipped the LSP-* wrappers (LSP-clangd, -pylsp, -intelephense, -rust-analyzer, -gopls, -css, -html, -eslint) and passed over SublimeLinter-gjslint, and Donald objected: "you skipped a few. Why? You are not supposed to have a weak approach."

**Why:** the campaign rule is already "never skip for missing prerequisites" ([[feedback_never_skip_for_missing_prereqs]]). A rig limitation or a prompt is a barrier to solve, not a reason to skip. The clangd "install clangd?" prompt is in the throwaway portable, so I answer it myself with computer-use; Donald must not have to.

**How to apply:** for LSP packages use one batch in one portable session: install LSP, satisfy_libraries, unpack the .sublime-package into Data/Packages (the resource index does not see raw-API installs), reload LSP.boot, then each wrapper the same way; open a sample file, wait for the server download, exercise diagnostics/hover/completion. Warn Donald once before relaunching the portable. Only skip when there is genuinely nowhere to report AND nothing to test; say so plainly.
