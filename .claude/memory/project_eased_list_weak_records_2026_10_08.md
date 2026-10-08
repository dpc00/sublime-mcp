---
name: eased-list-weak-records-2026-10-08
description: 2026-10-08 Donald said "ease something"; I re-included packages whose only record was an incidental install (134 rows), 19 passed his other rules; list file and order
metadata:
  type: project
---

Donald (2026-10-08): "ease something" after the list ran dry again. I chose the rule "not already in the tested file": rows in `.tested_packages.tsv` whose note says "install line seen in ... (may be a rig/dependency install)" or "(install signal)" (134 rows) are not real tests, so they count as untested again. Rows with real test evidence (dated, queue, "testing signal") still exclude a package. Every other rule is unchanged: top 1,000 by installs, not archived, pushed in the last 2 years, at least 4 KB of Python, not by Sainan/alepez/Naereen, newest push first. Built from the saved 2026-10-07 data (`popular_gh_2026_10_07.jsonl`), no network. 56 of the 134 are in the top 1,000; 19 pass. List: `C:\Users\donal\data\st_packages\audit_list_2026_10_08_weakrecords.tsv` (LSP, A File Icon, Debugger, StringEncode, Markdown Images, NeoVintageous, EditorConfig, GitGutter, MarkdownPreview, ColorConverter, CoffeeScript, TabsExtra, ApplySyntax, ScopeHunter, EasyDiff, Wrap Plus, Simple FTP Deploy, xpath, Sass).

**Why:** the strict list and the 4-year and no-Python easings were used up; this one keeps maintained, popular packages and does not bring back dead ones. **How to apply:** when a package from this list is tested, append a real row to `.tested_packages.tsv` (the old weak row stays, the newer dated row is the real record). Next easing, if needed: older than 4 years is dead packages (do not); top 1,000 to top 2,000 by installs is the next candidate. Related: [[eased-audit-list-2026-10-07]], [[audit-exhausted-and-reload-hang-2026-10-08]].
