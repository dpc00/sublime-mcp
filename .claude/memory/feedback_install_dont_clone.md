---
name: install-dont-clone
description: "In the package audit, install packages through Package Control; clone a repo only when there is absolutely no other option"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 80ae38f1-7ab9-4aa3-be87-7693e48d1b6b
  modified: 2026-09-26T21:43:49.689Z
---

For the package audit, always INSTALL the package (Package Control) to test it; do not clone the repo to test it. Clone only if installing is truly impossible, and say why.

**Why:** 2026-09-26, Donald, right after an omp agent's `git clone` failed on a mangled Windows path and left a stray folder; testing the installed package is also what a real user gets.

**How to apply:** use the install path in the baton (pb_install.py pattern + installed_packages entry + satisfy_libraries, see [[feedback_install_package_skips_libraries]]). Reading source for a finding may still use a shallow clone under %TEMP%\q_<name> only when the installed copy is not readable enough. See [[feedback_never_skip_for_missing_prereqs]].
