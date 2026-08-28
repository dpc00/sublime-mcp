import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).parents[1] / "packages" / "st-plugin" / "ide_companion.py"
SPEC = importlib.util.spec_from_file_location("ide_companion", MODULE_PATH)
IDE_COMPANION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IDE_COMPANION)


class IdeLineEndingsTest(unittest.TestCase):
    def test_detects_crlf_and_lf(self):
        self.assertEqual(IDE_COMPANION.detect_line_ending(b"one\r\ntwo\r\n"), "\r\n")
        self.assertEqual(IDE_COMPANION.detect_line_ending(b"one\ntwo\n"), "\n")

    def test_preserves_source_convention_for_proposed_text(self):
        proposed = "one\ntwo\r\nthree\r"
        self.assertEqual(
            IDE_COMPANION.preserve_line_endings(proposed, "\r\n"),
            "one\r\ntwo\r\nthree\r\n",
        )
        self.assertEqual(
            IDE_COMPANION.preserve_line_endings(proposed, "\n"),
            "one\ntwo\nthree\n",
        )


if __name__ == "__main__":
    unittest.main()
