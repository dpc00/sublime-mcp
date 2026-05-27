"""
Comprehensive integration tests for the sublime-mcp HTTP API (port 9500).

Prerequisites:
  - Sublime Text must be running with sublime_mcp.py loaded
  - At least one file must be open in ST

Run:
  cd C:\\Users\\donal\\projects\\sublime-mcp
  pytest tests/test_http_api.py -v

Tests are grouped into:
  - Connectivity
  - Read-only GET endpoints
  - View targeting (by name / by index)
  - Write/edit POST endpoints (use a scratch buffer, all changes undone)
  - Navigation
  - Search
  - Settings
  - Layout / window
  - Scripting (eval_python)
  - Error handling
"""

import time
import httpx
import pytest

BASE = "http://127.0.0.1:9500"
TIMEOUT = 10.0


# ── helpers ───────────────────────────────────────────────────────────────────


def get(endpoint, **params):
    r = httpx.get(f"{BASE}{endpoint}", params=params, timeout=TIMEOUT)
    return r


def post(endpoint, **body):
    r = httpx.post(f"{BASE}{endpoint}", json=body, timeout=TIMEOUT)
    return r


def ok(r):
    """Assert 200 and return parsed JSON."""
    assert r.status_code == 200, f"{r.url} → {r.status_code}: {r.text}"
    return r.json()


# ── connectivity ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def require_server():
    """Skip entire session if ST is not running."""
    try:
        httpx.get(f"{BASE}/open_files", timeout=2.0)
    except httpx.ConnectError:
        pytest.skip("ST not running on port 9500 — start Sublime Text first")


# ── scratch buffer fixture ────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def scratch_path(tmp_path_factory):
    """Create a real temp file, open it in ST, yield its path, then close it."""
    p = tmp_path_factory.mktemp("sublime_mcp_test") / "scratch.txt"
    p.write_text("line one\nline two\nline three\n", encoding="utf-8")
    r = post("/open_file", path=str(p))
    assert r.status_code == 200
    time.sleep(0.3)  # give ST time to open it
    yield str(p)
    post("/close_file", path=str(p))


# ══ GET endpoints ═════════════════════════════════════════════════════════════


class TestGetActiveFile:
    def test_returns_200(self):
        r = get("/active_file")
        assert r.status_code == 200

    def test_has_required_keys(self):
        d = ok(get("/active_file"))
        assert "content" in d
        assert "line" in d
        assert "col" in d
        assert "is_dirty" in d
        assert "syntax" in d

    def test_content_is_string(self):
        d = ok(get("/active_file"))
        assert isinstance(d["content"], str)

    def test_cursor_line_is_int(self):
        d = ok(get("/active_file"))
        assert isinstance(d["line"], int)


class TestGetSelection:
    def test_returns_200(self):
        assert get("/selection").status_code == 200

    def test_has_selections_list(self):
        d = ok(get("/selection"))
        assert "selections" in d
        assert isinstance(d["selections"], list)

    def test_each_selection_has_text(self):
        d = ok(get("/selection"))
        for sel in d["selections"]:
            assert "text" in sel


class TestGetCursorContext:
    def test_default_lines(self):
        d = ok(get("/cursor_context"))
        assert "context" in d

    def test_custom_lines(self):
        d = ok(get("/cursor_context", lines=5))
        assert "context" in d

    def test_zero_lines(self):
        r = get("/cursor_context", lines=0)
        assert r.status_code == 200


class TestGetOpenFiles:
    def test_returns_list(self):
        d = ok(get("/open_files"))
        assert "files" in d
        assert isinstance(d["files"], list)

    def test_each_file_has_name(self):
        d = ok(get("/open_files"))
        for f in d["files"]:
            assert "name" in f
            assert "is_dirty" in f


class TestGetProjectFolders:
    def test_returns_folders(self):
        d = ok(get("/project_folders"))
        assert "folders" in d
        assert isinstance(d["folders"], list)


class TestGetFileContent:
    def test_active_file_content(self):
        af = ok(get("/active_file"))
        path = af.get("path")
        if not path:
            pytest.skip("active file has no path (untitled)")
        d = ok(get("/file_content", path=path))
        assert "content" in d
        assert isinstance(d["content"], str)

    def test_missing_path_returns_error(self):
        r = get("/file_content", path="C:\\nonexistent\\file.txt")
        d = r.json()
        assert "error" in d or r.status_code != 200


