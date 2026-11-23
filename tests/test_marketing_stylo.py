import sys
import unittest
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import marketing_lib as ml


class TestMarketingStylo(unittest.TestCase):
    def test_three_word_unpunctuated_headline(self):
        """Opus Audit H3 test: A 3-word headline without closing punctuation must count as 3 words."""
        h = "Agentic Infrastructure Vercel"
        m = ml.headline_metrics(h)
        self.assertEqual(m["word_count"], 3)
        self.assertFalse(m["terminal_period"])
        self.assertEqual(m["terminal_punct"], "")

    def test_markdown_heading_not_deleted(self):
        """Opus Audit H3 test: Markdown header prefix (#) is stripped, but words remain intact."""
        h = "## Built for Developers"
        m = ml.headline_metrics(h)
        self.assertEqual(m["word_count"], 3)
        self.assertEqual(m["text"], "Built for Developers")

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
        # Matches: cutting-edge, supercharge, seamlessly, unleash (4 buzzwords)
        self.assertEqual(ml.buzzword_count(slop_text), 4)

    def test_emdash_detection_in_marketing(self):
        stripe_h1 = "Financial infrastructure for the internet — accept payments globally."
        m = ml.headline_metrics(stripe_h1)
        self.assertTrue(m["has_emdash"])

        clean_h1 = "Financial infrastructure for the internet: accept payments globally."
        m2 = ml.headline_metrics(clean_h1)
        self.assertFalse(m2["has_emdash"])


if __name__ == "__main__":
    unittest.main()
