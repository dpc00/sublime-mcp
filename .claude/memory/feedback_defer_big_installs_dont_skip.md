---
name: defer-big-installs-dont-skip
description: "2026-10-03 Donald: never skip a package because it needs a large install; put it on a deferred list and do it in off hours when the internet is quiet"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-04T02:50:13.831Z
---

Donald: "balking on account of large installs required, is not appropriate. If you feel we should skip something, ... put in a deferred list to pick up later, during off hours. When internet is not as busy."

He added: "or when I'm sleeping." So off hours = when the internet is quiet OR when he is asleep. I don't know his schedule (see [[feedback_no_time_of_day_assumptions]]), so run big installs only when he tells me he is going to sleep or that it is off hours.

**Why:** the bandwidth worry (Xfinity Internet Essentials, see [[feedback_no_retests_no_big_downloads]]) is about timing, not about leaving packages untested.

**How to apply:** the list is `C:\Users\donal\data\st_packages\deferred_big_installs.md` (SublimeHaskell backend, SwiftKitten, elasticsearch client, plus licence-blocked packages noted separately). Add an entry instead of skipping. Do NOT start big downloads during normal hours; start them only when Donald says it is off hours, and do not schedule unattended installs on my own (see [[feedback_no_unattended_package_harness]]). This replaces the "ask before >50 MB, otherwise skip" part of [[feedback_no_retests_no_big_downloads]]; the no-retest-on-request part stands.
