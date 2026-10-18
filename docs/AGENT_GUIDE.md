# Agent Guide for sublime-mcp (MCP Commander)

Canonical copy for repo readers. `get_help` serves
`AGENT_GUIDE.md` (repo root) -- keep these two files in sync.

How to use sublime-mcp tools. Call `get_help` if you are unsure how to
save, close tabs, or run ST Python.

Eight workflow tools are shown by default; the complete typed catalog (381
tools) remains available through `discover_tools` and `batch`. Prefer a named capability over
`run_command`, which often opens UI that steals focus from the agent chat.

On the first Sublime operation, call `get_help` once. The guide is long (about 16 KB):
`get_help(section="console")` returns only the sections whose heading contains that word, and
every `get_help` result lists the section headings.

ST tools use **1-based** line/column (`get_active_file`, `open_file`,
`goto_line`, `replace_lines`). Language-server tools use **0-based**. Subtract 1 when
passing an ST cursor into an `lsp_*` tool.

## Quick start

Eight tools are listed and are called directly: `get_help`, `get_active_file`, `ui_screenshot`,
`project_search`, `str_replace_based_edit_tool`, `save_file`, `batch`, `discover_tools`.
Every other tool is hidden. Find it with `discover_tools`, run it with `batch`.
`discover_tools` never returns the eight listed tools, so do not search for them.

```
discover_tools(query="sort lines")                    # find a tool by words
discover_tools()                                      # or browse: categories -> subcategories -> tools
batch(calls=[{"tool": "sort_lines"}])                 # run it (also for a single call)
```

A new tab with text, sorted and upper-cased, then read back (one round trip):

```
batch(calls=[
  {"tool": "new_file"},
  {"tool": "insert", "args": {"characters": "pear\napple\nmango"}},
  {"tool": "select_all"},
  {"tool": "sort_lines"},
  {"tool": "upper_case"},
  {"tool": "get_active_file"}
])
```

Close that tab without saving (only the active, modified, untitled tab is touched):

```
batch(calls=[{"tool": "eval_python", "args": {"code": "v = window.active_view()\nif v.is_dirty() and not v.file_name() and not v.settings().get('ai_terminal_view'):\n    v.set_scratch(True)\n    v.close()\n    print('closed')"}}])
```

- `insert` types at the cursor, so calling it twice puts the text in twice.
- Case commands (`upper_case`, `lower_case`, `title_case`, `swap_case`) act on the
  selection: `select_all` first. `sort_lines` sorts the whole buffer when nothing is selected.
- `get_active_file` returns untitled tabs too (`path` is null).
- `close_file` on a modified untitled tab opens a native "Save Changes?" dialog that blocks
  every tool; see "When a native dialog blocks Sublime" below. Once, `set_scratch` followed
  by `close_file` in one `batch` was followed by Sublime exiting (cause not established).

A file on disk: create it, change it, save it, read it back, close it. The first four are
listed tools, called directly:

```
str_replace_based_edit_tool(command="create", path="C:\\dir\\notes.txt", file_text="hello world")
str_replace_based_edit_tool(command="str_replace", path=..., old_str="hello", new_str="goodbye")
save_file(path=...)
str_replace_based_edit_tool(command="view", path=...)
batch(calls=[{"tool": "close_file", "args": {"path": "..."}}])      # hidden tool, saved file: no prompt
```

`create` opens the new tab itself (no `open_file` needed) and fails if the file already exists;
the file reaches the disk when `save_file` runs. `str_replace` and `insert` edit the open tab, so
they also need `save_file`. `create` does not make missing folders. To open an existing file use
the hidden tool `open_file(path=...)`.

Hidden tools (everything except the eight) are only reachable through `batch`; calling one
directly gives "No such tool". `get_sheets` returns every tab's full settings (over 100 lines per
tab) unless you pass `settings=false`, which gives a compact list; the hidden `get_open_files`
returns just each tab's path, name and dirty flag.

## Batch (cuts round trips)

