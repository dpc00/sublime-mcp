---
name: recycle-bin-and-keep-big-tools
description: "Donald wants deletions sent to the Recycle Bin, and big tool downloads kept (not deleted) because maintainers ask for retests"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-02T13:04:52.325Z
---

2026-10-02: Donald asked "Don't you know how to use the recycle bin?" and "if they want things retested, what will we do, download everything again?" after I had permanently deleted (rm -rf / Remove-Item) test artifacts, including multi-hundred-MB tool downloads (GHC 9.14.1 452 MB, Kotlin LSP server 390 MB zip, Gradle cache 462 MB, typst 0.15.1, Julia soon).

**Why:** deletions must be recoverable, and maintainers do ask for retests (alimony asked to retest sublime-sort-numerically; kaste/rwols review PRs), so re-downloading big toolchains wastes hours.

**How to apply:**
- Delete via the Recycle Bin: `powershell -File <scratchpad>/recycle.ps1 "path1" "path2"` (uses Microsoft.VisualBasic FileSystem SendToRecycleBin; skips anything containing junctions/symlinks; tested 2026-10-02). Never `rm -rf`/`Remove-Item -Recurse` on user-visible folders. Still junction-check first. Throwaway scratch inside the session scratchpad may be removed normally.
- Keep reusable tool downloads: move them to `C:\Users\donal\tools\<name>-<version>\` (his existing convention: erlang, verible, fantom) instead of deleting after a package test, and note the path + download URL in the campaign log. Delete only the per-test project folders and the package under test.
- Tools I already deleted today are re-downloadable: GHC https://downloads.haskell.org/ghc/9.14.1/ghc-9.14.1-x86_64-unknown-mingw32.tar.xz ; Kotlin LSP server https://download-cdn.jetbrains.com/language-server/kotlin-server/263.4702.0/kotlin-server-263.4702.0.win.zip ; typst github.com/typst/typst releases (typst-x86_64-pc-windows-msvc.zip); Gradle 9.1.0 via wrapper properties; Julia 1.12.7 https://julialang-s3.julialang.org/bin/winnt/x64/1.12/julia-1.12.7-win64.zip.

Related: [[feedback_destructive_tests_sandbox_only]], [[feedback_report_bugs_never_patch_authors_code]].

**2026-10-02 follow-ups:** (1) recycle.ps1 used to print "recycled:" even when the shell call threw ("This function is not supported on this system", seen when ST still held a .sublime-workspace file); it now prints FAILED unless the item is really gone - read its output, retry after a few seconds, or recycle the children first. (2) Packages that call `subl`/`sublime_text.exe --new-window <folder>` (e.g. Sesame open) can leave a stray windowless launcher process in the portable (parent = portable plugin_host, cmdline contains the test folder); it keeps that folder locked. Stop ONLY that PID after checking its path/cmdline. (3) Donald 2026-10-02: opening new windows in the portable is fine ("you can always close them"); close only the windows I opened by id diff and never the first one.
