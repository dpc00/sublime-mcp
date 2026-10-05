---
name: portable-st-4200-older-build
description: "A second, older portable Sublime Text 4200 (Python 3.8 and 3.3 hosts) at D:\\st_portable_4200 for testing packages that only work before build 4215; HTTP bridge port 9520, MCP port 9522"
metadata:
  node_type: memory
  type: reference
  originSessionId: fcb54aa2-1c5d-45af-9d39-81632204ff55
  modified: 2026-10-05T01:53:06.243Z
---

2026-10-03 Donald: "Just install earlier portable version somewhere." Installed official build 4200 (zip from download.sublimetext.com, Authenticode-verified Sublime HQ) at `D:\st_portable_4200` (zip left at D:\st_4200.zip), with `Data\KEEPME`, Package Control copied from the 4215 portable, and a copy of the MCP Commander package whose `.python-version` is changed to `3.8` (the 4215 copy says 3.14, which does not exist in 4200 and silently falls back to Python 3.3). Settings: `mcp_port 9522`, `http_port 9520`. When first set up it was not registered as an MCP server in Claude and was driven over HTTP; since 2026-10-04 the project `.mcp.json` also lists it as `sublime-mcp-portable-4200` (port 9522), and the HTTP route still works. The HTTP scripts (session scratchpad, which is temporary and may no longer exist) were `st4200.py <file.py>` (runs eval_python), `console4200.py`, `win4200.py [hwnd]` (list or dismiss dialogs), `install4200.py` (Package Control install, edit NAMES), `reload4200.py` (ignore/un-ignore a package to register it; edit PKG).

**Why:** build 4215 runs every plugin on Python 3.14, and many older packages need libraries that exist only for Python 3.3/3.8 (Golang Build's golangconfig and shellenv). In 4200 Golang Build loads and runs a Go build; in 4215 it cannot start (filed golang/sublime-build#45).

**How to apply:** when a package fails in the 4215 portable for missing libraries or old-Python syntax, retest it in 4200 and say in any issue which build fails. A window test needs that window in front; on 2026-10-04/05 both portables ran at the same time without trouble, but see [[feedback_one_portable_instance_no_test_windows]] for the earlier instruction to run only one. Related: [[reference_portable_st_4215]].
