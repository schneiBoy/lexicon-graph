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
import checks  # noqa: E402
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
        fails = self.check(d)["fails"]
        self.assertTrue(any("sacrificial" in f for f in fails))

    def test_padding_beyond_own_quote_is_flagged_even_if_word_is_elsewhere_in_source(self):
        d = good_draft()
        d["etymology_note"] = [{"text": "Derived from the verb, meaning benevolence toward neighbours.",
                                "quote": "From G25 (ἀγαπάω)"}]
        fails = self.check(d)["fails"]
        self.assertTrue(any("benevolence" in f for f in fails), fails)

    def test_strongs_must_be_exact_format(self):
        d = good_draft()
        d["semantic_contrasts"] = [{"strongs": ["$G5368"], "summary": "A contrast with another word entirely.",
                                    "quote": GOOD_QUOTE}]
        self.assertTrue(any("exactly" in f for f in self.check(d)["fails"]))

    def test_source_field_is_recorded_for_each_quote(self):
        fields = checks.to_fields(good_draft(), self.source)
        self.assertEqual(fields["evidence"][0]["source_field"], "strongs.definition")

    def test_wrong_shape_fails(self):
        d = good_draft()
        del d["distinctions"]
        self.assertTrue(self.check(d)["fails"])
        self.assertTrue(self.check("not an object")["fails"])
        d = good_draft()
        d["distinctions"][0] = "a bare string"
        self.assertTrue(self.check(d)["fails"])

    def test_same_quote_twice_fails(self):
        d = good_draft()
        d["key_theological_notes"] = [{"text": "Strong's defines it as love, affection or benevolence.", "quote": GOOD_QUOTE}]
        self.assertTrue(any("same quote" in f for f in self.check(d)["fails"]))

    def test_contrast_with_only_own_number_fails(self):
        d = good_draft()
        d["semantic_contrasts"] = [{"strongs": ["G26"], "summary": "Love, affection or benevolence, as defined.",
                                    "quote": "love, i.e. affection or benevolence"}]
        self.assertTrue(any("own number" in f for f in self.check(d)["fails"]))

    def test_contrast_must_mention_the_other_word_in_its_quote(self):
        d = good_draft()
        d["semantic_contrasts"] = [{"strongs": ["G25"], "summary": "Love, affection or benevolence, as defined.",
                                    "quote": "love, i.e. affection or benevolence"}]
        self.assertTrue(any("G25 is not mentioned" in f for f in self.check(d)["fails"]))
        d["semantic_contrasts"][0]["quote"] = "From G25 (ἀγαπάω)"
        self.assertFalse(any("is not mentioned" in f for f in self.check(d)["fails"]))

    def test_contrast_can_name_other_word_by_its_greek_lemma(self):
        d = good_draft()
        d["semantic_contrasts"] = [{"strongs": ["G25"], "summary": "Love, affection or benevolence, as defined.",
                                    "quote": "From G25 (ἀγαπάω)"}]
        src = copy.deepcopy(self.source)
        src["bullinger"] = {"text": "ἀγαπάω is to make much of a thing, to admire for some good reason"}
        d["semantic_contrasts"][0]["quote"] = "ἀγαπάω is to make much of a thing, to admire"
        self.assertEqual(check_draft(d, src, {"G25": "ἀγαπάω"})["fails"].count("x"), 0)
        self.assertFalse(any("is not mentioned" in f for f in check_draft(d, src, {"G25": "ἀγαπάω"})["fails"]))

    def test_quote_with_damaged_print_fails(self):
        d = good_draft()
        src = copy.deepcopy(self.source)
        src["bullinger"] = {"text": "a self-surrende ing fellowship", "do_not_quote": ["surrende ing"]}
        d["distinctions"][0]["quote"] = "a self-surrende ing fellowship"
        self.assertTrue(any("do_not_quote" in f for f in check_draft(d, src)["fails"]))

    def test_known_copy_error_in_thayers_cannot_be_quoted(self):
        d = good_draft()
        src = copy.deepcopy(self.source)
        src["thayers"] = {"text": "where δίκαιος καί ὁσιότης are connected", "do_not_quote": ["δίκαιος καί ὁσιότης"]}
        d["distinctions"][0]["quote"] = "where δίκαιος καί ὁσιότης are connected"
        self.assertTrue(any("do_not_quote" in f for f in check_draft(d, src)["fails"]))

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
