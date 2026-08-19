"""GENERATED FILE - do not edit. Produced by tools/generate_fallback_catalog.py from packages/st-plugin/sublime_mcp.py::_MCP_TOOLS. Regenerate after changing the backend tool catalog."""

TOOLS = [   {   'name': 'add_folder',
        'description': 'Add a folder to the current project.',
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string'}},
                           'required': ['path']}},
    {   'name': 'add_missing_newline',
        'description': 'Alias of ensure_newline_at_eof — add a trailing newline at EOF if absent.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'add_to_kill_ring',
        'description': 'Add the current selection to the kill ring (TextCommand, used by yank).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'arithmetic',
        'description': 'Evaluate the selected expression as arithmetic and replace it with the '
                       "result (TextCommand). Select '2+2' to get '4'.",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'auto_complete_goto_definition',
        'description': 'Auto-complete and goto the definition of the symbol under the cursor '
                       '(TextCommand).',
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
    {   'name': 'clear_bookmarks',
        'description': 'Clear all bookmarks in the active view.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'clear_fields',
        'description': 'Clear the current snippet field highlights (used after inserting a snippet '
                       'with $1/$2 tab stops).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'clone_file',
        'description': 'Create a clone of the active view (opens the same file in a new tab, '
                       'sharing the buffer).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_all',
        'description': 'Close all open files/views in the current window.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_file',
        'description': 'Close a file by path, or close the active file if path is omitted.',
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string', 'default': ''}}}},
    {   'name': 'close_other_tabs',
        'description': 'Alias of close_others — close all views in the current group except the '
                       'active one.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_others',
        'description': 'Close all views in the current group except the active one (Close Other '
                       'Tabs).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_pane',
        'description': 'Close the current pane/group and all views inside it.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_transient',
        'description': 'Close all transient views (preview tabs) in the current window.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'close_unmodified',
        'description': 'Close all unmodified (clean) views in the current window.',
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
    {   'name': 'copy_path',
        'description': "Copy the active file's path to the clipboard (WindowCommand).",
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'customize_color_scheme',
        'description': 'Open the active color scheme for customization (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'customize_theme',
        'description': 'Open the active theme for customization (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'cut',
        'description': 'Cut the current selection(s) to the clipboard.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'delete_to_mark',
        'description': 'Delete the text between the cursor and the previously set mark '
                       '(TextCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'detect_indentation',
        'description': "Auto-detect the file's indentation style (tabs vs spaces, width) and set "
                       "the view's indent settings accordingly.",
        'inputSchema': {'type': 'object', 'properties': {}}},
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
    {   'name': 'expand_tabs',
        'description': 'Convert leading tabs in the current selection (or whole file) to spaces, '
                       "using the view's tab_size.",
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
    {   'name': 'focus_group',
        'description': 'Move focus to a pane group by 0-based index.',
        'inputSchema': {   'type': 'object',
                           'properties': {'group': {'type': 'integer'}},
                           'required': ['group']}},
    {   'name': 'focus_neighboring_group',
        'description': 'Move focus to the neighboring pane group (cycle through panes).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'fold_lines',
        'description': 'Fold (collapse) lines begin through end (1-based) in the active file.',
        'inputSchema': {   'type': 'object',
                           'properties': {'begin': {'type': 'integer'}, 'end': {'type': 'integer'}},
                           'required': ['begin', 'end']}},
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
    {   'name': 'get_console_full',
        'description': 'Return the entire captured ST console buffer with no tail limit.\n'
                       'Includes startup messages, plugin load events, and all errors since ST '
                       'started.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'get_console_log',
        'description': 'Return recent Sublime Text console output (plugin log messages and '
                       'stdout).\n'
                       'tail=N limits to the last N entries. tail=0 returns all captured entries.',
        'inputSchema': {   'type': 'object',
                           'properties': {'tail': {'type': 'integer', 'default': 100}}}},
    {   'name': 'get_console_win',
        'description': 'Windows-only fallback: captures ST console by clicking the output area via '
                       'ctypes then Ctrl+A/Ctrl+C.\n'
                       'Use when get_console_full fails. Returns error on non-Windows.',
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
                       'build output.',
        'inputSchema': {   'type': 'object',
                           'properties': {'name': {'type': 'string', 'default': ''}}}},
    {   'name': 'get_package_mcp_info',
        'description': 'Return everything needed to write an MCP extension for an installed '
                       'Package Control package.\n'
                       'Returns: path, output_file, commands (with captions and args), '
                       'settings_keys, python_files, extension_template.\n'
                       'Write the extension to output_file following extension_template; ST loads '
                       'it automatically.',
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
    {   'name': 'get_sheets',
        'description': 'List ALL sheets (tabs) in the current window by index, including images '
                       'and untitled buffers.\n'
                       'Returns index, type (TextSheet/ImageSheet), path, name, is_dirty for '
                       'each.\n'
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
    {   'name': 'html_print',
        'description': 'Open the current file as HTML for printing (TextCommand). Equivalent to '
                       'File > Print.',
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
    {   'name': 'lookup_symbol',
        'description': 'Find where a symbol is defined across all open files.',
        'inputSchema': {   'type': 'object',
                           'properties': {'symbol': {'type': 'string'}},
                           'required': ['symbol']}},
    {   'name': 'lower_case',
        'description': 'Convert the current selection(s) to lower case.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'move_line_down',
        'description': 'Move the current line(s) down by one line.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'move_line_up',
        'description': 'Move the current line(s) up by one line.',
        'inputSchema': {'type': 'object', 'properties': {}}},
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
    {   'name': 'next_bookmark',
        'description': 'Move the cursor to the next bookmark in the active view.',
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
    {   'name': 'open_symbol_definition',
        'description': "Open the definition of a named symbol (WindowCommand). Pass 'symbol'.",
        'inputSchema': {   'type': 'object',
                           'properties': {'symbol': {'type': 'string'}},
                           'required': ['symbol']}},
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
    {   'name': 'profile_plugins',
        'description': 'Profile plugin load times (ApplicationCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'profile_syntax_definition',
        'description': 'Profile a syntax definition for performance issues (ApplicationCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'prompt_goto_line',
        'description': 'Open the Goto Line prompt (WindowCommand).',
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
    {   'name': 'reindent',
        'description': "Re-indent the current selection(s) so each line's indentation matches its "
                       'nesting depth.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'remove_folder',
        'description': 'Remove a folder from the current project by path.',
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string'}},
                           'required': ['path']}},
    {   'name': 'rename_file',
        'description': "Rename the active file (WindowCommand). Pass 'path' for the new name.",
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string'}},
                           'required': ['path']}},
    {   'name': 'reopen_closed_file',
        'description': 'Reopen the most recently closed file (File → Reopen Closed File).',
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
    {   'name': 'replace_selection',
        'description': 'Replace the current selection(s) with text.',
        'inputSchema': {   'type': 'object',
                           'properties': {'text': {'type': 'string'}},
                           'required': ['text']}},
    {   'name': 'revert_file',
        'description': 'Revert the active file to its last saved state, discarding unsaved '
                       'changes.',
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
        'description': "Run any Sublime Text command. scope='window' (default) or 'view'.",
        'inputSchema': {   'type': 'object',
                           'properties': {   'command': {'type': 'string'},
                                             'args': {'type': 'object'},
                                             'scope': {'type': 'string', 'default': 'window'}},
                           'required': ['command']}},
    {   'name': 'run_macro',
        'description': 'Play back the most recently recorded macro at the cursor.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'run_syntax_tests',
        'description': 'Run syntax tests on the active syntax file (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'save_all',
        'description': 'Save all open files.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'save_file',
        'description': 'Save a file. Pass path to save a specific open file; omit path to save the '
                       'active file.',
        'inputSchema': {   'type': 'object',
                           'properties': {'path': {'type': 'string', 'default': ''}}}},
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
    {   'name': 'select_all',
        'description': 'Select the entire contents of the active view (Ctrl+A equivalent).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'select_all_bookmarks',
        'description': 'Select every line containing a bookmark in the active view.',
        'inputSchema': {'type': 'object', 'properties': {}}},
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
    {   'name': 'select_theme',
        'description': 'Open the theme picker (WindowCommand).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'select_to_mark',
        'description': 'Select the text between the cursor and the previously set mark '
                       '(TextCommand).',
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
    {   'name': 'set_encoding',
        'description': "Set the character encoding of the active file (e.g. 'UTF-8', 'Western "
                       "(Windows 1252)').",
        'inputSchema': {   'type': 'object',
                           'properties': {'encoding': {'type': 'string'}},
                           'required': ['encoding']}},
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
    {   'name': 'show_at_center',
        'description': 'Scroll the active view so the current cursor line is centered in the '
                       'window.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'show_panel',
        'description': "Bring an output panel to the front. Use name='exec' for the build panel.",
        'inputSchema': {   'type': 'object',
                           'properties': {'name': {'type': 'string', 'default': 'exec'}}}},
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
    {   'name': 'toggle_menu',
        'description': 'Show or hide the top menu bar.',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_minimap',
        'description': 'Show or hide the minimap (the zoomed-out code overview on the right '
                       'gutter).',
        'inputSchema': {'type': 'object', 'properties': {}}},
    {   'name': 'toggle_record_macro',
        'description': 'Start or stop recording a macro (keystrokes are captured until this is '
                       'called again).',
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
    {   'name': 'unindent',
        'description': 'Unindent the current selection(s) by one indentation level (Shift+Tab when '
                       'there is a selection).',
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
