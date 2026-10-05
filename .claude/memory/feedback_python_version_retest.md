---
name: python-version-retest-rule
description: When a package fails because it lacks .python-version (3.3 host), add one to a local unpacked copy and retest before moving on; don't stop at filing the issue
metadata:
  type: feedback
---

Donald's standing rule for the package campaign: if a package is broken only because it has no `.python-version` (so it loads in the Python 3.3 host and hits pathlib/typing/f-string errors), don't just file the issue and move on. Put a `.python-version` (3.8) into a local unpacked copy (Packages\<Name>, real dir, junction-checked, uninstall removes it) and retest the real commands.

**Why:** 2026-09-25 Donald asked "Why didn't [you] solve .python-version for testing" after I filed ukyouz/SublimeText-DefineParser#3 without retesting; he had told me earlier "why aren't you just putting it in somewhere and retesting". He wants the rest of the package exercised too, since a hidden load failure masks other bugs.

**How to apply:** file the load-failure issue first (one issue per finding), then retest with the local fix and file any further bugs found. Related: [[feedback_install_package_skips_libraries]] (run satisfy_libraries and reload the plugin), [[feedback_destructive_tests_sandbox_only]].
