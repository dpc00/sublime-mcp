"""Build tool_tree.json: the hierarchy that discover_tools walks.

Every tool except the ones advertised by default is placed in exactly one leaf
(path such as "editing/lines"). Run after adding tools; the unit test
test/test_tool_tree.py fails when a tool is missing or listed twice.
"""

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DESCRIPTIONS = {
    "files": "Open, create, save, close, rename and delete files",
    "files/open_and_create": "Open or create files, folders and recent items",
    "files/save_and_close": "Save, revert and close files, tabs and windows' views",
    "files/manage": "Rename, delete, copy a path, reveal a file",
    "tabs": "Tabs (sheets), panes and layouts",
    "tabs/sheets": "Select, focus, move and close tabs",
    "tabs/panes": "Pane layout and moving between groups",
    "editing": "Change text",
    "editing/basic": "Insert, replace, undo and redo",
    "editing/clipboard": "Cut, copy and paste",
    "editing/lines": "Line operations: move, join, sort, swap, indent",
    "editing/case_and_whitespace": "Change case, trim and normalise whitespace",
    "editing/snippets_macros_fields": "Snippets, macros, tag helpers and snippet fields",
    "editing/delete": "Delete words and characters",
    "selection": "Cursors and selections",
    "selection/select": "Select all, lines, words, brackets, scope",
    "selection/marks_and_history": "Mark, kill ring, jump back and forward",
    "search": "Find, replace and go to symbols",
    "search/find_in_file": "Find and replace inside the current file",
    "search/find_in_files": "Find and replace across files and folders",
    "search/symbols": "Symbols, definitions and references",
    "search/bookmarks": "Bookmarks",
    "read": "Read state from the editor without changing it",
    "read/text": "File, view and sheet contents",
    "read/state": "Selection, cursor, panels, layout, syntax, encoding, settings",
    "read/catalog": "Commands, menu items, palette entries, packages",
    "read/console": "Sublime's console",
    "view": "What the window shows",
    "view/folding": "Fold and unfold code",
    "view/scrolling": "Scroll and centre",
    "view/panels_and_popups": "Panels, overlays, popups, quick panels, status bar",
    "view/toggles": "Turn UI parts and view options on or off",
    "view/font_and_wrap": "Font size and word wrap",
    "project": "Project folders and workspaces",
    "project/folders": "Add, remove and refresh project folders",
    "project/workspaces": "Open and save projects and workspaces",
    "settings": "Settings, syntax, encoding, themes and colour schemes",
    "settings/editor": "Get and set settings, syntax, encoding, line endings, indentation",
    "settings/appearance": "Themes and colour schemes",
    "settings/build": "Build systems and building",
    "run": "Run code and commands",
    "run/python": "Run Python in Sublime or on the system",
    "run/commands": "Run a Sublime command by name",
    "run/build_and_exec": "Builds and external programs",
    "run/macros": "Record and play macros",
    "packages_and_dev": "Packages and plugin development",
    "packages_and_dev/packages": "Search, install and inspect packages",
    "packages_and_dev/create": "Create new plugins, snippets, syntaxes, build systems",
    "packages_and_dev/diagnostics": "Profiling, syntax tests and diagnostics",
    "app": "The Sublime Text application and its windows",
    "app/windows": "Windows, OS tabs and full screen",
    "app/native_dialogs": "Native dialogs and menus that block Sublime",
    "app/prompts": "Commands that open a file or folder chooser",
    "app/license_and_updates": "License, about, changelog, update check",
    "app/exit": "Commands that quit Sublime",
    "app/merge_and_web": "Sublime Merge and browser links",
    "app/misc": "Other application commands",
}

# tool -> leaf path.  Explicit names first; RULES catch the rest.
EXPLICIT = {}


def put(path, names):
    for n in names.split():
        if n in EXPLICIT:
            raise SystemExit("placed twice: {} ({} and {})".format(n, EXPLICIT[n], path))
        EXPLICIT[n] = path


put("files/open_and_create", "open_file new_file new_view new_file_at new_folder open_recent_file open_recent_folder "
    "open_recent_project_or_workspace reopen reopen_last_file reopen_closed_file clone_file switch_file open_dir "
    "open_folder open_containing_folder view_resource open_file_settings send_to_view")