Each call pays a trip through ST's main-thread scheduler. For 2+ independent
calls, use `batch` (max 50; cannot call itself):

```
batch(calls=[
  {"tool": "get_active_file"},
  {"tool": "get_selection"},
  {"tool": "get_cursor_context", "args": {"lines": 20}}
])
```

Returns `{"results": [...]}` in call order. A failed call is `{"error": ...}`
in its slot; the rest still run.

## Finding tools (discover_tools)

`discover_tools()` lists the categories (`app`, `editing`, `files`, `packages_and_dev`, `project`,
`read`, `run`, `search`, `selection`, `settings`, `tabs`, `view`); `category="editing"` opens one,
`category="editing/lines"` lists its tools with schemas; `query="upper case"` searches all tools.
Run any result with `batch(calls=[{"tool": "<name>", "args": {...}}])`.

## Editing

`str_replace_based_edit_tool` edits the **buffer**, not disk. Always save:

1. `str_replace_based_edit_tool(command="str_replace", path=..., old_str=..., new_str=...)`
2. `save_file(path=...)` — omit `path` to save the active file

Skip save and ST looks edited while `git diff` is empty.

- Disk `edit`/`write` on a file ST has open → `revert_file` so the buffer reloads.
- Short plain text into an empty tab: `insert` is fine. Indented or large multi-line
  content: use `replace_lines(begin, end, text)`, because `insert` (and
  `view.run_command("insert", ...)`) auto-indents every line and piles indentation.
- `str_replace` `old_str` must match **exactly once**.
- Commands: `str_replace`, `insert` (after 1-based `insert_line`; `0` = start),
  `create`, `view`.

## Closing tabs

A dirty view makes `close_file` open ST's save prompt. Save first, or use the
scratch snippet in the Quick start. Find a path with `window.find_open_file(path)`
(there is no `find_open_by_name`).

## eval_python

Runs in ST's plugin host. Use `print(expr)` — top-level `return` is a syntax
error; bare expressions produce no output. In scope: `sublime`, `window`,
`view`. Timeout is 5s (main-thread).

`eval_python_latest` is **system** Python on PATH, not the ST host — no
`sublime`/`window`/`view`.

## Common tools

```
get_active_file()                  # path, full content, 1-based line/col, is_dirty, syntax
get_cursor_context(lines=10)       # ±N lines, numbered
get_selection()                    # highlighted text
get_sheets()                       # every tab: stable id, group/index, selection/focus, path/name
get_sheet_content(index=2)         # untitled / scratch / terminal tabs too
open_file(path=..., line=42, col=1)
save_all()
revert_file()                      # active view only
project_search(pattern=..., where=...)  # ST Find-in-Files, structured matches
discover_tools()                        # categories; see "Finding tools"
get_commands()                     # command ids, scopes, packages, palette captions
```

`project_search` `where` accepts folder paths, `*.py`, `-*.md`, `${project}`,
`${open_files}`, `${folder:Name}`.

## Packages, menus, palette and input panels (no eval_python needed)

Call these through `batch`; find more with `discover_tools`.

```
search_packages(query="<name>")                # package manager search
install_package(package="<exact name>")       # exact name; installs in the background, watch the console
get_menu_items(caption="Command Palette")     # menu items with their command and args (filters: menu, caption, command)
run_command(command="show_overlay", args={"overlay": "command_palette", "text": "Install Package"})
get_command_palette(caption="Install")        # palette entries (filters: package, command, caption)
drive_input_panel(text="<name>", action="submit")   # fill and submit/cancel an open input panel
```

- `click_menu_item` runs an installed menu item by caption path, e.g.
  `path="Tools > Command Palette..."`; the end of the path is enough when it is unique. Most
  built-in items have no caption in the menu file, so use the command name: `Selection > select_all`.
  (Or find the item with `get_menu_items` and `run_command` its command and args.)
