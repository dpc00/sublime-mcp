---
name: write-notes-into-the-applicable-repo
description: Donald 2026-10-05 - every note I write goes into the repo it belongs to (sublime-mcp, GhostShell, AgentIDE) under .claude/memory with an index line; write ONLY in the repo; do not keep updating the global copy
metadata:
  type: feedback
---

On 2026-10-05 Donald said: "write your notes into the applicable repo. I don't care if you keep global copies. I will never see those." He does not back up the global memory folder (`C:\Users\donal\.claude\projects\C--Users-donal-projects-sublime-mcp\memory\`); the repos are what last.

**Why:** the repos are backed up and shareable; the global folder is not.

**How to apply:** when I write or change a note, put it in the repo it is about: `C:\Users\donal\projects\sublime-mcp\.claude\memory\` (sublime-mcp usage, the package audit, working with Donald), `C:\Users\donal\projects\GhostShell\.claude\memory\` (GhostShell), `C:\Users\donal\projects\AgentIDE\.claude\memory\` (AgentIDE). Add one line to that folder's `MEMORY.md`. UPDATE 2026-10-05 (Donald asked why I kept global copies): write notes only in the repo from now on and stop updating the global folder; the old global copies stay as they are, and the repo's CLAUDE.md imports the index so a session opened in that repo still sees the notes. The one-time copy of all existing notes was made on 2026-10-05, so later edits made only in the global folder need copying across. Do not commit or push for him unless he asks; pybackup also commits these repos. See [[feedback_name_package_and_screenshot_after_each_command]] for the other 2026-10-05 working rules.

**2026-10-05 later:** Donald: at the beginning of a session scan all projects and ingest the repo memories in their entirety, write only into the repos, and expect no global copies of notes that are in a repo. Done: every global note was verified identical to its repo copy and the 110 global copies were sent to the Recycle Bin; the global memory folder now holds only a pointer MEMORY.md. The start-of-session instruction itself lives in C:\Users\donal\.claude\rules\repo-memories.md, which Claude Code loads in every session.
