import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import marketing_lib as ml


def load_script(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


stylo_cli = load_script("marketing-stylo")
harvest = load_script("harvest-marketing")


class TestMarketingStylo(unittest.TestCase):
    def test_an_unpunctuated_headline_has_no_terminal_punctuation(self):
        m = ml.headline_metrics("Agentic Infrastructure Vercel")
        self.assertEqual(m["word_count"], 3)
        self.assertFalse(m["terminal_period"])
        self.assertEqual(m["terminal_punct"], "")

    def test_terminal_punctuation_is_reported(self):
        self.assertEqual(ml.headline_metrics("Titanium.")["terminal_punct"], ".")
        self.assertTrue(ml.headline_metrics("Titanium.")["terminal_period"])
        self.assertEqual(ml.headline_metrics("Hello!")["terminal_punct"], "!")

    def test_a_markdown_heading_prefix_is_stripped_and_the_words_kept(self):
        self.assertEqual(ml.headline_metrics("## Built for Developers")["text"], "Built for Developers")

    def test_bold_and_italic_markup_is_stripped(self):
        self.assertEqual(ml.headline_metrics("**Ship** _faster_")["text"], "Ship faster")

    def test_opener_classification(self):
        # Imperative
        self.assertEqual(ml.classify_opener("Build software faster with AI"), "imperative")
        self.assertEqual(ml.classify_opener("Accept payments online"), "imperative")
        self.assertEqual(ml.classify_opener("Deploy in seconds"), "imperative")

        # Noun fragment (short, no verb)
        self.assertEqual(ml.classify_opener("Titanium"), "noun_fragment")
        self.assertEqual(ml.classify_opener("Financial infrastructure"), "noun_fragment")

        # Subject-first declarative
        self.assertEqual(ml.classify_opener("We make payments simple"), "subject_first")
        self.assertEqual(ml.classify_opener("The system for modern product teams"), "subject_first")
        self.assertEqual(ml.classify_opener("Stripe is a financial platform"), "subject_first")

        # Adverbial opener (forbidden by Part 1 hard rule)
        self.assertEqual(ml.classify_opener("In a rapidly changing world, teams need speed"), "adverbial")
        self.assertEqual(ml.classify_opener("With Stripe, companies grow faster"), "adverbial")
        self.assertEqual(ml.classify_opener("From idea to production in minutes"), "adverbial")

    def test_buzzword_counting(self):
        clean_text = "Accept payments, build flexible billing, and move money globally."
        self.assertEqual(ml.buzzword_count(clean_text), 0)

        slop_text = "Our cutting-edge platform will supercharge your workflow and seamlessly unleash your potential."
        self.assertEqual(ml.buzzword_count(slop_text), 4)

    def test_buzzwords_match_regardless_of_case(self):
        self.assertEqual(ml.buzzword_count("Unlock. Supercharge."), 2)

    def test_emdash_detection_in_marketing(self):
        stripe_h1 = "Financial infrastructure for the internet — accept payments globally."
        m = ml.headline_metrics(stripe_h1)
        self.assertTrue(m["has_emdash"])

        clean_h1 = "Financial infrastructure for the internet: accept payments globally."
        m2 = ml.headline_metrics(clean_h1)
        self.assertFalse(m2["has_emdash"])


if __name__ == "__main__":
    unittest.main()