class TestGetViewContent:
    def test_active_view_no_params(self):
        d = ok(get("/view_content"))
        assert "content" in d

    def test_by_index_zero(self):
        d = ok(get("/view_content", index=0))
        assert "content" in d

    def test_by_name_partial(self):
        files = ok(get("/open_files"))["files"]
        names = [f["name"] for f in files if f["name"]]
        if not names:
            pytest.skip("no named views open")
        partial = names[0][:3]
        d = ok(get("/view_content", name=partial))
        assert "content" in d

    def test_invalid_index_returns_error(self):
        d = ok(get("/view_content", index=9999))
        assert "error" in d

    def test_invalid_name_returns_error(self):
        d = ok(get("/view_content", name="ZZZNOMATCHZZZ"))
        assert "error" in d


class TestGetViewSize:
    def test_returns_size(self):
        d = ok(get("/view_size"))
        assert "size" in d
        assert isinstance(d["size"], int)
        assert d["size"] >= 0

    def test_by_index(self):
        d = ok(get("/view_size", index=0))
        assert "size" in d


class TestGetViewChars:
    def test_read_first_100_chars(self):
        size = ok(get("/view_size"))["size"]
        end = min(100, size)
        if end == 0:
            pytest.skip("active view is empty")
        d = ok(get("/view_chars", begin=0, end=end))
        assert "content" in d
        assert isinstance(d["content"], str)

    def test_read_last_100_chars(self):
        size = ok(get("/view_size"))["size"]
        if size == 0:
            pytest.skip("active view is empty")
        begin = max(0, size - 100)
        d = ok(get("/view_chars", begin=begin, end=size))
        assert "content" in d

    def test_clamps_past_end(self):
        size = ok(get("/view_size"))["size"]
        d = ok(get("/view_chars", begin=0, end=size + 10000))
        assert "content" in d

    def test_zero_range(self):
        d = ok(get("/view_chars", begin=0, end=0))
        assert d["content"] == ""


class TestGetOutputPanel:
    def test_returns_200(self):
        assert get("/output_panel").status_code == 200

    def test_exec_panel(self):
        d = ok(get("/output_panel", name="exec"))
        assert "content" in d or "error" in d


class TestGetSymbols:
    def test_returns_symbols(self):
        d = ok(get("/symbols"))
        assert "symbols" in d
        assert isinstance(d["symbols"], list)


class TestLookupSymbol:
    def test_known_builtin(self):
        d = ok(get("/lookup_symbol", symbol="def"))
        assert "locations" in d or "error" in d

    def test_empty_symbol(self):
        r = get("/lookup_symbol", symbol="")
        assert r.status_code == 200


class TestGetProjectData:
    def test_returns_project_data(self):
        d = ok(get("/project_data"))
        assert "project_data" in d


class TestGetVariables:
    def test_returns_variables(self):
        d = ok(get("/variables"))
        # response is flat dict of variable key→value
        assert isinstance(d, dict)
        assert len(d) > 0

    def test_has_platform(self):
        d = ok(get("/variables"))
        assert "platform" in d


class TestGetBookmarks:
    def test_returns_bookmarks(self):
        d = ok(get("/bookmarks"))
        assert "bookmarks" in d
        assert isinstance(d["bookmarks"], list)


class TestGetLineCount:
    def test_returns_count(self):
        d = ok(get("/line_count"))
        assert "line_count" in d
        assert isinstance(d["line_count"], int)
        assert d["line_count"] >= 1


class TestGetSyntaxes:
    def test_returns_list(self):
        d = ok(get("/syntaxes"))
        assert "syntaxes" in d
        assert isinstance(d["syntaxes"], list)
        assert len(d["syntaxes"]) > 0

    def test_each_has_name_and_path(self):
        d = ok(get("/syntaxes"))
        for s in d["syntaxes"][:5]:
            assert "name" in s
            assert "path" in s


class TestGetCommandPalette:
    def test_returns_commands(self):
        d = ok(get("/command_palette"))
        assert "entries" in d
        assert isinstance(d["entries"], list)
        assert len(d["entries"]) > 0

    def test_filter_by_caption(self):
        d = ok(get("/command_palette", caption="save"))
        assert "entries" in d

    def test_filter_by_package(self):
        d = ok(get("/command_palette", package="Default"))
        assert "entries" in d


