---
name: feedback-never-skip-for-missing-prereqs
description: In the package audit never skip or hold a package because a tool/app/service isn't installed; install it (free ones) and test. The only barrier is cost. Don't guess what Donald "wouldn't want".
metadata:
  type: feedback
---

2026-09-26 Donald was upset that ~10 packages were held back for missing prerequisites (GitHub Desktop - which exists for Windows, GlassIt's SetTransparency.exe, direnv, Discord, Cursor, Ruby/RSpec, babashka, dotnet-csharpier, go-task, php-cs-fixer, verible, g++, inkscape, Postgres/SQLTools...). "My only barrier is if it costs money." Constellation is fine to test and could even open every installed agent in its own window. Ruby's syntax is the largest BNF he knows: test it. He also dislikes batching because it hides my bad decisions.

**Why:** skipping for "not installed" is an invalid reason; he would have installed things himself, and my guesses about what he likes were wrong.

**How to apply:** when a package needs an external tool, install the free one (winget/pip/npm, prefer user scope so no UAC prompt), then test. Ask only about paid software (MATLAB), accounts/credentials/API keys that cost money, or when data would leave the machine. Work ONE package at a time and say what I'm doing and why BEFORE any skip decision. Related: [[feedback-good-deeds-ok-and-inbox-deletes]], [[feedback-no-unattended-package-harness]].
