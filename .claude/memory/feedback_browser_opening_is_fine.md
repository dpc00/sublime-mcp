---
name: feedback-browser-opening-is-fine
description: Packages that open the default browser during tests are fine; don't suppress it
metadata:
  type: feedback
---

2026-10-06: while testing Markmon I set BROWSER to a no-op so the plugin would not open Donald's browser. He said "you don't need to avoid using the browser".

**Why:** opening a localhost tab is harmless to him; the workaround only added steps.
**How to apply:** let packages call webbrowser.open normally during audit tests; no BROWSER env override in the portable launchers.
