---
name: gemini-cli-replaced-by-agy
description: "Donald's Google agent CLI is now `agy` (Antigravity); Gemini CLI rejects individual accounts since 2026-06-18, so GeminiCLI-style packages cannot be chat-tested"
metadata:
  node_type: memory
  type: reference
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-02T23:50:44.993Z
---

2026-10-02: while testing the GeminiCLI package (flashmodel/gemini-st 1.2.0), `gemini --acp` answered "This client is no longer supported for Gemini Code Assist for individuals ... migrate to the Antigravity suite". Donald: "command is agy these days." `agy` is on his PATH (%LOCALAPPDATA%\agy\bin); `gemini` 0.55.1 is still installed via npm but unusable without an API key or enterprise account.

**Why:** a package that drives `gemini` can only be tested up to start-up and its error message; a real chat needs an API key (a secret I do not have). The same repo has an open PR (#4) adding an antigravity provider.

**How to apply:** for Gemini-based packages, test start-up and error handling, say plainly that chat was not testable, and do not hunt for credentials. Related: [[feedback_never_skip_for_missing_prereqs]].
