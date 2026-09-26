"""GENERATED FILE - do not edit. Produced by tools/generate_fallback_catalog.py from sublime_mcp.py::_MCP_TOOLS. Regenerate after changing the backend tool catalog."""

TOOLS = [   {   'name': 'add_directory',
        'description': "Opens an OS dialog box to prompt for a folder to the 'Where' field in the "
                       "'Find in Files' panel. (WindowCommand)",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'add_folder',
        'description': 'Add a folder to the current project.',
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string'}},
                           'required': ['path']}},
    {   'name': 'add_jump_record',
        'description': 'Allows packages/plugins to add a jump point without changing the '
                       'selection. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'selection': {   'description': 'The selection to be '
                                                                             'added to the jump '
                                                                             'history. Can be an '
                                                                             'integer, a list of 2 '
                                                                             'integers or a list '
                                                                             'of list of 2 '
                                                                             'integers.'}}}},
    {   'name': 'add_missing_newline',
        'description': 'Alias of ensure_newline_at_eof — add a trailing newline at EOF if absent.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'add_to_kill_ring',
        'description': 'Add the current selection to the kill ring (TextCommand, used by yank).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'add_where_snippet',
        'description': "Adds a snippet to the 'Where' field in the 'Find in Files' panel. "
                       '(WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'snippet': {   'type': 'string',
                                                            'description': 'The string to be '
                                                                           'inserted into the '
                                                                           "'Where' field in the "
                                                                           "'Find in Files' panel. "
                                                                           'Supports snippet like '
                                                                           'variables.'}}}},
    {   'name': 'add_word',
        'description': "Adds the given word to the 'added_words' setting in the user preferences. "
                       '(TextCommand) Observed on Sublime Text 4215: writes Sublime Text settings.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'word': {   'type': 'string',
                                                         'description': 'The word to be added.'}}}},
    {   'name': 'append',
        'description': 'Appends the given text string to the end of the buffer. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'characters': {   'type': 'string',
                                                               'description': 'The string to be '
                                                                              'appended to the end '
                                                                              'of the text '
                                                                              'buffer.'},
                                             'force': {'type': 'boolean'},
                                             'scroll_to_end': {   'type': 'boolean',
                                                                  'description': 'Whether to '
                                                                                 'scroll to the '
                                                                                 'end of the '
                                                                                 'buffer after '
                                                                                 'appending.'},
                                             'disable_tab_translation': {   'type': 'boolean',
                                                                            'description': 'Whether '
                                                                                           'to '
                                                                                           'disable '
                                                                                           'translating '
                                                                                           'tabs '
                                                                                           'to '
                                                                                           'spaces.'}}}},
    {   'name': 'arithmetic',
        'description': 'Evaluate the selected expression as arithmetic and replace it with the '
                       "result (TextCommand). Select '2+2' to get '4'.",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'auto_complete',
        'description': 'Shows the auto completion popup. (TextCommand) Observed on Sublime Text '
                       '4215: shows an in-app panel, popup or overlay (dismiss with hide_overlay, '
                       'hide_panel or hide_popup).',
        'inputSchema': {   'type': 'object',
                           'properties': {   'api_completions_only': {   'type': 'boolean',
                                                                         'description': 'Whether '
                                                                                        'to '
                                                                                        'include '
                                                                                        'completions '
                                                                                        'from '
                                                                                        'snippets/completions '
                                                                                        'file in '
                                                                                        'the AC '
                                                                                        'panel.'},
                                             'disable_auto_insert': {'type': 'boolean'},
                                             'next_completion_if_showing': {'type': 'boolean'},
                                             'auto_complete_commit_on_tab': {'type': 'boolean'},
                                             'mini': {'type': 'boolean'},
                                             'default': {'type': 'string'}}}},
    {   'name': 'auto_complete_goto_definition',
        'description': 'Auto-complete and goto the definition of the symbol under the cursor '
                       '(TextCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'auto_complete_open_link',
        'description': 'Opens the first link in the details pane of the AC panel, when the AC '
                       'panel is visible. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'auto_complete_prev',
        'description': 'Goes to the previous entry in the AC panel, when the AC panel is visible. '
                       '(TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'auto_indent',
        'description': 'Apply auto-indentation to the current selection(s) using the active '
                       "syntax's indentation rules.",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'auto_indent_tag',
        'description': 'Re-indent the enclosing HTML/XML tag structure (TextCommand). Useful for '
                       'fixing nested tag indentation.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'batch',
        'description': 'Run multiple sublime-mcp tool calls in a single request instead of paying '
                       'a\n'
                       'separate HTTP round trip per call. Each call still does its own '
                       'main-thread\n'
                       'work independently: the batch is not wrapped in one shared main-thread\n'
                       'dispatch, so a slow or polling call cannot freeze the UI for the rest of\n'
                       'the batch. Use this whenever you need more than one piece of editor state\n'
                       'at once (e.g. get_active_file + get_selection + get_cursor_context), or\n'
                       'want to chain several edits/reads together.\n'
                       'calls: list of {tool: <tool name>, args: <object, optional>}. Cannot call '
                       "'batch' itself.\n"
                       'Max 50 calls per batch.\n'
                       'Returns {results: [...]} — one entry per call, in order; failed calls '
                       'return {error: ...}\n'
                       'instead of aborting the whole batch.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'calls': {   'type': 'array',
                                                          'maxItems': 50,
                                                          'items': {   'type': 'object',
                                                                       'properties': {   'tool': {   'type': 'string'},
                                                                                         'args': {   'type': 'object'}},
                                                                       'required': ['tool']}}},
                           'required': ['calls']}},
    {   'name': 'build',
        'description': 'Executes the provided build system or prompt for selection (select: true) '
                       'and choose a default. build_system should be a resource path to a build '
                       'system file or the name of a project-specific build system. '
                       '(WindowCommand) Observed on Sublime Text 4215: when given arguments: shows '
                       'an in-app panel, popup or overlay (dismiss with hide_overlay, hide_panel '
                       'or hide_popup).',
        'inputSchema': {   'type': 'object',
                           'properties': {   'select': {   'type': 'boolean',
                                                           'description': 'Whether to prompt for '
                                                                          'selecting a build '
                                                                          'system.'},
                                             'build_system': {   'type': 'string',
                                                                 'description': 'A resource path '
                                                                                'to a '
                                                                                '.sublime-build '
                                                                                'file.'},
                                             'variant': {   'type': 'string',
                                                            'description': 'The name of the '
                                                                           'variant present in the '
                                                                           'build system as '
                                                                           'specified by the '
                                                                           "'name' key."},
                                             'choice_build_system': {'type': 'boolean'},
                                             'choice_variant': {'type': 'boolean'}}}},
    {   'name': 'cancel',
        'description': "Runs the Sublime Text 'cancel' command. (WindowCommand)",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'cancel_build',
        'description': 'Cancels the currently running build. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'cancel_find',
        'description': 'Cancels the Find panel, closing it. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'chain',
        'description': 'Runs a given set of command(s) sequentially, along with their argument(s) '
                       'if any. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'commands': {   'description': 'The list of commands '
                                                                            'and their respective '
                                                                            'arguments.'}}}},
    {   'name': 'clear_bookmarks',
        'description': 'Clear all bookmarks in the active view.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'clear_fields',
        'description': 'Clear the current snippet field highlights (used after inserting a snippet '
                       'with $1/$2 tab stops).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'clear_location',
        'description': "Clears the 'Where' field in the Find in Files panel. (WindowCommand)",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'clear_missing_recent_projects_and_workspaces',
        'description': 'Clears any deleted projects or workspaces from the session. '
                       '(WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'clear_recent_files',
        'description': 'Clears the list of recently opened files. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'clear_recent_projects_and_workspaces',
        'description': 'Clears the list of recently opened projects and workspaces. '
                       '(WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'clone_file',
        'description': 'Create a clone of the active view (opens the same file in a new tab, '
                       'sharing the buffer).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close',
        'description': 'Closes the active view. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_all',
        'description': 'Close all open files/views in the current window.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_by_index',
        'description': "Closes a view of the given group by it's index. (WindowCommand)",
        'inputSchema': {   'type': 'object',
                           'properties': {   'group': {   'type': 'integer',
                                                          'description': 'The index of the target '
                                                                         'group.'},
                                             'index': {   'type': 'integer',
                                                          'description': 'The index within the '
                                                                         'target group.'}}}},
    {   'name': 'close_deleted_files',
        'description': 'Closes all views into deleted files. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'group': {   'type': 'integer',
                                                          'description': 'The index of the target '
                                                                         'group.'}}}},
    {   'name': 'close_file',
        'description': 'Close a file by path, or close the active file if path is omitted. Routed '
                       "through Sublime's real close command (not a direct API call), so a "
                       "host-side close-blocking hook gets a chance to run -- e.g. GhostShell's "
                       'ai_terminal package refuses this outright (no dialog, just a no-op) for '
                       'any ai_terminal tab, so calling this on one does nothing rather than '
                       'closing it. Only ever targets an already-open view found by path or the '
                       'current active view -- it cannot target an unsaved/path-less tab (like an '
                       'ai_terminal tab) by index; do not call this expecting it to close '
                       "'whatever tab you mean' when no path resolves.",
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string', 'default': ''}}}},
    {   'name': 'close_folder_list',
        'description': 'Removes all the folder(s) from the sidebar and hides it. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_other_tabs',
        'description': 'Alias of close_others — close all views in the current group except the '
                       'active one.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_others',
        'description': 'Close all views in the current group except the active one (Close Other '
                       'Tabs).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_others_by_index',
        'description': 'Closes all views of a group but the one identified by group and index. '
                       '(WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'group': {   'type': 'integer',
                                                          'description': 'The index of the target '
                                                                         'group.'},
                                             'index': {   'type': 'integer',
                                                          'description': 'The index within the '
                                                                         'target group.'}}}},
    {   'name': 'close_pane',
        'description': 'Close the current pane/group and all views inside it.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_selected',
        'description': 'Closes all selected views in a group. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'group': {   'type': 'integer',
                                                          'description': 'The index of the target '
                                                                         'group.'},
                                             'index': {   'type': 'integer',
                                                          'description': 'The index within the '
                                                                         'target group.'}}}},
    {   'name': 'close_tag',
        'description': 'Close an HTML/XML tag. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {'insert_slash': {'type': 'boolean'}}}},
    {   'name': 'close_to_right_by_index',
        'description': 'Closes all views of a group right of the one identified by index. '
                       '(WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'group': {   'type': 'integer',
                                                          'description': 'The index of the target '
                                                                         'group.'},
                                             'index': {   'type': 'integer',
                                                          'description': 'The index within the '
                                                                         'target group.'}}}},
    {   'name': 'close_transient',
        'description': 'Close all transient views (preview tabs) in the current window.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_unmodified',
        'description': 'Close all unmodified (clean) views in the current window.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_unmodified_to_right_by_index',
        'description': 'Closes all unmodified views of a group right of the one identified by '
                       'index. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'group': {   'type': 'integer',
                                                          'description': 'The index of the target '
                                                                         'group.'},
                                             'index': {   'type': 'integer',
                                                          'description': 'The index within the '
                                                                         'target group.'}}}},
    {   'name': 'close_unselected',
        'description': 'Closes all unselected views in a group. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'group': {   'type': 'integer',
                                                          'description': 'The index of the target '
                                                                         'group.'},
                                             'index': {   'type': 'integer',
                                                          'description': 'The index within the '
                                                                         'target group.'}}}},
    {   'name': 'close_window',
        'description': 'Closes the active window. (WindowCommand) Observed on Sublime Text 4215: '
                       'quits Sublime Text (which also stops this MCP server).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_workspace',
        'description': 'Closes the active workspace. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'commit_completion',
        'description': 'Inserts the selected completion into the text and closes the AC panel. '
                       '(TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'console_python_version',
        'description': 'Switches the python interpreter version in console input. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'version': {   'type': 'string',
                                                            'description': 'The version of the '
                                                                           'python interpreter. '
                                                                           "Valid values are '3.3' "
                                                                           "or '3.8'."}}}},
    {   'name': 'context_menu',
        'description': 'Shows the context menu for the current view. (WindowCommand) Observed on '
                       'Sublime Text 4215: opens a native OS window ("native menu") that blocks '
                       "Sublime's main thread until a person dismisses it.",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'convert_color_scheme',
        'description': 'Convert a .sublime-color-scheme file to JSON for editing (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'convert_ident_case',
        'description': 'Convert the identifier under the cursor to a different case style '
                       "(TextCommand). Args: 'case' (lower/title/upper), 'separator' (e.g. '_' for "
                       "snake_case, '-' for kebab-case), 'first_case' (lower/upper for first "
                       'letter in title case).',
        'inputSchema': {   'type': 'object',
                           'properties': {   'case': {   'type': 'string',
                                                         'description': "Target case: 'lower', "
                                                                        "'title', or 'upper'."},
                                             'separator': {   'type': 'string',
                                                              'description': 'Word separator '
                                                                             'inserted between '
                                                                             "words, e.g. '_' for "
                                                                             "snake_case, '-' for "
                                                                             'kebab-case. Empty '
                                                                             'for camelCase.'},
                                             'first_case': {   'type': 'string',
                                                               'description': "When case='title', "
                                                                              'the case of the '
                                                                              'first letter: '
                                                                              "'lower' "
                                                                              '(lowerCamelCase) or '
                                                                              "'upper' "
                                                                              '(UpperCamelCase).'}}}},
    {   'name': 'convert_syntax',
        'description': 'Convert a .tmLanguage syntax file to .sublime-syntax (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'copy',
        'description': 'Copy the current selection(s) to the clipboard.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'copy_as_html',
        'description': 'Copies the contents of the current view as rich HTML to the system '
                       'clipboard. (TextCommand) Observed on Sublime Text 4215: changes the '
                       'clipboard.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'enclosing_tags': {'type': 'boolean'},
                                             'font_size': {'type': 'boolean'}}}},
    {   'name': 'copy_path',
        'description': "Copy the active file's path to the clipboard (WindowCommand).",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'correct_spelling',
        'description': "Corrects the incorrectly spelled word based on the incorrect word's region "
                       'and the correction. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'begin': {   'type': 'integer',
                                                          'description': 'The integer that '
                                                                         'represents the beginning '
                                                                         'of the region that spans '
                                                                         'the incorrect word.'},
                                             'end': {   'type': 'integer',
                                                        'description': 'The integer that '
                                                                       'represents the end of the '
                                                                       'region that spans the '
                                                                       'incorrect word.'},
                                             'correction': {   'type': 'string',
                                                               'description': 'The string to be '
                                                                              'placed as a '
                                                                              'correction for the '
                                                                              'incorrect word.'}}}},
    {   'name': 'customize_color_scheme',
        'description': 'Open the active color scheme for customization (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'customize_theme',
        'description': 'Open the active theme for customization (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'cut',
        'description': 'Cut the current selection(s) to the clipboard.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'decrease_font_size',
        'description': 'Increases the global font size. (ApplicationCommand) Observed on Sublime '
                       'Text 4215: writes Sublime Text settings.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'delete_file',
        'description': 'Deletes the given file(s) by moving the file(s) to the system '
                       'trash/recycle bin. (WindowCommand) Observed on Sublime Text 4215: when '
                       'given arguments: opens a native OS window ("Delete File") that blocks '
                       "Sublime's main thread until a person dismisses it.",
        'inputSchema': {   'type': 'object',
                           'properties': {   'files': {   'type': 'array',
                                                          'description': 'The absolute path(s) to '
                                                                         'the given file(s) on '
                                                                         'disk.'},
                                             'prompt': {   'type': 'boolean',
                                                           'description': 'Whether to prompt the '
                                                                          'user to confirm the '
                                                                          'deletion by showing a '
                                                                          'dialog box.'}}}},
    {   'name': 'delete_folder',
        'description': 'Deletes the given folder(s) by moving the folder(s) to the system trash '
                       'bin. (WindowCommand) Observed on Sublime Text 4215: when given arguments: '
                       'opens a native OS window ("Delete Folder") that blocks Sublime\'s main '
                       'thread until a person dismisses it.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'dirs': {   'type': 'array',
                                                         'description': 'The absolute path(s) to '
                                                                        'the given folder(s) on '
                                                                        'disk.'},
                                             'prompt': {   'type': 'boolean',
                                                           'description': 'Whether to prompt the '
                                                                          'user to confirm the '
                                                                          'deletion by showing a '
                                                                          'dialog box.'}}}},
    {   'name': 'delete_to_mark',
        'description': 'Delete the text between the cursor and the previously set mark '
                       '(TextCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'delete_word',
        'description': 'Deletes the (sub-)word in front of or after each caret. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'forward': {   'type': 'boolean',
                                                            'description': 'Whether the forward '
                                                                           '(sub-)word should be '
                                                                           'deleted.'},
                                             'sub_words': {   'type': 'boolean',
                                                              'description': 'Whether to delete '
                                                                             'subwords.'}}}},
    {   'name': 'detect_indentation',
        'description': "Auto-detect the file's indentation style (tabs vs spaces, width) and set "
                       "the view's indent settings accordingly.",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'diagnostics',
        'description': 'One-call plugin health snapshot: main-thread heartbeat freshness (and a '
                       'likely_wedged flag), the currently in-flight _on_main dispatch (if any) '
                       'with its label and running time, console-capture buffer size, and a live '
                       "main-thread stack trace. Answers 'wedged vs slow vs fine' without needing "
                       "the main thread's cooperation -- use this before assuming a timeout means "
                       'the server is dead.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'discover_tools',
        'description': 'Search advanced Sublime capabilities hidden from the default tool surface. '
                       'Returns matching names, descriptions, and schemas. Invoke a result through '
                       'batch(calls=[{tool: <name>, args: {...}}]), including for a single call.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'query': {   'type': 'string',
                                                          'description': 'Capability to find, such '
                                                                         'as bookmarks, tabs, '
                                                                         'syntax, or commands.'},
                                             'limit': {'type': 'integer', 'default': 10}},
                           'required': ['query']}},
    {   'name': 'dismiss_native_window',
        'description': 'Dismiss a native dialog or menu of this Sublime Text process (Windows '
                       "only), even while it has blocked Sublime's main thread. action: 'cancel' "
                       "(default; clicks Cancel/No or closes), 'ok' (clicks OK/Yes/the default "
                       "button), 'button' (click the button named in 'button') or 'close'. hwnd "
                       'defaults to the first dialog, then the first menu; take it from '
                       'list_native_windows. Acts only on windows of the Sublime Text process. '
                       "'ok' clicks OK/Yes/the default button.",
        'inputSchema': {   'type': 'object',
                           'properties': {   'hwnd': {   'type': 'integer',
                                                         'description': 'Window handle from '
                                                                        'list_native_windows '
                                                                        '(default: first dialog, '
                                                                        'then first menu).'},
                                             'action': {   'type': 'string',
                                                           'enum': [   'cancel',
                                                                       'ok',
                                                                       'button',
                                                                       'close'],
                                                           'description': 'What to do (default: '
                                                                          'cancel).'},
                                             'button': {   'type': 'string',
                                                           'description': 'Button label for action '
                                                                          "'button' (ignores case "
                                                                          'and & mnemonics).'}}}},
    {   'name': 'drag_select',
        'description': "Runs the Sublime Text 'drag_select' command. (TextCommand)",
        'inputSchema': {   'type': 'object',
                           'properties': {   'by': {   'type': 'string',
                                                       'description': 'The mode of selection. '
                                                                      "Valid values are 'words', "
                                                                      "'columns' and 'lines'."},
                                             'event': {   'type': 'object',
                                                          'description': 'An object that consists '
                                                                         'of the x & y window '
                                                                         'coordinates & the button '
                                                                         'detail via the button '
                                                                         'key.'},
                                             'additive': {   'type': 'boolean',
                                                             'description': 'Whether to add the '
                                                                            'selection to the '
                                                                            'existing '
                                                                            'selection(s).'},
                                             'subtractive': {   'type': 'boolean',
                                                                'description': 'Whether to remove '
                                                                               'the existing '
                                                                               'selection(s) '
                                                                               'before adding the '
                                                                               'new selection.'}}}},
    {   'name': 'drive_input_panel',
        'description': "Fill and/or submit or cancel Sublime's currently open input panel "
                       "(window.show_input_panel), e.g. a package's 'Enter a path...' prompt.\n"
                       'Input panels have no reachable View through normal APIs and Enter is a '
                       'native keybinding, not a scriptable insert -- this reaches both, and works '
                       'even when the panel belongs to a legacy Python 3.3-hosted package in a '
                       "different plugin_host process, since it drives the panel through Sublime's "
                       "own built-in commands rather than that package's code.\n"
                       "text (optional): replace the panel's current content before acting. "
                       "action: 'submit' (default, fires on_done) or 'cancel' (fires on_cancel). "
                       'Errors if no input panel is currently open.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'text': {'type': 'string'},
                                             'action': {'type': 'string', 'default': 'submit'}}}},
    {   'name': 'duplicate_line',
        'description': 'Duplicate the current line(s) in the active file.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'echo',
        'description': "Print a debug message to the ST console (ApplicationCommand). Pass 'msg'.",
        'inputSchema': {   'type': 'object',
                           'properties': {'msg': {'type': 'string'}},
                           'required': ['msg']}},
    {   'name': 'edit_settings',
        'description': 'Open the given settings resource for editing (WindowCommand). Pass '
                       "'resource' (e.g. 'Preferences').",
        'inputSchema': {   'type': 'object',
                           'properties': {'resource': {'type': 'string'}},
                           'required': ['resource']}},
    {   'name': 'edit_syntax_settings',
        'description': 'Open the syntax-specific settings file (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'encode_html_entities',
        'description': "Runs the Sublime Text 'encode_html_entities' command. (TextCommand)",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'ensure_newline_at_eof',
        'description': 'Ensure the file ends with a single trailing newline (add one if missing).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'eval_python',
        'description': "Execute arbitrary Python in Sublime Text's main thread.\n"
                       "Locals: sublime, window, view, print. Returns captured stdout in 'output'.",
        'inputSchema': {   'type': 'object',
                           'properties': {'code': {'type': 'string'}},
                           'required': ['code']}},
    {   'name': 'eval_python_latest',
        'description': 'Execute Python code using the system Python interpreter outside Sublime '
                       "Text's embedded sandbox.\n"
                       'Returns stdout, stderr, and returncode.',
        'inputSchema': {   'type': 'object',
                           'properties': {'code': {'type': 'string'}},
                           'required': ['code']}},
    {   'name': 'exec',
        'description': "Run a build system target via the exec command (WindowCommand). Pass 'cmd' "
                       "(list) and optional 'working_dir', 'shell_cmd', 'env', etc.",
        'inputSchema': {   'type': 'object',
                           'properties': {   'cmd': {'type': 'array', 'items': {'type': 'string'}},
                                             'working_dir': {'type': 'string'},
                                             'shell_cmd': {'type': 'string'},
                                             'env': {'type': 'object'}}}},
    {   'name': 'exit',
        'description': 'Closes all windows and exists the application. (ApplicationCommand) '
                       'Observed on Sublime Text 4215: quits Sublime Text (which also stops this '
                       'MCP server).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'expand_selection',
        'description': 'Expand the current selection to the next semantic boundary (Ctrl+Shift+A). '
                       'Repeated calls expand further: word → brackets → line → paragraph → scope.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'expand_selection_to_brackets',
        'description': 'Expand the current selection to the enclosing brackets/parens/braces.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'expand_selection_to_indentation',
        'description': 'Expand the current selection to the surrounding indentation block.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'expand_selection_to_paragraph',
        'description': 'Expand the current selection to the surrounding paragraph.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'expand_selection_to_scope',
        'description': 'Expand the current selection to the enclosing syntax scope.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'expand_snippet',
        'description': 'Expands the snippet under the cursor. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'expand_tabs',
        'description': 'Convert leading tabs in the current selection (or whole file) to spaces, '
                       "using the view's tab_size.",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'find_all',
        'description': 'Finds all the tokens which match the find pattern. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'close_panel': {   'type': 'boolean',
                                                                'description': 'Whether to close '
                                                                               'the Find panel '
                                                                               'after executing '
                                                                               'the Find All '
                                                                               'option. This '
                                                                               'argument holds '
                                                                               'good only for the '
                                                                               'Find & Replace '
                                                                               'panel.'}}}},
    {   'name': 'find_all_under',
        'description': 'Searches and selects all text matches, which are the same as the selected '
                       'text or the word under the caret. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'find_and_replace',
        'description': 'Open the single-file Find & Replace panel (Ctrl+H equivalent) on the '
                       'active view, or perform a silent replace_all on it. For multi-file replace '
                       'use replace_in_files. Supports regex with $1/$2 backrefs in replace, '
                       'preserve_case, whole_word, in_selection, and wrap. By default opens the '
                       'panel (show_panel=True); pass replace_all=True and show_panel=False to do '
                       'a silent Replace All without the panel.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'pattern': {'type': 'string'},
                                             'replace': {'type': 'string'},
                                             'case_sensitive': {   'type': 'boolean',
                                                                   'default': False},
                                             'regex': {'type': 'boolean', 'default': False},
                                             'whole_word': {'type': 'boolean', 'default': False},
                                             'preserve_case': {'type': 'boolean', 'default': False},
                                             'in_selection': {'type': 'boolean', 'default': False},
                                             'wrap': {'type': 'boolean', 'default': True},
                                             'show_panel': {'type': 'boolean', 'default': True},
                                             'replace_all': {'type': 'boolean', 'default': False}},
                           'required': ['pattern', 'replace']}},
    {   'name': 'find_in_file',
        'description': 'Find all occurrences of pattern in the active file. Returns list of {line, '
                       'col, text}. Does NOT open a panel — for the interactive Find/Replace panel '
                       'use find_and_replace. Use case_sensitive=True for case-sensitive match, '
                       'regex=True to treat pattern as a regular expression (Python re syntax).',
        'inputSchema': {   'type': 'object',
                           'properties': {   'pattern': {   'type': 'string',
                                                            'description': 'Search string or regex '
                                                                           'pattern'},
                                             'case_sensitive': {   'type': 'boolean',
                                                                   'default': False},
                                             'regex': {'type': 'boolean', 'default': False}},
                           'required': ['pattern']}},
    {   'name': 'find_in_files',
        'description': "Open ST's native Find in Files panel (Ctrl+Shift+H equivalent) and run a "
                       "search. Routes through ST's real C++ find engine, NOT a Python "
                       'reimplementation. The three-box Find / Replace / Where panel is shown so '
                       'the user sees exactly what is being searched. The `where` parameter '
                       'accepts the full ST Where syntax: globs (*.py, -*.md), folder paths, '
                       '${project}, ${folder:Name}, ${open_files}, <project filters>, or '
                       'combinations separated by commas. Pass show_panel=False for a silent '
                       'background search.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'pattern': {   'type': 'string',
                                                            'description': 'Search string or '
                                                                           'regex'},
                                             'replace': {   'type': 'string',
                                                            'description': 'Optional Replace box '
                                                                           'text. Does not '
                                                                           'auto-execute; use '
                                                                           'replace_in_files for '
                                                                           'that.'},
                                             'where': {   'type': 'string',
                                                          'description': 'Where filter: globs, '
                                                                         'folder paths, '
                                                                         '${project}, '
                                                                         '${folder:Name}, '
                                                                         '${open_files}, <project '
                                                                         'filters>'},
                                             'case_sensitive': {   'type': 'boolean',
                                                                   'default': False},
                                             'regex': {'type': 'boolean', 'default': False},
                                             'whole_word': {'type': 'boolean', 'default': False},
                                             'preserve_case': {'type': 'boolean', 'default': False},
                                             'show_panel': {'type': 'boolean', 'default': True}},
                           'required': ['pattern']}},
    {   'name': 'find_in_folder',
        'description': "Open Find in Files scoped to a folder (WindowCommand). Pass 'pattern' "
                       "(regex) and optional 'where'.",
        'inputSchema': {   'type': 'object',
                           'properties': {   'pattern': {'type': 'string'},
                                             'where': {'type': 'string'}},
                           'required': ['pattern']}},
    {   'name': 'find_next',
        'description': 'Jumps to the next occurrence of the text or pattern in the find buffer. '
                       '(TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'find_prev',
        'description': 'Jumps to the previous occurrence of the text or pattern in the find '
                       'buffer. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'find_under',
        'description': 'Finds the next occurrence of the current selection or the current word. '
                       '(TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'find_under_expand',
        'description': 'Adds a new selection based on the current selection or expands the '
                       'selection to the current word. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'find_under_expand_skip',
        'description': 'Adds a new selection based on the current selection or expands the '
                       'selection to the current word while removing the current selection. '
                       '(TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'find_under_prev',
        'description': 'Finds the previous occurrence of the current selection or the current '
                       'word. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'focus_by_index',
        'description': 'Focus one of multiple selected views in the active group by its index. '
                       '(WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'index': {   'type': 'integer',
                                                          'description': 'The index number of the '
                                                                         'view to be focussed.'}}}},
    {   'name': 'focus_group',
        'description': 'Move focus to a pane group by 0-based index.',
        'inputSchema': {   'type': 'object',
                           'properties': {'group': {'type': 'integer'}},
                           'required': ['group']}},
    {   'name': 'focus_neighboring_group',
        'description': 'Move focus to the neighboring pane group (cycle through panes).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'focus_sheet',
        'description': 'Move input focus to one sheet by global index or stable sheet ID without '
                       'changing the selected sheet set.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'index': {'type': 'integer', 'minimum': 0},
                                             'id': {'type': 'integer'}}}},
    {   'name': 'focus_side_bar',
        'description': 'Focus the sidebar to enable navigation by keyboard. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'focus_to_left',
        'description': 'Move input focus to the selected sheet on the left.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'focus_to_right',
        'description': 'Move input focus to the selected sheet on the right.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'fold',
        'description': "Runs the Sublime Text 'fold' command. (TextCommand)",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'fold_all',
        'description': "Runs the Sublime Text 'fold_all' command. (TextCommand)",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'fold_by_level',
        'description': 'Folds all the code at a given indentation level. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'level': {   'type': 'integer',
                                                          'description': 'The indentation level of '
                                                                         'the code.'}}}},
    {   'name': 'fold_lines',
        'description': 'Fold (collapse) lines begin through end (1-based) in the active file.',
        'inputSchema': {   'type': 'object',
                           'properties': {'begin': {'type': 'integer'}, 'end': {'type': 'integer'}},
                           'required': ['begin', 'end']}},
    {   'name': 'fold_tag_attributes',
        'description': 'Fold(s) the html/xml tag attributes. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'fold_unfold',
        'description': 'Toggle the fold state of the region at the cursor (TextCommand). Collapses '
                       'or expands the enclosing code block.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_active_file',
        'description': "Return the active file's path, full content, cursor line/col, dirty flag, "
                       'and syntax name.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_active_panel',
        'description': 'Return the active panel id and, if it is an output panel, its content.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_bookmarks',
        'description': 'Return all bookmarked positions in the active file.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_command_palette',
        'description': 'List Command Palette entries from installed *.sublime-commands resources.\n'
                       'Optional filters: package, command id, or caption substring.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'package': {'type': 'string', 'default': ''},
                                             'command': {'type': 'string', 'default': ''},
                                             'caption': {'type': 'string', 'default': ''}}}},
    {   'name': 'get_commands',
        'description': 'List runnable Sublime command ids from loaded command classes, optionally '
                       'enriched\n'
                       'with matching Command Palette entries from installed packages.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'package': {'type': 'string', 'default': ''},
                                             'command': {'type': 'string', 'default': ''},
                                             'include_palette': {   'type': 'boolean',
                                                                    'default': True}}}},
    {   'name': 'get_console',
        'description': "Read Sublime Text's built-in console. mode='auto' prefers a complete "
                       'visible-console capture and falls back to the reload-safe prospective '
                       "capture; mode='visible' requires a complete capture; mode='captured' is "
                       'non-invasive but contains only messages observed since capture began. '
                       'Results include source and complete metadata.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'mode': {   'type': 'string',
                                                         'enum': ['auto', 'visible', 'captured'],
                                                         'default': 'auto'},
                                             'tail': {'type': 'integer', 'default': 200}}}},
    {   'name': 'get_console_full',
        'description': 'Compatibility alias for a complete visible-console capture.\n'
                       "Currently supported on Windows; prefer get_console(mode='visible').",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_console_log',
        'description': 'Compatibility tool for reload-safe prospective console capture.\n'
                       'tail=N limits to the last N entries; tail=0 returns all retained entries.\n'
                       "Prefer get_console(mode='captured') for explicit completeness metadata.",
        'inputSchema': {   'type': 'object',
                           'properties': {'tail': {'type': 'integer', 'default': 100}}}},
    {   'name': 'get_console_win',
        'description': 'Windows complete-console backend using reversible UI automation. Restores '
                       'the previous panel, editor focus, pointer position, and text clipboard. '
                       "Prefer get_console(mode='auto').",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_cursor_context',
        'description': 'Return `lines` lines above and below the cursor with 1-based line numbers '
                       'prepended.',
        'inputSchema': {   'type': 'object',
                           'properties': {'lines': {'type': 'integer', 'default': 10}}}},
    {   'name': 'get_encoding',
        'description': 'Return the character encoding of the active file.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_file_content',
        'description': 'Return the full content of an already-open file by its path.',
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string'}},
                           'required': ['path']}},
    {   'name': 'get_help',
        'description': 'Return the Agent Guide (AGENT_GUIDE.md) with detailed instructions on how '
                       'to use sublime-mcp tools correctly. Call this first if you are unsure how '
                       'to save files, close tabs, or use eval_python.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_layout',
        'description': 'Return the current window layout (groups, cells) and which files are in '
                       'each group.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_line_count',
        'description': 'Return the total number of lines in the active file.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_menu_items',
        'description': 'List installed menu items from *.sublime-menu resources.\n'
                       'Optional filters: menu filename, caption substring, or command id '
                       'substring.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'menu': {'type': 'string', 'default': ''},
                                             'caption': {'type': 'string', 'default': ''},
                                             'command': {'type': 'string', 'default': ''}}}},
    {   'name': 'get_open_files',
        'description': 'List all files open in the current window (path, name, is_dirty).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_output_panel',
        'description': 'Return the text content of an output panel.\n'
                       "If name is omitted, read the active output panel. Use name='exec' for "
                       'build output.\n'
                       "Use name='Console' to read Sublime's built-in console through the best "
                       'available backend.',
        'inputSchema': {   'type': 'object',
                           'properties': {'name': {'type': 'string', 'default': ''}}}},
    {   'name': 'get_package_mcp_info',
        'description': 'Discover what an installed Sublime package can do, then just control it '
                       'directly --\n'
                       'no separate MCP server needed. Primary workflow: call this for the package '
                       'name, Read\n'
                       "the files it lists under python_files to find the package's real "
                       'command-dispatch table\n'
                       "and settings (this tool's own commands/settings_keys are a starting point, "
                       'not the full\n'
                       'picture -- a package that routes many actions through one command with an '
                       "'action' arg,\n"
                       'for example, only shows up here as that one wrapper command), then call '
                       'the real thing\n'
                       'with run_command or eval_python. That loop -- discover, read source, call '
                       'directly -- is\n'
                       'almost always enough on its own.\n'
                       'Returns: path, commands (with captions and args), settings_keys, '
                       'python_files, plus\n'
                       'output_file/extension_template for the rare theoretical case where a '
                       'standing,\n'
                       'independently-reachable MCP server is needed (e.g. a client with no '
                       'eval_python-\n'
                       'equivalent of its own) -- write the extension to output_file following '
                       'extension_template\n'
                       'and ST loads it automatically. A full audit of the real, current, popular '
                       'Package Control\n'
                       'catalog (2026-09-14) found zero packages that actually needed this path -- '
                       'treat it as a\n'
                       'documented escape hatch, not something to reach for by default.',
        'inputSchema': {   'type': 'object',
                           'properties': {'package': {'type': 'string'}},
                           'required': ['package']}},
    {   'name': 'get_project_data',
        'description': 'Return the raw .sublime-project JSON data for the current project.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_project_folders',
        'description': "Return the project's root folder paths.",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_scope_at_cursor',
        'description': 'Return the full syntax scope string at the cursor position.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_selected_sheets',
        'description': 'Return the currently multi-selected sheets, optionally limited to one '
                       'group, with stable IDs and group positions.',
        'inputSchema': {   'type': 'object',
                           'properties': {'group': {'type': 'integer', 'minimum': 0}}}},
    {   'name': 'get_selection',
        'description': 'Return the current selection(s): text and begin/end line+col for each.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_setting',
        'description': "Get a Sublime Text setting by key. scope='view' (default) or 'window'.",
        'inputSchema': {   'type': 'object',
                           'properties': {   'key': {'type': 'string'},
                                             'scope': {'type': 'string', 'default': 'view'}},
                           'required': ['key']}},
    {   'name': 'get_sheet_content',
        'description': 'Return the content of any tab by its sheet index (from get_sheets).\n'
                       'Works for text tabs including untitled buffers and Terminus tabs.\n'
                       'For image tabs returns the file path and content_base64 (base64-encoded '
                       'image data).',
        'inputSchema': {   'type': 'object',
                           'properties': {'index': {'type': 'integer'}},
                           'required': ['index']}},
    {   'name': 'get_sheet_index',
        'description': "Return a sheet's current group and index within that group. Identify it by "
                       'global index or stable sheet ID.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'index': {'type': 'integer', 'minimum': 0},
                                             'id': {'type': 'integer'}}}},
    {   'name': 'get_sheets',
        'description': 'List ALL sheets (tabs) in the current window by index, including images '
                       'and untitled buffers.\n'
                       'Returns identity, group position, selection/focus state, type, path, name, '
                       'and dirty state.\n'
                       'Use index with get_sheet_content to read a specific tab.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_symbols',
        'description': 'Return all symbols (functions, classes, etc.) in the active file with line '
                       'numbers.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_syntaxes',
        'description': 'List all syntax definitions available in Sublime Text (name + path).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_variables',
        'description': "Return Sublime Text's build variables: $file, $project_path, $platform, "
                       'etc.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_view_chars',
        'description': 'Return text at character offsets begin..end (0-based, end exclusive) from '
                       'any open tab.\n'
                       'Clamps to buffer bounds automatically. Omit name for the active view.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'begin': {'type': 'integer'},
                                             'end': {'type': 'integer'},
                                             'name': {'type': 'string', 'default': ''}},
                           'required': ['begin', 'end']}},
    {   'name': 'get_view_content',
        'description': 'Return the full content of any open tab by name (partial match, '
                       'case-insensitive).\n'
                       'Works for Terminus tabs and other nameless views that have no file path.\n'
                       'Use index (0-based, from get_open_files) to target a tab by position '
                       'instead of name.\n'
                       'Omit both to read the active view.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'name': {'type': 'string', 'default': ''},
                                             'index': {'type': 'integer', 'default': -1}}}},
    {   'name': 'get_view_phantoms',
        'description': 'Return phantom HTML and extracted text from a view by name.\n'
                       'If key is omitted, returns phantoms for all keys.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'name': {'type': 'string', 'default': ''},
                                             'key': {'type': 'string', 'default': ''}}}},
    {   'name': 'get_view_size',
        'description': 'Return the total character count of any open tab by name (partial match, '
                       'case-insensitive).\n'
                       'Use before get_view_chars to compute offsets. Omit name for the active '
                       'view.',
        'inputSchema': {   'type': 'object',
                           'properties': {'name': {'type': 'string', 'default': ''}}}},
    {   'name': 'get_word_at_cursor',
        'description': 'Return the word under the cursor and its line/col.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'goto_definition',
        'description': 'Goto definition for the symbol under the cursor (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'goto_line',
        'description': 'Move the cursor to a line (and optional column) in the active file.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'line': {'type': 'integer'},
                                             'col': {'type': 'integer', 'default': 1}},
                           'required': ['line']}},
    {   'name': 'goto_reference',
        'description': 'Goto reference for the symbol under the cursor (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'goto_symbol_in_project',
        'description': 'Open the Goto Symbol In Project quick panel. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'hide_auto_complete',
        'description': 'Hides the AC popup, if visible. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'hide_overlay',
        'description': 'Hides the currently visible overlay. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'hide_panel',
        'description': 'Hides the currently visible panel. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {'cancel': {'type': 'boolean'}}}},
    {   'name': 'hide_popup',
        'description': 'Hides the popup window, if visible. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'hot_exit',
        'description': "Saves the session and exits the application even if the 'hot_exit' setting "
                       'is disabled in preferences. (ApplicationCommand) Observed on Sublime Text '
                       '4215: quits Sublime Text (which also stops this MCP server).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'html_print',
        'description': 'Open the current file as HTML for printing (TextCommand). Equivalent to '
                       'File > Print.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'ignore_word',
        'description': 'Adds the given word to the ignored_words setting. (TextCommand) Observed '
                       'on Sublime Text 4215: writes Sublime Text settings.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'word': {   'type': 'string',
                                                         'description': 'The word to be '
                                                                        'ignored.'}}}},
    {   'name': 'increase_font_size',
        'description': 'Increases the global font size. (ApplicationCommand) Observed on Sublime '
                       'Text 4215: writes Sublime Text settings.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'indent',
        'description': 'Indent the current selection(s) by one indentation level (Tab when there '
                       'is a selection).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'insert',
        'description': 'Insert text at the cursor(s). Replacement for typing: characters are '
                       'inserted into each selection.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'characters': {   'type': 'string',
                                                               'description': 'Text to insert at '
                                                                              'each cursor.'}},
                           'required': ['characters']}},
    {   'name': 'insert_snippet',
        'description': "Insert a snippet at the cursor using Sublime Text's snippet syntax (e.g. "
                       '$1 for tab stops).',
        'inputSchema': {   'type': 'object',
                           'properties': {'contents': {'type': 'string'}},
                           'required': ['contents']}},
    {   'name': 'install_package',
        'description': 'Install a Package Control package by exact name. Use search_packages first '
                       'to find the correct name. Installation runs in the background — check the '
                       'ST console for progress.',
        'inputSchema': {   'type': 'object',
                           'properties': {'package': {'type': 'string'}},
                           'required': ['package']}},
    {   'name': 'install_package_control',
        'description': 'Install Package Control (ApplicationCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'invert_selection',
        'description': 'Invert the selection: what was selected becomes unselected and vice versa '
                       '(within the current line range).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'join_lines',
        'description': 'Join the selected lines into a single line (Ctrl+J).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'jump_back',
        'description': 'Jump back in the navigation history (TextCommand). Equivalent to Alt+- '
                       '(jump back through edit/cursor history).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'jump_forward',
        'description': 'Jump forward in the navigation history (TextCommand). Equivalent to '
                       'Alt+Shift+- (jump forward through edit/cursor history).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'left_delete',
        'description': 'Deletes the character(s) to the left of the text selection caret(s). '
                       '(TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'list_native_windows',
        'description': 'List the native OS windows, dialogs and menus of this Sublime Text process '
                       '(Windows only): kind (dialog, menu, editor_window, window), title, hwnd, '
                       'and for dialogs their buttons and message text. Works while a native '
                       "dialog has BLOCKED Sublime's main thread (every other tool then times "
                       'out); the result says whether the main thread is blocked and which tool '
                       'blocked it.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'lookup_symbol',
        'description': 'Find where a symbol is defined across all open files.',
        'inputSchema': {   'type': 'object',
                           'properties': {'symbol': {'type': 'string'}},
                           'required': ['symbol']}},
    {   'name': 'lower_case',
        'description': 'Convert the current selection(s) to lower case.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'main_thread_stack',
        'description': "Return ST's main thread's current Python stack trace right now, read "
                       'directly via sys._current_frames() from whichever thread handles this '
                       'request. Works even while the main thread is wedged, since it needs no '
                       'cooperation from it -- use this to see exactly what a stuck call is doing '
                       'instead of guessing from symptoms.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'move',
        'description': 'Moves the selection caret(s) by the specified unit. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'by': {   'type': 'string',
                                                       'description': 'The unit name. Valid values '
                                                                      "are 'chars', 'pages', "
                                                                      "'lines', 'characters', "
                                                                      "'words', 'word_ends', "
                                                                      "'subwords', 'subword_ends' "
                                                                      "and 'stops'."},
                                             'empty_line': {'type': 'boolean'},
                                             'forward': {   'type': 'boolean',
                                                            'description': 'Whether to move in the '
                                                                           'forward direction.'},
                                             'extend': {   'type': 'boolean',
                                                           'description': 'Whether to extend the '
                                                                          'selection as the '
                                                                          'caret(s) move.'},
                                             'lines': {'type': 'boolean'},
                                             'ignore_auto_complete': {   'type': 'boolean',
                                                                         'description': 'Whether '
                                                                                        'to skip '
                                                                                        'navigating '
                                                                                        'the AC '
                                                                                        'items '
                                                                                        'when the '
                                                                                        'AC is '
                                                                                        'open.'}}}},
    {   'name': 'move_line_down',
        'description': 'Move the current line(s) down by one line.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'move_line_up',
        'description': 'Move the current line(s) up by one line.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'move_sheets_to_group',
        'description': 'Move one or more sheets together to a group and optional insertion '
                       'position, preserving native multi-selection when requested.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'indices': {   'type': 'array',
                                                            'items': {   'type': 'integer',
                                                                         'minimum': 0},
                                                            'minItems': 1},
                                             'ids': {   'type': 'array',
                                                        'items': {'type': 'integer'},
                                                        'minItems': 1},
                                             'group': {'type': 'integer', 'minimum': 0},
                                             'insertion_index': {   'type': 'integer',
                                                                    'minimum': -1,
                                                                    'default': -1},
                                             'select': {'type': 'boolean', 'default': True}},
                           'required': ['group']}},
    {   'name': 'move_to',
        'description': 'Moves the selection caret(s) to the specified relative location. '
                       '(TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'to': {   'type': 'string',
                                                       'description': 'The relative location. '
                                                                      "Valid values are 'eol', "
                                                                      "'bol', 'eof', 'bof' and "
                                                                      "'brackets'."},
                                             'extend': {   'type': 'boolean',
                                                           'description': 'Whether to extend the '
                                                                          'selection while moving '
                                                                          'to the specified '
                                                                          'relative location.'}}}},
    {   'name': 'move_to_group',
        'description': 'Moves the active tab to the specified layout group. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'group': {   'type': 'integer',
                                                          'description': 'The index of the target '
                                                                         'group.'}}}},
    {   'name': 'move_to_neighboring_group',
        'description': 'Move the active view to the neighboring pane group.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'move_view',
        'description': 'Move the active view to a different group. Optional args: group (target '
                       "group index), direction ('left'/'right'/'up'/'down').",
        'inputSchema': {   'type': 'object',
                           'properties': {   'group': {'type': 'integer', 'default': -1},
                                             'direction': {'type': 'string', 'default': ''}}}},
    {   'name': 'new_build_system',
        'description': 'Create a new build system file (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'new_file',
        'description': 'Create a new untitled file in the current window (File → New File).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'new_file_at',
        'description': "Create a new file at the given path (WindowCommand). Pass 'path' in args.",
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string'}},
                           'required': ['path']}},
    {   'name': 'new_folder',
        'description': 'Create a new folder in the current project (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'new_os_tab',
        'description': 'Creates a new empty window in the os tab. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'new_pane',
        'description': 'Create a new pane in the active window (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'new_plugin',
        'description': 'Create a new plugin file in Packages/User (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'new_snippet',
        'description': 'Create a new snippet file in Packages/User (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'new_syntax',
        'description': 'Create a new syntax definition file in Packages/User (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'new_view',
        'description': 'Create a new untitled view/tab in the current window. Alias of new_file.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'new_window',
        'description': 'Opens a new ST window. (ApplicationCommand) Observed on Sublime Text 4215: '
                       'opens a new Sublime Text window.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'new_window_for_project',
        'description': 'Clones the project into a new workspace. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'next_bookmark',
        'description': 'Move the cursor to the next bookmark in the active view.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'next_field',
        'description': 'Navigate to the next field in the snippet. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'next_misspelling',
        'description': 'Navigate to the next misspelling in the document. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'next_modification',
        'description': 'Navigate to the next modification in the document. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'next_os_tab',
        'description': 'Set the focus to the next window in the os tab. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'next_pane',
        'description': 'Move focus to the next pane/group in the window.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'next_result',
        'description': 'Jump to the next find-in-files or build result. Visible in the view '
                       '(cursor moves).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'next_view',
        'description': 'Switch to the next view/tab in the current group.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'next_view_in_stack',
        'description': 'Switch to the next view in the view history stack (Ctrl+Tab equivalent).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'noop',
        'description': 'A non existent command. Use this if you want to unbind any particular key '
                       'binding & release it to the OS (ST 4117+). (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'old_expand_selection_to_paragraph',
        'description': 'Expand the selection to the surrounding paragraph (legacy TextCommand, '
                       'kept for compatibility).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'old_wrap_lines',
        'description': 'Wrap the selection at the configured wrap width using the legacy paragraph '
                       'algorithm (TextCommand, kept for compatibility).',
        'inputSchema': {   'type': 'object',
                           'properties': {   'width': {   'type': 'integer',
                                                          'description': 'Optional wrap width in '
                                                                         'columns. 0 = use the '
                                                                         "view's wrap_width "
                                                                         'setting.'}}}},
    {   'name': 'open_containing_folder',
        'description': 'Open the OS file manager at the directory containing the active file '
                       '(WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'open_context_url',
        'description': 'Open the URL under the cursor in the default browser (TextCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'open_control_panel',
        'description': 'Open (or focus) the Claude MCP Control Panel: an interactive minihtml '
                       'dashboard in a dedicated Sublime view, listing MCP servers with clickable '
                       'Enable/Disable toggle links. State persists on the view and the status '
                       'line reflects changes.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'open_dir',
        'description': 'Opens the specified dir in the default file manager application, '
                       'optionally highlighting the specified file. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'dir': {   'type': 'string',
                                                        'description': 'The absolute path to the '
                                                                       'directory to be opened in '
                                                                       'the default file manager '
                                                                       'application.'},
                                             'file': {   'type': 'string',
                                                         'description': 'The name of the file that '
                                                                        'is to be highlighted when '
                                                                        'the file manager '
                                                                        'application is launched, '
                                                                        'relative to the path of '
                                                                        'the directory.'}}}},
    {   'name': 'open_file',
        'description': 'Open a file in Sublime Text, optionally jumping to a specific line and '
                       'column.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'path': {'type': 'string'},
                                             'line': {'type': 'integer', 'default': 0},
                                             'col': {'type': 'integer', 'default': 0}},
                           'required': ['path']}},
    {   'name': 'open_file_settings',
        'description': 'Open the syntax-specific settings file for the active view '
                       '(WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'open_folder',
        'description': "Open a folder in a new window (WindowCommand). Pass 'path' in args.",
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string'}},
                           'required': ['path']}},
    {   'name': 'open_in_browser',
        'description': 'Open the current file in the default browser (TextCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'open_project_or_workspace',
        'description': 'Opens the specified project or workspace file, in a new window by default. '
                       '(WindowCommand) Observed on Sublime Text 4215: when given arguments: opens '
                       'a native OS window ("Sublime Text") that blocks Sublime\'s main thread '
                       'until a person dismisses it; writes files.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'file': {   'type': 'string',
                                                         'description': 'The absolute path to the '
                                                                        'project or workspace '
                                                                        'file.'},
                                             'new_window': {   'type': 'boolean',
                                                               'description': 'Whether to open the '
                                                                              'specified project '
                                                                              'or workspace file '
                                                                              'in a new '
                                                                              'window.'}}}},
    {   'name': 'open_recent_file',
        'description': 'Opens a recently opened file. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'open_recent_folder',
        'description': 'Opens a recently opened folder. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'index': {   'type': 'integer',
                                                          'description': 'The index of recent '
                                                                         'folder to be opened as '
                                                                         'per the folder_history '
                                                                         'in the session file.'}}}},
    {   'name': 'open_recent_project_or_workspace',
        'description': 'Opens a recently opened project or workspace. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'index': {   'type': 'integer',
                                                          'description': 'The index of the '
                                                                         'workspace as per '
                                                                         'recent_workspaces in the '
                                                                         'session file.'}}}},
    {   'name': 'open_symbol_definition',
        'description': "Open the definition of a named symbol (WindowCommand). Pass 'symbol'.",
        'inputSchema': {   'type': 'object',
                           'properties': {'symbol': {'type': 'string'}},
                           'required': ['symbol']}},
    {   'name': 'open_url',
        'description': 'Opens the web browser to display the URL or the default application '
                       'associated with the file/folder represented by the URL. '
                       '(ApplicationCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'url': {   'type': 'string',
                                                        'description': 'The URL to be opened.'}}}},
    {   'name': 'overwrite',
        'description': 'Overwrites the selection(s) at the caret(s) location(s) with the given '
                       'characters. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'characters': {   'type': 'string',
                                                               'description': 'The characters that '
                                                                              'will overwrite the '
                                                                              'selection(s).'}}}},
    {   'name': 'paste',
        'description': 'Paste the clipboard contents at the cursor(s), replacing any selection.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'paste_and_indent',
        'description': 'Paste and re-indent the pasted lines to match surrounding indentation.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'paste_from_history',
        'description': 'Open the paste-from-history panel so the user can pick a previously '
                       'cut/copied snippet to paste.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'paste_selection_clipboard',
        'description': 'Linux only. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'permute_lines',
        'description': 'Permute (shuffle) the lines in the current selection into a random order.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'permute_selection',
        'description': 'Permute (shuffle) the selections themselves into a random order.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'play_macro',
        'description': 'Alias of run_macro — play back the most recently recorded macro.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'prev_bookmark',
        'description': 'Move the cursor to the previous bookmark in the active view.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'prev_field',
        'description': 'Navigates to the previous field in the snippet. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'prev_misspelling',
        'description': 'Navigates to the previous misspelling in the document. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'prev_modification',
        'description': 'Navigates to the previous modification in the document. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'prev_os_tab',
        'description': 'Sets the focus to the previous window in the os tab. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'prev_pane',
        'description': 'Move focus to the previous pane/group in the window.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'prev_result',
        'description': 'Jump to the previous find-in-files or build result. Visible in the view '
                       '(cursor moves).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'prev_view',
        'description': 'Switch to the previous view/tab in the current group.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'prev_view_in_stack',
        'description': 'Switch to the previous view in the view history stack (Ctrl+Shift+Tab '
                       'equivalent).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'primary_j_changed',
        'description': 'Shows a dialog stating about the change of keybindings for the join_lines '
                       'command. (WindowCommand) Observed on Sublime Text 4215: opens a native OS '
                       'window ("Sublime Text") that blocks Sublime\'s main thread until a person '
                       'dismisses it.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'profile_plugins',
        'description': 'Profile plugin load times (ApplicationCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'profile_syntax_definition',
        'description': 'Profile a syntax definition for performance issues (ApplicationCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'project_search',
        'description': "Search project files with Sublime Text's native Find in Files engine and "
                       'return structured {path,line,col,text} matches. This is the preferred '
                       'project search tool.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'pattern': {'type': 'string'},
                                             'where': {   'type': 'string',
                                                          'description': 'ST Where expression; '
                                                                         'empty uses current '
                                                                         'project folders.'},
                                             'case_sensitive': {   'type': 'boolean',
                                                                   'default': False},
                                             'regex': {'type': 'boolean', 'default': False},
                                             'whole_word': {'type': 'boolean', 'default': False},
                                             'limit': {'type': 'integer', 'default': 200},
                                             'timeout': {'type': 'number', 'default': 30},
                                             'show_panel': {'type': 'boolean', 'default': False}},
                           'required': ['pattern']}},
    {   'name': 'prompt_add_folder',
        'description': 'Shows the OS native open dialog, so the user can choose what folder they '
                       'want to add to the sidebar. (WindowCommand) Observed on Sublime Text 4215: '
                       'opens a native OS window ("Select Folder") that blocks Sublime\'s main '
                       'thread until a person dismisses it.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'initial_directory': {   'type': 'string',
                                                                      'description': 'An absolute '
                                                                                     'folder path '
                                                                                     'on disk, '
                                                                                     'where the '
                                                                                     'native '
                                                                                     'dialog will '
                                                                                     'initially '
                                                                                     'open.'}}}},
    {   'name': 'prompt_goto_line',
        'description': 'Open the Goto Line prompt (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'prompt_open',
        'description': 'Shows the MacOS native open dialog, so that the user can choose what file '
                       'they want to open. (WindowCommand) Observed on Sublime Text 4215: shows an '
                       'in-app panel, popup or overlay (dismiss with hide_overlay, hide_panel or '
                       'hide_popup).',
        'inputSchema': {   'type': 'object',
                           'properties': {   'initial_directory': {   'type': 'string',
                                                                      'description': 'An absolute '
                                                                                     'folder path '
                                                                                     'on disk, '
                                                                                     'where the '
                                                                                     'native '
                                                                                     'dialog will '
                                                                                     'initially '
                                                                                     'open.'}}}},
    {   'name': 'prompt_open_file',
        'description': 'Shows the OS native open dialog, so that the user can choose what file '
                       'they want to open. (WindowCommand) Observed on Sublime Text 4215: opens a '
                       'native OS window ("Open") that blocks Sublime\'s main thread until a '
                       'person dismisses it.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'initial_directory': {   'type': 'string',
                                                                      'description': 'An absolute '
                                                                                     'folder path '
                                                                                     'on disk, '
                                                                                     'where the '
                                                                                     'native '
                                                                                     'dialog will '
                                                                                     'initially '
                                                                                     'open.'}}}},
    {   'name': 'prompt_open_folder',
        'description': 'Shows the OS native open dialog, so that the user can choose what folder '
                       'they want to open. (WindowCommand) Observed on Sublime Text 4215: opens a '
                       'native OS window ("Select Folder") that blocks Sublime\'s main thread '
                       'until a person dismisses it.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'initial_directory': {   'type': 'string',
                                                                      'description': 'An absolute '
                                                                                     'folder path '
                                                                                     'on disk, '
                                                                                     'where the '
                                                                                     'native '
                                                                                     'dialog will '
                                                                                     'initially '
                                                                                     'open.'}}}},
    {   'name': 'prompt_open_project_or_workspace',
        'description': "Show the OS' native open dialog, so the user can choose what project they "
                       'want to open. (WindowCommand) Observed on Sublime Text 4215: opens a '
                       'native OS window ("Open") that blocks Sublime\'s main thread until a '
                       'person dismisses it.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'initial_directory': {   'type': 'string',
                                                                      'description': 'An absolute '
                                                                                     'folder path '
                                                                                     'on disk, '
                                                                                     'where the '
                                                                                     'native '
                                                                                     'dialog will '
                                                                                     'initially '
                                                                                     'open.'}}}},
    {   'name': 'prompt_save_as',
        'description': 'Show the OS native save as dialog, so the user can choose the path where '
                       'they want the file to be saved. (WindowCommand) Observed on Sublime Text '
                       '4215: opens a native OS window ("Save As") that blocks Sublime\'s main '
                       'thread until a person dismisses it.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'initial_directory': {   'type': 'string',
                                                                      'description': 'An absolute '
                                                                                     'folder path '
                                                                                     'on disk, '
                                                                                     'where the '
                                                                                     'native '
                                                                                     'dialog will '
                                                                                     'initially '
                                                                                     'open.'}}}},
    {   'name': 'prompt_select_workspace',
        'description': 'Opens the Quick Switch Project window. (WindowCommand) Observed on Sublime '
                       'Text 4215: opens a separate window ("Switch Project").',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'prompt_switch_project_or_workspace',
        'description': 'Show the OS native open dialog, so the user can choose what project they '
                       'want to switch to. (WindowCommand) Observed on Sublime Text 4215: opens a '
                       'native OS window ("Open") that blocks Sublime\'s main thread until a '
                       'person dismisses it.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'initial_directory': {   'type': 'string',
                                                                      'description': 'An absolute '
                                                                                     'folder path '
                                                                                     'on disk, '
                                                                                     'where the '
                                                                                     'native '
                                                                                     'dialog will '
                                                                                     'initially '
                                                                                     'open.'}}}},
    {   'name': 'purchase_license',
        'description': 'Navigates to the url https://www.sublimehq.com/store/text in the default '
                       'browser to allow a user to purchase a license.. (ApplicationCommand) '
                       'Observed on Sublime Text 4215: starts another program (msedge.exe).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'quick_panel',
        'description': 'Open the Goto Anything overlay (WindowCommand show_overlay). Optional '
                       "'show_files' (bool) and 'text'.",
        'inputSchema': {   'type': 'object',
                           'properties': {   'show_files': {'type': 'boolean'},
                                             'text': {'type': 'string'}}}},
    {   'name': 'redo',
        'description': 'Redo the last undone edit in the active file.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'redo_or_repeat',
        'description': 'Redos the last undo or repeats the last action if there is no undo to '
                       'revert. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'refresh_folder_list',
        'description': 'Refreshs the folder list in the sidebar from the filesystem. '
                       '(WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'reindent',
        'description': "Re-indent the current selection(s) so each line's indentation matches its "
                       'nesting depth.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'remove_folder',
        'description': 'Remove a folder from the current project by path.',
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string'}},
                           'required': ['path']}},
    {   'name': 'remove_license',
        'description': 'Removes the license. This will cause Sublime Text/Merge to go into an '
                       'unregistered state. (ApplicationCommand) Observed on Sublime Text 4215: '
                       'opens a native OS window ("Remove license key?") that blocks Sublime\'s '
                       'main thread until a person dismisses it.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'rename_file',
        'description': "Rename the active file (WindowCommand). Pass 'path' for the new name.",
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string'}},
                           'required': ['path']}},
    {   'name': 'rename_path',
        'description': 'Renames the given file(s) on disk. (WindowCommand) Observed on Sublime '
                       'Text 4215: when given arguments: shows an in-app panel, popup or overlay '
                       '(dismiss with hide_overlay, hide_panel or hide_popup).',
        'inputSchema': {   'type': 'object',
                           'properties': {   'paths': {   'type': 'array',
                                                          'description': 'A list of absolute file '
                                                                         'paths to be renamed.'}}}},
    {   'name': 'reopen',
        'description': 'Reopens the file with a given encoding. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'encoding': {   'type': 'string',
                                                             'description': 'The encoding to be '
                                                                            'used when the file is '
                                                                            'reopened.'}}}},
    {   'name': 'reopen_closed_file',
        'description': 'Reopen the most recently closed file (File → Reopen Closed File).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'reopen_last_file',
        'description': 'Reopens the most recently closed file. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'replace_all',
        'description': 'Replaces all tokens in the view, which matches the pattern in the Find '
                       'input field. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'replace_completion_with_auto_complete',
        'description': 'Replaces the most recently inserted completion with the next result '
                       'provided by the auto completion engine. (TextCommand) Observed on Sublime '
                       'Text 4215: shows an in-app panel, popup or overlay (dismiss with '
                       'hide_overlay, hide_panel or hide_popup).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'replace_in_files',
        'description': 'Run the Replace half of Find in Files (Ctrl+Shift+H → Replace All) and '
                       'show the diff preview panel so the user can review every replacement '
                       'before it is committed. Same `where` syntax as find_in_files. Replace '
                       'string may be empty for deletion. Regex capture-group backrefs ($1, $2) '
                       'supported when regex=True.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'pattern': {'type': 'string'},
                                             'replace': {   'type': 'string',
                                                            'description': 'Replacement string '
                                                                           '(use empty string for '
                                                                           'deletion)'},
                                             'where': {'type': 'string'},
                                             'case_sensitive': {   'type': 'boolean',
                                                                   'default': False},
                                             'regex': {'type': 'boolean', 'default': False},
                                             'whole_word': {'type': 'boolean', 'default': False},
                                             'preserve_case': {'type': 'boolean', 'default': False},
                                             'show_panel': {'type': 'boolean', 'default': True}},
                           'required': ['pattern', 'replace']}},
    {   'name': 'replace_lines',
        'description': 'Replace lines begin through end (inclusive, 1-based) in the active file '
                       'with text.\n'
                       'Pass path to target a specific open file regardless of which tab is '
                       'focused.\n'
                       'Use index (0-based, from get_open_files) to target a nameless tab by '
                       'position.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'begin': {'type': 'integer'},
                                             'end': {'type': 'integer'},
                                             'text': {'type': 'string'},
                                             'path': {'type': 'string', 'default': ''},
                                             'index': {'type': 'integer', 'default': -1}},
                           'required': ['begin', 'end', 'text']}},
    {   'name': 'replace_next',
        'description': 'Replaces the next token in the view, which matches the pattern in the Find '
                       'input field. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'replace_selection',
        'description': 'Replace the current selection(s) with text.',
        'inputSchema': {   'type': 'object',
                           'properties': {'text': {'type': 'string'}},
                           'required': ['text']}},
    {   'name': 'reset_font_size',
        'description': 'Resets the font size to the default value. (ApplicationCommand) Observed '
                       'on Sublime Text 4215: writes Sublime Text settings.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'resize_window',
        'description': "Resizes the window's external bounds to the specified width and height. "
                       '(WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'width': {   'type': 'integer',
                                                          'description': 'The external width of '
                                                                         'the window.'},
                                             'height': {   'type': 'integer',
                                                           'description': 'The external height of '
                                                                          'the window.'}}}},
    {   'name': 'reveal_in_side_bar',
        'description': "Reveals the active view's file in the sidebar. (WindowCommand)",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'reveal_link_source',
        'description': 'Resolves a symlink to expand the folder it represents. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'dirs': {   'type': 'array',
                                                         'description': 'The list of symlink '
                                                                        'directorie(s) to be '
                                                                        'resolved.'}}}},
    {   'name': 'revert',
        'description': 'Reloads the file. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'revert_file',
        'description': 'Revert the active file to its last saved state, discarding unsaved '
                       'changes.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'revert_hunk',
        'description': 'Reverts a diff hunk. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'revert_modification',
        'description': 'Reverts a single modification. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'right_delete',
        'description': 'Deletes the character to the right of the text selection caret(s). '
                       '(TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'rot13',
        'description': 'Apply the ROT13 cipher to the current selection (TextCommand). Useful for '
                       'obscuring spoiler text or round-tripping text.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'run_build',
        'description': 'Trigger the current build system, or pass cmd/shell_cmd to run a specific '
                       'command.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'cmd': {'type': 'array', 'items': {'type': 'string'}},
                                             'shell_cmd': {'type': 'string'},
                                             'working_dir': {'type': 'string', 'default': ''}}}},
    {   'name': 'run_command',
        'description': "Run any Sublime Text command. scope='window' (default) or 'view'.\n"
                       "For scope='view'/'text', optionally target a specific tab with name "
                       '(partial, case-insensitive) or index (0-based, from get_open_files) '
                       'instead of whatever tab happens to be globally focused -- important when '
                       'another agent/session may be sharing this Sublime instance.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'command': {'type': 'string'},
                                             'args': {'type': 'object'},
                                             'scope': {'type': 'string', 'default': 'window'},
                                             'name': {'type': 'string', 'default': ''},
                                             'index': {'type': 'integer', 'default': -1}},
                           'required': ['command']}},
    {   'name': 'run_macro',
        'description': 'Play back the most recently recorded macro at the cursor.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'run_macro_file',
        'description': 'Runs a macro saved in a macro file. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'file': {   'type': 'string',
                                                         'description': "The 'Packages/' relative "
                                                                        'path to the '
                                                                        "'.sublime-macro' "
                                                                        'file.'}}}},
    {   'name': 'run_syntax_tests',
        'description': 'Run syntax tests on the active syntax file (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'save',
        'description': 'Saves the active view/document. (TextCommand) Observed on Sublime Text '
                       '4215: writes files.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'async': {   'type': 'boolean',
                                                          'description': 'Whether to save the file '
                                                                         'asynchronously.'},
                                             'encoding': {   'type': 'string',
                                                             'description': 'The encoding, to save '
                                                                            'the file as.'},
                                             'quiet': {   'type': 'boolean',
                                                          'description': 'Whether to suppress '
                                                                         'dialogs if the file save '
                                                                         'fails or requires '
                                                                         'elevated permissions on '
                                                                         'the host OS.'}}}},
    {   'name': 'save_all',
        'description': 'Save all open files.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'save_file',
        'description': 'Save a file. Pass path to save a specific open file; omit path to save the '
                       'active file.',
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string', 'default': ''}}}},
    {   'name': 'save_macro',
        'description': 'Save the recorded macro to a file. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'save_project_and_workspace_as',
        'description': 'Opens the OS dialog window to save the active project. (WindowCommand) '
                       'Observed on Sublime Text 4215: opens a native OS window ("Save As") that '
                       "blocks Sublime's main thread until a person dismisses it.",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'save_workspace_as',
        'description': 'Opens the OS dialog window to save the active workspace. (WindowCommand) '
                       'Observed on Sublime Text 4215: opens a native OS window ("Save As") that '
                       "blocks Sublime's main thread until a person dismisses it.",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'scroll_lines',
        'description': 'Scroll the active view by the specified number of lines. A negative number '
                       'means to scroll in an upwards direction. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'amount': {   'type': 'number',
                                                           'description': 'The specified amount by '
                                                                          'which the view has to '
                                                                          'be scrolled.'}}}},
    {   'name': 'scroll_to_bof',
        'description': 'Scroll the active view so the beginning of the file is visible (does not '
                       'move the cursor).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'scroll_to_eof',
        'description': 'Scroll the active view so the end of the file is visible (does not move '
                       'the cursor).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'search_packages',
        'description': 'Search Package Control for installable Sublime Text packages. Returns '
                       'name, description, author, homepage, labels, and last_modified for each '
                       'match. Searches both package names and descriptions.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'query': {   'type': 'string',
                                                          'description': 'Search term (name or '
                                                                         'description). Empty '
                                                                         'returns all.'},
                                             'limit': {   'type': 'integer',
                                                          'default': 20,
                                                          'description': 'Max results (1-100).'}}}},
    {   'name': 'select',
        'description': "Runs the Sublime Text 'select' command. (WindowCommand)",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'select_all',
        'description': 'Select the entire contents of the active view (Ctrl+A equivalent).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'select_all_bookmarks',
        'description': 'Select every line containing a bookmark in the active view.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'select_bookmark',
        'description': 'Select a specific bookmark (by index) in the current document. '
                       '(TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {'index': {'type': 'integer'}}}},
    {   'name': 'select_by_index',
        'description': 'Focus a view in the active group based on its index. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'index': {   'type': 'integer',
                                                          'description': 'The index of the view to '
                                                                         'focus. The first view '
                                                                         'will have an index of 0 '
                                                                         'and so on.'}}}},
    {   'name': 'select_color_scheme',
        'description': 'Open the color scheme picker (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'select_lines',
        'description': 'Select lines begin through end (1-based, inclusive). end defaults to '
                       'begin.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'begin': {'type': 'integer'},
                                             'end': {'type': 'integer', 'default': 0}},
                           'required': ['begin']}},
    {   'name': 'select_sheets',
        'description': 'Change native tab multi-selection across the window. Identify sheets by '
                       'global indices or stable sheet IDs; optionally choose the focused sheet.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'indices': {   'type': 'array',
                                                            'items': {   'type': 'integer',
                                                                         'minimum': 0},
                                                            'minItems': 1},
                                             'ids': {   'type': 'array',
                                                        'items': {'type': 'integer'},
                                                        'minItems': 1},
                                             'focus_index': {'type': 'integer', 'minimum': 0},
                                             'focus_id': {'type': 'integer'}}}},
    {   'name': 'select_theme',
        'description': 'Open the theme picker (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'select_to_left',
        'description': 'Add the sheet left of the focused sheet to the tab multi-selection.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'select_to_mark',
        'description': 'Select the text between the cursor and the previously set mark '
                       '(TextCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'select_to_right',
        'description': 'Add the sheet right of the focused sheet to the tab multi-selection.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'send_to_view',
        'description': 'Send a string to any open tab by name (partial match, case-insensitive).\n'
                       'Inserts the text at the cursor of the resolved view using the standard '
                       'insert command; returns an error if the view is read-only.\n'
                       'Use index (0-based, from get_open_files) to target a tab by position '
                       'instead of name.\n'
                       'Omit both name and index to target the active view.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'text': {'type': 'string'},
                                             'name': {'type': 'string', 'default': ''},
                                             'index': {'type': 'integer', 'default': -1}},
                           'required': ['text']}},
    {   'name': 'set_build_system',
        'description': 'Sets the given build system based on the build file. (WindowCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'file': {   'type': 'string',
                                                         'description': "Accepts a 'Packages/' "
                                                                        'relative path to a '
                                                                        'sublime build file to set '
                                                                        'as the current build '
                                                                        'system. An empty string '
                                                                        'will set it to the '
                                                                        "'Automatic' option as "
                                                                        "seen in 'Tools -> Build "
                                                                        "System'."}}}},
    {   'name': 'set_encoding',
        'description': "Set the character encoding of the active file (e.g. 'UTF-8', 'Western "
                       "(Windows 1252)').",
        'inputSchema': {   'type': 'object',
                           'properties': {'encoding': {'type': 'string'}},
                           'required': ['encoding']}},
    {   'name': 'set_file_type',
        'description': 'Sets the syntax for the active view. (TextCommand) Observed on Sublime '
                       'Text 4215: when given arguments: opens a separate window ("Sublime Text").',
        'inputSchema': {   'type': 'object',
                           'properties': {   'syntax': {   'type': 'string',
                                                           'description': 'The syntax to be set '
                                                                          'for the active view. '
                                                                          'Can either be a package '
                                                                          'relative path like '
                                                                          "'Packages/Foo/Bar.sublime-syntax' "
                                                                          "or 'scope:' prefixed "
                                                                          'syntax name.'}}}},
    {   'name': 'set_indent_spaces',
        'description': 'Set the active view to use spaces for indentation.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'set_indent_tabs',
        'description': 'Set the active view to use tabs for indentation.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'set_layout',
        'description': 'Set the window pane layout. layout must be a ST layout dict with cols, '
                       'rows, cells keys.',
        'inputSchema': {   'type': 'object',
                           'properties': {'layout': {'type': 'object'}},
                           'required': ['layout']}},
    {   'name': 'set_line_ending',
        'description': 'Sets the line endings for the files. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'type': {   'type': 'string',
                                                         'description': 'The platform type. Valid '
                                                                        "values are 'windows', "
                                                                        "'unix' & 'cr'."}}}},
    {   'name': 'set_mark',
        'description': 'Set a mark at the current cursor position (TextCommand). Used with '
                       'select_to_mark/swap_with_mark/delete_to_mark.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'set_max_columns',
        'description': 'Set the maximum number of columns for the current layout (WindowCommand). '
                       "Pass 'cols' integer.",
        'inputSchema': {   'type': 'object',
                           'properties': {'cols': {'type': 'integer'}},
                           'required': ['cols']}},
    {   'name': 'set_setting',
        'description': "Set a Sublime Text setting by key. scope='view' (default) or 'window'.",
        'inputSchema': {   'type': 'object',
                           'properties': {   'key': {'type': 'string'},
                                             'value': {},
                                             'scope': {'type': 'string', 'default': 'view'}},
                           'required': ['key', 'value']}},
    {   'name': 'set_sheet_index',
        'description': "Move one sheet to a group and position using Sublime's set_sheet_index "
                       'API.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'index': {'type': 'integer', 'minimum': 0},
                                             'id': {'type': 'integer'},
                                             'group': {'type': 'integer', 'minimum': 0},
                                             'sheet_index': {'type': 'integer', 'minimum': 0}},
                           'required': ['group', 'sheet_index']}},
    {   'name': 'set_status',
        'description': "Write a message to Sublime Text's status bar.",
        'inputSchema': {   'type': 'object',
                           'properties': {   'value': {'type': 'string'},
                                             'key': {'type': 'string', 'default': 'sublime_mcp'}},
                           'required': ['value']}},
    {   'name': 'set_syntax',
        'description': 'Set the syntax of the active file by name (case-insensitive partial match '
                       'is fine).',
        'inputSchema': {   'type': 'object',
                           'properties': {'name': {'type': 'string'}},
                           'required': ['name']}},
    {   'name': 'show_about_window',
        'description': 'Displays the about dialog. (ApplicationCommand) Observed on Sublime Text '
                       '4215: opens a separate window ("Sublime Text").',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'show_at_center',
        'description': 'Scroll the active view so the current cursor line is centered in the '
                       'window.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'show_changelog',
        'description': 'Displays the changelog dialog. (ApplicationCommand) Observed on Sublime '
                       'Text 4215: opens a separate window ("Changelog").',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'show_license_window',
        'description': 'Displays the license dialog. This will only work if you are running an '
                       'unregistered copy of Sublime Text. (ApplicationCommand) Observed on '
                       'Sublime Text 4215: opens a separate window ("Enter License").',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'show_panel',
        'description': "Bring an output panel to the front. Use name='exec' for the build panel.",
        'inputSchema': {   'type': 'object',
                           'properties': {'name': {'type': 'string', 'default': 'exec'}}}},
    {   'name': 'show_progress_window',
        'description': 'Displays the indexing status dialog. (ApplicationCommand) Observed on '
                       'Sublime Text 4215: opens a separate window ("Indexing Status").',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'show_scope_name',
        'description': 'Print the syntax scope at the cursor to the ST console (TextCommand). '
                       'Useful for debugging syntax-highlighting or writing snippet scopes.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'shrink_selection',
        'description': 'Shrink a multi-cursor selection back to a single cursor (reverse of '
                       'expand_selection).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'single_selection',
        'description': 'Collapse multiple selections/cursors down to a single selection (Escape '
                       'equivalent).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'slurp_find_string',
        'description': 'Uses the current selection as the find string. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'slurp_replace_string',
        'description': 'Uses the current selection as the replacement string. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'soft_redo',
        'description': 'Redos the last move or action, which has been undone. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'soft_undo',
        'description': 'Undos the last move or action. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'sort_lines',
        'description': 'Sort the selected lines (or all lines if nothing is selected).',
        'inputSchema': {   'type': 'object',
                           'properties': {   'case_sensitive': {   'type': 'boolean',
                                                                   'default': False}}}},
    {   'name': 'sort_selection',
        'description': 'Sort the selected lines alphabetically (locale-aware).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'split_line',
        'description': 'Split the line at the cursor position (Ctrl+Enter equivalent in some '
                       'keymaps).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'split_selection_into_lines',
        'description': 'Split the current selection into one cursor per line (Ctrl+Shift+L).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'str_replace_based_edit_tool',
        'description': 'ST-native file editor implementing the standard '
                       'str_replace_based_edit_tool interface.\n'
                       'Edits appear live in Sublime Text with full undo (Ctrl+Z), gutter diff '
                       'markers,\n'
                       'and 30-second highlight annotations showing what changed.\n'
                       '\n'
                       "command='str_replace': replace old_str with new_str in path.\n"
                       '  old_str must match exactly once (whitespace-sensitive).\n'
                       '  Returns error if 0 or 2+ matches, listing ambiguous line numbers.\n'
                       '\n'
                       "command='insert': insert insert_text after line insert_line (1-based).\n"
                       '  insert_line=0 inserts at the very start of the file.\n'
                       '\n'
                       "command='create': create a new file at path with file_text content.\n"
                       '  Syntax is auto-detected from the file extension. Errors if path exists.\n'
                       '\n'
                       "command='view': return file content with 1-based line numbers prepended.\n"
                       '  Optional view_range=[start, end] to read a slice (end=-1 for EOF).\n'
                       '\n'
                       'All commands auto-open the file in ST if not already open.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'command': {'type': 'string'},
                                             'path': {'type': 'string', 'default': ''},
                                             'old_str': {'type': 'string'},
                                             'new_str': {'type': 'string'},
                                             'insert_line': {'type': 'integer'},
                                             'insert_text': {'type': 'string'},
                                             'file_text': {'type': 'string'},
                                             'view_range': {   'type': 'array',
                                                               'items': {'type': 'integer'},
                                                               'minItems': 2,
                                                               'maxItems': 2}},
                           'required': ['command']}},
    {   'name': 'sublime_merge_blame_file',
        'description': 'Git blame selected file(s) with Sublime Merge. (WindowCommand) Observed on '
                       'Sublime Text 4215: opens a native OS window ("Sublime Merge Not Found") '
                       "that blocks Sublime's main thread until a person dismisses it.",
        'inputSchema': {'type': 'object', 'properties': {'files': {'type': 'array'}}}},
    {   'name': 'sublime_merge_file_history',
        'description': 'Show the history of the selected file(s) in Sublime Merge. (WindowCommand) '
                       'Observed on Sublime Text 4215: opens a native OS window ("Sublime Merge '
                       'Not Found") that blocks Sublime\'s main thread until a person dismisses '
                       'it.',
        'inputSchema': {'type': 'object', 'properties': {'files': {'type': 'array'}}}},
    {   'name': 'sublime_merge_folder_history',
        'description': 'Show the history of the selected folder(s) in Sublime Merge. '
                       '(WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {'paths': {'type': 'array'}}}},
    {   'name': 'sublime_merge_line_history',
        'description': 'Shows the history of the selected line(s) in Sublime Merge. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'sublime_merge_open_repo',
        'description': 'Open the repository of the selected file/folder in Sublime Merge. '
                       '(WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'swap_case',
        'description': 'Swap the case of each character in the current selection(s) (upper↔lower).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'swap_line_down',
        'description': 'Swap the current line(s) with the line below.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'swap_line_up',
        'description': 'Swap the current line(s) with the line above.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'swap_with_mark',
        'description': 'Swap the cursor position with the previously set mark (TextCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'switch_file',
        'description': 'Switch between files with the same base name and different extensions '
                       '(WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'syntax_definition_compatability',
        'description': 'Checks to see the syntax compatability of the currently active '
                       '<b>.sublime-syntax</b> file. Any incompatible regex patterns (which '
                       "doesn't conform to sregex) is shown in an output panel. (WindowCommand)",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'syntax_definition_compatibility',
        'description': 'Check syntax definition compatibility (ApplicationCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'tab',
        'description': 'Indent the current selection by one indentation level (TextCommand). '
                       'Equivalent to Tab when there is a selection.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'title_case',
        'description': 'Convert the current selection(s) to Title Case.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_bookmark',
        'description': 'Toggle a bookmark on the current line of the active view.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_case',
        'description': 'Alias of swap_case — toggle the case of each character in the selection.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_case_sensitive',
        'description': "Toggles the 'Case sensitive' flag in the Find/Replace/Incremental "
                       'Find/Find in Files panel. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_comment',
        'description': 'Toggle line comment (or block comment if block=true) on the current '
                       'selection.',
        'inputSchema': {   'type': 'object',
                           'properties': {'block': {'type': 'boolean', 'default': False}}}},
    {   'name': 'toggle_distraction_free',
        'description': 'Toggle distraction-free mode (hides side bar, minimap, status bar, tabs, '
                       'etc.).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_full_screen',
        'description': 'Toggle Sublime Text full-screen mode.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_highlight',
        'description': "Toggles the 'Highlight matches' flag in the Find/Replace/Incremental Find "
                       'panel. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_in_selection',
        'description': "Toggles the 'In selection' flag in the Find/Replace/Incremental Find "
                       'panel. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_inline_diff',
        'description': 'Toggles whether the inline diff of the modifications under the cursor '
                       'location(s) is displayed. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'prefer_hide': {   'type': 'boolean',
                                                                'description': 'Whether to hide '
                                                                               'the other visible '
                                                                               'diffs, while '
                                                                               'showing the ones '
                                                                               'under the cursor '
                                                                               'location(s).'}}}},
    {   'name': 'toggle_menu',
        'description': 'Show or hide the top menu bar.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_minimap',
        'description': 'Show or hide the minimap (the zoomed-out code overview on the right '
                       'gutter).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_overwrite',
        'description': 'Toggles whether the caret is in insert mode or overwrite mode. '
                       '(TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_preserve_case',
        'description': "Toggles the 'Preserve case' flag in the Replace panel. (WindowCommand)",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_record_macro',
        'description': 'Start or stop recording a macro (keystrokes are captured until this is '
                       'called again).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_regex',
        'description': "Toggles the 'Regular expression' flag in the Find/Replace/Incremental "
                       'Find/Find in Files panel. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_save_all_on_build',
        'description': 'Enables/Disables saving all open files before running a build command. '
                       '(WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_setting',
        'description': 'Toggles the specified boolean setting. (TextCommand)',
        'inputSchema': {   'type': 'object',
                           'properties': {   'setting': {   'type': 'string',
                                                            'description': 'The boolean setting to '
                                                                           'toggle.'}}}},
    {   'name': 'toggle_show_context',
        'description': "Toggles the 'Show Context' flag in the Find in Files panel. "
                       '(WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_show_open_files',
        'description': 'Toggles the visibility of the list of open files in the sidebar. '
                       '(WindowCommand) Observed on Sublime Text 4215: shows an in-app panel, '
                       'popup or overlay (dismiss with hide_overlay, hide_panel or hide_popup).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_side_bar',
        'description': 'Show or hide the left side bar (folder tree). Distinct from toggle_sidebar '
                       'which is the MCP control-panel toggle.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_sidebar',
        'description': 'Show or hide the Sublime Text sidebar.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_status_bar',
        'description': 'Show or hide the bottom status bar.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_tabs',
        'description': 'Show or hide the tab bar at the top of the view area.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_use_buffer',
        'description': "Toggles the 'Use Buffer' flag in the Find in Files panel. (WindowCommand)",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_use_gitignore',
        'description': "Toggles the 'Use gitignore' flag in the Find in Files panel. "
                       '(WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_whole_word',
        'description': "Toggles the 'Whole word' flag in the Find/Replace/Incremental Find/Find in "
                       'Files panel. (WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_wrap',
        'description': "Toggles the 'Wrap' flag in Find/Replace/Incremental Find panel. "
                       '(WindowCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'transformer',
        'description': 'Apply a transformer (case conversion, encoding, etc.) to the current '
                       'selection (TextCommand). A general-purpose text-transform base command.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'transpose',
        'description': 'Transpose characters at the cursor (swap the two characters on either side '
                       'of the cursor). Ctrl+T equivalent.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'transpose_chars',
        'description': 'Alias of transpose — swap the two characters adjacent to the cursor.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'trim_trailing_white_space',
        'description': 'Remove trailing whitespace from every line in the current selection (or '
                       'the whole file if no selection).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'trim_whitespace',
        'description': 'Alias of trim_trailing_white_space — remove trailing whitespace from the '
                       'selection/file.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'trim_whitespaces',
        'description': 'Alias of trim_trailing_white_space — remove trailing whitespace from the '
                       'selection/file.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'undo',
        'description': 'Undo the last edit in the active file.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'unexpand_tabs',
        'description': 'Convert leading spaces in the current selection (or whole file) to tabs, '
                       "using the view's tab_size.",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'unfold',
        'description': 'Unfolds all folded region(s) at the given caret location(s). (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'unfold_all',
        'description': 'Unfolds all folded region(s) in the given buffer. (TextCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'unindent',
        'description': 'Unindent the current selection(s) by one indentation level (Shift+Tab when '
                       'there is a selection).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'unselect_others',
        'description': 'Collapse tab multi-selection to the focused sheet.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'unselect_to_left',
        'description': 'Remove sheets left of the focused sheet from the tab multi-selection.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'unselect_to_right',
        'description': 'Remove sheets right of the focused sheet from the tab multi-selection.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'update_check',
        'description': 'Opens the update dialog box of Sublime Text. (ApplicationCommand) Observed '
                       'on Sublime Text 4215: opens a separate window ("Update").',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'upgrade_license',
        'description': 'Navigates to https://www.sublimehq.com/store/upgrade, where you can '
                       'upgrade an expired license. (ApplicationCommand)',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'upper_case',
        'description': 'Convert the current selection(s) to UPPER CASE.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'view_resource',
        'description': 'Open a read-only view of a bundled or packaged resource (WindowCommand). '
                       "Pass 'resource'.",
        'inputSchema': {   'type': 'object',
                           'properties': {'resource': {'type': 'string'}},
                           'required': ['resource']}},
    {   'name': 'wrap_block',
        'description': "Wrap lines in the selection as a block comment using the active syntax's "
                       'block comment markers (TextCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'wrap_lines',
        'description': 'Re-wrap the current selection(s) at the configured wrap width. Alt+Q '
                       'equivalent.',
        'inputSchema': {   'type': 'object',
                           'properties': {   'width': {   'type': 'integer',
                                                          'default': 0,
                                                          'description': 'Optional wrap width in '
                                                                         'columns. 0 = use the '
                                                                         "view's wrap_width "
                                                                         'setting.'}}}},
    {   'name': 'yank',
        'description': 'Yank (paste) the most recently killed/deleted text at the cursor. '
                       'Emacs-style kill-ring paste.',
        'inputSchema': {'type': 'object', 'properties': {}}}]
