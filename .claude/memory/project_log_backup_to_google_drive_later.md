---
name: project-log-backup-to-google-drive-later
description: Donald plans to open up log backup to Google Drive; it is blocked somewhere in pybackup. Future work, wait for him.
metadata:
  type: project
---

2026-09-29: Donald said he should probably "open up" log backup to Google Drive; it is blocked somewhere in pybackup (PyBackupPanel). He hadn't thought of it before purging `~/data/logs`.

**Why:** the purge of older logs lost campaign history (see [[reference_where_campaign_records_live]]); a Drive backup would let logs be pruned locally without losing them.

**How to apply:** don't start on it unprompted. When he asks, look for where pybackup blocks Google Drive as a destination. Until then keep local logs small and don't recreate build-up.