- `show_overlay` opens Goto Anything (`overlay="goto"`) or the command palette
  (`overlay="command_palette"`), with the same arguments as Sublime's own keymap. To move through an
  open completion popup use `move` (`by="lines"`, `forward=true` or `false`): Sublime has no separate
  next/previous command for it (tried on build 4215).
- `drive_input_panel` works on input panels (prompts such as "Packages to install
  (comma-separated)"). If several agents share the Sublime, call `claim_resource`
  with `resource="input_panel"` first.
- Limitation (tool survey 2026-10-07): there is no tool that lists the items of an
  open quick-panel picker (for example the package manager's "Install Package" list)
  or picks one. Close it with `hide_overlay`, or have the user pick.
- `context_menu` opens a native menu that blocks the main thread; see the next
  section.

## Removing packages, making folders, saving to disk

Observed on build 4200 (2026-10-07).

- **Remove a package:** call `run_command(command="remove_package")`. Do not open
  the palette with the text "Remove Package": the palette ranks
  "Remove Channel" first, and its Return opens the channel list. The list that
  `remove_package` opens also contains `MCP Commander` and other packages, so
  type the package name to filter the list and check the highlighted entry before
  confirming. A list opened right after a removal is stale until the status bar
  says "Package X successfully removed".
- **Make a folder:** there is no tool that creates a folder at a path.
  `run_command(command="new_folder", args={"dirs": ["<parent>"]})` then
  `drive_input_panel(text="<name>", action="submit")` does it. `str_replace_based_edit_tool`
  `create` does not create missing folders.
- **Files reach the disk only after `save_file`** (or `save_all`); `create` alone leaves an
  unsaved tab.

## Deleting files and folders

- **Delete files and folders:** pass `files` to `delete_file` and `dirs` (a list) to
  `delete_folder`; any other argument name, such as `path`, is dropped and the call still
  returns ok without deleting. Check the disk afterwards. As with the Side Bar menu, the
  confirmation is always shown, even with `prompt: false`. They open a Windows
  confirmation ("permanently delete" when the drive has no Recycle Bin) for every
  item, block the main thread until it is answered, and can stall at "99% complete".
  Use `list_native_windows`, then answer each dialog. `dismiss_native_window` does
  not see the Windows progress window.
- **Tabs of deleted files:** if files vanish while they are open (for example because a package
  folder was removed), closing each tab raises a "Save Deleted File?" dialog; answer No.

## Reading the console

- **Read the console:** `get_console` with the default mode, and `mode="captured"`, can miss
  Sublime's own output (load errors such as a plugin's SyntaxError). `mode="visible"`
  returns the console (the last 200 lines by default; `tail=N` for N lines, `tail=0` for all, and
  the result says `lines_total` and `truncated`) but needs the window in front. If the window
  is not in front it fails at once with a clear message and changes nothing. Pass
  `force_focus=true` on every visible call (tested on 4200 and 4215: complete read, no crash;
  the window does not stay in front between calls). Do not fall back to opening the panel with
  `show_panel` and reading the screen.
- **The console is only partly readable.** `get_console` in the default and `captured` modes
  misses Sublime's own error output (tracebacks printed after an install, `ImportError`);
  `mode="visible"` needs the window in front and often cannot get it, even after a click on the
  title bar (a click from the agent does not make it the system's front window; `force_focus=true`
  raises it but can crash a portable). `get_output_panel` for the console is the same as
  `get_console` in the default mode, so it also misses those errors when the window is not in
  front. A visible capture that succeeds prints one "[sublime-mcp] console capture marker" line
  into the console; one that fails for lack of focus now leaves nothing behind. The last N lines are available
  from `get_console(mode="visible", tail=N)` whenever the window is in front.

## Silent failures and timeouts

- **`run_command` returns `{"ok": true}` even when the command does not exist** or the
  package that provides it did not load. Check for a visible effect.
- **A "main-thread timeout" says what it found.** On Windows the message now lists the native
  dialog, menu or window that is open ("A native window blocks Sublime's main thread ...:
  "Delete File" (dialog)"), or says that none is open and the main thread is busy, for example
  while a large package loads or installs, or right after the `exit` command. Answer a dialog with
  `dismiss_native_window`; for a busy thread call again in a few seconds. Off Windows the message
  can only say a dialog may be blocking. (Before this change every timeout blamed a dialog.)
  The tool may still have worked: a `create` or `save_file` that timed out while a package was
  installing had in fact gone through, so check the state before repeating it.
- **Unknown arguments used to be dropped silently.** `delete_file` with `path` returned ok and
  deleted nothing (it takes `files`), and `get_commands(query=...)` returned all commands
  (58 KB) because its filters are `package` and `command`. A result now carries a `warning`
  that names the argument and lists the valid ones, but a command that the tool only passes on
  to Sublime can still drop one, so check the result and the tool's schema in `discover_tools`.

## Installs, restarts and quick panels

- **Language-server packages installed during a session** start their server only
  after Sublime restarts, and many need a separate syntax package and a Node or binary
  download, so the status can read "(installing...)" for minutes.
- **Installs can take minutes, and the status text does not tell you when they end.** Large
  packages (SublimeCodeIntel has hundreds of files) and packages with libraries (EasyClangComplete
  fetches seven, one by one) keep "Installing package ..." in the status bar until the very
  end. Watch the real state instead: the package folder or `.sublime-package`, its
  `package-metadata.json`, and `get_command_palette(package=...)`, which stays empty until the
  commands are registered. The package manager logs "Package X successfully installed" last.
- **After `run_command exit` and a new start,** three things happen. A package manager dialog
  "Sublime Text needs to be restarted for installed or updated libraries" can open (answer OK);
  an "Update Available" window can open and disable the main window (close it; its buttons are
  not accessible elements, use its Close button); and the sublime-mcp server may or may not
  reconnect by itself (the first restart did, the second did not and needed `/mcp`). A key press
  sent right after a restart is refused until the window has been focused with a click on its
  title bar. Replacing a package between Python hosts (release on 3.3, master on 3.8) in the
  same session gives false "No module named" errors; restart Sublime first.
- **Quick panels:** several packages ask for a decision in a quick panel (FileManager's delete asks
  "Confirm - Send item to trash"; the package manager's pickers). `get_quick_panel` lists the items of
  the panel and `pick_quick_panel` picks one (by index or text) or cancels it with index -1.
  They only see panels opened by packages in the same plugin host as sublime-mcp; the command
  palette, Goto Anything and panels from the other host give an error, and then the keyboard is
  the only way. Picking runs the package's own callback, so pick only items you mean to run (some
  pickers open files, folders or browser tabs). `drive_input_panel` only fills input panels.
  **The package manager's Install Package / Remove Package lists take up to ~15 s to appear after
  Enter** (the status bar says "Loading packages..."): pass `wait_ms` (at most 60000) to
  `pick_quick_panel` or `get_quick_panel`, for example `pick_quick_panel(text="Bicep",
  wait_ms=30000)`, and the call waits for the panel instead of failing with "no recorded quick
  panel". Without `wait_ms` that error carries a hint.
- **What a highlighting plugin drew:** `get_view_regions(key="ifdef")` returns the regions stored
  with `view.add_regions(key, ...)` (begin, end, first 80 characters); name several keys with
  commas. Sublime cannot list the keys, so read the plugin's source for them. Built-in example:
  after `toggle_bookmark`, key `bookmarks`.
- **Syntax names:** `get_active_file` and `get_sheets` give `syntax` (the name, or the file name
  when the syntax file has no `name:` line, as with Bicep) and `get_active_file` also gives
  `syntax_path`.
- **Scope names differ between Sublime builds.** In build 4200 the C syntax scopes `#ifdef` as
  `keyword.control.import`; in 4215 it is `keyword.control.directive.conditional`. A package that
  selects by scope can work on one build and do nothing on the other: check the scopes with
  `get_scope_at_cursor` on the build the user runs before calling it a defect.
- **PowerShell pipes add a byte-order mark.** `Get-Content file | tool -` feeds the tool a BOM and
  tools that read stdin may report a parse error; redirect the file instead (`tool - < file`)
  from Bash or cmd.
- **`exit`** replies first and closes Sublime 300 ms later, so the call returns `ok` and the
  connection then drops (restart, then reconnect the server).

## Tools with side effects

Every tool is a Sublime command passed straight through, so each does exactly what the command does in
the editor. Know these before calling a tool you have not used (checked on 1.14.3, build 4215):

- **They open a web page in the default browser:** `html_print` (the active tab as an HTML file), `open_in_browser`,
  `open_url`, `purchase_license`, `upgrade_license`. Close the browser window afterwards. `open_context_url`
  acts on a link under a right-click, so called alone it does nothing. `show_changelog`, `show_license_window`,
  `show_about_window`, `show_progress_window` and `update_check` open Sublime windows ("Changelog", "Enter License",
  "Sublime Text", "Indexing Status", "Update"); `dismiss_native_window` with `action="close"` closes them.
- **They quit Sublime:** `exit` and `hot_exit` (hot exit keeps unsaved buffers for the next start). `close_window` and `close_all` leave Sublime running with an empty window.
- **They change settings or create files:** `increase_font_size`, `decrease_font_size` (adds `font_size`),
  `ignore_word`, `add_word` (add `ignored_words`, `added_words`), `set_setting`, `open_file_settings`
  (creates an empty settings file in `User` and makes it the active tab, which the browser tools above then use).
- **They open a native dialog and block the main thread until it is closed:** the `prompt_*` tools
  (`prompt_open_file`, `prompt_open_folder`, `prompt_add_folder`, `prompt_save_as`, ...), `save`, `save_file`
  on an untitled buffer, `save_project_and_workspace_as`, `save_workspace_as`, `save_macro` (after a recorded
  macro), `primary_j_changed` ("Key Binding Changed"), `close_folder_list` ("Confirm Remove Folders": Remove or
  Cancel), `delete_file` and `delete_folder` with `prompt=true` (OK or Cancel), `remove_license` ("Remove license key?":
  Remove or Cancel; it removes the licence) and the `sublime_merge_*` tools when Sublime Merge is not installed
  ("Sublime Merge Not Found": Download or Cancel). The call returns "main-thread timeout after 5s"; `list_native_windows` shows the
  dialog and `dismiss_native_window` closes it. Open, Select Folder and Save As have Cancel, not OK: answer
  Cancel (`action="button", button="Cancel"`); OK on a dialog with no OK button fails and leaves the
  main thread blocked. `run_command` with `context_menu` opens a popup menu that blocks the same way.
- **Find and replace in files:** there is no tool for it; use `run_command` with Sublime's own commands. First `show_panel` with `{"panel": "find_in_files", "pattern": ..., "replace_pattern": ..., "where": ..., "regex": false, "case_sensitive": false, "whole_word": false, "preserve_case": false}` (the Replace box is filled by `replace_pattern`), then `replace_all`. Sublime asks "Confirm Replace": answer it with `dismiss_native_window` (`action="button"`, `button="Replace"` or `"Cancel"`). On Replace, the changes are made in the matching files' open buffers (the files open with unsaved changes); write them with `save_all`. For one file use `{"panel": "replace", ...}` with the same arguments and then `replace_all`. To search without the panel use `project_search`.
- **Tools that depend on state you must set first:** `focus_by_index` needs several tabs selected;
  `move_to_group` needs the target group to exist and the layout to have settled; `toggle_overwrite` changes how
  typed keys (`ui_type_text`) land, not `insert`; `toggle_save_all_on_build` decides whether `build` saves
  every modified file first; `next_modification`, `prev_modification`, `revert_hunk` and `revert_modification`
  need a saved file with unsaved edits; `close_deleted_files` closes a tab only after Sublime has noticed the
  file is gone.
- **They install packages:** `install_package` installs the package; the libraries it depends on come from
  `satisfy_libraries`. A package loads the moment it is installed, so to install one that needs libraries
  (its libraries are named in its install message): add the package to `ignored_packages`,
  `install_package`, run `satisfy_libraries`, then remove it from `ignored_packages`.
- **They ask a question in an overlay or picker, and wait for the answer:** `rename_file`, `rename_path`,
  `new_file_at`, `new_folder`, `view_resource`, `show_overlay`, `prompt_goto_line`, `select_color_scheme`,
  `select_theme`, `set_file_type`, `set_build_system`, `paste_from_history`, `build` (when the build system has
  variants, such as Python), `open_recent_*` (they take `index`, 0 being the most recent),
  `goto_symbol_in_project`, `prompt_select_workspace`. Answer with `ui_type_text` and `ui_press_key`
  (`Return` to accept, `Escape` to cancel, `Down` to move), then check the result. A picker opened by a plugin
  can also be read with `get_quick_panel` and answered with `pick_quick_panel`. `rename_file` pre-selects the
  base name, so typing replaces only that part. `edit_settings` opens its two views in a new window;
  `new_file_at` opens an unsaved buffer for the new name.
- **Pickers and the Find panel are drawn by Sublime, not Windows:** `list_native_windows` does not list them;
  `ui_screenshot` shows them. Look at the screen before you restart, kill or close anything, and answer what
  is waiting first.
- **Before closing several tabs from `eval_python`:** use `view.close()` for each view, the `close_all`
  command, or closes spaced out with `sublime.set_timeout`; do not call `Sheet.close()` repeatedly in one call.
- **"This is an unregistered copy" dialog:** Sublime shows this purchase reminder now and then, for example
  after a save. Read it, then close it with `dismiss_native_window`.
- **`goto_definition`, `goto_reference`, `auto_complete_goto_definition`** use Sublime's symbol index, which
  needs `index_files` true. `lookup_symbol` searches the open files.
- **Macros:** play a `.sublime-macro` file with `run_macro_file` (file="Packages/User/name.sublime-macro").
  `toggle_record_macro` records keys typed by a person.
- `ui_click`, `ui_hover` and `ui_press_key` with `method="input"` need the target window uncovered and the
  person at the keyboard idle for `min_idle_s` (default 8); pass `wait_idle_s` (up to 120) to wait, or a
  smaller `min_idle_s`. `ui_press_key` with the default `post` method needs neither.

## When a native dialog blocks Sublime (Windows)

If a tool call fails with "main-thread timeout after 5s", or a command just
opened a native dialog or menu, Sublime's main thread is blocked and almost
every tool will time out. Two tools still work, because they never use the main
thread:

```
list_native_windows()                     # dialogs/menus with buttons + message text,
                                          # main_thread_blocked, blocked_by (the tool)
dismiss_native_window()                   # default action "cancel": Cancel/No, else close
dismiss_native_window(action="ok")        # OK / Yes / the default button (this CONFIRMS)
dismiss_native_window(action="button", button="Remove")   # a named button
dismiss_native_window(hwnd=..., action="close")           # a specific window
```

The default action is `cancel`: on the `delete_file` confirmation it clicks
**No**, on `remove_license` it clicks **Cancel**. `action="ok"` clicks OK / Yes /
the default button, which confirms the action (on `delete_file` the file is
deleted; on `remove_license` the license is removed). The tools act only on windows of the Sublime Text process, and they are Windows
only (they use Win32). Verified on all 16 blocking commands with
`tools/verify_native_dialogs.py`: each froze Sublime, was listed and dismissed
by these tools, and Sublime answered again.

**Looking at and driving Sublime's own windows (Windows only).** `ui_screenshot`,
`ui_press_key`, `ui_type_text`, `ui_click` and `ui_hover` work on the windows of the Sublime Text
process only, and need no OS permission prompt, so they also work from a remote session.
`ui_screenshot` takes a picture of one window (it works for a window behind others, and for dialogs) and
returns the image itself, first in the reply, also through `batch`. Choose the window with `window_title`
(part of its title), `kind` (`dialog` or `menu`, for an open native dialog or menu, which a plain screenshot
does not show; the reply lists them as `open_popups_not_in_picture`) or `hwnd`; `tab` shows a tab that is not in front for the picture and puts the front
tab back; `region` crops, `scale` zooms (2 doubles the size) and `max_width` shrinks; `save_dir` also keeps
the PNG and reports `saved_path`; `inline=false` returns only a file path, for a client that cannot show
images.
`ui_press_key(key="Return")` and `ui_type_text(text="cel")` post the key or characters to the window
without moving focus or the pointer, for example to pick an entry in the command palette or a quick
panel: open the palette with `run_command show_overlay`, then Return, type the filter, Return. Input
is handled asynchronously, so each call waits `settle_ms` (default 150 ms, up to 5000) afterwards, and
`ui_screenshot` waits 200 ms first.

Sublime draws its own editor, palette and popups, so it ignores posted mouse messages and posted
keys carry no Ctrl/Shift/Alt state (a posted Ctrl+Shift+P arrives as a plain "p"). For those cases
the tools use the REAL mouse and keyboard, which would disturb the person using the computer, so
they are gated: `ui_click(x, y)` (x, y are pixels in the `ui_screenshot` picture), `ui_hover(x, y,
screenshot=true)` and `ui_press_key(..., method="input")` are refused unless the person has been idle
for `min_idle_s` seconds (default 8) and the target window is the one under the point at that moment;
the pointer is put back afterwards. A refusal says how long the person has been idle; wait and try
again, pass `wait_idle_s` (up to 120) to wait for them to stop typing instead of giving up, or use keys,
`pick_quick_panel` and editor commands instead. Native popups (an open menu, the `#32768` windows in
`list_native_windows`) are windows of the process too: pass the menu's own `hwnd` to `ui_screenshot`,
`ui_hover` and `ui_click` (x, y count from the menu's top-left corner) to read and click it; a click
on the editor window's coordinates is refused while the menu is in front of that point. `method="input"` also needs the
window in front, and activates it with a real click on its title bar (same gate). Never inject real
input while the person may be using the computer, and never use `SendMessage` from a plugin to a
Sublime window: it waits for the UI thread and can deadlock Sublime (the tools only use `PostMessage`).
The default window is the first editor window of the Sublime process, which on a person's own Sublime
may be the window that hosts your session; pass `hwnd` of the window you mean.

**A dialog that appears after `run_command` has returned.** `ok` from `run_command` only
means the command was dispatched. A command that shows its dialog from a timer, a worker
thread or `sublime.error_message` does so a moment later, so a `list_native_windows` in the
same `batch` can come back without it (seen with several packages'
error dialogs). Pass `settle_ms` (for example 300): `run_command` then waits up to that long
and returns every dialog that was not open before the command as `dialogs`, with the same
fields as `list_native_windows`. Without `settle_ms` nothing changes. When `get_console`
fails for lack of focus while a dialog is open, the error now names the dialog.

**What `list_native_windows` cannot read.** The message of a Windows task dialog (one whose
buttons have custom text, such as "Install <package>" / "Cancel") comes back with an empty
`messages` list, although the buttons are listed. Read it with computer-use
(`get_window_state` shows it as the dialog's main text). With computer-use, a click by
`element_index` on those buttons may do nothing; a click at the button's pixel position
from a `capture_mode="image"` snapshot worked, and a message box can take a second or two
to close after the click, so list the windows again before assuming it did not.

**Closing a tab that has no path.** `close_file(name="...")` (partial, case-insensitive) or
`close_file(index=N)` closes that tab; with none of `path`, `name`, `index` it closes the
active tab. `run_command` with `command="close"` and `scope="view"` returns ok and closes
nothing.

## More

The 160 tools generated from Sublime's command list, what each was observed to do, and
known issues are in `docs/COMMAND_TOOLS.md` in the repository.