class TestGetCommands:
    def test_returns_commands(self):
        d = ok(get("/commands"))
        assert "commands" in d
        assert isinstance(d["commands"], list)
        assert len(d["commands"]) > 0

    def test_filter_by_command(self):
        d = ok(get("/commands", command="save"))
        assert "commands" in d


class TestGetMenuItems:
    def test_returns_items(self):
        d = ok(get("/menu_items"))
        assert "entries" in d
        assert isinstance(d["entries"], list)
        assert len(d["entries"]) > 0

    def test_filter_by_caption(self):
        d = ok(get("/menu_items", caption="File"))
        assert "entries" in d

    def test_filter_by_command(self):
        d = ok(get("/menu_items", command="save"))
        assert "entries" in d


class TestGetActivePanel:
    def test_returns_200(self):
        d = ok(get("/active_panel"))
        assert "panel" in d or "active_panel" in d or "error" in d


class TestGetScopeAtCursor:
    def test_returns_scope(self):
        d = ok(get("/scope_at_cursor"))
        assert "scope" in d
        assert isinstance(d["scope"], str)


class TestGetEncoding:
    def test_returns_encoding(self):
        d = ok(get("/encoding"))
        assert "encoding" in d
        assert isinstance(d["encoding"], str)


class TestGetWordAtCursor:
    def test_returns_word(self):
        d = ok(get("/word_at_cursor"))
        assert "word" in d


class TestGetLayout:
    def test_returns_layout(self):
        d = ok(get("/layout"))
        assert "layout" in d or "cols" in d or "groups" in d

    def test_has_groups(self):
        d = ok(get("/layout"))
        layout = d.get("layout", d)
        assert "cols" in layout or "groups" in layout or "cells" in layout


# ══ POST write endpoints ══════════════════════════════════════════════════════


class TestSetStatus:
    def test_set_and_clear(self):
        d = ok(post("/set_status", key="pytest_test", value="pytest running"))
        assert d.get("ok") is True
        # clear it
        ok(post("/set_status", key="pytest_test", value=""))


class TestOpenAndCloseFile:
    def test_open_existing_file(self, scratch_path):
        # scratch_path fixture already opened it; open again (idempotent)
        d = ok(post("/open_file", path=scratch_path))
        assert d.get("ok") is True

    def test_open_with_line(self, scratch_path):
        d = ok(post("/open_file", path=scratch_path, line=1))
        assert d.get("ok") is True

    def test_open_nonexistent_returns_ok(self):
        # ST opens a new empty buffer for nonexistent paths rather than erroring
        r = post("/open_file", path="C:\\no\\such\\file.txt")
        assert r.status_code == 200


class TestGotoLine:
    def test_goto_line_1(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/goto_line", line=1))
        assert d.get("ok") is True

    def test_goto_line_with_col(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/goto_line", line=1, col=3))
        assert d.get("ok") is True


class TestReplaceLines:
    def test_replace_line_1(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/replace_lines", begin=1, end=1,
                    text="replaced line one\n", path=scratch_path))
        assert d.get("ok") is True
        # undo
        post("/undo")

    def test_replace_multiple_lines(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/replace_lines", begin=1, end=2,
                    text="new line 1\nnew line 2\n", path=scratch_path))
        assert d.get("ok") is True
        post("/undo")

    def test_replace_by_index(self, scratch_path):
        files = ok(get("/open_files"))["files"]
        idx = next((i for i, f in enumerate(files)
                    if f.get("path") == scratch_path), None)
        if idx is None:
            pytest.skip("scratch file not found by index")
        d = ok(post("/replace_lines", begin=1, end=1,
                    text="index replace\n", index=idx))
        assert d.get("ok") is True
        post("/undo")


