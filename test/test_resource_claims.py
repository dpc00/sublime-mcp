"""Resource claims (claim_resource / release_resource / list_claims).

The plugin imports `sublime`, so it cannot be imported outside Sublime Text. The claims code only needs
`threading` and `time`, so this test cuts that block out of the source and runs it in a plain namespace,
with a fake clock to check the expiry. A source check makes sure the three tools are registered and routed.
"""
import threading
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parent.parent / "sublime_mcp.py").read_text(encoding="utf-8")
START = SOURCE.index("# ── resource claims")
END = SOURCE.index("def _command_name_from_class")


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def time(self):
        return self.now


class ResourceClaimsTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.ns = {"threading": threading, "time": self.clock}
        exec(compile(SOURCE[START:END], "sublime_mcp.py (claims)", "exec"), self.ns)
        self.claim = self.ns["_claim_resource"]
        self.release = self.ns["_release_resource"]
        self.list = self.ns["_list_claims"]

    def test_claim_then_busy_for_another_holder(self):
        first = self.claim({"resource": "input_panel", "holder": "a", "note": "goto", "ttl_seconds": 30})
        self.assertEqual(first, {"ok": True, "resource": "input_panel", "holder": "a", "ttl_seconds": 30.0})
        busy = self.claim({"resource": "input_panel", "holder": "b"})
        self.assertEqual(busy["error"], "busy")
        self.assertEqual((busy["holder"], busy["note"], busy["expires_in"]), ("a", "goto", 30.0))

    def test_the_same_holder_is_also_told_busy(self):
        self.claim({"resource": "r", "holder": "a"})
        self.assertEqual(self.claim({"resource": "r", "holder": "a"})["error"], "busy")

    def test_force_takes_the_claim_over(self):
        self.claim({"resource": "r", "holder": "a"})
        self.assertTrue(self.claim({"resource": "r", "holder": "b", "force": True})["ok"])
        self.assertEqual(self.list({})["claims"][0]["holder"], "b")

    def test_claims_expire_on_their_own(self):
        self.claim({"resource": "r", "holder": "a", "ttl_seconds": 10})
        self.clock.now += 9
        self.assertEqual(len(self.list({})["claims"]), 1)
        self.clock.now += 1
        self.assertEqual(self.list({}), {"claims": []})
        self.assertTrue(self.claim({"resource": "r", "holder": "b"})["ok"])

    def test_ttl_is_clamped(self):
        self.assertEqual(self.claim({"resource": "a", "holder": "h", "ttl_seconds": 0})["ttl_seconds"], 1.0)
        self.assertEqual(self.claim({"resource": "b", "holder": "h", "ttl_seconds": 99999})["ttl_seconds"], 600.0)
        self.assertEqual(self.claim({"resource": "c", "holder": "h"})["ttl_seconds"], 60.0)

    def test_only_the_holder_can_release(self):
        self.claim({"resource": "r", "holder": "a"})
        wrong = self.release({"resource": "r", "holder": "b"})
        self.assertEqual((wrong["error"], wrong["holder"]), ("held by a different holder", "a"))
        self.assertEqual(self.release({"resource": "r", "holder": "a"}), {"ok": True, "resource": "r", "was_claimed": True})
        self.assertEqual(self.list({}), {"claims": []})

    def test_releasing_nothing_is_not_an_error(self):
        self.assertEqual(self.release({"resource": "r", "holder": "a"}), {"ok": True, "resource": "r", "was_claimed": False})

    def test_required_and_invalid_parameters(self):
        self.assertEqual(self.claim({"holder": "a"}), {"error": "resource required"})
        self.assertEqual(self.claim({"resource": "r"}), {"error": "holder required"})
        self.assertEqual(self.claim({"resource": "r", "holder": "a", "ttl_seconds": "soon"}), {"error": "ttl_seconds must be a number"})
        self.assertEqual(self.release({"holder": "a"}), {"error": "resource required"})
        self.assertEqual(self.release({"resource": "r"}), {"error": "holder required"})

    def test_resources_are_independent(self):
        self.claim({"resource": "input_panel", "holder": "a"})
        self.assertTrue(self.claim({"resource": "control_panel", "holder": "b"})["ok"])
        self.assertEqual(sorted(c["resource"] for c in self.list({})["claims"]), ["control_panel", "input_panel"])


class RegistrationTest(unittest.TestCase):
    def test_tools_and_routes_are_registered(self):
        for name in ("claim_resource", "release_resource", "list_claims"):
            self.assertIn('("' + name + '",', SOURCE)
            self.assertIn('"/' + name + '": _' + name + ",", SOURCE)

    def test_drive_input_panel_points_at_the_claim(self):
        self.assertIn("resource='input_panel'", SOURCE)


if __name__ == "__main__":
    unittest.main()
