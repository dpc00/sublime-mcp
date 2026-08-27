"""Pure helpers for parsing Sublime Text's native Find Results buffer."""

import re


_SUMMARY_RE = re.compile(
    r"(?:\d+ matches? in \d+ files?|No results found|Search (?:cancelled|aborted))\s*$",
    re.IGNORECASE,
)
_RESULT_RE = re.compile(r"^\s+(\d+):\s?(.*)$")


def search_is_complete(text):
    """Return True once Sublime has appended a terminal search summary."""
    return bool(_SUMMARY_RE.search((text or "").rstrip()))


def parse_find_results(text, pattern="", regex=False, case_sensitive=False, limit=200):
    """Convert ST's Find Results text into stable, structured matches."""
    matches = []
    current_path = None
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = None
    if pattern:
        try:
            compiled = re.compile(pattern if regex else re.escape(pattern), flags)
        except re.error:
            compiled = None

    for line in (text or "").splitlines():
        if line and not line[0].isspace() and line.endswith(":"):
            candidate = line[:-1]
            if not candidate.lower().startswith("searching "):
                current_path = candidate
            continue
        result = _RESULT_RE.match(line)
        if not result or not current_path:
            continue
        line_number = int(result.group(1))
        preview = result.group(2)
        found = compiled.search(preview) if compiled else None
        matches.append({
            "path": current_path,
            "line": line_number,
            "col": found.start() + 1 if found else 1,
            "text": preview,
        })
        if len(matches) >= max(1, int(limit)):
            break
    return matches
