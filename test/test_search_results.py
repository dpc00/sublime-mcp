import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).parents[1] / "packages" / "st-plugin" / "search_results.py"
SPEC = importlib.util.spec_from_file_location("search_results", MODULE_PATH)
SEARCH_RESULTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SEARCH_RESULTS)


class SearchResultsTest(unittest.TestCase):
    def test_parses_native_results(self):
        content = """Searching 11 files for \"needle\"

C:\\work\\one.py:
  12: before needle after
C:\\work\\two.py:
  3: needle again

2 matches in 2 files
"""
        self.assertTrue(SEARCH_RESULTS.search_is_complete(content))
        self.assertEqual(
            SEARCH_RESULTS.parse_find_results(content, "needle"),
            [
                {"path": r"C:\work\one.py", "line": 12, "col": 8, "text": "before needle after"},
                {"path": r"C:\work\two.py", "line": 3, "col": 1, "text": "needle again"},
            ],
        )

    def test_limit_and_no_results(self):
        self.assertTrue(SEARCH_RESULTS.search_is_complete("No results found"))
        content = "C:\\work\\one.py:\n  1: x\n  2: x\n\n2 matches in 1 file\n"
        self.assertEqual(len(SEARCH_RESULTS.parse_find_results(content, "x", limit=1)), 1)


if __name__ == "__main__":
    unittest.main()
