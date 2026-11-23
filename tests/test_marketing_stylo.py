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

    def test_a_string_of_fragments_differs_from_a_single_fragment(self):
        self.assertEqual(ml.classify_opener("Fast. Simple. Powerful."), "fragment_string")
        self.assertEqual(ml.classify_opener("Titanium."), "noun_fragment")
        self.assertEqual(ml.classify_opener("Ship faster. Sleep better."), "fragment_string")
        self.assertNotEqual(ml.classify_opener("Stripe is fast. It scales."), "fragment_string")

    def test_a_long_verbless_headline_is_unclassified_not_subject_first(self):
        self.assertEqual(ml.classify_opener("Payments, billing, and banking for modern businesses everywhere"), "unclassified")

    def test_the_noun_fragment_cutoff_is_six_words(self):
        self.assertEqual(ml.classify_opener("Financial infrastructure for modern internet businesses"), "noun_fragment")
        self.assertEqual(ml.classify_opener("Financial infrastructure for modern internet businesses everywhere"), "unclassified")

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


def corpus(*surfaces):
    return [{"name": "Acme", "surfaces": list(surfaces)}]


class TestPoolMetrics(unittest.TestCase):
    def test_cta_buzzwords_count_toward_the_buzzword_rate(self):
        m = stylo_cli.pool_metrics(corpus({"hero": {"headline": "Ship faster", "cta": "Unlock your seamless potential"}}))
        self.assertAlmostEqual(m["buzzwords_per_1k"], 1000.0 * 2 / 6)

    def test_a_headline_with_no_words_is_skipped_and_counted(self):
        m = stylo_cli.pool_metrics(corpus({"hero": {"headline": "\U0001F680"}}, {"hero": {"headline": "Build it now"}}))
        self.assertEqual(m["headline_count"], 1)
        self.assertEqual(m["headline_len_mean"], 3)
        self.assertEqual(m["headline_len_min"], 3)
        self.assertEqual(m["headlines_skipped"], 1)

    def test_opener_shares_sum_to_one(self):
        m = stylo_cli.pool_metrics(corpus({"hero": {"headline": "##"}}, {"hero": {"headline": "Build it now"}}))
        self.assertAlmostEqual(sum(m["opener_dist"].values()), 1.0)

    def test_unclassified_headlines_appear_in_the_opener_distribution(self):
        m = stylo_cli.pool_metrics(corpus({"hero": {"headline": "Payments, billing, and banking for modern businesses everywhere"}}))
        self.assertEqual(m["opener_dist"]["unclassified"], 1.0)

    def test_fragment_strings_appear_in_the_opener_distribution(self):
        m = stylo_cli.pool_metrics(corpus({"hero": {"headline": "Fast. Simple. Powerful."}}))
        self.assertEqual(m["opener_dist"]["fragment_string"], 1.0)


class TestCorpusInput(unittest.TestCase):
    def write(self, data):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        f.write(data if isinstance(data, str) else json.dumps(data))
        f.close()
        self.addCleanup(Path(f.name).unlink)
        return f.name

    def test_a_dict_without_companies_or_surfaces_is_rejected(self):
        with self.assertRaises(SystemExit) as cm:
            stylo_cli.load_corpus(self.write({"results": [1]}))
        self.assertNotEqual(cm.exception.code, 0)

    def test_the_three_supported_shapes_load(self):
        company = {"name": "Acme", "surfaces": []}
        self.assertEqual(stylo_cli.load_corpus(self.write([company])), [company])
        self.assertEqual(stylo_cli.load_corpus(self.write({"companies": [company]})), [company])
        self.assertEqual(stylo_cli.load_corpus(self.write(company)), [company])

    def test_invalid_json_exits_with_the_path_in_the_message(self):
        path = self.write("{not json")
        with self.assertRaises(SystemExit) as cm:
            stylo_cli.load_corpus(path)
        self.assertIn(path, str(cm.exception.code))

    def test_a_missing_file_exits_with_the_path_in_the_message(self):
        with self.assertRaises(SystemExit) as cm:
            stylo_cli.load_corpus("/nonexistent/corpus.json")
        self.assertIn("/nonexistent/corpus.json", str(cm.exception.code))

    def test_null_sections_are_treated_as_absent(self):
        self.assertEqual(ml.surface_metrics({"hero": None, "announcement": None}), {})

    def test_analyze_exits_nonzero_when_no_headlines_are_found(self):
        path = self.write({"companies": [{"name": "Acme", "surfaces": []}]})
        sys.argv = ["marketing-stylo.py", "analyze", path]
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as cm:
            stylo_cli.main()
        self.assertNotEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
