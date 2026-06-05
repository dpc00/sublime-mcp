"""
Session-level cleanup: mark any test-owned views as scratch before closing
so ST never raises a save dialog.
"""

import httpx

BASE = "http://127.0.0.1:9500"

SCRATCH_CODE = (
    "[\n"
    "    v.set_scratch(True)\n"
    "    for v in window.views()\n"
    "    if 'pytest' in (v.name() or '').lower()\n"
    "    or 'pytest' in (v.file_name() or '').lower()\n"
    "]"
)


def _post(endpoint, **body):
    try:
        httpx.post(f"{BASE}{endpoint}", json=body, timeout=5.0)
    except Exception:
        pass


def pytest_sessionstart(session):
    """Before tests: clear out any leftover pytest buffers from a prior run."""
    _post("/eval_python", code=SCRATCH_CODE)


def pytest_sessionfinish(session, exitstatus):
    """After all tests: mark leftover pytest buffers scratch so ST won't prompt."""
    _post("/eval_python", code=SCRATCH_CODE)
