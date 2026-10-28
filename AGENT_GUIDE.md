# Agent Guide for sublime-mcp (MCP Commander)

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

Close that tab without saving. Name the tab (an untitled tab's name is its first line); a name that fits
several tabs is refused and lists them. Throwing away unsaved text asks the person first:

```
batch(calls=[{"tool": "close_file", "args": {"name": "pear", "discard": true}}])
```

- `insert` types at the cursor, so calling it twice puts the text in twice.
- Case commands (`upper_case`, `lower_case`, `title_case`, `swap_case`) act on the
  selection: `select_all` first. `sort_lines` sorts the whole buffer when nothing is selected.
- `get_active_file` returns untitled tabs too (`path` is null). It cuts `content` at 20000 characters
  (`truncated: true`, `size` gives the full length); pass `max_chars` for more, or read a part with
  `get_view_chars`.
- `close_file` on a modified tab without `discard` opens a native "Save Changes?" dialog that blocks
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
they also need `save_file`. `create` does not make missing folders, and `save_file` into a missing folder is
refused with an error (it used to answer ok while Sublime showed an "Unable to save" dialog); the result says
`saved: true`, or `saved: false` with `pending: true` when the tab is still modified after 1.5 s (a Save As or
error dialog, or a read-only file). `get_sheets` and `get_open_files` add `disk_differs: true` to a tab that
reads as clean but holds an empty buffer for a file that has content on disk: Sublime then counts the buffer as
modified and asks "Save changes?" on close. To open an existing file use
the hidden tool `open_file(path=...)`; it returns once the file is loaded and is the active tab
(`active: true`), or says `pending: true` after 3 s when it is not yet.

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

- Disk `edit`/`write` on a file ST has open → `revert_file(name=...)` (or `index`) so the buffer reloads;
  it asks the person first, and a name that fits several tabs is refused.
- Short plain text into an empty tab: `insert` is fine. Indented or large multi-line
  content: use `replace_lines(begin, end, text)`, because `insert` (and
  `view.run_command("insert", ...)`) auto-indents every line and piles indentation.
- `str_replace` `old_str` must match **exactly once**.
- Commands: `str_replace`, `insert` (after 1-based `insert_line`; `0` = start),
  `create`, `view`.

## Closing tabs

A dirty view makes `close_file` open ST's save prompt. Save first, or pass `discard: true`
(it asks the person). Always give `name` (or `index`, or `path`): with none of them `close_file`
closes the ACTIVE tab, which the person may be typing in. A `name` that fits several tabs is
refused with the list of matches. The result says `closed: true` once the tab is gone. `closed: false` with
`pending: true` means it is still open after 1.5 s because Sublime is asking "Save changes before closing?" (this
can happen even when `get_sheets` says `is_dirty: false`, for example a file that was created after its tab was
opened) or a host hook refused the close. Do not repeat the call: each repeat raises another dialog. Answer the
first dialog (Windows: `list_native_windows`, `dismiss_native_window`; WSL/Linux: on screen).

## eval_python

Asks the person first (see "Destructive tools ask the person first"); prefer a dedicated tool.
Runs in ST's plugin host. Use `print(expr)` — top-level `return` is a syntax
error; bare expressions produce no output. In scope: `sublime`, `window`,
`view`. Timeout is 5s (main-thread).

`eval_python_latest` is **system** Python on PATH, not the ST host — no
`sublime`/`window`/`view`.

## Common tools

```
get_active_file()                  # path, content (first 20000 chars), 1-based line/col, is_dirty, syntax
get_cursor_context(lines=10)       # ±N lines, numbered
get_selection()                    # highlighted text
get_sheets()                       # every tab: stable id, group/index, selection/focus, path/name
get_sheet_content(index=2)         # untitled / scratch / terminal tabs too
open_file(path=..., line=42, col=1)
save_all()
revert_file(name="notes.txt")      # asks the person; name or index, else the active view
project_search(pattern=..., where=...)  # ST Find-in-Files, structured matches
discover_tools()                        # categories; see "Finding tools"
get_commands()                     # command ids, scopes, packages, palette captions
```

`project_search` `where` accepts folder paths, `*.py`, `-*.md`, `${project}`,
`${open_files}`, `${folder:Name}`.

## Typing into a GhostShell terminal tab (a shell, Claude Code and other agent CLIs)

GhostShell has no command for sending text into a terminal tab (removed 2026-10-19: `ai_terminal_send_string`,
`ai_terminal_send_string_window`, `ai_terminal_queue_input`, `ai_terminal_queue_input_to`). Do it the way a person does:
select the tab, type, read it back, go back to your own tab. Tested 2026-10-19 on build 4200 with a `cmd.exe` tab:

```
get_sheets(settings=false)                       # find the target sheet id and your own (the focused one)
batch(calls=[
  {"tool": "focus_sheet", "args": {"id": <target id>}},
  {"tool": "ui_type_text", "args": {"text": "echo hello\n"}},   # a newline is sent as Return
  {"tool": "focus_sheet", "args": {"id": <your own id>}}])
get_sheet_content(index=<target index>)          # quote the echoed line and its output
```

- **Guard the focus.** Sheet ids change when Sublime restarts (tested 2026-10-19: the cmd tab went from id 284 to 12), so
  call `get_sheets` in the same turn. Run `focus_sheet` first and check it did not return an error and that
  `get_sheets(settings=false)` shows the target with `is_focused: true` before typing anything (not `eval_python`: it
  asks the person on every call). A `focus_sheet` on a stale id
  returned "sheet id 284 not found", and nothing was typed.
- **`ok` is not proof.** `ui_type_text` types into whichever tab is active in the window; if the `focus_sheet` before it
  did not select the target, the text goes to the wrong tab (possibly your own session) and still returns ok. Read the
  target tab back with `get_sheet_content` and quote the line before saying it was sent.
- **Leave the line for the person to press Enter** (for example `npm publish`, which asks for browser authentication):
  type the text with no trailing newline, read it back, then tell them to press Enter in that tab.
- **A cmd.exe tab takes `ui_type_text` as typed.** UNVERIFIED for Claude Code tabs: Claude Code reads a burst of text as a
  paste and takes an Enter in the same read, or within about 100 ms after it, as part of the paste (text of 60 characters
  or fewer still submitted; 120 or more stayed in the box, measured 2026-10-17). For such a tab type the text with no
  newline, then send the Return as its own `ui_press_key` (`key="Return"`, `method="post"`) at least 300 ms later.
- **Escape: do not type a raw `\x1b`.** Use `ui_press_key` with `method="post"` (`Escape`, `Return`, arrows).
- `cls` in a cmd.exe tab clears the tab text that `get_sheet_content` returns (tested: 183 characters left), so read
  what you need first.
- A string typed before the shell has printed its prompt is dropped. After `ai_terminal_open_here` wait a few seconds, and
  confirm the prompt with a screenshot before typing.

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

- **Delete files and folders:** both ask the person first (see "Destructive tools ask the person
  first"). Pass `files` to `delete_file` and `dirs` (a list) to
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
  Sublime's own output (load errors such as a plugin's SyntaxError, and anything printed by
  Python 3.3-host plugins). `mode="visible"` returns the whole console (the last 200 lines by
  default; `tail=N` for N lines, `tail=0` for all; the result says `lines_total` and
  `truncated`). It clicks into the console and copies it, so the window must be in front; if it
  is not, it fails at once with a clear message and changes nothing. Pass `force_focus=true` on
  every visible call to raise the window first. A read then takes about 150 ms (measured on
  Windows 11, 2026-10-19: 99 of 100 reads on portable 4215 and 92 of 100 on 4200 succeeded; the
  rest were focus refusals that sent no input; no wrong text). Do not fall back to opening the
  panel with `show_panel` and reading the screen.
- **When the raise is refused.** Windows lets a process take the foreground only if it received
  the last input event, started the foreground process, or the foreground lock timeout has
  expired. So the first raise on a freshly started Sublime usually fails, and a raise also fails
  while the user is typing or clicking in another window. The error says "could not give the
  Sublime Text window the keyboard focus; no input was sent": nothing was sent, so call again a
  moment later. Later raises on the same instance succeed because the click and keys of the
  previous capture count as input.
- **Crash history (do not repeat it as fact).** On 2026-10-04 a loop that killed and relaunched
  portable 4200 for each capture (12 per variant) crashed it 2 times in 12 with the raise used
  here (CoreMessaging.dll), and 5 to 8 times in 12 with variants that attach thread input; those
  logs were not kept. On 2026-10-19 about 1,000 raises on portables 4200 and 4215, long-running
  and freshly relaunched, gave no crash and no new dump file. The cause of the earlier crashes
  is unknown, and no crash of the user's main Sublime from `force_focus` has been recorded.
  The two dumps on hand (4200 on 2026-10-16, 4215 on 2026-10-18; read with `cdbX64.exe`, no
  symbols) are both access violations on a Sublime worker thread, every frame in
  `sublime_text.exe`: a read of address 0x8 (null object) on 4200 and a jump to a data address
  on 4215. No frame is in user32, the clipboard, Python or a plugin, and the dumps carry no
  mark of `get_console`, so nothing ties them to `force_focus`.
- **The console is only partly readable.** `get_console` in the default and `captured` modes
  misses Sublime's own error output (tracebacks printed after an install, `ImportError`).
  `get_output_panel` for the console is the same as `get_console` in the default mode, so it
  also misses those errors when the window is not in front. A visible capture that succeeds
  prints one "[sublime-mcp] console capture marker" line into the console; one that fails for
  lack of focus leaves nothing behind.

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
  They see panels opened by packages in Sublime's Python 3.8 host. Older packages (no
  `.python-version`) run in the 3.3 host: those panels are visible only when the user has set
  `"install_py33_helper": true` in `MCP Commander.sublime-settings` (off by default; it makes
  sublime-mcp write a small package, "MCP Commander Py33", into Packages, which records them;
  the error says so when it is off); the command palette and
  Goto Anything give an error, and then the keyboard is the only way. Picking runs the package's own callback, so pick only items you mean to run (some
  pickers open files, folders or browser tabs). If the callback of a
  3.3-host package raises a modal dialog (Jekyll's remove commands: "Confirm Delete"),
  `pick_quick_panel` answers `{ok: true, pending: true, note: ...}` after 2 s: the pick went
  through, the dialog is open and blocks Sublime. Answer it with `list_native_windows` and
  `dismiss_native_window` (or Return on its hwnd), then check the result. `drive_input_panel` only fills input panels.
  **The package manager's Install Package / Remove Package lists take up to ~15 s to appear after
  Enter** (the status bar says "Loading packages..."): pass `wait_ms` (at most 60000) to
  `pick_quick_panel` or `get_quick_panel`, for example `pick_quick_panel(text="Bicep",
  wait_ms=30000)`, and the call waits for the panel instead of failing with "no recorded quick
  panel". Without `wait_ms` that error carries a hint.
- **What a highlighting plugin drew:** `get_view_regions(key="ifdef")` returns the regions stored
  with `view.add_regions(key, ...)` (begin, end, first 80 characters); name several keys with
  commas. Sublime cannot list the keys, so read the plugin's source for them. Built-in example:
  after `toggle_bookmark`, key `bookmarks`.
- **A tab drawn with phantoms** (GhostShell's omp tab: the buffer is only blank lines, the content is
  in hundreds of phantoms): `get_view_phantoms(name="omp", html=false, last=20, max_chars=500)`
  returns the newest panels as plain text. Without `html=false` and `last` the answer is about
  290 KB. It works for any package that lists its `PhantomSet` in a module-level `_phantom_sets`
  dict (view id to set); GhostShell does since 2026-10-14.
- **Syntax names:** `get_active_file` and `get_sheets` give `syntax` (the name, or the file name
  when the syntax file has no `name:` line, as with Bicep) and `get_active_file` also gives
  `syntax_path`. A view whose syntax was set through a legacy path (`Packages/CSS/CSS.tmLanguage`,
  which old Python 3.3 packages use) has no `view.syntax()` in the API although Sublime shows it;
  both tools then report it from the view's `syntax` setting (`syntax: "CSS"`, `syntax_path` the
  legacy path) instead of `null`.
