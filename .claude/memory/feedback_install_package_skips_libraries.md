---
name: install-package-skips-libraries
description: "PackageManager().install_package() does not install libraries; run satisfy_libraries before calling a package \"dead on arrival\" for a missing dependency"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1e07794b-efe6-4e5f-bbc3-7d3161a16a46
  modified: 2026-09-25T07:00:18.059Z
---

In the package bug-hunt campaign, installing via `PackageManager().install_package(name, unattended=True)` skips library installation (the real Install Package UI flow does it in a second step in `package_tasks.py`). Any "declared dependency never installs / ModuleNotFoundError right after install" observation made that way is a harness artifact.

**Why:** discovered 2026-09-25 with UnitTesting (`sublime_aio`). `sublime.run_command('satisfy_libraries')` then installed everything. Four already-filed issues were false positives and had to be retracted publicly (Avrae#3, KodiDevKit#6, AmxxEditor#23, RememberCommandPaletteInput#3 comment) - embarrassing for Donald's GitHub account.

**How to apply:** after every test install run `sublime.run_command('satisfy_libraries')`, wait for "All libraries have been satisfied!", re-check; after removal run `PackageManager().cleanup_libraries()` to drop orphan libs. Only a library truly absent from the channel for that Python/platform is a finding. Missing/export-ignored `.python-version` is a separate real class. Related: [[feedback-report-bugs-never-patch-authors-code]], [[feedback-one-issue-per-finding]].

**Second trap (2026-09-26): legacy dependency names.** Package Control's `package_control/library.py` translates old names (`enum`->`enum34`, `python-markdown`->`Markdown`, `python-jinja2`->`Jinja2`, `bs4`->`beautifulsoup4`, `pymdownx`->`pymdown-extensions`, `dateutil`->`python-dateutil`, `python-six`->`six`, `python-toml`->`toml`, `ruamel-yaml`->`ruamel.yaml`, `serial`->`pyserial`, `python-pywin32`->`pywin32`...). Comparing a package's `dependencies.json` names against `list_available_libraries()` alone gives false "unknown library" hits: I filed then had to close bicarlsen/vintage_relnums#6 for exactly that. Read the map from the live PC (`inspect.getsource` of `library`) and, better, actually run `satisfy_libraries` before claiming a dependency is unresolvable.
