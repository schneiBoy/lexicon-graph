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


class CheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lemmas = pilot.load_lemmas(pilot.DEFAULT_SAMPLE)

    def test_control_gold_has_no_hard_fails(self):
        for name, lemma in self.lemmas.items():
            result = check_draft(lemma["gold"], lemma["source"])
            self.assertEqual(result["fails"], [], f"{name}: {result['fails']}")

    def test_unknown_strongs_number_fails(self):
        lemma = copy.deepcopy(self.lemmas["agape"])
        lemma["gold"]["semantic_contrasts"][0]["strongs"].append("G9999")
        result = check_draft(lemma["gold"], lemma["source"])
        self.assertTrue(any("G9999" in f for f in result["fails"]))

    def test_invented_number_fails(self):
        lemma = copy.deepcopy(self.lemmas["agape"])
        lemma["gold"]["etymology_note"] += " It appears 4721 times in the corpus."
        result = check_draft(lemma["gold"], lemma["source"])
        self.assertTrue(any("4721" in f for f in result["fails"]))

    def test_wrong_shape_fails(self):
        lemma = copy.deepcopy(self.lemmas["agape"])
        del lemma["gold"]["distinctions"]
        self.assertTrue(check_draft(lemma["gold"], lemma["source"])["fails"])
        self.assertTrue(check_draft("not an object", lemma["source"])["fails"])

    def test_invented_greek_word_is_flagged_not_failed(self):
        lemma = copy.deepcopy(self.lemmas["agape"])
        lemma["gold"]["etymology_note"] += " Compare γνῶσις in the same period."
        result = check_draft(lemma["gold"], lemma["source"])
        self.assertEqual(result["fails"], [])
        self.assertTrue(any("γνῶσις" in f for f in result["flags"]))


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
