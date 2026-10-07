---
name: binaryplist-fork-test-2026-10-06
description: "2026-10-06 tested eugenesvk's st3-binaryplist fork for the UID plist report (tyrone-sudeium/st3-binaryplist#12): reader fixed, XML writer still raises TypeError; comment posted; rig leftovers"
metadata:
  type: project
---

eugenesvk (fork maintainer, issues disabled on the fork) asked on #12 to re-check with his fork (Python 3.14). Tested 2026-10-06 on the 4215 portable (the only build here with a 3.14 host; 4200 has 3.3/3.8 only): the UID is read, but `to_xml_plist` fails with `TypeError: unsupported type: UID` (fork plistlib.py line 565), buffer stays hex. Posted as a comment on #12 (issuecomment-6008549881) with Donald's yes; not a new issue because the fork has issues off. Save-back to binary was not reached.

**Update (same day, evening):** eugenesvk fixed it and asked for a retest. Retested on 4215: XML shows `CF$UID` dict, save-back gives `bplist00` and `plistlib.load` returns `UID(1)`; works. Posted a thank-you comment (issuecomment-6023837082). Trap: ST does not reload the nested `plistlib` folder, so delete `BinaryPlist*` from `sys.modules` and touch BinaryPlist.py (or restart) after updating the files. Issue is done; the files at the leftovers path below can be recycled.

**Rig leftovers:** fork copied to `D:\st_portable_4215\Data\Packages\BinaryPlist` and test file `D:\st_portable_4215\testdata\uid_test.plist`, kept for a retest if eugenesvk replies. Limitcode folder was recycled from 4215 the same day. 4215 and 4200 portables were both running; Naomi (4200) is installed and half-tested: syntax works, `close_jsx_tag` / `toggle_jsx_comment` did nothing via run_command with no console error (source not yet read).

**How to apply:** download a repo without cloning with `Invoke-WebRequest codeload.github.com/<owner>/<repo>/zip/refs/heads/<branch>` (PowerShell `>` redirect corrupts zips). Packages installed through `PackageManager.install_package` must also be added to `installed_packages` in `Package Control.sublime-settings`, or Package Control removes them as orphans at the next start.
