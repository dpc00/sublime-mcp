---
name: feedback-prioritize-dialogs-console-errors-during-install
description: "during any package/software install-and-test loop, a native dialog or a Python console error is the single most important signal to check first -- it usually means the install failed and something needs a restart"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a393e427-5520-48bb-9c04-b2887aafdba8
  modified: 2026-10-05T01:53:27.022Z
---

After installing a package (Package Control or otherwise) and before doing anything else -- before claiming the install succeeded, before moving to the next package, before running any other check -- look for a native dialog and read the Python console. A dialog or a console error at this point can mean the install failed (ST needs a restart, or the package's Python dependencies failed to install), but it can also be something harmless or expected (a package's own "requires tool X" dialog, a "file changed on disk, reload?" prompt, a messages tab). Either way it is worth reading first, because it decides whether the rest of the loop's result means anything.

**Why:** Said 2026-09-28 reflecting on the omp package-audit meltdown (feedback_scope_is_ghostshell_bugs_only (note not found) session) -- "The dialog block was not prioritized over the test of it. On package install, it is often the most important thing to observe... Tried everything I could think of to get it to concentrate on dialogs and python console error messages" and it never reliably did. omp repeatedly reported the console as clean when it visibly wasn't, and let dialogs accumulate (10 at once at one point) while proceeding as if things were fine.

**How to apply:** In any GhostShell/sublime-mcp package-testing work, check `list_native_windows` (or equivalent) and the Python console immediately after every install action, before reporting success or moving on. Don't take an absence-of-error claim at face value from a prior turn or another agent's log -- verify it live. See also feedback_check_console_before_declaring_load_failure (note not found) and feedback_screenshot_verify_before_after (note not found).

**2026-09-28 self-caught lapse (proof this rule is easy to skip even right after writing it):** tested Quarto (queue #604) with a sample .qmd, saw clean scopes, wrote "no defects found" and moved on to the next package -- without checking the console. The console actually had 4 real warnings from that exact test (`no such context scope:text.tex.latex#begin-end-commands` etc., a genuine missing-context bug, later filed as quarto-dev/quarto-sublime#6). The user caught it two packages later with "there are console errors from previous package." Lesson sharpened: check the console after *every* test that touches a package, not just ones where something visibly looked wrong -- a clean-looking sample doesn't mean a clean console.
