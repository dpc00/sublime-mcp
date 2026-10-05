---
name: feedback_destructive_tests_sandbox_only
description: "Donald's Packages\\ entries are junctions to his real repos; never run delete/clear/uninstall tests where any path could resolve into them"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 165e315a-efcb-49b3-8b31-7320fbdb0c43
  modified: 2026-09-24T16:50:53.111Z
---

Donald's `AppData\Roaming\Sublime Text\Packages\` holds junctions (AgentIDE, AiSDK, AiSearch, GhostShell, MCP Commander -> sublime-mcp, PyBackupPanel, STConfig) pointing at his real repos under `C:\Users\donal\projects`. On 2026-09-24, while auditing Package Control's clear_directory (which follows junctions and deletes the target's files), he said "try not to delete my repos".

**Why:** a delete/clear/prune test that resolves into one of those junctions destroys real work. Package Control's own `clear_directory` does exactly that on Windows/py3.8.

**How to apply:** run destructive tests only on throwaway dirs under the scratchpad, with junctions I create to other scratchpad dirs. Do not create test junctions inside the real `Packages\` or `Backup\`. Clean up links with `os.rmdir`/`cmd /c rmdir` only, never a recursive delete, and re-count his repos' files afterward. Related: [[feedback_never_close_or_retarget_windows_by_exclusion]], [[project_gadzillion_package_test_campaign]].