- **`focus_sheet` echo:** it returns the sheet without its view settings (they were about 7 KB on
  every call); pass `settings: true` to get them, as `get_sheets` does.
- **Scope names differ between Sublime builds.** In build 4200 the C syntax scopes `#ifdef` as
  `keyword.control.import`; in 4215 it is `keyword.control.directive.conditional`. A package that
  selects by scope can work on one build and do nothing on the other: check the scopes with
  `get_scope_at_cursor` on the build the user runs before calling it a defect.
- **PowerShell pipes add a byte-order mark.** `Get-Content file | tool -` feeds the tool a BOM and
  tools that read stdin may report a parse error; redirect the file instead (`tool - < file`)
  from Bash or cmd.
- **`exit`** replies first and closes Sublime 300 ms later, so the call returns `ok` and the
  connection then drops (restart, then reconnect the server).

## Destructive tools ask the person first

These calls do not run until the person says yes: `delete_file`, `delete_folder`, `revert`,
`revert_file`, `close_window`, `close_workspace`, `remove_folder`, `exit`, `eval_python`, `close_file`
with `discard`, and `run_command` of any of those commands. Inside a `batch`, one such call makes the
whole batch ask once, before any call of it runs.

- Your client shows an Accept / Decline question (Claude Code: in the terminal) and repeats the call
  for you. You see only the final result. Nothing is changed before the person accepts.