put("files/save_and_close", "save_all revert_file revert revert_hunk revert_modification save close_file "
    "close_all close_others close_other_tabs close_unmodified close_pane close_transient close_deleted_files "
    "close_by_index close_others_by_index close_selected close_unselected close_to_right_by_index "
    "close_unmodified_to_right_by_index close")
put("files/manage", "rename_file rename_path delete_file delete_folder copy_path reveal_in_side_bar reveal_link_source "
    "clear_recent_files clear_missing_recent_projects_and_workspaces clear_recent_projects_and_workspaces")
put("tabs/sheets", "get_sheets get_selected_sheets get_sheet_index select_sheets focus_sheet set_sheet_index "
    "move_sheets_to_group next_view prev_view next_view_in_stack prev_view_in_stack move_view focus_by_index "
    "select_by_index select next_os_tab prev_os_tab new_os_tab")
put("tabs/panes", "get_layout set_layout focus_group focus_to_left focus_to_right new_pane next_pane prev_pane "
    "focus_neighboring_group move_to_neighboring_group move_to_group set_max_columns move move_to")
put("editing/basic", "replace_selection replace_lines insert undo redo soft_undo soft_redo "
    "redo_or_repeat overwrite toggle_overwrite echo noop append replace_all")
put("editing/clipboard", "paste paste_from_history paste_and_indent cut copy yank paste_selection_clipboard copy_as_html")
put("editing/lines", "duplicate_line sort_lines join_lines split_line swap_line_up swap_line_down move_line_up "
    "move_line_down indent unindent reindent auto_indent wrap_lines permute_lines transpose transpose_chars "
    "sort_selection permute_selection old_wrap_lines wrap_block toggle_comment")
put("editing/case_and_whitespace", "upper_case lower_case title_case swap_case toggle_case convert_ident_case "
    "trim_trailing_white_space trim_whitespace trim_whitespaces ensure_newline_at_eof add_missing_newline "
    "expand_tabs unexpand_tabs detect_indentation set_indent_tabs set_indent_spaces rot13 "
    "encode_html_entities transformer arithmetic tab")
put("editing/snippets_macros_fields", "insert_snippet expand_snippet next_field prev_field clear_fields close_tag "
    "auto_indent_tag add_where_snippet commit_completion auto_complete auto_complete_prev auto_complete_open_link "
    "hide_auto_complete replace_completion_with_auto_complete")
put("editing/delete", "left_delete right_delete delete_word delete_to_mark")
put("selection/select", "get_selection select_all expand_selection expand_selection_to_paragraph "
    "expand_selection_to_indentation expand_selection_to_scope expand_selection_to_brackets shrink_selection "
    "split_selection_into_lines single_selection invert_selection select_lines unselect_others unselect_to_left "
    "unselect_to_right select_to_left select_to_right old_expand_selection_to_paragraph drag_select "
    "find_all_under select_all_bookmarks select_bookmark")
put("selection/marks_and_history", "clear_location set_mark select_to_mark swap_with_mark add_to_kill_ring jump_back jump_forward "
    "add_jump_record")
put("search/find_in_file", "find_in_file find_and_replace next_result prev_result find_all find_next find_prev "
    "find_under find_under_expand find_under_expand_skip find_under_prev replace_next slurp_find_string "
    "slurp_replace_string toggle_case_sensitive toggle_regex toggle_whole_word toggle_preserve_case "
    "toggle_in_selection toggle_highlight cancel_find")
put("search/find_in_files", "find_in_files replace_in_files find_in_folder toggle_use_buffer toggle_use_gitignore")
put("search/symbols", "get_symbols lookup_symbol goto_definition goto_reference auto_complete_goto_definition "
    "open_symbol_definition goto_symbol_in_project goto_line prompt_goto_line show_scope_name")
put("search/bookmarks", "get_bookmarks toggle_bookmark next_bookmark prev_bookmark clear_bookmarks")
put("read/text", "get_cursor_context get_sheet_content get_file_content get_view_content get_view_size "
    "get_view_chars get_view_phantoms get_output_panel get_word_at_cursor get_line_count")
put("read/state", "get_open_files get_project_folders get_project_data get_variables get_active_panel get_syntaxes "
    "get_encoding get_scope_at_cursor get_setting")
