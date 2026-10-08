"""get_help(section=...) returns only the matching part of the guide.

The splitting helpers are pure functions, so they are pulled out of the plugin source and run for real,
on made-up text and on the real AGENT_GUIDE.md (the plugin imports `sublime` and cannot be imported
outside Sublime Text).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = (ROOT / "sublime_mcp.py").read_text(encoding="utf-8")
GUIDE = (ROOT / "AGENT_GUIDE.md").read_text(encoding="utf-8")


def _load():
    match = re.search(r"(def _split_guide.*?)\ndef _get_help\(", SOURCE, re.S)
    assert match, "help helpers not found"
    namespace = {}
    exec(match.group(1), namespace)
    return namespace["_split_guide"], namespace["_help_for"]


split_guide, help_for = _load()

SAMPLE = (
    "# Title\nintro line\n\n"
    "## Alpha topic\nalpha text\n```\n## not a heading\n```\nmore alpha\n\n"
    "## Beta (cuts trips)\nbeta text\n"
)


class SplitTest(unittest.TestCase):
    def test_parts_and_overview(self):
        self.assertEqual([h for h, _ in split_guide(SAMPLE)], ["Overview", "Alpha topic", "Beta (cuts trips)"])

    def test_nothing_is_lost(self):
        self.assertEqual("".join(t for _, t in split_guide(SAMPLE)), SAMPLE)

    def test_a_heading_inside_a_code_fence_is_not_a_split(self):
        alpha = dict(split_guide(SAMPLE))["Alpha topic"]
        self.assertIn("## not a heading", alpha)
        self.assertIn("more alpha", alpha)

    def test_text_without_headings_is_one_overview(self):
        self.assertEqual(split_guide("just text\n"), [("Overview", "just text\n")])


class HelpForTest(unittest.TestCase):
    def test_no_section_returns_everything_and_lists_headings(self):
        result = help_for(SAMPLE, None)
        self.assertEqual(result["content"], SAMPLE)
        self.assertEqual(result["sections"], ["Overview", "Alpha topic", "Beta (cuts trips)"])

    def test_empty_section_is_the_same_as_none(self):
        self.assertEqual(help_for(SAMPLE, "  ")["content"], SAMPLE)

    def test_section_matches_any_case_and_part_of_a_heading(self):
        result = help_for(SAMPLE, "ALPHA")
        self.assertEqual(result["matched"], ["Alpha topic"])
        self.assertIn("alpha text", result["content"])
        self.assertNotIn("beta text", result["content"])

    def test_several_matches_are_joined(self):
        self.assertEqual(help_for(SAMPLE, "a")["matched"], ["Alpha topic", "Beta (cuts trips)"])

    def test_no_match_is_an_error_with_the_headings(self):
        result = help_for(SAMPLE, "zzz")
        self.assertIn("error", result)
        self.assertEqual(result["sections"], ["Overview", "Alpha topic", "Beta (cuts trips)"])

    def test_the_tool_passes_the_argument_on(self):
        self.assertIn('return _help_for(text, body.get("section"))', SOURCE)
        self.assertIn('"section": {', SOURCE)


class RealGuideTest(unittest.TestCase):
    def test_console_section_is_small_and_has_the_console_notes(self):
        result = help_for(GUIDE, "console")
        self.assertTrue(result["ok"])
        self.assertLess(len(result["content"]), len(GUIDE) / 2)
        self.assertIn("get_console", result["content"])

    def test_every_real_heading_can_be_asked_for(self):
        for heading in help_for(GUIDE, None)["sections"]:
            result = help_for(GUIDE, heading)
            self.assertIn(heading, result["matched"], heading)

    def test_no_section_is_huge(self):
        # get_help(section=...) only helps if the sections are small; split a section that grows
        for heading, text in split_guide(GUIDE):
            self.assertLess(len(text), 4000, "section too large for get_help(section=): " + heading)

    def test_both_guide_copies_have_the_same_headings(self):
        other = (ROOT / "docs" / "AGENT_GUIDE.md").read_text(encoding="utf-8")
        self.assertEqual([h for h, _ in split_guide(GUIDE)], [h for h, _ in split_guide(other)])

    def test_the_real_guide_has_a_section_per_topic(self):
        sections = help_for(GUIDE, None)["sections"]
        self.assertGreaterEqual(len(sections), 8)
        self.assertEqual(len(sections), len(set(sections)), "section headings must be unique")


if __name__ == "__main__":
    unittest.main()