class TestReplaceSelection:
    def test_replace_selection(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        post("/select_lines", begin=1, end=1)
        time.sleep(0.1)
        d = ok(post("/replace_selection", text="selection replaced\n"))
        assert d.get("ok") is True
        post("/undo")


class TestSelectLines:
    def test_select_single_line(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/select_lines", begin=1, end=1))
        assert d.get("ok") is True

    def test_select_range(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/select_lines", begin=1, end=3))
        assert d.get("ok") is True


class TestUndoRedo:
    def test_undo(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        post("/replace_lines", begin=1, end=1,
             text="undo test\n", path=scratch_path)
        d = ok(post("/undo"))
        assert d.get("ok") is True

    def test_redo(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        post("/replace_lines", begin=1, end=1,
             text="redo test\n", path=scratch_path)
        post("/undo")
        d = ok(post("/redo"))
        assert d.get("ok") is True


class TestDuplicateLine:
    def test_duplicate(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/duplicate_line"))
        assert d.get("ok") is True
        post("/undo")


class TestToggleComment:
    def test_line_comment(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        post("/select_lines", begin=1, end=1)
        d = ok(post("/toggle_comment", block=False))
        assert d.get("ok") is True
        post("/undo")

    def test_block_comment(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        post("/select_lines", begin=1, end=2)
        d = ok(post("/toggle_comment", block=True))
        assert d.get("ok") is True
        post("/undo")


class TestSortLines:
    def test_sort(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/sort_lines", case_sensitive=False))
        assert d.get("ok") is True
        post("/undo")

    def test_sort_case_sensitive(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/sort_lines", case_sensitive=True))
        assert d.get("ok") is True
        post("/undo")


class TestFoldLines:
    def test_fold(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/fold_lines", begin=1, end=2))
        assert d.get("ok") is True


class TestInsertSnippet:
    def test_insert(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        post("/goto_line", line=3)
        d = ok(post("/insert_snippet", contents="snippet_test_$1"))
        assert d.get("ok") is True
        post("/undo")


class TestFindInFile:
    def _results(self, d):
        return d.get("matches") or d.get("results") or d.get("findings") or d.get("hits") or []

    def test_find_existing_text(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/find_in_file", pattern="line"))
        # just check it responded without error
        assert "error" not in d

    def test_find_no_match(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/find_in_file", pattern="ZZZNOMATCHZZZ"))
        assert "error" not in d

    def test_find_regex(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/find_in_file", pattern=r"line \w+", regex=True))
        assert "error" not in d

    def test_find_case_sensitive(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/find_in_file", pattern="LINE", case_sensitive=True))
        assert "error" not in d


SMALL_FOLDER = "C:\\Users\\donal\\projects\\sublime-mcp"


class TestFindInFiles:
    def test_find_across_project(self):
        # Scope to the small sublime-mcp repo only — never the full projects tree
        d = ok(post("/find_in_files", pattern="def ", folders=[SMALL_FOLDER]))
        assert "results" in d or "matches" in d or "findings" in d

    def test_find_no_match(self):
        # Search mcp_server.py only — a source file that will never contain a test-internal pattern
        d = ok(post("/find_in_files",
                    pattern="XQZPATTERN_NOT_IN_SOURCE",
                    folders=[SMALL_FOLDER],
                    max_results=1))
        # Filter out any match from the test file itself
        results = d.get("results") or d.get("matches") or d.get("findings") or []
        non_test = [r for r in results if "test_" not in r.get("path", "")]
        assert non_test == []


class TestSetSyntax:
    def test_set_plain_text(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/set_syntax", name="Plain Text"))
        assert d.get("ok") is True

    def test_set_python(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/set_syntax", name="Python"))
        assert d.get("ok") is True
        post("/set_syntax", name="Plain Text")

    def test_set_nonexistent_syntax(self):
        d = ok(post("/set_syntax", name="ZZZNOSUCHSYNTAXZZZ"))
        assert "error" in d or d.get("ok") is True


class TestSetEncoding:
    def test_set_utf8(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/set_encoding", encoding="UTF-8"))
        assert d.get("ok") is True


def _post_json(endpoint, body):
    """Post with an explicit dict body — avoids kwarg name conflicts."""
    r = httpx.post(f"{BASE}{endpoint}", json=body, timeout=TIMEOUT)
    return r


class TestGetSetting:
    def test_get_tab_size(self):
        d = ok(_post_json("/get_setting", {"key": "tab_size", "scope": "view"}))
        assert "value" in d

    def test_get_word_wrap(self):
        d = ok(_post_json("/get_setting", {"key": "word_wrap", "scope": "view"}))
        assert "value" in d


class TestSetSetting:
    def test_set_and_restore_tab_size(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        orig = ok(_post_json("/get_setting", {"key": "tab_size", "scope": "view"}))["value"]
        d = ok(_post_json("/set_setting", {"key": "tab_size", "value": 2, "scope": "view"}))
        assert d.get("ok") is True
        _post_json("/set_setting", {"key": "tab_size", "value": orig, "scope": "view"})


class TestSaveFile:
    def test_save_scratch(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/save_file", path=scratch_path))
        assert d.get("ok") is True

    def test_save_active(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/save_file"))
        assert d.get("ok") is True


class TestSaveAll:
    def test_save_all(self):
        d = ok(post("/save_all"))
        assert d.get("ok") is True


class TestRunCommand:
    def test_window_command(self):
        # Use a safe non-blocking command that doesn't open a modal
        d = ok(post("/run_command", command="new_window", args={}, scope="window"))
        assert d.get("ok") is True
        # close the new window immediately
        post("/run_command", command="close_window", args={}, scope="window")

    def test_view_command(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        d = ok(post("/run_command", command="move",
                    args={"by": "lines", "forward": True}, scope="view"))
        assert d.get("ok") is True


class TestShowPanel:
    def test_show_exec_panel(self):
        d = ok(post("/show_panel", name="exec"))
        assert d.get("ok") is True


class TestToggleSidebar:
    def test_toggle_twice(self):
        d1 = ok(post("/toggle_sidebar"))
        assert d1.get("ok") is True
        d2 = ok(post("/toggle_sidebar"))
        assert d2.get("ok") is True


class TestFocusGroup:
    def test_focus_group_0(self):
        d = ok(post("/focus_group", group=0))
        assert d.get("ok") is True

    def test_focus_invalid_group(self):
        r = post("/focus_group", group=9999)
        d = r.json()
        assert "error" in d or d.get("ok") is True


class TestSetLayout:
    def test_single_column(self):
        single = {"cols": [0.0, 1.0], "rows": [0.0, 1.0], "cells": [[0, 0, 1, 1]]}
        d = ok(post("/set_layout", layout=single))
        assert d.get("ok") is True


class TestEvalPython:
    def test_simple_expression(self):
        d = ok(post("/eval_python", code="print(1 + 1)"))
        assert "output" in d
        assert "2" in d["output"]

    def test_access_sublime(self):
        d = ok(post("/eval_python", code="print(sublime.version())"))
        assert "output" in d
        assert d["output"].strip().isdigit()

    def test_access_window(self):
        d = ok(post("/eval_python",
                    code="print(type(window).__name__)"))
        assert "output" in d
        assert "Window" in d["output"]

    def test_access_view(self):
        d = ok(post("/eval_python",
                    code="print(type(view).__name__)"))
        assert "output" in d
        assert "View" in d["output"]

    def test_syntax_error(self):
        d = ok(post("/eval_python", code="def ("))
        assert "error" in d or "output" in d

    def test_runtime_error(self):
        d = ok(post("/eval_python", code="raise ValueError('test error')"))
        assert "error" in d or "output" in d

    def test_multiline_code(self):
        code = "total = 0\nfor i in range(5):\n    total += i\nprint(total)"
        d = ok(post("/eval_python", code=code))
        assert "10" in d["output"]


class TestGetViewPhantoms:
    def test_returns_phantoms(self):
        d = ok(get("/view_phantoms"))
        assert "phantoms" in d or "error" in d


# ══ send_to_view ══════════════════════════════════════════════════════════════


class TestSendToView:
    def test_send_to_named_view(self):
        files = ok(get("/open_files"))["files"]
        terminus = next((f for f in files
                         if "command" in (f.get("name") or "").lower()
                         or "terminus" in (f.get("name") or "").lower()), None)
        if not terminus:
            pytest.skip("no Terminus/Command Prompt tab open")
        idx = files.index(terminus)
        d = ok(post("/send_to_view", text="echo pytest_send_ok\n", index=idx))
        assert d.get("ok") is True


# ══ error handling ════════════════════════════════════════════════════════════


class TestErrorHandling:
    def test_unknown_get_endpoint(self):
        r = get("/no_such_endpoint")
        assert r.status_code == 404

    def test_unknown_post_endpoint(self):
        r = post("/no_such_endpoint")
        assert r.status_code == 404

    def test_get_view_content_bad_index(self):
        # very large positive index should error
        d = ok(get("/view_content", index=99999))
        assert "error" in d

    def test_replace_lines_out_of_range(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        r = post("/replace_lines", begin=99999, end=99999,
                 text="oob\n", path=scratch_path)
        d = r.json()
        assert "error" in d or d.get("ok") is True

    def test_goto_line_zero(self, scratch_path):
        post("/open_file", path=scratch_path)
        time.sleep(0.2)
        r = post("/goto_line", line=0)
        assert r.status_code == 200

    def test_eval_python_empty(self):
        d = ok(post("/eval_python", code=""))
        assert "output" in d or "error" in d
