---
name: wsl-st-update-dialog-hosts-block
description: 2026-10-06: the WSL Sublime shows an unclickable "Update Available" dialog on start; blocked by a /etc/hosts entry; how to tell a package hang from it
metadata:
  type: project
---

On 2026-10-06 the WSL Sublime (4200) froze at startup with ST's own "Update - Sublime Text" dialog (Current 4200, latest 4215). `update_check: false` is ignored while UNREGISTERED, and in the WSLg window neither Donald's keys/mouse nor PostMessage Enter/WM_CLOSE nor xdotool Escape/click dismissed it. The main thread then times out every eval_python call ("main-thread timeout ... native dialog").

**Fix that worked:** added `127.0.0.1 www.sublimetext.com` to WSL's /etc/hosts (via Tab 2 sudo), then killed and relaunched with wsl_restart.sh. No dialog since. WSL regenerates /etc/hosts on a WSL restart, so re-add it if the dialog returns. xdotool is installed in WSL (`DISPLAY=:0 xdotool search --name Update`).

**Also learned:** a package that blocks the main thread looks the same (BuildSock, iccir/BuildSock#3: unloading it hangs Linux ST because of close()+join() on an accept() thread). Check list_windows for a dialog first; if none, suspect the package just installed. If a dead session wedges startup, move `~/.config/sublime-text/Local/*.sublime_session` aside (backup in ~/removed_packages/session_bak).

**Why:** cost about an hour and several restarts. **How to apply:** after any WSL ST restart, confirm eval_python answers before testing; don't restart it needlessly. Related: [[project_wsl_st_running_2026_10_06]].
