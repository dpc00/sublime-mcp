---
name: tested-list-not-log-2026-10-07
description: 2026-10-07 Donald: the 1 MB audit log is his record of the audit procedure; I only need a small file of tested packages, .tested_packages.tsv
metadata:
  type: feedback
---

2026-10-07, Donald: "You are having trouble with the log size. You need just a file of tested packages. You don't need that log. I need that log to show the general nature of the audit procedure." He also wants the log preserved; it is backed up to Google Drive (pybackup; checked the same day, Drive copy matched the local 1,080,355 bytes).

**Why:** the log passed 1 MB; my Read limit is 256 KB, so I kept searching it by name, which was clumsy and error-prone. The audit's real record of what is done only needs name, date and where to look.

**How to apply:** look up tested packages in `.tested_packages.tsv` (name, date, log line; built from the log's headings plus hand-added rows). Append a row when a package is done or skipped. Keep adding dated entries to the log, but never read it whole. Related: [[eased-audit-list-2026-10-07]], [[project_log_backup_to_google_drive_later]].
