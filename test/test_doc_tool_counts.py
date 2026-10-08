"""The tool count quoted in the docs matches the generated fallback catalog.

Adding a tool changes the catalog (tools/generate_fallback_catalog.py) and the count in four places
in the docs; this fails when one of them is left behind.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _catalog_size():
    namespace = {}
    exec((ROOT / "packages" / "python-proxy" / "tool_catalog.py").read_text(encoding="utf-8"), namespace)
    return len(namespace["TOOLS"])


def _quoted(path, pattern):
    text = (ROOT / path).read_text(encoding="utf-8")
    match = re.search(pattern, text, re.S)
    assert match, "%s: no tool count found" % path
    return int(match.group(1))


class DocToolCountTest(unittest.TestCase):
    def test_every_quoted_count_matches_the_catalog(self):
        size = _catalog_size()
        for path, pattern in (
            ("README.md", r"catalog of (\d+) typed"),
            ("AGENT_GUIDE.md", r"typed catalog \((\d+)"),
            ("docs/AGENT_GUIDE.md", r"typed catalog \((\d+)"),
            ("docs/COMMAND_TOOLS.md", r"of the (\d+) tools"),
        ):
            self.assertEqual(_quoted(path, pattern), size, path)


if __name__ == "__main__":
    unittest.main()
