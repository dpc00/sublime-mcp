---
name: no-unattended-package-harness
description: launching an unattended sandbox Sublime that auto-installs/runs thousands of third-party packages was denied by the permission classifier; ask Donald before building or running such a harness
metadata:
  type: feedback
---

On 2026-09-25 I built a portable ST copy plus an auto-install harness (scratchpad `st_sandbox`) and tried to launch it; the auto-mode classifier denied it as "Create Unsafe Agents". I did not retry by another route.

**Why:** an unattended loop that installs and executes code from ~3,000 third-party packages (with network access and auto-answered dialogs) is treated as an unsafe autonomous agent, even in an isolated Data dir.

**How to apply:** do not launch it (or any similar bulk-execution harness, including via computer-use `start_app`) unless Donald explicitly approves it in the conversation; keep to static triage and single-package live tests in a throwaway window. Related: [[project-static-triage-campaign]].
