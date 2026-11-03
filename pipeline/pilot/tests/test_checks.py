import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PILOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PILOT))

import pilot  # noqa: E402
from checks import check_draft  # noqa: E402


GOOD_QUOTE = "love, i.e. affection or benevolence; specially (plural) a love-feast"


def good_draft():
    return {
        "etymology_note": [],
        "distinctions": [{"text": "Strong's defines it as love, affection or benevolence, and in the plural a love-feast.",
                          "quote": GOOD_QUOTE}],
        "semantic_contrasts": [],
        "key_theological_notes": [],
    }


class CheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lemmas = pilot.load_lemmas(pilot.DEFAULT_SAMPLE)
        cls.source = cls.lemmas["agape"]["source"]

    def check(self, draft):
        return check_draft(draft, self.source)

    def test_supported_draft_has_no_fails(self):
        self.assertEqual(self.check(good_draft())["fails"], [])

    def test_made_up_quote_fails(self):
        d = good_draft()
        d["distinctions"][0]["quote"] = "agape is the highest form of love known to man"
        self.assertTrue(any("not verbatim" in f for f in self.check(d)["fails"]))

    def test_quote_spanning_two_fields_fails(self):
        d = good_draft()
        d["distinctions"][0]["quote"] = GOOD_QUOTE + " Grouped under the English heading LOVE"
        self.assertTrue(any("not verbatim" in f for f in self.check(d)["fails"]))

    def test_unknown_strongs_number_fails(self):
        d = good_draft()
        d["semantic_contrasts"] = [{"strongs": ["G9999"], "summary": "A contrast with another word entirely.",
                                    "quote": GOOD_QUOTE}]
        self.assertTrue(any("G9999" in f for f in self.check(d)["fails"]))

    def test_invented_number_fails(self):
        d = good_draft()
        d["distinctions"][0]["text"] += " It appears 4721 times."
        self.assertTrue(any("4721" in f for f in self.check(d)["fails"]))

    def test_invented_greek_word_fails(self):
        d = good_draft()
        d["distinctions"][0]["text"] += " Compare γνῶσις in the same period."
        self.assertTrue(any("γνῶσις" in f for f in self.check(d)["fails"]))

    def test_reference_not_in_source_fails_without_in_1_false_positive(self):
        d = good_draft()
        d["distinctions"][0]["text"] += " In 1 John 4:8 God is love."
        fails = self.check(d)["fails"]
        self.assertTrue(any("1 John 4:8" in f for f in fails))
        self.assertFalse(any(f.endswith("In 1") for f in fails))

    def test_padded_wording_is_flagged(self):
        d = good_draft()
        d["distinctions"][0]["text"] += " It means deliberate, sacrificial devotion."
        flags = self.check(d)["flags"]
        self.assertTrue(any("sacrificial" in f for f in flags))

    def test_wrong_shape_fails(self):
        d = good_draft()
        del d["distinctions"]
        self.assertTrue(self.check(d)["fails"])
        self.assertTrue(self.check("not an object")["fails"])
        d = good_draft()
        d["distinctions"][0] = "a bare string"
        self.assertTrue(self.check(d)["fails"])

    def test_example_in_prompt_passes_its_own_check(self):
        result = check_draft(pilot.EXAMPLE_DRAFT, pilot.EXAMPLE_SOURCE)
        self.assertEqual(result["fails"], [])


class SpendGuardTests(unittest.TestCase):
    def run_pilot(self, *extra, env=None):
        full_env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        full_env.update(env or {})
        return subprocess.run([sys.executable, str(PILOT / "pilot.py"), "--models", "x", *extra],
                              capture_output=True, text=True, env=full_env)

    def test_verify_refuses_without_every_guard(self):
        r = self.run_pilot("--verify")
        self.assertNotEqual(r.returncode, 0)
        for needle in ("ANTHROPIC_API_KEY", "--verify-model", "--max-usd", "--confirm-spend", "pricing"):
            self.assertIn(needle, r.stderr)

    def test_verify_refuses_when_prices_are_blank(self):
        with tempfile.TemporaryDirectory() as d:
            prices = Path(d) / "p.json"
            prices.write_text(json.dumps({"input_per_mtok": None, "output_per_mtok": None}))
            r = self.run_pilot("--verify", "--verify-model", "m", "--max-usd", "1", "--confirm-spend",
                               "--pricing", str(prices), env={"ANTHROPIC_API_KEY": "test"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("fill in input_per_mtok", r.stderr)

    def test_budget_stops_before_exceeding_cap(self):
        with tempfile.TemporaryDirectory() as d:
            b = pilot.Budget(0.01, {"input_per_mtok": 100.0, "output_per_mtok": 100.0}, Path(d) / "l.jsonl")
            with self.assertRaises(RuntimeError):
                b.check(chars=100000, max_output=600)

    def test_dry_run_calls_nothing(self):
        r = self.run_pilot("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Dry run: nothing was called.", r.stdout)


if __name__ == "__main__":
    unittest.main()