- A result starting **"Denied, nothing was changed"** means the person declined, or your client cannot be
  asked. Do not retry, rename an argument, or reach the same effect through another tool or `eval_python`.
  Tell the person what you wanted to do and why.
- Pick the right target before asking: the question names the target, and a vague name (`close_file name="test"`
  matches the first tab containing "test") can ask about the wrong tab.
- The setting `require_consent_for_destructive` turns this off (read at plugin start); it is on by default.
  The direct HTTP bridge cannot ask, so it refuses these calls outright (403, "Denied, nothing was
  changed"); `eval_python` stays open there.

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
- **Before closing several tabs:** call `close_file` once per tab with its `name`, or use the `close_all`
  command; do not call `Sheet.close()` repeatedly in one `eval_python` call.
- **"This is an unregistered copy" dialog:** Sublime shows this purchase reminder now and then, for example
  after a save. Read it, then close it with `dismiss_native_window`.
- **`goto_definition`, `goto_reference`, `auto_complete_goto_definition`** use Sublime's symbol index, which
  needs `index_files` true. `lookup_symbol` searches the open files.
- **Macros:** play a `.sublime-macro` file with `run_macro_file` (file="Packages/User/name.sublime-macro").
  `toggle_record_macro` records keys typed by a person.
- `ui_click`, `ui_hover` and `ui_press_key` with `method="input"` need the target window uncovered and the
  person at the keyboard idle for `min_idle_s` (default 8); pass `wait_idle_s` (up to 120) to wait, or a
  smaller `min_idle_s`. `ui_press_key` with the default `post` method needs neither.

## When a native dialog blocks Sublime (Linux, macOS, WSL)

`list_native_windows` and `dismiss_native_window` are Windows only, so off Windows a dialog shows up as
"main-thread timeout after 5s" (the message says so) and only the person, or a computer-use client, can answer it.
Under WSL (WSLg) a computer-use client sees each dialog as its own window titled " (Ubuntu)": `list_apps`,
`get_window_state` with an image snapshot shows the message (read it, it is often the finding), then `click` at the
button's position in the picture. Tools that do not need the main thread (`get_console`, `get_help`) keep
answering. Seen on the WSL Sublime 4215: Save Changes, Unable to save, Error loading syntax file, and a package's
own "cannot find perltidy" message. Do not repeat a call that raised a dialog before you have answered it.

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
`close_file(index=N)` closes that tab (a name that fits several tabs is refused, with the list);
with none of `path`, `name`, `index` it closes the active tab, so always name the tab. `run_command` with `command="close"` and `scope="view"` returns ok and closes
nothing.

## More

The 160 tools generated from Sublime's command list, what each was observed to do, and
known issues are in `docs/COMMAND_TOOLS.md` in the repository.