put("read/catalog", "get_command_palette get_commands get_menu_items get_package_mcp_info console_python_version")
put("read/console", "get_console get_console_log get_console_full get_console_win")
put("view/folding", "fold_lines fold_unfold fold fold_all fold_by_level fold_tag_attributes unfold unfold_all")
put("view/scrolling", "scroll_to_bof scroll_to_eof show_at_center scroll_lines")
put("view/panels_and_popups", "show_panel set_status drive_input_panel quick_panel hide_overlay hide_panel hide_popup "
    "context_menu toggle_show_context html_print open_control_panel toggle_show_open_files focus_side_bar "
    "show_progress_window prompt_open cancel")
put("view/toggles", "toggle_sidebar toggle_side_bar toggle_menu toggle_minimap toggle_status_bar toggle_tabs "
    "toggle_distraction_free toggle_full_screen toggle_inline_diff next_modification prev_modification "
    "next_misspelling prev_misspelling correct_spelling add_word ignore_word toggle_setting toggle_save_all_on_build")
put("view/font_and_wrap", "increase_font_size decrease_font_size reset_font_size toggle_wrap")
put("project/folders", "add_folder remove_folder add_directory refresh_folder_list close_folder_list "
    "prompt_add_folder prompt_open_folder")
put("project/workspaces", "open_project_or_workspace prompt_open_project_or_workspace prompt_select_workspace "
    "prompt_switch_project_or_workspace save_project_and_workspace_as save_workspace_as close_workspace "
    "new_window_for_project")
put("settings/editor", "set_setting set_syntax set_encoding set_file_type set_line_ending edit_settings "
    "edit_syntax_settings")
put("settings/appearance", "select_color_scheme select_theme customize_color_scheme customize_theme "
    "convert_color_scheme convert_syntax")
put("settings/build", "set_build_system build cancel_build run_build")
put("run/python", "eval_python eval_python_latest")
put("run/commands", "run_command chain")
put("run/build_and_exec", "exec")
put("run/macros", "toggle_record_macro run_macro play_macro run_macro_file save_macro")
put("packages_and_dev/packages", "search_packages install_package install_package_control")
put("packages_and_dev/create", "new_build_system new_plugin new_snippet new_syntax")
put("packages_and_dev/diagnostics", "profile_plugins profile_syntax_definition syntax_definition_compatibility "
    "syntax_definition_compatability run_syntax_tests diagnostics main_thread_stack")
put("app/windows", "new_window close_window resize_window")
put("app/native_dialogs", "list_native_windows dismiss_native_window")
put("app/prompts", "prompt_open_file prompt_save_as")
put("app/license_and_updates", "purchase_license upgrade_license remove_license show_license_window "
    "show_about_window show_changelog update_check")
put("app/exit", "exit hot_exit")
put("app/merge_and_web", "sublime_merge_blame_file sublime_merge_file_history sublime_merge_folder_history "
    "sublime_merge_line_history sublime_merge_open_repo open_url open_in_browser open_context_url")
put("app/misc", "primary_j_changed")

DEFAULT_ADVERTISED = {"get_help", "batch", "get_active_file", "project_search",
                      "str_replace_based_edit_tool", "save_file", "discover_tools"}


def tool_names():
    tree = ast.parse((ROOT / "sublime_mcp.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_MCP_TOOLS" for t in node.targets):
            return [e.elts[0].value for e in node.value.elts]
    raise SystemExit("_MCP_TOOLS not found")


def main():
    names = [n for n in tool_names() if n not in DEFAULT_ADVERTISED]
    leaves = {}
    missing = []
    for n in names:
        path = EXPLICIT.get(n)
        if path is None:
            missing.append(n)
        else:
            leaves.setdefault(path, []).append(n)
    if missing:
        raise SystemExit("unplaced tools: " + " ".join(missing))
    unknown = [n for n in EXPLICIT if n not in set(names)]
    if unknown:
        print("note: placed but not in catalog (or advertised by default):", " ".join(unknown))
    out = {}
    for path in sorted(leaves):
        top = path.split("/")[0]
        out.setdefault(top, {"description": DESCRIPTIONS[top], "children": {}})
        out[top]["children"][path.split("/")[1]] = {
            "description": DESCRIPTIONS[path], "tools": sorted(leaves[path])}
    (ROOT / "tool_tree.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("placed", len(names), "tools in", len(leaves), "leaves under", len(out), "categories")


if __name__ == "__main__":
    main()
